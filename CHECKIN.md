# Paper trader — ChatGPT check-in

> PAPER TRADING ONLY. No Coinbase account connected. No real orders.

Last market check: **16 Nov 2026 02:55 AM AEST**. If this time is not recent, the runner may be paused or failing — **do not present stale data as live**.

**Status:** ACTIVE (from 13 Nov 2026 08:59 AM AEST to 13 Dec 2026 08:59 AM AEST)  
**Last decision:** HOLD CASH: no qualifying signal with acceptable bid–ask spread

| What to report | Current simulation |
|---|---:|
| Starting balance | A$1,000.00 |
| Current estimated liquidation value | **A$1,000.00** |
| Net profit or loss, including estimated exit costs | **A$0.00 (+0.00%)** |
| Simulated cash available | A$1,000.00 |
| Current holding | None (all cash) |
| Realised profit or loss on completed trades | A$0.00 |
| Estimated fees paid to date | A$0.00 |
| Completed round-trip trades (winners) | 0 (0) |
| Current drawdown from recorded peak | 0.00% |
| Worst observed peak-to-trough drawdown | 0.00% |
| Current portfolio exposure | 0.00% |
| Estimated risk limit per new trade, not guaranteed | 1.00% |
| Closed-trade win rate | Not enough trades |
| Net mean per completed trade | Not enough trades |
| Fees + bid–ask effects + extra slippage estimate | A$0.00 |
| BTC passive reference liquidation | A$897.01 |
| Desired monthly net profit (not guaranteed) | A$50 to A$100 |

## Regional market-clock context

**Current stock-hours proxy:** Outside stock-hour windows. Tokyo Mon 01:55 JST, London Sun 16:55 GMT, New York Sun 11:55 EST.  
**Weekend by UTC:** Yes. Stock markets have holidays and closures; the agent does not check those calendars. **Crypto is open 24/7**. This context does not trigger a purchase or promise better results.

| Entry window | Completed trades | Net profit/loss |
|---|---:|---:|
| No completed trades | 0 | — |

## Latest recorded trade signals

Signals were last recorded: **16 Nov 2026 02:55 AM AEST**.

| Permitted coin | Entry status | Signal score | RSI(14) | 24-hour momentum | Same-hour relative volume |
|---|---|---:|---:|---:|---:|
| BTC-USD | No signal | -100.00 | 67.4 | -1.50% | 0.76× |
| LTC-USD | No signal | -100.00 | 69.5 | -2.83% | 0.83× |
| ADA-USD | No signal | -100.00 | 77.6 | -2.55% | 0.89× |

## Most recent transactions

| Brisbane time | Action | Closed net P/L | Estimated fee | Explanation |
|---|---|---:|---:|---|
| — | No trades yet | — | — | Awaiting a qualifying signal |

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
