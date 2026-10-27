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
.hero .title{position:absolute;left:0;right:0;bottom:22px;z-index:2;padding-inline:clamp(16px,4vw,48px);display:flex;align-items:flex-end}
.hero h1{margin:0;font-weight:600;font-size:clamp(26px,4.2vw,44px);letter-spacing:-.02em;text-wrap:balance;text-shadow:0 2px 18px rgba(14,12,21,.6)}
.hero h1 small{display:block;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--lav);font-weight:500;margin-bottom:8px}
.asof{font-family:var(--mono);font-size:12px;color:var(--water);text-align:left;line-height:1.5;margin-top:12px}
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
#t_pools th{white-space:normal;line-height:1.25;vertical-align:bottom;min-width:56px}
a.hl{color:inherit;text-decoration:underline;text-decoration-style:dotted;text-underline-offset:3px}a.hl:hover{color:var(--fg)}
#t_slip th,#t_sellers th,#t_cpty th,#t_pnl th{white-space:normal;line-height:1.25;vertical-align:bottom} #t_slip td,#t_sellers td,#t_cpty td,#t_cpty th{padding:6px 5px} #t_cpty .cpf{border-left:1px solid var(--line2);padding-left:10px} #t_cpty th.cpg{text-align:center;border-bottom:1px solid var(--line2)} #t_sellers td:nth-child(2){white-space:normal;text-align:left;font-family:var(--sans)} #t_sellers th:nth-child(2){text-align:left}
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
  .wrap{padding-inline:12px;padding-bottom:40px}
  .hero{height:210px} .hero h1{font-size:26px} .hero h1 small{font-size:10px;letter-spacing:.1em;margin-bottom:5px}
  .asof{font-size:11px;margin-top:8px}
  .nav{flex-wrap:nowrap;overflow-x:auto;scrollbar-width:none;padding:6px 12px;gap:0;-webkit-mask-image:linear-gradient(90deg,#000 88%,transparent)} .nav::-webkit-scrollbar{display:none} .nav a{white-space:nowrap;padding:6px 8px}
  .kpis{gap:8px;margin-block:14px 18px} .kpi{min-height:0;padding:12px 12px 10px} .kpi .l{font-size:9.5px;letter-spacing:.08em;white-space:normal;overflow:visible;line-height:1.3}
  .kpi .v{font-size:20px;margin-top:4px} .kpi .s{white-space:normal;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;min-height:0;padding-top:4px;font-size:11px}
  .kpis.small{gap:8px;margin-top:-10px} .kpis.small .kpi{min-height:0;padding:10px 12px 8px} .kpis.small .v{font-size:16px} .kpis.small .s{min-height:0}
  h2{margin:26px 0 10px} h2 .hint{display:none}
  .panel{padding:14px 14px 12px;border-radius:10px}
  .panel .h{flex-wrap:wrap;align-items:flex-start;gap:4px 10px;padding-right:22px;min-height:0}
  .panel .t{white-space:normal;line-height:1.3;font-size:14.5px}
  .panel .h>div:last-child{width:100%;justify-content:flex-start;flex-wrap:wrap;gap:8px}
  .panel .n{white-space:normal;text-align:left;font-size:11.5px;line-height:1.45}
  .panel>.i{top:14px;right:12px} .panel>.tip{width:calc(100vw - 48px);right:8px;top:36px}
  .ch{height:390px;margin-top:6px}
  .stats{grid-template-columns:1fr 1fr;gap:8px} .stats>div{padding:9px 10px} .stats .v{font-size:20px;white-space:normal} .stats .v small{display:block;margin-left:0;margin-top:2px} .stats .s{font-size:10.5px}
  .legend2{font-size:12px} .bridge{font-size:11.5px}
  table{font-size:11.5px} th{font-size:9.5px;padding:5px 6px} td{padding:6px 6px}
  .tw table th:first-child,.tw table td:first-child{position:sticky;left:0;background:var(--panel);z-index:1;box-shadow:4px 0 8px -4px rgba(0,0,0,.6)}
  .btn{font-size:10.5px;padding:4px 10px}
}
.strip{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:22px}
@media (max-width:900px){.strip{grid-template-columns:1fr}}
.sc{position:relative;background:linear-gradient(180deg,var(--panel2),var(--panel));border:1px solid var(--line2);border-radius:12px;padding:16px 18px 12px;min-width:0}
.sc .l{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--lav);padding-right:22px}
.sc .v{font-family:var(--mono);font-size:30px;color:var(--gold);margin-top:6px;font-variant-numeric:tabular-nums;white-space:nowrap}
.sc .s{font-family:var(--mono);font-size:12px;color:var(--fg);margin-top:4px;font-variant-numeric:tabular-nums}
.sc .t{font-family:var(--mono);font-size:11.5px;color:var(--muted);margin-top:2px;font-variant-numeric:tabular-nums}
.sc svg{display:block;width:100%;height:46px;margin-top:10px}
.sc .i{position:absolute;top:12px;right:12px;width:16px;height:16px;border-radius:50%;border:1px solid var(--line2);color:var(--dim);font-size:10px;font-family:var(--mono);display:flex;align-items:center;justify-content:center;cursor:help}
.sc .tip{display:none;position:absolute;right:8px;top:32px;z-index:30;width:300px;background:var(--panel2);border:1px solid var(--line2);border-radius:8px;padding:10px 12px;font-size:12px;color:var(--fg);line-height:1.45;box-shadow:0 10px 28px rgba(0,0,0,.45)}
.sc .i:hover + .tip,.sc .i:focus + .tip{display:block}
.stats1{display:grid;grid-template-columns:auto 1fr;gap:4px 14px;margin-top:12px;font-family:var(--mono);font-size:12px} .stats1 div:nth-child(odd){font-family:var(--sans);color:var(--muted)} .stats1 div:nth-child(even){text-align:right}
@media (max-width:600px){.sc .v{font-size:24px} .sc .tip{width:calc(100vw - 48px)}}
.foot{margin-top:40px;color:var(--dim);font-size:12px;font-family:var(--mono);line-height:1.7}
</style>

<div class="hero">
  <img src="__HERO__" alt="Standard Reserve: the reserve dam at dusk">
  <div class="title">
    <div><h1><small>Standard Reserve · Robinhood Chain</small>Protocol Monitor</h1>
    <div class="asof" id="asof">As of <b>__ASOF_UTC__ UTC</b> · block __TIP__ · <span id="epochpill" class="pill"></span></div></div>
  </div>
</div>
<nav class="nav">
  <a href="#market">Market</a><a href="#revenue">Revenue</a><a href="#equity">Liquidity business</a><a href="#auctions">Auctions</a><a href="#reserve">Reserve</a><a href="#supply">Supply</a><a href="#bank">Banking</a><a href="#log">Data log</a>
  <span class="sp"></span>
  <span class="seg" id="range"><button data-n="7">7d</button><button data-n="30" class="on">30d</button><button data-n="0">all</button></span>
</nav>

