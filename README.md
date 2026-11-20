# Standard Reserve Monitor

An independent on-chain monitor of Standard Reserve on Robinhood Chain. [Open the dashboard](https://standardrsvmonitor.github.io/).

Overview opens on seven complete UTC days. Treasury groups underlying asset exposure, reserve changes, Safe transactions and pool performance. Revenue retains launchpad history alongside fees and noncash license cancellations. Token covers issuance, supply, S-Bill maturities and modeled sale proceeds. Banks covers participation and auctions. Data provides the daily ledger and downloads.

## Sources and method

Figures are rebuilt from Robinhood Chain logs and balances (public RPC) and the Standard Reserve indexer, with STANDARD's price from
its own pool on chain (daily closes) and DexScreener (live), ETH from Coinbase, and GeckoTerminal as a cross-check. Every panel's ⓘ note gives its method. Between compiles, market and banker readings update after the browser verifies their inputs. Treasury, liquidity, bill maturities and accrued fees carry compile-block marks. A failed refresh, UTC rollover or new epoch returns the page to the compiled snapshot until the next complete build.

## Publication and checks

GitHub Actions compiles the page every 30 minutes. A compile is published only when `qa/check.py` passes:

- **Reconciliation.** Each rebuilt figure is set against an independent reading of the same quantity: balances read directly at the compile
  block, the indexer, GeckoTerminal, DexScreener and Coinbase. The results are published in `api/recon.json` and `api/qa.json`, linked from the Data tab.
- **Consistency.** Every figure shown in more than one place reads the same, and headline totals match a separate recomputation.
- **History.** No figure for a day three or more days old may move from the published page unless a dated entry in `qa/accept.json` explains why.
- **Freshness and completeness** of the last complete day, and the house style (every chart follows the range selector, nothing clipped).

A failing check keeps the previous page up and opens an issue labelled `qa-gate`.

## Open data

Published with every compile: `api/daily.csv` and `api/daily.json` (every daily observation, with field definitions), `api/summary.json`
(every tile and panel headline), `api/investor.json` (asset exposure, bill maturities, execution scenarios and Safe history), `api/recon.json` and `api/qa.json`. They are written from the rendered page, so every figure matches it. Field names follow the page's vocabulary (circulating supply and market cap as the protocol defines them, revenue as what the protocol keeps).

## Code

`pull.py`, `extra.py` and `stewardship.py` collect into `data/dash.json` (incremental caches in `data/cache/`), `build.py` renders `index.html`,
`qa/render.py` renders it in headless Chrome and writes the open data, `qa/check.py` is the gate, `qa/watch_sr.py` watches the protocol's
site for new contracts. Standard library Python only. Working rules for contributors and the scheduled agent: `CLAUDE.md`; backlog: `ROADMAP.md`.
