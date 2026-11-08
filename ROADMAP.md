# Roadmap

The scheduled agent takes the first open item, top to bottom, one pull request per item (see `CLAUDE.md`). Each item says what done means.
Owners may reorder, add or strike items at any time.

## Correctness

- [ ] **Readability pass, every chart and table.** The owner found two charts that read backwards on 29 Oct (bank deposits looked automatic;
  net sales plotted upward looked like buying). Go through every panel against the readability rule in `CLAUDE.md`: what a holder would
  conclude from the chart alone, without the ⓘ note, must be true, and nothing visible may be redundant (the concision rule in
  `CLAUDE.md`; the owner trimmed tooltips, tile lines and headlines on 29 Oct). Fix signs, labels, colours and wording; no restyling. Done: one
  pull request listing each panel checked, what a reader would have concluded before, and what changed.
- [x] **Pool fee income against the positions' uncollected fees.** On 29 Oct the swap-based totals since seeding ran SPCX +2.1%,
  SKHY −3.6%, BABA +5.3%, ETH/USDG +4.1% against the fees read from the reserve's positions (reconciliation `poolfees_*`, watch, 5%).
  The stock pools are sole-LP, so the gap should be near zero. Find the cause (fee tier, input-side fee, protocol fee, in-range share,
  a position modification that collected fees) and fix the daily figure. Done: every pool within 1%, gate item at 2%.
- [ ] **Ledger balance against the indexer: the recycle buffer.** Cause found 29 Oct: the stayers' cut (half of every exit and revocation
  fee) is not credited to banks at once; the bank parks it in a recycle buffer and releases it gradually (indexer bank fields `recycleBuffer`,
  `cumulativeRecycled`, `recycleRate`). The rebuild credits it immediately, so it runs ahead by what sits in the buffer: on 29 Oct the buffer
  held 15,153 STANDARD against a 15,716 gap, and recycled plus buffer (349,236) matches the stayers' cut credited (349,531). Model the buffer:
  read the release rule from the bank contract, credit the stayers' cut as it is released, and show it in the bank flows chart as released.
  Done: ledger within 0.02% of `totalPendingLive`, gate tolerance tightened to 0.05%.
- [ ] **Launchpad fees at trade time.** Fee Safe receipts are valued at daily closes and sit about 1% below the markets API's trade-time
  total. Value each receipt at the pool price of its own block. Done: within 0.3% of the API.
- [ ] **Counterparty sampling error.** 150 receipts per pool and day leave about eight points of error on a daily organic share. Read
  every swap's transaction sender for the pools' top executors (exact), sample the rest. Done: stated error under two points a day.
- [ ] **Venue discovery on chain.** The "share of chain volume" and "share of chain liquidity" panels start from DexScreener's pair list.
  Discover every pool holding SPCX, SKHY, BABA or ETH against USDG or WETH from PoolManager Initialize events and pool-factory events
  instead, and keep DexScreener only as a cross-check. Done: no aggregator in the venue scan.
- [ ] **POL buyback ETH that routing did not send.** On 4 Nov 2026 the POL buyback held 275.86 ETH against 0.046 ETH left from the
  477.05 ETH routed to it (it spent 477.0 ETH in 79 ticks of 6 ETH, one of 9). No event log on the contract, the fee splitter, the team,
  reserve or owner Safes shows the source; the public RPC has no trace or archive methods and the explorer is behind Cloudflare. Watch
  `routed_pol` shows the gap. Find the source (a trace-capable RPC, or the deployment transaction) and say in the routed ETH note what it is.
- [ ] **Outage behaviour.** When the indexer, an API or the RPC fails mid-pull, the pull must fail loudly (and the gate keep the last good
  page) rather than publish partial data. Add a test that simulates each source failing.

## Depth: entities

- [ ] **Charter register.** Every charter: id, owner, founding or auctioned, price paid, date, branches now, licenses bought, emissions,
  withdrawals and exit fees paid, revoked or burned. Sortable table on Banks, open data file `api/charters.json`.
- [ ] **Banker profile by address.** Search box on Banks: an address shows its charters, branches, ledger balance, emissions this epoch and
  lifetime, deposits, withdrawals, S-Bills, STANDARD held and traded with the pool, and launchpad activity. Static index file per compile
  plus the live overlay for the current block.
- [ ] **Event tape.** One chronological table of protocol events: charter purchases, license periods, deposits, withdrawals with their
  resolution fee, revocations, epoch settlements and routing, S-Bill entries and exits, reserve Safe transactions, large pool swaps.
  Filter by kind, link every row to its transaction. Data tab, open data file `api/events.json`.
- [ ] **Holders.** Full STANDARD transfer scan (today only protocol-side transfers are read): holder count by day, distribution by
  size band, top holders with group labels (team, bankers, S-Bill holders, protocol contracts), concentration. Token tab.