<div class="wrap">
  <div class="strip" id="strip"></div>
  <div class="kpis" id="kpis"></div>
  <div class="kpis small" id="kpis2"></div>

  <h2 id="market">Market <span class="hint">Shaded intervals denote contraction epochs.</span></h2>
  <div class="grid">
    <div class="panel w8"><span class="i" tabindex="0">i</span><div class="tip">Price is the GeckoTerminal daily close for the STANDARD/ETH pool. Market capitalization on minted supply corresponds to the figure quoted by DexScreener and GeckoTerminal. Market capitalization on outstanding supply excludes STANDARD held in the protocol’s own pool and in the Incentives Vault. Shaded intervals denote contraction epochs.</div><div class="h"><div><div class="t">Token price and market capitalization</div><div class="d">Daily closing price with market capitalization on minted supply and on outstanding supply.</div></div><div class="n" id="px_now"></div></div><div class="ch tall"><canvas id="c_price"></canvas></div><div class="src">Source: GeckoTerminal daily close for the STANDARD/ETH pool; STANDARD transfer logs for supply and outstanding supply; epoch-settled events for the regime.</div></div>
    <div class="panel w4"><span class="i" tabindex="0">i</span><div class="tip">Market capitalization on outstanding supply divided by reserve assets, equivalently token price divided by backing per outstanding token. Reserve assets at each day’s close are rebuilt from on-chain events: ETH in the reserve Safe and both policy vaults from Safe transactions, vault buybacks and forwards, epoch routing and the genesis seeding; USDG and equities held by the Safe from token transfers; and the Safe’s Uniswap v4 positions from liquidity events, valued at the day’s closing pool price. Today uses the reserve read at the compile block. Uncollected position fees are excluded. The reserve bought its tokenized equities on 2 and 13 October, before their pools opened on 14 October; until then they are valued at each pool’s first closing price.</div><div class="h"><div><div class="t">Price to backing, daily</div><div class="d">Market capitalization on outstanding supply as a multiple of reserve assets.</div></div><div class="n" id="pb_now"></div></div><div class="ch tall"><canvas id="c_pb"></canvas></div><div class="src">Source: reserve Safe, policy vault, fee splitter and genesis minter events; ERC-20 transfers; Uniswap v4 ModifyLiquidity and Swap events; Coinbase ETH-USD.</div></div>
    <div class="panel w8"><span class="i" tabindex="0">i</span><div class="tip">STANDARD sold into the protocol’s STANDARD/ETH pool less STANDARD bought from it, from every transfer into and out of the pool; positive values are net sales. A trade is assigned to the wallet that sent STANDARD to the pool or received it; when a router or aggregator stands in between, the same transaction also moves STANDARD between it and a wallet, and that wallet is used. Groups apply in order: the team wallet; bankers, wallets that have bought, deposited into, withdrawn from or checked in a charter; S-Bill holders, wallets that have deposited into S-Bills; high-frequency wallets and bots, with 300 or more pool trades; launch-week buyers, whose first purchase came in the first epoch; and other wallets. Protocol contracts are excluded. The groups sum to net market sales in the supply table.</div><div class="h"><div><div class="t">Net sales into the pool by holder group, daily</div><div class="d">STANDARD sold into the protocol’s STANDARD/ETH pool less STANDARD bought from it.</div></div><div class="n" id="sell_now"></div></div><div class="ch tall"><canvas id="c_sell"></canvas></div><div class="src">Source: every STANDARD Transfer log; charter, deposit, withdrawal, check-in and S-Bill events for group membership.</div></div>
    <div class="panel w4 tw"><span class="i" tabindex="0">i</span><div class="tip">Wallets with the largest net sales into the pool over the last seven complete days. Net is STANDARD sold less STANDARD bought. Trades through routers are assigned to the wallet on the other side of the router.</div><div class="h"><div><div class="t">Largest net sellers, trailing seven days</div><div class="d">Net STANDARD sold into the pool, by wallet.</div></div></div><table id="t_sellers"></table></div>
    <div class="panel w8"><span class="i" tabindex="0">i</span><div class="tip">The ETH, in USD, that moves STANDARD’s price two or five percent in the protocol’s STANDARD/ETH pool. Bid depth is what sellers receive taking the price down; ask depth, in the tooltip, is what buyers pay taking it up. The pool’s liquidity is almost entirely one wide protocol position, so the two sides are close to symmetric. Computed from every open liquidity range in the pool, rebuilt from liquidity events, at each day’s closing pool price. The pool fee and the tax are excluded.</div><div class="h"><div><div class="t">STANDARD/ETH market depth, daily</div><div class="d">ETH that sellers receive taking STANDARD’s price down two and five percent, in USD; ask depth in the tooltip.</div></div><div class="n" id="dp_now"></div></div><div class="ch tall"><canvas id="c_depth"></canvas></div><div class="src">Source: Uniswap v4 ModifyLiquidity and Swap events for the STANDARD/ETH pool; Coinbase ETH-USD.</div></div>
    <div class="panel w4 tw"><span class="i" tabindex="0">i</span><div class="tip">Each trade is simulated against the pool’s open liquidity at the compile block. Price impact is the average execution price against the pool price before costs. Cost is the all-in cost: it adds the pool’s 1% fee and the hook’s tax, 2% on buys and 3% on sells. Sizes are in USD at the compile ETH price. Protocol share is the protocol position’s share of in-range liquidity.</div><div class="h"><div><div class="t">STANDARD/ETH execution cost by size</div><div class="d">Price impact and all-in cost of a market order, by size.</div></div></div><table id="t_slip"></table><div class="stats1" id="slip_s"></div><div class="src">Source: Uniswap v4 StateView and liquidity events for the STANDARD/ETH pool; tax rates from the hook via the indexer.</div></div>
  </div>

  <h2 id="revenue">Revenue <span class="hint">Recurring revenue is token trading fees plus the reserve’s pool fees. Charter sales are shown separately.</span></h2>
  <div class="grid">
    <div class="panel w8"><span class="i" tabindex="0">i</span><div class="tip">Token trading fees are known per three-day epoch and are allocated evenly across its days; the current epoch is estimated from ETH held in the tax hook and fee splitter. Pool fee income is derived from each swap’s fee, weighted by the reserve’s share of in-range liquidity; in the ETH/USDG pool it excludes Uniswap’s protocol fee of 0.0125%. Together they are recurring revenue. Charter sales are auction proceeds for new charters, recorded on the sale date; they sell new bank capacity and are not recurring.</div><div class="h"><div><div class="t">Revenue by source, daily</div><div class="d">Recurring revenue from token trading fees and pool fees, with charter sales alongside, in USD.</div></div><div class="n" id="inc7"></div></div><div class="ch tall"><canvas id="c_income"></canvas></div><div class="src">Source: SR indexer epoch-routed events, charter purchase events, PoolManager swap logs, Coinbase ETH-USD.</div></div>
    <div class="panel w4"><span class="i" tabindex="0">i</span><div class="tip">Market capitalization on outstanding supply at each day’s close divided by trailing seven-day recurring revenue, annualized. Charter sales are excluded. Windows that include the launch epoch are omitted because genesis-day fees distort them.</div><div class="h"><div><div class="t">Price to recurring revenue, daily</div><div class="d">Market capitalization on outstanding supply as a multiple of annualized recurring revenue.</div></div><div class="n" id="prr_now"></div></div><div class="ch tall"><canvas id="c_prr"></canvas></div><div class="src">Source: epoch-routed events and PoolManager swap logs for revenue; transfer logs and GeckoTerminal closes for market capitalization.</div></div>
    <div class="panel"><span class="i" tabindex="0">i</span><div class="tip">In expansion epochs 70% is allocated to the reserve; in contraction epochs 70% is allocated to buybacks and burns. A further 15% purchases STANDARD into the Incentives Vault and 15% is allocated to the team. Gold denotes charter sales within the total.</div><div class="h"><div><div class="t">Income routing by epoch</div><div class="d">Trading fees and charter sales routed by the fee engine at each epoch settlement, in ETH.</div></div></div><div class="ch tall"><canvas id="c_epochs"></canvas></div><div class="src">Source: SR indexer epoch-routed and epoch-settled events.</div></div>
    <div class="panel tw"><span class="i" tabindex="0">i</span><div class="tip">Pool fee income accrues within the reserve’s liquidity positions and does not pass through the fee engine; it therefore adds to backing and funds no buybacks. Token trading fees and charter proceeds are routed at settlement: 70% to the reserve in expansion epochs or to buybacks in contraction epochs, 15% to POL buybacks and 15% to the team. Each day follows its own epoch’s routing; days of the current epoch are not yet routed. The total equals recurring revenue plus charter sales over the same seven days.</div><div class="h"><div><div class="t">Income allocation, trailing seven days</div><div class="d">Recurring revenue and charter sales by destination.</div></div><div class="n" id="went_n"></div></div><div class="bar" id="went_bar"></div><div class="legend2" id="went_leg"></div><div class="src" id="went_src"></div></div>
    <div class="panel w12 tw"><span class="i" tabindex="0">i</span><div class="tip">Net flow is ETH purchased less ETH sold through the pool during the epoch, as reported by the hook; its sign sets the regime. Routed total comprises trading fees and charter sales. The vault allocation is 70%, to the reserve in expansion and to buybacks in contraction. Multiplier after is the issuance multiplier applied from the following epoch.</div><div class="h"><div><div class="t">Epoch settlement ledger</div><div class="d">Net flow determines the regime; routed fees are the levy on total volume and are therefore always positive.</div></div><div><button class="btn" id="fold_ep">View ledger</button></div></div><div class="fold" id="f_ep"><table id="t_epochs"></table></div></div>
  </div>

  <h2 id="equity">Liquidity business <span class="hint">Progress toward a liquidity hub that earns from trading in protocol-owned pools.</span></h2>
  <div class="grid">
    <div class="panel w12"><span class="i" tabindex="0">i</span><div class="tip">Fee income and volume are derived from PoolManager swap logs for the reserve’s pools; liquidity from StateView; competing venues from DexScreener token-pair data for the same assets on Robinhood Chain. Share of chain equity volume is the last complete day’s volume served by the reserve’s liquidity in its three equity pools as a share of every on-chain pool for the same equities; the ETH/USDG figure is the same measure, counting only the volume its own liquidity served in a pool it shares with other providers. Yield is trailing seven-day pool fee income annualized over capital in pools. Fee-exempt volume transacts through an arbitrage contract that pays no fee.</div><div class="h"><div><div class="t">Trading venue economics</div><div class="d">All protocol-owned pools: three tokenized equities and ETH/USDG. Fee income reflects the reserve’s share of in-range liquidity.</div></div></div><div class="stats" id="eq_stats"></div></div>
    <div class="panel" id="p_vshare"><span class="i" tabindex="0">i</span><div class="tip">The volume the reserve’s liquidity served in each pool as a share of all trading volume in the same asset on Robinhood Chain, by UTC day. The reserve is the only provider in the equity pools; in the ETH/USDG pool, which other providers share, only the volume its own liquidity served counts. Every pool DexScreener lists that pairs the asset with USDG or ETH is counted: Uniswap v4 pools from their swap events, and other pools (Uniswap v3, Metric, Ramses, Aero, Alandale and others) from token transfers into and out of the pool, counting transactions in which one token goes in and the other comes out. Memecoins quoted in an equity are not venues for the equity and are excluded. Volume is in USD at the USDG leg, or at the day’s closing price.</div><div class="h"><div><div class="t">Share of chain volume by pool, daily</div><div class="d">Volume served by the reserve’s liquidity as a share of all on-chain volume in the same asset.</div></div><div class="n" id="vs_now"></div></div><div class="ch"><canvas id="c_vshare"></canvas></div><div class="src">Source: Uniswap v4 Swap events; ERC-20 Transfer logs of every other listed pool; pool list from DexScreener.</div></div>
    <div class="panel" id="p_lshare"><span class="i" tabindex="0">i</span><div class="tip">The reserve’s position value as a share of all liquidity in pools pairing the same asset with USDG or ETH on Robinhood Chain, at the day’s close. Uniswap v4 pools are valued from every liquidity event since the pool was created, at the closing pool price; other pools from their token balances. Current values match DexScreener’s pool liquidity within 0.1% for every venue except Metric’s main SPCX pool, whose on-chain token balances are about 10% below DexScreener’s figure.</div><div class="h"><div><div class="t">Share of chain liquidity by pool, daily</div><div class="d">The reserve’s position in each pool as a share of all on-chain liquidity in the same asset.</div></div><div class="n" id="ls_now"></div></div><div class="ch"><canvas id="c_lshare"></canvas></div><div class="src">Source: Uniswap v4 ModifyLiquidity and Swap events; ERC-20 balances of every other listed pool; reserve positions rebuilt from liquidity events.</div></div>
    <div class="panel w8"><span class="i" tabindex="0">i</span><div class="tip">Volume the reserve’s liquidity served in its four pools, by who traded, for each complete UTC day. Fee-exempt swaps are summed exactly. The rest is estimated from 150 trades per pool and day, drawn in proportion to size and read from their transaction receipts. Cross-venue arbitrage: the same transaction trades the asset the opposite way on another pool. Other bots: the trade came through a private contract, one operator’s rotating wallets with near-identical activity, or from a wallet with 1,000 or more transactions. Organic users: a wallet with fewer transactions trading through a public router, one used by wallets whose activity differs tenfold or more. Each day’s shares carry a sampling error of up to eight percentage points; seven-day shares about three.</div><div class="h"><div><div class="t">Pool volume by counterparty, daily</div><div class="d">Volume the reserve’s liquidity served, by organic users, arbitrage and other bots.</div></div><div class="n" id="cp_now"></div></div><div class="ch tall"><canvas id="c_cpty"></canvas></div><div class="src">Source: PoolManager Swap events for the reserve’s pools; receipts and sending-wallet transaction counts of 150 sampled trades per pool and day.</div></div>
    <div class="panel w4 tw"><span class="i" tabindex="0">i</span><div class="tip">Shares of the volume the reserve’s liquidity served in each pool over the last seven complete days, by counterparty as defined in the chart: organic users, cross-venue arbitrage, other bots and the fee-exempt contract. The four volume shares sum to 100%. The last column is a separate measure: the share of the reserve’s fee income in that pool paid by organic users.</div><div class="h"><div><div class="t">Counterparty mix, trailing seven days</div><div class="d">Share of each pool’s volume by counterparty.</div></div></div><table id="t_cpty"></table></div>
    <div class="panel w8"><span class="i" tabindex="0">i</span><div class="tip">Each pool’s result against simply holding what the reserve deposited. Deposits and withdrawals are the reserve’s liquidity changes, valued at the pool price just before each one. Divergence is the position’s value less the value of holding those tokens at the day’s close. Fees are those accrued in the reserve’s positions, read from the pool contract and valued at current prices; earlier days scale the swap-based estimate to that figure. The line is divergence plus fees, cumulative since the pool was seeded.</div><div class="h"><div><div class="t">Pool profit and loss against holding, cumulative</div><div class="d">Fees earned plus divergence from holding the deposited tokens, by pool.</div></div><div class="n" id="pl_now"></div></div><div class="ch tall"><canvas id="c_pnl"></canvas></div><div class="src">Source: the reserve’s ModifyLiquidity events with the pool price before each; daily closing pool prices; PoolManager swap logs for fees.</div></div>
    <div class="panel w4 tw"><span class="i" tabindex="0">i</span><div class="tip">Fees are those accrued in the reserve’s positions since they were seeded, read from the pool contract and valued at current prices; none has been withdrawn. Divergence is the position’s value at the day’s close, excluding uncollected fees, less the value of holding the deposited tokens. Net against holding is fees plus divergence. Net in USD compares value plus fees with the USD cost of the deposits, so it also carries the move in the assets’ prices. Hover a row for cost, value and holding.</div><div class="h"><div><div class="t">Pool profit and loss since seeding</div><div class="d">At the close of the last complete day.</div></div></div><table id="t_pnl"></table></div>
    <div class="panel w12"><div class="h"><div><div class="t">Pool fee income by pool</div><div class="d">Daily fee income earned by the reserve in each pool, with pool fees as a trailing seven-day share of recurring revenue.</div></div><div class="n" id="eq_n"></div></div><div class="ch tall"><canvas id="c_equity"></canvas></div><div class="src">Source: PoolManager swap logs; epoch-routed events.</div></div>
  </div>

  <h2 id="auctions">Auctions</h2>
  <div class="grid">
    <div class="panel"><span class="i" tabindex="0">i</span><div class="tip"><span id="ch_tip"></span> One charter is offered per 12-hour period in a Dutch auction. The price opens at three times the previous clearing price and halves every two hours toward a floor of 1 ETH until a purchase occurs. Proceeds are distributed through the fee engine. Triangles denote purchases executed through a contract.</div><div class="h"><div><div class="t">Charter auction clearing prices</div><div class="d">Clearing price of each charter sold, in ETH.</div></div><div class="n" id="ch_now"></div></div><div class="ch"><canvas id="c_charter"></canvas></div><div class="src">Source: CharterPurchased events on the auction contract; current price from the auction contract.</div></div>
    <div class="panel"><span class="i" tabindex="0">i</span><div class="tip"><span id="lic_tip"></span> Expansion licenses open additional branches, are paid in STANDARD and are burned on purchase. Twenty-five are offered per 12-hour period (24-hour periods at launch), opening at twice the previous clearing price with a floor of approximately two days of one branch’s issuance.</div><div class="h"><div><div class="t">License auction clearing prices and volume</div><div class="d">Period close price in STANDARD and licenses sold per period.</div></div><div class="n" id="lic_now"></div></div><div class="ch"><canvas id="c_license"></canvas></div><div class="src">Source: licenses-purchased events grouped by auction period.</div></div>
  </div>

  <h2 id="reserve">Reserve assets and protocol-owned liquidity</h2>
  <div class="grid">
    <div class="panel w4"><span class="i" tabindex="0">i</span><div class="tip">Comprises ETH and USDG held in the reserve Safe, ETH in the policy vaults, tokenized equities held outside pools, and the Safe’s Uniswap v4 positions. Excludes ETH held by the POL buyback contract and the team wallet.</div><div class="h"><div><div class="t">Reserve composition by asset</div><div class="d">Current reserve holdings, in USD.</div></div><div class="n" id="res_tot"></div></div><div class="ch"><canvas id="c_reserve"></canvas></div><div class="src">Source: Robinhood Chain RPC balances of the reserve Safe, vaults and the Safe's Uniswap v4 positions.</div></div>
    <div class="panel w8"><span class="i" tabindex="0">i</span><div class="tip">Bars are the volume served by the reserve’s own liquidity: each swap’s USDG amount multiplied by the reserve’s share of in-range liquidity at that swap. In the stock pools the reserve is effectively the sole provider, so the bar equals pool volume. The ETH/USDG pool is shared with third-party providers, so its bar is only the reserve’s share; the pool’s total volume and the share served appear in the tooltip. Fee income is weighted the same way. The grey line denotes the share of pool volume transacted at a 0% fee, attributable to a fee-exempt arbitrage contract.</div><div class="h"><div><div class="t">Pool trading volume and fee income</div><div class="d">Daily volume served by the reserve’s liquidity, by pool, with fee income to the reserve and the share of volume transacted at zero fee.</div></div><div class="n" id="sp7"></div></div><div class="ch tall"><canvas id="c_pools"></canvas></div><div class="src">Source: PoolManager swap logs for the reserve’s pools; fee and liquidity from the swap event; the reserve’s in-range liquidity from its positions. Pool totals in the tooltip.</div></div>
    <div class="panel w12 tw"><span class="i" tabindex="0">i</span><div class="tip">Holdings and prices are read from Uniswap v4 StateView and PositionManager; other venues for the same asset from DexScreener. The reserve is the sole liquidity provider in the equity pools but shares the ETH/USDG pool with third-party providers, so fee income reflects its share of in-range liquidity at each swap. Equity pools apply a session fee set by the hook; the ETH/USDG pool applies a fixed tier. Value is the reserve’s position. Volume is the volume served by the reserve’s liquidity, as in the chart above. Yield is trailing seven-day fee income annualized over value. Share of pool is the reserve’s share of in-range liquidity; the chain shares, venues, rank and largest other venue compare the reserve with every pool for the same asset on Robinhood Chain on the last complete day, from on-chain events (see the daily share charts); rank and venues count pools with at least $100 of liquidity. Totals sum the four pools; yield in the total row is on combined value.</div><div class="h"><div><div class="t">Protocol-owned liquidity by pool</div><div class="d">The reserve’s position in each pool and its standing against other venues on the chain. The two chain share columns link to their daily history.</div></div></div><table id="t_pools"></table><div class="src">Source: Uniswap v4 StateView and PositionManager for holdings; on-chain events of every listed pool for the chain columns.</div></div>
    <div class="panel w12 tw"><span class="i" tabindex="0">i</span><div class="tip">Today is the reserve read at the compile block. Earlier closes are rebuilt from on-chain events, as in the price to backing chart, and valued at each day’s closing pool prices and ETH price.</div><div class="h"><div><div class="t">Reserve composition, daily change</div><div class="d">Each reserve component today against the close one day and seven days earlier.</div></div><div><span class="n" id="resd_n"></span> <button class="btn" id="fold_rs">View table</button></div></div><div class="fold" id="f_rs"><table id="t_resd"></table></div><div class="src">Source: Robinhood Chain RPC balances at the compile block; reserve Safe, vault and liquidity events for earlier closes.</div></div>
  </div>

  <h2 id="supply">Supply and market capitalization</h2>
  <div class="grid">
    <div class="panel w4"><span class="i" tabindex="0">i</span><div class="tip">Outstanding supply equals minted supply less STANDARD held in the protocol’s pool less the Incentives Vault. Free float further excludes S-Bill principal, the S-Bill premium pot and the team wallet. DexScreener and GeckoTerminal quote market capitalization on minted supply. Withdrawals are minted from bankers’ ledger balances; deposits are burned into them. Buybacks and other burns tie to the token contract’s burned total.</div><div class="h"><div><div class="t">Supply reconciliation</div><div class="d">From the genesis mint to minted supply, outstanding supply and free float.</div></div></div><div class="bridge" id="bridge"></div><div class="src">Source: STANDARD Transfer logs, deposited and withdrawn events, and balances read at the same block.</div></div>
    <div class="panel w8"><span class="i" tabindex="0">i</span><div class="tip">Issuance does not mint tokens. It credits bankers’ ledger balances, and tokens are minted only when a banker retires a branch. Outstanding supply therefore falls when holders sell into the protocol’s pool or deposit into branches, which converts tokens to ledger, and rises on withdrawals and Incentives Vault distributions. Buybacks burn tokens out of the pool, shrinking the total without touching outstanding supply. Minted supply, the ERC-20 total, is the lower two bands together; minted plus ledger is the full height.</div><div class="h"><div><div class="t">STANDARD supply composition, daily</div><div class="d">Outstanding supply, protocol holdings in the pool and Incentives Vault, and the ledger balance owed to bankers but not yet minted. The full height is every STANDARD that exists or is owed.</div></div><div class="n" id="mc_now"></div></div><div class="ch tall"><canvas id="c_mc"></canvas></div><div class="src">Source: STANDARD transfer logs classified by counterparty; ledger balance from issuance, deposit, license, withdrawal and revocation events.</div></div>
    <div class="panel"><span class="i" tabindex="0">i</span><div class="tip">Outstanding supply rises when withdrawals are minted, when the Incentives Vault distributes, when the market buys from the protocol’s pool, and when the POL manager collects the protocol position’s STANDARD fees and forwards them to the team wallet. It falls when holders sell into the pool, deposit into branches, which burns tokens into the ledger, and when the S-Bills contract burns tokens. Buybacks, POL purchases and the tax hook’s burns take tokens from the pool and leave outstanding supply unchanged. The bars sum to the line, the daily change in outstanding supply.</div><div class="h"><div><div class="t">Outstanding supply flows by source</div><div class="d">Daily movements of STANDARD into and out of outstanding supply, summing to the daily change.</div></div></div><div class="ch tall"><canvas id="c_flows"></canvas></div><div class="src">Source: STANDARD Transfer logs involving the pool, vaults, S-Bills and the zero address.</div></div>
    <div class="panel"><span class="i" tabindex="0">i</span><div class="tip">STANDARD leaves supply permanently through three doors. Expansion licenses are paid from bankers’ ledger balances and never minted. Half of every resolution fee on a withdrawal and half of every revocation fee is burned, the other half is recycled to remaining bankers. Buybacks by the contraction vault burn minted tokens, as do the S-Bills contract and the tax hook, which burns STANDARD it takes from the pool. The line is the running total of all three as a share of the 1 billion hard cap, the protocol’s own “Burned forever” measure.</div><div class="h"><div><div class="t">STANDARD burned by source, daily</div><div class="d">Expansion licenses, the burned half of resolution and revocation fees, and buybacks, with the cumulative total as a share of the 1 billion hard cap.</div></div><div class="n" id="burn_now"></div></div><div class="ch tall"><canvas id="c_issue"></canvas></div><div class="src">Source: licenses-purchased, withdrawn and revoked events; STANDARD transfers to the zero address. Cumulative from events; the tile reads the token contract.</div></div>
    <div class="panel w12 tw"><span class="i" tabindex="0">i</span><div class="tip">Minted supply changes when withdrawals are minted (+), deposits are burned into the ledger (−) and tokens are burned (−). The pool changes with net market sales (+ when the market sells, − when it buys) and with the protocol’s own transfers: contraction vault and POL buybacks, and the POL manager’s collection of the protocol position’s fees, which it forwards to the team wallet. A buyback reduces supply and the pool by equal amounts and leaves outstanding supply unchanged. Every row ties.</div><div class="h"><div><div class="t">Supply, pool and outstanding reconciliation</div><div class="d">Daily reconciliation: outstanding supply equals minted supply less the protocol pool less the Incentives Vault.</div></div><div><button class="btn" id="fmore">View all days</button></div></div><table id="t_float"></table><div class="src">Source: STANDARD Transfer logs classified by counterparty. Net market sales equal the sum of the holder groups in the Market section.</div></div>
  </div>

  <h2 id="bank">Banking system</h2>
  <div class="grid">
    <div class="panel"><span class="i" tabindex="0">i</span><div class="tip">Ledger balance equals issuance plus deposits plus recycled fees, less license purchases, gross withdrawals and revocations. The resolution fee, the exit fee on withdrawals, is 2% and rises to 60% as seven-day exit pressure approaches 10% of the ledger.</div><div class="h"><div><div class="t">Bank deposits, withdrawals and ledger balance</div><div class="d">Daily deposits against gross withdrawals, with bankers’ ledger balance, which is minted only on withdrawal.</div></div><div class="n" id="exitfee"></div></div><div class="ch"><canvas id="c_bank"></canvas></div><div class="src">Source: deposited and withdrawn events. Ledger = issuance + deposits + recycled fees − licenses − gross withdrawals − revocations.</div></div>
    <div class="panel"><span class="i" tabindex="0">i</span><div class="tip">A charter opens with one branch and licenses add up to nine more. Withdrawals and revocations destroy branches; a charter with no remaining branches is burned. The reconstruction matches the live census. The multiplier by epoch is shown in the epoch settlement ledger.</div><div class="h"><div><div class="t">Branch and charter count</div><div class="d">Branches outstanding and active charters, reconstructed from on-chain events.</div></div><div class="n" id="sb_now"></div></div><div class="ch"><canvas id="c_policy"></canvas></div><div class="src">Source: charter-created, branches-opened, withdrawn and revoked events.</div></div>
    <div class="panel w12 tw"><span class="i" tabindex="0">i</span><div class="tip">Ranked by lifetime emissions from the Standard Reserve indexer leaderboard. Names are the owners’ own primary ENS names on Ethereum mainnet, looked up by reverse record and refreshed weekly; wallets without one are shown by address. Charters are soulbound, so the listed wallet is the original buyer. Share is the banker’s branches as a share of all branches. Rank change compares with the previous epoch’s lifetime ranking.</div><div class="h"><div><div class="t">Top bankers</div><div class="d">Ranked by lifetime emissions, with ENS names where the owner has set one.</div></div><div><span class="n" id="lead_n"></span> <button class="btn" id="lead_more">View top 25</button></div></div><table id="t_lead"></table></div>
    <div class="panel w12 tw" id="log"><span class="i" tabindex="0">i</span><div class="tip">Every field is reconstructed from protocol events and transfer logs; today’s reserve is read at the compile block. Recurring revenue is token trading fees plus pool fees.</div><div class="h"><div><div class="t">Daily data log</div><div class="d">One observation per UTC day since genesis. The current day is partial.</div></div><div><button class="btn" id="more">View all days</button> <button class="btn" id="csv">Export CSV</button></div></div><table id="t_log"></table></div>
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
  pct:(v,d)=>v==null||isNaN(v)?'–':(v<0?'−':'')+(Math.abs(v)*100).toFixed(d==null?1:d)+'%',
  sx:(v,d)=>v==null||isNaN(v)?'–':(v>0?'+':v<0?'−':'')+Math.abs(v).toFixed(d==null?1:d),
  eth:(v,d)=>v==null?'–':v.toFixed(d==null?1:d)+' ETH',
  dt:(ts)=>new Date(ts*1000).toISOString().slice(0,10),
  hm:(ts)=>new Date(ts*1000).toISOString().slice(11,16),
  sgn:(v)=>v>0?'+':'',
  int:(v)=>v==null||isNaN(v)?'–':Math.round(v).toLocaleString('en-US'),
  chg:(v,d)=>v==null||isNaN(v)?'':`<span class="${v>=0?'up':'dn'}">${v>=0?'+':'−'}${(Math.abs(v)*100).toFixed(d==null?1:d)}%</span>`,
  days:(v)=>v==null||!isFinite(v)?'–':v>=365?(v/365).toFixed(1)+' yrs':Math.round(v)+' days'
};
const MOBILE = window.matchMedia('(max-width:600px)').matches;
if (window.Chart) {
  Chart.defaults.color = C.muted; Chart.defaults.font.family = getComputedStyle(document.documentElement).getPropertyValue('--mono');
  Chart.defaults.font.size = 10.5; Chart.defaults.borderColor = 'rgba(190,172,232,.12)';
  Chart.defaults.plugins.legend.labels.boxWidth = 9; Chart.defaults.plugins.legend.labels.boxHeight = 9; Chart.defaults.plugins.legend.labels.padding = 14;
  Chart.defaults.plugins.legend.align = 'center'; Chart.defaults.plugins.legend.position = 'bottom'; Chart.defaults.plugins.legend.labels.font = {size: 10.5};
  Chart.defaults.plugins.legend.labels.padding = MOBILE ? 10 : 18; Chart.defaults.layout.padding = {top: 8, bottom: 0};
  if (MOBILE) { Chart.defaults.font.size = 10; Chart.defaults.plugins.legend.labels.font = {size: 10}; Chart.defaults.scale.ticks.maxTicksLimit = 6; Chart.defaults.scale.ticks.maxRotation = 45; }
  Chart.defaults.interaction = {mode: 'index', intersect: false}; Chart.defaults.plugins.tooltip.mode = 'index'; Chart.defaults.plugins.tooltip.intersect = false; Chart.defaults.elements.point.hitRadius = 12;
  Chart.defaults.plugins.tooltip.backgroundColor = '#1c1829'; Chart.defaults.plugins.tooltip.borderColor = 'rgba(190,172,232,.3)'; Chart.defaults.plugins.tooltip.borderWidth = 1;
  Chart.defaults.elements.bar.borderRadius = 2; Chart.defaults.animation = false;
}
const last = (arr,n)=>n?arr.slice(Math.max(0,arr.length-n)):arr;
const sum = (a)=>a.reduce((x,y)=>x+(y||0),0);
const ethOf = (r)=>r.eth||L.ethusd;
const tr = (r)=>(r.tradingFeeEth||0)*ethOf(r), chs = (r)=>(r.charterEth||0)*ethOf(r), rec = (r)=>tr(r)+(r.spFee||0);   // recurring revenue: trading fees and pool fees
const inc = (r)=>rec(r)+chs(r);                                                                                          // recurring revenue plus charter sales
const burnLedger = (r)=>(r.licBurn||0)+(r.exitFeeBurn||0)+(r.revokeFeeBurn||0), burnTokens = (r)=>(r.burnBuyback||0)+(r.burnOther||0), burnAll = (r)=>burnLedger(r)+burnTokens(r);
const claims = (r)=>(r.issuance||0)-burnAll(r);                                // net new claims on STANDARD: issuance less everything burned
const pbOf = (r)=>r&&r.reserveUsd&&r.mcFloat ? r.mcFloat/r.reserveUsd : null;  // price to backing
const GROUPS = [['team','Team wallet','#e9b7d4'],['bankers','Bankers','#deb553'],['sbills','S-Bill holders','#cdbdf0'],['active','High-frequency wallets and bots','#8fa2f0'],['launch','Launch-week buyers','#f3b690'],['other','Other wallets','#6f6690']];
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
const rec7 = sum(s7.map(rec)), chs7 = sum(s7.map(chs));
const winEnd = (r,n)=>{const i=Sp.indexOf(r); return i>=n-1 ? Sp.slice(i-n+1,i+1) : null;};
const recRoll = (r)=>{const w=winEnd(r,7); return w && w[0].date>=ep2 ? sum(w.map(rec)) : null;};            // trailing seven-day recurring revenue, launch epoch excluded
const prrOf = (r)=>{const v=recRoll(r); return v && r.mcFloat ? r.mcFloat/(v*365/7) : null;};             // price to recurring revenue
const Y = Sp[Sp.length-1]||{}, Y2 = Sp[Sp.length-2]||{};      // yesterday (last complete UTC day) and the day before
const dm = (d)=>new Date(d+'T00:00:00Z').toLocaleDateString('en-GB',{day:'numeric',month:'short',timeZone:'UTC'});
const yd = Y.date ? dm(Y.date) : '';
let NOWTS = DATA.pulledAt, LIVE = false;   // NOWTS and L are refreshed in place by goLive() from the indexer and DexScreener
let mcFloat, mcTotal, epLeft, backing, backingTot, perBranch, licPayback, chPayback, mUp, mDn, burnShare, capRemoved, p7, pbNow;
const derive = ()=>{ mcFloat = L.price*L.float; mcTotal = L.price*L.totalSupply; epLeft = Math.max(0, L.epochEnd - NOWTS);
  backing = L.reserve.totalUsd/L.float; backingTot = L.reserve.totalUsd/L.totalSupply; perBranch = L.baseIssuance*L.multiplier/L.branches;
  licPayback = L.licenseLastSale/perBranch; chPayback = L.charterLastSale*L.ethusd/(perBranch*L.price);
  mUp = (L.positiveStreak||0)+1>=2 ? Math.min(L.mMax, L.multiplier+L.mStepUp) : L.multiplier; mDn = Math.max(L.mMin, L.multiplier-L.mStepDown);
  burnShare = L.burnedForever/(L.totalSupply+L.burnedForever); capRemoved = 1e9-L.maxSupply; p7 = back('price',7); pbNow = mcFloat/L.reserve.totalUsd; };
