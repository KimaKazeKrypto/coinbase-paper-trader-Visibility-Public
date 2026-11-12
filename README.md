# Coinbase 3-coin paper trading agent — reviewed risk-first edition (BTC, LTC, ADA)

This is a **simulator, not a live trading bot**. It reads public Coinbase
Exchange price data for exactly `BTC-USD`, `LTC-USD` and `ADA-USD` and a public
AUD/USD reference rate. It never connects to your Coinbase account, never
asks for API keys and **cannot submit orders or withdrawals**.

The experiment models **A$1,000 for 30 days**, a maximum of **one coin at a
time**, and starts no trading until you **run/deploy the code**. It tracks net
liquidation equity, every simulated purchase or sale, costs, profit/loss and
signals. The A$50–A$100 monthly goal is merely a benchmark, not a guarantee.

**Review outcome (13 November 2026):** the strategy is ready for a *controlled
paper-trading trial* after you deploy it. It is **not** proven profitable or
ready to handle A$10,000 of real money. A$50–A$100 profit on A$1,000 in one
month means 5%–10% net return per month: an ambitious target that cannot be
made reliable or low risk simply by adding indicators. The safest trade may
be **no trade**.

## Deployment: create an hourly dashboard (no real money)

This project is **not running yet**. To run it for 30 days without leaving a
computer on, we use GitHub Actions to run Python every hour and GitHub Pages
to publish the dashboard. A **public repository** is simplest (only fake trading
records are published). Private repository setup is possible but may require
paid GitHub features and/or connecting ChatGPT's GitHub integration.

1. Download this package, **extract the ZIP**, and create a **new GitHub repository**
   from the contents. On a computer, GitHub Desktop is a convenient way to
   publish the entire extracted directory, **including the hidden `.github`
   folder**. Do not upload personal Coinbase account details or any API keys.
2. In the GitHub repository, open **Settings > Actions > General > Workflow
   permissions** and ensure **Read and write permissions** are allowed for
   GitHub Actions, if the setting is available. That allows the workflow to
   save its paper-trading files in the repository.
3. Open **Settings > Pages > Build and deployment > Source** and choose
   **GitHub Actions**, **not** “Deploy from a branch”. The workflow explicitly
   publishes its own artifact on every run, because workflow-made commits do
   not normally trigger the branch-based Pages rebuild.
4. In **Actions**, choose **BTC + LTC + ADA Paper Trader (NO LIVE ORDERS)**,
   then **Run workflow**. That first **successful** run begins the 30-day
   clock and creates the simulated trading history. Confirm the run shows
   the `simulate` and `deploy` jobs both completed successfully.
5. Your dashboard address will appear under **Settings > Pages** or in the
   deployment job. The site shows the portfolio graph, current balance,
   trades, and a `CHECKIN.md` summary. The repository saves `REPORT.md`,
   `CHECKIN.md` and `data/checkin.json` on each successful run.
6. **Send the public repository link to ChatGPT once.** Then ask, for example,
   “Check my three-coin paper trader — how much is it up or down, what did it
   trade, how reliable were the signals, and is its data current?” ChatGPT can
   read the saved `CHECKIN.md` or `data/checkin.json` **on request** and explain
   the results. If you want a private repository, connect an appropriate
   GitHub app or share the report in your chat instead.

The scheduled workflow targets hourly runs at minute 17 UTC. GitHub may delay,
skip, or disable schedules; check the “last checked” time. The assistant in
ChatGPT **cannot keep the bot running just by leaving this chat open** and
will not silently place trades or monitor it between check-ins.

### Important initial files

- `index.html`: the public dashboard after deployment; before the first run,
  it accurately says “not started”.
- `CHECKIN.md`: short, human-readable report designed for ChatGPT check-ins.
- `data/checkin.json`: machine-readable snapshot with current value, latest
  decision, signal scores, fees, profits and recent simulated trades.
- `REPORT.md`, `data/trades.csv`, `data/hourly_history.csv`: full audit trail.
- `data/state.json`: the **persistent simulation state**. Do not delete it or
  it will reset the test. This is not a Coinbase account wallet.

## Local start

Use Python 3.11+, a working internet connection, and run:

```shell
python -m unittest discover -s tests -v
python paper_agent.py
```

Each subsequent run uses the **same persisted state**; it doesn't replay old
hours it missed. A SHA-256 fingerprint freezes *all* settings after the initial
run. Editing any setting mid-experiment stops the run rather than silently
altering the strategy. To conduct a separately configured experiment, use a
different folder/repository; never erase an active test to improve its results.

## How the signals work

- Every hour, inspect the latest **closed** Coinbase Exchange candles from all
  three USD markets, without predicting future candles. Reject gaps in the
  last 120 hours of data and ticker prices over five minutes old.
- Compare EMA(9), EMA(26), RSI(14), volume relative to the last 24 hours,
  24-hour momentum, and recent hourly volatility. Reject fresh entries when
  the last closed candle swings more than 2.5% in one hour (an experimental
  anti-chasing safety filter, **not** a proven predictive edge).
- If holding a coin, obey stop-loss, trailing-stop, take-profit and trend
  reversal rules first. No second coin can be bought while a position is open.
