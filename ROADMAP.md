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