derive();
const bbY = (Y.burnBuyback||0)+(Y.toIncentives||0), bb7 = sum(s7.map(r=>(r.burnBuyback||0)+(r.toIncentives||0)));
const dF =Y.float!=null&&Y2.float!=null ? Y.float-Y2.float : null;
const ledgerRemoved =sum(S.map(r=>(r.licBurn||0)+(r.exitFeeBurn||0)+(r.revokeFeeBurn||0)));
const dv = (k)=>Y[k]!=null&&Y2[k]!=null ? fmt.sgn(Y[k]-Y2[k])+fmt.n(Y[k]-Y2[k],2) : '–';
const dvi = (k)=>Y[k]!=null&&Y2[k]!=null ? fmt.sgn(Y[k]-Y2[k])+fmt.int(Y[k]-Y2[k]) : '–';
function renderKpis(){ derive();
const kpis = [
  ['Token price', '$'+L.price.toFixed(4), `${L.priceChange24h!=null?fmt.chg(L.priceChange24h/100)+' 24h':''}${p7?' · '+fmt.chg(L.price/p7-1)+' 7d':''}`,
    `Live price from DexScreener for the STANDARD/ETH pool. The daily history uses GeckoTerminal closing prices.`],
  ['Market cap, minted supply', fmt.usd(mcTotal), ``,
    `<b>Price × minted supply (${fmt.n(L.totalSupply,1)}), the figure DexScreener and GeckoTerminal show as both market cap and FDV.</b> Adding the ${fmt.n(L.pending,1)} unminted ledger balance owed to bankers gives ${fmt.usd(L.price*(L.totalSupply+L.pending))}. Minted supply includes ${fmt.n(L.poolStd,1)} STANDARD held in the protocol’s own STANDARD/ETH pool and ${fmt.n(L.incentivesStd,1)} in the Incentives Vault, neither of which is available for sale.`],
  ['Market cap, outstanding', fmt.usd(mcFloat), ``,
    `<b>The equity analog of shares outstanding.</b> Minted supply less the protocol’s own pool and the Incentives Vault, the two balances the protocol cannot sell; the whitepaper calls this circulating supply. It includes ${fmt.n(L.sbills.locked||0,1)} of S-Bill principal plus the ${fmt.n(Math.max(0,L.sbillsStd-(L.sbills.locked||0)),1)} premium pot held by the S-Bills contract, and ${fmt.n(L.teamStd,1)} held by the team wallet; free float, which excludes all three, is ${fmt.n(L.float-L.sbillsStd-L.teamStd,1)} (${fmt.usd(L.price*(L.float-L.sbillsStd-L.teamStd))}).`],
  ['Reserve assets', fmt.usd(L.reserve.totalUsd), `price ${pbNow.toFixed(2)}× backing`,
    `ETH and USDG held in the reserve Safe, ETH in the policy vaults, tokenized equities held outside pools, and the reserve’s Uniswap v4 positions (${fmt.pct(L.reserve.lpUsd/L.reserve.totalUsd,0)} of the total). Excludes ${fmt.eth(L.reserve.polBuybackEth,1)} held by the POL buyback contract for STANDARD purchases, and the team wallet. Backing is $${backing.toFixed(3)} per outstanding token and $${backingTot.toFixed(3)} per minted token.`],
  ['Recurring revenue, '+yd, fmt.usd(rec(Y)), `charter sales ${fmt.usd(chs(Y))}`,
    `The most recent complete UTC day. Recurring revenue is STANDARD/ETH trading fees (each epoch’s routed ETH allocated evenly across its days; the current epoch estimated from tax hook and fee splitter balances) plus the reserve’s fee income from its pools. Charter sales, proceeds from auctioning new charters, are shown separately. Seven-day average ${fmt.usd(rec7/7)} per day of recurring revenue.`],
  ['Buybacks, '+yd+' (STANDARD)', fmt.n(bbY,2), `${fmt.usd(bbY*(Y.price||L.price))}`,
    `STANDARD purchased from the pool and burned by the contraction vault, plus the 15% POL allocation purchased into the Incentives Vault. ${fmt.eth(L.reserve.contractionEth,1)} remains in the contraction vault pending deployment.`],
  ['Epoch '+L.epoch+' net flow', fmt.sx(L.epochNetFlow,1)+' ETH', `settles in ${Math.floor(epLeft/3600)}h ${Math.floor(epLeft%3600/60)}m`,
    `Net flow is ETH purchased less ETH sold through the pool so far this epoch. Its sign at settlement sets the regime: expansion allocates 70% of fees to the reserve, contraction allocates them to buybacks. Prior epoch ${fmt.sx(L.previousEpochFlow,1)} ETH; consecutive positive epochs ${L.positiveStreak}. The multiplier settles to ${mUp.toFixed(2)}× if positive and ${mDn.toFixed(2)}× if negative.`],
  ['Issuance multiplier', L.multiplier.toFixed(2)+'×', ``,
    `Daily issuance equals 700,000 multiplied by the multiplier, ${fmt.n(L.baseIssuance*L.multiplier,0)} today or ${perBranch.toFixed(1)} per branch, allocated evenly across branches. The multiplier rises 0.10 from the second consecutive positive epoch and falls 0.15 per negative epoch, within a range of 0.20 to 1.25. Ledger balance credited to bankers but not yet minted: ${fmt.n(L.pending,1)}.`],
  ['License payback period', fmt.days(licPayback), ``,
    `Last license clearing price (${fmt.int(L.licenseLastSale)} STANDARD) divided by one branch’s daily issuance (${perBranch.toFixed(1)}). A charter at its last clearing price, ${fmt.usd(L.charterLastSale*L.ethusd,1)}, pays back in ${fmt.days(chPayback)} at today’s token price. Both exclude resolution fees and future multiplier changes. The auction quote is not used because it keeps falling after a period sells out, when no license can be bought.`],
  ['Charter auction, last clearing', L.charterLastSale.toFixed(2)+' ETH', `${(L.charterRemaining||0)>0?'quote '+L.charterPriceNow.toFixed(2)+' ETH, descending':'next '+fmt.hm(L.charterNextOpen)+' UTC at '+L.charterNextStart.toFixed(2)+' ETH'}`,
    `<b>The most recent charter cleared at ${L.charterLastSale.toFixed(2)} ETH.</b> One charter is offered per ${L.auctionPeriodHours}-hour period in a Dutch auction: the period opened at ${L.charterDayStart.toFixed(2)} ETH (three times the previous clearing price) and the price halves every ${L.charterHalfLife||2} hours toward the ${L.charterFloor.toFixed(2)} ETH floor until a purchase occurs. After the period’s charter is sold the contract continues to quote a declining price, but no charter is available until the next period opens.`],
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
  ['Resolution fee (exit fee)', fmt.pct(L.exitFeeNow,1), ``,
    `The whitepaper’s resolution fee, the exit fee charged on withdrawals: 2%, rising quadratically to 60% as seven-day exit pressure approaches 10% of the ledger. Gross withdrawals over the last seven days: ${fmt.n(L.w7,1)}. Half of each fee is burned and half is recycled to remaining bankers (${fmt.n(L.cumulativeRecycled,1)} cumulative).`],
  ['Team wallet holdings', fmt.eth(L.teamEth,0), `${fmt.n(L.teamStd,2)} STANDARD`,
    `The wallet to which the fee splitter routes 15% of fee ETH. The STANDARD balance is tracked from transfer logs, so any sale into the pool would be visible here.`],
  ['Burned forever', fmt.n(capRemoved,2), `${fmt.pct(capRemoved/1e9,1)} of the 1B hard cap · ${fmt.n(L.burnedForever,2)} bought back and burned`,
    `<b>The protocol’s own “Burned forever” figure: the 1 billion hard cap less the current maximum supply (${fmt.n(L.maxSupply,2)}).</b> It comprises tokens burned, open-market buybacks and the protocol position’s token-side fees (${fmt.n(L.burnedForever,2)}, ${fmt.pct(burnShare,1)} of minted supply plus tokens burned), and ledger removals that are never minted, expansion licenses and the burned half of resolution and revocation fees (${fmt.n(capRemoved-L.burnedForever,2)}). Deposits to branches are conversions that re-enter the ledger and are excluded.`],
];
const PRIMARY = ['Token price','Market cap, minted supply','Market cap, outstanding','Reserve assets','Recurring revenue, '+yd,'Buybacks, '+yd+' (STANDARD)','Epoch '+L.epoch+' net flow','License payback period'];
const tile = k=>`<div class="kpi"><span class="i" tabindex="0">i</span><div class="tip">${k[3]}</div><div class="l">${k[0]}</div><div class="v ${k[4]||''}">${k[1]}</div><div class="s">${k[2]}</div></div>`;
document.getElementById('kpis').innerHTML = PRIMARY.map(n=>kpis.find(k=>k[0]===n)).filter(Boolean).map(tile).join('');
document.getElementById('kpis2').innerHTML = kpis.filter(k=>!PRIMARY.includes(k[0])).map(tile).join('');
document.getElementById('epochpill').textContent = `Epoch ${L.epoch} · ${L.epochNetFlow>=0?'expansion':'contraction'} to date`;
document.getElementById('epochpill').className = 'pill '+(L.epochNetFlow>=0?'exp':'con');
renderStrip();
}
const spark = (vals, bars)=>{const w=300, h=46, p=3, xs=vals.filter(v=>v!=null); if(!xs.length) return '';
  let lo=Math.min(...xs, bars?0:Infinity), hi=Math.max(...xs, bars?0:-Infinity); if(hi===lo){hi+=1; lo-=1;}
  const X=i=>p+(w-2*p)*(vals.length>1?i/(vals.length-1):.5), Yp=y=>h-p-(h-2*p)*(y-lo)/(hi-lo);
  if (bars) { const bw=Math.max(1,(w-2*p)/vals.length*.7), z=Yp(0);
    return `<svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none">`+vals.map((y,i)=>y==null?'':`<rect x="${(X(i)-bw/2).toFixed(1)}" y="${Math.min(Yp(y),z).toFixed(1)}" width="${bw.toFixed(1)}" height="${Math.max(.5,Math.abs(Yp(y)-z)).toFixed(1)}" fill="${y<0?C.green:C.peach}"/>`).join('')+`<line x1="${p}" x2="${w-p}" y1="${z.toFixed(1)}" y2="${z.toFixed(1)}" stroke="${C.dim}" stroke-width="1" vector-effect="non-scaling-stroke"/></svg>`; }
  const pts=vals.map((y,i)=>y==null?null:`${X(i).toFixed(1)},${Yp(y).toFixed(1)}`).filter(Boolean).join(' ');
  return `<svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none"><polyline points="${pts}" fill="none" stroke="${C.gold}" stroke-width="1.8" vector-effect="non-scaling-stroke"/></svg>`;};
