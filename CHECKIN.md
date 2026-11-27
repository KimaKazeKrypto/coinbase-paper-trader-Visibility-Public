# Paper trader — ChatGPT check-in

> PAPER TRADING ONLY. No Coinbase account connected. No real orders.

Last market check: **28 Nov 2026 07:17 AM AEST**. If this time is not recent, the runner may be paused or failing — **do not present stale data as live**.

**Status:** ACTIVE (from 13 Nov 2026 08:59 AM AEST to 13 Dec 2026 08:59 AM AEST)  
**Last decision:** BUY LTC: strongest qualifying signal (score 1.05)

| What to report | Current simulation |
|---|---:|
| Starting balance | A$1,000.00 |
| Current estimated liquidation value | **A$960.28** |
| Net profit or loss, including estimated exit costs | **A$-39.72 (-3.97%)** |
| Simulated cash available | A$784.50 |
| Current holding | 2.66460686 LTC |
| Realised profit or loss on completed trades | A$-37.21 |
| Estimated fees paid to date | A$16.14 |
| Completed round-trip trades (winners) | 7 (0) |
| Current drawdown from recorded peak | 3.97% |
| Worst observed peak-to-trough drawdown | 3.97% |
| Current portfolio exposure | 18.31% |
| Estimated risk limit per new trade, not guaranteed | 1.00% |
| Closed-trade win rate | 0.0% |
| Net mean per completed trade | A$-5.32 |
| Fees + bid–ask effects + extra slippage estimate | A$19.20 |
| BTC passive reference liquidation | A$845.60 |
| Desired monthly net profit (not guaranteed) | A$50 to A$100 |

## Regional market-clock context

**Current stock-hours proxy:** Outside stock-hour windows. Tokyo Sat 06:17 JST, London Fri 21:17 GMT, New York Fri 16:17 EST.  
**Weekend by UTC:** No. Stock markets have holidays and closures; the agent does not check those calendars. **Crypto is open 24/7**. This context does not trigger a purchase or promise better results.

| Entry window | Completed trades | Net profit/loss |
|---|---:|---:|
| London hours | 2 | A$-11.27 |
| Outside stock-hour windows | 4 | A$-20.18 |
| Tokyo hours | 1 | A$-5.76 |

## Latest recorded trade signals

Signals were last recorded: **28 Nov 2026 07:17 AM AEST**.

| Permitted coin | Entry status | Signal score | RSI(14) | 24-hour momentum | Same-hour relative volume |
|---|---|---:|---:|---:|---:|
| BTC-USD | No signal | -100.00 | 26.0 | -1.58% | 0.47× |
| LTC-USD | Qualifies | 1.05 | 48.6 | +0.64% | 1.29× |
| ADA-USD | No signal | -100.00 | 34.6 | -1.06% | 0.63× |

## Most recent transactions

| Brisbane time | Action | Closed net P/L | Estimated fee | Explanation |
|---|---|---:|---:|---|
| 28 Nov 2026 07:17 AM AEST | BUY LTC-USD | Position opened | A$1.06 | Best of three momentum signals; score 1.05; Too little closed-trade evidence to adapt |
| 28 Nov 2026 01:15 AM AEST | SELL ADA-USD | A$-4.27 | A$1.06 | Trailing stop |
| 26 Nov 2026 07:14 AM AEST | BUY ADA-USD | Position opened | A$1.07 | Best of three momentum signals; score 1.83; Too little closed-trade evidence to adapt |
| 24 Nov 2026 01:08 PM AEST | SELL BTC-USD | A$-4.49 | A$1.06 | Trailing stop |
| 22 Nov 2026 08:01 PM AEST | BUY BTC-USD | Position opened | A$1.07 | Best of three momentum signals; score 3.57; Too little closed-trade evidence to adapt |
| 22 Nov 2026 02:12 PM AEST | SELL ADA-USD | A$-6.04 | A$1.06 | Trend reversal |
| 22 Nov 2026 07:56 AM AEST | BUY ADA-USD | Position opened | A$1.08 | Best of three momentum signals; score 2.85; Too little closed-trade evidence to adapt |
| 20 Nov 2026 02:19 AM AEST | SELL LTC-USD | A$-6.86 | A$1.06 | Trend reversal |
| 19 Nov 2026 07:24 PM AEST | BUY LTC-USD | Position opened | A$1.09 | Best of three momentum signals; score 1.24; Too little closed-trade evidence to adapt |
| 19 Nov 2026 01:14 AM AEST | SELL ADA-USD | A$-5.76 | A$1.07 | Trend reversal |

## How to interpret

- Prices are from public Coinbase BTC-USD, LTC-USD and ADA-USD markets; AUD is a reference conversion.
- Net liquidation value includes a hypothetical fee and slippage if the current holding were sold now.
- Bid–ask spreads are incorporated in simulated fills and liquidation values; coin entries are avoided above a 0.50% quoted spread.
- The rules automatically decide when to hold cash, buy, sell or pause. Trading more frequently is not necessarily better.
- To reduce overtrading, entries are limited to 2 per rolling 24 hours. Sudden one-hour moves above 2.5% block new entries; this is a cautious anti-chasing filter, not a proven predictive signal.
- The volume indicator is adjusted for recurring UTC-hour patterns in available candle history; it does not assume New York, London or Tokyo hours are automatically profitable.
- Costs assume 0.60% fee and 0.10% slippage **per side**; actual account-specific charges can differ.
- Strategy settings are frozen when the experiment starts. Mid-test config edits are rejected so comparisons cannot be quietly tuned after the fact.
- Trading is simulated, signals are experimental, and 30 days does not prove consistent profitability.
- If you ask ChatGPT for a check-in, provide the *public repository URL* once, then ask it to read `CHECKIN.md` or `data/checkin.json`. ChatGPT reads reports on request; this chat itself does not continuously run or watch the trader.