- [ ] **Founding charter allocation.** The protocol's site bundle (`mountApp-*.js`) carries a map of 108 wallets to numbers near its
  charter-drop code. First establish what it is against chain data (charter NFT mints, the founding charter ids). If it is the founding
  allocation, show who received founding charters and what they did with them (kept, opened branches, withdrew, sold STANDARD).
- [ ] **Epoch drilldown.** Per epoch: net flow by holder group, routed split, multiplier step, issuance, burns, withdrawals, charter and
  license sales. Selecting an epoch in the routing chart fills a detail table.
- [ ] **Auction House depth.** Every charter and license sale against the Dutch decay curve: minutes after open, price relative to the
  opening price, buyer, payback period at the issuance in force.
- [ ] **Reserve Safe ledger.** Every Safe transaction, MultiSend decoded: what moved, to whom, signers, and its effect on reserve assets.
- [ ] **Launchpad tokens.** Every launched token: creator, launch date, bonding-curve progress or graduation, volume, fees by recipient,
  holders. King of the Markets by trader once the season closes on 4 Nov 18:00 UTC.
- [ ] **Pool microstructure.** Per reserve pool: swap tape, the reserve's ranges against other liquidity, in-range time, fee share lost
  to concentrated or just-in-time liquidity.
- [ ] **S-Bill ledger.** Every bill: principal, rate at entry, maturity; a maturity ladder of principal coming due.
- [ ] **Exit pressure.** The contract's seven protocol-day withdrawal buckets, who withdrew, and the resolution fee path against the 10%
  threshold.

## Depth: access

- [ ] **90D and 180D range settings.** Add 90D once 90 complete days of history exist (13 Dec 2026) and 180D at 180 days (13 Mar 2027).
  Every chart, the growth monitor (a 90- or 180-day window against the one before, compared only when that earlier window is complete
  and after the launch epoch), Revenue by destination and Counterparty mix already take the window from the range. Done: the buttons
  appear on those dates, the range sweep in `qa/render.py` covers them, and the gate passes. (Sonnet)
- [ ] Per-chart CSV download from the ⓘ note, using the chart's own data. (Sonnet)
- [ ] Permalinks to panels (`#p_<id>`) shown in the method note. (Sonnet)
- [ ] Open data files for every new entity table, each with field definitions.

## Findings (facts later runs rely on)

- 29 Oct 2026: GeckoTerminal daily candles were cached the first time a day appeared (mid-day) and never refreshed; 20–27 Oct closes were
  published up to 6.6% off. Fixed in `pull.py` (fresh candles overwrite) and reconciled daily against the pool's own last trade × Coinbase.
- 29 Oct 2026: the protocol's site names three contract sets: genesis (charter auction 0x65B4…, never sold a charter; license auction
  0xA45C…, 692 purchase events), the 22 Sep 00:19 UTC upgrade (license auction 0x4473…, 487 events) and the 26 Sep 23:25 UTC upgrade
  (charter auction 0x1E36…, license auction 0x7CD3…, current). The indexer's license events cover all three exactly; charter sales all fall
  on the current auction. `qa/sr_contracts.json` is the reviewed snapshot.
- 29 Oct 2026: a revocation destroys the whole charter, every branch, not one branch (the indexer's `revoked` event carries no count).
  The replay had counted one, which matched until multi-branch charters 641 (4 branches) and 492 (5) were revoked on 28 and 29 Oct;
  the page then overstated branches by 7 and charters by 2. Fixed; reconciled each compile against the census and per banker against
  the leaderboard.
- 29 Oct 2026: pool fee income is replayed swap by swap (`extra.pool_fees`, cache `pool_fees.json`): each swap walked tick by tick against
  every provider's liquidity rebuilt from ModifyLiquidity events, fee on the input token, split by in-range liquidity. The replay's
  uncollected fees match the positions to within 0.001% in all four pools and its liquidity matches every Swap event's (0 mismatches). The
  old 2–5% gaps were valuation, not missing fees: in the stock pools the in-range-share estimate was within 0.5% of trade-time fees, but
  the positions' reading values the stock-side fees at today's price (BABA 7,425 USD at trade time against 7,001 today). ETH/USDG also
  carried a final-tick share error and the fees settled by the 14 Oct 2026 liquidity add (0.0097 ETH, 26.00 USDG). The RPC keeps no
  historical state (eth_call at old blocks fails), so the replay's starting tick map is today's map with every change since seeding
  undone. A rebuild takes about 7 minutes and can outlast the compile block's state, so the cache is committed.
- Block dating (2 Nov 2026). Robinhood Chain's block times are irregular, and dating blocks by interpolating between anchors 100,000 blocks
  apart put swaps near midnight on the wrong day: the swap cache and the venue scan, dated with different anchor sets, disagreed by one
  swap at the 30/31 Oct boundary (ETH/USDG 675 USD, SPCX 2,200 USD) and the 1/2 Nov boundary (SKHY 3,926 USD, gate held 00:21 to the fix).
  Each run now reads the first block of every UTC day and the block before it (`day_anchors` in `pull.py`, `data/cache/midnights.json`),
  so interpolation can never cross a midnight. The day-keyed caches written at scan time were rebuilt under new names (`venue_v4b`,
  `venue_v4liqb`, `venue_custb`, `pool_fees3`, `pool_close2`); `cpty.json` was kept because its classes are scaled to the exact volume served each
  run, and `launchpad.json` because it dates most transfers by the log's own block timestamp (open: rebuild it for the days the RPC
  returned blockTimestamp 0x0, which fell back to interpolation). Any new cache that stores days computed at scan time must be built after `day_anchors` runs.