function renderStrip(){
  const L30 = last(Sp, 30), d30 = Sp.length>30 ? Sp[Sp.length-31] : null;
  const r30 = d30 ? recRoll(d30) : null;
  const i7 = sum(s7.map(r=>r.issuance||0)), b7 = sum(s7.map(burnAll)), c7 = i7-b7, c30 = sum(L30.map(claims));
  const P = last(Sh, 31), pb30 = Sh.length>30 ? pbOf(Sh[Sh.length-31]) : null;
  const cards = [
    ['Recurring revenue, trailing seven days', fmt.usd(rec7), `${fmt.usd(rec7*365/7)} annualized · charter sales ${fmt.usd(chs7)} excluded`,
      r30 ? `${fmt.chg(rec7/r30-1,0)} against the seven days to ${dm(d30.date)}` : '', spark(L30.map(recRoll)),
      `Token trading fees plus the reserve’s pool fees over the seven complete days to ${yd}, annualized at 365/7. Charter sales, proceeds from auctioning new charters, are excluded. The line is the trailing seven-day figure on each of the last 30 days.`],
    ['Net new STANDARD claims, trailing seven days', fmt.sgn(c7)+fmt.n(c7,2), `issued ${fmt.n(i7,2)} · burned ${fmt.n(b7,2)}`,
      `${fmt.sgn(c30)}${fmt.n(c30,2)} over the last 30 days`, spark(L30.map(claims), true),
      `Issuance credited to bankers less everything burned: expansion licenses, the burned half of resolution and revocation fees, buybacks and other token burns. It equals the change in minted supply plus the unminted ledger balance, the total claim on STANDARD. Negative means the claim shrank. Bars are daily over the last 30 days, green where burns exceeded issuance.`],
    ['Price to backing', pbNow.toFixed(2)+'×', `backing $${backing.toFixed(3)} per outstanding token · reserve ${fmt.usd(L.reserve.totalUsd)}`,
      pb30!=null ? `${pb30.toFixed(2)}× on ${dm(Sh[Sh.length-31].date)}` : '', spark(P.map(pbOf)),
      `Market capitalization on outstanding supply divided by reserve assets, equivalently token price over backing per outstanding token. Live price and outstanding supply; the reserve as read at the compile block. Earlier days use reserve closes rebuilt from on-chain events. The line covers the last 30 days.`],
  ];
  document.getElementById('strip').innerHTML = cards.map(c=>`<div class="sc"><span class="i" tabindex="0">i</span><div class="tip">${c[5]}</div><div class="l">${c[0]}</div><div class="v">${c[1]}</div><div class="s">${c[2]}</div><div class="t">${c[3]}</div>${c[4]}</div>`).join('');
}
renderKpis();

// ---------- static charts (not range dependent) ----------
const E2 = E.filter(e=>e.epoch>1);
new Chart(c_epochs, {type:'bar', data:{labels:E2.map(e=>'E'+e.epoch), datasets:[
  {label:'Trading fees', data:E2.map(e=>e.routed-e.charterEth), backgroundColor:E2.map(e=>isExp(e)?C.green:C.peach), stack:'a'},
  {label:'Charter proceeds', data:E2.map(e=>e.charterEth), backgroundColor:C.gold2, stack:'a'},
]}, options:{maintainAspectRatio:false, scales:{x:{stacked:true,grid:{display:false}}, y:{stacked:true, ticks:{callback:v=>v+' ETH'}}}, plugins:{legend:{display:true}, tooltip:{callbacks:{afterTitle:i=>{const e=E2[i[0].dataIndex];return (isExp(e)?'expansion':'contraction')+' · net flow '+fmt.sx(e.netFlow,1)+' ETH';}, label:c=>c.dataset.label+': '+c.parsed.y.toFixed(1)+' ETH'}}}}});
document.getElementById('t_epochs').innerHTML = '<tr><th>Epoch</th><th>Settled</th><th>Net flow (ETH)</th><th>Regime</th><th>Trading fees (ETH)</th><th>Charter proceeds (ETH)</th><th>Routed, total (ETH)</th><th>Vault (70%)</th><th>POL (15%)</th><th>Team (15%)</th><th>Multiplier after</th></tr>' +
  E.slice().reverse().map(e=>`<tr><td>${e.epoch}</td><td>${fmt.dt(e.settledAt)}</td><td class="${e.netFlow>=0?'pos':'neg'}">${fmt.sx(e.netFlow,1)}</td><td>${isExp(e)?'<span class="pill exp">expansion</span>':'<span class="pill con">contraction</span>'}</td><td>${(e.routed-e.charterEth).toFixed(1)}</td><td>${e.charterEth.toFixed(1)}</td><td>${e.routed.toFixed(1)}</td><td>${e.toVault.toFixed(1)}</td><td>${e.toPol.toFixed(1)}</td><td>${e.team.toFixed(1)}</td><td>${e.multiplierAfter.toFixed(2)}×</td></tr>`).join('');

const CH = DATA.charters, LP = DATA.licensePeriods;
let auc = [];
function renderAuctions(){   // re-run by goLive() when sales after the compile are replayed
  auc.forEach(c=>c.destroy()); auc = [];
  const chOpen = (L.charterRemaining||0)>0, licOpen = (L.licenseRemaining||0)>0;
  auc.push(new Chart(c_charter, {type:'line', data:{labels:CH.map(c=>fmt.dt(c.ts).slice(5)), datasets:[
    {label:'Clearing price (ETH)', data:CH.map(c=>c.eth), borderColor:C.gold, backgroundColor:'rgba(255,221,138,.18)', fill:true, pointRadius:CH.map(c=>c.viaContract?4:2.5), pointStyle:CH.map(c=>c.viaContract?'triangle':'circle'), pointBackgroundColor:C.gold, tension:.25},
    ...(chOpen?[{label:'Current quote', data:CH.map((c,i)=>i===CH.length-1?L.charterPriceNow:null), borderColor:C.water, pointRadius:5, pointStyle:'rectRot', pointBackgroundColor:C.water, showLine:false}]:[]),
  ]}, options:{maintainAspectRatio:false, scales:{x:{grid:{display:false}, ticks:{maxTicksLimit:9}}, y:{ticks:{callback:v=>v+' ETH'}, beginAtZero:true}}, plugins:{tooltip:{callbacks:{title:i=>{const c=CH[i[0].dataIndex];return 'charter #'+c.id+' · '+fmt.dt(c.ts)+(c.viaContract?' · via contract':'');}, afterBody:i=>{const c=CH[i[0].dataIndex];return c.buyer?'buyer '+c.buyer.slice(0,10):'';}}}}}}));
  document.getElementById('ch_tip').textContent = `${CH.length} charters sold to date for ${sum(CH.map(c=>c.eth)).toFixed(1)} ETH; the period is ${chOpen?'open':'sold out'}.`;
  document.getElementById('lic_tip').textContent = `${fmt.n(sum(LP.map(p=>p.burned)),2)} STANDARD burned over ${LP.length} periods; the period is ${licOpen?'open':'sold out'}.`;
  auc.push(new Chart(c_license, {data:{labels:LP.map(p=>fmt.dt(p.start).slice(5)+' '+(new Date(p.start*1000).getUTCHours()<12?'am':'pm')), datasets:[
    {type:'bar', label:'Licenses sold (branches opened)', data:LP.map(p=>p.sold), backgroundColor:'rgba(185,166,227,.35)', yAxisID:'y1', order:2},
    {type:'line', label:'Period close price (STANDARD)', data:LP.map(p=>p.close), borderColor:C.gold, backgroundColor:C.gold, pointRadius:2, tension:.25, yAxisID:'y', order:1},
  ]}, options:{maintainAspectRatio:false, scales:{x:{grid:{display:false}, ticks:{maxTicksLimit:10}}, y:{position:'left', ticks:{callback:v=>fmt.n(v,1)}}, y1:{position:'right', grid:{display:false}, beginAtZero:true}}, plugins:{tooltip:{callbacks:{afterTitle:i=>{const p=LP[i[0].dataIndex];return 'period '+p.day+' · burned '+fmt.n(p.burned,1)+' STANDARD';}}}}}}));
}
renderAuctions();

const R = L.reserve;
document.getElementById('res_tot').textContent = fmt.usd(R.totalUsd);
const pname = (s)=>s==='ETH'?'ETH/USDG pool':s+' pool';
const lpItems = Object.entries(L.lp).map(([s,v])=>[pname(s), v.valueUSD]);
const resItems = [...lpItems, ['USDG', R.safeUsdg], ['ETH (Safe + vaults)', (R.safeEth+R.contractionEth+R.expansionEth)*L.ethusd], ['Equities outside pools', R.safeStockUsd]].filter(x=>x[1]>1);
new Chart(c_reserve, {type:'bar', data:{labels:resItems.map(x=>x[0]), datasets:[{data:resItems.map(x=>x[1]), backgroundColor:resItems.map((x,i)=>i<lpItems.length?C.peri:x[0].startsWith('USDG')?C.water:x[0].startsWith('ETH')?C.peach:C.green)}]}, options:{indexAxis:'y', maintainAspectRatio:false, plugins:{legend:{display:false}, tooltip:{callbacks:{label:c=>fmt.usd(c.parsed.x)+' · '+fmt.pct(c.parsed.x/R.totalUsd,1)}}}, scales:{x:{ticks:{callback:v=>fmt.usd(v,1)}}, y:{grid:{display:false}, ticks:{autoSkip:false}}}}});

const pools = Object.keys(L.lp);
const ctx = L.poolCtx;
const ydS = Y.date ? dm(Y.date) : '1d';
const pvm = (r,p)=>r['spVolMine_'+p]!=null ? r['spVolMine_'+p] : (r['spVol_'+p]||0);   // volume served by the reserve's liquidity, as in the chart
const prow = pools.map(p=>{const v=L.lp[p], c=ctx[p]||{}; return {p, v, c, f1:Y['spFee_'+p]||0, f7:sum(s7.map(r=>r['spFee_'+p]||0)), v1:pvm(Y,p)};});
const pt = {usdg:sum(prow.map(x=>x.v.usdg||0)), val:sum(prow.map(x=>x.v.valueUSD||0)), f1:sum(prow.map(x=>x.f1)), f7:sum(prow.map(x=>x.f7)), v1:sum(prow.map(x=>x.v1))};
document.getElementById('t_pools').innerHTML = `<tr><th>Pool</th><th>Tokens</th><th>USDG</th><th>Price</th><th>Fee tier</th><th>Value</th><th>Fees, ${ydS.replace(' ','&nbsp;')}</th><th>Fees, 7d</th><th>Volume, ${ydS.replace(' ','&nbsp;')}</th><th>Yield</th><th>Share of pool</th><th><a class="hl" href="#p_lshare">Share of chain liquidity, ${ydS.replace(' ','&nbsp;')}</a></th><th><a class="hl" href="#p_vshare">Share of chain volume, ${ydS.replace(' ','&nbsp;')}</a></th><th>Venues</th><th>Rank</th><th>Largest other venue</th></tr>` +
  prow.map(({p,v,c,f1,f7,v1})=>`<tr><td>${p==='ETH'?'ETH/USDG':p}</td><td>${fmt.n(v.stock,1)}</td><td>${fmt.usd(v.usdg,1)}</td><td>$${v.price.toFixed(2)}</td><td>${v.feeTier>=8388608?'session':(v.feeTier/1e4).toFixed(3)+'%'}</td><td>${fmt.usd(v.valueUSD)}</td><td>${fmt.usd(f1,1)}</td><td>${fmt.usd(f7,1)}</td><td>${fmt.usd(v1,1)}</td><td>${v.valueUSD?fmt.pct(f7*365/7/v.valueUSD,0):'–'}</td><td>${v.share!=null?fmt.pct(v.share,0):'–'}</td><td>${Y['liqShare_'+p]!=null?fmt.pct(Y['liqShare_'+p],0):'–'}</td><td>${Y['volShare_'+p]!=null?fmt.pct(Y['volShare_'+p],0):'–'}</td><td>${Y['venues_'+p]??'–'}</td><td>${Y['rank_'+p]?'#'+Y['rank_'+p]:'–'}</td><td>${Y['otherTvl_'+p]?fmt.usd(Y['otherTvl_'+p],1)+' · '+Y['otherDex_'+p]:'–'}</td></tr>`).join('') +
  `<tr class="sr"><td>Total</td><td>–</td><td>${fmt.usd(pt.usdg,1)}</td><td>–</td><td>–</td><td>${fmt.usd(pt.val)}</td><td>${fmt.usd(pt.f1,1)}</td><td>${fmt.usd(pt.f7,1)}</td><td>${fmt.usd(pt.v1,1)}</td><td>${pt.val?fmt.pct(pt.f7*365/7/pt.val,0):'–'}</td><td>–</td><td>–</td><td>–</td><td>–</td><td>–</td><td>–</td></tr>`;
const comp = (r)=>{const q=r&&r.reserveParts; if(!q) return null; const o={}; Object.entries(q.lp||{}).forEach(([k,v])=>o[pname(k)]=v); o['USDG']=q.usdg; o['ETH (Safe + vaults)']=q.eth; o['Equities outside pools']=q.stocks; o['Total']=q.total; return o;};
const RT = Sh[Sh.length-1], rc0 = comp(RT), rc1 = comp(Sh[Sh.length-2]), rc7 = comp(Sh[Sh.length-8]);
const dcell = (a,b)=>a!=null&&b!=null ? `<td class="${a-b>=0?'pos':'neg'}">${fmt.sgn(a-b)}${fmt.usd(a-b,1)}</td><td class="${a-b>=0?'pos':'neg'}">${b?fmt.sgn(a-b)+fmt.pct((a-b)/b,1):'–'}</td>` : '<td>–</td><td>–</td>';
document.getElementById('resd_n').textContent = `${Sh.filter(r=>r.reserveParts).length} days of closes`;
document.getElementById('t_resd').innerHTML = rc0 ? '<tr><th>Component</th><th>Today</th><th>Share</th><th>Change, 1 day</th><th>%</th><th>Change, 7 days</th><th>%</th></tr>' +
  Object.keys(rc0).map(k=>`<tr class="${k==='Total'?'sr':''}"><td>${k}</td><td>${fmt.usd(rc0[k])}</td><td>${k==='Total'?'':fmt.pct(rc0[k]/rc0.Total,1)}</td>${dcell(rc0[k], rc1&&rc1[k])}${dcell(rc0[k], rc7&&rc7[k])}</tr>`).join('') : '';

