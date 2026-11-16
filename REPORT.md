# BTC–LTC–ADA 30-day paper trading experiment

**SIMULATION ONLY. NO REAL ORDERS.**

Status: **ACTIVE**  
Started: 13 Nov 2026 08:59 AM AEST  
Ends: 13 Dec 2026 08:59 AM AEST  
Last checked: 17 Nov 2026 09:01 AM AEST  
Decision: **HOLD BTC: risk checks passed; awaiting a new closed candle for trend signals**

## Account (Australian dollars)

| Metric | Value |
|---|---:|
| Starting funds | A$1,000.00 |
| Simulated available cash | A$814.81 |
| Single current position | 0.00189884 BTC |
| **Estimated liquidation balance** | **A$996.91** |
| **Profit/loss to date** | **A$-3.09 (-0.31%)** |
| Estimated fees paid | A$1.10 |
| Completed trades | 0 (0 winners) |
| Target range, not a guarantee | A$1,050–A$1,100 |
| Max observed drawdown | 0.31% |
| Current account exposure | 18.27% |
| Per-new-trade loss budget (estimated, not guaranteed) | 1.00% |
| Closed-trade win rate | Not enough trades |
| Mean profit per closed trade | Not enough trades |
| Estimated fees + quoted spread + extra slippage | A$1.28 |
| Passive BTC reference liquidation | A$910.60 |

## Market-session context (clock-time proxies only)

Current approximation: **Outside stock-hour windows**, Brisbane time **17 Nov 2026 09:01 AM AEST**.  
Tokyo: Tue 08:01 JST · London: Mon 23:01 GMT · New York: Mon 18:01 EST.

| Entry-window label | Closed trades | Net P/L | Win rate |
|---|---:|---:|---:|
| No round trips yet | 0 | — | — |

**Important:** Time windows describe typical stock trading hours, not crypto exchange opening times. Public holidays are not checked. Small sample sizes do not establish that any window is profitable. Same-hour volume comparisons remove some predictable daily volume seasonality; the agent does **not** auto-buy just because a session is open.

## Public market prices used (USD source, AUD reference conversion)

- BTC-USD: Coinbase US$65,250.07000, indicative A$96,572.34 per coin; bid–ask spread 0.000%
- LTC-USD: Coinbase US$44.52500, indicative A$65.90 per coin; bid–ask spread 0.058%
- ADA-USD: Coinbase US$0.15296, indicative A$0.23 per coin; bid–ask spread 0.013%

Reference AUD/USD: **0.675660** dated 2026-11-16. Prices are indicative **converted proxies**, not guaranteed Coinbase AUD execution prices.

## Simulated trade ledger (last 40 events)

| Brisbane time | Side | Pair | Units | Simulated price (A$) | Estimated fee | Closed profit/loss | Decision reason |
|---|---|---|---:|---:|---:|---:|---|
| 17 Nov 2026 08:03 AM AEST | BUY | BTC-USD | 0.00189884 | A$96,944.00 | A$1.10 | — | Best of three momentum signals; score 0.98; Too little closed-trade evidence to adapt |

## Important methodology and limitations

- Whitelist: BTC-USD, LTC-USD, ADA-USD only. One position at a time, maximum 35% exposure; risk-sized new entries target at most 1.0% of account equity lost at the modeled stop **under assumed costs and continuous prices, not guaranteed**.
- Signals: aligned, continuous, CLOSED hourly candles, EMA(9/26), RSI(14), 24-hour change, same-UTC-hour volume, volatility. A sudden >2.5% one-hour movement blocks entries, and spread >0.50% blocks that coin's entries.
- Maximum 2 fresh buys in any rolling 24-hour period; no forced trades to meet a profit goal. A config fingerprint prevents mid-test tuning to flatter the results.
- Adaptation: trade outcome history may **reduce** future position size. This is rules-based adaptive sizing, **not** a trained machine-learning model.
- Simulated fills reference the more conservative of the last-price ticker and quoted best **ask** on buys or **bid** on sells, plus estimated taker fee 0.60% and additional slippage 0.10% **per side**. Quote depth, latency and FX execution costs remain unmodeled.
- No transactions, deposits, API keys, or withdrawal rights are used; data only. No tax, FX execution costs, latency or overnight financing modeled.
- Skips trades when public prices are stale. One 30-day test cannot establish reliable monthly returns. A$50–A$100 is only the evaluation target; losing money is possible.
