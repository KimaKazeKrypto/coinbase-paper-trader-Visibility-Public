# Pre-deployment review — 13 November 2026

**Verdict: ready for a 30-day, read-only PAPER-TRADING experiment after deployment, not validated as profitable or safe for real-money use.** No Coinbase login, API key, wallet or order-placement function is present.

## Prioritised changes actually made

| Priority | Change | Purpose |
|---|---|---|
| Critical | Reject missing hourly candles and stale or invalid order-book ticker data | Avoid acting on misleading prices and indicator histories |
| Critical | Recheck simulated stop and portfolio drawdown using fresh prices, even on a repeated candle | Avoid skipping exits when prices change but the signal candle has not |
| Critical | Use quoted best ask on simulated buys, best bid on simulated sells, plus extra slippage and fees | Avoid flattering results by assuming every trade happens at the last-trade price |
| High | New-entry position sizing using a 1% modeled account-loss budget and 35% absolute exposure cap | Limit single-trade damage under modeled stop and cost assumptions; **not a guaranteed loss ceiling** |
| High | Stop opening fresh trades when spread exceeds 0.5%, or when last hour moved over 2.5% | Avoid illiquid fills and chasing sudden jumps; entry filters are NOT proven return signals |
| High | Limit fresh buys to two per rolling 24 hours; keep cooldown and one coin held at a time | Reduce transaction-cost churn and overtrading |
| High | Halt at 8% simulated portfolio drawdown and pause new purchases after 2% estimated daily decline | Restrict how far the experiment can continue taking exposure; price gaps can exceed these targets |
| High | Freeze every strategy parameter when the first run begins; freeze final 30-day report and BTC benchmark | Prevent tuning rules to make the record look better or comparing different dates |
| Medium | Keep Tokyo/London/New York clocks and same-UTC-hour volume normalisation | Contextual analysis, not a claim of session-specific profits |
| Medium | Compare against BTC buy-and-hold after costs, and show expectancy, profit factor and worst observed drawdown | Distinguish actual net results from apparent wins |

## Trading economics to keep in mind

- The objective of A$50–A$100 profit from A$1,000 equals **5%–10% in one month**, after fees, a high-risk ambition rather than an expected monthly income.
- The simulator assumes a **0.60% taker fee + 0.10% additional slippage each side**: approximately **1.40% of each round-trip position notional before bid–ask spread**, even if the coin does not change value.
- Real account-specific Coinbase fees may differ. The program uses USD trading-pair quotes converted to AUD at a public daily **reference rate**, not real AUD executable prices. Actual conversion spreads, transfer costs and taxes are not modelled.
- A paper fill against the displayed best bid or ask does not prove there would be enough market depth, stable prices or matching liquidity for a real trade at that level.
- The rough 1% planned account-loss budget cannot prevent larger losses from price gaps, delayed schedules, failed data feeds, or market dislocations.

## Features deliberately left out

- **Social-media sentiment**, influencer-driven signals and automatic round-number trades: no verified incremental edge, easy to overfit or manipulate.
- **Training an ML predictor on one month of data**: an inadequate sample; outcome-based sizing only reduces exposure and cannot be labelled learned alpha.
- **Connecting Coinbase trading keys**: intentionally out of scope until a fresh, separately authorised execution security review.

## Acceptance gates

1. Start on GitHub Actions with the intended default configuration, ensure all tests pass and the first *successful market-data run* creates `data/state.json` and a live-sourced `data/checkin.json`.
2. Each scheduled run must show a current `last_checked_utc`; if old, treat the dashboard as stale, not current. Confirm the public Pages site and the ChatGPT-readable report agree.
3. Throughout the pilot, monitor trade count, net return **after all estimated costs**, maximum observed drawdown, stale-feed events, fees, expectancy and BTC/cash benchmarks. No trades is a valid outcome when no acceptable signal exists.
4. At day 30, evaluate the frozen ledger. One profitable month is **not** sufficient to justify scaling to A$10,000: require further prospective months, independent historical out-of-sample testing, higher-cost sensitivity analysis and a separately reviewed live trading design.

Official data and fee documentation:
- https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-ticker
- https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-candles
- https://help.coinbase.com/en-au/coinbase/trading-and-funding/advanced-trade/advanced-trade-fees
- https://frankfurter.dev/v1/