function renderBridge(){   // re-run by goLive() once the blocks after the compile are replayed
  const mintAll = sum(S.map(r=>r.mint||0)), bbAll = sum(S.map(r=>r.burnBuyback||0)), depAll = sum(S.map(r=>r.depositBurn||0)), othAll = sum(S.map(r=>r.burnOther||0));
  const sbLock = L.sbills.locked||0, sbPot = Math.max(0, L.sbillsStd - sbLock), resid = L.totalSupply-(100e6+mintAll-bbAll-othAll-depAll);
  const br = [['Genesis liquidity mint', 100e6], ['+ Withdrawals minted', mintAll], ['− Buybacks burned', -bbAll], ['− Tax hook burns', -othAll], ['− Deposits to ledger', -depAll],
    ...(Math.abs(resid)>=0.5?[['± Unreconciled', resid]]:[]), ['= Minted supply', L.totalSupply, 'tot'],
    ['− Protocol STANDARD/ETH pool', -L.poolStd], ['− Incentives Vault', -L.incentivesStd], ['= Outstanding supply', L.float, 'tot'],
    ['− S-Bill principal', -sbLock], ['− S-Bill premium pot', -sbPot], ['− Team wallet', -L.teamStd], ['= Free float', L.float-L.sbillsStd-L.teamStd, 'tot']];
  document.getElementById('bridge').innerHTML = br.map(b=>`<div class="${b[2]||''}">${b[0]}</div><div class="${b[2]||''}">${fmt.n(b[1],2)}</div>`).join('');
}
renderBridge();
function renderHeads(){   // panel header figures that depend on live state; re-run by goLive()
  const chOpen=(L.charterRemaining||0)>0, licOpen=(L.licenseRemaining||0)>0;
  document.getElementById('ch_now').textContent = chOpen ? `quote ${L.charterPriceNow.toFixed(2)} ETH, descending` : `next ${fmt.hm(L.charterNextOpen)} UTC at ${L.charterNextStart.toFixed(2)} ETH`;
  document.getElementById('lic_now').textContent = licOpen ? `quote ${fmt.int(L.licensePriceNow)}, descending · ${L.licenseRemaining} left` : `next ${fmt.hm(L.licenseNextOpen)} UTC at ${fmt.int(L.licenseNextStart)}`;
  document.getElementById('mc_now').textContent = fmt.n(L.float,2)+' outstanding · '+fmt.n(L.poolStd+L.incentivesStd,2)+' protocol · '+fmt.n(L.pending,2)+' owed to bankers';
  document.getElementById('exitfee').textContent = 'resolution fee '+fmt.pct(L.exitFeeNow,1)+' · ledger '+fmt.n(L.pending,1);
  document.getElementById('sb_now').textContent = `${fmt.int(L.branches)} branches · ${fmt.int(L.activeCharters)} charters`;
  document.getElementById('burn_now').textContent = `${fmt.n(capRemoved,2)} burned forever · ${fmt.pct(capRemoved/1e9,1)} of the 1B cap`;
  document.getElementById('px_now').textContent = `${fmt.usd(mcTotal)} minted · ${fmt.usd(mcFloat)} outstanding`;
  document.getElementById('pb_now').textContent = `${pbNow.toFixed(2)}× · backing $${backing.toFixed(3)}`;
  document.getElementById('inc7').textContent = s7.length ? `recurring ${fmt.usd(rec7)} · charter sales ${fmt.usd(chs7)}, ${dm(s7[0].date)} to ${dm(s7[s7.length-1].date)}` : '';
  const prY = prrOf(Y); document.getElementById('prr_now').textContent = prY!=null ? `${prY.toFixed(1)}× on ${yd}` : '';
}
renderHeads();
const sp7v = sum(s7.map(r=>r.spVolMine!=null?r.spVolMine:(r.spVol||0))), sp7g = sum(s7.map(r=>r.spVol||0)), sp7f = sum(s7.map(r=>r.spFee||0));
document.getElementById('sp7').textContent = `${fmt.usd(sp7v,2)} served of ${fmt.usd(sp7g,2)} pool volume · ${fmt.usd(sp7f,1)} fees, 7 days`;

// ---------- Liquidity hub business ----------
const stockPools = pools.filter(p=>!L.lp[p].isEth), allPools = pools;
const spf = (r,ps)=>sum(ps.map(p=>r['spFee_'+p]||0)), spv = (r,ps)=>sum(ps.map(p=>r['spVol_'+p]||0));
const poolFees7 = sum(s7.map(r=>spf(r,allPools))), eqFees7 = sum(s7.map(r=>spf(r,stockPools))), ethFees7 = sum(s7.map(r=>r['spFee_ETH']||0));
const poolVol7 = sum(s7.map(r=>spv(r,allPools))), poolFeesY = spf(Y,allPools);
const poolLiq = sum(allPools.map(p=>L.lp[p].valueUSD)), poolYield = poolLiq?poolFees7*365/7/poolLiq:null;
const ctxS = stockPools.map(p=>ctx[p]||{}), ctxE = ctx['ETH']||{};
const srV = sum(ctxS.map(c=>c.srVol24||0)), allV = sum(ctxS.map(c=>c.totalVol24||0)), srL = sum(stockPools.map(p=>L.lp[p].valueUSD)), allL = sum(ctxS.map(c=>c.totalLiq||0));
const firstEq = (S.find(r=>spv(r,allPools)>0)||{}).date;
const zf7 = sum(s7.map(r=>r.spVolZeroFee||0)), spAll7 = sum(s7.map(r=>r.spVolMine!=null?r.spVolMine:(r.spVol||0)));   // fee-exempt swaps trade only in the equity pools, where the reserve serves all volume
const poolAnn = poolFees7*365/7;
document.getElementById('eq_stats').innerHTML = [
  ['Pool fee income, 7 days', fmt.usd(poolFees7), `${fmt.pct(rec7?poolFees7/rec7:null,0)} of recurring revenue`, `equities ${fmt.usd(eqFees7)} · ETH/USDG ${fmt.usd(ethFees7)}`],
  ['Capital in pools', fmt.usd(poolLiq), `${fmt.pct(poolLiq/L.reserve.totalUsd,0)} of reserve`, `${fmt.pct(poolYield,0)} yield, annualized`],
  ['Share of chain equity volume', fmt.pct(sum(stockPools.map(p=>Y['chainVol_'+p]||0))?sum(stockPools.map(p=>pvm(Y,p)))/sum(stockPools.map(p=>Y['chainVol_'+p]||0)):null,0), ydS, `ETH/USDG pool ${fmt.pct(Y['volShare_ETH'],0)}`],
  ['Fee-paying share of volume', fmt.pct(spAll7?1-zf7/spAll7:null,0), `7d`, `${fmt.usd(zf7,1)} fee-exempt`],
].map(k=>`<div><div class="l">${k[0]}</div><div class="v">${k[1]}<small>${k[2]}</small></div><div class="s">${k[3]}</div></div>`).join('');
document.getElementById('eq_n').textContent = `${fmt.usd(poolFees7)} trailing 7 days`;
// chain shares, counterparties and profit and loss (last complete day, trailing seven days)
const PCOL = {SPCX:'#8fa2f0', SKHY:'#a8c79a', BABA:'#e9b7d4', ETH:'#f3b690'};
const LP0 = '2026-10-14';   // the reserve's pools opened on 14 October
const shortP = p=>p==='ETH'?'ETH/USDG':p;
document.getElementById('vs_now').textContent = pools.map(p=>`${shortP(p)} ${fmt.pct(Y['volShare_'+p],0)}`).join(' · ');
document.getElementById('ls_now').textContent = pools.map(p=>`${shortP(p)} ${fmt.pct(Y['liqShare_'+p],0)}`).join(' · ');
const ck = (r,k,ps)=>sum((ps||pools).map(p=>r[`vol${k}_${p}`]||0));
const CPK = ['Org','Arb','Bot','Fx'];
const c7 = Object.fromEntries(CPK.map(k=>[k, sum(s7.map(r=>ck(r,k)))])), c7t = sum(CPK.map(k=>c7[k]));
document.getElementById('cp_now').textContent = c7t ? `organic ${fmt.pct(c7.Org/c7t,0)} of ${fmt.usd(c7t,1)}, 7 days` : '';
const cpRow = (name, ps)=>{const v=Object.fromEntries(CPK.map(k=>[k, sum(s7.map(r=>ck(r,k,ps)))])), t=sum(CPK.map(k=>v[k]));
  const fo=sum(s7.map(r=>sum(ps.map(p=>r['feeOrg_'+p]||0)))), ft=sum(s7.map(r=>sum(ps.map(p=>sum(CPK.map(k=>r[`fee${k}_${p}`]||0))))));
  const raw = CPK.map(k=>t?v[k]/t*100:0), fl = raw.map(Math.floor), left = 100-sum(fl);   // largest remainder, so the four volume shares sum to exactly 100%
  raw.map((x,i)=>[x-fl[i],i]).sort((a,b)=>b[0]-a[0]).slice(0, t?left:0).forEach(([,i])=>fl[i]++);
  return CPK.map((k,i)=>`<td>${t?fl[i]+'%':'–'}</td>`).join('') + `<td class="cpf">${ft?fmt.pct(fo/ft,0):'–'}</td>`;};
document.getElementById('t_cpty').innerHTML = '<tr><th rowspan="2">Pool</th><th colspan="4" class="cpg">Share of volume</th><th rowspan="2" class="cpf">Share of fees paid by organic users</th></tr><tr><th>Organic</th><th>Arbitrage</th><th>Bots</th><th>Fee-exempt</th></tr>' +
  pools.map(p=>`<tr><td>${shortP(p)}</td>${cpRow(p,[p])}</tr>`).join('') + `<tr class="sr"><td>All pools</td>${cpRow('all',pools)}</tr>`;
const pnlOf = (r,p)=>r['lpVal_'+p]!=null ? {lp:r['lpVal_'+p], hold:r['holdVal_'+p], cost:r['lpCost_'+p], fees:r['lpFees_'+p]} : null;
const PY = pools.map(p=>[p, pnlOf(Y,p)]).filter(x=>x[1]);
const pt7 = PY.reduce((a,[p,v])=>({lp:a.lp+v.lp, hold:a.hold+v.hold, cost:a.cost+v.cost, fees:a.fees+v.fees}), {lp:0,hold:0,cost:0,fees:0});
const pcell = v=>`<td class="${v>=0?'pos':'neg'}">${fmt.sgn(v)}${fmt.usd(v,1)}</td>`;
document.getElementById('pl_now').textContent = PY.length ? `${fmt.sgn(pt7.lp+pt7.fees-pt7.hold)}${fmt.usd(pt7.lp+pt7.fees-pt7.hold,1)} against holding, ${yd}` : '';
document.getElementById('t_pnl').innerHTML = '<tr><th>Pool</th><th>Fees</th><th>Divergence</th><th>Net vs holding</th><th>Net in USD</th></tr>' +
  PY.map(([p,v])=>`<tr title="cost ${fmt.usd(v.cost,2)} · value ${fmt.usd(v.lp,2)} · holding ${fmt.usd(v.hold,2)}"><td>${shortP(p)}</td><td>${fmt.usd(v.fees,1)}</td>${pcell(v.lp-v.hold)}${pcell(v.lp+v.fees-v.hold)}${pcell(v.lp+v.fees-v.cost)}</tr>`).join('') +
  (PY.length?`<tr class="sr" title="cost ${fmt.usd(pt7.cost,2)} · value ${fmt.usd(pt7.lp,2)} · holding ${fmt.usd(pt7.hold,2)}"><td>Total</td><td>${fmt.usd(pt7.fees,1)}</td>${pcell(pt7.lp-pt7.hold)}${pcell(pt7.lp+pt7.fees-pt7.hold)}${pcell(pt7.lp+pt7.fees-pt7.cost)}</tr>`:'') +
  (PY.length?`<tr><td colspan="5" style="text-align:left;white-space:normal;font-family:var(--sans);color:var(--muted);font-size:11.5px;border:0;padding-top:10px">Deposited at a cost of ${fmt.usd(pt7.cost,2)}; positions worth ${fmt.usd(pt7.lp,2)} on ${yd}, against ${fmt.usd(pt7.hold,2)} had the reserve held the same tokens.</td></tr>`:'');
// allocation of the same seven days of fee income as the fee income chart: each day's token fees and charter proceeds follow its epoch's
// routing (vault 70%, to the reserve in expansion and to buybacks in contraction; POL 15%; team 15%); days of the live epoch are not yet routed
const epOfDate = {}; E.forEach(e=>{for(let t=e.start+3600;t<e.end;t+=86400) epOfDate[fmt.dt(t)] = e;});
const al = {pool:0, vExp:0, vCon:0, pol:0, team:0, open:0};
s7.forEach(r=>{const tok=((r.tradingFeeEth||0)+(r.charterEth||0))*ethOf(r), e=epOfDate[r.date]; al.pool += r.spFee||0;
  if(e && e.routed>0){ const v=tok*e.toVault/e.routed; if(isExp(e)) al.vExp+=v; else al.vCon+=v; al.pol += tok*e.toPol/e.routed; al.team += tok*e.team/e.routed; } else al.open += tok; });
const went = [
  ['Reserve backing', al.pool+al.vExp, C.peri, [['pool fees',al.pool],['expansion vault',al.vExp]].filter(x=>x[1]>0.5).map(x=>x[0]+' '+fmt.usd(x[1])).join(' · ')],
  ['Buybacks', al.vCon+al.pol, C.gold, [['contraction vault',al.vCon],['POL',al.pol]].filter(x=>x[1]>0.5).map(x=>x[0]+' '+fmt.usd(x[1])).join(' · ')],
  ['Team', al.team, C.peach, `15% of routed fees`],
  ['Not yet routed', al.open, C.dim, `epoch ${L.epoch}, routed at settlement ${dm(fmt.dt(L.epochEnd))} ${fmt.hm(L.epochEnd)} UTC`],
];
const wTot = sum(went.map(w=>w[1]));
document.getElementById('went_bar').innerHTML = went.map(w=>`<div style="width:${(100*w[1]/wTot).toFixed(2)}%;background:${w[2]}" title="${w[0]}"></div>`).join('');
document.getElementById('went_leg').innerHTML = went.map(w=>`<i style="background:${w[2]}"></i><span>${w[0]}</span><span class="v">${fmt.usd(w[1])}</span><span class="p">${fmt.pct(w[1]/wTot,0)}</span><span class="sub">${w[3]}</span>`).join('');
document.getElementById('went_n').textContent = fmt.usd(wTot);
document.getElementById('went_src').textContent = s7.length ? `Total ${fmt.usd(wTot)}: recurring revenue ${fmt.usd(rec7)} and charter sales ${fmt.usd(chs7)} for ${dm(s7[0].date)} to ${dm(s7[s7.length-1].date)}. ${fmt.n(bb7,2)} STANDARD bought back in the same days.` : '';

// ---------- holder groups, sellers, depth (compiled) ----------
const GN = Object.fromEntries(GROUPS.map(g=>[g[0], g[1]]));
const ms7 = sum(s7.map(r=>r.mktNet||0)), gs7 = GROUPS.map(([k,n])=>[n, sum(s7.map(r=>r['sell_'+k]||0))]).sort((a,b)=>b[1]-a[1]);
document.getElementById('sell_now').textContent = s7.length ? `${fmt.sgn(ms7)}${fmt.n(ms7,2)} net, ${dm(s7[0].date)} to ${dm(s7[s7.length-1].date)} · ${gs7[0][0].toLowerCase()} ${fmt.sgn(gs7[0][1])}${fmt.n(gs7[0][1],2)}` : '';
const SL = DATA.sellers || [];
const shortA = a=>`<a href="https://robin.etherscan.io/address/${a}" target="_blank" rel="noopener" style="color:inherit;text-decoration:none">${a.slice(0,6)}…${a.slice(-4)}</a>`;
document.getElementById('t_sellers').innerHTML = '<tr><th>Wallet</th><th>Group</th><th>Net sold</th><th>Sells</th><th>Buys</th></tr>' +
  SL.map(x=>`<tr><td style="font-family:var(--mono)">${shortA(x.addr)}</td><td style="text-align:left">${GN[x.group]||x.group}</td><td>${fmt.n(x.net,2)}</td><td>${x.sells}</td><td>${x.buys}</td></tr>`).join('');
