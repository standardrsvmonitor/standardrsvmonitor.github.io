#!/usr/bin/env python3
"""Render data/dash.json into index.html (single file, charts via Chart.js CDN, hero image embedded)."""
import json, os, base64, datetime as dt
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
data = json.load(open(os.path.join(D, "dash.json")))
hero_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "reserve-dam.webp")
hero = "data:image/webp;base64," + base64.b64encode(open(hero_path, "rb").read()).decode() if os.path.exists(hero_path) else ""
built = dt.datetime.utcfromtimestamp(data["pulledAt"])
kst = built + dt.timedelta(hours=9)

TEMPLATE = r"""<meta charset="utf-8">
<title>Standard Reserve Monitor</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap">
<style>
/* Layout: full-bleed hero fading into a dark lavender-black page; sticky section nav; KPI strip; two-column panels of charts and tables. */
:root{
  --bg:#0e0c15; --panel:#161321; --panel2:#1c1829; --line:rgba(190,172,232,.14); --line2:rgba(190,172,232,.26);
  --fg:#f2eefb; --muted:#a79ec4; --dim:#6f6690;
  --gold:#ffdd8a; --gold2:#deb553; --lav:#b9a6e3; --peri:#8fa2f0; --peach:#f3b690; --rose:#e9b7d4; --water:#cdbdf0;
  --green:#a8c79a; --red:#e5484d;
  --sans:"Instrument Sans",ui-sans-serif,system-ui,-apple-system,"Helvetica Neue",Arial,sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  color-scheme:dark;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth;scroll-padding-top:56px}
body{margin:0;background:var(--bg);color:var(--fg);font-family:var(--sans);font-size:14px;line-height:1.45;-webkit-font-smoothing:antialiased}
a{color:var(--peri)}
.hero{position:relative;height:clamp(220px,34vw,420px);overflow:hidden;background:#2a2342}
.hero img{width:100%;height:100%;object-fit:cover;object-position:center 55%;display:block}
.hero:after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(14,12,21,.05) 0%,rgba(14,12,21,.15) 45%,rgba(14,12,21,.92) 88%,var(--bg) 100%)}
.hero .title{position:absolute;left:0;right:0;bottom:18px;z-index:2;padding-inline:clamp(16px,4vw,48px);display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:space-between;gap:12px}
.hero h1{margin:0;font-weight:600;font-size:clamp(26px,4.2vw,44px);letter-spacing:-.02em;text-wrap:balance;text-shadow:0 2px 18px rgba(14,12,21,.6)}
.hero h1 small{display:block;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--lav);font-weight:500;margin-bottom:8px}
.asof{font-family:var(--mono);font-size:12px;color:var(--water);text-align:right;line-height:1.5}
.asof b{color:var(--gold);font-weight:500}
.nav{position:sticky;top:0;z-index:20;display:flex;align-items:center;gap:4px;flex-wrap:wrap;padding:8px clamp(16px,4vw,48px);background:rgba(14,12,21,.82);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border-bottom:1px solid var(--line)}
.nav a{color:var(--muted);text-decoration:none;font-size:11.5px;letter-spacing:.1em;text-transform:uppercase;padding:6px 10px;border-radius:6px}
.nav a:hover{color:var(--fg);background:var(--panel2)}
.nav .sp{flex:1}
.seg{display:inline-flex;border:1px solid var(--line2);border-radius:999px;overflow:hidden;font-family:var(--mono);font-size:11px}
.seg button{background:transparent;border:0;color:var(--muted);padding:5px 12px;cursor:pointer;font:inherit}
.seg button.on{background:var(--panel2);color:var(--gold)}
.seg button:hover{color:var(--fg)}
.wrap{padding-inline:clamp(16px,4vw,48px);padding-block:8px 64px;max-width:1440px;margin:0 auto}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-block:18px 28px}
@media (max-width:900px){.kpis{grid-template-columns:repeat(2,1fr)}}
.kpi{position:relative;background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px 16px 12px;min-width:0;display:flex;flex-direction:column;min-height:104px}
.kpi .i{position:absolute;top:10px;right:10px;width:16px;height:16px;border-radius:50%;border:1px solid var(--line2);color:var(--dim);font-size:10px;font-family:var(--mono);display:flex;align-items:center;justify-content:center;cursor:help}
.kpi .i:hover{color:var(--gold);border-color:var(--gold2)}
.kpi .tip{display:none;position:absolute;right:8px;top:30px;z-index:30;width:270px;background:var(--panel2);border:1px solid var(--line2);border-radius:8px;padding:10px 12px;font-size:12px;color:var(--fg);line-height:1.45;box-shadow:0 10px 28px rgba(0,0,0,.45);font-family:var(--sans)}
.kpi .i:hover + .tip,.kpi .i:focus + .tip{display:block}
.kpi .tip b{color:var(--gold);font-weight:500}
tr.more{display:none} table.open tr.more{display:table-row}
.chip{display:inline-block;padding:2px 8px;border-radius:999px;font-family:var(--mono);font-size:11px;margin:2px 4px 2px 0;border:1px solid var(--line2);color:var(--fg);white-space:nowrap}
.chip.up{color:var(--green);border-color:rgba(168,199,154,.5)} .chip.dn{color:var(--red);border-color:rgba(229,72,77,.5)} .chip.nt{color:var(--muted);border-style:dashed}
td.why{white-space:normal;min-width:460px;text-align:left;line-height:1.9}
th.why{text-align:left}
.kpi .l{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);padding-right:22px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.kpi .v.sm{font-size:19px;padding-top:4px}
.kpi .v{font-family:var(--mono);font-size:24px;font-weight:500;margin-top:6px;color:var(--gold);font-variant-numeric:tabular-nums;letter-spacing:-.01em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.kpi .s{font-family:var(--mono);font-size:11.5px;color:var(--muted);margin-top:auto;padding-top:6px;font-variant-numeric:tabular-nums;line-height:1.5;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-height:23px}
.up{color:var(--green)} .dn{color:var(--red)}
.pill{display:inline-block;padding:2px 8px;border-radius:999px;font-family:var(--mono);font-size:11px;border:1px solid var(--line2);color:var(--water);vertical-align:middle}
.pill.exp{color:var(--green);border-color:rgba(168,199,154,.5)} .pill.con{color:var(--peach);border-color:rgba(243,182,144,.5)}
h2{font-size:12px;letter-spacing:.16em;text-transform:uppercase;color:var(--lav);font-weight:600;margin:34px 0 12px;display:flex;align-items:center;gap:12px}
h2:after{content:"";flex:1;height:1px;background:var(--line)}
h2 .hint{font-weight:400;letter-spacing:0;text-transform:none;color:var(--dim);font-family:var(--mono);font-size:11px}
.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:12px}
.panel{grid-column:span 6;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:18px 18px 16px;min-width:0}
.panel.w12{grid-column:span 12} .panel.w4{grid-column:span 4} .panel.w8{grid-column:span 8}
@media (max-width:900px){.panel,.panel.w4,.panel.w8{grid-column:span 12}}
.panel .h{display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:nowrap;min-height:26px}
.panel .h>div:first-child{min-width:0}
.panel .t{font-weight:600;font-size:15px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.panel .n{font-family:var(--mono);color:var(--gold);font-size:12.5px;font-variant-numeric:tabular-nums;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;flex-shrink:1;text-align:right}
.panel .h>div:last-child{display:flex;align-items:center;gap:10px;flex-shrink:0;min-width:0}
.panel .d{color:var(--muted);font-size:12px;margin-top:2px}
.ch{position:relative;height:316px;margin-top:10px}
.ch.tall{height:316px}
.src{font-family:var(--mono);font-size:10.5px;color:var(--dim);margin-top:8px}
table{width:100%;border-collapse:collapse;font-size:12.5px;margin-top:14px;font-variant-numeric:tabular-nums}
th{font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);font-weight:500;text-align:right;padding:6px 8px;border-bottom:1px solid var(--line2);white-space:nowrap}
th:first-child,td:first-child{text-align:left}
td{padding:7px 8px;border-bottom:1px solid var(--line);text-align:right;font-family:var(--mono);white-space:nowrap}
td:first-child{font-family:var(--sans)}
tr.sr td{color:var(--gold)}
tr.today td{color:var(--water)}
.tw{overflow-x:auto}
.pos{color:var(--green)} .neg{color:var(--red)} .mut{color:var(--muted)}
.btn{background:transparent;border:1px solid var(--line2);color:var(--water);font-family:var(--mono);font-size:11px;padding:5px 12px;border-radius:999px;cursor:pointer}
.btn:hover{color:var(--gold);border-color:var(--gold2)}
.bridge{display:grid;grid-template-columns:1fr auto;gap:5px 16px;font-family:var(--mono);font-size:12.5px;margin-top:14px}
.bridge div:nth-child(odd){font-family:var(--sans);color:var(--muted)} .bridge .tot{color:var(--gold);font-weight:600;border-top:1px solid var(--line2);padding-top:6px}
.bridge .tot:nth-child(odd){color:var(--fg)}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:14px} @media (max-width:900px){.stats{grid-template-columns:repeat(2,1fr)}}
.stats>div{background:var(--panel2);border:1px solid var(--line);border-radius:8px;padding:10px 12px;min-width:0}
.stats .l{font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
.stats .v{font-family:var(--mono);font-size:24px;color:var(--gold);margin-top:4px;font-variant-numeric:tabular-nums;white-space:nowrap} .stats .v small{font-size:13px;color:var(--muted);margin-left:6px}
.stats .s{font-family:var(--mono);font-size:11px;color:var(--muted);margin-top:3px;line-height:1.45}
.kpis.small{grid-template-columns:repeat(5,1fr);margin-top:-18px}
@media (max-width:900px){.kpis.small{grid-template-columns:repeat(2,1fr)}}
.kpis.small .kpi{padding:10px 12px 8px;background:transparent;min-height:78px}
.kpis.small .l{font-size:10px} .kpis.small .v{font-size:17px;margin-top:3px;color:var(--fg)} .kpis.small .s{font-size:11px;min-height:19px;padding-top:4px}
.panel{position:relative} .panel .h{padding-right:26px}
.panel>.i{position:absolute;top:23px;right:18px;width:16px;height:16px;border-radius:50%;border:1px solid var(--line2);color:var(--dim);font-size:10px;font-family:var(--mono);display:flex;align-items:center;justify-content:center;cursor:help}
.panel>.i:hover{color:var(--gold);border-color:var(--gold2)}
.panel>.tip{display:none;position:absolute;right:16px;top:46px;z-index:30;width:320px;background:var(--panel2);border:1px solid var(--line2);border-radius:8px;padding:10px 12px;font-size:12px;color:var(--fg);line-height:1.5;box-shadow:0 10px 28px rgba(0,0,0,.45)}
.panel>.i:hover + .tip,.panel>.i:focus + .tip{display:block}
.fold{display:none} .fold.open{display:block}
.panel .d,.panel .src{display:none} .panel .tip .srcnote{display:block;margin-top:6px;color:var(--muted);font-size:11px}
.bar{display:flex;height:26px;border-radius:7px;overflow:hidden;margin-top:18px;background:var(--panel2)} .bar>div{height:100%}
.legend2{display:grid;grid-template-columns:auto 1fr auto auto;gap:9px 10px;margin-top:14px;font-size:13px;align-items:center}
.legend2 i{width:10px;height:10px;border-radius:2px;display:inline-block} .legend2 .v{font-family:var(--mono);text-align:right} .legend2 .p{font-family:var(--mono);color:var(--muted);text-align:right;min-width:40px}
.legend2 .sub{grid-column:2/5;color:var(--muted);font-size:11.5px;margin-top:-6px}
@media (max-width:600px){
  .kpi .l{white-space:normal;overflow:visible} .kpi .v{font-size:21px}
  .stats .v{white-space:normal} .stats .v small{display:block;margin-left:0;margin-top:2px}
  .nav{flex-wrap:nowrap;overflow-x:auto;scrollbar-width:none} .nav::-webkit-scrollbar{display:none} .nav a{white-space:nowrap}
  .hero .asof{text-align:left} .panel>.tip{width:min(320px,calc(100vw - 48px))}
  .legend2{font-size:12px} .bridge{font-size:12px}
}
.foot{margin-top:40px;color:var(--dim);font-size:12px;font-family:var(--mono);line-height:1.7}
</style>

<div class="hero">
  <img src="__HERO__" alt="Standard Reserve: the reserve dam at dusk">
  <div class="title">
    <h1><small>Standard Reserve · Robinhood Chain</small>Protocol Monitor</h1>
    <div class="asof">as of <b>__ASOF_UTC__ UTC</b><br>block __TIP__ · <span id="epochpill" class="pill"></span></div>
  </div>
</div>
<nav class="nav">
  <a href="#market">Market</a><a href="#income">Fee income</a><a href="#equity">Liquidity business</a><a href="#auctions">Auctions</a><a href="#reserve">Reserve</a><a href="#supply">Supply</a><a href="#bank">Banking</a><a href="#log">Data log</a>
  <span class="sp"></span>
  <span class="seg" id="range"><button data-n="7">7d</button><button data-n="30" class="on">30d</button><button data-n="0">all</button></span>
</nav>

<div class="wrap">
  <div class="kpis" id="kpis"></div>
  <div class="kpis small" id="kpis2"></div>

  <h2 id="market">Market <span class="hint">Shaded intervals denote contraction epochs.</span></h2>
  <div class="grid">
    <div class="panel w8"><span class="i" tabindex="0">i</span><div class="tip">Price is the GeckoTerminal daily close for the STANDARD/ETH pool. Market capitalization on minted supply corresponds to the figure quoted by DexScreener and GeckoTerminal. Market capitalization on outstanding supply excludes STANDARD held in the protocol’s own pool and in the Incentives Vault. Shaded intervals denote contraction epochs.</div><div class="h"><div><div class="t">Token price and market capitalization</div><div class="d">Daily closing price with market capitalization on minted supply and on outstanding supply.</div></div><div class="n" id="px_now"></div></div><div class="ch tall"><canvas id="c_price"></canvas></div><div class="src">Source: GeckoTerminal daily close for the STANDARD/ETH pool; STANDARD transfer logs for supply and outstanding supply; epoch-settled events for the regime.</div></div>
    <div class="panel w4"><span class="i" tabindex="0">i</span><div class="tip">Fee income comprises token trading fees, charter auction proceeds and fee income from every reserve pool. The launch epoch is excluded because genesis-day fees distort the first week.</div><div class="h"><div><div class="t">Fee yield</div><div class="d">Trailing seven-day fee income, annualized, as a share of market capitalization on outstanding supply.</div></div><div class="n" id="yield_now"></div></div><div class="ch tall"><canvas id="c_yield"></canvas></div><div class="src">Source: epoch-routed events, charter purchases, stock-pool swap fees; outstanding supply from transfer logs.</div></div>
  </div>

  <h2 id="income">Fee income</h2>
  <div class="grid">
    <div class="panel w8"><span class="i" tabindex="0">i</span><div class="tip">Token trading fees are known per three-day epoch and are allocated evenly across its days; the current epoch is estimated from ETH held in the tax hook and fee splitter. Charter proceeds are recorded on the sale date. Pool fee income is derived from the fee field of each swap, weighted by the reserve’s share of in-range liquidity.</div><div class="h"><div><div class="t">Fee income by source</div><div class="d">Token trading fees, charter auction proceeds and pool fee income, in USD.</div></div><div class="n" id="inc7"></div></div><div class="ch tall"><canvas id="c_income"></canvas></div><div class="src">Source: SR indexer epoch-routed events, charter purchase events, PoolManager swap logs, Coinbase ETH-USD.</div></div>
    <div class="panel w4"><span class="i" tabindex="0">i</span><div class="tip">In expansion epochs 70% is allocated to the reserve; in contraction epochs 70% is allocated to buybacks and burns. A further 15% purchases STANDARD into the Incentives Vault and 15% is allocated to the team. Gold denotes charter auction proceeds within the total.</div><div class="h"><div><div class="t">Fee distribution by epoch</div><div class="d">ETH distributed by the fee engine at each epoch settlement.</div></div></div><div class="ch tall"><canvas id="c_epochs"></canvas></div><div class="src">Source: SR indexer epoch-routed and epoch-settled events.</div></div>
    <div class="panel w12 tw"><span class="i" tabindex="0">i</span><div class="tip">Net flow is ETH purchased less ETH sold through the pool during the epoch, as reported by the hook; its sign sets the regime. Distributed total comprises trading fees and charter proceeds. The vault allocation is 70%, to the reserve in expansion and to buybacks in contraction. Multiplier after is the issuance multiplier applied from the following epoch.</div><div class="h"><div><div class="t">Epoch settlement ledger</div><div class="d">Net flow determines the regime; distributed fees are the levy on total volume and are therefore always positive.</div></div><div><button class="btn" id="fold_ep">View ledger</button></div></div><div class="fold" id="f_ep"><table id="t_epochs"></table></div></div>
  </div>

  <h2 id="equity">Liquidity business <span class="hint">Progress toward a liquidity hub that earns from trading in protocol-owned pools.</span></h2>
  <div class="grid">
    <div class="panel w12"><span class="i" tabindex="0">i</span><div class="tip">Fee income and volume are derived from PoolManager swap logs for the reserve’s pools; liquidity from StateView; competing venues from DexScreener token-pair data for the same assets on Robinhood Chain. Share of on-chain trading uses DexScreener’s 24-hour window.</div><div class="h"><div><div class="t">Trading venue economics</div><div class="d">All protocol-owned pools: three tokenized equities and ETH/USDG. Fee income reflects the reserve’s share of in-range liquidity.</div></div></div><div class="stats" id="eq_stats"></div></div>
    <div class="panel w8"><div class="h"><div><div class="t">Pool fee income by pool</div><div class="d">Daily fee income earned by the reserve in each pool, with pool fee income as a trailing seven-day share of total fee income.</div></div><div class="n" id="eq_n"></div></div><div class="ch tall"><canvas id="c_equity"></canvas></div><div class="src">Source: PoolManager swap logs; epoch-routed events; charter purchase events.</div></div>
    <div class="panel w4 tw"><span class="i" tabindex="0">i</span><div class="tip">Pool fee income accrues within the reserve’s liquidity positions and does not pass through the fee engine; it therefore adds to backing and funds no buybacks. Token trading fees and charter proceeds are distributed at settlement: 70% to the reserve in expansion epochs or to buybacks in contraction epochs, 15% to POL buybacks and 15% to the team.</div><div class="h"><div><div class="t">Fee income allocation, trailing seven days</div><div class="d">Allocation of fee income to reserve backing, buybacks and the team.</div></div></div><div class="bar" id="went_bar"></div><div class="legend2" id="went_leg"></div><div class="src" id="went_src"></div></div>
  </div>

  <h2 id="auctions">Auctions</h2>
  <div class="grid">
    <div class="panel"><span class="i" tabindex="0">i</span><div class="tip"><span id="ch_tip"></span> One charter is offered per 12-hour period in a descending-price auction. The price opens at three times the previous clearing price and halves every two hours toward a floor of 1 ETH until a purchase occurs. Proceeds are distributed through the fee engine. Triangles denote purchases executed through a contract.</div><div class="h"><div><div class="t">Charter auction clearing prices</div><div class="d">Clearing price of each charter sold, in ETH.</div></div><div class="n" id="ch_now"></div></div><div class="ch"><canvas id="c_charter"></canvas></div><div class="src">Source: CharterPurchased events on the auction contract; current price from the auction contract.</div></div>
    <div class="panel"><span class="i" tabindex="0">i</span><div class="tip"><span id="lic_tip"></span> Licenses open additional branches, are paid in STANDARD and are burned on purchase. Twenty-five are offered per 12-hour period (24-hour periods at launch), opening at twice the previous clearing price with a floor of approximately two days of one branch’s issuance.</div><div class="h"><div><div class="t">License auction clearing prices and volume</div><div class="d">Period close price in STANDARD and licenses sold per period.</div></div><div class="n" id="lic_now"></div></div><div class="ch"><canvas id="c_license"></canvas></div><div class="src">Source: licenses-purchased events grouped by auction period.</div></div>
  </div>

  <h2 id="reserve">Reserve assets and protocol-owned liquidity</h2>
  <div class="grid">
    <div class="panel w4"><span class="i" tabindex="0">i</span><div class="tip">Comprises ETH and USDG held in the reserve Safe, ETH in the policy vaults, tokenized equities held outside pools, and the Safe’s Uniswap v4 positions. Excludes the S-Bill premium pot and the team wallet.</div><div class="h"><div><div class="t">Reserve composition by asset</div><div class="d">Current reserve holdings, in USD.</div></div><div class="n" id="res_tot"></div></div><div class="ch"><canvas id="c_reserve"></canvas></div><div class="src">Source: Robinhood Chain RPC balances of the reserve Safe, vaults and the Safe's Uniswap v4 positions. Excludes the S-Bill premium pot and team wallet.</div></div>
    <div class="panel w8"><span class="i" tabindex="0">i</span><div class="tip">The grey line denotes the share of volume transacted at a 0% fee, attributable to a fee-exempt arbitrage contract. Fee income accrues to the reserve, which owns every position, weighted by its share of in-range liquidity.</div><div class="h"><div><div class="t">Pool trading volume and fee income</div><div class="d">Daily volume by pool in USDG, fee income to the reserve, and the share of volume transacted at zero fee.</div></div><div class="n" id="sp7"></div></div><div class="ch tall"><canvas id="c_pools"></canvas></div><div class="src">Source: PoolManager swap logs for the reserve's pools; fee from the swap's fee field.</div></div>
    <div class="panel w12 tw"><span class="i" tabindex="0">i</span><div class="tip">Holdings and prices are read from Uniswap v4 StateView and PositionManager; other venues for the same asset from DexScreener. The reserve is the sole liquidity provider in the equity pools but shares the ETH/USDG pool with third-party providers, so fee income reflects its share of in-range liquidity at each swap. Equity pools apply a session fee set by the hook; the ETH/USDG pool applies a fixed tier. Yield is trailing seven-day fee income annualized over position value.</div><div class="h"><div><div class="t">Protocol-owned liquidity by pool</div><div class="d">The reserve’s position in each pool and its standing against other venues on the chain.</div></div></div><table id="t_pools"></table><div class="src">Source: Uniswap v4 StateView and PositionManager for holdings; DexScreener token-pairs for the other pools.</div></div>
    <div class="panel w12 tw"><span class="i" tabindex="0">i</span><div class="tip">Balances are read on-chain at each run. The chain retains no archival state, so the series begins on the first day of operation (22 October 2026) and extends by one observation per run.</div><div class="h"><div><div class="t">Reserve composition, daily change</div><div class="d">Each reserve component against the prior day and seven days earlier.</div></div><div><span class="n" id="resd_n"></span> <button class="btn" id="fold_rs">View table</button></div></div><div class="fold" id="f_rs"><table id="t_resd"></table></div><div class="src">Source: Robinhood Chain RPC balances and Uniswap v4 position values at each run, USD at that run's ETH price and pool prices.</div></div>
  </div>

  <h2 id="supply">Supply and market capitalization</h2>
  <div class="grid">
    <div class="panel w4"><span class="i" tabindex="0">i</span><div class="tip">Outstanding supply equals minted supply less STANDARD held in the protocol’s pool less the Incentives Vault. Free float further excludes S-Bills locked and the team wallet; fully diluted adds pending issuance. DexScreener and GeckoTerminal quote market capitalization on minted supply. Pending issuance has been credited to branches but not yet minted.</div><div class="h"><div><div class="t">Supply reconciliation</div><div class="d">From the genesis mint to outstanding supply, free float and fully diluted supply.</div></div></div><div class="bridge" id="bridge"></div><div class="src">Outstanding = minted supply less the protocol's pool and the Incentives Vault, the equity analog of shares outstanding. Free float further excludes S-Bills locked and the team wallet. Fully diluted adds pending issuance. DexScreener and GeckoTerminal quote market capitalization on minted supply.</div></div>
    <div class="panel w8"><span class="i" tabindex="0">i</span><div class="tip">Bars equal the change in outstanding supply multiplied by price: negative when tokens are sold into the pool or deposited to branches, positive when withdrawals are minted.</div><div class="h"><div><div class="t">Market capitalization, outstanding supply, with daily change</div><div class="d">Market capitalization on outstanding supply, with each day’s change in outstanding supply valued at that day’s price.</div></div><div class="n" id="mc_now"></div></div><div class="ch tall"><canvas id="c_mc"></canvas></div><div class="src">Source: GeckoTerminal daily close for STANDARD/ETH, STANDARD transfer logs for outstanding supply. Bars = Δoutstanding × price.</div></div>
    <div class="panel"><span class="i" tabindex="0">i</span><div class="tip">Withdrawals minted to bankers and Incentives Vault distributions add to outstanding supply; deposits to branches, which are burned to the ledger, reduce it. Buybacks and POL purchases remove tokens from the pool. Net flow into the pool is sales less purchases.</div><div class="h"><div><div class="t">Outstanding supply flows by source</div><div class="d">Daily movements of STANDARD into and out of outstanding supply.</div></div></div><div class="ch tall"><canvas id="c_flows"></canvas></div><div class="src">Source: STANDARD Transfer logs involving the pool, vaults, S-Bills and the zero address.</div></div>
    <div class="panel"><span class="i" tabindex="0">i</span><div class="tip">Issuance accrues to branches as a ledger entry at 700,000 multiplied by the policy multiplier per day. Licenses purchased with accrued STANDARD and resolution fees are burned before any minting occurs. The line is net issuance, the new STANDARD owed to bankers.</div><div class="h"><div><div class="t">Issuance and burn</div><div class="d">Daily issuance accrued to branches against STANDARD burned before minting.</div></div></div><div class="ch tall"><canvas id="c_issue"></canvas></div><div class="src">Source: epoch-settled multipliers, licenses-purchased, withdrawn and revoked events.</div></div>
    <div class="panel w12 tw"><span class="i" tabindex="0">i</span><div class="tip">Supply changes when withdrawals are minted (+), deposits are burned to branches (−) and buybacks are burned (−). The pool changes when the market sells into it (+) or purchases from it (−) and when buybacks withdraw tokens (−). A buyback reduces supply and the pool by equal amounts, lowering market capitalization on minted supply while leaving outstanding supply unchanged. S-Bill premiums are paid from a pot held by the S-Bills contract and move tokens within outstanding supply.</div><div class="h"><div><div class="t">Supply, pool and outstanding reconciliation</div><div class="d">Daily reconciliation: outstanding supply equals minted supply less the protocol pool less the Incentives Vault.</div></div><div><button class="btn" id="fmore">View all days</button></div></div><table id="t_float"></table><div class="src">Source: STANDARD Transfer logs classified by counterparty (zero address, PoolManager, contraction vault, POL buyback, Incentives Vault). S-Bill premiums are paid from a pot the S-Bills contract already holds, so they move tokens within outstanding supply and do not appear.</div></div>
  </div>

  <h2 id="bank">Banking system</h2>
  <div class="grid">
    <div class="panel"><span class="i" tabindex="0">i</span><div class="tip">Pending ledger equals issuance plus deposits plus recycled fees, less licenses, gross withdrawals and revocations. The resolution fee is 2%, rising to 60% as seven-day withdrawals approach 10% of the ledger.</div><div class="h"><div><div class="t">Bank deposits, withdrawals and pending ledger</div><div class="d">Daily deposits against gross withdrawals, with the unminted balance owed to bankers.</div></div><div class="n" id="exitfee"></div></div><div class="ch"><canvas id="c_bank"></canvas></div><div class="src">Source: deposited and withdrawn events. Ledger = issuance + deposits + recycled fees − licenses − gross withdrawals − revocations.</div></div>
    <div class="panel"><span class="i" tabindex="0">i</span><div class="tip">A charter opens with one branch and licenses add up to nine more. Withdrawals and revocations destroy branches; a charter with no remaining branches is burned. The reconstruction matches the live census. The multiplier by epoch is shown in the epoch settlement ledger.</div><div class="h"><div><div class="t">Branch and charter count</div><div class="d">Branches outstanding and active charters, reconstructed from on-chain events.</div></div><div class="n" id="sb_now"></div></div><div class="ch"><canvas id="c_policy"></canvas></div><div class="src">Source: charter-created, branches-opened, withdrawn and revoked events.</div></div>
    <div class="panel w12 tw" id="log"><span class="i" tabindex="0">i</span><div class="tip">Reserve value is read from on-chain balances and begins on the first day of operation. All other fields are reconstructed from protocol events and transfer logs.</div><div class="h"><div><div class="t">Daily data log</div><div class="d">One observation per UTC day since genesis. The current day is partial.</div></div><div><button class="btn" id="more">View all days</button> <button class="btn" id="csv">Export CSV</button></div></div><table id="t_log"></table></div>
  </div>

  <div class="foot">Standard Reserve Protocol Monitor · compiled __ASOF_UTC__ UTC · Sources: Standard Reserve indexer, Robinhood Chain RPC, DexScreener, GeckoTerminal, Coinbase · Artwork: Standard Reserve</div>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<script>
const DATA = __DATA__;
const L = DATA.live, S = DATA.series, E = DATA.epochs, HIST = DATA.history || {};
const C = {gold:'#ffdd8a',gold2:'#deb553',lav:'#b9a6e3',peri:'#8fa2f0',peach:'#f3b690',rose:'#e9b7d4',water:'#cdbdf0',green:'#a8c79a',red:'#e5484d',dim:'#6f6690',muted:'#a79ec4'};
const fmt = {
  usd:(v,d)=>{if(v==null||isNaN(v))return '–';const s=v<0?'−':'';v=Math.abs(v);return s+(v>=1e6?'$'+(v/1e6).toFixed(d==null?2:d)+'M':v>=1e3?'$'+(v/1e3).toFixed(d==null?1:d)+'K':'$'+v.toFixed(d==null?2:d));},
  n:(v,d)=>{if(v==null||isNaN(v))return '–';const s=v<0?'−':'';v=Math.abs(v);return s+(v>=1e6?(v/1e6).toFixed(d==null?2:d)+'M':v>=1e3?(v/1e3).toFixed(d==null?1:d)+'K':v.toFixed(d==null?0:d));},
  pct:(v,d)=>v==null||isNaN(v)?'–':(v*100).toFixed(d==null?1:d)+'%',
  eth:(v,d)=>v==null?'–':v.toFixed(d==null?1:d)+' ETH',
  dt:(ts)=>new Date(ts*1000).toISOString().slice(0,10),
  hm:(ts)=>new Date(ts*1000).toISOString().slice(11,16),
  sgn:(v)=>v>0?'+':'',
  int:(v)=>v==null||isNaN(v)?'–':Math.round(v).toLocaleString('en-US'),
  chg:(v,d)=>v==null||isNaN(v)?'':`<span class="${v>=0?'up':'dn'}">${v>=0?'+':'−'}${(Math.abs(v)*100).toFixed(d==null?1:d)}%</span>`,
  days:(v)=>v==null||!isFinite(v)?'–':v>=365?(v/365).toFixed(1)+' yrs':Math.round(v)+' days'
};
if (window.Chart) {
  Chart.defaults.color = C.muted; Chart.defaults.font.family = getComputedStyle(document.documentElement).getPropertyValue('--mono');
  Chart.defaults.font.size = 10.5; Chart.defaults.borderColor = 'rgba(190,172,232,.12)';
  Chart.defaults.plugins.legend.labels.boxWidth = 9; Chart.defaults.plugins.legend.labels.boxHeight = 9; Chart.defaults.plugins.legend.labels.padding = 14;
  Chart.defaults.plugins.legend.align = 'start'; Chart.defaults.plugins.legend.position = 'bottom'; Chart.defaults.plugins.legend.labels.font = {size: 10.5};
  Chart.defaults.plugins.legend.labels.padding = 18; Chart.defaults.layout.padding = {top: 8, bottom: 0};
  Chart.defaults.plugins.tooltip.backgroundColor = '#1c1829'; Chart.defaults.plugins.tooltip.borderColor = 'rgba(190,172,232,.3)'; Chart.defaults.plugins.tooltip.borderWidth = 1;
  Chart.defaults.elements.bar.borderRadius = 2; Chart.defaults.animation = false;
}
const last = (arr,n)=>n?arr.slice(Math.max(0,arr.length-n)):arr;
const sum = (a)=>a.reduce((x,y)=>x+(y||0),0);
const ethOf = (r)=>r.eth||L.ethusd;
const inc = (r)=>(r.tradingFeeEth||0)*ethOf(r)+(r.charterEth||0)*ethOf(r)+(r.spFee||0);
const Sh = S.filter(r=>r.date<=L.date);            // every day through today (today partial)
const ep2 = E.length>1 ? fmt.dt(E[1].start) : '';   // launch epoch excluded from rolling yield (genesis-day fees distort it)
const Sp = Sh.filter(r=>r.date<L.date);            // complete days only
const back = (k,n)=>{const i=Sh.length-1-n; return i>=0?Sh[i][k]:null;};
const s7 = last(Sp,7);
// regime by date: expansion (true) or contraction (false), from settled epochs plus the live one
const regime = {};
const isExp = (e)=>e.expansion===true||e.expansion==='true'||e.expansion===1;
E.forEach(e=>{for(let t=e.start+3600;t<e.end;t+=86400) regime[fmt.dt(t)] = isExp(e);});
for(let t=L.epochStart+3600;t<L.epochEnd;t+=86400) regime[fmt.dt(t)] = L.epochNetFlow>=0;
const bands = {id:'bands', beforeDatasetsDraw(ch){const o=(ch.options.plugins||{}).bands; if(!o||!o.dates||!o.dates.length) return; const x=ch.scales.x, a=ch.chartArea, ctx=ch.ctx;
  const w = o.dates.length>1 ? x.getPixelForValue(1)-x.getPixelForValue(0) : a.width; ctx.save();
  o.dates.forEach((d,i)=>{const r=regime[d]; if(r===undefined) return; ctx.fillStyle = r?'rgba(168,199,154,.045)':'rgba(243,182,144,.10)'; ctx.fillRect(x.getPixelForValue(i)-w/2, a.top, w, a.height);}); ctx.restore();}};
if (window.Chart) Chart.register(bands);

// ---------- KPIs ----------
const inc7 = sum(s7.map(inc)), incAnn = inc7*365/7, incLife = sum(S.map(r=>(r.routedEth||0)*ethOf(r)+(r.spFee||0)));
const Y = Sp[Sp.length-1]||{}, Y2 = Sp[Sp.length-2]||{};      // yesterday (last complete UTC day) and the day before
const yd = Y.date ? new Date(Y.date+'T00:00:00Z').toLocaleDateString('en-GB',{day:'numeric',month:'short',timeZone:'UTC'}) : '';
const mcFloat = L.price*L.float, mcTotal = L.price*L.totalSupply;
const epLeft = Math.max(0, L.epochEnd - DATA.pulledAt);
const backing = L.reserve.totalUsd/L.float, backingTot = L.reserve.totalUsd/L.totalSupply;
const perBranch = L.baseIssuance*L.multiplier/L.branches;
const licPayback = L.licensePriceNow/perBranch, chPayback = L.charterPriceNow*L.ethusd/(perBranch*L.price);
const bbY = (Y.burnBuyback||0)+(Y.toIncentives||0), bb7 = sum(s7.map(r=>(r.burnBuyback||0)+(r.toIncentives||0)));
const mUp = (L.positiveStreak||0)+1>=2 ? Math.min(L.mMax, L.multiplier+L.mStepUp) : L.multiplier, mDn = Math.max(L.mMin, L.multiplier-L.mStepDown);
const dF = Y.float!=null&&Y2.float!=null ? Y.float-Y2.float : null, p7 = back('price',7);
const dv = (k)=>Y[k]!=null&&Y2[k]!=null ? fmt.sgn(Y[k]-Y2[k])+fmt.n(Y[k]-Y2[k],2) : '–';
const dvi = (k)=>Y[k]!=null&&Y2[k]!=null ? fmt.sgn(Y[k]-Y2[k])+fmt.int(Y[k]-Y2[k]) : '–';
const kpis = [
  ['Token price', '$'+L.price.toFixed(4), `${L.priceChange24h!=null?fmt.chg(L.priceChange24h/100)+' 24h':''}${p7?' · '+fmt.chg(L.price/p7-1)+' 7d':''}`,
    `Live price from DexScreener for the STANDARD/ETH pool. The daily history uses GeckoTerminal closing prices.`],
  ['Market capitalization', fmt.usd(mcTotal), ``,
    `<b>The figure quoted by DexScreener and GeckoTerminal.</b> Price multiplied by ERC-20 total supply. Minted supply includes ${fmt.n(L.poolStd,1)} STANDARD held in the protocol’s own STANDARD/ETH pool and ${fmt.n(L.incentivesStd,1)} in the Incentives Vault, neither of which is available for sale.`],
  ['Market capitalization, outstanding', fmt.usd(mcFloat), ``,
    `<b>The equity analog of shares outstanding.</b> Minted supply less the protocol’s own pool and the Incentives Vault, the two balances the protocol cannot sell. It includes ${fmt.n(L.sbillsStd,1)} locked in S-Bills and ${fmt.n(L.teamStd,1)} held by the team wallet; free float, which excludes both, is ${fmt.n(L.float-L.sbillsStd-L.teamStd,1)} (${fmt.usd(L.price*(L.float-L.sbillsStd-L.teamStd))}). Fully diluted, adding ${fmt.n(L.pending,1)} of pending issuance, is ${fmt.n(L.totalSupply+L.pending,1)} (${fmt.usd(L.price*(L.totalSupply+L.pending))}).`],
  ['Reserve assets', fmt.usd(L.reserve.totalUsd), `price ${(L.price/backing).toFixed(1)}× backing`,
    `ETH and USDG held in the reserve Safe, ETH in the policy vaults, tokenized equities held outside pools, and the reserve’s Uniswap v4 positions (${fmt.pct(L.reserve.lpUsd/L.reserve.totalUsd,0)} of the total). Excludes the ${fmt.eth(L.reserve.polBuybackEth,0)} S-Bill premium pot and the team wallet. Backing is $${backing.toFixed(3)} per outstanding token and $${backingTot.toFixed(3)} per minted token.`],
  ['Fee income, '+yd, fmt.usd(inc(Y)), `7-day average ${fmt.usd(inc7/7)} per day`,
    `The most recent complete UTC day. Comprises STANDARD/ETH trading fees (each epoch’s distributed ETH allocated evenly across its days; the current epoch estimated from tax hook and fee splitter balances), charter auction proceeds, and the reserve’s fee income from its pools, in USD. Cumulative since genesis: ${fmt.usd(incLife)}.`],
  ['Buybacks, '+yd+' (STANDARD)', fmt.n(bbY,2), `${fmt.usd(bbY*(Y.price||L.price))}`,
    `STANDARD purchased from the pool and burned by the contraction vault, plus the 15% POL allocation purchased into the Incentives Vault. ${fmt.eth(L.reserve.contractionEth,1)} remains in the contraction vault pending deployment.`],
  ['Epoch '+L.epoch+' net flow', (L.epochNetFlow>=0?'+':'')+L.epochNetFlow.toFixed(1)+' ETH', `settles in ${Math.floor(epLeft/3600)}h ${Math.floor(epLeft%3600/60)}m`,
    `Net flow is ETH purchased less ETH sold through the pool so far this epoch. Its sign at settlement sets the regime: expansion allocates 70% of fees to the reserve, contraction allocates them to buybacks. Prior epoch ${fmt.sgn(L.previousEpochFlow)}${L.previousEpochFlow.toFixed(1)} ETH; consecutive positive epochs ${L.positiveStreak}. The multiplier settles to ${mUp.toFixed(2)}× if positive and ${mDn.toFixed(2)}× if negative.`],
  ['Issuance multiplier', L.multiplier.toFixed(2)+'×', ``,
    `Daily issuance equals 700,000 multiplied by the multiplier, ${fmt.n(L.baseIssuance*L.multiplier,0)} today or ${perBranch.toFixed(1)} per branch, allocated evenly across branches. The multiplier rises 0.10 from the second consecutive positive epoch and falls 0.15 per negative epoch, within a range of 0.20 to 1.25. Pending issuance, credited but not minted: ${fmt.n(L.pending,1)}.`],
  ['License payback period', fmt.days(licPayback), ``,
    `Current license price (${fmt.int(L.licensePriceNow)} STANDARD) divided by one branch’s daily issuance (${perBranch.toFixed(1)}). The charter figure divides ${fmt.usd(L.charterPriceNow*L.ethusd,1)} by the USD value of one branch’s daily issuance. Both exclude resolution fees and future multiplier changes.`],
  ['Charter auction, last clearing', L.charterLastSale.toFixed(2)+' ETH', `${(L.charterRemaining||0)>0?'quote '+L.charterPriceNow.toFixed(2)+' ETH, descending':'next '+fmt.hm(L.charterNextOpen)+' UTC at '+L.charterNextStart.toFixed(2)+' ETH'}`,
    `<b>The most recent charter cleared at ${L.charterLastSale.toFixed(2)} ETH.</b> One charter is offered per ${L.auctionPeriodHours}-hour period in a descending-price auction: the period opened at ${L.charterDayStart.toFixed(2)} ETH (three times the previous clearing price) and the price halves every ${L.charterHalfLife||2} hours toward the ${L.charterFloor.toFixed(2)} ETH floor until a purchase occurs. After the period’s charter is sold the contract continues to quote a declining price, but no charter is available until the next period opens.`],
  ['License auction, last clearing (STANDARD)', fmt.int(L.licenseLastSale), `${(L.licenseRemaining||0)>0?'quote '+fmt.int(L.licensePriceNow)+', descending':'next '+fmt.hm(L.licenseNextOpen)+' UTC at '+fmt.int(L.licenseNextStart)}`,
    `<b>The most recent license cleared at ${fmt.int(L.licenseLastSale)} STANDARD</b>, burned on purchase. Twenty-five are offered per ${L.auctionPeriodHours}-hour period, opening at ${fmt.int(L.licenseDayStart)} (twice the previous clearing price) and halving every ${L.licenseHalfLife||2} hours toward a floor of ${fmt.int(L.licenseFloor)}, approximately two days of one branch’s issuance. Current quote ${fmt.int(L.licensePriceNow)}. Limited to three per charter per 24 hours.`, 'sm'],
  ['Branches outstanding', fmt.int(L.branches), `${dvi('branches')} on ${yd}`,
    `Each charter opens with one branch; licenses add up to nine more, for a maximum of ten per charter. Withdrawals and revocations destroy branches. Reconstructed from events and reconciled to the live census.`],
  ['Active charters', fmt.int(L.activeCharters), ``,
    `A charter is the NFT that holds a banker’s branches. ${L.chartersMinted} have been minted (1,000 founding charters plus those auctioned). A charter is burned when its last branch is destroyed; ${L.burnedCharters} have been burned. Active equals minted less burned.`],
  ['Outstanding supply change, '+yd, dF==null?'–':fmt.sgn(dF)+fmt.n(dF,2), Y2.float?`${fmt.pct(dF/Y2.float,2)}`:'',
    `Outstanding supply equals minted supply less the protocol pool less the Incentives Vault. It falls when tokens are sold into the pool or deposited to branches, and rises when withdrawals are minted, the market purchases from the pool, or the Incentives Vault distributes. Buybacks reduce supply and the pool equally and leave outstanding supply unchanged. On ${yd}: minted supply ${dv('supply')}, pool ${dv('pool')}, Incentives Vault ${dv('incentives')}.`],
  ['S-Bills outstanding', fmt.n(L.sbills.locked,2), `${(L.sbills.rate*100).toFixed(2)}% per 15-day term`,
    `STANDARD locked in 15-day S-Bills. The term rate drifts between a ${(L.sbills.floor*100).toFixed(0)}% floor and a ${(L.sbills.ceiling*100).toFixed(0)}% ceiling with demand. Premiums are paid from a pot funded by the Incentives Vault.`],
  ['Resolution fee', fmt.pct(L.exitFeeNow,1), ``,
    `Fee applied to withdrawals: 2%, rising quadratically to 60% as seven-day withdrawals approach 10% of the ledger. Gross withdrawals over the last seven days: ${fmt.n(L.w7,1)}. Half of each fee is burned and half is recycled to remaining bankers (${fmt.n(L.cumulativeRecycled,1)} cumulative).`],
  ['Team wallet holdings', fmt.eth(L.teamEth,0), `${fmt.n(L.teamStd,2)} STANDARD`,
    `The wallet to which the fee splitter allocates 15% of distributed ETH. The STANDARD balance is tracked from transfer logs, so any sale into the pool would be visible here.`],
  ['Cumulative burn', fmt.n(L.burnedForever,2), ``,
    `License purchases and fee burns permanently reduce the 1 billion hard cap. Deposits to branches also burn tokens but are re-minted on withdrawal and are excluded here.`],
];
const PRIMARY = ['Token price','Market capitalization','Market capitalization, outstanding','Reserve assets','Fee income, '+yd,'Buybacks, '+yd+' (STANDARD)','Epoch '+L.epoch+' net flow','License payback period'];
const tile = k=>`<div class="kpi"><span class="i" tabindex="0">i</span><div class="tip">${k[3]}</div><div class="l">${k[0]}</div><div class="v ${k[4]||''}">${k[1]}</div><div class="s">${k[2]}</div></div>`;
document.getElementById('kpis').innerHTML = PRIMARY.map(n=>kpis.find(k=>k[0]===n)).filter(Boolean).map(tile).join('');
document.getElementById('kpis2').innerHTML = kpis.filter(k=>!PRIMARY.includes(k[0])).map(tile).join('');
document.getElementById('epochpill').textContent = `Epoch ${L.epoch} · ${L.epochNetFlow>=0?'expansion':'contraction'} to date`;
document.getElementById('epochpill').className = 'pill '+(L.epochNetFlow>=0?'exp':'con');

// ---------- static charts (not range dependent) ----------
const E2 = E.filter(e=>e.epoch>1);
new Chart(c_epochs, {type:'bar', data:{labels:E2.map(e=>'E'+e.epoch), datasets:[
  {label:'Trading fees', data:E2.map(e=>e.routed-e.charterEth), backgroundColor:E2.map(e=>isExp(e)?C.green:C.peach), stack:'a'},
  {label:'Charter proceeds', data:E2.map(e=>e.charterEth), backgroundColor:C.gold2, stack:'a'},
]}, options:{maintainAspectRatio:false, scales:{x:{stacked:true,grid:{display:false}}, y:{stacked:true, ticks:{callback:v=>v+' ETH'}}}, plugins:{legend:{display:true}, tooltip:{callbacks:{afterTitle:i=>{const e=E2[i[0].dataIndex];return (isExp(e)?'expansion':'contraction')+' · net flow '+(e.netFlow>=0?'+':'')+e.netFlow.toFixed(1)+' ETH';}, label:c=>c.dataset.label+': '+c.parsed.y.toFixed(1)+' ETH'}}}}});
document.getElementById('t_epochs').innerHTML = '<tr><th>Epoch</th><th>Settled</th><th>Net flow (ETH)</th><th>Regime</th><th>Trading fees (ETH)</th><th>Charter proceeds (ETH)</th><th>Distributed, total (ETH)</th><th>Vault (70%)</th><th>POL (15%)</th><th>Team (15%)</th><th>Multiplier after</th></tr>' +
  E.slice().reverse().map(e=>`<tr><td>${e.epoch}</td><td>${fmt.dt(e.settledAt)}</td><td class="${e.netFlow>=0?'pos':'neg'}">${fmt.sgn(e.netFlow)}${e.netFlow.toFixed(1)}</td><td>${isExp(e)?'<span class="pill exp">expansion</span>':'<span class="pill con">contraction</span>'}</td><td>${(e.routed-e.charterEth).toFixed(1)}</td><td>${e.charterEth.toFixed(1)}</td><td>${e.routed.toFixed(1)}</td><td>${e.toVault.toFixed(1)}</td><td>${e.toPol.toFixed(1)}</td><td>${e.team.toFixed(1)}</td><td>${e.multiplierAfter.toFixed(2)}×</td></tr>`).join('');

const CH = DATA.charters;
const chOpen = (L.charterRemaining||0)>0, licOpen = (L.licenseRemaining||0)>0;
document.getElementById('ch_now').textContent = chOpen ? `quote ${L.charterPriceNow.toFixed(2)} ETH, descending` : `next ${fmt.hm(L.charterNextOpen)} UTC at ${L.charterNextStart.toFixed(2)} ETH`;
new Chart(c_charter, {type:'line', data:{labels:CH.map(c=>fmt.dt(c.ts).slice(5)), datasets:[
  {label:'Clearing price (ETH)', data:CH.map(c=>c.eth), borderColor:C.gold, backgroundColor:'rgba(255,221,138,.18)', fill:true, pointRadius:CH.map(c=>c.viaContract?4:2.5), pointStyle:CH.map(c=>c.viaContract?'triangle':'circle'), pointBackgroundColor:C.gold, tension:.25},
  ...(chOpen?[{label:'Current quote', data:CH.map((c,i)=>i===CH.length-1?L.charterPriceNow:null), borderColor:C.water, pointRadius:5, pointStyle:'rectRot', pointBackgroundColor:C.water, showLine:false}]:[]),
]}, options:{maintainAspectRatio:false, scales:{x:{grid:{display:false}, ticks:{maxTicksLimit:9}}, y:{ticks:{callback:v=>v+' ETH'}, beginAtZero:true}}, plugins:{tooltip:{callbacks:{title:i=>{const c=CH[i[0].dataIndex];return 'charter #'+c.id+' · '+fmt.dt(c.ts)+(c.viaContract?' · via contract':'');}, afterBody:i=>{const c=CH[i[0].dataIndex];return c.buyer?'buyer '+c.buyer.slice(0,10):'';}}}}}});
document.getElementById('ch_tip').textContent = `${CH.length} charters sold to date for ${L.charterEthLifetime.toFixed(1)} ETH; the period is ${chOpen?'open':'sold out'}.`;
const LP = DATA.licensePeriods;
document.getElementById('lic_now').textContent = licOpen ? `quote ${fmt.int(L.licensePriceNow)}, descending · ${L.licenseRemaining} left` : `next ${fmt.hm(L.licenseNextOpen)} UTC at ${fmt.int(L.licenseNextStart)}`;
document.getElementById('lic_tip').textContent = `${fmt.n(sum(LP.map(p=>p.burned)),2)} STANDARD burned over ${LP.length} periods; the period is ${licOpen?'open':'sold out'}.`;
new Chart(c_license, {data:{labels:LP.map(p=>fmt.dt(p.start).slice(5)+' '+(new Date(p.start*1000).getUTCHours()<12?'am':'pm')), datasets:[
  {type:'bar', label:'Licenses sold', data:LP.map(p=>p.sold), backgroundColor:'rgba(185,166,227,.35)', yAxisID:'y1', order:2},
  {type:'line', label:'Period close price (STANDARD)', data:LP.map(p=>p.close), borderColor:C.gold, backgroundColor:C.gold, pointRadius:2, tension:.25, yAxisID:'y', order:1},
]}, options:{maintainAspectRatio:false, scales:{x:{grid:{display:false}, ticks:{maxTicksLimit:10}}, y:{position:'left', ticks:{callback:v=>fmt.n(v,1)}}, y1:{position:'right', grid:{display:false}, beginAtZero:true}}, plugins:{tooltip:{callbacks:{afterTitle:i=>{const p=LP[i[0].dataIndex];return 'period '+p.day+' · burned '+fmt.n(p.burned,1)+' STANDARD';}}}}}});

const R = L.reserve;
document.getElementById('res_tot').textContent = fmt.usd(R.totalUsd);
const pname = (s)=>s==='ETH'?'ETH/USDG pool':s+' pool';
const lpItems = Object.entries(L.lp).map(([s,v])=>[pname(s), v.valueUSD]);
const resItems = [...lpItems, ['USDG', R.safeUsdg], ['ETH (Safe + vaults)', (R.safeEth+R.contractionEth+R.expansionEth)*L.ethusd], ['Stock held outside pools', R.safeStockUsd]].filter(x=>x[1]>1);
new Chart(c_reserve, {type:'bar', data:{labels:resItems.map(x=>x[0]), datasets:[{data:resItems.map(x=>x[1]), backgroundColor:resItems.map((x,i)=>i<lpItems.length?C.peri:x[0].startsWith('USDG')?C.water:x[0].startsWith('ETH')?C.peach:C.green)}]}, options:{indexAxis:'y', maintainAspectRatio:false, plugins:{legend:{display:false}, tooltip:{callbacks:{label:c=>fmt.usd(c.parsed.x)+' · '+fmt.pct(c.parsed.x/R.totalUsd,1)}}}, scales:{x:{ticks:{callback:v=>fmt.usd(v,1)}}, y:{grid:{display:false}}}}});

const pools = Object.keys(L.lp);
const ctx = L.poolCtx;
document.getElementById('t_pools').innerHTML = '<tr><th>Pool</th><th>Tokens held</th><th>USDG held</th><th>Pool price</th><th>Fee tier</th><th>Position value</th><th>Fee income, prior day</th><th>Fee income, 7 days</th><th>Volume, prior day</th><th>Venues on chain</th><th>Reserve share of pool</th><th>Reserve share of chain liquidity</th><th>Pool share of 24h volume</th><th>Yield, 7-day annualized</th><th>Rank</th><th>Next largest venue</th></tr>' +
  pools.map(p=>{const v=L.lp[p], c=ctx[p]||{}; const d1=Sp.slice(-1)[0]||{}; const f7=sum(s7.map(r=>r['spFee_'+p]||0));
    return `<tr><td>${pname(p)}</td><td>${fmt.n(v.stock,1)}</td><td>${fmt.usd(v.usdg,1)}</td><td>$${v.price.toFixed(2)}</td><td>${v.feeTier>=8388608?'session':(v.feeTier/1e4).toFixed(3)+'%'}</td><td>${fmt.usd(v.valueUSD)}</td><td>${fmt.usd(d1['spFee_'+p]||0,2)}</td><td>${fmt.usd(f7,2)}</td><td>${fmt.usd(d1['spVol_'+p]||0,1)}</td><td>${c.pools||'–'}</td><td>${v.share!=null?fmt.pct(v.share,0):'–'}</td><td>${c.totalLiq?fmt.pct(v.valueUSD/c.totalLiq,0):'–'}</td><td>${c.totalVol24?fmt.pct(c.srVol24/c.totalVol24,0):'–'}</td><td>${v.valueUSD?fmt.pct(f7*52/v.valueUSD,0):'–'}</td><td>${c.rank?'#'+c.rank:'–'}</td><td>${c.nextLiq?fmt.usd(c.nextLiq,1)+' · '+c.nextDex:'–'}</td></tr>`;}).join('');
const HD = Object.keys(HIST).filter(d=>HIST[d]&&HIST[d].reserve).sort();
const comp = (h)=>{if(!h||!h.reserve) return null; const r=h.reserve, o={}; Object.entries(h.lp||{}).forEach(([s,v])=>o[pname(s)]=v.valueUSD); o['USDG']=r.safeUsdg; o['ETH (Safe + vaults)']=(r.safeEth+r.contractionEth+r.expansionEth)*(h.ethusd||L.ethusd); o['Stock held outside pools']=r.safeStockUsd; o['Total']=r.totalUsd; return o;};
const rc0 = comp(HIST[HD[HD.length-1]]), rc1 = comp(HIST[HD[HD.length-2]]), rc7 = comp(HIST[HD[HD.length-8]]);
const dcell = (a,b)=>a!=null&&b!=null ? `<td class="${a-b>=0?'pos':'neg'}">${fmt.sgn(a-b)}${fmt.usd(a-b,1)}</td><td class="${a-b>=0?'pos':'neg'}">${fmt.sgn(a-b)}${fmt.pct((a-b)/b,1)}</td>` : '<td>–</td><td>–</td>';
document.getElementById('resd_n').textContent = HD.length ? `${HD.length} obs. since ${HD[0].slice(5)}` : '';
document.getElementById('t_resd').innerHTML = rc0 ? '<tr><th>Component</th><th>'+HD[HD.length-1]+'</th><th>Share</th><th>Change, 1 day</th><th>%</th><th>Change, 7 days</th><th>%</th></tr>' +
  Object.keys(rc0).map(k=>`<tr class="${k==='Total'?'sr':''}"><td>${k}</td><td>${fmt.usd(rc0[k])}</td><td>${k==='Total'?'':fmt.pct(rc0[k]/rc0.Total,1)}</td>${dcell(rc0[k], rc1&&rc1[k])}${dcell(rc0[k], rc7&&rc7[k])}</tr>`).join('') : '';

const mintAll = sum(S.map(r=>r.mint||0)), bbAll = sum(S.map(r=>r.burnBuyback||0)), depAll = sum(S.map(r=>r.depositBurn||0));
const br = [['Genesis liquidity mint', 100e6], ['+ withdrawals minted to bankers', mintAll], ['− bought back and burned', -bbAll], ['− deposited to branches (burned to ledger)', -depAll], ['± other', L.totalSupply-(100e6+mintAll-bbAll-depAll)], ['= Minted supply (market capitalization basis)', L.totalSupply, 'tot'],
  ['− held in the protocol\'s STANDARD/ETH pool', -L.poolStd], ['− Incentives Vault (purchased, undistributed)', -L.incentivesStd], ['= Outstanding supply', L.float, 'tot'], ['− locked in S-Bills', -L.sbillsStd], ['− team wallet', -L.teamStd], ['= Free float', L.float-L.sbillsStd-L.teamStd, 'tot'], ['= Fully diluted (minted + pending issuance)', L.totalSupply+L.pending, 'tot'], ['Maximum supply after burns', L.maxSupply]];
document.getElementById('bridge').innerHTML = br.map(b=>`<div class="${b[2]||''}">${b[0]}</div><div class="${b[2]||''}">${fmt.n(b[1],2)}</div>`).join('');
document.getElementById('mc_now').textContent = fmt.usd(mcFloat)+' outstanding · '+fmt.usd(mcTotal)+' minted';
document.getElementById('exitfee').textContent = 'resolution fee '+fmt.pct(L.exitFeeNow,1);
document.getElementById('sb_now').textContent = `${fmt.int(L.branches)} branches · ${fmt.int(L.activeCharters)} charters`;
document.getElementById('px_now').textContent = `${fmt.usd(mcTotal)} minted · ${fmt.usd(mcFloat)} outstanding`;
const y7 = s7.length? inc7*365/7/mcFloat : null;
document.getElementById('yield_now').textContent = y7!=null ? fmt.pct(y7,1)+' annualized' : '';
document.getElementById('inc7').textContent = fmt.usd(inc7)+' last 7 days';
const sp7v = sum(s7.map(r=>r.spVol||0)), sp7f = sum(s7.map(r=>r.spFee||0));
document.getElementById('sp7').textContent = `${fmt.usd(sp7v,2)} volume · ${fmt.usd(sp7f,1)} fees, 7 days`;

// ---------- Liquidity hub business ----------
const stockPools = pools.filter(p=>!L.lp[p].isEth), allPools = pools;
const spf = (r,ps)=>sum(ps.map(p=>r['spFee_'+p]||0)), spv = (r,ps)=>sum(ps.map(p=>r['spVol_'+p]||0));
const poolFees7 = sum(s7.map(r=>spf(r,allPools))), eqFees7 = sum(s7.map(r=>spf(r,stockPools))), ethFees7 = sum(s7.map(r=>r['spFee_ETH']||0));
const poolVol7 = sum(s7.map(r=>spv(r,allPools))), poolFeesY = spf(Y,allPools);
const poolLiq = sum(allPools.map(p=>L.lp[p].valueUSD)), poolYield = poolLiq?poolFees7*52/poolLiq:null;
const ctxS = stockPools.map(p=>ctx[p]||{}), ctxE = ctx['ETH']||{};
const srV = sum(ctxS.map(c=>c.srVol24||0)), allV = sum(ctxS.map(c=>c.totalVol24||0)), srL = sum(stockPools.map(p=>L.lp[p].valueUSD)), allL = sum(ctxS.map(c=>c.totalLiq||0));
const firstEq = (S.find(r=>spv(r,allPools)>0)||{}).date;
const zf7 = sum(s7.map(r=>r.spVolZeroFee||0)), spAll7 = sum(s7.map(r=>r.spVol||0));
const poolAnn = poolFees7*52;
document.getElementById('eq_stats').innerHTML = [
  ['Pool fee income, 7 days', fmt.usd(poolFees7), `${fmt.pct(inc7?poolFees7/inc7:null,0)} of total fee income`, `equities ${fmt.usd(eqFees7)} · ETH/USDG ${fmt.usd(ethFees7)} · ${fmt.usd(poolAnn)} annualized`],
  ['Capital deployed in pools', fmt.usd(poolLiq), `${fmt.pct(poolLiq/L.reserve.totalUsd,0)} of reserve assets`, `${fmt.pct(poolYield,0)} annualized yield · ${allPools.length} pools since ${firstEq?new Date(firstEq+'T00:00:00Z').toLocaleDateString('en-GB',{day:'numeric',month:'short',timeZone:'UTC'}):'–'}`],
  ['Share of on-chain equity volume', fmt.pct(allV?srV/allV:null,0), `24-hour window`, `${fmt.pct(ctxE.totalVol24?ctxE.srVol24/ctxE.totalVol24:null,1)} of ETH/USDG volume · reserve share of its ETH/USDG pool ${fmt.pct(L.lp.ETH?L.lp.ETH.share:null,0)}`],
  ['Fee-paying share of volume', fmt.pct(spAll7?1-zf7/spAll7:null,0), `trailing 7 days`, `${fmt.usd(zf7,1)} of ${fmt.usd(spAll7,1)} transacted through the fee-exempt contract`],
].map(k=>`<div><div class="l">${k[0]}</div><div class="v">${k[1]}<small>${k[2]}</small></div><div class="s">${k[3]}</div></div>`).join('');
document.getElementById('eq_n').textContent = `${fmt.usd(poolFees7)} trailing 7 days`;
const bb7usd = sum(s7.map(r=>((r.burnBuyback||0)+(r.toIncentives||0))*(r.price||L.price)));
const cut7 = DATA.pulledAt - 7*86400, E7 = E.filter(e=>e.settledAt>=cut7);
const vExp = sum(E7.filter(isExp).map(e=>e.toVault)), vCon = sum(E7.filter(e=>!isExp(e)).map(e=>e.toVault)), pol7 = sum(E7.map(e=>e.toPol)), team7 = sum(E7.map(e=>e.team)), rt7 = sum(E7.map(e=>e.routed)), rtCh7 = sum(E7.map(e=>e.charterEth));
const went = [
  ['Reserve backing', eqFees7+ethFees7+vExp*L.ethusd, C.peri, `pool fee income ${fmt.usd(eqFees7+ethFees7)} · expansion vault ${fmt.usd(vExp*L.ethusd)}`],
  ['Buybacks', (vCon+pol7)*L.ethusd, C.gold, `contraction vault ${fmt.usd(vCon*L.ethusd)} · POL ${fmt.usd(pol7*L.ethusd)} · ${fmt.n(bb7,2)} STANDARD purchased`],
  ['Team allocation', team7*L.ethusd, C.peach, `15% of ${rt7.toFixed(1)} ETH distributed`],
  ['Collected, pending settlement', (L.accruedEth||0)*L.ethusd, C.dim, `${(L.accruedEth||0).toFixed(1)} ETH collected in the current epoch`],
];
const wTot = sum(went.map(w=>w[1]));
document.getElementById('went_bar').innerHTML = went.map(w=>`<div style="width:${(100*w[1]/wTot).toFixed(2)}%;background:${w[2]}" title="${w[0]}"></div>`).join('');
document.getElementById('went_leg').innerHTML = went.map(w=>`<i style="background:${w[2]}"></i><span>${w[0]}</span><span class="v">${fmt.usd(w[1])}</span><span class="p">${fmt.pct(w[1]/wTot,0)}</span><span class="sub">${w[3]}</span>`).join('');
document.getElementById('went_src').textContent = `Total ${fmt.usd(wTot)}. Token fees and charter proceeds reflect the ${E7.length} epochs settled in the window (${rt7.toFixed(1)} ETH, of which ${rtCh7.toFixed(1)} ETH charter proceeds).`;

// ---------- range-dependent charts ----------
let N = 30, charts = [];
const mk = (el, cfg)=>{const c=new Chart(el, cfg); charts.push(c); return c;};
function draw(){
  charts.forEach(c=>c.destroy()); charts = [];
  const Rl = last(Sh, N), Rf = last(Sp, N);                 // levels (incl. today) and flows (complete days)
  const ll = Rl.map(r=>r.date.slice(5)), lf = Rf.map(r=>r.date.slice(5));
  const dl = Rl.map(r=>r.date), df = Rf.map(r=>r.date);
  const g = (k)=>Rf.map(r=>r[k]||0);
  const tt = (f)=>({callbacks:{label:c=>c.dataset.label+': '+f(c.parsed.y)}});
  mk(c_price, {data:{labels:ll, datasets:[
    {type:'line', label:'Price (USD)', data:Rl.map(r=>r.price), borderColor:C.gold, backgroundColor:'rgba(255,221,138,.10)', fill:true, pointRadius:0, tension:.25, yAxisID:'y'},
    {type:'line', label:'Market capitalization, minted supply', data:Rl.map(r=>r.mcTotal), borderColor:C.water, pointRadius:0, tension:.25, yAxisID:'y1'},
    {type:'line', label:'Market capitalization, outstanding', data:Rl.map(r=>r.mcFloat), borderColor:C.peri, pointRadius:0, tension:.25, yAxisID:'y1'},
  ]}, options:{maintainAspectRatio:false, plugins:{bands:{dates:dl}, tooltip:{callbacks:{label:c=>c.dataset.yAxisID==='y1'?c.dataset.label+': '+fmt.usd(c.parsed.y,2):c.dataset.label+': $'+c.parsed.y.toFixed(4)}}}, scales:{x:{grid:{display:false}, ticks:{maxTicksLimit:10}}, y:{position:'left', ticks:{callback:v=>'$'+v.toFixed(2)}}, y1:{position:'right', grid:{display:false}, beginAtZero:true, ticks:{callback:v=>fmt.usd(v,0)}}}}});
  const roll = Rf.map((r,i)=>{const idx=Sp.indexOf(r); const win=Sp.slice(Math.max(0,idx-6),idx+1); return (win.length===7&&win[0].date>=ep2)?sum(win.map(inc)):null;});
  mk(c_yield, {data:{labels:lf, datasets:[
    {type:'bar', label:'Fee income, trailing 7 days', data:roll, backgroundColor:'rgba(185,166,227,.35)', yAxisID:'y', order:2},
    {type:'line', label:'Annualized yield on market capitalization, outstanding', data:roll.map((v,i)=>v!=null&&Rf[i].mcFloat?v*365/7/Rf[i].mcFloat:null), borderColor:C.gold, pointRadius:0, tension:.25, yAxisID:'y1', order:1},
  ]}, options:{maintainAspectRatio:false, plugins:{bands:{dates:df}, tooltip:{callbacks:{label:c=>c.dataset.yAxisID==='y1'?c.dataset.label+': '+fmt.pct(c.parsed.y,1):c.dataset.label+': '+fmt.usd(c.parsed.y,1)}}}, scales:{x:{grid:{display:false}, ticks:{maxTicksLimit:8}}, y:{position:'left', ticks:{callback:v=>fmt.usd(v,0)}}, y1:{position:'right', grid:{display:false}, beginAtZero:true, ticks:{callback:v=>fmt.pct(v,0)}}}}});
  const eqRoll = Rf.map(r=>{const idx=Sp.indexOf(r); const win=Sp.slice(Math.max(0,idx-6),idx+1); const t=sum(win.map(inc)); return (win.length===7&&t&&win[0].date>=ep2)?sum(win.map(w=>spf(w,allPools)))/t:null;});
  mk(c_equity, {data:{labels:lf, datasets:[
    ...allPools.map((p,i)=>({type:'bar', label:pname(p)+' fees', data:Rf.map(r=>r['spFee_'+p]||0), backgroundColor:p==='ETH'?C.peach:[C.peri,C.lav,C.rose,C.water,C.green][i%5], stack:'a', yAxisID:'y', order:2})),
    {type:'line', label:'Pool fee income as a share of total, trailing 7 days', data:eqRoll, borderColor:C.gold, pointRadius:0, tension:.25, yAxisID:'y1', order:1},
  ]}, options:{maintainAspectRatio:false, scales:{x:{stacked:true, grid:{display:false}}, y:{stacked:true, ticks:{callback:v=>fmt.usd(v,1)}}, y1:{position:'right', grid:{display:false}, min:0, max:1, ticks:{callback:v=>fmt.pct(v,0)}}}, plugins:{bands:{dates:df}, tooltip:{callbacks:{label:c=>c.dataset.yAxisID==='y1'?c.dataset.label+': '+fmt.pct(c.parsed.y,1):c.dataset.label+': '+fmt.usd(c.parsed.y,1)}}}}});
  mk(c_income, {type:'bar', data:{labels:lf, datasets:[
    {label:'Token trading fees', data:Rf.map(r=>(r.tradingFeeEth||0)*ethOf(r)), backgroundColor:C.lav, stack:'a'},
    {label:'Charter auction proceeds', data:Rf.map(r=>(r.charterEth||0)*ethOf(r)), backgroundColor:C.gold2, stack:'a'},
    {label:'Pool fee income', data:g('spFee'), backgroundColor:C.peach, stack:'a'},
  ]}, options:{maintainAspectRatio:false, scales:{x:{stacked:true,grid:{display:false}}, y:{stacked:true, ticks:{callback:v=>fmt.usd(v,0)}}}, plugins:{bands:{dates:df}, tooltip:tt(v=>fmt.usd(v,1))}}});
  const pcol = [C.peri, C.lav, C.rose, C.water, C.green, C.gold2];
  mk(c_pools, {data:{labels:lf, datasets:[
    ...pools.map((p,i)=>({type:'bar', label:pname(p)+' volume', data:Rf.map(r=>r['spVol_'+p]||0), backgroundColor:p==='ETH'?C.peach:pcol[i%pcol.length], stack:'v', yAxisID:'y', order:2})),
    {type:'line', label:'Fee income', data:g('spFee'), borderColor:C.gold, backgroundColor:C.gold, pointRadius:2, yAxisID:'y1', order:1, tension:.25},
    {type:'line', label:'Share of volume at zero fee', data:Rf.map(r=>r.spVol?r.spVolZeroFee/r.spVol:null), borderColor:C.muted, pointRadius:0, yAxisID:'y2', order:0},
  ]}, options:{maintainAspectRatio:false, scales:{x:{stacked:true, grid:{display:false}}, y:{stacked:true, ticks:{callback:v=>fmt.usd(v,1)}}, y1:{position:'right', grid:{display:false}, ticks:{callback:v=>fmt.usd(v,1)}}, y2:{display:false, min:0, max:1}}, plugins:{tooltip:{callbacks:{label:c=>c.dataset.yAxisID==='y2'?c.dataset.label+': '+fmt.pct(c.parsed.y,0):c.dataset.label+': '+fmt.usd(c.parsed.y,1)}}}}});
  mk(c_mc, {data:{labels:ll, datasets:[
    {type:'bar', label:'Daily change in outstanding supply, USD', data:Rl.map(r=>r.dSupply||0), backgroundColor:Rl.map(r=>(r.dSupply||0)>=0?C.green:C.red), yAxisID:'y1', order:2},
    {type:'line', label:'Market capitalization, outstanding', data:Rl.map(r=>r.mcFloat), borderColor:C.gold, backgroundColor:'rgba(255,221,138,.12)', fill:true, pointRadius:0, tension:.25, yAxisID:'y', order:1},
  ]}, options:{maintainAspectRatio:false, scales:{x:{stacked:true, grid:{display:false}}, y:{position:'left', ticks:{callback:v=>fmt.usd(v,0)}}, y1:{position:'right', stacked:true, grid:{display:false}, ticks:{callback:v=>fmt.usd(v,1)}}}, plugins:{bands:{dates:dl}, tooltip:tt(v=>fmt.usd(v,2))}}});
  mk(c_flows, {type:'bar', data:{labels:lf, datasets:[
    {label:'Withdrawals minted', data:g('mint'), backgroundColor:C.green, stack:'a'},
    {label:'Vault distributions', data:g('fromIncentives'), backgroundColor:C.water, stack:'a'},
    {label:'Buyback and burn', data:g('burnBuyback').map(v=>-v), backgroundColor:C.red, stack:'a'},
    {label:'POL buyback', data:g('toIncentives').map(v=>-v), backgroundColor:C.peach, stack:'a'},
    {label:'Deposits (burned)', data:g('depositBurn').map(v=>-v), backgroundColor:C.dim, stack:'a'},
    {label:'Net market purchases (sales negative)', data:Rf.map(r=>-((r.poolIn||0)-(r.poolOut||0))), backgroundColor:'rgba(185,166,227,.45)', stack:'b'},
  ]}, options:{maintainAspectRatio:false, scales:{x:{stacked:true, grid:{display:false}}, y:{stacked:true, ticks:{callback:v=>fmt.n(v,0)}}}, plugins:{bands:{dates:df}, tooltip:tt(v=>fmt.n(v,2)+' STANDARD')}}});
  const burned = (r)=>(r.licBurn||0)+(r.exitFeeBurn||0)+(r.revokeFeeBurn||0);
  mk(c_issue, {data:{labels:lf, datasets:[
    {type:'bar', label:'Issued to branches', data:g('issuance'), backgroundColor:'rgba(185,166,227,.55)', order:2},
    {type:'bar', label:'Burned before minting', data:Rf.map(burned), backgroundColor:C.gold2, order:2},
    {type:'line', label:'Net issuance', data:Rf.map(r=>(r.issuance||0)-burned(r)), borderColor:C.green, pointRadius:0, tension:.25, order:1},
  ]}, options:{maintainAspectRatio:false, scales:{x:{grid:{display:false}}, y:{ticks:{callback:v=>fmt.n(v,0)}}}, plugins:{bands:{dates:df}, tooltip:tt(v=>fmt.n(v,2)+' STANDARD')}}});
  mk(c_bank, {data:{labels:lf, datasets:[
    {type:'bar', label:'Deposits', data:g('deposits'), backgroundColor:C.green, stack:'a', order:2},
    {type:'bar', label:'Withdrawals (gross)', data:g('wdGross').map(v=>-v), backgroundColor:C.peach, stack:'a', order:2},
    {type:'line', label:'Pending ledger', data:g('pending'), borderColor:C.gold, pointRadius:0, tension:.25, yAxisID:'y1', order:1},
  ]}, options:{maintainAspectRatio:false, scales:{x:{stacked:true, grid:{display:false}}, y:{stacked:true, ticks:{callback:v=>fmt.n(v,0)}}, y1:{position:'right', grid:{display:false}, beginAtZero:true, ticks:{callback:v=>fmt.n(v,1)}}}, plugins:{tooltip:tt(v=>fmt.n(v,2)+' STANDARD')}}});
  mk(c_policy, {data:{labels:ll, datasets:[
    {type:'line', label:'Branches', data:Rl.map(r=>r.branches), borderColor:C.peri, backgroundColor:'rgba(143,162,240,.12)', fill:true, pointRadius:0, tension:.2},
    {type:'line', label:'Active charters', data:Rl.map(r=>r.activeCharters), borderColor:C.rose, pointRadius:0, tension:.2},
  ]}, options:{maintainAspectRatio:false, scales:{x:{grid:{display:false}, ticks:{maxTicksLimit:10}}, y:{beginAtZero:true, ticks:{callback:v=>fmt.n(v,1)}}}, plugins:{bands:{dates:dl}, tooltip:tt(v=>fmt.int(v))}}});
}
draw();
document.querySelectorAll('#range button').forEach(b=>b.addEventListener('click',()=>{N=+b.dataset.n; document.querySelectorAll('#range button').forEach(x=>x.classList.toggle('on',x===b)); draw();}));

// ---------- daily log, since launch ----------
const resOf = (d)=>HIST[d]&&HIST[d].reserveUsd!=null?HIST[d].reserveUsd:null;
const cols = [
  ['Date', r=>r.date, r=>r.date],
  ['Price', r=>r.price!=null?'$'+r.price.toFixed(4):'–', r=>r.price],
  ['Market cap (minted)', r=>fmt.usd(r.mcTotal), r=>r.mcTotal],
  ['Market cap (outstanding)', r=>fmt.usd(r.mcFloat), r=>r.mcFloat],
  ['Outstanding', r=>fmt.n(r.float,2), r=>r.float],
  ['Fee income ($)', r=>fmt.usd(inc(r),1), r=>inc(r)],
  ['Distributed (ETH)', r=>(r.routedEth||0).toFixed(1), r=>r.routedEth||0],
  ['Charters sold', r=>r.chartersSold?`${r.chartersSold} @ ${(r.charterEth/r.chartersSold).toFixed(2)}`:'–', r=>r.chartersSold||0],
  ['Charter proceeds (ETH)', r=>(r.charterEth||0).toFixed(2), r=>r.charterEth||0],
  ['License close', r=>r.licClose?fmt.int(r.licClose):'–', r=>r.licClose||''],
  ['Licenses', r=>fmt.int(r.licCount||0), r=>r.licCount||0],
  ['Branches', r=>fmt.int(r.branches), r=>r.branches],
  ['Charters', r=>fmt.int(r.activeCharters), r=>r.activeCharters],
  ['Multiplier', r=>r.multiplier!=null?r.multiplier.toFixed(2)+'×':'–', r=>r.multiplier],
  ['Issued', r=>fmt.n(r.issuance||0,1), r=>r.issuance||0],
  ['Buyback burn', r=>fmt.n(r.burnBuyback||0,1), r=>r.burnBuyback||0],
  ['POL buyback', r=>fmt.n(r.toIncentives||0,1), r=>r.toIncentives||0],
  ['Deposits', r=>fmt.n(r.deposits||0,1), r=>r.deposits||0],
  ['Withdrawn', r=>fmt.n(r.wdGross||0,1), r=>r.wdGross||0],
  ['Pending', r=>fmt.n(r.pending,2), r=>r.pending],
  ['Resolution fee', r=>fmt.pct(r.exitFee,1), r=>r.exitFee],
  ['S-Bill rate', r=>r.sbRate!=null?(r.sbRate*100).toFixed(2)+'%':'–', r=>r.sbRate==null?'':r.sbRate],
  ['S-Bills locked', r=>fmt.n(r.sbills,2), r=>r.sbills],
  ['Team STANDARD', r=>fmt.n(r.teamStd,2), r=>r.teamStd],
  ['Pool volume', r=>fmt.usd(r.spVol||0,1), r=>r.spVol||0],
  ['Pool fee income', r=>fmt.usd(r.spFee||0,1), r=>r.spFee||0],
  ['Reserve', r=>resOf(r.date)!=null?fmt.usd(resOf(r.date)):'–', r=>resOf(r.date)??''],
  ['Regime', r=>regime[r.date]===undefined?'–':regime[r.date]?'exp':'con', r=>regime[r.date]===undefined?'':regime[r.date]?'expansion':'contraction'],
];
// supply / pool / float table
const fl = (r,i)=>{const p=i>0?Sh[i-1]:null; const mint=r.mint||0, dep=r.depositBurn||0, bb=r.burnBuyback||0, toInc=r.toIncentives||0, fromInc=r.fromIncentives||0;
  const mkt=(r.poolIn||0)-((r.poolOut||0)-toInc-bb), prot=toInc+bb;
  return {p, dS:p?r.supply-p.supply:null, dP:p?r.pool-p.pool:null, dI:p?r.incentives-p.incentives:null, dF:p?r.float-p.float:null, mint, dep, bb, mkt, prot};};
const frows = Sh.map((r,i)=>({r, ...fl(r,i)})).reverse();
const sc = (v,inv)=>v==null?'<td>–</td>':`<td class="${(inv?-v:v)>0?'pos':(inv?-v:v)<0?'neg':'mut'}">${Math.abs(v)<0.5?'0':fmt.sgn(v)+fmt.n(v,2)}</td>`;
document.getElementById('t_float').innerHTML = '<tr><th>Date</th><th>Minted supply</th><th>Change</th><th>+ Withdrawals minted</th><th>− Deposits to branches</th><th>− Buybacks burned</th><th>Protocol pool</th><th>Change</th><th>+ Net market sales</th><th>− Buyback purchases</th><th>Incentives Vault change</th><th>Outstanding</th><th>Change</th><th>%</th><th>Price</th></tr>' +
  frows.map((x,i)=>`<tr class="${x.r.date===L.date?'today':''}${i>=10?' more':''}"><td>${x.r.date}</td><td>${fmt.n(x.r.supply,2)}</td>${sc(x.dS)}${sc(x.mint)}${sc(-x.dep)}${sc(-x.bb)}<td>${fmt.n(x.r.pool,2)}</td>${sc(x.dP,true)}${sc(x.mkt,true)}${sc(-x.prot,true)}${sc(x.dI,true)}<td>${fmt.n(x.r.float,2)}</td>${sc(x.dF)}<td class="${x.dF>0?'pos':x.dF<0?'neg':''}">${x.p?fmt.sgn(x.dF)+fmt.pct(x.dF/x.p.float,2):'–'}</td><td>${x.r.price!=null?'$'+x.r.price.toFixed(4):'–'}</td></tr>`).join('');
document.getElementById('fmore').textContent = `View all ${frows.length} days`;
document.getElementById('fmore').addEventListener('click',()=>{const t=document.getElementById('t_float'); t.classList.toggle('open'); document.getElementById('fmore').textContent = t.classList.contains('open')?'View 10 days':`View all ${frows.length} days`;});
[['fold_ep','f_ep','ledger'],['fold_rs','f_rs','table']].forEach(([b,f,n])=>{const B=document.getElementById(b), F=document.getElementById(f); B.addEventListener('click',()=>{F.classList.toggle('open'); B.textContent=(F.classList.contains('open')?'Hide ':'View ')+n;});});
document.querySelectorAll('.panel').forEach(pn=>{const d=pn.querySelector(':scope > .h .d'), src=pn.querySelector(':scope > .src'); let tip=pn.querySelector(':scope > .tip');
  if(!tip && (d||src)){const i=document.createElement('span'); i.className='i'; i.tabIndex=0; i.textContent='i'; tip=document.createElement('div'); tip.className='tip'; pn.prepend(tip); pn.prepend(i);}
  if(tip){ if(d && d.textContent.trim() && !tip.textContent.includes(d.textContent.trim().slice(0,40))) tip.innerHTML = d.textContent.trim()+' '+tip.innerHTML; if(src && src.textContent.trim()) tip.innerHTML += '<span class="srcnote">'+src.textContent.trim()+'</span>'; }});
const logRows = Sh.slice().reverse();
document.getElementById('t_log').innerHTML = '<tr>'+cols.map(c=>'<th>'+c[0]+'</th>').join('')+'</tr>' +
  logRows.map((r,i)=>`<tr class="${r.date===L.date?'today':''}${i>=10?' more':''}">`+cols.map(c=>'<td>'+c[1](r)+'</td>').join('')+'</tr>').join('');
document.getElementById('more').textContent = `View all ${logRows.length} days`;
document.getElementById('more').addEventListener('click',()=>{const t=document.getElementById('t_log'); t.classList.toggle('open'); document.getElementById('more').textContent = t.classList.contains('open')?'View 10 days':`View all ${logRows.length} days`;});
document.getElementById('csv').addEventListener('click',()=>{
  const esc = v=>{v=v==null?'':String(v); return /[",\n]/.test(v)?'"'+v.replace(/"/g,'""')+'"':v;};
  const csv = [cols.map(c=>esc(c[0])).join(',')].concat(Sh.map(r=>cols.map(c=>esc(c[2](r))).join(','))).join('\n');
  const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([csv],{type:'text/csv'})); a.download = 'standard-reserve-daily-'+L.date+'.csv'; a.click();
});
</script>
"""

html = (TEMPLATE.replace("__HERO__", hero).replace("__ASOF_UTC__", built.strftime("%Y-%m-%d %H:%M")).replace("__ASOF_KST__", kst.strftime("%m-%d %H:%M"))
        .replace("__TIP__", f"{data['tip']:,}").replace("__PERIOD__", str(int(data["live"]["auctionPeriodHours"])))
        .replace("__DATA__", json.dumps({k: v for k, v in data.items() if k != "swaps"}, separators=(",", ":"))))
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html"), "w").write(html)
print("index.html", len(html) // 1024, "KB")
