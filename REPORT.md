# BTC–LTC–ADA 30-day paper trading experiment

**SIMULATION ONLY. NO REAL ORDERS.**

Status: **ACTIVE**  
Started: 13 Nov 2026 08:59 AM AEST  
Ends: 13 Dec 2026 08:59 AM AEST  
Last checked: 15 Nov 2026 12:02 AM AEST  
Decision: **HOLD CASH: no qualifying signal with acceptable bid–ask spread**

## Account (Australian dollars)

| Metric | Value |
|---|---:|
| Starting funds | A$1,000.00 |
| Simulated available cash | A$1,000.00 |
| Single current position | None (all cash) |
| **Estimated liquidation balance** | **A$1,000.00** |
| **Profit/loss to date** | **A$0.00 (+0.00%)** |
| Estimated fees paid | A$0.00 |
| Completed trades | 0 (0 winners) |
| Target range, not a guarantee | A$1,050–A$1,100 |
| Max observed drawdown | 0.00% |
| Current account exposure | 0.00% |
| Per-new-trade loss budget (estimated, not guaranteed) | 1.00% |
| Closed-trade win rate | Not enough trades |
| Mean profit per closed trade | Not enough trades |
| Estimated fees + quoted spread + extra slippage | A$0.00 |
| Passive BTC reference liquidation | A$922.76 |

## Market-session context (clock-time proxies only)

Current approximation: **Outside stock-hour windows**, Brisbane time **15 Nov 2026 12:02 AM AEST**.  
Tokyo: Sat 23:02 JST · London: Sat 14:02 GMT · New York: Sat 09:02 EST.

| Entry-window label | Closed trades | Net P/L | Win rate |
|---|---:|---:|---:|
| No round trips yet | 0 | — | — |

**Important:** Time windows describe typical stock trading hours, not crypto exchange opening times. Public holidays are not checked. Small sample sizes do not establish that any window is profitable. Same-hour volume comparisons remove some predictable daily volume seasonality; the agent does **not** auto-buy just because a session is open.

## Public market prices used (USD source, AUD reference conversion)

- BTC-USD: Coinbase US$66,403.48000, indicative A$97,862.29 per coin; bid–ask spread 0.001%
- LTC-USD: Coinbase US$47.02200, indicative A$69.30 per coin; bid–ask spread 0.140%
- ADA-USD: Coinbase US$0.15954, indicative A$0.24 per coin; bid–ask spread 0.031%

Reference AUD/USD: **0.678540** dated 2026-11-13. Prices are indicative **converted proxies**, not guaranteed Coinbase AUD execution prices.

## Simulated trade ledger (last 40 events)

| Brisbane time | Side | Pair | Units | Simulated price (A$) | Estimated fee | Closed profit/loss | Decision reason |
|---|---|---|---:|---:|---:|---:|---|
| — | None yet | — | — | — | — | — | Waiting for signal |

## Important methodology and limitations

- Whitelist: BTC-USD, LTC-USD, ADA-USD only. One position at a time, maximum 35% exposure; risk-sized new entries target at most 1.0% of account equity lost at the modeled stop **under assumed costs and continuous prices, not guaranteed**.
- Signals: aligned, continuous, CLOSED hourly candles, EMA(9/26), RSI(14), 24-hour change, same-UTC-hour volume, volatility. A sudden >2.5% one-hour movement blocks entries, and spread >0.50% blocks that coin's entries.
- Maximum 2 fresh buys in any rolling 24-hour period; no forced trades to meet a profit goal. A config fingerprint prevents mid-test tuning to flatter the results.
- Adaptation: trade outcome history may **reduce** future position size. This is rules-based adaptive sizing, **not** a trained machine-learning model.
- Simulated fills reference the more conservative of the last-price ticker and quoted best **ask** on buys or **bid** on sells, plus estimated taker fee 0.60% and additional slippage 0.10% **per side**. Quote depth, latency and FX execution costs remain unmodeled.
- No transactions, deposits, API keys, or withdrawal rights are used; data only. No tax, FX execution costs, latency or overnight financing modeled.
- Skips trades when public prices are stale. One 30-day test cannot establish reliable monthly returns. A$50–A$100 is only the evaluation target; losing money is possible.
