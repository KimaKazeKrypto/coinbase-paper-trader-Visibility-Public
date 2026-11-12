#!/usr/bin/env python3
"""Read-only Coinbase 3-coin PAPER TRADING experiment.

Trades are bookkeeping in JSON/CSV only. Public market data + public AUD/USD
reference feed; NO authentication, API keys, trading requests, or withdrawals.
Python 3.11+, standard library only. State is local and GitHub-persisted if deployed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import statistics
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

UTC = timezone.utc
BRISBANE = ZoneInfo('Australia/Brisbane')
LONDON = ZoneInfo('Europe/London')
NEW_YORK = ZoneInfo('America/New_York')
TOKYO = ZoneInfo('Asia/Tokyo')
ALLOWED = ('BTC-USD', 'LTC-USD', 'ADA-USD')  # compile-time whitelist, not agent-chosen
COINBASE = 'https://api.exchange.coinbase.com'
FX_API = 'https://api.frankfurter.dev/v1/latest'
HEADERS = {'Accept': 'application/json', 'User-Agent': 'ReadOnly-Paper-Simulator/2.0'}
MAX_TICK_AGE_SECONDS = 300
MAX_HOURLY_ENTRY_JUMP = 0.025  # avoid chasing large one-hour price shocks


def iso(dt: datetime) -> str:
    return dt.astimezone(UTC).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def parse_time(s: str) -> datetime:
    return datetime.fromisoformat(s.replace('Z', '+00:00'))


def local_time(s: str) -> str:
    return parse_time(s).astimezone(BRISBANE).strftime('%d %b %Y %I:%M %p AEST')


def cash(a: float) -> str:
    return f'A${a:,.2f}'


def read_json(url: str, params: dict | None = None) -> object:
    if params:
        url += '?' + urlencode(params)
    exc = None
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers=HEADERS), timeout=15) as response:
                return json.load(response)
        except (HTTPError, URLError, TimeoutError, ValueError) as e:
            exc = e
            if attempt < 2:
                time.sleep(1 + attempt)
    raise RuntimeError(f'Public data source unavailable: {exc}')


def strategy_digest(c: dict) -> str:
    """Freeze ALL configurable rules at experiment start (no moving goalposts)."""
    return hashlib.sha256(json.dumps(c, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def validate_config(c: dict) -> dict:
    if c.get('products') != list(ALLOWED):
        raise ValueError('Product allowlist is fixed: BTC-USD, LTC-USD, ADA-USD')
    limits = {
        'starting_balance_aud': (100, 1000000), 'run_days': (1, 180),
        'estimated_taker_fee_rate': (0, 0.03), 'estimated_slippage_rate': (0, 0.03),
        'max_position_fraction': (0.05, 0.9), 'max_drawdown_fraction': (0.02, 0.5),
        'max_trade_risk_fraction': (0.001, 0.05),
        'max_spread_fraction': (0.0001, 0.05),
        'max_entries_per_24h': (1, 12),
        'daily_loss_pause_fraction': (0.005, 0.5), 'stop_loss_fraction': (0.005, 0.3),
        'take_profit_fraction': (0.005, 0.5), 'trailing_stop_fraction': (0.005, 0.3),
        'minimum_trade_aud': (5, 1000), 'cooldown_hours': (0, 72),
    }
    for key, (minimum, maximum) in limits.items():
        val = float(c[key])
        if not math.isfinite(val) or not (minimum <= val <= maximum):
            raise ValueError(f'Invalid setting {key}: {val}')
    if int(c['max_entries_per_24h']) != c['max_entries_per_24h']:
        raise ValueError('max_entries_per_24h must be an integer')
    return c


def get_market(now: datetime) -> dict:
    """Fetch closed hourly candles, fresh bid/ask ticker, and reference FX."""
    end_time = int(now.timestamp() // 3600 * 3600)
    start = iso(datetime.fromtimestamp(end_time - 200 * 3600, UTC))
    end = iso(datetime.fromtimestamp(end_time, UTC))
    markets = {}
    for product in ALLOWED:   # cannot request any other coin
        payload = read_json(f'{COINBASE}/products/{product}/candles',
                            {'start': start, 'end': end, 'granularity': 3600})
        if not isinstance(payload, list):
            raise RuntimeError(f'Unexpected candle format for {product}')
        unique = {}
        for row in payload:
            if not isinstance(row, list) or len(row) < 6:
                continue
            stamp, lo, hi, op, close, vol = row[:6]
            stamp = int(stamp)
            if stamp + 3600 > now.timestamp() - 90:
                continue  # never use unfinished bars or barely closed bars
            if any(not math.isfinite(float(v)) or float(v) < 0 for v in [lo, hi, op, close, vol]):
                continue
            if min(float(lo), float(hi), float(op), float(close)) <= 0:
                continue
            unique[stamp] = {'stamp': stamp, 'low': float(lo), 'high': float(hi),
                             'open': float(op), 'close': float(close), 'volume': float(vol)}
        candles = [unique[t] for t in sorted(unique)]
        if len(candles) < 120 or now.timestamp() - (candles[-1]['stamp'] + 3600) > 7200:
            raise RuntimeError(f'Insufficient or stale market candles for {product}: no paper trades')
        # Coinbase explicitly warns that no candles are published in empty
        # intervals. Irregular hourly spacing invalidates EMA/RSI assumptions.
        if any(b['stamp'] - a['stamp'] != 3600 for a, b in zip(candles[-120:-1], candles[-119:])):
            raise RuntimeError(f'Gap in recent hourly candles for {product}: no paper trades')
        ticker = read_json(f'{COINBASE}/products/{product}/ticker')
        if not isinstance(ticker, dict) or not all(x in ticker for x in ('price', 'bid', 'ask', 'time')):
            raise RuntimeError(f'Ticker unavailable for {product}')
        px, bid, ask = (float(ticker[k]) for k in ('price', 'bid', 'ask'))
        if any(not math.isfinite(p) or p <= 0 for p in (px, bid, ask)) or bid > ask:
            raise RuntimeError(f'Invalid ticker price for {product}')
        tick_time = parse_time(str(ticker['time']))
        age = (now - tick_time).total_seconds()
        if not -60 <= age <= MAX_TICK_AGE_SECONDS:
            raise RuntimeError(f'Stale/out-of-order Coinbase ticker for {product}: no paper trades')
        spread = (ask - bid) / ((ask + bid) / 2)
        markets[product] = {'usd': px, 'bid_usd': bid, 'ask_usd': ask,
                            'spread_fraction': spread, 'ticker_time_utc': iso(tick_time),
                            'candles': candles}
    fx = read_json(FX_API, {'base': 'AUD', 'symbols': 'USD'})
    if not isinstance(fx, dict) or 'rates' not in fx:
        raise RuntimeError('AUD/USD reference unavailable')
    rate = float(fx['rates']['USD'])
    rate_date = datetime.strptime(fx['date'], '%Y-%m-%d').date()
    if not 0.2 < rate < 2 or not 0 <= (now.date() - rate_date).days <= 6:
        raise RuntimeError('AUD/USD reference is stale or invalid')
    for m in markets.values():
        m['aud'] = m['usd'] / rate  # indicative proxy; not a Coinbase AUD quote
        m['bid_aud'] = m['bid_usd'] / rate
        m['ask_aud'] = m['ask_usd'] / rate
    return {'products': markets, 'aud_usd': rate, 'fx_date': fx['date']}


def ema(values: list[float], periods: int) -> float:
    alpha = 2 / (periods + 1)
    result = values[0]
    for value in values[1:]:
        result += alpha * (value - result)
    return result


def rsi(values: list[float], window: int = 14) -> float:
    changes = [values[i] - values[i - 1] for i in range(len(values) - window, len(values))]
    gains = sum(max(x, 0) for x in changes) / window
    losses = sum(max(-x, 0) for x in changes) / window
    if losses == 0:
        return 100 if gains else 50
    return 100 - 100 / (1 + gains / losses)


def market_session(now: datetime) -> dict:
    """Approximate stock-market clock windows; NOT an exchange holiday calendar.

    Crypto itself trades 24/7. Sessions add context and are not directional signals.
    zoneinfo correctly adjusts London and New York daylight saving changes.
    """
    if now.tzinfo is None:
        raise ValueError('Market-session timestamp needs a timezone')
    ny, lon, jp = (now.astimezone(z) for z in (NEW_YORK, LONDON, TOKYO))
    def hour(dt: datetime) -> float:
        return dt.hour + dt.minute/60 + dt.second/3600
    us = ny.weekday() < 5 and 9.5 <= hour(ny) < 16
    uk = lon.weekday() < 5 and 8 <= hour(lon) < 16.5
    asia = jp.weekday() < 5 and (9 <= hour(jp) < 11.5 or 12.5 <= hour(jp) < 15.5)
    if us and uk:
        label = 'London–New York overlap'
    elif us:
        label = 'New York hours'
    elif uk:
        label = 'London hours'
    elif asia:
        label = 'Tokyo hours'
    else:
        label = 'Outside stock-hour windows'
    return {
        'label': label,
        'stock_hour_windows': {'tokyo': asia, 'london': uk, 'new_york': us},
        'near_stock_open': {
            'tokyo': asia and 9 <= hour(jp) < 10,
            'london': uk and 8 <= hour(lon) < 9,
            'new_york': us and 9.5 <= hour(ny) < 10.5,
        },
        'weekend_utc': now.astimezone(UTC).weekday() >= 5,
        'utc_hour': now.astimezone(UTC).hour,
        'local_clocks': {
            'tokyo': jp.strftime('%a %H:%M %Z'),
            'london': lon.strftime('%a %H:%M %Z'),
            'new_york': ny.strftime('%a %H:%M %Z'),
        },
        'qualification': 'Clock windows only: public holidays and exchange closures not verified; crypto trades 24/7.',
    }


def hour_matched_volume(bars: list[dict]) -> tuple[float, int]:
    """Volume relative to this UTC hour on previous days, without look-ahead.

    Prevents the ordinary US/UK daily volume peak being mistaken for a unique
    bullish signal. Requires four earlier matches; otherwise uses trailing 24h.
    """
    current = bars[-1]
    utc_hour = datetime.fromtimestamp(current['stamp'], UTC).hour
    prior = [float(x['volume']) for x in bars[:-1]
             if datetime.fromtimestamp(x['stamp'], UTC).hour == utc_hour][-12:]
    if len(prior) >= 4:
        baseline = statistics.median(prior)
    else:
        baseline = statistics.mean([x['volume'] for x in bars[-25:-1]])
    return float(current['volume']) / max(float(baseline), 1e-8), len(prior)


def session_performance(state: dict) -> list[dict]:
    """Descriptive sample stats grouped by BUY session (not trading advice)."""
    grouped: dict[str, list[float]] = {}
    for result in state['closed_results']:
        label = result.get('entry_market_session', 'Not recorded')
        grouped.setdefault(label, []).append(float(result['profit_aud']))
    return [{'session': label, 'completed_trades': len(results),
             'net_pnl_aud': round(sum(results), 2),
             'win_rate_pct': round(100 * sum(x > 0 for x in results) / len(results), 1)}
            for label, results in sorted(grouped.items())]


def quality_metrics(state: dict, cfg: dict, quotes: dict,
                    execution_prices: dict | None = None) -> dict:
    """Basic after-cost trading diagnostics, undefined with too few closes."""
    outcomes = [float(x['profit_aud']) for x in state['closed_results']]
    wins = [x for x in outcomes if x > 0]
    losses = [x for x in outcomes if x < 0]
    observations = [float(r['net_equity_aud']) for r in state['observations']]
    running_peak = float(state['starting_balance_aud'])
    max_drawdown = 0.0
    for value in observations:
        running_peak = max(running_peak, value)
        max_drawdown = max(max_drawdown, 100 * (1 - value / running_peak))
    trades = state['trades']
    slip = sum(float(t['coin_quantity']) * abs(float(t['simulated_fill_aud']) - float(t['reference_price_aud'])) for t in trades)
    fee = float(cfg['estimated_taker_fee_rate'])
    friction = float(cfg['estimated_slippage_rate'])
    benchmark = None
    base = state.get('btc_baseline_ask_aud', state.get('btc_baseline_aud'))
    if base and float(base) > 0:
        starting = float(state['starting_balance_aud'])
        btc_units = starting / (1 + fee) / (float(base) * (1 + friction))
        current_btc = quotes['BTC-USD']
        if execution_prices:
            current_btc = min(current_btc, float(execution_prices['BTC-USD'].get('bid_aud', current_btc)))
        benchmark = round(btc_units * current_btc * (1 - friction) * (1 - fee), 2)
    return {
        'completed_trades': len(outcomes),
        'win_rate_pct': round(100 * len(wins)/len(outcomes), 1) if outcomes else None,
        'net_expectancy_per_trade_aud': round(statistics.mean(outcomes), 2) if outcomes else None,
        'profit_factor': round(sum(wins)/abs(sum(losses)), 3) if losses else None,
        'profit_factor_note': 'Undefined without losing trades' if not losses else None,
        'max_observed_drawdown_pct': round(max_drawdown, 2),
        'estimated_fee_total_aud': round(float(state['fees_aud']), 2),
        'estimated_spread_and_slippage_total_aud': round(slip, 2),
        'current_exposure_pct': round(100 * (1 - float(state['cash_aud']) /
                                              max(estimated_equity(state, quotes, cfg, execution_prices=execution_prices), 1e-9)), 2)
                                if state['position'] else 0.,
        'estimated_round_trip_cost_pct_before_spread': round(200 * (fee + friction), 2),
        'risk_budget_per_new_trade_pct': round(100 * float(cfg['max_trade_risk_fraction']), 2),
        'btc_hold_baseline_liquidation_aud': benchmark,
        'btc_hold_baseline_net_pnl_aud': round(benchmark - float(state['starting_balance_aud']), 2) if benchmark is not None else None,
        'sample_warning': 'A small 30-day paper sample cannot establish persistent profitability, Sharpe or market-timing skill.'
    }


def signals(bars: list[dict]) -> dict:
    closes = [b['close'] for b in bars]
    vol = [b['volume'] for b in bars]
    r9, r26, r14 = ema(closes[-90:], 9), ema(closes[-100:], 26), rsi(closes)
    daily_change = closes[-1] / closes[-25] - 1
    # Compare with the same UTC hour on previous days to avoid time-of-day bias.
    rel_volume, same_hour_samples = hour_matched_volume(bars)
    rel_volume_24h = vol[-1] / max(statistics.mean(vol[-25:-1]), 1e-8)
    logreturns = [math.log(closes[i] / closes[i - 1]) for i in range(len(closes) - 24, len(closes))]
    hourly_vol = statistics.stdev(logreturns)
    last_hour_return = closes[-1] / closes[-2] - 1
    trend = (r9 / r26 - 1)
    buy_eligible = (trend > .0008 and closes[-1] >= r9 and 47 <= r14 <= 68
                    and daily_change > -.015 and rel_volume > .55
                    and abs(last_hour_return) <= MAX_HOURLY_ENTRY_JUMP)
    score = (2 * min(trend / .008, 5) + min(daily_change / .025, 3)
             + .4 * min(rel_volume, 2) - max(0, hourly_vol / .013 - 1)
             - max(0, (r14 - 64) / 5)) if buy_eligible else -100
    return {'ema9': r9, 'ema26': r26, 'rsi14': r14, 'change_24h': daily_change,
            'relative_volume': rel_volume, 'relative_volume_24h': rel_volume_24h,
            'same_hour_volume_samples': same_hour_samples,
            'hourly_volatility': hourly_vol, 'last_hour_return': last_hour_return,
            'entry_shock_filter_triggered': abs(last_hour_return) > MAX_HOURLY_ENTRY_JUMP,
            'eligible': buy_eligible, 'score': score}


def initial_state(cfg: dict, now: datetime) -> dict:
    starting = float(cfg['starting_balance_aud'])
    return {'version': 3, 'products': list(ALLOWED),
            'strategy_sha256': strategy_digest(cfg), 'started_at': iso(now),
            'ends_at': iso(now + timedelta(days=float(cfg['run_days']))), 'status': 'ACTIVE',
            'starting_balance_aud': starting, 'cash_aud': starting, 'position': None,
            'peak_equity_aud': starting, 'day_utc': now.date().isoformat(),
            'day_start_equity_aud': starting, 'last_candle': None, 'last_trade_at': None,
            'fees_aud': 0.0, 'closed_results': [], 'trades': [], 'observations': [],
            'signal_log': [], 'last_reason': 'Initialized; awaiting closed hourly market candles',
            'last_market': None}


def estimated_equity(state: dict, quotes: dict, cfg: dict, exit_costs: bool = True,
                     execution_prices: dict | None = None) -> float:
    equity = state['cash_aud']
    p = state['position']
    if p:
        # Use a tradable bid for liquidation if the public quote supplies it.
        ref = quotes[p['product']]
        if exit_costs and execution_prices:
            ref = min(ref, float(execution_prices[p['product']].get('bid_aud', ref)))
        amount = p['quantity'] * ref
        if exit_costs:
            amount *= 1 - float(cfg['estimated_taker_fee_rate'])
            amount *= 1 - float(cfg['estimated_slippage_rate'])
        equity += amount
    return equity


def trade_row(state: dict, now: datetime, product: str, side: str,
              units: float, reference_aud: float, fill_aud: float,
              fee: float, pnl: float | None, reason: str, quotes: dict, cfg: dict,
              execution_prices: dict | None = None) -> None:
    state['trades'].append({'timestamp_utc': iso(now), 'product': product, 'side': side,
                            'coin_quantity': units, 'reference_price_aud': reference_aud,
                            'simulated_fill_aud': fill_aud,
                            'estimated_fee_aud': fee, 'closed_profit_aud': pnl,
                            'cash_after_aud': state['cash_aud'],
                            'net_equity_after_aud': estimated_equity(state, quotes, cfg, execution_prices=execution_prices),
                            'reason': reason, 'market_session': market_session(now)['label'],
                            'weekend_utc': market_session(now)['weekend_utc']})


def simulated_buy(state: dict, now: datetime, product: str, quotes: dict,
                  cfg: dict, allocation: float, reason: str,
                  execution_prices: dict | None = None) -> bool:
    if product not in ALLOWED:
        raise RuntimeError('Attempted trade on non-whitelisted product')
    if state['position'] is not None or state['status'] != 'ACTIVE':
        return False
    fee = float(cfg['estimated_taker_fee_rate'])
    slip = float(cfg['estimated_slippage_rate'])
    budget = min(state['cash_aud'] * allocation,
                 estimated_equity(state, quotes, cfg) * float(cfg['max_position_fraction']))
    if budget < float(cfg['minimum_trade_aud']):
        return False
    notional = budget / (1 + fee)
    fee_aud = notional * fee
    ref = quotes[product]
    ask = float(execution_prices[product].get('ask_aud', ref)) if execution_prices else ref
    fill = max(ref, ask) * (1 + slip)
    units = notional / fill
    state['cash_aud'] -= budget
    state['position'] = {'product': product, 'quantity': units, 'entry_cost_aud': budget,
                         'entry_fill_aud': fill, 'highest_reference_aud': ref,
                         'entry_market_session': market_session(now)['label']}
    state['fees_aud'] += fee_aud
    state['last_trade_at'] = iso(now)
    trade_row(state, now, product, 'BUY', units, ref, fill, fee_aud, None, reason,
              quotes, cfg, execution_prices=execution_prices)
    return True


def simulated_sell(state: dict, now: datetime, quotes: dict, cfg: dict, reason: str,
                   execution_prices: dict | None = None) -> bool:
    p = state['position']
    if p is None:
        return False
    product = p['product']
    ref = quotes[product]
    bid = float(execution_prices[product].get('bid_aud', ref)) if execution_prices else ref
    fill = min(ref, bid) * (1 - float(cfg['estimated_slippage_rate']))
    gross = p['quantity'] * fill
    fee_aud = gross * float(cfg['estimated_taker_fee_rate'])
    realised = gross - fee_aud - p['entry_cost_aud']
    state['cash_aud'] += gross - fee_aud
    state['fees_aud'] += fee_aud
    state['closed_results'].append({'product': product, 'profit_aud': realised,
                                    'entry_market_session': p.get('entry_market_session', 'Not recorded')})
    state['position'] = None
    state['last_trade_at'] = iso(now)
    trade_row(state, now, product, 'SELL', p['quantity'], ref, fill, fee_aud,
              realised, reason, quotes, cfg, execution_prices=execution_prices)
    return True


def adaptive_factor(state: dict, product: str) -> tuple[float, str]:
    """Outcome-based risk reduction only; not ML or reliable market prediction."""
    history = [x['profit_aud'] for x in state['closed_results'] if x['product'] == product][-6:]
    if len(history) < 6:
        return 1.0, 'Too little closed-trade evidence to adapt'
    rate = sum(x > 0 for x in history) / len(history)
    if rate < .40 or sum(history) < 0:
        return .50, f'Risk reduced: {len(history)} recent {product} outcomes, {rate:.0%} profitable'
    if rate < .60:
        return .80, f'Risk moderately reduced: {len(history)} outcomes'
    return 1.0, 'Positive history; risk remains capped (not increased)'


def decide(state: dict, cfg: dict, now: datetime, market: dict) -> str:
    products = market['products']
    quotes = {key: products[key]['aud'] for key in ALLOWED}
    # New entries and trend analysis run only on a NEW common CLOSED candle.
    # Price-based stop/drawdown protections must STILL run on repeat snapshots.
    # Otherwise a second run in the same hour can ignore a sharp price drop.
    last_common = min(products[k]['candles'][-1]['stamp'] for k in ALLOWED)
    new_candle = state['last_candle'] is None or last_common > state['last_candle']
    sig = None
    if new_candle:
        aligned = {k: [b for b in products[k]['candles'] if b['stamp'] <= last_common]
                   for k in ALLOWED}
        if all(len(bars) >= 120 and bars[-1]['stamp'] == last_common for bars in aligned.values()):
            sig = {key: signals(aligned[key]) for key in ALLOWED}
            state['last_candle'] = last_common
            state['signal_log'].append({'time_utc': iso(now), 'market_session': market_session(now),
                                       'market_candle_utc': iso(datetime.fromtimestamp(last_common, UTC)),
                                       'signals': {
                key: {k: v for k, v in sig[key].items() if k in
                      ('rsi14', 'score', 'eligible', 'change_24h', 'relative_volume',
                       'relative_volume_24h', 'same_hour_volume_samples', 'hourly_volatility',
                       'last_hour_return', 'entry_shock_filter_triggered')}
                for key in ALLOWED}})
            state['signal_log'] = state['signal_log'][-4500:]
    current = estimated_equity(state, quotes, cfg, execution_prices=products)
    state['peak_equity_aud'] = max(state['peak_equity_aud'], current)
    if now.date().isoformat() != state['day_utc']:
        state['day_utc'] = now.date().isoformat()
        state['day_start_equity_aud'] = current
    if current <= state['peak_equity_aud'] * (1 - float(cfg['max_drawdown_fraction'])):
        simulated_sell(state, now, quotes, cfg, 'Maximum portfolio drawdown circuit breaker',
                       execution_prices=products)
        state['status'] = 'HALTED_DRAWDOWN'
        return f"HALTED: {100*float(cfg['max_drawdown_fraction']):.1f}% portfolio drawdown threshold met"
    held = state['position']
    if held:
        product = held['product']
        info = sig[product] if sig else None
        price = min(quotes[product], float(products[product].get('bid_aud', quotes[product])))
        held['highest_reference_aud'] = max(held['highest_reference_aud'], price)
        entry, peak = held['entry_fill_aud'], held['highest_reference_aud']
        trigger = None
        if price <= entry * (1 - float(cfg['stop_loss_fraction'])):
            trigger = 'Stop loss'
        elif peak >= entry * 1.01 and price <= peak * (1 - float(cfg['trailing_stop_fraction'])):
            trigger = 'Trailing stop'
        elif price >= entry * (1 + float(cfg['take_profit_fraction'])):
            trigger = 'Take profit'
        elif info and (info['ema9'] < info['ema26'] or info['rsi14'] < 40):
            trigger = 'Trend reversal'
        if trigger:
            simulated_sell(state, now, quotes, cfg, trigger, execution_prices=products)
            return f'SELL {product.split("-")[0]}: {trigger}; compare all three next hour'
        return f'HOLD {product.split("-")[0]}: risk checks passed' + (
            '; awaiting a new closed candle for trend signals' if sig is None else '')
    if sig is None:
        return 'HOLD CASH: no new aligned, closed hourly candle; no entry'
    if current < state['day_start_equity_aud'] * (1 - float(cfg['daily_loss_pause_fraction'])):
        return 'HOLD CASH: daily loss limit prevents new buys'
    if state['last_trade_at'] and now < parse_time(state['last_trade_at']) + timedelta(hours=float(cfg['cooldown_hours'])):
        return 'HOLD CASH: cooldown after last simulated trade'
    recent_entries = sum(t['side'] == 'BUY' and parse_time(t['timestamp_utc']) > now - timedelta(hours=24)
                         for t in state['trades'])
    if recent_entries >= int(cfg['max_entries_per_24h']):
        return 'HOLD CASH: limit on new entries per rolling 24 hours'
    qualified = [k for k in ALLOWED if sig[k]['eligible'] and sig[k]['score'] >= .8
                 and float(products[k].get('spread_fraction', 0)) <= float(cfg['max_spread_fraction'])]
    if not qualified:
        return 'HOLD CASH: no qualifying signal with acceptable bid–ask spread'
    strongest = max(qualified, key=lambda k: sig[k]['score'])
    winner = sig[strongest]
    correction = min(1., .008 / max(.0001, winner['hourly_volatility']))
    adapt, label = adaptive_factor(state, strongest)
    # Approximate one-trade loss budget including BOTH sides of fees, slippage
    # and the largest allowed bid-ask spread. Not a loss guarantee during gaps.
    planned_loss_per_dollar = (float(cfg['stop_loss_fraction']) +
                               2 * (float(cfg['estimated_taker_fee_rate']) +
                                    float(cfg['estimated_slippage_rate'])) +
                               float(cfg['max_spread_fraction']))
    trade_risk_cap = float(cfg['max_trade_risk_fraction']) / planned_loss_per_dollar
    allocation = min(float(cfg['max_position_fraction']) * correction * adapt,
                     trade_risk_cap, float(cfg['max_position_fraction']))
    if simulated_buy(state, now, strongest, quotes, cfg, allocation,
                     f"Best of three momentum signals; score {winner['score']:.2f}; {label}",
                     execution_prices=products):
        return f'BUY {strongest.split("-")[0]}: strongest qualifying signal (score {winner["score"]:.2f})'
    return 'HOLD CASH: trade failed minimum simulation size'


def step(state: dict, cfg: dict, now: datetime, market: dict) -> dict:
    if state.get('version') != 3 or state.get('products') != list(ALLOWED) or cfg['products'] != list(ALLOWED):
        raise RuntimeError('Trading whitelist/state mismatch: abort')
    if state.get('strategy_sha256') != strategy_digest(cfg):
        raise RuntimeError('Strategy/configuration changed during experiment: abort')
    if state['starting_balance_aud'] != float(cfg['starting_balance_aud']):
        raise RuntimeError('Starting balance changed mid-experiment: abort')
    quotes = {key: market['products'][key]['aud'] for key in ALLOWED}
    # BTC buy-and-hold baseline has the same estimated entry/exit friction.
    state.setdefault('btc_baseline_aud', quotes['BTC-USD'])
    state.setdefault('btc_baseline_ask_aud', market['products']['BTC-USD'].get('ask_aud', quotes['BTC-USD']))
    for price in quotes.values():
        if not math.isfinite(price) or price <= 0:
            raise RuntimeError('Invalid quote; no trade')
    if state['status'] == 'ACTIVE' and now >= parse_time(state['ends_at']):
        simulated_sell(state, now, quotes, cfg, '30-day simulation ended; closing paper position',
                       execution_prices=market['products'])
        state['status'] = 'FINISHED'
        decision = 'FINISHED: final paper portfolio recorded'
    elif state['status'] == 'ACTIVE':
        decision = decide(state, cfg, now, market)
    else:
        decision = f"{state['status']}: no further trades"
    state['last_reason'] = decision
    state['last_market'] = {'time_utc': iso(now), 'aud_usd_reference': market['aud_usd'],
                            'fx_date': market['fx_date'],
                            'prices': {key: {'usd': market['products'][key]['usd'],
                                             'aud_proxy': quotes[key],
                                             'bid_aud': market['products'][key].get('bid_aud', quotes[key]),
                                             'ask_aud': market['products'][key].get('ask_aud', quotes[key]),
                                             'spread_fraction': market['products'][key].get('spread_fraction', 0),
                                             'ticker_time_utc': market['products'][key].get('ticker_time_utc')}
                                       for key in ALLOWED}}
    candle_time = min(market['products'][k]['candles'][-1]['stamp'] for k in ALLOWED)
    if (not state['observations'] or state['observations'][-1]['candle'] != candle_time
            or state['observations'][-1]['decision'] != decision):
        state['observations'].append({'timestamp_utc': iso(now), 'candle': candle_time,
                                       'net_equity_aud': estimated_equity(state, quotes, cfg,
                                                                          execution_prices=market['products']),
                                       'cash_aud': state['cash_aud'],
                                       'held_product': state['position']['product'] if state['position'] else '',
                                       'decision': decision})
    state['peak_equity_aud'] = max(state['peak_equity_aud'],
                                   estimated_equity(state, quotes, cfg,
                                                    execution_prices=market['products']))
    return state


def safe_save(path: Path, value: dict) -> None:
    path.parent.mkdir(exist_ok=True, parents=True)
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent, delete=False) as out:
        json.dump(value, out, indent=2, allow_nan=False)
        out.write('\n')
        name = Path(out.name)
    name.replace(path)


def csv_out(path: Path, items: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(exist_ok=True, parents=True)
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        for item in items:
            writer.writerow(item)


def svg_graph(state: dict) -> str:
    history = state['observations']
    values = [float(row['net_equity_aud']) for row in history]
    start = state['starting_balance_aud']
    vals = values or [start]
    smallest, largest = min(vals + [start - 20, start + 50]), max(vals + [start + 100, start + 20])
    wiggle = (largest - smallest) * .12 or 10
    smallest, largest = smallest - wiggle, largest + wiggle
    width, height = 850, 240
    def x(i): return 48 + i * (width - 65) / max(1, len(vals) - 1)
    def y(v): return 18 + (largest-v) / (largest-smallest) * (height-42)
    points = ' '.join(f'{x(i):.2f},{y(v):.2f}' for i, v in enumerate(vals))
    guidelines = ''.join(f'<line x1="47" x2="835" y1="{y(v):.2f}" y2="{y(v):.2f}" '
                         f'stroke="#6885a7" opacity=".5" stroke-dasharray="5 5"/>'
                         f'<text x="1" y="{y(v)-4:.2f}" fill="#b7c8e3" font-size="12">{label}</text>'
                         for v, label in [(start, 'Start'), (start+50, '+A$50'), (start+100, '+A$100')])
    path = (f'<polyline points="{points}" fill="none" stroke="#6ecbfa" stroke-width="3"/>'
            if len(vals) > 1 else f'<circle cx="48" cy="{y(vals[0]):.2f}" r="4" fill="#6ecbfa"/>')
    return f'<svg viewBox="0 0 {width} {height}" width="100%" role="img" aria-label="30-day simulated net equity over time">{guidelines}{path}</svg>'


def report(state: dict, cfg: dict, root: Path) -> None:
    market = state['last_market']
    quotes = {k: market['prices'][k]['aud_proxy'] for k in ALLOWED}
    execution_prices = market['prices']
    worth = estimated_equity(state, quotes, cfg, execution_prices=execution_prices)
    pnl = worth - state['starting_balance_aud']
    per = (worth / state['starting_balance_aud'] - 1)*100
    holding = state['position']
    holding_text = f"{holding['quantity']:.8f} {holding['product'].split('-')[0]}" if holding else 'None (all cash)'
    sold = [x for x in state['trades'] if x['side'] == 'SELL']
    wins = sum(x['closed_profit_aud'] > 0 for x in sold)
    trade_fields = ['timestamp_utc', 'product', 'side', 'market_session', 'weekend_utc', 'coin_quantity', 'reference_price_aud',
                    'simulated_fill_aud', 'estimated_fee_aud', 'closed_profit_aud',
                    'cash_after_aud', 'net_equity_after_aud', 'reason']
    csv_out(root / 'data' / 'trades.csv', state['trades'], trade_fields)
    stats = quality_metrics(state, cfg, quotes, execution_prices=execution_prices)
    sessions = session_performance(state)
    session_now = market_session(parse_time(market['time_utc']))
    csv_out(root / 'data' / 'hourly_history.csv', state['observations'],
            ['timestamp_utc', 'candle', 'net_equity_aud', 'cash_aud', 'held_product', 'decision'])
    rows = '\n'.join(
        f"| {local_time(x['timestamp_utc'])} | {x['side']} | {x['product']} | {x['coin_quantity']:.8f} | "
        f"{cash(x['simulated_fill_aud'])} | {cash(x['estimated_fee_aud'])} | "
        f"{cash(x['closed_profit_aud']) if x['closed_profit_aud'] is not None else '—'} | {x['reason']} |"
        for x in reversed(state['trades'][-40:])) or '| — | None yet | — | — | — | — | — | Waiting for signal |'
    prices = '\n'.join(f"- {key}: Coinbase US${market['prices'][key]['usd']:,.5f}, "
                       f"indicative {cash(market['prices'][key]['aud_proxy'])} per coin; "
                       f"bid–ask spread {100*market['prices'][key].get('spread_fraction', 0):.3f}%"
                       for key in ALLOWED)
    session_table = '\n'.join(
        f"| {v['session']} | {v['completed_trades']} | {cash(v['net_pnl_aud'])} | {v['win_rate_pct']:.1f}% |"
        for v in sessions) or '| No round trips yet | 0 | — | — |'
    md = f'''# BTC–LTC–ADA 30-day paper trading experiment

**SIMULATION ONLY. NO REAL ORDERS.**\n\nStatus: **{state['status']}**  
Started: {local_time(state['started_at'])}  
Ends: {local_time(state['ends_at'])}  
Last checked: {local_time(market['time_utc'])}  
Decision: **{state['last_reason']}**

## Account (Australian dollars)

| Metric | Value |
|---|---:|
| Starting funds | {cash(state['starting_balance_aud'])} |
| Simulated available cash | {cash(state['cash_aud'])} |
| Single current position | {holding_text} |
| **Estimated liquidation balance** | **{cash(worth)}** |
| **Profit/loss to date** | **{cash(pnl)} ({per:+.2f}%)** |
| Estimated fees paid | {cash(state['fees_aud'])} |
| Completed trades | {len(sold)} ({wins} winners) |
| Target range, not a guarantee | A$1,050–A$1,100 |
| Max observed drawdown | {stats['max_observed_drawdown_pct']:.2f}% |
| Current account exposure | {stats['current_exposure_pct']:.2f}% |
| Per-new-trade loss budget (estimated, not guaranteed) | {stats['risk_budget_per_new_trade_pct']:.2f}% |
| Closed-trade win rate | {stats['win_rate_pct'] if stats['win_rate_pct'] is not None else 'Not enough trades'} |
| Mean profit per closed trade | {cash(stats['net_expectancy_per_trade_aud']) if stats['net_expectancy_per_trade_aud'] is not None else 'Not enough trades'} |
| Estimated fees + quoted spread + extra slippage | {cash(stats['estimated_fee_total_aud'] + stats['estimated_spread_and_slippage_total_aud'])} |
| Passive BTC reference liquidation | {cash(stats['btc_hold_baseline_liquidation_aud']) if stats['btc_hold_baseline_liquidation_aud'] is not None else 'Not recorded'} |

## Market-session context (clock-time proxies only)

Current approximation: **{session_now['label']}**, Brisbane time **{local_time(market['time_utc'])}**.  
Tokyo: {session_now['local_clocks']['tokyo']} · London: {session_now['local_clocks']['london']} · New York: {session_now['local_clocks']['new_york']}.

| Entry-window label | Closed trades | Net P/L | Win rate |
|---|---:|---:|---:|
{session_table}

**Important:** Time windows describe typical stock trading hours, not crypto exchange opening times. Public holidays are not checked. Small sample sizes do not establish that any window is profitable. Same-hour volume comparisons remove some predictable daily volume seasonality; the agent does **not** auto-buy just because a session is open.

## Public market prices used (USD source, AUD reference conversion)

{prices}

Reference AUD/USD: **{market['aud_usd_reference']:.6f}** dated {market['fx_date']}. Prices are indicative **converted proxies**, not guaranteed Coinbase AUD execution prices.

## Simulated trade ledger (last 40 events)

| Brisbane time | Side | Pair | Units | Simulated price (A$) | Estimated fee | Closed profit/loss | Decision reason |
|---|---|---|---:|---:|---:|---:|---|
{rows}

## Important methodology and limitations

- Whitelist: BTC-USD, LTC-USD, ADA-USD only. One position at a time, maximum {float(cfg['max_position_fraction']):.0%} exposure; risk-sized new entries target at most {float(cfg['max_trade_risk_fraction']):.1%} of account equity lost at the modeled stop **under assumed costs and continuous prices, not guaranteed**.
- Signals: aligned, continuous, CLOSED hourly candles, EMA(9/26), RSI(14), 24-hour change, same-UTC-hour volume, volatility. A sudden >{MAX_HOURLY_ENTRY_JUMP:.1%} one-hour movement blocks entries, and spread >{float(cfg['max_spread_fraction']):.2%} blocks that coin's entries.
- Maximum {int(cfg['max_entries_per_24h'])} fresh buys in any rolling 24-hour period; no forced trades to meet a profit goal. A config fingerprint prevents mid-test tuning to flatter the results.
- Adaptation: trade outcome history may **reduce** future position size. This is rules-based adaptive sizing, **not** a trained machine-learning model.
- Simulated fills reference the more conservative of the last-price ticker and quoted best **ask** on buys or **bid** on sells, plus estimated taker fee {float(cfg['estimated_taker_fee_rate'])*100:.2f}% and additional slippage {float(cfg['estimated_slippage_rate'])*100:.2f}% **per side**. Quote depth, latency and FX execution costs remain unmodeled.
- No transactions, deposits, API keys, or withdrawal rights are used; data only. No tax, FX execution costs, latency or overnight financing modeled.
- Skips trades when public prices are stale. One 30-day test cannot establish reliable monthly returns. A$50–A$100 is only the evaluation target; losing money is possible.
'''
    (root/'REPORT.md').write_text(md, encoding='utf-8')

    # Stable, deliberately public, machine-readable snapshot for check-ins from
    # ChatGPT. This file contains ONLY simulated trading information.
    last_signals = state['signal_log'][-1] if state['signal_log'] else None
    latest = last_signals['signals'] if last_signals else {}
    reported_time = market['time_utc']
    realised = sum(float(x['profit_aud']) for x in state['closed_results'])
    position = state['position']
    unrealised = (worth - float(state['cash_aud']) - float(position['entry_cost_aud'])) if position else 0.0
    snapshot = {
        'schema_version': 3,
        'mode': 'PAPER_ONLY', 'live_trading_enabled': False,
        'account_connected': False,
        'allowed_pairs': list(ALLOWED), 'currency': 'AUD',
        'last_checked_utc': reported_time, 'started_at_utc': state['started_at'],
        'ends_at_utc': state['ends_at'], 'status': state['status'],
        'starting_balance_aud': float(state['starting_balance_aud']),
        'net_liquidation_equity_aud': round(worth, 2),
        'net_profit_loss_aud': round(pnl, 2),
        'net_return_pct': round(per, 3),
        'target_profit_aud': {'low': 50, 'high': 100, 'note': 'Goal only, not guaranteed'},
        'cash_aud': round(float(state['cash_aud']), 2),
        'open_position': ({'pair': position['product'],
                           'coin_quantity': round(position['quantity'], 10),
                           'entry_cost_aud': round(position['entry_cost_aud'], 2),
                           'unrealised_after_exit_costs_aud': round(unrealised, 2)} if position else None),
        'fees_paid_estimate_aud': round(float(state['fees_aud']), 2),
        'slippage_each_side_pct': float(cfg['estimated_slippage_rate'])*100,
        'fee_rate_each_side_pct': float(cfg['estimated_taker_fee_rate'])*100,
        'max_new_trade_risk_fraction_estimate': float(cfg['max_trade_risk_fraction']),
        'max_quote_spread_fraction': float(cfg['max_spread_fraction']),
        'max_new_entries_per_24h': int(cfg['max_entries_per_24h']),
        'max_position_fraction': float(cfg['max_position_fraction']),
        'max_portfolio_drawdown_fraction': float(cfg['max_drawdown_fraction']),
        'entry_shock_filter_fraction': MAX_HOURLY_ENTRY_JUMP,
        'fixed_strategy_sha256': state['strategy_sha256'],
        'closed_trades': len(sold), 'winning_closed_trades': wins,
        'realised_profit_loss_aud': round(realised, 2),
        'peak_equity_aud': round(float(state['peak_equity_aud']), 2),
        'drawdown_from_peak_pct': round((1-worth/float(state['peak_equity_aud']))*100, 2),
        'last_decision': state['last_reason'],
        'market_session_context': session_now,
        'performance_by_entry_session': sessions,
        'quality_metrics': stats,
        'signals_checked_at_utc': last_signals['time_utc'] if last_signals else None,
        'signals': latest,
        'latest_prices': market['prices'],
        'aud_usd_reference': market['aud_usd_reference'],
        'fx_rate_date': market['fx_date'],
        'recent_trades': list(reversed(state['trades'][-10:])),
        'trade_count_total': len(state['trades']),
        'limitations': ['Simulated prices/fills and estimated costs, not real Coinbase trade outcomes',
                        'Public USD quotes converted to AUD at a reference FX rate, not actual AUD executable prices',
                        'Hourly stop checks can miss price gaps and exceed the modeled stop loss',
                        'No historical out-of-sample or sustained profitability proof',
                        'This is a rules-based system, not a machine-learning prediction model']
    }
    safe_save(root / 'data' / 'checkin.json', snapshot)
    sig_rows = '\n'.join(
        f"| {product} | {('Qualifies' if latest[product]['eligible'] else 'No signal') if product in latest else 'Not checked'} | "
        f"{latest[product]['score']:.2f} | {latest[product]['rsi14']:.1f} | "
        f"{latest[product]['change_24h']*100:+.2f}% | {latest[product]['relative_volume']:.2f}× |"
        if product in latest else f'| {product} | Not checked | — | — | — | — |'
        for product in ALLOWED
    )
    session_table_checkin = '\n'.join(
        f"| {v['session']} | {v['completed_trades']} | {cash(v['net_pnl_aud'])} |"
        for v in sessions) or '| No completed trades | 0 | — |'
    latest_trades = '\n'.join(
        f"| {local_time(t['timestamp_utc'])} | {t['side']} {t['product']} | "
        f"{cash(t['closed_profit_aud']) if t['closed_profit_aud'] is not None else 'Position opened'} | "
        f"{cash(t['estimated_fee_aud'])} | {t['reason']} |"
        for t in reversed(state['trades'][-10:])
    ) or '| — | No trades yet | — | — | Awaiting a qualifying signal |'
    checkin = f'''# Paper trader — ChatGPT check-in

> PAPER TRADING ONLY. No Coinbase account connected. No real orders.

Last market check: **{local_time(reported_time)}**. If this time is not recent, the runner may be paused or failing — **do not present stale data as live**.

**Status:** {state['status']} (from {local_time(state['started_at'])} to {local_time(state['ends_at'])})  
**Last decision:** {state['last_reason']}

| What to report | Current simulation |
|---|---:|
| Starting balance | {cash(state['starting_balance_aud'])} |
| Current estimated liquidation value | **{cash(worth)}** |
| Net profit or loss, including estimated exit costs | **{cash(pnl)} ({per:+.2f}%)** |
| Simulated cash available | {cash(state['cash_aud'])} |
| Current holding | {holding_text} |
| Realised profit or loss on completed trades | {cash(realised)} |
| Estimated fees paid to date | {cash(state['fees_aud'])} |
| Completed round-trip trades (winners) | {len(sold)} ({wins}) |
| Current drawdown from recorded peak | {(1-worth/float(state['peak_equity_aud']))*100:.2f}% |
| Worst observed peak-to-trough drawdown | {stats['max_observed_drawdown_pct']:.2f}% |
| Current portfolio exposure | {stats['current_exposure_pct']:.2f}% |
| Estimated risk limit per new trade, not guaranteed | {stats['risk_budget_per_new_trade_pct']:.2f}% |
| Closed-trade win rate | {str(stats['win_rate_pct'])+'%' if stats['win_rate_pct'] is not None else 'Not enough trades'} |
| Net mean per completed trade | {cash(stats['net_expectancy_per_trade_aud']) if stats['net_expectancy_per_trade_aud'] is not None else 'Not enough trades'} |
| Fees + bid–ask effects + extra slippage estimate | {cash(stats['estimated_fee_total_aud'] + stats['estimated_spread_and_slippage_total_aud'])} |
| BTC passive reference liquidation | {cash(stats['btc_hold_baseline_liquidation_aud']) if stats['btc_hold_baseline_liquidation_aud'] is not None else 'Not recorded'} |
| Desired monthly net profit (not guaranteed) | A$50 to A$100 |

## Regional market-clock context

**Current stock-hours proxy:** {session_now['label']}. Tokyo {session_now['local_clocks']['tokyo']}, London {session_now['local_clocks']['london']}, New York {session_now['local_clocks']['new_york']}.  
**Weekend by UTC:** {'Yes' if session_now['weekend_utc'] else 'No'}. Stock markets have holidays and closures; the agent does not check those calendars. **Crypto is open 24/7**. This context does not trigger a purchase or promise better results.

| Entry window | Completed trades | Net profit/loss |
|---|---:|---:|
{session_table_checkin}

## Latest recorded trade signals

Signals were last recorded: **{local_time(last_signals['time_utc']) if last_signals else 'No signals recorded yet'}**.

| Permitted coin | Entry status | Signal score | RSI(14) | 24-hour momentum | Same-hour relative volume |
|---|---|---:|---:|---:|---:|
{sig_rows}

## Most recent transactions

| Brisbane time | Action | Closed net P/L | Estimated fee | Explanation |
|---|---|---:|---:|---|
{latest_trades}

## How to interpret

- Prices are from public Coinbase BTC-USD, LTC-USD and ADA-USD markets; AUD is a reference conversion.
- Net liquidation value includes a hypothetical fee and slippage if the current holding were sold now.
- Bid–ask spreads are incorporated in simulated fills and liquidation values; coin entries are avoided above a {100*float(cfg['max_spread_fraction']):.2f}% quoted spread.
- The rules automatically decide when to hold cash, buy, sell or pause. Trading more frequently is not necessarily better.
- To reduce overtrading, entries are limited to {int(cfg['max_entries_per_24h'])} per rolling 24 hours. Sudden one-hour moves above {MAX_HOURLY_ENTRY_JUMP:.1%} block new entries; this is a cautious anti-chasing filter, not a proven predictive signal.
- The volume indicator is adjusted for recurring UTC-hour patterns in available candle history; it does not assume New York, London or Tokyo hours are automatically profitable.
- Costs assume {float(cfg['estimated_taker_fee_rate'])*100:.2f}% fee and {float(cfg['estimated_slippage_rate'])*100:.2f}% slippage **per side**; actual account-specific charges can differ.
- Strategy settings are frozen when the experiment starts. Mid-test config edits are rejected so comparisons cannot be quietly tuned after the fact.
- Trading is simulated, signals are experimental, and 30 days does not prove consistent profitability.
- If you ask ChatGPT for a check-in, provide the *public repository URL* once, then ask it to read `CHECKIN.md` or `data/checkin.json`. ChatGPT reads reports on request; this chat itself does not continuously run or watch the trader.
'''
    (root/'CHECKIN.md').write_text(checkin, encoding='utf-8')
    bodyrows = ''.join(
        f"<tr><td>{html.escape(local_time(x['timestamp_utc']))}</td>"
        f"<td>{html.escape(x['side'])}</td><td>{html.escape(x['product'])}</td>"
        f"<td>{x['coin_quantity']:.6f}</td><td>{cash(x['estimated_fee_aud'])}</td>"
        f"<td>{cash(x['closed_profit_aud']) if x['closed_profit_aud'] is not None else '—'}</td>"
        f"<td>{html.escape(x['reason'])}</td></tr>" for x in reversed(state['trades'][-30:]))
    if not bodyrows:
        bodyrows = '<tr><td colspan="7">No trades yet. Waiting for a valid signal.</td></tr>'
    market_cards = ''.join(f'<div class="panel"><div class="eyebrow">{k}</div>'
                           f'<div class="metric">{cash(quotes[k])}</div><div class="sub">Converted proxy · bid–ask spread {100*market["prices"][k].get("spread_fraction", 0):.3f}%</div></div>'
                           for k in ALLOWED)
    dashboard = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Bitcoin • Litecoin • Cardano | Paper Trading</title>
<style>*{{box-sizing:border-box}}body{{background:#0b1220;color:#e6edfb;font-family:system-ui,Arial,sans-serif;line-height:1.45;margin:0;padding:16px}}
main{{max-width:1060px;margin:auto}}h1{{font-size:1.8rem}}h2{{font-size:1.15rem;margin:0 0 12px}}.alert{{color:#ffd093}}
.panels{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}}
.panel{{background:#16243b;border:1px solid #32435e;border-radius:14px;padding:16px;margin:10px 0}}
.eyebrow,.sub{{color:#b9cce0;font-size:.86rem}}.metric{{font-weight:750;font-size:1.7rem;margin:8px 0}}
.chart{{overflow:hidden}}table{{border-collapse:collapse;width:100%;font-size:.87rem}}
th,td{{padding:10px;text-align:left;border-bottom:1px solid #37475f;white-space:nowrap}}
.tablewrap{{overflow-x:auto}}a{{color:#69d9ff}}.small{{color:#b6c7da;font-size:.83rem}}</style></head>
<body><main><h1>BTC · LTC · ADA paper agent</h1>
<p class="alert"><strong>SIMULATED FUNDS ONLY — NO REAL COINBASE TRADES</strong></p>
<p>Status: <b>{state['status']}</b> · Started {html.escape(local_time(state['started_at']))} · Ends {html.escape(local_time(state['ends_at']))}</p>
<p>Last market check {html.escape(local_time(market['time_utc']))} · Decision: {html.escape(state['last_reason'])}</p>
<div class="panels"><div class="panel"><div class="eyebrow">Portfolio after estimated exit costs</div><div class="metric">{cash(worth)}</div></div>
<div class="panel"><div class="eyebrow">30-day profit/loss</div><div class="metric">{cash(pnl)}</div><div class="sub">{per:+.2f}% from A$1,000</div></div>
<div class="panel"><div class="eyebrow">Available cash / position</div><div class="metric">{cash(state['cash_aud'])}</div><div class="sub">{html.escape(holding_text)}</div></div>
<div class="panel"><div class="eyebrow">Fees / completed trades</div><div class="metric">{cash(state['fees_aud'])}</div><div class="sub">{len(sold)} closed · {wins} winners</div></div>
<div class="panel"><div class="eyebrow">Risk / worst sampled drawdown</div><div class="metric">{stats['max_observed_drawdown_pct']:.2f}%</div><div class="sub">Current exposure {stats['current_exposure_pct']:.1f}% · target risk cap {stats['risk_budget_per_new_trade_pct']:.1f}% per new position (not guaranteed)</div></div>
<div class="panel"><div class="eyebrow">Global market-clock context</div><div class="metric" style="font-size:1.15rem">{html.escape(session_now['label'])}</div><div class="sub">Tokyo {html.escape(session_now['local_clocks']['tokyo'])} · London {html.escape(session_now['local_clocks']['london'])} · New York {html.escape(session_now['local_clocks']['new_york'])}</div></div></div>
<section class="panel"><h2>Net equity vs monthly A$50–A$100 target</h2><div class="chart">{svg_graph(state)}</div>
<p class="small">A target is not a prediction. The curve starts only when the live-source simulator is deployed and run. BTC buy-and-hold benchmark liquidation: {cash(stats['btc_hold_baseline_liquidation_aud']) if stats['btc_hold_baseline_liquidation_aud'] is not None else 'Not recorded'}; approximate fees included.</p></section>
<section><h2>Monitored Coinbase spot pairs</h2><div class="panels">{market_cards}</div>
<p class="small">USD market quotes converted using AUD/USD {market['aud_usd_reference']:.6f} (dated {market['fx_date']}); not executable AUD quotes.</p></section>
<section class="panel"><h2>Most recent simulated actions</h2><div class="tablewrap"><table><thead><tr><th>Brisbane time</th><th>Action</th><th>Pair</th><th>Quantity</th><th>Fee</th><th>Realised P/L</th><th>Why</th></tr></thead>
<tbody>{bodyrows}</tbody></table></div></section>
<p class="small">No API keys or account connection. Trades only in saved simulation files. Simulated bid/ask plus estimated taker fee {float(cfg['estimated_taker_fee_rate'])*100:.2f}% and additional slippage {float(cfg['estimated_slippage_rate'])*100:.2f}% each side. Costs are estimates; stops do not guarantee a maximum loss. Strategy settings cannot be changed after start. <a href="CHECKIN.md">ChatGPT check-in</a> · <a href="data/checkin.json">JSON summary</a> · <a href="REPORT.md">Full report</a> · <a href="data/trades.csv">Trade history CSV</a> · <a href="data/hourly_history.csv">Hourly balances CSV</a>.</p>
</main></body></html>'''
    (root/'index.html').write_text(dashboard, encoding='utf-8')


def run(root: Path, config_file: Path) -> None:
    config = validate_config(json.loads(config_file.read_text(encoding='utf-8')))
    path = root/'data'/'state.json'
    state = json.loads(path.read_text(encoding='utf-8')) if path.exists() else None
    if state is not None and state.get('status') in ('FINISHED', 'HALTED_DRAWDOWN'):
        # Do not shift the benchmark, reported dates, or P/L after the trial ends.
        # GitHub may continue scheduling, but the final result stays frozen.
        print(f"{state['status']} | historical paper-trading results frozen; no new market requests")
        return
    now = datetime.now(UTC)
    market = get_market(now)  # fetch and validate *all* 3 before touching state
    if state is None:
        state = initial_state(config, now)
    step(state, config, now, market)
    safe_save(path, state)
    report(state, config, root)
    eq = estimated_equity(state, {k: market['products'][k]['aud'] for k in ALLOWED},
                          config, execution_prices=market['products'])
    print(f"{state['status']} | {state['last_reason']} | Equity {cash(eq)} | Net change {cash(eq - state['starting_balance_aud'])}")


def main() -> None:
    p = argparse.ArgumentParser(description='Three-coin, no-credentials Coinbase PAPER trader')
    p.add_argument('--root', type=Path, default=Path('.'))
    p.add_argument('--config', type=Path, default=Path('config.json'))
    a = p.parse_args()
    try:
        run(a.root, a.config)
    except Exception as e:
        sys.exit(f'FAILED SAFELY: no real trades exist, market state unchanged. {e}')


if __name__ == '__main__':
    main()