const DP = DATA.depth || null;
if (DP) {
  document.getElementById('dp_now').textContent = `${fmt.usd(DP.bid2)} bid · ${fmt.usd(DP.ask2)} ask within 2%`;
  const pc = v=>v==null?'–':fmt.pct(v,1);
  document.getElementById('t_slip').innerHTML = '<tr><th>Size</th><th>Buy impact</th><th>Buy cost</th><th>Sell impact</th><th>Sell cost</th></tr>' +
    DP.slip.map(x=>`<tr><td>${fmt.usd(x.usd,0)}</td><td>${pc(x.buyImpact)}</td><td>${pc(x.buyAllIn)}</td><td>${pc(x.sellImpact)}</td><td>${pc(x.sellAllIn)}</td></tr>`).join('');
  document.getElementById('slip_s').innerHTML = [['Pool fee and tax', `${fmt.pct(DP.fee,0)} · ${fmt.pct(DP.taxBuy,0)} buy, ${fmt.pct(DP.taxSell,0)} sell`], ['Depth within 5%', `${fmt.usd(DP.bid5)} bid · ${fmt.usd(DP.ask5)} ask`], ['Protocol share of in-range liquidity', fmt.pct(DP.protocolShare,0)], ['Open liquidity ranges', fmt.int(DP.positions)]].map(x=>`<div>${x[0]}</div><div>${x[1]}</div>`).join('');
}

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
  mk(c_pb, {type:'line', data:{labels:ll, datasets:[
    {label:'Price to backing', data:Rl.map(pbOf), borderColor:C.gold, backgroundColor:'rgba(255,221,138,.10)', fill:true, pointRadius:0, tension:.25},
  ]}, options:{maintainAspectRatio:false, plugins:{legend:{display:false}, bands:{dates:dl}, tooltip:{callbacks:{label:c=>'Price to backing: '+c.parsed.y.toFixed(2)+'×',
    afterBody:items=>{const r=Rl[items[0].dataIndex]; return r.reserveUsd&&r.float ? [`price $${(r.price||0).toFixed(4)} · backing $${(r.reserveUsd/r.float).toFixed(4)} per outstanding token`, `reserve ${fmt.usd(r.reserveUsd)} · outstanding ${fmt.n(r.float,2)}`, ...(r.date<'2026-10-14'&&r.reserveParts&&r.reserveParts.stocks>0?['equities at their pools’ first close, 14 Oct']:[])] : [];}}}},
    scales:{x:{grid:{display:false}, ticks:{maxTicksLimit:8}}, y:{beginAtZero:true, ticks:{callback:v=>v.toFixed(1)+'×'}}}}});
  mk(c_prr, {type:'line', data:{labels:lf, datasets:[
    {label:'Price to recurring revenue', data:Rf.map(prrOf), borderColor:C.gold, backgroundColor:'rgba(255,221,138,.10)', fill:true, pointRadius:0, tension:.25, spanGaps:false},
  ]}, options:{maintainAspectRatio:false, plugins:{legend:{display:false}, bands:{dates:df}, tooltip:{callbacks:{label:c=>'Price to recurring revenue: '+c.parsed.y.toFixed(1)+'×',
    afterBody:items=>{const r=Rf[items[0].dataIndex], v=recRoll(r); return v!=null ? [`market capitalization, outstanding ${fmt.usd(r.mcFloat)}`, `recurring revenue ${fmt.usd(v)} over seven days, ${fmt.usd(v*365/7)} annualized`] : [];}}}},
    scales:{x:{grid:{display:false}, ticks:{maxTicksLimit:8}}, y:{beginAtZero:true, ticks:{callback:v=>v.toFixed(1)+'×'}}}}});
  mk(c_sell, {data:{labels:lf, datasets:[
    ...GROUPS.map(([k,n,c])=>({type:'bar', label:n, data:Rf.map(r=>r['sell_'+k]||0), backgroundColor:c, stack:'s', order:2})),
    {type:'line', label:'Net market sales', data:Rf.map(r=>r.mktNet||0), borderColor:C.gold, backgroundColor:C.gold, pointRadius:2, tension:.25, stack:'line', order:1},
  ]}, options:{maintainAspectRatio:false, scales:{x:{stacked:true, grid:{display:false}}, y:{stacked:true, ticks:{callback:v=>fmt.n(v,0)}}}, plugins:{bands:{dates:df}, tooltip:{callbacks:{label:c=>c.dataset.label+': '+fmt.sgn(c.parsed.y)+fmt.n(c.parsed.y,2)+' STANDARD',
    footer:items=>{const r=Rf[items[0].dataIndex]; return r.price ? `net ${fmt.usd((r.mktNet||0)*r.price)} at the day’s close; positive is net selling` : '';}}}}}});
  mk(c_depth, {type:'line', data:{labels:ll, datasets:[
    {label:'Bid depth within 2%', data:Rl.map(r=>r.bid2??null), borderColor:C.gold, backgroundColor:'rgba(255,221,138,.12)', fill:'origin', pointRadius:0, tension:.25},
    {label:'Bid depth within 5%', data:Rl.map(r=>r.bid5??null), borderColor:C.peri, pointRadius:0, tension:.25},
  ]}, options:{maintainAspectRatio:false, plugins:{bands:{dates:dl}, tooltip:{callbacks:{label:c=>c.dataset.label+': '+fmt.usd(c.parsed.y,1),
    afterBody:items=>{const r=Rl[items[0].dataIndex]; return r.ask2!=null ? [`ask depth ${fmt.usd(r.ask2,1)} within 2% · ${fmt.usd(r.ask5,1)} within 5%`] : [];}}}}, scales:{x:{grid:{display:false}, ticks:{maxTicksLimit:8}}, y:{beginAtZero:true, ticks:{callback:v=>fmt.usd(v,0)}}}}});
  const eqRoll = Rf.map(r=>{const w=winEnd(r,7), t=w?sum(w.map(rec)):0; return (w&&t&&w[0].date>=ep2)?sum(w.map(x=>spf(x,allPools)))/t:null;});
  mk(c_equity, {data:{labels:lf, datasets:[
    ...allPools.map((p,i)=>({type:'bar', label:pname(p)+' fees', data:Rf.map(r=>r['spFee_'+p]||0), backgroundColor:p==='ETH'?C.peach:[C.peri,C.lav,C.rose,C.water,C.green][i%5], stack:'a', yAxisID:'y', order:2})),
    {type:'line', label:'Pool fees as a share of recurring revenue, trailing 7 days', data:eqRoll, borderColor:C.gold, pointRadius:0, tension:.25, yAxisID:'y1', order:1},
  ]}, options:{maintainAspectRatio:false, scales:{x:{stacked:true, grid:{display:false}}, y:{stacked:true, ticks:{callback:v=>fmt.usd(v,1)}}, y1:{position:'right', grid:{display:false}, min:0, max:1, ticks:{callback:v=>fmt.pct(v,0)}}}, plugins:{bands:{dates:df}, tooltip:{callbacks:{label:c=>c.dataset.yAxisID==='y1'?c.dataset.label+': '+fmt.pct(c.parsed.y,1):c.dataset.label+': '+fmt.usd(c.parsed.y,1)}}}}});
  const Rq = Rf.filter(r=>r.date>=LP0), lq = Rq.map(r=>r.date.slice(5)), dq = Rq.map(r=>r.date);   // pool panels start when the pools opened
  const shareChart = (el, key, num, den, numLabel)=>mk(el, {type:'line', data:{labels:lq, datasets:pools.map(p=>({label:shortP(p), data:Rq.map(r=>r[key+p]??null), borderColor:PCOL[p]||C.water, backgroundColor:PCOL[p]||C.water, pointRadius:0, tension:.25, spanGaps:true}))},
    options:{maintainAspectRatio:false, plugins:{bands:{dates:dq}, tooltip:{callbacks:{label:c=>`${c.dataset.label}: ${fmt.pct(c.parsed.y,1)}`,
      afterBody:items=>{const r=Rq[items[0].dataIndex]; return pools.filter(p=>r[den+p]).map(p=>`${shortP(p)}: ${numLabel} ${fmt.usd(num(r,p)||0,1)} of ${fmt.usd(r[den+p],1)}`);}}}},
      scales:{x:{grid:{display:false}, ticks:{maxTicksLimit:8}}, y:{min:0, max:1, ticks:{callback:v=>fmt.pct(v,0)}}}}});
  shareChart(c_vshare, 'volShare_', (r,p)=>r['spVolMine_'+p]??r['poolVolChain_'+p], 'chainVol_', 'reserve volume');
  shareChart(c_lshare, 'liqShare_', (r,p)=>((r.reserveParts||{}).lp||{})[p], 'chainTvl_', 'reserve position');
  const Rc = Rq.filter(r=>pools.some(p=>r['cpN_'+p]!=null)), lc = Rc.map(r=>r.date.slice(5));   // complete days with a counterparty sample
  mk(c_cpty, {data:{labels:lc, datasets:[
    {type:'bar', label:'Organic users', data:Rc.map(r=>ck(r,'Org')), backgroundColor:C.green, stack:'v', order:2},
    {type:'bar', label:'Cross-venue arbitrage', data:Rc.map(r=>ck(r,'Arb')), backgroundColor:C.rose, stack:'v', order:2},
    {type:'bar', label:'Other bots', data:Rc.map(r=>ck(r,'Bot')), backgroundColor:C.peri, stack:'v', order:2},
    {type:'bar', label:'Fee-exempt contract', data:Rc.map(r=>ck(r,'Fx')), backgroundColor:C.dim, stack:'v', order:2},
    {type:'line', label:'Organic share of volume', data:Rc.map(r=>{const t=sum(CPK.map(k=>ck(r,k))); return t?ck(r,'Org')/t:null;}), borderColor:C.gold, backgroundColor:C.gold, pointRadius:0, tension:.25, yAxisID:'y1', stack:'l', order:1},
  ]}, options:{maintainAspectRatio:false, scales:{x:{stacked:true, grid:{display:false}}, y:{stacked:true, ticks:{callback:v=>fmt.usd(v,1)}}, y1:{position:'right', grid:{display:false}, min:0, max:1, ticks:{callback:v=>fmt.pct(v,0)}}},
    plugins:{bands:{dates:Rc.map(r=>r.date)}, tooltip:{callbacks:{label:c=>c.dataset.yAxisID==='y1'?c.dataset.label+': '+fmt.pct(c.parsed.y,0):c.dataset.label+': '+fmt.usd(c.parsed.y,1)}}}}});
  const plRows = Rq.map(r=>pools.map(p=>{const v=pnlOf(r,p); return v? v.lp+v.fees-v.hold : null;}));
  mk(c_pnl, {type:'line', data:{labels:lq, datasets:[
    ...pools.map((p,i)=>({label:shortP(p), data:plRows.map(x=>x[i]), borderColor:PCOL[p]||C.water, backgroundColor:PCOL[p]||C.water, pointRadius:0, tension:.25})),
    {label:'All pools', data:plRows.map(x=>x.some(v=>v!=null)?sum(x):null), borderColor:C.gold, backgroundColor:C.gold, borderWidth:2.5, pointRadius:0, tension:.25},
  ]}, options:{maintainAspectRatio:false, plugins:{bands:{dates:dq}, tooltip:{callbacks:{label:c=>c.dataset.label+': '+fmt.sgn(c.parsed.y)+fmt.usd(c.parsed.y,1),
    afterBody:items=>{const r=Rq[items[0].dataIndex]; return pools.map(p=>{const v=pnlOf(r,p); return v?`${shortP(p)}: fees ${fmt.usd(v.fees,1)}, divergence ${fmt.sgn(v.lp-v.hold)}${fmt.usd(v.lp-v.hold,1)}`:'';}).filter(Boolean);}}}},
    scales:{x:{grid:{display:false}, ticks:{maxTicksLimit:8}}, y:{ticks:{callback:v=>fmt.usd(v,0)}}}}});
  mk(c_income, {type:'bar', data:{labels:lf, datasets:[
    {label:'Token trading fees', data:Rf.map(tr), backgroundColor:C.lav, stack:'r'},
    {label:'Pool fee income', data:g('spFee'), backgroundColor:C.peach, stack:'r'},
    {label:'Charter sales', data:Rf.map(chs), backgroundColor:C.gold2, stack:'c'},
  ]}, options:{maintainAspectRatio:false, scales:{x:{stacked:true,grid:{display:false}}, y:{stacked:true, ticks:{callback:v=>fmt.usd(v,0)}}}, plugins:{bands:{dates:df}, tooltip:{callbacks:{label:c=>c.dataset.label+': '+fmt.usd(c.parsed.y,1),
    footer:items=>{const r=Rf[items[0].dataIndex]; return `recurring revenue ${fmt.usd(rec(r),1)} · charter sales ${fmt.usd(chs(r),1)}`;}}}}}});
  const pcol = [C.peri, C.lav, C.rose, C.water, C.green, C.gold2];
  mk(c_pools, {data:{labels:lf, datasets:[
    ...pools.map((p,i)=>({type:'bar', label:pname(p)+' volume, reserve share', data:Rf.map(r=>r['spVolMine_'+p]!=null?r['spVolMine_'+p]:(r['spVol_'+p]||0)), backgroundColor:p==='ETH'?C.peach:pcol[i%pcol.length], stack:'v', yAxisID:'y', order:2})),
    {type:'line', label:'Fee income', data:g('spFee'), borderColor:C.gold, backgroundColor:C.gold, pointRadius:2, yAxisID:'y1', order:1, tension:.25},
    {type:'line', label:'Share of volume at zero fee', data:Rf.map(r=>r.spVol?r.spVolZeroFee/r.spVol:null), borderColor:C.muted, pointRadius:0, yAxisID:'y2', order:0},
  ]}, options:{maintainAspectRatio:false, scales:{x:{stacked:true, grid:{display:false}}, y:{stacked:true, ticks:{callback:v=>fmt.usd(v,1)}}, y1:{position:'right', grid:{display:false}, ticks:{callback:v=>fmt.usd(v,1)}}, y2:{display:false, min:0, max:1}}, plugins:{tooltip:{callbacks:{label:c=>c.dataset.yAxisID==='y2'?c.dataset.label+': '+fmt.pct(c.parsed.y,0):c.dataset.label+': '+fmt.usd(c.parsed.y,1),
    afterBody:items=>{const r=Rf[items[0].dataIndex]; return pools.filter(p=>(r['spVol_'+p]||0)>0).map(p=>{const g=r['spVol_'+p]||0, m=r['spVolMine_'+p]!=null?r['spVolMine_'+p]:g; return `${pname(p)}: pool total ${fmt.usd(g,1)}, served by the reserve ${fmt.pct(g?m/g:null,0)}`;});}}}}}});
  const fd = (r)=>(r.supply!=null&&r.pending!=null) ? r.supply+r.pending : null;   // minted plus ledger
  const dFdAll = Sh.map((r,i)=> i>0&&fd(r)!=null&&fd(Sh[i-1])!=null ? fd(r)-fd(Sh[i-1]) : null), dFd = last(dFdAll, N);
  mk(c_mc, {type:'line', data:{labels:ll, datasets:[
    {label:'Outstanding supply', data:Rl.map(r=>r.float), borderColor:C.gold, backgroundColor:'rgba(255,221,138,.38)', fill:'origin', borderWidth:1.5, pointRadius:0, tension:.25},
    {label:'Protocol pool and Incentives Vault', data:Rl.map(r=>(r.pool||0)+(r.incentives||0)), borderColor:C.peri, backgroundColor:'rgba(143,162,240,.32)', fill:'-1', borderWidth:1.5, pointRadius:0, tension:.25},
    {label:'Ledger balance owed to bankers, unminted', data:Rl.map(r=>r.pending), borderColor:C.water, backgroundColor:'rgba(205,189,240,.22)', fill:'-1', borderWidth:1.5, pointRadius:0, tension:.25},
  ]}, options:{maintainAspectRatio:false, scales:{x:{grid:{display:false}}, y:{stacked:true, beginAtZero:true, ticks:{callback:v=>fmt.n(v,0)}}}, plugins:{bands:{dates:dl}, tooltip:{callbacks:{label:c=>c.dataset.label+': '+fmt.n(c.parsed.y,2),
    footer:items=>{const r=Rl[items[0].dataIndex]; return 'Total '+fmt.n((r.supply||0)+(r.pending||0),2)+' STANDARD, of which '+fmt.n(r.supply||0,2)+' exists as tokens';}}}}}});
  // outstanding supply flows: named movements plus protocol-contract inventory, summing to the day's change in outstanding supply
  const ofl = (r)=>{const i=Sh.indexOf(r), p=i>0?Sh[i-1]:null; if(!p) return null;
    const dF=r.float-p.float, W=(r.mint||0), Dist=(r.fromIncentives||0), Fees=(r.feesToTeam||0), Mk=-(r.mktNet||0), Dep=-(r.depositBurn||0), Ob=-((r.burn||0)-(r.depositBurn||0)-(r.burn_contraction||0)-(r.burnOther||0));   // tax hook burns come out of the pool, not outstanding supply
    return {dF, W, Dist, Fees, Mk, Dep, Ob, Oth:dF-(W+Dist+Fees+Mk+Dep+Ob)};};
  const OF = Rf.map(ofl), of = (k)=>OF.map(o=>o?o[k]:null);
  mk(c_flows, {data:{labels:lf, datasets:[
    {type:'bar', label:'Withdrawals minted', data:of('W'), backgroundColor:C.green, stack:'a', order:2},
    {type:'bar', label:'Incentives Vault distributions', data:of('Dist'), backgroundColor:C.water, stack:'a', order:2},
    {type:'bar', label:'Position fees to the team wallet', data:of('Fees'), backgroundColor:C.rose, stack:'a', order:2},
    {type:'bar', label:'Net market purchases from the pool', data:of('Mk'), backgroundColor:'rgba(185,166,227,.55)', stack:'a', order:2},
    {type:'bar', label:'Deposits (converted to ledger)', data:of('Dep'), backgroundColor:C.dim, stack:'a', order:2},
    {type:'bar', label:'S-Bill burns', data:of('Ob'), backgroundColor:C.red, stack:'a', order:2},
    ...(OF.some(o=>o&&Math.abs(o.Oth)>=0.5)?[{type:'bar', label:'Protocol contracts, other', data:of('Oth'), backgroundColor:C.peach, stack:'a', order:2}]:[]),
    {type:'line', label:'Change in outstanding supply', data:of('dF'), borderColor:C.gold, backgroundColor:C.gold, pointRadius:2, tension:.25, stack:'line', order:1},
  ]}, options:{maintainAspectRatio:false, scales:{x:{stacked:true, grid:{display:false}}, y:{stacked:true, ticks:{callback:v=>fmt.n(v,0)}}}, plugins:{bands:{dates:df}, tooltip:tt(v=>fmt.sgn(v)+fmt.n(v,2)+' STANDARD')}}});
  const cumAll = []; { let c=0; Sp.forEach(r=>{c+=burnAll(r); cumAll.push(c);}); }
  const cumW = last(cumAll, N);
  mk(c_issue, {data:{labels:lf, datasets:[
    {type:'bar', label:'Expansion licenses', data:g('licBurn'), backgroundColor:C.gold2, stack:'b', yAxisID:'y', order:3},
    {type:'bar', label:'Resolution and revocation fees, burned half', data:Rf.map(r=>(r.exitFeeBurn||0)+(r.revokeFeeBurn||0)), backgroundColor:C.peach, stack:'b', yAxisID:'y', order:3},
    {type:'bar', label:'Buybacks and other token burns', data:Rf.map(burnTokens), backgroundColor:C.red, stack:'b', yAxisID:'y', order:3},
    {type:'line', label:'Cumulative burned, share of the 1B cap', data:cumW.map(v=>v/1e9), borderColor:C.water, pointRadius:0, tension:.25, yAxisID:'y1', order:1},
  ]}, options:{maintainAspectRatio:false, scales:{x:{stacked:true, grid:{display:false}}, y:{stacked:true, ticks:{callback:v=>fmt.n(v,0)}}, y1:{position:'right', grid:{display:false}, ticks:{callback:v=>fmt.pct(v,1)}}}, plugins:{bands:{dates:df}, tooltip:{callbacks:{label:c=>c.dataset.yAxisID==='y1'?c.dataset.label+': '+fmt.pct(c.parsed.y,2):c.dataset.label+': '+fmt.n(c.parsed.y,2)+' STANDARD',
    afterBody:items=>{const i=items[0].dataIndex; return [`burned that day ${fmt.n(burnAll(Rf[i]),2)} · cumulative ${fmt.n(cumW[i],2)} STANDARD`];}}}}}});
  mk(c_bank, {data:{labels:lf, datasets:[
    {type:'bar', label:'Deposits', data:g('deposits'), backgroundColor:C.green, stack:'a', order:2},
    {type:'bar', label:'Withdrawals (gross)', data:g('wdGross').map(v=>-v), backgroundColor:C.peach, stack:'a', order:2},
    {type:'line', label:'Ledger balance (unminted)', data:g('pending'), borderColor:C.gold, pointRadius:0, tension:.25, yAxisID:'y1', order:1},
  ]}, options:{maintainAspectRatio:false, scales:{x:{stacked:true, grid:{display:false}}, y:{stacked:true, ticks:{callback:v=>fmt.n(v,0)}}, y1:{position:'right', grid:{display:false}, beginAtZero:true, ticks:{callback:v=>fmt.n(v,1)}}}, plugins:{tooltip:tt(v=>fmt.n(v,2)+' STANDARD')}}});
  mk(c_policy, {data:{labels:ll, datasets:[
    {type:'line', label:'Branches', data:Rl.map(r=>r.branches), borderColor:C.peri, backgroundColor:'rgba(143,162,240,.12)', fill:true, pointRadius:0, tension:.2},
    {type:'line', label:'Active charters', data:Rl.map(r=>r.activeCharters), borderColor:C.rose, pointRadius:0, tension:.2},
  ]}, options:{maintainAspectRatio:false, scales:{x:{grid:{display:false}, ticks:{maxTicksLimit:10}}, y:{beginAtZero:true, ticks:{callback:v=>fmt.n(v,1)}}}, plugins:{bands:{dates:dl}, tooltip:tt(v=>fmt.int(v))}}});
}
draw();
document.querySelectorAll('#range button').forEach(b=>b.addEventListener('click',()=>{N=+b.dataset.n; document.querySelectorAll('#range button').forEach(x=>x.classList.toggle('on',x===b)); draw();}));

