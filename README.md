# Standard Reserve Monitor

An independent on-chain monitor of the Standard Reserve protocol on Robinhood Chain: reserve assets and backing, revenue by stream, the
liquidity business in the reserve's own pools, the launchpad and King of the Markets, STANDARD supply, burns and holder flows, banks,
branches, the Auction House and S-Bills. Live at https://standardrsvmonitor.github.io/.

## Sources and method

Figures are rebuilt from Robinhood Chain logs and balances (public RPC) and the Standard Reserve indexer and markets API, with prices from
GeckoTerminal (daily closes), DexScreener (live) and Coinbase (ETH). Every panel's ⓘ note gives its method. Between compiles the page
replays the blocks after the compile in the browser, so tiles, the current day and the top bankers describe the latest block.

## Publication and checks

GitHub Actions compiles the page every 30 minutes. A compile is published only when `qa/check.py` passes:

- **Reconciliation.** Each rebuilt figure is set against an independent reading of the same quantity: balances read directly at the compile
  block, the indexer, GeckoTerminal, DexScreener and Coinbase. The results are on the Data tab and in `api/recon.json`.
- **Consistency.** Every figure shown in more than one place reads the same, and headline totals match a separate recomputation.
- **History.** No figure for a day three or more days old may move from the published page unless a dated entry in `qa/accept.json` explains why.
- **Freshness and completeness** of the last complete day, and the house style (every chart follows the range selector, nothing clipped).

A failing check keeps the previous page up and opens an issue labelled `qa-gate`.

## Open data

Published with every compile: `api/daily.csv` and `api/daily.json` (every daily observation, with field definitions), `api/summary.json`
(every tile and panel headline), `api/recon.json` and `api/qa.json`. They are written from the rendered page, so every figure matches it.

## Code

`pull.py` and `extra.py` collect into `data/dash.json` (incremental caches in `data/cache/`), `build.py` renders `index.html`,
`qa/render.py` renders it in headless Chrome and writes the open data, `qa/check.py` is the gate, `qa/watch_sr.py` watches the protocol's
site for new contracts. Standard library Python only. Working rules for contributors and the scheduled agent: `CLAUDE.md`; backlog: `ROADMAP.md`.
