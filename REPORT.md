# BTC–LTC–ADA 30-day paper trading experiment

**SIMULATION ONLY. NO REAL ORDERS.**

Status: **ACTIVE**  
Started: 13 Nov 2026 08:59 AM AEST  
Ends: 13 Dec 2026 08:59 AM AEST  
Last checked: 19 Nov 2026 05:15 AM AEST  
Decision: **HOLD CASH: no qualifying signal with acceptable bid–ask spread**

## Account (Australian dollars)

| Metric | Value |
|---|---:|
| Starting funds | A$1,000.00 |
| Simulated available cash | A$984.47 |
| Single current position | None (all cash) |
| **Estimated liquidation balance** | **A$984.47** |
| **Profit/loss to date** | **A$-15.53 (-1.55%)** |
| Estimated fees paid | A$6.54 |
| Completed trades | 3 (0 winners) |
| Target range, not a guarantee | A$1,050–A$1,100 |
| Max observed drawdown | 1.55% |
| Current account exposure | 0.00% |
| Per-new-trade loss budget (estimated, not guaranteed) | 1.00% |
| Closed-trade win rate | 0.0 |
| Mean profit per closed trade | A$-5.18 |
| Estimated fees + quoted spread + extra slippage | A$7.72 |
| Passive BTC reference liquidation | A$879.42 |

## Market-session context (clock-time proxies only)

Current approximation: **New York hours**, Brisbane time **19 Nov 2026 05:15 AM AEST**.  
Tokyo: Thu 04:15 JST · London: Wed 19:15 GMT · New York: Wed 14:15 EST.

| Entry-window label | Closed trades | Net P/L | Win rate |
|---|---:|---:|---:|
| London hours | 1 | A$-4.40 | 0.0% |
| Outside stock-hour windows | 1 | A$-5.37 | 0.0% |
| Tokyo hours | 1 | A$-5.76 | 0.0% |

**Important:** Time windows describe typical stock trading hours, not crypto exchange opening times. Public holidays are not checked. Small sample sizes do not establish that any window is profitable. Same-hour volume comparisons remove some predictable daily volume seasonality; the agent does **not** auto-buy just because a session is open.

## Public market prices used (USD source, AUD reference conversion)

- BTC-USD: Coinbase US$62,779.42000, indicative A$93,264.93 per coin; bid–ask spread 0.000%
- LTC-USD: Coinbase US$43.85800, indicative A$65.16 per coin; bid–ask spread 0.057%
- ADA-USD: Coinbase US$0.15168, indicative A$0.23 per coin; bid–ask spread 0.026%

Reference AUD/USD: **0.673130** dated 2026-11-18. Prices are indicative **converted proxies**, not guaranteed Coinbase AUD execution prices.

## Simulated trade ledger (last 40 events)

| Brisbane time | Side | Pair | Units | Simulated price (A$) | Estimated fee | Closed profit/loss | Decision reason |
|---|---|---|---:|---:|---:|---:|---|
| 19 Nov 2026 01:14 AM AEST | SELL | ADA-USD | 790.80395288 | A$0.23 | A$1.07 | A$-5.76 | Trend reversal |
| 18 Nov 2026 10:02 AM AEST | BUY | ADA-USD | 790.80395288 | A$0.23 | A$1.09 | — | Best of three momentum signals; score 1.81; Too little closed-trade evidence to adapt |
| 18 Nov 2026 03:22 AM AEST | SELL | ADA-USD | 800.88264197 | A$0.23 | A$1.09 | A$-4.40 | Trend reversal |
| 17 Nov 2026 10:03 PM AEST | BUY | ADA-USD | 800.88264197 | A$0.23 | A$1.10 | — | Best of three momentum signals; score 1.26; Too little closed-trade evidence to adapt |
| 17 Nov 2026 01:03 PM AEST | SELL | BTC-USD | 0.00189884 | A$95,268.03 | A$1.09 | A$-5.37 | Trend reversal |
| 17 Nov 2026 08:03 AM AEST | BUY | BTC-USD | 0.00189884 | A$96,944.00 | A$1.10 | — | Best of three momentum signals; score 0.98; Too little closed-trade evidence to adapt |

## Important methodology and limitations

- Whitelist: BTC-USD, LTC-USD, ADA-USD only. One position at a time, maximum 35% exposure; risk-sized new entries target at most 1.0% of account equity lost at the modeled stop **under assumed costs and continuous prices, not guaranteed**.
- Signals: aligned, continuous, CLOSED hourly candles, EMA(9/26), RSI(14), 24-hour change, same-UTC-hour volume, volatility. A sudden >2.5% one-hour movement blocks entries, and spread >0.50% blocks that coin's entries.
- Maximum 2 fresh buys in any rolling 24-hour period; no forced trades to meet a profit goal. A config fingerprint prevents mid-test tuning to flatter the results.
- Adaptation: trade outcome history may **reduce** future position size. This is rules-based adaptive sizing, **not** a trained machine-learning model.
- Simulated fills reference the more conservative of the last-price ticker and quoted best **ask** on buys or **bid** on sells, plus estimated taker fee 0.60% and additional slippage 0.10% **per side**. Quote depth, latency and FX execution costs remain unmodeled.
- No transactions, deposits, API keys, or withdrawal rights are used; data only. No tax, FX execution costs, latency or overnight financing modeled.
- Skips trades when public prices are stale. One 30-day test cannot establish reliable monthly returns. A$50–A$100 is only the evaluation target; losing money is possible.