// ---------- top bankers ----------
let LD = DATA.leaders || {rows:[]};
const who = (l)=>`<a href="https://robin.etherscan.io/address/${l.owner}" target="_blank" rel="noopener" style="color:inherit;text-decoration:none">${l.ens ? l.ens : l.owner.slice(0,6)+'…'+l.owner.slice(-4)}</a>`;
const rkc = (l)=>l.prevRank==null ? '<td class="mut">–</td>' : (l.prevRank-l.rank===0 ? '<td class="mut">0</td>' : `<td class="${l.prevRank-l.rank>0?'pos':'neg'}">${l.prevRank-l.rank>0?'▲':'▼'} ${Math.abs(l.prevRank-l.rank)}</td>`);
let leadOpen = false;
function renderLeaders(){
  document.getElementById('lead_n').textContent = `${fmt.int(LD.bankers)} bankers · ${fmt.int(LD.banks)} charters · ${fmt.int(LD.branches)} branches`;
  document.getElementById('t_lead').innerHTML = '<tr><th>Rank</th><th>Banker</th><th>Charters</th><th>Branches</th><th>Share of branches</th><th>Emissions, this epoch</th><th>Emissions, lifetime</th><th>Rank change</th></tr>' +
    LD.rows.map((l,i)=>`<tr class="${i>=10?'more':''}"><td>${l.rank}</td><td style="text-align:left;font-family:var(--mono)">${who(l)}</td><td>${l.banks}</td><td>${l.branches}</td><td>${fmt.pct(l.branchShare,1)}</td><td>${fmt.n(l.epochEmissions,1)}</td><td>${fmt.n(l.lifetimeEmissions,2)}</td>${rkc(l)}</tr>`).join('');
  document.getElementById('t_lead').classList.toggle('open', leadOpen);
  document.getElementById('lead_more').textContent = leadOpen ? 'View top 10' : 'View top 25';
}
renderLeaders();
document.getElementById('lead_more').addEventListener('click',()=>{leadOpen=!leadOpen; renderLeaders();});

// ---------- daily log, since launch ----------
const cols = [
  ['Date', r=>r.date, r=>r.date],
  ['Price', r=>r.price!=null?'$'+r.price.toFixed(4):'–', r=>r.price],
  ['Market cap (minted)', r=>fmt.usd(r.mcTotal), r=>r.mcTotal],
  ['Market cap (outstanding)', r=>fmt.usd(r.mcFloat), r=>r.mcFloat],
  ['Minted supply', r=>fmt.n(r.supply,2), r=>r.supply],
  ['Outstanding', r=>fmt.n(r.float,2), r=>r.float],
  ['Recurring revenue ($)', r=>fmt.usd(rec(r),1), r=>rec(r)],
  ['Charter sales ($)', r=>fmt.usd(chs(r),1), r=>chs(r)],
  ['Routed (ETH)', r=>(r.routedEth||0).toFixed(1), r=>r.routedEth||0],
  ['Charters sold', r=>r.chartersSold?`${r.chartersSold} @ ${(r.charterEth/r.chartersSold).toFixed(2)}`:'–', r=>r.chartersSold||0],
  ['Charter sales (ETH)', r=>(r.charterEth||0).toFixed(2), r=>r.charterEth||0],
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
  ['Ledger balance', r=>fmt.n(r.pending,2), r=>r.pending],
  ['Resolution (exit) fee', r=>fmt.pct(r.exitFee,1), r=>r.exitFee],
  ['S-Bill rate', r=>r.sbRate!=null?(r.sbRate*100).toFixed(2)+'%':'–', r=>r.sbRate==null?'':r.sbRate],
  ['S-Bill principal', r=>fmt.n(r.sbLocked!=null?r.sbLocked:r.sbills,2), r=>r.sbLocked!=null?r.sbLocked:r.sbills],
  ['Team STANDARD', r=>fmt.n(r.teamStd,2), r=>r.teamStd],
  ['Pool volume', r=>fmt.usd(r.spVol||0,1), r=>r.spVol||0],
  ['Served by reserve', r=>fmt.usd(r.spVolMine!=null?r.spVolMine:(r.spVol||0),1), r=>r.spVolMine!=null?r.spVolMine:(r.spVol||0)],
  ['Pool fee income', r=>fmt.usd(r.spFee||0,1), r=>r.spFee||0],
  ['Reserve', r=>r.reserveUsd!=null?fmt.usd(r.reserveUsd):'–', r=>r.reserveUsd??''],
  ['Price to backing', r=>pbOf(r)!=null?pbOf(r).toFixed(2)+'×':'–', r=>pbOf(r)??''],
  ['Net market sales', r=>r.mktNet!=null?fmt.sgn(r.mktNet)+fmt.n(r.mktNet,1):'–', r=>r.mktNet??''],
  ['Depth ±2%, bid', r=>r.bid2!=null?fmt.usd(r.bid2,1):'–', r=>r.bid2??''],
  ['Regime', r=>regime[r.date]===undefined?'–':regime[r.date]?'exp':'con', r=>regime[r.date]===undefined?'':regime[r.date]?'expansion':'contraction'],
];
// supply / pool / outstanding table; the market column is the pool change plus the protocol's own purchases, so every row ties
const fl = (r,i)=>{const p=i>0?Sh[i-1]:null; const mint=(r.mint||0)+(r.genesisMint||0), dep=r.depositBurn||0, bb=(r.burn||0)-dep;
  const dP=p?r.pool-p.pool:null, mkt=r.mktNet!=null?r.mktNet:null, prot=dP!=null&&mkt!=null?dP-mkt:null;   // protocol: buybacks, POL purchases, position fees collected
  return {p, dS:p?r.supply-p.supply:null, dP, dI:p?r.incentives-p.incentives:null, dF:p?r.float-p.float:null, mint, dep, bb, mkt, prot};};
const sc = (v,inv)=>v==null?'<td>–</td>':`<td class="${(inv?-v:v)>0?'pos':(inv?-v:v)<0?'neg':'mut'}">${Math.abs(v)<0.5?'0':fmt.sgn(v)+fmt.n(v,2)}</td>`;
let floatOpen = false;
function renderFloat(){
  const frows = Sh.map((r,i)=>({r, ...fl(r,i)})).reverse();
  document.getElementById('t_float').innerHTML = '<tr><th>Date</th><th>Minted supply</th><th>Change</th><th>+ Withdrawals</th><th>− Deposits</th><th>− Burned</th><th>Protocol pool</th><th>Change</th><th>+ Market sales</th><th>− Protocol</th><th>Incentives Vault, change</th><th>Outstanding</th><th>Change</th><th>%</th><th>Price</th></tr>' +
    frows.map((x,i)=>`<tr class="${x.r.date===L.date?'today':''}${i>=10?' more':''}"><td>${x.r.date}</td><td>${fmt.n(x.r.supply,2)}</td>${sc(x.dS)}${sc(x.mint)}${sc(-x.dep)}${sc(-x.bb)}<td>${fmt.n(x.r.pool,2)}</td>${sc(x.dP,true)}${sc(x.mkt,true)}${sc(x.prot,true)}${sc(x.dI,true)}<td>${fmt.n(x.r.float,2)}</td>${sc(x.dF)}<td class="${x.dF>0?'pos':x.dF<0?'neg':''}">${x.p?fmt.sgn(x.dF)+fmt.pct(x.dF/x.p.float,2):'–'}</td><td>${x.r.price!=null?'$'+x.r.price.toFixed(4):'–'}</td></tr>`).join('');
  document.getElementById('t_float').classList.toggle('open', floatOpen);
  document.getElementById('fmore').textContent = floatOpen ? 'View 10 days' : `View all ${frows.length} days`;
}
renderFloat();
document.getElementById('fmore').addEventListener('click',()=>{floatOpen=!floatOpen; renderFloat();});
[['fold_ep','f_ep','ledger'],['fold_rs','f_rs','table']].forEach(([b,f,n])=>{const B=document.getElementById(b), F=document.getElementById(f); B.addEventListener('click',()=>{F.classList.toggle('open'); B.textContent=(F.classList.contains('open')?'Hide ':'View ')+n;});});
document.querySelectorAll('.panel').forEach(pn=>{const d=pn.querySelector(':scope > .h .d'), src=pn.querySelector(':scope > .src'); let tip=pn.querySelector(':scope > .tip');
  if(!tip && (d||src)){const i=document.createElement('span'); i.className='i'; i.tabIndex=0; i.textContent='i'; tip=document.createElement('div'); tip.className='tip'; pn.prepend(tip); pn.prepend(i);}
  if(tip){ if(d && d.textContent.trim() && !tip.textContent.includes(d.textContent.trim().slice(0,40))) tip.innerHTML = d.textContent.trim()+' '+tip.innerHTML; if(src && src.textContent.trim()) tip.innerHTML += '<span class="srcnote">'+src.textContent.trim()+'</span>'; }});