- Stops and drawdown checks evaluate each *fresh ticker* even if a run sees
  no new closed candle. This fixes a prior hole where repeated runs within
  the same hour could overlook price-based exits.
- If all cash and past the cooldown, buy only the **strongest qualifying**
  coin with a bid–ask spread of at most 0.50%. Or hold cash if none qualifies.
  One position only. New allocations cannot exceed 35% of equity, and a
  separate cost-aware risk budget typically limits an entry to **about 18.5%**
  of the portfolio under default assumptions. No more than **two new buys
  within a rolling 24-hour window**.
- The entry risk budget aims to limit loss at the modeled stop to **1%** of
  the whole paper portfolio, including assumed fees, slippage, and spread.
  Because executions are only checked periodically and prices can jump, that
  is **not an enforceable maximum loss**.
- After **six** completed trades in the same coin, weak results can only
  **reduce** sizing. Too few outcomes do not justify an optimistic increase.
- At 30 days, any open position is sold in the *simulation* and the program
  stops making new paper trades. After FINISHED or HALTED_DRAWDOWN, the saved
  result **freezes**, including the BTC comparison, even if GitHub keeps
  scheduling the workflow.

**This version is a rules-based adaptive system, NOT a trained predictive
machine-learning model.** A month is a very short sample and cannot establish
predictability or consistent returns. Later ML work requires separate
out-of-sample validation and trading-cost controls.

## Costs, caveats, and protection

Defaults are **0.60% estimated taker fee + 0.10% estimated extra slippage each side**, **plus bid–ask effects** when simulated fills use Coinbase's quoted
best ask for buys and best bid for sells. The approximate minimum round-trip
friction *before the spread* is therefore **1.40% of position value**.
Coinbase's actual fees depend on your account, order type, country and fee tier.
Edit `config.json` if you verify the correct rates; don't assume these are
Coinbase's guaranteed rates. **Do not edit settings after the trial has begun.**
AUD prices are USD quotes divided by a public
AUD/USD reference rate (not real executable AUD order prices); FX conversion
spreads and transfer costs aren't included. Simulator fills are simplified,
so realised live results can be much worse. Taxes are not modelled.

Simulated total equity includes an **estimated exit fee and slippage** on the
open coin so reported gains aren't inflated by ignoring selling costs.
At an estimated **8%** peak-to-trough loss the agent halts, and a **2%** daily loss
prevents fresh buys for the current UTC day. Hourly checks can't guarantee a
stop order would execute at its trigger; gaps can exceed stop levels.

### Serious investor checks and evidence gate

The reports show realised closed-trade profit/loss, *after-fee* portfolio
equity, estimated execution friction, win rate, average net profit per closed
trade (expectancy), profit factor when defined, peak-to-trough drawdown,
Bitcoin buy-and-hold comparison, exposure, and market-session outcomes.
Small samples can make win rate, profit factor, and session comparisons
misleading; absence of losing trades is **not** proof of an infinite profit
factor. A 30-day paper run tests the technology and produces an early
prospective sample. Before considering real funds, we'd require longer
forward testing, independent out-of-sample historical tests across different
market conditions, higher-fee/slippage sensitivity, market data reliability,
and a separately reviewed real-money execution architecture.

**Not added:** social media sentiment, influencer mentions, round-number
trading triggers, or a black-box machine-learning model. Their incremental
value has not been validated. They're more likely to introduce noise and
overfitting during the first month than make A$50/month dependable.

Never connect real Coinbase keys to this prototype. The public-data endpoints
are read-only. If you later want live trading, that would require a separate
reviewed and separately permissioned execution system with hard account limits.

## Coinbase connection later — separate project, never automatic

The paper-trading strategy reads Coinbase **public** prices and stores only
virtual balances. It does **not** contain any code that can authenticate to
Coinbase or place actual trades. It was designed with separately stored
signals, decision logs and simulated fills so we can **review and reuse the
research** if you later approve an optional live execution module.

A live trading upgrade would require a **separate review and your explicit
approval**, account-specific fee checks, and new tests with very small
position sizes. Coinbase Advanced Trade describes **portfolio-scoped CDP API
keys**: ideally you would use a separate Coinbase portfolio with a strictly
scoped `view/trade` key, **no transfers or withdrawals**, an IP allowlist if
supported, exchange-side limits where available, and a separate kill switch.
Never place Coinbase credentials in this public GitHub repository, its Pages
website, or a message to ChatGPT. Even a portfolio-scoped key is not proof of
all restrictions; the execution layer must reject unsupported coins and
transactions itself. This package deliberately has **no live-trading switch**.

Source: https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/guides/portfolios

## Notes about ChatGPT check-ins

When you ask for a check-in, ChatGPT should verify **as-of time** and report:

- Current simulated equity and profit/loss **after estimated exit costs**.
- Total estimated fees, completed trades and whether an open position exists.
- Latest simulated decision and the relative strength of the BTC/LTC/ADA
  signals; what information *was* and *was not* demonstrated.
- Maximum drawdown, target comparison, and any stale-data or failed-schedule
  warning.

This is a human-readable **status reporting capability**, not a ChatGPT-native
continuous live dashboard. A successful single month does not demonstrate
repeatable returns or safe real-money trading.