- STANDARD trading fees (2 Nov 2026) come from the tax hook's TaxCollected and LpTaxCollected events, dated by block (82,598 events,
  2,903.81 ETH to 2 Nov). The routed reading (each epoch's routed ETH less charter sales, plus ETH not yet routed) is 2,907.02 ETH: 3.2 ETH
  (0.11%) more, unexplained so far, kept as a watch item (`tax_logs`). Open: find what else reaches the fee splitter, then make it a gate.
- STANDARD pool LP fees (2 Nov 2026): the 1% pool fee earned by the protocol's own two positions in the STANDARD/ETH pool (owner: POL
  manager; ticks -887200..115000 and 115000..115200, salt 0), replayed swap by swap at the share of active liquidity they held
  (`extra.std_pool_fees`, cache `std_fees.json`). Both sides go to the team wallet at each harvest: FeesHarvested (topic 0x5f8f8abb) from
  the POL manager, STANDARD by transfer, ETH logged by the team wallet as received. Replay 243.1151 ETH and 2,062,931 STANDARD against
  harvests (100) plus uncollected 243.0875 ETH and 2,062,938 STANDARD: gate items `stdlp_eth` and `stdlp_std` at 0.1%.
- License purchases move no STANDARD from the buyer's wallet: the central bank debits the charter's bank balance and the token lowers
  its cap by the price. Lifetime licenses 24.68M exceed lifetime deposits 16.30M, so at least 8.4M came from issued balances.
- 3 Nov 2026: the reserve Safe re-ranged at 07:05 UTC (tx 0x75eae165…): it removed and burned positions 3789188 and 3789189 and minted
  4154479 to 4154481 in one transaction. The reserve history and pool P&L had counted only positions the Safe still owns, so the burned
  positions vanished from every day back to 14 Oct (BABA LP value and cost −15%) and the gate held the page from 07:27 UTC. Both now use
  every position the Safe has held (`positions.json`); `lp_liquidity` still checks the summed liquidity against the positions held now.
- The stock pools' hook (0xc15b155a…6080, owner EOA 0xb1748f18…c3c1) keeps a fee-exemption list, event FeeExemptSet(address,bool)
  (topic 0x5a8cf666…). Exempt swaps report fee 0 in the Swap event; everyone else pays 2900 pips in SKHY and 450 in SPCX. History:
  14 Oct 14:55 UTC 0x4dbd3fe6, 0xce5be7b4, 0xc348f695, 0x6353e3ec exempted; 19:50 the last three removed; 21 Oct 05:52 0x922ec650 added;
  30 Oct 14:08 0xce5be7b4, 0xc348f695 (the largest bot executor) and 0x6353e3ec exempted again. Since then most stock-pool volume pays
  nothing: 2 Nov $5.21M of $6.45M served was fee-exempt and LP fees were $727 (27 to 29 Oct averaged $6,358 a day).
- 3 Nov 2026: the swap replay keeps a sixth daily figure, the volume served to senders on the hook's fee-exemption list (fee 0), cache
  `pool_fees4.json` (rebuilt from the seeding blocks in 607 s, 0 liquidity mismatches, every earlier figure identical to `pool_fees3`).
  The volume chart's headline is the volume that paid the fee; the counterparty mix takes its fee-exempt class from the replay and scales
  the sampled classes to the rest; watch item `exempt_served` compares the replay with the counterparty pass (0.08% apart on 3 Nov).