let logOpen = false;
function renderLog(){
  const logRows = Sh.slice().reverse();
  document.getElementById('t_log').innerHTML = '<tr>'+cols.map(c=>'<th>'+c[0]+'</th>').join('')+'</tr>' +
    logRows.map((r,i)=>`<tr class="${r.date===L.date?'today':''}${i>=10?' more':''}">`+cols.map(c=>'<td>'+c[1](r)+'</td>').join('')+'</tr>').join('');
  document.getElementById('t_log').classList.toggle('open', logOpen);
  document.getElementById('more').textContent = logOpen ? 'View 10 days' : `View all ${logRows.length} days`;
}
renderLog();
document.getElementById('more').addEventListener('click',()=>{logOpen=!logOpen; renderLog();});
document.getElementById('csv').addEventListener('click',()=>{
  const esc = v=>{v=v==null?'':String(v); return /[",\n]/.test(v)?'"'+v.replace(/"/g,'""')+'"':v;};
  const csv = [cols.map(c=>esc(c[0])).join(',')].concat(Sh.map(r=>cols.map(c=>esc(c[2](r))).join(','))).join('\n');
  const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([csv],{type:'text/csv'})); a.download = 'standard-reserve-daily-'+L.date+'.csv'; a.click();
});

// ---------- live overlay ----------
// Between compiles the browser replays every block after the compile block. It reads the indexer's snapshot, takes that snapshot's block
// as the reference, reads balances there over the RPC, replays STANDARD transfer logs, charter purchases and indexer events up to it with
// the same rules as the compiler, and reads DexScreener's price. Tiles, panel headers, today's chart points and table rows, the supply
// reconciliation, the auctions and the top bankers then describe one block. Pool swaps, fee income and the reserve stay as compiled.
const COMPILED = '__ASOF_UTC__', STD_ADDR = '0x88ad8DdF1E3898412146a534538d418c6F8A9062';
const RPCU = 'https://rpc.mainnet.chain.robinhood.com', IXU = 'https://indexer.standardreserve.xyz/v1/';
const TRF = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef', PURCH = '0x1c54748c22f6bf384e0cf9a6a4dfbc630c9ac343ba8a88a5769508bd2da18e50';
const A = DATA.addrs || null, TIP = DATA.tip, TIPTS = DATA.tipTs || DATA.pulledAt;
const clone = o=>JSON.parse(JSON.stringify(o));
const BASE = {L:clone(L), row:clone(Sh[Sh.length-1]||{}), n:Sh.length, sn:S.length, ch:clone(CH), lp:clone(LP), ld:clone(LD)};
const WN = A ? {[A.zero]:'zero', [A.poolManager]:'pool', [A.contractionVault]:'contraction', [A.polBuyback]:'polBuyback', [A.incentivesVault]:'incentives',
  [A.sbills]:'sbills', [A.centralBank]:'bank', [A.teamWallet]:'team', [A.reserveSafe]:'safe', [A.polManager]:'polManager', [A.feeSplitter]:'feeSplitter', [A.taxHook]:'taxHook', [A.expansionVault]:'expansion'} : {};
const MARKET = new Set(['team','other']);   // pool counterparties that are not protocol contracts
const pad = a=>'0x'+a.slice(2).toLowerCase().padStart(64,'0');
const big = x=>Number(BigInt(x))/1e18;
function restore(){
  Object.keys(L).forEach(k=>{if(!(k in BASE.L)) delete L[k];}); Object.assign(L, clone(BASE.L));
  Sh.length = BASE.n; S.length = BASE.sn; const R = Sh[BASE.n-1];
  if (R) { Object.keys(R).forEach(k=>{if(!(k in BASE.row)) delete R[k];}); Object.assign(R, clone(BASE.row)); }
  CH.length = 0; CH.push(...clone(BASE.ch)); LP.length = 0; LP.push(...clone(BASE.lp)); LD = clone(BASE.ld);
}
async function rpc(calls){
  const r = await fetch(RPCU, {method:'POST', headers:{'content-type':'application/json'}, body:JSON.stringify(calls.map((c,i)=>({jsonrpc:'2.0', id:i, method:c[0], params:c[1]})))});
  const j = await r.json(), out = []; (Array.isArray(j)?j:[j]).forEach(x=>{out[x.id] = x.result;}); return out;
}
async function logsTo(B, q){   // eth_getLogs from the block after the compile to B, in 100k-block steps (the RPC's limit for OR-lists in a topic)
  const out = []; for (let lo=TIP+1; lo<=B; lo+=100000) { const [r] = await rpc([['eth_getLogs', [{...q, fromBlock:'0x'+lo.toString(16), toBlock:'0x'+Math.min(B, lo+99999).toString(16)}]]]); if (!Array.isArray(r)) throw new Error('logs'); out.push(...r); } return out;
}
async function events(kind, B){
  const out = []; let cur = null;
  do { const d = await fetch(`${IXU}activity?chainId=4663&since=${TIPTS-300}&limit=100&kind=${kind}`+(cur?`&cursor=${cur}`:''), {cache:'no-store'}).then(r=>r.json());
       out.push(...(d.events||[])); cur = (d.page||{}).nextCursor; if (!(d.events||[]).length) break; } while (cur);
  return out.filter(e=>{const b=parseInt(e.blockNumber,10); return b>TIP && b<=B;});
}
async function replay(s, B){
  const BT = '0x'+B.toString(16), sc = (to,data)=>['eth_call', [{to, data}, BT]], bal = (who)=>sc(A.STANDARD, '0x70a08231'+pad(who).slice(2));
  const st = await rpc([['eth_call',[{to:A.STANDARD, data:'0x18160ddd'}, BT]], bal(A.poolManager), bal(A.incentivesVault), bal(A.sbills), bal(A.teamWallet),
    sc(A.STANDARD,'0x1ac4a8b5'), sc(A.STANDARD,'0xd5abeb01'), ['eth_getBalance',[A.teamWallet, BT]]]);
  if (st.slice(0,7).some(x=>!x || x==='0x')) throw new Error('state at block '+B+' unavailable');
  const wl = Object.keys(WN).map(pad);
  const [la, lb, lc, ev] = await Promise.all([logsTo(B, {address:A.STANDARD, topics:[TRF, wl]}), logsTo(B, {address:A.STANDARD, topics:[TRF, null, wl]}),
    logsTo(B, {address:A.charterAuction, topics:[PURCH]}),
    Promise.all(['withdrawn','deposited','licenses-purchased','revoked','charter-created'].map(k=>events(k, B)))]);
  const [wd, dep, lic, rev, cc] = ev;
  // flows by UTC date, with the compiler's rules
  const F = {}, f = (d)=>F[d] || (F[d] = {}), add = (d,k,v)=>{const o=f(d); o[k]=(o[k]||0)+v;};
  const seen = new Set();
  // the RPC often returns blockTimestamp 0x0; then interpolate between the compile block and the snapshot block
  const lts = l=>{const t=parseInt(l.blockTimestamp||'0x0',16); if(t) return t; const b=parseInt(l.blockNumber,16); return Math.round(TIPTS + (b-DATA.tip)*(+s.blockTimestamp-TIPTS)/Math.max(1,B-DATA.tip));};
  [...la, ...lb].forEach(l=>{const key=l.transactionHash+':'+l.logIndex; if(seen.has(key)) return; seen.add(key);
    const d = fmt.dt(lts(l)), fr = WN['0x'+l.topics[1].slice(-40)]||'other', to = WN['0x'+l.topics[2].slice(-40)]||'other', a = big(l.data);
    if (fr==='zero') add(d, a>=5e7?'genesisMint':'mint', a);
    if (to==='zero') { add(d,'burn',a); add(d,'burn_'+fr,a); }
    if (to==='pool') add(d, (fr==='zero'||fr==='polManager')?'genesisPool':'poolIn', a);
    if (fr==='pool') add(d,'poolOut',a);
    if (fr==='pool' && to==='polManager') add(d,'feesToTeam',a);
    if (to==='pool' || fr==='pool') { const cp = to==='pool'?fr:to, sg = to==='pool'?1:-1; add(d, MARKET.has(cp)?'mktNet':'protNet', sg*a); }
    if (to==='incentives') add(d,'toIncentives',a); if (fr==='incentives') add(d,'fromIncentives',a);
    if (to==='sbills') add(d,'sbillIn',a); if (fr==='sbills') add(d,'sbillOut',a);
    if (to==='team') add(d,'teamIn',a); if (fr==='team') add(d,'teamOut',a); });
  const tsd = e=>fmt.dt(+e.timestamp), V = e=>e.values||{};
  wd.forEach(e=>{const d=tsd(e), g=big(V(e).gross), n=big(V(e).net); add(d,'wdGross',g); add(d,'wdNet',n); add(d,'exitFeeBurn',(g-n)/2); add(d,'exitFeeRedis',(g-n)/2); add(d,'exits',1);});
  dep.forEach(e=>add(tsd(e),'deposits',big(V(e).amount)));
  rev.forEach(e=>{const v=V(e), g=big(v.gross), fee=g-big(v.bounty)-big(v.ownerNet); add(tsd(e),'revokeFeeBurn',fee/2); add(tsd(e),'revokeGross',g); add(tsd(e),'revoked',1);});
  lic.sort((a,b)=>a.timestamp-b.timestamp).forEach(e=>{const v=V(e), c=+v.count, px=big(v.unitPrice), d=tsd(e); add(d,'licBurn',c*px); add(d,'licCount',c); f(d).licClose = px;
    let q = LP.find(p=>p.day===+v.day); if(!q){ q={day:+v.day, start:+e.timestamp, sold:0, burned:0, close:0, sales:0}; LP.push(q);} q.sold+=c; q.burned+=c*px; q.close=px; q.sales+=1;});
  cc.forEach(e=>{ if (+e.charterId > (DATA.foundingCharters||1000)) add(tsd(e),'chartersSold',1); });
  lc.forEach(l=>{const ts=lts(l), px=Number(BigInt(l.data.slice(0,66)))/1e18; add(fmt.dt(ts),'charterEth',px);
    CH.push({id:parseInt(l.topics[1]||'0x0',16), ts, eth:px, buyer:l.topics[2]?'0x'+l.topics[2].slice(-40):'', viaContract:false});});
  // rows: the compiled last day takes the flows dated to it; any later UTC day gets a new row
  const R0 = Sh[Sh.length-1], dLive = fmt.dt(+s.blockTimestamp), rows = [R0];
  for (let t=Date.parse(R0.date+'T00:00:00Z')/1000+86400; fmt.dt(t)<=dLive; t+=86400) { const r = {date:fmt.dt(t), eth:R0.eth}; S.push(r); Sh.push(r); rows.push(r); }
  rows.forEach(r=>{ Object.entries(F[r.date]||{}).forEach(([k,v])=>{ if(k==='licClose') r[k]=v; else r[k]=(r[k]||0)+v; });
    r.burnBuyback = (r.burn_contraction||0)+(r.burn_polManager||0)+(r.burn_sbills||0); r.depositBurn = r.deposits||0;
    r.burnOther = Math.max(0, (r.burn_other||0)+(r.burn_bank||0)-(r.deposits||0)); });
  // issuance after the compile accrues per second at the multiplier in force (the epoch may have turned since); a compiled day that has
  // since closed carries its ledger balance forward through the replayed events
  const tNow = +s.blockTimestamp, iss = (a,b)=>{ if(b<=a) return 0; const c=Math.min(Math.max(L.epochStart,a),b); return L.baseIssuance*(BASE.L.multiplier*(c-a)+L.multiplier*(b-c))/86400; };
  rows.forEach(r=>{const ds=Date.parse(r.date+'T00:00:00Z')/1000, a=iss(Math.max(ds,TIPTS), Math.min(ds+86400,tNow)); r.issuance=(r===R0?(BASE.row.issuance||0):0)+a; r._iss=a;});
  if (rows.length>1) { const x=F[R0.date]||{};
    R0.pending=(BASE.row.pending||0)+R0._iss+(x.deposits||0)+(x.exitFeeRedis||0)+(x.revokeFeeBurn||0)-(x.licBurn||0)-(x.wdGross||0)-(x.revokeGross||0); }
  // levels at the reference block on the live row, walked back across any day boundary as the compiler does
  let lv = {supply:big(st[0]), pool:big(st[1]), incentives:big(st[2]), sbills:big(st[3]), teamStd:big(st[4])};
  for (let k=rows.length-1; k>=0; k--) { const r=rows[k], x=F[r.date]||{}; Object.assign(r, lv); r.float = r.supply-r.pool-r.incentives;
    lv = {supply:lv.supply-((x.mint||0)+(x.genesisMint||0)-(x.burn||0)), pool:lv.pool-((x.poolIn||0)+(x.genesisPool||0)-(x.poolOut||0)),
          incentives:lv.incentives-((x.toIncentives||0)-(x.fromIncentives||0)), sbills:lv.sbills-((x.sbillIn||0)-(x.sbillOut||0)), teamStd:lv.teamStd-((x.teamIn||0)-(x.teamOut||0))}; }
  const RL = rows[rows.length-1];
  if (RL.reserveUsd==null) { RL.reserveUsd = L.reserve.totalUsd; RL.reserveParts = BASE.row.reserveParts; }   // a new day carries the reserve read at the compile block
  Object.assign(RL, {price:L.price, mcTotal:L.price*RL.supply, mcFloat:L.price*RL.float, pending:L.pending, exitFee:L.exitFeeNow, sbRate:L.sbills.rate, sbLocked:L.sbills.locked,
    multiplier:L.multiplier, branches:L.branches, activeCharters:L.activeCharters, burnedCharters:L.burnedCharters});
  Object.assign(L, {date:RL.date, totalSupply:RL.supply, poolStd:RL.pool, incentivesStd:RL.incentives, sbillsStd:RL.sbills, teamStd:RL.teamStd, float:RL.float,
    burnedForever:big(st[5]), maxSupply:big(st[6]), teamEth:st[7]?Number(BigInt(st[7]))/1e18:L.teamEth});
}
async function goLive(){
  try{
    const j = (u)=>fetch(u,{cache:'no-store'}).then(r=>{if(!r.ok) throw new Error('HTTP '+r.status); return r.json();});
    const [h, sb, dx, lb] = await Promise.all([
      j(IXU+'home?chainId=4663'),
      j(IXU+'sbills/history?chainId=4663&range=1d').catch(()=>null),
      j('https://api.dexscreener.com/tokens/v1/robinhood/'+STD_ADDR).catch(()=>null),
      j(IXU+'leaderboard?chainId=4663').catch(()=>null)]);
    const s = h && h.snapshot; if(!s || !s.bank || !s.token) return;
    restore();
    const W = x=>parseFloat(x)/1e18, I = x=>parseInt(x,10), now = Math.floor(Date.now()/1000);
    const b=s.bank, t=s.token, c=s.census||{}, la=s.licenseAuction, ca=s.charterAuction;
    Object.assign(L, {branches:I(b.totalBranches), multiplier:W(b.multiplierWad), epoch:I(b.epochNumber), epochStart:I(b.epochStart), epochEnd:I(b.epochEnd),
      epochNetFlow:W(s.tax.epochNetFlow), previousEpochFlow:W(b.previousEpochFlow||'0'), positiveStreak:I(b.positiveSignalStreak||'0'),
      pending:W(b.totalPendingLive), cumulativeIssued:W(b.cumulativeIssued), cumulativeRecycled:W(b.cumulativeRecycled||'0'),
      burnedForever:W(t.burnedForever), maxSupply:W(t.maxSupply)});
    if (c.active!=null) Object.assign(L, {activeCharters:I(c.active), burnedCharters:I(c.burned)});
    if (s.charterNft) L.chartersMinted = I(s.charterNft.nextId)-1;
    if (la) Object.assign(L, {licensePriceNow:W(la.currentPrice), licenseLastSale:W(la.lastSalePrice), licenseFloor:W(la.dayFloorPrice), licenseDayStart:W(la.dayStartPrice),
      licenseSoldToday:I(la.soldToday), licenseCap:I(la.dayCap), licenseRemaining:I(la.remainingToday||'0')});
    if (ca) Object.assign(L, {charterPriceNow:W(ca.currentPrice), charterLastSale:W(ca.lastSalePrice), charterFloor:W(ca.dayFloorPrice), charterDayStart:W(ca.dayStartPrice),
      charterSoldToday:I(ca.soldToday), charterCap:I(ca.dayCap), charterRemaining:I(ca.remainingToday||'0')});
    const nxt = a=>{const anchor=I(a.auctionAnchor), per=I(a.AUCTION_DAY), k=Math.floor((now-anchor)/per); return [anchor+(k+1)*per, I(a.startMultiplier)*W(a.lastSalePrice)];};
    if (la) { const n=nxt(la); L.licenseNextOpen=n[0]; L.licenseNextStart=n[1]; }
    if (ca) { const n=nxt(ca); L.charterNextOpen=n[0]; L.charterNextStart=n[1]; }
    // resolution fee: the contract's seven protocol-day buckets of gross withdrawals, today included
    if (Array.isArray(s.withdrawnByDay)) { const w7=sum(s.withdrawnByDay.map(W)); const P=w7/Math.max(L.pending+w7,1e7); L.w7=w7; L.exitPressure7d=P; L.exitFeeNow=0.02+0.58*Math.pow(Math.min(P/0.10,1),2); }
    // S-Bill term rate: the indexer reports it as of the last deposit; it drifts up between deposits
    if (sb && sb.current) { const q=sb.current, dps=q.drifting?W(q.driftPerSecond||'0'):0, cap=q.ceiling?W(q.ceiling):1;
      L.sbills.rate=Math.min(cap, W(q.rate)+dps*Math.max(0, I(s.blockTimestamp)-(q.rateUpdatedAt||I(s.blockTimestamp)))); L.sbills.locked=W(q.locked); L.sbills.principal=W(q.principal||q.locked);
      if(q.floor) L.sbills.floor=W(q.floor); if(q.ceiling) L.sbills.ceiling=W(q.ceiling); }
    if (dx && dx[0] && dx[0].priceUsd) { const p=dx[0]; L.price=parseFloat(p.priceUsd); L.priceChange24h=(p.priceChange||{}).h24; L.vol24=(p.volume||{}).h24; L.poolLiqUsd=(p.liquidity||{}).usd; }
    let rep = '';
    if (A && TIP) { try { await replay(s, I(s.blockNumber)); } catch(e) { restoreRows(); rep = ' · supply as compiled'; console.warn('replay unavailable', e); } }
    if (lb && Array.isArray(lb.bankers)) {
      const ens = {}; (BASE.ld.rows||[]).forEach(r=>{ens[r.owner]=r.ens;});
      const bk = lb.bankers.slice().sort((a,b)=>Number(BigInt(b.lifetimeEmissions||'0')-BigInt(a.lifetimeEmissions||'0')));
      const tb = sum(bk.map(r=>+r.branches||0)) || 1;
      LD = {bankers:bk.length, banks:sum(bk.map(r=>+r.banks||0)), branches:tb, rows:bk.slice(0,25).map((r,i)=>({rank:i+1, owner:r.owner.toLowerCase(), ens:ens[r.owner.toLowerCase()]||'',
        banks:+r.banks||0, branches:+r.branches||0, branchShare:(+r.branches||0)/tb, epochEmissions:W(r.epochEmissions||'0'), lifetimeEmissions:W(r.lifetimeEmissions||'0'), prevRank:(r.previousRank||{}).lifetime}))};
    }
    NOWTS = now; LIVE = true;
    renderKpis(); renderHeads(); renderBridge(); renderFloat(); renderLog(); renderLeaders(); renderAuctions(); draw();
    const hm = new Date(I(s.blockTimestamp)*1000).toISOString().slice(0,16).replace('T',' ');
    document.getElementById('asof').innerHTML = `Live <b>${hm} UTC</b> · block ${I(s.blockNumber).toLocaleString('en-US')} · <span id="epochpill" class="pill ${L.epochNetFlow>=0?'exp':'con'}">Epoch ${L.epoch} · ${L.epochNetFlow>=0?'expansion':'contraction'} to date</span> · pool trading, fee income and reserve compiled ${COMPILED} UTC${rep}`;
  }catch(e){ console.warn('live overlay unavailable, showing compiled figures', e); }
}
function restoreRows(){   // a failed replay leaves supply, rows and auctions at the compile; indexer counts still update the tiles
  const keep = {}; ['branches','multiplier','epoch','epochStart','epochEnd','epochNetFlow','previousEpochFlow','positiveStreak','pending','cumulativeIssued','cumulativeRecycled',
    'activeCharters','burnedCharters','chartersMinted','licensePriceNow','licenseLastSale','licenseFloor','licenseDayStart','licenseSoldToday','licenseCap','licenseRemaining',
    'charterPriceNow','charterLastSale','charterFloor','charterDayStart','charterSoldToday','charterCap','charterRemaining','licenseNextOpen','licenseNextStart','charterNextOpen',
    'charterNextStart','w7','exitPressure7d','exitFeeNow','price','priceChange24h','vol24','poolLiqUsd'].forEach(k=>{keep[k]=L[k];});
  const sbk = clone(L.sbills); restore(); Object.assign(L, keep); L.sbills = sbk;
}
goLive(); setInterval(goLive, 300000);
</script>
"""

html = (TEMPLATE.replace("__HERO__", hero).replace("__ASOF_UTC__", built.strftime("%Y-%m-%d %H:%M")).replace("__ASOF_KST__", kst.strftime("%m-%d %H:%M"))
        .replace("__TIP__", f"{data['tip']:,}").replace("__PERIOD__", str(int(data["live"]["auctionPeriodHours"])))
        .replace("__DATA__", json.dumps({k: v for k, v in data.items() if k != "swaps"}, separators=(",", ":"))))
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html"), "w").write(html)
print("index.html", len(html) // 1024, "KB")
