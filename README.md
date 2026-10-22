# Standard Reserve Protocol Monitor

Daily monitor of the Standard Reserve protocol on Robinhood Chain: token price and market capitalization, fee income by source, the liquidity business in protocol-owned pools, charter and license auctions, reserve assets, supply and float reconciliation, and the banking system.

Data is pulled from the Standard Reserve indexer, Robinhood Chain RPC, DexScreener, GeckoTerminal and Coinbase, rebuilt from on-chain events and transfer logs, and refreshed every day at 00:15 UTC by GitHub Actions. `pull.py` collects data into `data/`, `build.py` renders `index.html`. Standard library Python only.