- 3 Nov 2026 accuracy audit, fixed:
  - Resolution fee history counts revoked balances in the seven-day buckets (the contract's withdrawnOnDay does), so every feeWad on chain is reproduced exactly.
  - In banks credits the stayers' cut as it streams: FeesRecycled(epoch, amount) (topic 0xee894dd5…), spread evenly over that epoch; the live epoch uses recycleRate. The ledger now ties to totalPendingLive within 4 STANDARD and is gated at 0.02%.
  - License periods are keyed by auction contract (`lic_logs2.json`): 93 periods, previously 76.
  - charterNft.nextId() is the last id minted, not the next one.
  - Epoch settlement and routing events are paired by transaction.
  - Chain liquidity per asset counts v4 liquidity added before 14 Oct.
  - Reserve positions are read at the compile block.
  - The pools table shows the fee each pool charges now (450 / 2900 / 900 pips for SPCX / SKHY / BABA; 500 for ETH/USDG), and APR follows the range.
  - The live overlay retries the RPC and keeps the whole page compiled when the chain replay fails.
  - New watch `served_cp`: replay against counterparty-pass served volume.
- The stock pools are not sole-LP: SPCX has 27 live third-party positions, the largest 19 times the reserve's in-range liquidity (3 Nov).
- 3 Nov 2026 audit, token batch:
  - Minted from banks splits into net withdrawals and revocation payouts (bounty plus owner net); watch item `mint_split` is exact.
  - Buybacks burned counts the contraction vault only; S-Bill fee burns and the POL manager's 4.34 launch-day burn are `burnFees`.
  - Live overlay fixes: tax-hook burns are included (the replay names the hook taxHook), and the complete-day window moves past midnight.
- Open for the owner, 3 Nov 2026:
  - Protocol liquidity is the PoolManager's whole STANDARD balance, as the protocol's own site defines it. That balance also holds third-party liquidity and other pools' STANDARD, about 86K to 402K, so In wallets reads 0.2% to 0.76% low.
  - The S-Bill premium pot (1.15M funded by the Incentives vault) sits inside In wallets, as on the protocol's site.
- 3 Nov 2026 audit, launchpad batch: launchpad figures come from every trade's Trade event (topic 0xaca20ddd…, from curves and launch
  hooks; data words 4 to 8 = side, total fee, creator, fee Safe, snipe), cache `lpad_trades.json` (seeded from the auditor's full scan,
  verified against the chain; launches from the factories' events 0xa0354dae…/0x93e9aed1…). Volume is the traded side (snipe fees had
  inflated the implied volume 9%, 30% on 14 Oct); snipe fees are all the protocol's, per its fee table (launchpad revenue +$5.4K to date);
  days are dated by block; gate `lpad_trades` ties the trades' fee Safe part to the Safe's Transfer receipts (exact). The Safe's native ETH
  (launch fees, 0.0005 ETH a launch) shows in its holdings and is not counted as revenue (owner decision pending).
- Open: launchpad-routed LP fees remain a floor; matching reserve-pool swaps to Trade events by transaction would make them exact
  (creator buys in launch transactions, 1,271 swaps, and trades through other routers are missed).
- Routed ETH by use (4 Nov 2026; first in, first out by epoch since 5 Nov, shown inside Revenue by destination): `extra.routed_use` follows
  every settlement's routed ETH and the genesis seed (111.72 ETH to each vault) to its use; `epochs[].use` holds each epoch's split. The reserve Safe sold 1,682.3 ETH for 4.25M USDG in five swaps (2, 13, 14 Oct), paid 2.55M USDG to 0x3cf569a9 for stock
  tokens delivered by 0x8aeaca1e on the same days (3,461.7 SPCX, 6,233.8 SKHY, 8,698.2 BABA), and has bought none since 14 Oct. The
  contraction vault's 85 buybacks burned 5.04M STANDARD for 456.7 ETH. The POL buyback sends every STANDARD it buys to the Incentives vault,
  which holds nothing else (gate `routed_incentives` exact); the vault paid 1.5M (1 Oct) and 250K (30 Oct) to the S-Bill premium budget,
  1.0M to branch claims (0x6FfC470f) and 89.5K to branch top-ups (0x4a97f28A), named in the site bundle, and 40,179 to one wallet. The
  protocol's S-Bill page says bought-back tokens top up the budget each epoch; the chain shows two top-ups in eleven epochs.
- Beans's "King of the Markets" share chart (4 Nov 2026) counts only Uniswap v4 stock/USDG pools as Robinhood Chain trading; our venue
  data reproduces it (SKHY 98.9%, SPCX 88.2% for the week to 2 Nov). The other venues are real trading (the Uniswap v3 SPCX/USDG pool's own
  Swap events match our flow method to the dollar on 2 Nov; 287 of its 11,488 transactions also touched the reserve pool).
- DexScreener's token-pairs list drops pools as their liquidity falls (8 Nov 2026: a SKHY/USDG v4 pool, 0x0df0a8bf, with $25K of SKHY
  volume on 17 Oct). The venue scan now reads `data/cache/stock_venues.json`, every pair ever listed per asset, so a dropped pool's past
  volume and liquidity stay in chain volume and venue counts; `stock_pairs.json` (today's list) still feeds the live market context only.
