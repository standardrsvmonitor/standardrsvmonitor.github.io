# Roadmap

The scheduled agent takes the first open item, top to bottom, one pull request per item (see `CLAUDE.md`). Each item says what done means.
Owners may reorder, add or strike items at any time.

## Correctness

- [x] **Pool fee income against the positions' uncollected fees.** On 29 Oct the swap-based totals since seeding ran SPCX +2.1%,
  SKHY −3.6%, BABA +5.3%, ETH/USDG +4.1% against the fees read from the reserve's positions (reconciliation `poolfees_*`, watch, 5%).
  The stock pools are sole-LP, so the gap should be near zero. Find the cause (fee tier, input-side fee, protocol fee, in-range share,
  a position modification that collected fees) and fix the daily figure. Done: every pool within 1%, gate item at 2%.
- [ ] **Ledger balance against the indexer.** The rebuilt ledger ran 8.4K STANDARD (0.08%) above `totalPendingLive` on 28 Oct 08:10 UTC
  and 15.8K (0.16%) on 29 Oct 05:20 UTC, so the gap is growing. Suspects: the contract's recycle (`recycleRate`, `recycleBuffer`,
  `cumulativeRecycled` in the indexer's bank snapshot), how a revocation settles the revoked charter's ledger (two multi-branch charters
  were revoked on 28 and 29 Oct), snapshot timing. Close it or document it in the ⓘ note. Done: within 0.02%, gate tolerance tightened.
- [ ] **Launchpad fees at trade time.** Fee Safe receipts are valued at daily closes and sit about 1% below the markets API's trade-time
  total. Value each receipt at the pool price of its own block. Done: within 0.3% of the API.
- [ ] **Counterparty sampling error.** 150 receipts per pool and day leave about eight points of error on a daily organic share. Read
  every swap's transaction sender for the pools' top executors (exact), sample the rest. Done: stated error under two points a day.
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
