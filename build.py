#!/usr/bin/env python3
"""Render data/dash.json into index.html: a single-file, tabbed protocol monitor (Chart.js from jsDelivr, fonts from Google Fonts)."""
import json, os, base64, datetime as dt
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
hero_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "reserve-dam.webp")
HERO_IMG = "data:image/webp;base64," + base64.b64encode(open(hero_path, "rb").read()).decode()
data = json.load(open(os.path.join(D, "dash.json")))
built = dt.datetime.fromtimestamp(data["pulledAt"], dt.timezone.utc)


# ---------- page skeleton helpers ----------
def info(tip): return f'<span class="i" tabindex="0">i<span class="tip">{tip}</span></span>'
def panel(w, title, tip, body, head=None, pid=None):
    hd = f'<div class="pn" id="{head}"></div>' if head else ""
    ida = f' id="{pid}"' if pid else ""
    return f'<div class="panel w{w}"{ida}><div class="ph"><div class="pt">{title}</div>{hd}{info(tip)}</div>{body}</div>'
def chart(cid, h=""): return f'<div class="ch {h}"><canvas id="{cid}"></canvas></div>'
def table(tid, cls=""): return f'<div class="tw"><table id="{tid}" class="{cls}"></table></div>'
def kpis(tab): return f'<div class="kpis" id="k_{tab}"></div>'

TABS = [("overview", "Overview"), ("revenue", "Revenue"), ("liquidity", "Liquidity"), ("launchpad", "Launchpad"), ("reserve", "Reserve"),
        ("token", "Token"), ("banks", "Banks"), ("data", "Data")]

SECTIONS = {
"overview": kpis("overview") + '<div class="grid">' +
    panel(7, "Growth monitor, trailing seven days",
          "Flows compare the last seven complete UTC days with the seven before. Levels compare the latest reading with the close seven days earlier. "
          "Shares change in percentage points. Green marks a move that favours the protocol, red one that works against it, grey a neutral measure. "
          "Trends cover 30 days: rolling seven-day sums for flows, daily closes for levels.", table("t_gm", "gm")) +
    '<div class="col w5">' +
    panel(12, "Revenue by stream, weekly", "Seven-day blocks ending on the last complete UTC day, following the range: All shows every complete week since the launch epoch "
          "(the launch week’s genesis fees are left out), 30D the last four weeks, 7D the last seven days by day. Revenue is what the protocol keeps: STANDARD trading "
          "fees (the buy and sell tax), LP fees earned by the reserve’s pool positions, the protocol’s 50% of the launchpad base fee, and charter sales.", chart("c_wrev", "s"), "h_wrev", "p_wrev") +
    panel(12, "Price and backing per token, daily", "Token price against reserve assets per STANDARD in wallets, the tokens holders own; the protocol’s own liquidity and the Incentives vault are left out. The gap between the lines is the premium to backing.",
          chart("c_pxb", "s"), "h_pxb") + '</div>' +
    panel(6, "Reserve assets by component, daily", "Reserve assets at each day’s close, rebuilt from on-chain events and valued at the day’s closing prices. "
          "Today is the reserve read at the compile block.", chart("c_reso"), "h_reso") +
    panel(6, "Branches and active charters, daily", "Branches and active charters, reconstructed from charter, license, withdrawal and revocation events.",
          chart("c_brco"), "h_brco") + '</div>',

"revenue": kpis("revenue") + '<div class="grid">' +
    panel(7, "Revenue by stream, daily", "STANDARD trading fees, the buy and sell tax, are known per three-day epoch and spread evenly over its days; the live epoch is estimated from ETH held in the tax hook "
          "and fee splitter. LP fees replay every swap in the reserve’s pools tick by tick and value each swap’s fee at the pool price of that swap. The launchpad line is the protocol’s 50% of the 1% base fee, "
          "held in the launchpad fee Safe. Charter sales are recorded on the sale date.", chart("c_rev", "l"), "h_rev") +
    panel(5, "Where fees land, trailing seven days", "Where the last seven complete days of revenue went. STANDARD trading fees and charter sales are routed by the fee engine at settlement: 70% to the "
          "reserve in expansion or to buybacks in contraction, 15% to POL buybacks and 15% to the team. LP fees accrue inside the reserve’s positions. The launchpad’s "
          "protocol share sits in the fee Safe and has not been routed.", '<div class="alloc" id="alloc"></div>', "h_alloc") +
    panel(7, "Fee routing by epoch", "STANDARD trading fees and charter proceeds routed by the fee engine at each settlement, in ETH, for the epochs settled inside the selected range. "
          "Green bars are expansion epochs, red contraction.",
          chart("c_epochs"), "h_epochs") +
    panel(5, "Price to revenue, daily", "Market cap, price times circulating supply, over trailing seven-day revenue, annualized. Windows that include the "
          "launch epoch are omitted.", chart("c_prr"), "h_prr") + '</div>',

"liquidity": kpis("liquidity") + '<div class="grid">' +
    panel(12, "Protocol-owned liquidity by pool", "The reserve’s position in each pool and its standing among every pool for the same asset on Robinhood Chain on the last complete "
          "day. Volume is the volume the reserve’s own liquidity served. APR is trailing seven-day LP fees annualized over position value. Rank and venues count pools with "
          "at least $100 of liquidity.", table("t_pools")) +
    panel(6, "Volume served by the reserve, by pool, daily", "Each swap’s USDG amount times the reserve’s share of in-range liquidity. The reserve is the only provider in the equity "
          "pools; it shares the ETH/USDG pool with others.", chart("c_vol"), "h_vol") +
    panel(6, "LP fees by pool, daily", "LP fees earned by the reserve’s positions. Every swap is replayed from the pool’s price before it to the price after it, one "
          "initialized tick at a time, against the liquidity of every provider rebuilt from the pool’s events; the fee on each step is charged on the input token and split "
          "among the providers in range, as the pool contract does. Each swap’s fee is valued at the pool price of that swap. The ETH/USDG figure excludes Uniswap’s "
          "0.0125% protocol fee. A change to a position settles its accrued fees to the Safe; the only one so far, the 14 Oct 2026 addition to the ETH/USDG "
          "position, settled 0.0097 ETH and 26.00 USDG, counted on the days they accrued. Each compile reconciles the fees not yet collected, at today’s pool price, with the "
          "same fees read from the positions; the difference from the sum of daily figures is the move in the pool price since each fee was earned.", chart("c_pfee"), "h_pfee") +
    panel(6, "Share of chain volume by pool, daily", "Volume served by the reserve’s liquidity as a share of all on-chain volume in the same asset, across every pool DexScreener "
          "lists against USDG or ETH.", chart("c_vshare"), "h_vshare", "p_vshare") +
    panel(6, "Share of chain liquidity by pool, daily", "The reserve’s position value as a share of all on-chain liquidity in pools pairing the same asset with USDG or ETH.",
          chart("c_lshare"), "h_lshare", "p_lshare") +
    panel(7, "Pool volume by counterparty, daily", "Fee-exempt swaps are summed exactly. The rest is estimated from 150 size-weighted trades per pool and day, read from receipts. "
          "Arbitrage trades the asset the other way on another pool in the same transaction. Organic users are wallets with fewer than 1,000 transactions trading through a "
          "public router. Other bots are everything else. Daily shares carry up to eight points of sampling error, seven-day shares about three.", chart("c_cpty"), "h_cpty") +
    panel(5, "Counterparty mix, trailing seven days", "Share of the volume the reserve’s liquidity served in each pool over the last seven complete days. Rows sum to 100%.",
          table("t_cpty")) +
    panel(7, "Pool profit and loss against holding, cumulative", "Fees earned plus divergence, the position’s value less the value of holding the deposited tokens, since "
          "each pool was seeded. Position, holding and the fee tokens earned to date are all valued at the same day’s closing pool price.", chart("c_pnl"), "h_pnl") +
    panel(5, "Pool profit and loss since seeding", "Net against holding is fees plus divergence. Net in USD compares value plus fees with the USD cost of the deposits, so it also "
          "carries the move in the assets’ prices. Fees are the tokens earned to date at the last close, including those settled to the Safe. "
          "Hover a row for cost, value and holding.", table("t_pnl")) + '</div>',

"launchpad": kpis("launchpad") + '<div class="grid">' +
    panel(7, "Launchpad fees by recipient, daily", "Every launchpad-token trade, on the bonding curve or in the graduated pool, pays a 1% base fee on its stock or WETH side: "
          "30% to the token’s creator, 20% to the King of the Markets reward pool and 50% to the protocol. The reward pool and protocol shares arrive together in one 2-of-4 "
          "Safe signed by the reserve’s signers and are split here 2:5. Creator receipts include optional hook-module fees. Valued at each day’s closing prices.",
          chart("c_lfee", "l"), "h_lfee") +
    panel(5, "King of the Markets standings", "Season 1 points by team from the launchpad’s markets API. Launchpad-token trades score five points a dollar; stock trades through "
          "reserve markets scored one point a dollar until 21 Oct 13:55 UTC. The reward pool opens with $1.1M from the Standard Reserve, as the protocol’s site states; "
          "the fee Safe holds none of it. 65% is shared by points and 35% goes to the leading team.", table("t_kotm") + '<div class="kv2" id="kotm_pool"></div>', "h_kotm") +
    panel(7, "LP fees from launchpad trades, daily", "Launchpad trades paid in USDG or ETH cross the reserve’s stock pools on the way in and out. Every swap in "
          "the reserve’s pools executed by one of the launchpad’s two routers is counted exactly. Launchpad trades sent through Uniswap’s router or an aggregator are not "
          "identifiable from the pool swap and fall under all other trades, so the launchpad figure is a floor.", chart("c_lroute"), "h_lroute") +
    panel(5, "Launchpad fee Safe holdings", "Balances received by the fee Safe from launchpad trades, valued at current prices. Nothing has left the Safe since the launchpad opened.",
          table("t_fsafe"), "h_fsafe") + '</div>',

"reserve": kpis("reserve") + '<div class="grid">' +
    panel(7, "Reserve assets by component, daily", "ETH and USDG in the reserve Safe, ETH in the policy vaults, tokenized equities held outside pools and the Safe’s Uniswap v4 "
          "positions, at each day’s close. Excludes ETH held by the POL buyback contract and the team wallet, and uncollected position fees.", chart("c_res", "l"), "h_res") +
    panel(5, "Price to backing, daily", "Market cap of the STANDARD in wallets divided by reserve assets. The protocol’s own liquidity and the Incentives vault are left out: "
          "the reserve backs the tokens holders own, not the protocol’s own STANDARD.", chart("c_pb", "l"), "h_pb") +
    panel(12, "Reserve composition, daily change", "Each component today, read at the compile block, against the close one and seven days earlier.", table("t_resd")) + '</div>',

"token": kpis("token") + '<div class="grid">' +
    panel(7, "Price and market capitalization, daily", "GeckoTerminal daily close for the STANDARD/ETH pool. Market cap is price times circulating supply, every STANDARD minted, as the protocol’s "
          "site and DexScreener show it. In wallets leaves out the protocol’s own liquidity and the Incentives vault. Shaded days are contraction epochs.", chart("c_price", "l"), "h_price") +
    panel(5, "Supply reconciliation", "From the genesis mint to circulating supply, the STANDARD in wallets and free float, at one block.", '<div class="bridge" id="bridge"></div>') +
    panel(7, "Net buying of STANDARD by holder group, daily", "STANDARD bought from the protocol’s STANDARD/ETH pool less STANDARD sold into it, by the group of the "
          "wallet behind each trade. Above zero a group bought more than it sold; below zero it sold more. Groups apply in order: team "
          "wallet, bankers, S-Bill holders, wallets with 300 or more pool trades, launch-week buyers, others. A wallet’s group is its standing at the compile, so a "
          "wallet that later becomes a banker moves into Bankers for its whole history; each day’s total does not change.", chart("c_sell"), "h_sell") +
    panel(5, "Largest net sellers, trailing seven days", "Net STANDARD sold into the pool by wallet over the last seven complete days; trades through routers are assigned to the "
          "wallet behind the router.", table("t_sellers")) +
    panel(6, "STANDARD supply composition, daily", "The protocol’s own split of circulating supply: in wallets, protocol liquidity and the Incentives vault, with "
          "the STANDARD in banks, ledger balances owed to bankers and minted only on withdrawal. The full height is every STANDARD that exists or is owed.", chart("c_mc"), "h_mc") +
    panel(6, "STANDARD in wallets, flows by source, daily", "Daily movements into and out of the STANDARD in wallets; the bars sum to the line.", chart("c_flows")) +
    panel(7, "STANDARD/ETH market depth, daily", "ETH, in USD, that sellers receive taking STANDARD’s price down two and five percent, from every open liquidity range at the "
          "day’s closing price. Ask depth is in the tooltip.", chart("c_depth"), "h_depth") +
    panel(5, "STANDARD/ETH execution cost by size", "Each order simulated against the pool’s liquidity at the compile block. Cost adds the 1% pool fee and the hook’s tax.",
          table("t_slip") + '<div class="kv2" id="slip_s"></div>') +
    panel(12, "STANDARD burned by source, daily", "Expansion licenses paid from ledger balances, the burned half of resolution and revocation fees, and buybacks and other token "
          "burns. The line is the cumulative total as a share of the 1 billion hard cap.", chart("c_burn"), "h_burn") + '</div>',

"banks": kpis("banks") + '<div class="grid">' +
    panel(6, "STANDARD in banks, inflows and outflows, daily", "Every movement of the STANDARD held in banks; each day’s bars sum to the change in the line. In: "
          "issuance, which every branch earns automatically, STANDARD bankers deposit from their wallets, and the stayers’ cut, half of every exit and "
          "revocation fee, paid to the bankers who stay. Out: STANDARD spent on expansion licenses, which is burned, STANDARD withdrawn by closing "
          "branches (before the exit fee), and the balances of revoked charters. STANDARD in banks is ledger value, minted only when withdrawn.",
          chart("c_bank"), "h_bank") +
    panel(6, "Branches and active charters, daily", "A charter opens with one branch and licenses add up to nine more. Withdrawals and revocations destroy branches.",
          chart("c_policy"), "h_policy") +
    panel(6, "Charter auction clearing prices", "One charter per 12-hour period in a Dutch auction that opens at three times the last clearing price and halves every two hours "
          "toward a 1 ETH floor. Triangles are purchases made through a contract.", chart("c_charter"), "h_charter") +
    panel(6, "License auction clearing prices and volume", "Twenty-five expansion licenses per 12-hour period, paid in STANDARD and burned, opening at twice the last clearing "
          "price with a floor of about two days of one branch’s issuance.", chart("c_license"), "h_license") +
    panel(6, "S-Bill principal and term rate, daily", "STANDARD locked in 15-day S-Bills and the term rate at each day’s close.", chart("c_sb"), "h_sb") +
    panel(6, "Issuance multiplier and resolution fee, daily", "The multiplier scales daily issuance of 700,000 STANDARD and moves at each epoch settlement within 0.20 to 1.25. "
          "The resolution fee, the exit fee on withdrawals, rises from 2% to 60% with seven-day exit pressure.", chart("c_mult"), "h_mult") +
    panel(12, "Top bankers", "Ranked as the protocol’s own leaderboard ranks, by branches, which set each banker’s share of issuance, then by this epoch’s emissions. Share of "
          "emissions is the banker’s part of everything issued to bankers this epoch. Names are the owners’ primary ENS names on Ethereum mainnet. Rank change compares with "
          "the previous epoch.", table("t_lead") + '<button class="btn" id="lead_more"></button>', "h_lead") + '</div>',

"data": '<div class="grid">' +
    panel(12, "Reconciliation with independent sources", "Each figure the monitor rebuilds from on-chain events, set against an independent reading of the same quantity: "
          "balances read directly at the compile block, the protocol’s own indexer, GeckoTerminal, DexScreener and Coinbase. Gate items stop publication when they fall outside "
          "tolerance, and the previous page stays up. Watched items are published with their gap. Every compile is also checked for figures that disagree across panels, "
          "recomputed totals, freshness, and any figure for a day three or more days old that has moved since the last published page.", table("t_recon"), "h_recon") +
    panel(12, "Open data", "Files published with every compile at the same address, written from the rendered page after it passes the checks, so every figure in them is "
          "the page’s own. Field definitions travel with the JSON.", '<div class="kv2 files" id="files"></div>', "h_files") +
    panel(12, "Daily data log", "One observation per UTC day since genesis, every field reconstructed from protocol events and transfer logs. The current day is partial.",
          table("t_log") + '<div class="btns"><button class="btn" id="more"></button><button class="btn" id="csv">Export CSV</button></div>', "h_log") +
    panel(12, "Epoch settlement ledger", "Net flow is ETH bought less ETH sold through the pool during the epoch; its sign sets the regime. Routed comprises STANDARD trading fees and charter "
          "proceeds.", table("t_epochs")) +
    panel(12, "Supply reconciliation, circulating to in wallets, daily", "STANDARD in wallets equals circulating supply less protocol liquidity less the Incentives vault. Every row ties.",
          table("t_float") + '<div class="btns"><button class="btn" id="fmore"></button></div>') + '</div>',
}

SUB = {"revenue": "Fees and revenue from the token economy, the reserve’s pools and the launchpad.", "liquidity": "The reserve as market maker for stock tokens and ETH.",
       "launchpad": "Fees from tokens launched against reserve markets, and King of the Markets.", "reserve": "The assets behind STANDARD, rebuilt daily from on-chain events.",
       "token": "Price, supply, burns, and who is buying and selling.", "banks": "Bank charters and branches, issuance, the Auction House and S-Bills.", "data": "Every daily observation since genesis, its reconciliation and the open data files."}
def hero(k, n):
    if k == "overview": return '<div class="hero big"><div class="hero-in" id="ov_hero"></div></div>'
    return f'<div class="hero mini"><div class="hero-in"><h1>{n}</h1><p>{SUB[k]}</p></div></div>'
BODY = "".join(f'<section class="tab" id="t-{k}">{hero(k, n)}{SECTIONS[k]}</section>' for k, n in TABS)
NAV = "".join(f'<button data-t="{k}">{n}</button>' for k, n in TABS)

TEMPLATE = r"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<title>Standard Reserve Monitor</title>
<meta name="description" content="Independent on-chain monitor of the Standard Reserve protocol on Robinhood Chain.">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Figtree:wght@400;450;500;600&display=swap">
<style>
/* The Standard Reserve app's dark design system (standardreserve.xyz/liquidity): warm charcoal surfaces, off-white text, glass panels with
   15% white borders, uppercase badges with wide tracking, medal accents (silver US, gold CN, celadon KR, sapphire ETH). Their typeface, KH Teka,
   is licensed to their domain; Figtree is the closest open match. Numbers use tabular figures; addresses use the system mono stack. */
:root{
  --ink:#0d0e0e; --page:#121211; --app:#22221f; --card:#282824; --overlay:#292925; --side:#1b1b19; --sel:#34332c; --hov:#2a2a25;
  --fg:#e8e3d9; --white:#fff; --sec:#aaa79c; --dis:#77776c; --dim:rgb(255 255 255 / 45%);
  --line:rgb(255 255 255 / 10%); --line2:rgb(255 255 255 / 15%); --dash:rgb(255 255 255 / 18%); --bsub:#34342d;
  --gold:#deb553; --gold2:#ffdd8a; --silver:#c9cacd; --celadon:#a8c79a; --sapphire:#8fa2f0; --red:#e5484d; --rose:#e7a3aa; --bronze:#d5c4a5; --violet:#d7cce3;
  --up:#b5c69b; --dn:#e7a3aa;
  --medal-gold:linear-gradient(90deg,#deb553 0%,#ffdd8a 37%,#bc973e 67%,#ab8834 100%);
  --sans:"Figtree",ui-sans-serif,system-ui,-apple-system,"Helvetica Neue",Arial,sans-serif;
  --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
  --ease:cubic-bezier(.4,0,.2,1);
  color-scheme:dark;
}
*{box-sizing:border-box}
html,body{margin:0;background:var(--ink);color:var(--fg)}
body{font-family:var(--sans);font-size:14px;line-height:1.43;font-weight:400;-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;text-rendering:optimizeLegibility;font-variant-numeric:tabular-nums}
a{color:inherit}
/* shell */
.shell{display:flex;min-height:100vh}
.side{position:sticky;top:0;height:100vh;width:15.25rem;flex:0 0 15.25rem;display:flex;flex-direction:column;background:var(--side);border-right:1px solid var(--bsub);z-index:30}
.brand{display:flex;align-items:center;gap:.75rem;height:4.25rem;padding:0 1.25rem;border-bottom:1px solid var(--bsub)}
.brand i{width:5px;height:20px;border-radius:1px;background:var(--medal-gold);display:block}
.brand b{font-weight:500;font-size:.8125rem;letter-spacing:.16em;color:var(--white)}
.brand span{display:block;font-size:.6875rem;letter-spacing:.12em;color:var(--dim);margin-top:2px}
.nav{padding:1.25rem .75rem;display:flex;flex-direction:column;gap:.1875rem;flex:1}
.nlabel{margin:.25rem 0 .5rem;padding:0 .625rem;color:var(--sec);font-size:.6875rem;font-weight:500;letter-spacing:.08em;text-transform:uppercase}
.nlabel.gap{margin-top:1.5rem}
.nav button,.nav a{display:flex;align-items:center;gap:.6875rem;min-height:2.5rem;padding:.5rem .875rem;border:0;border-radius:.25rem;background:transparent;color:var(--sec);font:inherit;font-size:.875rem;text-align:left;cursor:pointer;text-decoration:none;transition:background var(--ease) .15s,color var(--ease) .15s}
.nav button:hover,.nav a:hover{background:rgb(232 227 217 / 5%);color:var(--fg)}
.nav button.on{background:var(--sel);color:var(--fg)}
.nav button i{width:6px;height:6px;border-radius:50%;background:currentColor;opacity:.35;flex:none}
.nav button.on i{opacity:1;background:var(--white)}
.nav a::after{content:"↗";margin-left:auto;font-size:.75rem;color:var(--dis)}
.side-foot{padding:1rem 1.25rem 1.25rem;border-top:1px solid var(--bsub);color:var(--dis);font-size:.75rem;line-height:1.5}
.main{flex:1;min-width:0;display:flex;flex-direction:column;position:relative;overflow-x:clip}
.top{position:sticky;top:0;z-index:20;display:flex;align-items:center;gap:.75rem;height:4.25rem;padding:0 1.5rem;border-bottom:1px solid var(--bsub);background:rgb(18 18 17 / 92%);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px)}
.crumb{color:var(--sec);font-size:.8125rem;white-space:nowrap}
.crumb strong{color:var(--fg);font-weight:500}
.status{margin-left:auto;display:flex;align-items:center;gap:.5rem;min-width:0;overflow:hidden}
.badge{display:inline-flex;align-items:center;gap:.5rem;padding:.5rem .75rem;border:1px solid var(--line);border-radius:.5rem;color:var(--white);font-size:.75rem;line-height:1;text-transform:uppercase;white-space:nowrap;letter-spacing:.02em}
.badge span{color:var(--dim)}
.badge i{width:6px;height:6px;border-radius:50%;background:var(--dim);flex:none}
.badge i.live{background:var(--celadon);box-shadow:0 0 0 0 rgb(168 199 154 / 50%);animation:pulse 2.4s infinite}
.badge.exp i{background:var(--celadon)} .badge.con i{background:var(--red)}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgb(168 199 154 / 45%)}70%{box-shadow:0 0 0 7px rgb(168 199 154 / 0%)}100%{box-shadow:0 0 0 0 rgb(168 199 154 / 0%)}}
.seg{display:flex;gap:.375rem;flex:none}
@media (max-width:1300px){.status .hide{display:none}}
.seg button{display:inline-flex;align-items:center;gap:.5rem;padding:.5rem .75rem;border:1px solid var(--line);border-radius:.5rem;background:rgb(255 255 255 / 1%);color:rgb(255 255 255 / 40%);font:inherit;font-size:.75rem;line-height:1;text-transform:uppercase;cursor:pointer;transition:all .22s var(--ease)}
.seg button:hover{color:var(--white)}
.seg button.on{border-color:var(--white);background:rgb(255 255 255 / 8%);box-shadow:inset 0 0 12px rgb(255 255 255 / 10%);color:var(--white)}
/* page */
.page{position:relative;isolation:isolate;width:min(100%,82rem);margin:0 auto;padding:1.25rem clamp(1rem,3vw,2.5rem) 4rem}
.page::before{content:"";position:absolute;z-index:-1;inset:0 -50vw auto;height:46rem;pointer-events:none;opacity:.3;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='4' height='4'%3E%3Crect width='1' height='1' fill='white'/%3E%3C/svg%3E");
  -webkit-mask-image:linear-gradient(180deg,transparent,#000 6rem,#000 22rem,transparent);mask-image:linear-gradient(180deg,transparent,#000 6rem,#000 22rem,transparent)}
.tab{display:none} .tab.on{display:block;animation:pin .26s cubic-bezier(.25,1,.5,1) both}
@keyframes pin{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}
/* heroes: the reserve dam */
.hero{position:relative;overflow:hidden;border:1px solid var(--line2);border-radius:.75rem;margin-bottom:1rem;background:#1d1b26 url(__HERO__) center 42%/cover no-repeat}
.hero::before{content:"";position:absolute;inset:0;pointer-events:none}
.hero.big::before{background:linear-gradient(180deg,rgb(13 14 14 / 10%) 0%,rgb(13 14 14 / 30%) 32%,rgb(13 14 14 / 72%) 58%,rgb(13 14 14 / 94%) 82%,#0d0e0e 100%)}
.hero.mini{background-position:center 58%}
.hero.mini::before{background:linear-gradient(90deg,rgb(13 14 14 / 92%) 0%,rgb(13 14 14 / 70%) 45%,rgb(13 14 14 / 25%) 100%)}
.hero-in{position:relative;z-index:1}
.hero.mini .hero-in{padding:2.25rem 2rem 2rem}
.hero.mini h1{margin:0;font-size:1.75rem;font-weight:500;letter-spacing:-.035em;color:var(--white);line-height:1.15}
.hero.mini p{margin:.4rem 0 0;color:rgb(255 255 255 / 70%);font-size:.875rem}
.hero.big .hero-in{padding:1.5rem 2rem 1.75rem;color:var(--white)}
.h-top{display:grid;grid-template-columns:1fr auto 1fr;gap:1rem;align-items:center}
.h-top>div:last-child{justify-self:end}
.h-top .badge{background:rgb(13 14 14 / 50%);backdrop-filter:blur(3px)}
.mark{display:flex;gap:.6rem;align-items:center;font-size:.8rem;letter-spacing:.22em;text-transform:uppercase;white-space:nowrap;color:var(--white)}
.mark i{width:1px;height:1.3rem;background:var(--white)}
.h-num{text-align:center;margin-top:9rem}
.h-num strong{display:block;font-size:3.5rem;font-weight:400;line-height:1.2;letter-spacing:-.01em;text-shadow:0 0 4px #fff}
.h-num p{margin:.6rem auto 0;max-width:40rem;color:rgb(255 255 255 / 82%);font-size:1.125rem;line-height:1.45}
.h-num p b{color:var(--white);font-weight:500}
.race{display:flex;gap:4px;margin-top:1.75rem}
.race span{height:3px;min-width:3px;border-radius:2px}
.totals{display:flex;flex-wrap:wrap;gap:.75rem 1rem;align-items:center;justify-content:space-between;margin-top:1rem;font-size:.75rem;text-transform:uppercase}
.totals ol{display:flex;flex-wrap:wrap;gap:.5rem 1.125rem;margin:0;padding:0;list-style:none}
.totals li{display:flex;gap:.375rem;align-items:center} .totals li i{width:6px;height:6px} .totals li span,.totals p span{color:var(--dim)}
.totals p{display:flex;gap:1.25rem;margin:0}
.how{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1.5rem;margin:1.5rem 0 0;padding:1.25rem 0 0;border-top:1px dashed var(--dash);list-style:none}
.how li{color:rgb(255 255 255 / 62%);font-size:.875rem;line-height:1.45}
.how b{display:block;margin-bottom:.25rem;color:var(--fg);font-weight:500}
.how span{white-space:nowrap}
#t_pools th,#t_lead th{white-space:normal;vertical-align:bottom;line-height:1.25;max-width:7rem}
#t_recon td.l{white-space:normal;line-height:1.35;min-width:9rem}
.how strong{display:block;font-size:1.5rem;font-weight:450;letter-spacing:-.02em;color:var(--white);margin:.15rem 0}
/* grid and panels */
.grid{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));gap:1rem}
.col{display:flex;flex-direction:column;gap:1rem;min-width:0}
.w12{grid-column:span 12}.w8{grid-column:span 8}.w7{grid-column:span 7}.w6{grid-column:span 6}.w5{grid-column:span 5}.w4{grid-column:span 4}
.col>.panel{flex:1;display:flex;flex-direction:column} .col>.panel .ch{flex:1;min-height:220px}
.panel{position:relative;min-width:0;padding:1.125rem 1.25rem 1rem;border:1px solid rgb(255 255 255 / 12%);border-radius:.5rem;background:linear-gradient(180deg,rgb(255 255 255 / 5%),rgb(255 255 255 / 1.6%)),#141413}
.ph{display:flex;flex-wrap:wrap;align-items:baseline;gap:.25rem 1rem;padding-right:1.5rem;min-height:1.25rem}
.pt{font-size:.9375rem;font-weight:500;letter-spacing:-.015em;color:var(--white);white-space:nowrap}
.pn{margin-left:auto;color:var(--sec);font-size:.8125rem;white-space:nowrap}
.pn em{font-style:normal;color:var(--white);font-weight:500}
.ph>.i{position:absolute;top:1.15rem;right:1rem}
.i{position:relative;display:inline-flex;align-items:center;justify-content:center;width:15px;height:15px;flex:none;border:1px solid rgb(255 255 255 / 20%);border-radius:50%;color:var(--dim);font:500 9px var(--sans);cursor:help}
.i:hover,.i:focus{color:var(--white);border-color:rgb(255 255 255 / 50%);outline:none}
.i .tip{display:none;position:absolute;top:22px;right:-8px;z-index:60;width:320px;padding:.75rem .875rem;border:1px solid var(--line2);border-radius:.5rem;background:var(--overlay);
  box-shadow:0 8px 28px rgb(0 0 0 / 40%);color:var(--fg);font:400 .8125rem/1.5 var(--sans);text-align:left;text-transform:none;letter-spacing:0;white-space:normal}
.i:hover .tip,.i:focus .tip{display:block}
.ch{position:relative;height:270px;margin-top:.875rem}
.ch.s{height:200px} .ch.l{height:310px}
/* KPI cards, after the leader cards */
.kpis{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1rem;margin-bottom:1rem}
@media (min-width:1640px){.kpis{grid-template-columns:repeat(6,minmax(0,1fr))}}
.kpi{position:relative;display:flex;flex-direction:column;min-width:0;padding:.875rem 1rem 0;border:1px solid rgb(255 255 255 / 12%);border-radius:.5rem;background:linear-gradient(180deg,rgb(255 255 255 / 5%),rgb(255 255 255 / 1.6%)),#141413}
.kl{display:flex;align-items:center;gap:.4rem;color:rgb(255 255 255 / 50%);font-size:.625rem;letter-spacing:.12em;text-transform:uppercase;white-space:nowrap;min-width:0}
.kl span.t{overflow:hidden;text-overflow:ellipsis} .kl .i{margin-left:auto}
.kv{margin-top:.5rem;color:var(--white);font-size:1.5rem;font-weight:450;letter-spacing:-.02em;line-height:1.15;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.kd{margin-top:.3rem;color:var(--sec);font-size:.75rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-height:1rem}
.kd .ks{margin-left:.4rem;color:var(--dis)}
.kpi svg{display:block;width:calc(100% + 2rem);height:28px;margin:.6rem -1rem 0}
.up{color:var(--up)} .dn{color:var(--dn)} .nt{color:var(--sec)} .mut{color:var(--sec)}
/* tables, after the board table */
.tw{overflow-x:auto;margin-top:.75rem}
table{width:100%;border-collapse:collapse;font-size:.8125rem}
th{padding:.5rem .625rem;border-bottom:1px solid var(--line);color:var(--fg);font-weight:500;font-size:.75rem;text-align:right;white-space:nowrap}
td{padding:.5rem .625rem;border-bottom:1px solid rgb(255 255 255 / 6%);color:var(--fg);text-align:right;white-space:nowrap}
th:first-child,td:first-child{text-align:left}
td:first-child{color:var(--sec)}
tr{transition:background .15s} tbody tr:hover td,table tr:hover td{background:var(--hov)}
tr.tot td{color:var(--white);font-weight:500;border-top:1px dashed var(--dash)}
tr.more{display:none} table.open tr.more{display:table-row}
tr.today td{color:var(--white)}
td.l,th.l{text-align:left}
.pos{color:var(--up)} .neg{color:var(--dn)}
.addr{font-family:var(--mono);font-size:.75rem}
table.gm td{padding:.4375rem .625rem}
table.gm td:first-child{color:var(--fg)}
table.gm tr.grp td{padding:1rem .625rem .375rem;border-bottom:1px dashed var(--dash);background:none;color:rgb(255 255 255 / 50%);font-size:.625rem;letter-spacing:.12em;text-transform:uppercase}
table.gm tr.grp:first-child td{padding-top:.25rem}
table.gm td .u{margin-left:.4rem;color:var(--dis);font-size:.75rem}
table.gm td svg{display:block;width:72px;height:20px;margin-left:auto}
table.gm td.c{min-width:80px}
.btn{display:inline-flex;align-items:center;height:2.125rem;margin-top:.875rem;padding:0 .8125rem;border:0;border-radius:.5rem;background:rgb(255 255 255 / 8%);box-shadow:inset 0 0 12px rgb(255 255 255 / 10%);color:var(--white);font:inherit;font-size:.75rem;cursor:pointer}
.btn:hover{background:rgb(255 255 255 / 14%)}
.btns{display:flex;gap:.5rem}
.chip{display:inline-flex;align-items:center;gap:.4rem;padding:.25rem .5rem;border:1px solid var(--line);border-radius:.375rem;font-size:.6875rem;text-transform:uppercase;letter-spacing:.04em;color:var(--fg)}
.chip::before{content:"";width:5px;height:5px;border-radius:50%;background:var(--dim)}
.chip.exp::before{background:var(--celadon)} .chip.con::before{background:var(--red)}
.bridge{display:grid;grid-template-columns:1fr auto;gap:.4rem 1rem;margin-top:.875rem;font-size:.8125rem}
.bridge div:nth-child(odd){color:var(--sec)}
.bridge .tot{color:var(--white);font-weight:500;border-top:1px dashed var(--dash);padding-top:.4rem}
.kv2{display:grid;grid-template-columns:auto 1fr;gap:.35rem 1rem;margin-top:.875rem;font-size:.8125rem}
.kv2 div:nth-child(odd){color:var(--sec)} .kv2 div:nth-child(even){text-align:right;color:var(--fg)}
.kv2.files div:nth-child(even){text-align:left;color:var(--sec)} .kv2.files a{color:var(--fg);text-decoration:none;font-family:var(--mono);font-size:.75rem} .kv2.files a:hover{color:var(--white)}
.alloc .abar{display:flex;gap:3px;height:6px;margin-top:1.25rem} .alloc .abar>div{height:100%;border-radius:2px}
.alloc .lg{display:grid;grid-template-columns:auto 1fr auto auto;gap:.6rem .75rem;margin-top:1.25rem;font-size:.8125rem;align-items:center}
.alloc .lg i{width:6px;height:6px;display:inline-block}
.alloc .lg .v{text-align:right;color:var(--white)} .alloc .lg .p{text-align:right;color:var(--sec);min-width:2.5rem}
.foot{margin-top:2.5rem;padding-top:1rem;border-top:1px dashed var(--dash);color:var(--dis);font-size:.75rem;line-height:1.6}
@media (max-width:1360px){.w8,.w7,.w5,.w4{grid-column:span 12}}
@media (max-width:980px){
  .shell{flex-direction:column} .side{position:sticky;top:0;height:auto;width:100%;flex:none;border-right:0;border-bottom:1px solid var(--bsub)}
  .brand{height:3.25rem;border-bottom:0} .nlabel,.side-foot,.nav a{display:none}
  .nav{flex-direction:row;overflow-x:auto;padding:0 .75rem .625rem;scrollbar-width:none;gap:.25rem} .nav::-webkit-scrollbar{display:none}
  .nav button{min-height:2.125rem;padding:.375rem .75rem;white-space:nowrap} .nav button i{display:none}
  .top{position:static;height:auto;padding:.75rem 1rem;flex-wrap:wrap} .crumb{display:none} .status{margin-left:0;flex-wrap:wrap} .w6{grid-column:span 12}
}
@media (max-width:640px){
  .page{padding:.75rem .75rem 3rem} .kpis{grid-template-columns:repeat(2,minmax(0,1fr));gap:.625rem} .grid{gap:.75rem}
  .kv{font-size:1.25rem} .panel{padding:.875rem .875rem .75rem} .ch,.ch.l{height:280px} .ch.s{height:220px}
  .pt{white-space:normal} .ph{flex-wrap:wrap;gap:.125rem .75rem} .pn{margin-left:0;width:100%;white-space:normal}
  .i .tip{width:calc(100vw - 3rem);right:-.5rem}
  .tw table th:first-child,.tw table td:first-child{position:sticky;left:0;background:#1a1a18;z-index:1}
  table.gm td:nth-child(3),table.gm th:nth-child(3),table.gm td:nth-child(5),table.gm th:nth-child(5){display:none}
  table.gm td:first-child{white-space:normal}
  .kl{white-space:normal;align-items:flex-start;line-height:1.3} .kd{white-space:normal}
  .hero.big .hero-in{padding:1rem} .h-top{grid-template-columns:1fr} .h-top>div:last-child{justify-self:start} .mark{grid-row:1;font-size:.6875rem;letter-spacing:.16em}
  .h-num{margin-top:4.5rem} .h-num strong{font-size:2.25rem} .h-num p{font-size:.9375rem} .how{grid-template-columns:1fr;gap:1rem}
  .hero.mini .hero-in{padding:1.5rem 1rem 1.25rem} .hero.mini h1{font-size:1.4rem}
  .badge{padding:.4rem .55rem;font-size:.6875rem}
}
</style>
</head><body>
<div class="shell">
  <aside class="side">
    <div class="brand"><i></i><div><b>STANDARD RESERVE</b><span>MONITOR</span></div></div>
    <nav class="nav" id="tabs">__NAV__<div class="nlabel gap">Information</div>
      <a href="https://www.standardreserve.xyz/" target="_blank" rel="noopener">Standard Reserve</a>
      <a href="https://github.com/standardrsvmonitor/standardrsvmonitor.github.io" target="_blank" rel="noopener">Source and methods</a></nav>
    <div class="side-foot">Independent on-chain monitor.<br>Compiled __ASOF__ UTC.</div>
  </aside>
  <div class="main">
    <header class="top"><div class="crumb">Monitor&nbsp;&nbsp;/&nbsp;&nbsp;<strong id="crumb">Overview</strong></div>
      <div class="status" id="status"></div>
      <div class="seg" id="range"><button data-n="7">7D</button><button data-n="30" class="on">30D</button><button data-n="0">All</button></div></header>
    <main class="page">__BODY__
      <div class="foot">Standard Reserve Monitor, an independent monitor compiled __ASOF__ UTC from the Standard Reserve indexer and markets API, the Robinhood Chain RPC,
      DexScreener, GeckoTerminal and Coinbase. Figures are reconstructed from on-chain events; each ⓘ gives the method. Artwork: Standard Reserve.</div></main>
  </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<script>
const DATA = __DATA__;
const L = DATA.live, S = DATA.series, E = DATA.epochs, LPD = DATA.launchpad || {};
const C = {gold:'#deb553', gold2:'#ffdd8a', silver:'#c9cacd', celadon:'#a8c79a', sapphire:'#8fa2f0', red:'#e5484d', rose:'#e7a3aa', bronze:'#d5c4a5', violet:'#d7cce3',
  sand:'#aaa79c', grey:'#77776c', fg:'#e8e3d9', up:'#b5c69b', dn:'#e7a3aa',
  blue:'#8fa2f0', teal:'#a8c79a', green:'#b5c69b', orange:'#d5c4a5', pink:'#e7a3aa', muted:'#aaa79c', fg2:'#e8e3d9'};   // aliases keep older series names on the same palette
const PCOL = {SPCX:'#c9cacd', SKHY:'#a8c79a', BABA:'#deb553', ETH:'#8fa2f0'};   // the site's own team colours: US silver, KR celadon, CN gold, ETH sapphire
const STREAM = {tr:C.gold, pool:C.celadon, lpad:C.sapphire, ch:C.silver};
const alpha = (h,a)=>{const n=parseInt(h.slice(1),16); return `rgba(${n>>16},${(n>>8)&255},${n&255},${a})`;};
const fmt = {
  usd:(v,d)=>{if(v==null||isNaN(v))return '–';const s=v<0?'−':'';v=Math.abs(v);return s+(v>=1e9?'$'+(v/1e9).toFixed(d==null?2:d)+'B':v>=1e6?'$'+(v/1e6).toFixed(d==null?2:d)+'M':v>=1e3?'$'+(v/1e3).toFixed(d==null?1:d)+'K':'$'+v.toFixed(d==null?2:d));},
  n:(v,d)=>{if(v==null||isNaN(v))return '–';const s=v<0?'−':'';v=Math.abs(v);return s+(v>=1e6?(v/1e6).toFixed(d==null?2:d)+'M':v>=1e3?(v/1e3).toFixed(d==null?1:d)+'K':v.toFixed(d==null?0:d));},
  pct:(v,d)=>v==null||isNaN(v)?'–':(v<0?'−':'')+(Math.abs(v)*100).toFixed(d==null?1:d)+'%',
  sx:(v,d)=>v==null||isNaN(v)?'–':(v>0?'+':v<0?'−':'')+Math.abs(v).toFixed(d==null?1:d),
  eth:(v,d)=>v==null?'–':v.toFixed(d==null?1:d)+' ETH',
  dt:(ts)=>new Date(ts*1000).toISOString().slice(0,10),
  hm:(ts)=>new Date(ts*1000).toISOString().slice(11,16),
  sgn:(v)=>v>0?'+':'',
  int:(v)=>v==null||isNaN(v)?'–':Math.round(v).toLocaleString('en-US'),
  px:(v)=>v==null?'–':'$'+v.toFixed(4),
  x:(v,d)=>v==null||!isFinite(v)?'–':v.toFixed(d==null?2:d)+'×',
};
const pxf = (v)=>v==null?'–':'$'+v.toLocaleString('en-US',{minimumFractionDigits:2, maximumFractionDigits:2});
const dm = (d)=>new Date(d+'T00:00:00Z').toLocaleDateString('en-GB',{day:'numeric',month:'short',timeZone:'UTC'});
const MOBILE = window.matchMedia('(max-width:640px)').matches;
if (window.Chart) {
  const D = Chart.defaults;
  D.color = 'rgba(255,255,255,.42)'; D.font.family = getComputedStyle(document.documentElement).getPropertyValue('--sans'); D.font.size = 11; D.borderColor = 'rgba(255,255,255,.06)';
  D.plugins.legend.position = 'bottom'; D.plugins.legend.align = 'center';
  Object.assign(D.plugins.legend.labels, {boxWidth:6, boxHeight:6, padding:MOBILE?10:16, color:C.sand}); D.plugins.legend.labels.font = {size:11.5};
  D.layout.padding = {top:4, bottom:0};
  D.interaction = {mode:'index', intersect:false}; D.plugins.tooltip.mode = 'index'; D.plugins.tooltip.intersect = false;
  D.plugins.tooltip.backgroundColor = '#292925'; D.plugins.tooltip.borderColor = 'rgba(255,255,255,.15)'; D.plugins.tooltip.borderWidth = 1; D.plugins.tooltip.padding = 12; D.plugins.tooltip.cornerRadius = 8;
  D.plugins.tooltip.titleColor = '#ffffff'; D.plugins.tooltip.bodyColor = '#e8e3d9'; D.plugins.tooltip.footerColor = '#aaa79c'; D.plugins.tooltip.boxWidth = 6; D.plugins.tooltip.boxHeight = 6; D.plugins.tooltip.bodySpacing = 5;
  D.plugins.tooltip.titleFont = {weight:'500', size:12}; D.plugins.tooltip.bodyFont = {size:12}; D.plugins.tooltip.footerFont = {weight:'400', size:11.5};
  D.elements.point.radius = 0; D.elements.point.hitRadius = 10; D.elements.line.borderWidth = 1.5; D.elements.line.tension = .3; D.elements.line.cubicInterpolationMode = 'monotone';
  D.elements.bar.borderRadius = 2; D.datasets.bar.maxBarThickness = 20; D.datasets.bar.categoryPercentage = .72; D.animation = false;
  D.scale.ticks.maxTicksLimit = MOBILE ? 5 : 8; D.scale.border.display = false;
}
const last = (arr,n)=>n?arr.slice(Math.max(0,arr.length-n)):arr;
const sum = (a)=>a.reduce((x,y)=>x+(y||0),0);
const ethOf = (r)=>r.eth||L.ethusd;
// revenue streams
const tr = (r)=>(r.tradingFeeEth||0)*ethOf(r), chs = (r)=>(r.charterEth||0)*ethOf(r);
const lpp = (r)=>(r.lpadSafe||0)*5/7, lpot = (r)=>(r.lpadSafe||0)*2/7, lcr = (r)=>r.lpadEsc||0;   // launchpad base fee: protocol 50%, reward pool 20% (both into the fee Safe), creators 30% plus module fees
const lvol = (r)=>(r.lpadSafe||0)/0.007;                                                              // launchpad trading volume implied by the 0.7% the fee Safe receives
const rec = (r)=>tr(r)+(r.spFee||0)+lpp(r);                                                        // trading fees, LP fees and the launchpad's 50%; inc adds charter sales, which is revenue
const inc = (r)=>rec(r)+chs(r);
const burnLedger = (r)=>(r.licBurn||0)+(r.exitFeeBurn||0)+(r.revokeFeeBurn||0), burnTokens = (r)=>(r.burnBuyback||0)+(r.burnOther||0), burnAll = (r)=>burnLedger(r)+burnTokens(r);
const pbOf = (r)=>r&&r.reserveUsd&&r.mcFloat ? r.mcFloat/r.reserveUsd : null;
const bkOf = (r)=>r&&r.reserveUsd&&r.float ? r.reserveUsd/r.float : null;
const served = (r)=>r.spVolMine!=null?r.spVolMine:(r.spVol||0);
const GROUPS = [['team','Team wallet',C.rose],['bankers','Bankers',C.gold],['sbills','S-Bill holders',C.celadon],['active','High-frequency wallets and bots',C.sapphire],['launch','Launch-week buyers',C.silver],['other','Other wallets',C.grey]];
const Sh = S.filter(r=>r.date<=L.date);
const ep2 = E.length>1 ? fmt.dt(E[1].start) : '';
const Sp = Sh.filter(r=>r.date<L.date);
const s7 = last(Sp,7), P7 = Sp.length>=14 ? Sp.slice(-14,-7) : [];
const Y = Sp[Sp.length-1]||{}, yd = Y.date ? dm(Y.date) : '';
const regime = {};
const isExp = (e)=>e.expansion===true||e.expansion==='true'||e.expansion===1;
E.forEach(e=>{for(let t=e.start+3600;t<e.end;t+=86400) regime[fmt.dt(t)] = isExp(e);});
for(let t=L.epochStart+3600;t<L.epochEnd;t+=86400) regime[fmt.dt(t)] = L.epochNetFlow>=0;
const bands = {id:'bands', beforeDatasetsDraw(ch){const o=(ch.options.plugins||{}).bands; if(!o||!o.dates||!o.dates.length) return; const x=ch.scales.x, a=ch.chartArea, ctx=ch.ctx;
  const w = o.dates.length>1 ? x.getPixelForValue(1)-x.getPixelForValue(0) : a.width; ctx.save();
  o.dates.forEach((d,i)=>{if(regime[d]===false){ ctx.fillStyle='rgba(229,72,77,.05)'; ctx.fillRect(x.getPixelForValue(i)-w/2, a.top, w, a.height);} }); ctx.restore();}};
if (window.Chart) Chart.register(bands);
const winEnd = (r,n)=>{const i=Sp.indexOf(r); return i>=n-1 ? Sp.slice(i-n+1,i+1) : null;};
const revRoll = (r)=>{const w=winEnd(r,7); return w && w[0].date>=ep2 ? sum(w.map(inc)) : null;};
const prrOf = (r)=>{const v=revRoll(r); return v && r.mcTotal ? r.mcTotal/(v*365/7) : null;};   // price to revenue: market cap on circulating supply over annualized seven-day revenue
let NOWTS = DATA.pulledAt, LIVE = false;
let mcFloat, mcTotal, epLeft, backing, perBranch, pbNow, capRemoved, W0;
const derive = ()=>{ mcFloat = L.price*L.float; mcTotal = L.price*L.totalSupply; epLeft = Math.max(0, L.epochEnd - NOWTS);
  backing = L.reserve.totalUsd/L.float; perBranch = L.baseIssuance*L.multiplier/L.branches; pbNow = mcFloat/L.reserve.totalUsd; capRemoved = 1e9-L.maxSupply;
  W0 = Sh.length>7 ? Sh[Sh.length-8] : null; };
derive();
const pools = Object.keys(L.lp), stockPools = pools.filter(p=>!L.lp[p].isEth);
const shortP = p=>p==='ETH'?'ETH/USDG':p, pname = (s)=>s==='ETH'?'ETH/USDG pool':s+' pool';
const ck = (r,k,ps)=>sum((ps||pools).map(p=>r[`vol${k}_${p}`]||0));
const CPK = ['Org','Arb','Bot','Fx'];
const cpShares = (rows, ps)=>{const v=CPK.map(k=>sum(rows.map(r=>ck(r,k,ps)))), t=sum(v); if(!t) return null;   // largest remainder, so the four shares sum to exactly 100
  const raw=v.map(x=>x/t*100), fl=raw.map(Math.floor), left=100-sum(fl); raw.map((x,i)=>[x-fl[i],i]).sort((a,b)=>b[0]-a[0]).slice(0,left).forEach(([,i])=>fl[i]++);
  return Object.fromEntries(CPK.map((k,i)=>[k, fl[i]]));};

// ---------- sparklines and change cells ----------
const spark = (vals, color, fill)=>{const w=300, h=40, p=2, xs=vals.filter(v=>v!=null&&isFinite(v)); if(xs.length<2) return '<svg></svg>';
  let lo=Math.min(...xs), hi=Math.max(...xs); if(hi===lo){hi+=1; lo-=1;}
  const n=vals.length, X=i=>p+(w-2*p)*(n>1?i/(n-1):.5), Yp=y=>h-p-(h-2*p)*(y-lo)/(hi-lo);
  const pts=vals.map((y,i)=>y==null||!isFinite(y)?null:[X(i),Yp(y)]).filter(Boolean);
  const d='M'+pts.map(q=>q[0].toFixed(1)+','+q[1].toFixed(1)).join('L');
  const area = fill ? `<path d="${d}L${pts[pts.length-1][0].toFixed(1)},${h}L${pts[0][0].toFixed(1)},${h}Z" fill="${alpha(color,.10)}"/>` : '';
  return `<svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none">${area}<path d="${d}" fill="none" stroke="${color}" stroke-width="1.5" vector-effect="non-scaling-stroke"/></svg>`;};
const tone = (dlt, pol)=>dlt==null||!isFinite(dlt)||Math.abs(dlt)<1e-9||!pol ? 'nt' : (dlt*pol>0?'up':'dn');
const chg = (cur, prev, o={})=>{ if(cur==null||prev==null||!isFinite(cur)||!isFinite(prev)) return {t:'–', c:'nt', v:null};
  if (o.pp) { const d=(cur-prev)*100; return {t:`${d>=0?'▲':'▼'} ${Math.abs(d).toFixed(1)} pp`, c:tone(d,o.pol), v:d}; }
  if (o.abs || prev===0 || (prev<0)!==(cur<0)) { const d=cur-prev; return {t:`${d>=0?'▲':'▼'} ${o.f?o.f(Math.abs(d)):fmt.n(Math.abs(d),1)}`, c:tone(d,o.pol), v:d}; }
  const d=cur/prev-1; return {t:`${d>=0?'▲':'▼'} ${Math.abs(d*100)>=100?Math.round(Math.abs(d*100)).toLocaleString('en-US'):(Math.abs(d)*100).toFixed(1)}%`, c:tone(d,o.pol), v:d}; };
const roll7 = (f, n=30)=>{const R=last(Sp, n+6); return R.map((r,i)=> i>=6 ? sum(R.slice(i-6,i+1).map(f)) : null).slice(-n);};
const rollRatio = (nf, df, n=30)=>{const R=last(Sp, n+6); return R.map((r,i)=>{ if(i<6) return null; const w=R.slice(i-6,i+1), d=sum(w.map(df)); return d?sum(w.map(nf))/d:null;}).slice(-n);};

// ---------- KPI tiles ----------
const tile = (k)=>{const c = k.c || {t:'',c:'nt'};
  return `<div class="kpi"><div class="kl"><span class="t">${k.l}</span>${k.tip?`<span class="i" tabindex="0">i<span class="tip">${k.tip}</span></span>`:''}</div><div class="kv">${k.v}</div>`+
    `<div class="kd"><span class="${c.c}">${c.t}</span><span class="ks">${k.s||''}</span></div>${spark(k.sp||[], k.col||C.gold, true)}</div>`;};
const lvl = (f)=>last(Sh,30).map(f);
function renderKpis(){ derive();
  const rev7 = sum(s7.map(inc)), revP = P7.length?sum(P7.map(inc)):null;
  const lv7 = sum(s7.map(lvol)), lvP = P7.length?sum(P7.map(lvol)):null, lf7 = sum(s7.map(r=>(r.lpadSafe||0)+(r.lpadEsc||0))), lfP = P7.length?sum(P7.map(r=>(r.lpadSafe||0)+(r.lpadEsc||0))):null;
  const pf7 = sum(s7.map(r=>r.spFee||0)), pfP = P7.length?sum(P7.map(r=>r.spFee||0)):null;
  const poolLiq = sum(pools.map(p=>L.lp[p].valueUSD));
  const eqShare = (rows)=>{const d=sum(rows.map(r=>sum(stockPools.map(p=>r['chainVol_'+p]||0)))); return d?sum(rows.map(r=>sum(stockPools.map(p=>r['spVolMine_'+p]??r['spVol_'+p]??0))))/d:null;};
  const orgS = (rows)=>{const t=sum(rows.map(r=>sum(CPK.map(k=>ck(r,k))))); return t?sum(rows.map(r=>ck(r,'Org')))/t:null;};
  const zf = (rows)=>{const t=sum(rows.map(served)); return t?1-sum(rows.map(r=>r.spVolZeroFee||0))/t:null;};
  const K = {
    overview:[
      {l:'STANDARD price', v:fmt.px(L.price), c:chg(L.price, W0&&W0.price, {pol:1}), s:'7d', sp:lvl(r=>r.price), tip:'Live price from DexScreener for the STANDARD/ETH pool; history uses GeckoTerminal daily closes.'},
      {l:'Market cap', v:fmt.usd(mcTotal), c:chg(mcTotal, W0&&W0.mcTotal, {pol:1}), s:`in wallets ${fmt.usd(mcFloat)}`, sp:lvl(r=>r.mcTotal), tip:'Price times circulating supply, every STANDARD minted, the figure the protocol’s site and DexScreener show. In wallets leaves out the protocol’s own liquidity and the Incentives vault.'},
      {l:'Reserve assets', v:fmt.usd(L.reserve.totalUsd), c:chg(L.reserve.totalUsd, W0&&W0.reserveUsd, {pol:1}), s:`${fmt.x(pbNow)} P/B`, sp:lvl(r=>r.reserveUsd), col:C.blue, tip:'ETH and USDG in the reserve Safe, ETH in the policy vaults, equities held outside pools and the Safe’s Uniswap v4 positions, read at the compile block.'},
      {l:'Revenue, 7d', v:fmt.usd(rev7), c:chg(rev7, revP, {pol:1}), s:'vs prior 7d', sp:roll7(inc), col:C.gold, tip:`What the protocol kept over the seven complete days to ${yd}: STANDARD trading fees, LP fees, the launchpad’s 50% and charter sales.`},
      {l:'Branches', v:fmt.int(L.branches), c:chg(L.branches, W0&&W0.branches, {pol:1}), s:`${fmt.int(L.activeCharters)} charters`, sp:lvl(r=>r.branches), col:C.violet, tip:'Branches open now, from the indexer census.'},
      {l:`Epoch ${L.epoch} net flow`, v:fmt.sx(L.epochNetFlow,1)+' ETH', c:{t:`${L.epochNetFlow>=0?'expansion':'contraction'}`, c:L.epochNetFlow>=0?'up':'dn'}, s:`${Math.floor(epLeft/86400)}d ${Math.floor(epLeft%86400/3600)}h left`,
        sp:E.slice(-12).map(e=>e.netFlow), col:L.epochNetFlow>=0?C.green:C.red, tip:`ETH bought less ETH sold through the STANDARD/ETH pool this epoch; its sign at settlement sets the regime. Multiplier ${fmt.x(L.multiplier)}. The line shows settled epochs.`},
    ],
    revenue:[
      {l:'Revenue, 7d', v:fmt.usd(rev7), c:chg(rev7, revP, {pol:1}), s:'vs prior 7d', sp:roll7(inc), col:C.teal},
      {l:'STANDARD trading fees, 7d', v:fmt.usd(sum(s7.map(tr))), c:chg(sum(s7.map(tr)), P7.length?sum(P7.map(tr)):null, {pol:1}), sp:roll7(tr), col:STREAM.tr},
      {l:'LP fees, 7d', v:fmt.usd(pf7), c:chg(pf7, pfP, {pol:1}), sp:roll7(r=>r.spFee||0), col:STREAM.pool},
      {l:'Launchpad revenue, 7d', v:fmt.usd(sum(s7.map(lpp))), c:chg(sum(s7.map(lpp)), P7.length?sum(P7.map(lpp)):null, {pol:1}), s:'protocol 50%', sp:roll7(lpp), col:STREAM.lpad, tip:'The protocol’s 50% of the 1% launchpad base fee, held in the launchpad fee Safe.'},
      {l:'Charter sales, 7d', v:fmt.usd(sum(s7.map(chs))), c:chg(sum(s7.map(chs)), P7.length?sum(P7.map(chs)):null, {pol:1}), sp:roll7(chs), col:STREAM.ch},
      {l:'Price to revenue', v:fmt.x(prrOf(Y),1), c:chg(prrOf(Y), Sp.length>7?prrOf(Sp[Sp.length-8]):null, {pol:-1, abs:true, f:v=>v.toFixed(1)+'×'}), s:yd, sp:last(Sp,30).map(prrOf), col:C.fg2},
    ],
    liquidity:[
      {l:'Capital in pools', v:fmt.usd(poolLiq), c:{t:fmt.pct(poolLiq/L.reserve.totalUsd,0)+' of reserve', c:'nt'}, sp:lvl(r=>{const q=(r.reserveParts||{}).lp; return q?sum(Object.values(q)):null;}), col:C.blue},
      {l:'LP fees, 7d', v:fmt.usd(pf7), c:chg(pf7, pfP, {pol:1}), sp:roll7(r=>r.spFee||0), col:C.blue},
      {l:'LP fee APR', v:fmt.pct(poolLiq?pf7*365/7/poolLiq:null,0), c:{t:'on capital in pools', c:'nt'}, sp:roll7(r=>r.spFee||0), col:C.blue},
      {l:'Volume served, 7d', v:fmt.usd(sum(s7.map(served))), c:chg(sum(s7.map(served)), P7.length?sum(P7.map(served)):null, {pol:1}), sp:roll7(served), col:C.blue},
      {l:'Share of chain equity volume', v:fmt.pct(eqShare(s7),0), c:chg(eqShare(s7), P7.length?eqShare(P7):null, {pp:true, pol:1}), s:'7d', sp:rollRatio(r=>sum(stockPools.map(p=>r['spVolMine_'+p]??r['spVol_'+p]??0)), r=>sum(stockPools.map(p=>r['chainVol_'+p]||0))), col:C.teal},
      {l:'Organic share of volume', v:(cpShares(s7)||{}).Org!=null?cpShares(s7).Org+'%':'–', c:chg(orgS(s7), P7.length?orgS(P7):null, {pp:true, pol:1}), s:`fee-paying ${fmt.pct(zf(s7),0)}`, sp:rollRatio(r=>ck(r,'Org'), r=>sum(CPK.map(k=>ck(r,k)))), col:C.green},
    ],
    launchpad:[
      {l:'Launchpad volume, 7d', v:fmt.usd(lv7), c:chg(lv7, lvP, {pol:1}), s:'implied by fees', sp:roll7(lvol), col:C.teal, tip:'Trading volume implied by the 0.7% of every launchpad trade that reaches the fee Safe.'},
      {l:'Launchpad fees, 7d', v:fmt.usd(lf7), c:chg(lf7, lfP, {pol:1}), s:'all recipients', sp:roll7(r=>(r.lpadSafe||0)+(r.lpadEsc||0)), col:C.teal},
      {l:'Launchpad revenue, 7d', v:fmt.usd(sum(s7.map(lpp))), c:chg(sum(s7.map(lpp)), P7.length?sum(P7.map(lpp)):null, {pol:1}), s:'50% of base fee', sp:roll7(lpp), col:C.teal},
      {l:'Launchpad revenue, to date', v:fmt.usd(sum(Sh.map(lpp))), c:{t:`of ${fmt.usd(sum(Sh.map(r=>(r.lpadSafe||0)+(r.lpadEsc||0))))} fees`, c:'nt'}, sp:(()=>{let c=0; return last(Sh.map(r=>c+=lpp(r)),30);})(), col:C.teal},
      {l:'Reward pool', v:fmt.usd((LPD.seedUsd||0)+sum(Sh.map(lpot))), c:{t:`${fmt.usd(sum(Sh.map(lpot)))} from fees`, c:'nt'}, s:`seed ${fmt.usd(LPD.seedUsd||0,1)}`, sp:(()=>{let c=LPD.seedUsd||0; return last(Sh.map(r=>c+=lpot(r)),30);})(), col:C.gold,
        tip:'The $1.1M opening pot the protocol’s site attributes to the Standard Reserve, plus 20% of every base fee. The fee Safe holds only the fee part.'},
      {l:'Season 1 closes', v:LPD.season?dm(fmt.dt(LPD.season.endsAt)):'–', c:{t:LPD.season?`${Math.max(0,Math.floor((LPD.season.endsAt-NOWTS)/86400))}d ${Math.max(0,Math.floor((LPD.season.endsAt-NOWTS)%86400/3600))}h left`:'', c:'nt'}, s:LPD.season?fmt.hm(LPD.season.endsAt)+' UTC':'', sp:[], col:C.gold},
    ],
    reserve:[
      {l:'Reserve assets', v:fmt.usd(L.reserve.totalUsd), c:chg(L.reserve.totalUsd, W0&&W0.reserveUsd, {pol:1}), s:'7d', sp:lvl(r=>r.reserveUsd), col:C.blue},
      {l:'Backing per token', v:'$'+backing.toFixed(4), c:chg(backing, bkOf(W0), {pol:1}), s:'per STANDARD in wallets', sp:lvl(bkOf), col:C.blue},
      {l:'Price to backing', v:fmt.x(pbNow), c:chg(pbNow, pbOf(W0), {abs:true, f:v=>v.toFixed(2)+'×'}), s:'7d', sp:lvl(pbOf), col:C.fg2},
      {l:'In pools', v:fmt.usd(L.reserve.lpUsd), c:{t:fmt.pct(L.reserve.lpUsd/L.reserve.totalUsd,0)+' of reserve', c:'nt'}, sp:lvl(r=>{const q=(r.reserveParts||{}).lp; return q?sum(Object.values(q)):null;}), col:C.blue},
      {l:'USDG', v:fmt.usd(L.reserve.safeUsdg), c:{t:fmt.pct(L.reserve.safeUsdg/L.reserve.totalUsd,0)+' of reserve', c:'nt'}, sp:lvl(r=>(r.reserveParts||{}).usdg), col:C.teal},
      {l:'ETH, Safe and vaults', v:fmt.usd((L.reserve.safeEth+L.reserve.contractionEth+L.reserve.expansionEth)*L.ethusd), c:{t:fmt.eth(L.reserve.safeEth+L.reserve.contractionEth+L.reserve.expansionEth,0), c:'nt'}, sp:lvl(r=>(r.reserveParts||{}).eth), col:C.violet},
    ],
    token:[
      {l:'STANDARD price', v:fmt.px(L.price), c:chg(L.price, W0&&W0.price, {pol:1}), s:L.priceChange24h!=null?`${fmt.sx(L.priceChange24h,1)}% 24h`:'7d', sp:lvl(r=>r.price)},
      {l:'Market cap', v:fmt.usd(mcTotal), c:chg(mcTotal, W0&&W0.mcTotal, {pol:1}), s:'circulating supply', sp:lvl(r=>r.mcTotal)},
      {l:'Market cap, in wallets', v:fmt.usd(mcFloat), c:chg(mcFloat, W0&&W0.mcFloat, {pol:1}), s:'7d', sp:lvl(r=>r.mcFloat)},
      {l:'In wallets', v:fmt.n(L.float,2), c:chg(L.float, W0&&W0.float, {}), s:'7d', sp:lvl(r=>r.float), col:C.fg2},
      {l:'Free float', v:fmt.n(L.float-L.sbillsStd-L.teamStd,2), c:{t:'ex S-Bills and team', c:'nt'}, sp:lvl(r=>r.float!=null&&r.sbills!=null&&r.teamStd!=null?r.float-r.sbills-r.teamStd:null), col:C.fg2},
      {l:'Burned', v:fmt.n(capRemoved,2), c:{t:fmt.pct(capRemoved/1e9,1)+' of the 1B cap', c:'nt'}, sp:(()=>{let c=0; return last(Sp.map(r=>c+=burnAll(r)),30);})(), col:C.orange,
        tip:'The protocol’s own figure: the 1 billion hard cap less the current maximum supply. Token burns plus ledger removals that are never minted.'},
    ],
    banks:[
      {l:'Branches', v:fmt.int(L.branches), c:chg(L.branches, W0&&W0.branches, {pol:1}), s:'7d', sp:lvl(r=>r.branches), col:C.violet},
      {l:'Active charters', v:fmt.int(L.activeCharters), c:chg(L.activeCharters, W0&&W0.activeCharters, {pol:1}), s:'7d', sp:lvl(r=>r.activeCharters), col:C.violet},
      {l:'Issuance multiplier', v:fmt.x(L.multiplier), c:{t:`${fmt.n(L.baseIssuance*L.multiplier,0)} a day`, c:'nt'}, s:`${perBranch.toFixed(1)} per branch`, sp:lvl(r=>r.multiplier), col:C.gold},
      {l:'In banks', v:fmt.n(L.pending,2), c:chg(L.pending, W0&&W0.pending, {}), s:'ledger balance, unminted', sp:lvl(r=>r.pending), col:C.fg2},
      {l:'Resolution fee', v:fmt.pct(L.exitFeeNow,1), c:{t:`stayers’ cut ${fmt.pct(L.exitFeeNow/2,1)}`, c:'nt'}, s:`${Math.round((L.exitPressure7d||0)/0.10*100)}% of threshold`, sp:lvl(r=>r.exitFee), col:C.orange,
        tip:'The exit fee on withdrawals, 2% at rest rising to 60% as seven-day withdrawals approach the 10% threshold. Half is burned and half goes to the bankers who stay, the protocol’s “stayers’ cut”.'},
      {l:'S-Bills locked', v:fmt.n(L.sbills.locked,2), c:chg(L.sbills.locked, W0&&(W0.sbLocked??W0.sbills), {pol:1}), s:`${(L.sbills.rate*100).toFixed(2)}% per term`, sp:lvl(r=>r.sbLocked??r.sbills), col:C.teal},
    ],
  };
  Object.entries(K).forEach(([t,ks])=>{const el=document.getElementById('k_'+t); if(el) el.innerHTML = ks.map(tile).join('');});
  renderStatus(); renderGM();
}
function renderStatus(){
  const reg_ = L.epochNetFlow>=0 ? 'exp' : 'con', left = `${Math.floor(epLeft/86400)}d ${Math.floor(epLeft%86400/3600)}h`;
  document.getElementById('status').innerHTML =
    `<span class="badge"><i class="${LIVE?'live':''}"></i>${LIVE?'Live':'Compiled'} <span>${LIVE?LIVEHM:'__ASOFHM__'} UTC</span></span>`+
    `<span class="badge ${reg_} hide"><i></i><span>Epoch ${L.epoch}</span> ${reg_==='exp'?'Expansion':'Contraction'} · ${left}</span>`+
    `<span class="badge hide"><span>STANDARD</span> ${fmt.px(L.price)}</span>`;
  renderHero();
}
const MEDAL = {SPCX:'linear-gradient(90deg,#ebecef 0%,#c9cacd 50%,#83868c 100%)', SKHY:'linear-gradient(90deg,#d6ecc9 0%,#a8c79a 50%,#5f7a55 100%)',
  BABA:'linear-gradient(90deg,#deb553 0%,#ffdd8a 37%,#bc973e 67%,#ab8834 100%)', ETH:'linear-gradient(90deg,#c9d3fa 0%,#8fa2f0 50%,#4a5fb8 100%)'};
function renderHero(){
  const el = document.getElementById('ov_hero'); if (!el) return;
  const R_ = L.reserve, ethU = (R_.safeEth+R_.contractionEth+R_.expansionEth)*L.ethusd;
  const parts = [...pools.map(p=>[pname(p), L.lp[p].valueUSD, MEDAL[p]||C.sand]), ['USDG', R_.safeUsdg, '#e8e3d9'], ['ETH', ethU, '#77776c'], ['Equities outside pools', R_.safeStockUsd, C.bronze]].filter(x=>x[1]>1);
  const tot = sum(parts.map(x=>x[1])), left = `${Math.floor(epLeft/86400)}d ${Math.floor(epLeft%86400/3600)}h`;
  const tok7 = sum(s7.map(r=>tr(r)+chs(r))), tokP = P7.length?sum(P7.map(r=>tr(r)+chs(r))):null, pf7 = sum(s7.map(r=>r.spFee||0)), sv7 = sum(s7.map(served));
  const lp7 = sum(s7.map(lpp)), lv7 = sum(s7.map(lvol)), eqd = sum(s7.map(r=>sum(stockPools.map(p=>r['chainVol_'+p]||0)))), eqn = sum(s7.map(r=>sum(stockPools.map(p=>r['spVolMine_'+p]??r['spVol_'+p]??0))));
  const cg = (a,b)=>{const c=chg(a,b,{pol:1}); return `<span class="${c.c}">${c.t}</span>`;};
  el.innerHTML = `<div class="h-top"><div></div>
      <div class="mark">Standard Reserve<i></i>Protocol monitor</div>
      <div><span class="badge ${L.epochNetFlow>=0?'exp':'con'}"><i></i><span>Epoch ${L.epoch} settles</span> ${left}</span></div></div>
    <div class="h-num"><strong>$${Math.round(L.reserve.totalUsd).toLocaleString('en-US')}</strong>
      <p>in reserve assets behind <b>${fmt.n(L.float,2)}</b> STANDARD in wallets. The token trades at <b>${fmt.x(pbNow)}</b> backing.</p></div>
    <div class="race">${parts.map(x=>`<span style="flex-grow:${(x[1]/tot*1000).toFixed(0)};background:${x[2]}"></span>`).join('')}</div>
    <div class="totals"><ol>${parts.map(x=>`<li><i style="background:${x[2]}"></i><span>${x[0]}</span> ${fmt.pct(x[1]/tot,0)}</li>`).join('')}</ol>
      <p>${fmt.usd(sum(s7.map(inc)))} <span>revenue, 7d</span> ${fmt.int(L.branches)} <span>branches</span></p></div>
    <ul class="how">
      <li><b>Token economy</b><strong>${fmt.usd(tok7)}</strong>STANDARD trading fees and charter sales over seven days, ${cg(tok7,tokP)} on the week before.</li>
      <li><b>Liquidity business</b><strong>${fmt.usd(pf7)}</strong>LP fees on ${fmt.usd(sv7)} of volume served, ${fmt.pct(eqd?eqn/eqd:null,0)} of chain equity volume.</li>
      <li><b>Launchpad</b><strong>${fmt.usd(lp7)}</strong>Launchpad revenue on ${fmt.usd(lv7)} of volume, ${cg(lp7, P7.length?sum(P7.map(lpp)):null)} on the week before.</li></ul>`;
}
let LIVEHM = '', LIVEB = 0;

// ---------- growth monitor ----------
function renderGM(){
  const flow = (label, f, fm, pol, o={})=>({label, u:'7d', cur:sum(s7.map(f)), prev:P7.length?sum(P7.map(f)):null, fm, pol, sp:roll7(f), ...o});
  const ratio = (label, nf, df, pol)=>{const r=(rows)=>{const d=sum(rows.map(df)); return d?sum(rows.map(nf))/d:null;}; return {label, u:'7d', cur:r(s7), prev:P7.length?r(P7):null, fm:v=>fmt.pct(v,1), pol, pp:true, sp:rollRatio(nf,df)};};
  const level = (label, cur, f, fm, pol, o={})=>({label, u:'', cur, prev:W0?f(W0):null, fm, pol, sp:lvl(f), ...o});
  const eqN = r=>sum(stockPools.map(p=>r['spVolMine_'+p]??r['spVol_'+p]??0)), eqD = r=>sum(stockPools.map(p=>r['chainVol_'+p]||0));
  const G = [
    ['Revenue', [
      flow('Revenue', inc, fmt.usd, 1),
      flow('STANDARD trading fees', tr, fmt.usd, 1),
      flow('LP fees', r=>r.spFee||0, fmt.usd, 1),
      flow('Launchpad revenue', lpp, fmt.usd, 1),
      flow('Charter sales', chs, fmt.usd, 1)]],
    ['Liquidity business', [
      flow('Volume served by the reserve', served, fmt.usd, 1),
      ratio('Share of chain equity volume', eqN, eqD, 1),
      ratio('Organic share of pool volume', r=>ck(r,'Org'), r=>sum(CPK.map(k=>ck(r,k))), 1),
      flow('Launchpad trading volume', lvol, fmt.usd, 1)]],
    ['Token', [
      level('STANDARD price', L.price, r=>r.price, fmt.px, 1),
      level('Market cap', mcTotal, r=>r.mcTotal, fmt.usd, 1),
      level('Market cap, in wallets', mcFloat, r=>r.mcFloat, fmt.usd, 1),
      flow('Net buying, STANDARD', r=>-(r.mktNet||0), v=>fmt.sx(v/1e6,2)+'M', 1, {abs:true, f:v=>fmt.n(v,2)}),
      flow('STANDARD burned', burnAll, v=>fmt.n(v,2), 1)]],
    ['Balance sheet', [
      level('Reserve assets', L.reserve.totalUsd, r=>r.reserveUsd, fmt.usd, 1),
      level('Backing per STANDARD in wallets', backing, bkOf, v=>v==null?'–':'$'+v.toFixed(4), 1),
      level('Price to backing', pbNow, pbOf, v=>fmt.x(v), 0, {abs:true, f:v=>v.toFixed(2)+'×'})]],
    ['Banks', [
      level('Branches', L.branches, r=>r.branches, fmt.int, 1),
      level('Active charters', L.activeCharters, r=>r.activeCharters, fmt.int, 1),
      flow('Withdrawn from banks, STANDARD', r=>r.wdGross||0, v=>fmt.n(v,2), -1),
      level('In banks, ledger balance', L.pending, r=>r.pending, v=>fmt.n(v,2), 0),
      level('S-Bills locked', L.sbills.locked, r=>r.sbLocked??r.sbills, v=>fmt.n(v,2), 1),
      level('Issuance multiplier', L.multiplier, r=>r.multiplier, v=>fmt.x(v), 1, {abs:true, f:v=>v.toFixed(2)})]],
  ];
  const head = `<tr><th>Metric</th><th>Current</th><th>Week earlier</th><th>Change</th><th>Trend</th></tr>`;
  document.getElementById('t_gm').innerHTML = head + G.map(([g,rows])=>`<tr class="grp"><td colspan="5">${g}</td></tr>`+rows.map(m=>{
    const c = chg(m.cur, m.prev, m); const col = c.c==='up'?C.green:c.c==='dn'?C.red:C.muted;
    return `<tr><td>${m.label}${m.u?`<span class="u">${m.u}</span>`:''}</td><td>${m.fm(m.cur)}</td><td class="mut">${m.prev==null?'–':m.fm(m.prev)}</td><td class="c ${c.c}">${c.t}</td><td>${spark(m.sp, col, false)}</td></tr>`;}).join('')).join('');
}

// ---------- tables and blocks that do not depend on the range ----------
const R = L.reserve, ctx = L.poolCtx, ydS = yd || '1d';
const pvm = (r,p)=>r['spVolMine_'+p]!=null ? r['spVolMine_'+p] : (r['spVol_'+p]||0);
function renderStatic(){
  document.getElementById('t_epochs').innerHTML = '<tr><th>Epoch</th><th>Settled</th><th>Net flow, ETH</th><th>Regime</th><th>STANDARD trading fees, ETH</th><th>Charter proceeds, ETH</th><th>Routed, ETH</th><th>Vault 70%</th><th>POL 15%</th><th>Team 15%</th><th>Multiplier after</th></tr>' +
    E.slice().reverse().map(e=>`<tr><td>${e.epoch}</td><td>${fmt.dt(e.settledAt)}</td><td class="${e.netFlow>=0?'pos':'neg'}">${fmt.sx(e.netFlow,1)}</td><td><span class="chip ${isExp(e)?'exp':'con'}">${isExp(e)?'expansion':'contraction'}</span></td><td>${(e.routed-e.charterEth).toFixed(1)}</td><td>${e.charterEth.toFixed(1)}</td><td>${e.routed.toFixed(1)}</td><td>${e.toVault.toFixed(1)}</td><td>${e.toPol.toFixed(1)}</td><td>${e.team.toFixed(1)}</td><td>${e.multiplierAfter.toFixed(2)}×</td></tr>`).join('');
  const prow = pools.map(p=>{const v=L.lp[p], c=ctx[p]||{}; return {p, v, f7:sum(s7.map(r=>r['spFee_'+p]||0)), v1:pvm(Y,p), v7:sum(s7.map(r=>pvm(r,p)))};});
  const pt = {val:sum(prow.map(x=>x.v.valueUSD||0)), f7:sum(prow.map(x=>x.f7)), v1:sum(prow.map(x=>x.v1)), v7:sum(prow.map(x=>x.v7))};
  document.getElementById('t_pools').innerHTML = `<tr><th>Pool</th><th>Position value</th><th>Price</th><th>Fee tier</th><th>Volume, 7d</th><th>LP fees, 7d</th><th>APR</th><th>Share of in-range liquidity</th><th>Share of chain volume</th><th>Share of chain liquidity</th><th>Rank on chain</th><th>Venues</th></tr>` +
    prow.map(({p,v,f7,v7})=>`<tr title="${Y['otherTvl_'+p]?'largest other venue '+fmt.usd(Y['otherTvl_'+p],1)+' '+Y['otherDex_'+p]:''}"><td><i style="display:inline-block;width:6px;height:6px;background:${PCOL[p]||C.muted};margin-right:.5rem"></i>${shortP(p)}</td><td>${fmt.usd(v.valueUSD)}</td><td>${pxf(v.price)}</td><td>${v.feeTier>=8388608?'session':(v.feeTier/1e4).toFixed(2)+'%'}</td><td>${fmt.usd(v7)}</td><td>${fmt.usd(f7,1)}</td><td>${v.valueUSD?fmt.pct(f7*365/7/v.valueUSD,0):'–'}</td><td>${v.share!=null?fmt.pct(v.share,0):'–'}</td><td>${Y['volShare_'+p]!=null?fmt.pct(Y['volShare_'+p],0):'–'}</td><td>${Y['liqShare_'+p]!=null?fmt.pct(Y['liqShare_'+p],0):'–'}</td><td>${Y['rank_'+p]?'#'+Y['rank_'+p]:'–'}</td><td>${Y['venues_'+p]??'–'}</td></tr>`).join('') +
    `<tr class="tot"><td>Total</td><td>${fmt.usd(pt.val)}</td><td></td><td></td><td>${fmt.usd(pt.v7)}</td><td>${fmt.usd(pt.f7,1)}</td><td>${pt.val?fmt.pct(pt.f7*365/7/pt.val,0):'–'}</td><td></td><td></td><td></td><td></td><td></td></tr>`;
  const comp = (r)=>{const q=r&&r.reserveParts; if(!q) return null; const o={}; Object.entries(q.lp||{}).forEach(([k,v])=>o[pname(k)]=v); o['USDG']=q.usdg; o['ETH, Safe and vaults']=q.eth; o['Equities outside pools']=q.stocks; o['Total']=q.total; return o;};
  const RT = Sh[Sh.length-1], rc0 = comp(RT), rc1 = comp(Sh[Sh.length-2]), rc7 = comp(Sh[Sh.length-8]);
  const dcell = (a,b)=>a!=null&&b!=null ? `<td class="${Math.abs(a-b)<0.5?'mut':a-b>0?'pos':'neg'}">${fmt.sgn(a-b)}${fmt.usd(a-b,1)}</td><td class="${Math.abs(a-b)<0.5?'mut':a-b>0?'pos':'neg'}">${b?fmt.sgn(a-b)+fmt.pct((a-b)/b,1):'–'}</td>` : '<td>–</td><td>–</td>';
  document.getElementById('t_resd').innerHTML = rc0 ? '<tr><th>Component</th><th>Today</th><th>Share</th><th>Change, 1 day</th><th>%</th><th>Change, 7 days</th><th>%</th></tr>' +
    Object.keys(rc0).map(k=>`<tr class="${k==='Total'?'tot':''}"><td>${k}</td><td>${fmt.usd(rc0[k])}</td><td class="mut">${k==='Total'?'':fmt.pct(rc0[k]/rc0.Total,1)}</td>${dcell(rc0[k], rc1&&rc1[k])}${dcell(rc0[k], rc7&&rc7[k])}</tr>`).join('') : '';
  const cpRow = (ps)=>{const q=cpShares(s7, ps); return CPK.map(k=>`<td>${q?q[k]+'%':'–'}</td>`).join('');};
  document.getElementById('t_cpty').innerHTML = '<tr><th>Pool</th><th>Organic</th><th>Arbitrage</th><th>Bots</th><th>Fee-exempt</th></tr>' +
    pools.map(p=>`<tr><td>${shortP(p)}</td>${cpRow([p])}</tr>`).join('') + `<tr class="tot"><td>All pools</td>${cpRow(pools)}</tr>`;
  const pnlOf = (r,p)=>r['lpVal_'+p]!=null ? {lp:r['lpVal_'+p], hold:r['holdVal_'+p], cost:r['lpCost_'+p], fees:r['lpFees_'+p]} : null;
  const PY = pools.map(p=>[p, pnlOf(Y,p)]).filter(x=>x[1]);
  const t7 = PY.reduce((a,[p,v])=>({lp:a.lp+v.lp, hold:a.hold+v.hold, cost:a.cost+v.cost, fees:a.fees+v.fees}), {lp:0,hold:0,cost:0,fees:0});
  const pcell = v=>`<td class="${v>=0?'pos':'neg'}">${fmt.sgn(v)}${fmt.usd(v,1)}</td>`;
  document.getElementById('t_pnl').innerHTML = '<tr><th>Pool</th><th>Fees</th><th>Divergence</th><th>Net vs holding</th><th>Net in USD</th></tr>' +
    PY.map(([p,v])=>`<tr title="cost ${fmt.usd(v.cost,2)} · value ${fmt.usd(v.lp,2)} · holding ${fmt.usd(v.hold,2)}"><td>${shortP(p)}</td><td>${fmt.usd(v.fees,1)}</td>${pcell(v.lp-v.hold)}${pcell(v.lp+v.fees-v.hold)}${pcell(v.lp+v.fees-v.cost)}</tr>`).join('') +
    (PY.length?`<tr class="tot" title="cost ${fmt.usd(t7.cost,2)} · value ${fmt.usd(t7.lp,2)} · holding ${fmt.usd(t7.hold,2)}"><td>Total</td><td>${fmt.usd(t7.fees,1)}</td>${pcell(t7.lp-t7.hold)}${pcell(t7.lp+t7.fees-t7.hold)}${pcell(t7.lp+t7.fees-t7.cost)}</tr>`:'');
  // where fees land, over the same seven days as the revenue figures
  const epOfDate = {}; E.forEach(e=>{for(let t=e.start+3600;t<e.end;t+=86400) epOfDate[fmt.dt(t)] = e;});
  const al = {pool:0, lp:0, vExp:0, vCon:0, pol:0, team:0, open:0};
  s7.forEach(r=>{const tok=((r.tradingFeeEth||0)+(r.charterEth||0))*ethOf(r), e=epOfDate[r.date]; al.pool += r.spFee||0; al.lp += lpp(r);
    if(e && e.routed>0){ const v=tok*e.toVault/e.routed; if(isExp(e)) al.vExp+=v; else al.vCon+=v; al.pol += tok*e.toPol/e.routed; al.team += tok*e.team/e.routed; } else al.open += tok; });
  const went = [['Reserve backing', al.pool+al.vExp, C.celadon], ['Buybacks', al.vCon+al.pol, C.gold], ['Team', al.team, C.rose], ['Launchpad fee Safe', al.lp, C.sapphire], ['Not yet routed', al.open, C.grey]];
  const wTot = sum(went.map(w=>w[1]));
  document.getElementById('alloc').innerHTML = `<div class="abar">${went.map(w=>`<div style="width:${(100*w[1]/wTot).toFixed(2)}%;background:${w[2]}"></div>`).join('')}</div>`+
    `<div class="lg">${went.map(w=>`<i style="background:${w[2]}"></i><span>${w[0]}</span><span class="v">${fmt.usd(w[1])}</span><span class="p">${fmt.pct(w[1]/wTot,0)}</span>`).join('')}</div>`;
  document.getElementById('h_alloc').innerHTML = `<em>${fmt.usd(wTot)}</em>`;
  // holder groups, sellers, depth
  const GN = Object.fromEntries(GROUPS.map(g=>[g[0], g[1]]));
  const shortA = a=>`<a href="https://robin.etherscan.io/address/${a}" target="_blank" rel="noopener" style="text-decoration:none">${a.slice(0,6)}…${a.slice(-4)}</a>`;
  document.getElementById('t_sellers').innerHTML = '<tr><th>Wallet</th><th class="l">Group</th><th>Net sold</th><th>Sells</th><th>Buys</th></tr>' +
    (DATA.sellers||[]).map(x=>`<tr><td class="addr">${shortA(x.addr)}</td><td class="l">${GN[x.group]||x.group}</td><td>${fmt.n(x.net,2)}</td><td>${x.sells}</td><td>${x.buys}</td></tr>`).join('');
  const DP = DATA.depth;
  if (DP) {
    const pc = v=>v==null?'–':fmt.pct(v,1);
    document.getElementById('t_slip').innerHTML = '<tr><th>Size</th><th>Buy impact</th><th>Buy cost</th><th>Sell impact</th><th>Sell cost</th></tr>' +
      DP.slip.map(x=>`<tr><td>${fmt.usd(x.usd,0)}</td><td>${pc(x.buyImpact)}</td><td>${pc(x.buyAllIn)}</td><td>${pc(x.sellImpact)}</td><td>${pc(x.sellAllIn)}</td></tr>`).join('');
    document.getElementById('slip_s').innerHTML = [['Pool fee and tax', `${fmt.pct(DP.fee,0)} · ${fmt.pct(DP.taxBuy,0)} buy, ${fmt.pct(DP.taxSell,0)} sell`], ['Depth within 5%', `${fmt.usd(DP.bid5)} bid · ${fmt.usd(DP.ask5)} ask`], ['Protocol share of in-range liquidity', fmt.pct(DP.protocolShare,0)]].map(x=>`<div>${x[0]}</div><div>${x[1]}</div>`).join('');
  }
  // launchpad: standings and the fee Safe
  const TEAM = {US:['United States','SPCX'], CN:['China','BABA'], KR:['South Korea','SKHY'], ETH:['ETH','ETH']}, TCOL = {US:C.silver, CN:C.gold, KR:C.celadon, ETH:C.sapphire};
  const tm = (LPD.teams||[]).slice().sort((a,b)=>b.points-a.points), tp = sum(tm.map(t=>t.points));
  document.getElementById('t_kotm').innerHTML = '<tr><th>Team</th><th>Points</th><th>Share</th><th>Scored volume</th></tr>' +
    tm.map((t,i)=>`<tr class="${i===0?'today':''}" title="${fmt.int(t.traders)} traders"><td><i style="display:inline-block;width:6px;height:6px;margin-right:.5rem;background:${TCOL[t.country]||C.sand}"></i>${(TEAM[t.country]||[t.country])[0]} <span style="color:var(--dis);font-size:.75rem">$${(TEAM[t.country]||[])[1]||''}</span></td><td>${fmt.n(t.points,1)}</td><td>${fmt.pct(tp?t.points/tp:null,0)}</td><td>${fmt.usd(t.volumeUsd,1)}</td></tr>`).join('');
  const potFees = sum(Sh.map(lpot)), pot = (LPD.seedUsd||0)+potFees;
  document.getElementById('kotm_pool').innerHTML = [['Opening pot, per the protocol’s site', fmt.usd(LPD.seedUsd||0)], ['Reward pool share of fees, 20%', fmt.usd(potFees)], ['Incentives, 65%, by points', fmt.usd(pot*.65)], ['Jackpot, 35%, leading team', fmt.usd(pot*.35)]].map(x=>`<div>${x[0]}</div><div>${x[1]}</div>`).join('');
  document.getElementById('h_kotm').innerHTML = LPD.season ? `closes <em>${dm(fmt.dt(LPD.season.endsAt))} ${fmt.hm(LPD.season.endsAt)} UTC</em>` : '';
  const HP = {USDG:1, WETH:L.ethusd}; pools.forEach(p=>{HP[p]=L.lp[p].price;});
  const held = Object.entries(LPD.held||{}).filter(([s,a])=>a>1e-9).sort((a,b)=>b[1]*(HP[b[0]]||0)-a[1]*(HP[a[0]]||0));
  const hTot = sum(held.map(([s,a])=>a*(HP[s]||0)));
  document.getElementById('t_fsafe').innerHTML = '<tr><th>Token</th><th>Balance</th><th>Value</th></tr>' +
    held.map(([s,a])=>`<tr title="at ${pxf(HP[s]||0)}"><td>${s}</td><td>${a.toFixed(2)}</td><td>${fmt.usd(a*(HP[s]||0))}</td></tr>`).join('') +
    `<tr class="tot"><td>Total</td><td></td><td>${fmt.usd(hTot)}</td></tr>` +
    `<tr><td>Withdrawn since launch</td><td></td><td>${fmt.usd(sum(S.map(r=>r.lpadSafeOut||0)))}</td></tr>`;
  document.getElementById('h_fsafe').innerHTML = `<a href="https://robin.etherscan.io/address/${LPD.feeSafe||''}" target="_blank" rel="noopener" style="text-decoration:none">${(LPD.feeSafe||'').slice(0,6)}…${(LPD.feeSafe||'').slice(-4)}</a> · 2-of-4`;
}
function renderBridge(){
  const mintAll = sum(S.map(r=>r.mint||0)), bbAll = sum(S.map(r=>r.burnBuyback||0)), depAll = sum(S.map(r=>r.depositBurn||0)), othAll = sum(S.map(r=>r.burnOther||0));
  const sbLock = L.sbills.locked||0, sbPot = Math.max(0, L.sbillsStd - sbLock), resid = L.totalSupply-(100e6+mintAll-bbAll-othAll-depAll);
  const br = [['Genesis liquidity mint', 100e6], ['+ Withdrawn from banks, minted', mintAll], ['− Buybacks burned', -bbAll], ['− Tax hook burns', -othAll], ['− Deposited into banks', -depAll],
    ...(Math.abs(resid)>=0.5?[['± Unreconciled', resid]]:[]), ['= Circulating supply', L.totalSupply, 'tot'],
    ['− Protocol liquidity', -L.poolStd], ['− Incentives vault', -L.incentivesStd], ['= In wallets', L.float, 'tot'],
    ['− S-Bill principal', -sbLock], ['− S-Bill premium pot', -sbPot], ['− Team wallet', -L.teamStd], ['= Free float', L.float-L.sbillsStd-L.teamStd, 'tot']];
  document.getElementById('bridge').innerHTML = br.map(b=>`<div class="${b[2]||''}">${b[0]}</div><div class="${b[2]||''}">${fmt.n(b[1],2)}</div>`).join('');
}

// ---------- charts, built per tab on demand ----------
const grad = (color, a=.22)=>(c)=>{const {ctx, chartArea:ar}=c.chart; if(!ar) return alpha(color,a/2); const g=ctx.createLinearGradient(0,ar.top,0,ar.bottom); g.addColorStop(0,alpha(color,a)); g.addColorStop(1,alpha(color,0)); return g;};
const bar = (label, data, color, o={})=>({type:'bar', label, data, backgroundColor:color, stack:o.stack||'s', yAxisID:o.ax||'y', fmt:o.fmt, ...(o.x||{})});
const line = (label, data, color, o={})=>({type:'line', label, data, borderColor:color, backgroundColor:o.fill?grad(color):color, fill:o.fill?'origin':false, borderWidth:o.w||1.6,
  yAxisID:o.ax||'y', stack:'l_'+label, fmt:o.fmt, spanGaps:o.gaps??false, pointRadius:o.pts||0, pointStyle:o.ps, pointBackgroundColor:color, ...(o.x||{})});
function mk(el, labels, sets, o={}){
  const yf = o.y||(v=>v), scales = {x:{stacked:!!o.stacked, grid:{display:false}, ticks:{maxRotation:0, autoSkipPadding:14}},
    y:{stacked:!!o.stacked, beginAtZero:o.zero!==false, min:o.ymin, max:o.ymax, grid:{color:'rgba(255,255,255,.06)'}, ticks:{callback:yf}}};
  if (o.y1) scales.y1 = {position:'right', grid:{display:false}, beginAtZero:true, min:o.y1min, max:o.y1max, ticks:{callback:o.y1}};
  const cb = {label:c=>`${c.dataset.label}: ${(c.dataset.fmt||(c.dataset.yAxisID==='y1'?(o.tfy1||o.y1):null)||o.tf||yf)(c.parsed.y)}`};
  if (o.footer) cb.footer = o.footer; if (o.after) cb.afterBody = o.after; if (o.title) cb.title = o.title;
  return new Chart(el, {data:{labels, datasets:sets}, options:{maintainAspectRatio:false, scales,
    plugins:{legend:{display:o.legend!==false}, bands:{dates:o.bands}, tooltip:{callbacks:cb}}}});
}
let N = 30;
const REG = {}, BUILT = {}, DIRTY = {};
const reg = (tab, fn)=>{(REG[tab]=REG[tab]||[]).push(fn);};
function rctx(){ const Rl = last(Sh, N), Rf = last(Sp, N);
  return {Rl, Rf, ll:Rl.map(r=>dm(r.date)), lf:Rf.map(r=>dm(r.date)), dl:Rl.map(r=>r.date), df:Rf.map(r=>r.date)}; }
function drawTab(t){ (BUILT[t]||[]).forEach(c=>c.destroy()); BUILT[t]=[]; const x = rctx();
  (REG[t]||[]).forEach(fn=>{try{ const c=fn(x); if(c) BUILT[t].push(...[].concat(c)); }catch(e){ console.warn('chart', t, e); }}); DIRTY[t]=false; }
let TAB = 'overview';
function show(t){ if(!REG[t] && !document.getElementById('t-'+t)) t='overview'; TAB=t;
  document.querySelectorAll('.tab').forEach(s=>s.classList.toggle('on', s.id==='t-'+t));
  document.querySelectorAll('#tabs button[data-t]').forEach(b=>{b.classList.toggle('on', b.dataset.t===t); if(b.dataset.t===t) document.getElementById('crumb').textContent=b.textContent;});
  if (DIRTY[t]!==false || !BUILT[t]) drawTab(t); }
function redrawAll(){ Object.keys(REG).forEach(t=>{DIRTY[t]=true;}); drawTab(TAB); }
const usd0 = v=>fmt.usd(v,0), usd1 = v=>fmt.usd(v,1), pct0 = v=>fmt.pct(v,0), n0 = v=>fmt.n(v,0);

// overview
reg('overview', ()=>{ const B=[], daily = N===7, maxW = N===0 ? 99 : Math.floor(N/7);
  if (daily) last(Sp,7).forEach(r=>B.push([r]));
  else for(let e=Sp.length; e-7>=0 && B.length<maxW; e-=7) { const b=Sp.slice(e-7,e); if (b[0].date<ep2) break; B.unshift(b); }
  document.querySelector('#p_wrev .pt').textContent = daily ? 'Revenue by stream, last seven days' : 'Revenue by stream, weekly';
  const lab = B.map(b=>dm(b[b.length-1].date)), S_ = f=>B.map(b=>sum(b.map(f)));
  const c = mk(c_wrev, lab, [bar('STANDARD trading fees', S_(tr), STREAM.tr), bar('LP fees', S_(r=>r.spFee||0), STREAM.pool), bar('Launchpad revenue', S_(lpp), STREAM.lpad), bar('Charter sales', S_(chs), STREAM.ch)],
    {stacked:true, y:usd0, tf:usd1, title:i=>daily ? lab[i[0].dataIndex] : `7 days to ${lab[i[0].dataIndex]}`, footer:i=>{const b=B[i[0].dataIndex]; return `revenue ${fmt.usd(sum(b.map(inc)))}`;}});
  const i7 = sum(s7.map(inc)), p7 = P7.length ? sum(P7.map(inc)) : null; document.getElementById('h_wrev').innerHTML = `<em>${fmt.usd(i7)}</em> last 7d${p7!=null?` · ${chg(i7, p7, {pol:1}).t}`:''}`;
  return c; });
reg('overview', ({Rl, ll, dl})=>{ document.getElementById('h_pxb').innerHTML = `<em>${fmt.x(pbNow)}</em> price to backing`;
  return mk(c_pxb, ll, [line('Price', Rl.map(r=>r.price), C.gold, {fill:true}), line('Backing per STANDARD in wallets', Rl.map(bkOf), C.blue)], {y:v=>'$'+v.toFixed(3), tf:fmt.px,
    footer:i=>{const r=Rl[i[0].dataIndex]; return pbOf(r)!=null?`price to backing ${fmt.x(pbOf(r))}`:'';}}); });
const resStack = (el, {Rl, ll, dl}, byPool)=>{ const parts = (r,k)=>(r.reserveParts||{})[k], lpv = (r,p)=>((r.reserveParts||{}).lp||{})[p];
  const sets = [...(byPool ? pools.map(p=>line(pname(p), Rl.map(r=>lpv(r,p)??null), PCOL[p])) : [line('Uniswap v4 positions', Rl.map(r=>{const q=(r.reserveParts||{}).lp; return q?sum(Object.values(q)):null;}), C.blue)]),
    line('USDG', Rl.map(r=>parts(r,'usdg')??null), '#e8e3d9'), line('ETH, Safe and vaults', Rl.map(r=>parts(r,'eth')??null), '#77776c'), line('Equities outside pools', Rl.map(r=>parts(r,'stocks')??null), C.bronze)];
  sets.forEach((s,i)=>{s.fill = i===0?'origin':'-1'; s.backgroundColor = alpha(s.borderColor,.62); s.borderColor = s.borderColor; s.borderWidth = 1; s.stack='res';});
  return mk(el, ll, sets, {stacked:true, y:usd0, tf:v=>fmt.usd(v), footer:i=>{const r=Rl[i[0].dataIndex]; return r.reserveUsd?`total ${fmt.usd(r.reserveUsd)}`:'';}}); };
reg('overview', (x)=>{ document.getElementById('h_reso').innerHTML = `<em>${fmt.usd(L.reserve.totalUsd)}</em>`; return resStack(c_reso, x, true); });
reg('overview', ({Rl, ll, dl})=>{ document.getElementById('h_brco').innerHTML = `<em>${fmt.int(L.branches)}</em> branches · ${fmt.int(L.activeCharters)} charters`;
  return mk(c_brco, ll, [line('Branches', Rl.map(r=>r.branches), C.violet, {fill:true}), line('Active charters', Rl.map(r=>r.activeCharters), C.teal)], {y:n0, tf:fmt.int}); });

// revenue
reg('revenue', ({Rf, lf, df})=>{ const r7 = sum(s7.map(inc)), c7 = sum(s7.map(chs));
  document.getElementById('h_rev').innerHTML = `revenue <em>${fmt.usd(r7)}</em> · charter sales ${fmt.usd(c7)} · 7d`;
  return mk(c_rev, lf, [bar('STANDARD trading fees', Rf.map(tr), STREAM.tr), bar('LP fees', Rf.map(r=>r.spFee||0), STREAM.pool), bar('Launchpad revenue', Rf.map(lpp), STREAM.lpad), bar('Charter sales', Rf.map(chs), STREAM.ch)],
    {stacked:true, y:usd0, tf:usd1, bands:df, footer:i=>{const r=Rf[i[0].dataIndex]; return `revenue ${fmt.usd(inc(r),1)}`;}}); });
reg('revenue', ()=>{ const E2 = E.filter(e=>e.epoch>1 && inRange(e.settledAt)); document.getElementById('h_epochs').innerHTML = `${E.filter(isExp).length} of ${E.length} settled epochs in expansion`;
  return new Chart(c_epochs, {type:'bar', data:{labels:E2.map(e=>'E'+e.epoch), datasets:[
    {label:'STANDARD trading fees', data:E2.map(e=>e.routed-e.charterEth), backgroundColor:E2.map(e=>isExp(e)?C.celadon:alpha(C.red,.8)), stack:'a'},
    {label:'Charter proceeds', data:E2.map(e=>e.charterEth), backgroundColor:STREAM.ch, stack:'a'}]},
    options:{maintainAspectRatio:false, scales:{x:{stacked:true, grid:{display:false}}, y:{stacked:true, grid:{color:'rgba(255,255,255,.06)'}, ticks:{callback:v=>v+' ETH'}}},
      plugins:{legend:{display:true, onClick:()=>{}, labels:{generateLabels:()=>[{text:'STANDARD trading fees, expansion', fillStyle:C.celadon, strokeStyle:'transparent', fontColor:C.sand}, {text:'STANDARD trading fees, contraction', fillStyle:alpha(C.red,.8), strokeStyle:'transparent', fontColor:C.sand}, {text:'Charter proceeds', fillStyle:STREAM.ch, strokeStyle:'transparent', fontColor:C.sand}]}},
        tooltip:{callbacks:{afterTitle:i=>{const e=E2[i[0].dataIndex]; return (isExp(e)?'expansion':'contraction')+' · net flow '+fmt.sx(e.netFlow,1)+' ETH';}, label:c=>c.dataset.label+': '+c.parsed.y.toFixed(1)+' ETH'}}}}}); });
reg('revenue', ({Rf, lf, df})=>{ const v = prrOf(Y); document.getElementById('h_prr').innerHTML = v!=null?`<em>${fmt.x(v,1)}</em> ${yd}`:'';
  return mk(c_prr, lf, [line('Price to revenue', Rf.map(prrOf), C.gold, {fill:true})], {legend:false, y:v=>v.toFixed(1)+'×', tf:v=>fmt.x(v,1)}); });

// liquidity
reg('liquidity', ({Rf})=>{ document.getElementById('h_vol').innerHTML = `<em>${fmt.usd(sum(s7.map(served)))}</em> 7d`; Rf = Rf.filter(r=>r.date>=LP0);
  return mk(c_vol, Rf.map(r=>dm(r.date)), pools.map(p=>bar(shortP(p), Rf.map(r=>pvm(r,p)), PCOL[p])), {stacked:true, y:usd0, tf:usd1,
    after:i=>{const r=Rf[i[0].dataIndex]; return (r.spVol_ETH||0)>0?[`ETH/USDG pool total ${fmt.usd(r.spVol_ETH,1)}, served by the reserve ${fmt.pct(pvm(r,'ETH')/r.spVol_ETH,0)}`]:[];},
    footer:i=>`total ${fmt.usd(served(Rf[i[0].dataIndex]),1)} · fee-exempt ${fmt.usd(Rf[i[0].dataIndex].spVolZeroFee||0,1)}`}); });
reg('liquidity', ({Rf})=>{ document.getElementById('h_pfee').innerHTML = `<em>${fmt.usd(sum(s7.map(r=>r.spFee||0)))}</em> 7d`; Rf = Rf.filter(r=>r.date>=LP0);
  return mk(c_pfee, Rf.map(r=>dm(r.date)), pools.map(p=>bar(shortP(p), Rf.map(r=>r['spFee_'+p]||0), PCOL[p])), {stacked:true, y:usd0, tf:usd1, footer:i=>`total ${fmt.usd(Rf[i[0].dataIndex].spFee||0,1)}`}); });
const LP0 = '2026-10-14';
const shareChart = (el, key, num, den, what)=>({Rf})=>{ const Rq = Rf.filter(r=>r.date>=LP0);
  return mk(el, Rq.map(r=>dm(r.date)), pools.map(p=>line(shortP(p), Rq.map(r=>r[key+p]??null), PCOL[p], {gaps:true})), {y:pct0, tf:v=>fmt.pct(v,1), ymin:0, ymax:1,
    after:i=>{const r=Rq[i[0].dataIndex]; return pools.filter(p=>r[den+p]).map(p=>`${shortP(p)}: ${what} ${fmt.usd(num(r,p)||0,1)} of ${fmt.usd(r[den+p],1)}`);}}); };
reg('liquidity', (x)=>{ document.getElementById('h_vshare').innerHTML = pools.map(p=>`${shortP(p)} <em>${fmt.pct(Y['volShare_'+p],0)}</em>`).join(' · '); return shareChart(c_vshare, 'volShare_', (r,p)=>r['spVolMine_'+p]??r['poolVolChain_'+p], 'chainVol_', 'served')(x); });
reg('liquidity', (x)=>{ document.getElementById('h_lshare').innerHTML = pools.map(p=>`${shortP(p)} <em>${fmt.pct(Y['liqShare_'+p],0)}</em>`).join(' · '); return shareChart(c_lshare, 'liqShare_', (r,p)=>((r.reserveParts||{}).lp||{})[p], 'chainTvl_', 'position')(x); });
reg('liquidity', ({Rf})=>{ const Rc = Rf.filter(r=>r.date>=LP0 && pools.some(p=>r['cpN_'+p]!=null));
  const c7 = Object.fromEntries(CPK.map(k=>[k, sum(s7.map(r=>ck(r,k)))])), t7 = sum(CPK.map(k=>c7[k]));
  document.getElementById('h_cpty').innerHTML = t7 ? `organic <em>${cpShares(s7).Org}%</em> of ${fmt.usd(t7)} · 7d` : '';
  return mk(c_cpty, Rc.map(r=>dm(r.date)), [bar('Organic users', Rc.map(r=>ck(r,'Org')), C.celadon), bar('Cross-venue arbitrage', Rc.map(r=>ck(r,'Arb')), C.rose), bar('Other bots', Rc.map(r=>ck(r,'Bot')), C.sapphire), bar('Fee-exempt contract', Rc.map(r=>ck(r,'Fx')), C.grey)],
    {stacked:true, y:usd0, tf:usd1, footer:i=>{const r=Rc[i[0].dataIndex], t=sum(CPK.map(k=>ck(r,k))); return t?`organic share ${fmt.pct(ck(r,'Org')/t,0)}`:'';}}); });
reg('liquidity', ({Rf})=>{ const Rq = Rf.filter(r=>r.date>=LP0), pnl = (r,p)=>r['lpVal_'+p]!=null ? r['lpVal_'+p]+r['lpFees_'+p]-r['holdVal_'+p] : null;
  const tot = r=>{const v=pools.map(p=>pnl(r,p)); return v.some(x=>x!=null)?sum(v):null;};
  document.getElementById('h_pnl').innerHTML = Y.date ? `<em>${fmt.sgn(tot(Y))}${fmt.usd(tot(Y),1)}</em> against holding, ${yd}` : '';
  return mk(c_pnl, Rq.map(r=>dm(r.date)), [...pools.map(p=>line(shortP(p), Rq.map(r=>pnl(r,p)), PCOL[p])), line('All pools', Rq.map(tot), C.gold, {w:2.4})], {zero:false, y:usd0, tf:v=>fmt.sgn(v)+fmt.usd(v,1)}); });

// launchpad
reg('launchpad', ({Rf})=>{ const Rq = Rf.filter(r=>r.date>=LP0);
  document.getElementById('h_lfee').innerHTML = `<em>${fmt.usd(sum(Sh.map(r=>(r.lpadSafe||0)+(r.lpadEsc||0))))}</em> since 14 Oct · protocol ${fmt.usd(sum(Sh.map(lpp)))}`;
  return mk(c_lfee, Rq.map(r=>dm(r.date)), [bar('Protocol, 50%', Rq.map(lpp), C.sapphire), bar('Reward pool, 20%', Rq.map(lpot), C.gold), bar('Creators, 30% and module fees', Rq.map(lcr), C.silver)],
    {stacked:true, y:usd0, tf:usd1, footer:i=>{const r=Rq[i[0].dataIndex]; return `implied launchpad volume ${fmt.usd(lvol(r),2)}`;}}); });
reg('launchpad', ({Rf})=>{ const Rc = Rf.filter(r=>r.date>=LP0), lf_ = r=>r.spFeeLpad||0, all_ = r=>r.spFee||0;
  const a = sum(s7.map(lf_)), b = sum(s7.map(all_));
  document.getElementById('h_lroute').innerHTML = b ? `<em>${fmt.usd(a)}</em>, ${fmt.pct(a/b,1)} of LP fees · 7d` : '';
  return mk(c_lroute, Rc.map(r=>dm(r.date)), [bar('Launchpad-routed trades', Rc.map(lf_), C.sapphire), bar('All other trades', Rc.map(r=>Math.max(0, all_(r)-lf_(r))), alpha(C.sand,.45))],
    {stacked:true, y:usd0, tf:usd1, footer:i=>{const r=Rc[i[0].dataIndex]; return all_(r)?`launchpad-routed share ${fmt.pct(lf_(r)/all_(r),1)} · ${fmt.usd(r.spVolLpad||0)} of volume`:'';}}); });

// reserve
reg('reserve', (x)=>{ document.getElementById('h_res').innerHTML = `<em>${fmt.usd(L.reserve.totalUsd)}</em>`; return resStack(c_res, x, true); });
reg('reserve', ({Rl, ll, dl})=>{ document.getElementById('h_pb').innerHTML = `<em>${fmt.x(pbNow)}</em> · backing $${backing.toFixed(4)}`;
  return mk(c_pb, ll, [line('Price to backing', Rl.map(pbOf), C.gold, {fill:true})], {legend:false, y:v=>v.toFixed(1)+'×', tf:v=>fmt.x(v),
    after:i=>{const r=Rl[i[0].dataIndex]; return r.reserveUsd&&r.float?[`price ${fmt.px(r.price)} · backing $${(r.reserveUsd/r.float).toFixed(4)}`]:[];}}); });

// token
reg('token', ({Rl, ll, dl})=>{ document.getElementById('h_price').innerHTML = `<em>${fmt.px(L.price)}</em> · ${fmt.usd(mcTotal)} market cap · ${fmt.usd(mcFloat)} in wallets`;
  return mk(c_price, ll, [line('Price', Rl.map(r=>r.price), C.gold, {fill:true}), line('Market cap', Rl.map(r=>r.mcTotal), C.blue, {ax:'y1'})],
    {y:v=>'$'+v.toFixed(2), tf:fmt.px, y1:usd0, tfy1:usd1, bands:dl, footer:i=>{const r=Rl[i[0].dataIndex]; return r.mcFloat?`market cap, in wallets ${fmt.usd(r.mcFloat)}`:'';}}); });
reg('token', ({Rf, lf, df})=>{ const nb7 = -sum(s7.map(r=>r.mktNet||0));   // net buying: STANDARD bought from the pool less STANDARD sold into it
  document.getElementById('h_sell').innerHTML = `net ${nb7>=0?'buying':'selling'} <em>${fmt.n(Math.abs(nb7),2)}</em> STANDARD, 7d`;
  return mk(c_sell, lf, [...GROUPS.map(([k,n,c])=>bar(n, Rf.map(r=>-(r['sell_'+k]||0)), c)), line('Net buying, all groups', Rf.map(r=>-(r.mktNet||0)), C.fg2, {pts:2})],
    {stacked:true, zero:false, y:n0, tf:v=>fmt.sgn(v)+fmt.n(v,2), footer:i=>{const r=Rf[i[0].dataIndex], v=-(r.mktNet||0); return r.price?`net ${v>=0?'buying':'selling'} ${fmt.usd(Math.abs(v)*r.price)} at the close`:'';}}); });
reg('token', ({Rl, ll, dl})=>{ document.getElementById('h_mc').innerHTML = `<em>${fmt.n(L.float,2)}</em> in wallets · ${fmt.n(L.pending,2)} in banks`;
  const sets = [line('In wallets', Rl.map(r=>r.float), C.gold), line('Protocol liquidity and Incentives vault', Rl.map(r=>(r.pool||0)+(r.incentives||0)), C.blue), line('In banks', Rl.map(r=>r.pending), C.violet)];
  sets.forEach((s,i)=>{s.fill=i===0?'origin':'-1'; s.backgroundColor=alpha(s.borderColor,.4); s.borderWidth=1; s.stack='sup';});
  return mk(c_mc, ll, sets, {stacked:true, y:n0, tf:v=>fmt.n(v,2), footer:i=>{const r=Rl[i[0].dataIndex]; return `total ${fmt.n((r.supply||0)+(r.pending||0),2)}, of which ${fmt.n(r.supply||0,2)} circulating`;}}); });
reg('token', ({Rf, lf, df})=>{ const ofl = (r)=>{const i=Sh.indexOf(r), p=i>0?Sh[i-1]:null; if(!p) return null;
    const dF=r.float-p.float, W=(r.mint||0), Dist=(r.fromIncentives||0), Fees=(r.feesToTeam||0), Mk=-(r.mktNet||0), Dep=-(r.depositBurn||0), Ob=-((r.burn||0)-(r.depositBurn||0)-(r.burn_contraction||0)-(r.burnOther||0));
    return {dF, W, Dist, Fees, Mk, Dep, Ob, Oth:dF-(W+Dist+Fees+Mk+Dep+Ob)};};
  const OF = Rf.map(ofl), of = (k)=>OF.map(o=>o?o[k]:null);
  return mk(c_flows, lf, [bar('Withdrawn from banks, minted', of('W'), C.green), bar('Incentives Vault distributions', of('Dist'), C.teal), bar('Position fees to the team', of('Fees'), C.pink),
    bar('Net buying', of('Mk'), C.blue), bar('Deposited into banks', of('Dep'), C.grey), bar('S-Bill burns', of('Ob'), C.red),
    ...(OF.some(o=>o&&Math.abs(o.Oth)>=0.5)?[bar('Protocol contracts, other', of('Oth'), C.orange)]:[]), line('Change in wallets', of('dF'), C.fg2, {pts:2})],
    {stacked:true, zero:false, y:n0, tf:v=>fmt.sgn(v)+fmt.n(v,2)}); });
reg('token', ({Rl, ll, dl})=>{ const DP=DATA.depth||{}; document.getElementById('h_depth').innerHTML = `<em>${fmt.usd(DP.bid2)}</em> bid within 2%`;
  return mk(c_depth, ll, [line('Bid depth within 2%', Rl.map(r=>r.bid2??null), C.gold, {fill:true}), line('Bid depth within 5%', Rl.map(r=>r.bid5??null), C.blue)], {y:usd0, tf:usd1,
    after:i=>{const r=Rl[i[0].dataIndex]; return r.ask2!=null?[`ask ${fmt.usd(r.ask2,1)} within 2% · ${fmt.usd(r.ask5,1)} within 5%`]:[];}}); });
reg('token', ({Rf, lf, df})=>{ document.getElementById('h_burn').innerHTML = `<em>${fmt.n(capRemoved,2)}</em> burned · ${fmt.pct(capRemoved/1e9,1)} of the cap`;
  const cum = []; {let c=0; Sp.forEach(r=>{c+=burnAll(r); cum.push(c);});} const cw = last(cum, N);
  return mk(c_burn, lf, [bar('Expansion licenses', Rf.map(r=>r.licBurn||0), C.gold), bar('Resolution and revocation fees, burned half', Rf.map(r=>(r.exitFeeBurn||0)+(r.revokeFeeBurn||0)), C.orange),
    bar('Buybacks and other token burns', Rf.map(burnTokens), C.red), line('Cumulative, share of the 1B cap', cw.map(v=>v/1e9), C.fg2, {ax:'y1'})],
    {stacked:true, y:n0, tf:v=>fmt.n(v,2), y1:v=>fmt.pct(v,1), after:i=>[`cumulative ${fmt.n(cw[i[0].dataIndex],2)} STANDARD`]}); });

// banks
reg('banks', ({Rf, lf, df})=>{ document.getElementById('h_bank').innerHTML = `in banks <em>${fmt.n(L.pending,2)}</em> · resolution fee ${fmt.pct(L.exitFeeNow,1)}`;
  return mk(c_bank, lf, [bar('Issued to banks', Rf.map(r=>r.issuance||0), C.gold), bar('Deposited by bankers', Rf.map(r=>r.deposits||0), C.celadon),
    bar('Stayers’ cut', Rf.map(r=>(r.exitFeeRedis||0)+(r.revokeFeeBurn||0)), C.violet), bar('Spent on licenses, burned', Rf.map(r=>-(r.licBurn||0)), C.grey),
    bar('Withdrawn by closing branches', Rf.map(r=>-(r.wdGross||0)), C.orange), bar('Revoked charters', Rf.map(r=>-(r.revokeGross||0)), C.red),
    line('In banks', Rf.map(r=>r.pending), C.fg2, {ax:'y1'})],
    {stacked:true, zero:false, y:n0, y1:v=>fmt.n(v,1), tf:v=>fmt.sgn(v)+fmt.n(v,2), tfy1:v=>fmt.n(v,2),
     footer:i=>{const r=Rf[i[0].dataIndex], k=Sh.indexOf(r), p=k>0?Sh[k-1]:null; return p&&p.pending!=null&&r.pending!=null?`change in banks ${fmt.sgn(r.pending-p.pending)}${fmt.n(r.pending-p.pending,2)}`:'';}}); });
reg('banks', ({Rl, ll, dl})=>{ document.getElementById('h_policy').innerHTML = `<em>${fmt.int(L.branches)}</em> branches · ${fmt.int(L.activeCharters)} charters`;
  return mk(c_policy, ll, [line('Branches', Rl.map(r=>r.branches), C.violet, {fill:true}), line('Active charters', Rl.map(r=>r.activeCharters), C.teal)], {y:n0, tf:fmt.int}); });
const CH = DATA.charters, LP = DATA.licensePeriods, CHall = CH, LPall = LP;
const inRange = (ts)=>!N || ts >= NOWTS - N*86400;   // event charts (epochs, auctions) show the events inside the selected range
reg('banks', ()=>{ const open = (L.charterRemaining||0)>0, CH = CHall.filter(c=>inRange(c.ts));
  document.getElementById('h_charter').innerHTML = `last <em>${L.charterLastSale.toFixed(2)} ETH</em> · ${open?'quote '+L.charterPriceNow.toFixed(2)+' ETH':'next '+fmt.hm(L.charterNextOpen)+' UTC at '+L.charterNextStart.toFixed(2)+' ETH'}`;
  return mk(c_charter, CH.map(c=>dm(fmt.dt(c.ts))), [line('Clearing price', CH.map(c=>c.eth), C.violet, {fill:true, pts:CH.map(c=>c.viaContract?3.5:1.8), ps:CH.map(c=>c.viaContract?'triangle':'circle')}),
    ...(open?[{type:'line', label:'Current quote', data:CH.map((c,i)=>i===CH.length-1?L.charterPriceNow:null), borderColor:C.gold, backgroundColor:C.gold, pointRadius:4, pointStyle:'rectRot', showLine:false}]:[])],
    {y:v=>v+' ETH', tf:v=>v.toFixed(2)+' ETH', title:i=>{const c=CH[i[0].dataIndex]; return 'charter #'+c.id+' · '+fmt.dt(c.ts)+(c.viaContract?' · via contract':'');}}); });
reg('banks', ()=>{ const open = (L.licenseRemaining||0)>0, LP = LPall.filter(p=>inRange(p.start));
  document.getElementById('h_license').innerHTML = `last <em>${fmt.int(L.licenseLastSale)}</em> · ${open?'quote '+fmt.int(L.licensePriceNow)+', '+L.licenseRemaining+' left':'next '+fmt.hm(L.licenseNextOpen)+' UTC at '+fmt.int(L.licenseNextStart)}`;
  return mk(c_license, LP.map(p=>dm(fmt.dt(p.start))+(new Date(p.start*1000).getUTCHours()<12?' am':' pm')), [bar('Licenses sold', LP.map(p=>p.sold), alpha(C.violet,.45), {ax:'y1'}), line('Period close price, STANDARD', LP.map(p=>p.close), C.gold)],
    {y:v=>fmt.n(v,1), y1:n0, tf:v=>fmt.int(v), after:i=>{const p=LP[i[0].dataIndex]; return [`burned ${fmt.n(p.burned,1)} STANDARD`];}}); });
reg('banks', ({Rl, ll, dl})=>{ document.getElementById('h_sb').innerHTML = `<em>${fmt.n(L.sbills.locked,2)}</em> · ${(L.sbills.rate*100).toFixed(2)}% per term`;
  return mk(c_sb, ll, [line('S-Bill principal', Rl.map(r=>r.sbLocked??r.sbills??null), C.teal, {fill:true, gaps:true}), line('Term rate', Rl.map(r=>r.sbRate??null), C.gold, {ax:'y1', gaps:true})], {y:n0, tf:v=>fmt.n(v,2), y1:v=>fmt.pct(v,1), ymin:0}); });
reg('banks', ({Rl, ll, dl})=>{ document.getElementById('h_mult').innerHTML = `<em>${fmt.x(L.multiplier)}</em> · resolution fee ${fmt.pct(L.exitFeeNow,1)}`;
  return mk(c_mult, ll, [line('Issuance multiplier', Rl.map(r=>r.multiplier??null), C.gold, {x:{stepped:true}}), line('Resolution fee', Rl.map(r=>r.exitFee??null), C.orange, {ax:'y1'})],
    {y:v=>v.toFixed(2)+'×', tf:v=>v.toFixed(2), y1:v=>fmt.pct(v,0), ymin:0, ymax:1.3}); });

// ---------- top bankers, daily log, reconciliation ----------
let LD = DATA.leaders || {rows:[]}, leadOpen = false;
const who = (l)=>`<a href="https://robin.etherscan.io/address/${l.owner}" target="_blank" rel="noopener" style="text-decoration:none">${l.ens ? l.ens : l.owner.slice(0,6)+'…'+l.owner.slice(-4)}</a>`;
const rkc = (l)=>l.prevRank==null ? '<td class="mut">–</td>' : (l.prevRank-l.rank===0 ? '<td class="mut">0</td>' : `<td class="${l.prevRank-l.rank>0?'pos':'neg'}">${l.prevRank-l.rank>0?'▲':'▼'} ${Math.abs(l.prevRank-l.rank)}</td>`);
function renderLeaders(){
  document.getElementById('h_lead').innerHTML = `<em>${fmt.int(LD.bankers)}</em> bankers · ${fmt.int(LD.banks)} banks · ${fmt.int(LD.branches)} branches`;
  document.getElementById('t_lead').innerHTML = '<tr><th>Rank</th><th class="l">Banker</th><th>Banks</th><th>Branches</th><th>Share of branches</th><th>Share of emissions, this epoch</th><th>Emissions, this epoch</th><th>Emissions, lifetime</th><th>Rank change</th></tr>' +
    LD.rows.map((l,i)=>`<tr class="${i>=10?'more':''}"><td>${l.rank}</td><td class="l ${l.ens?'':'addr'}">${who(l)}</td><td>${l.banks}</td><td>${l.branches}</td><td>${fmt.pct(l.branchShare,1)}</td><td>${l.epochShare!=null?fmt.pct(l.epochShare,2):'–'}</td><td>${fmt.int(l.epochEmissions)}</td><td>${fmt.int(l.lifetimeEmissions)}</td>${rkc(l)}</tr>`).join('');
  document.getElementById('t_lead').classList.toggle('open', leadOpen);
  document.getElementById('lead_more').textContent = leadOpen ? 'Top 10' : 'Top 25';
}
document.getElementById('lead_more').addEventListener('click',()=>{leadOpen=!leadOpen; renderLeaders();});
const cols = [
  ['Date', r=>r.date, r=>r.date],
  ['Price', r=>r.price!=null?'$'+r.price.toFixed(4):'–', r=>r.price],
  ['Market cap', r=>fmt.usd(r.mcTotal), r=>r.mcTotal],
  ['Market cap, in wallets', r=>fmt.usd(r.mcFloat), r=>r.mcFloat],
  ['Circulating supply', r=>fmt.n(r.supply,2), r=>r.supply],
  ['In wallets', r=>fmt.n(r.float,2), r=>r.float],
  ['Revenue', r=>fmt.usd(inc(r),1), r=>inc(r)],
  ['STANDARD trading fees', r=>fmt.usd(tr(r),1), r=>tr(r)],
  ['LP fees', r=>fmt.usd(r.spFee||0,1), r=>r.spFee||0],
  ['Launchpad revenue', r=>fmt.usd(lpp(r),1), r=>lpp(r)],
  ['Launchpad, reward pool', r=>fmt.usd(lpot(r),1), r=>lpot(r)],
  ['Launchpad, creators', r=>fmt.usd(lcr(r),1), r=>lcr(r)],
  ['Launchpad volume', r=>fmt.usd(lvol(r),1), r=>lvol(r)],
  ['Charter sales', r=>fmt.usd(chs(r),1), r=>chs(r)],
  ['Routed, ETH', r=>(r.routedEth||0).toFixed(1), r=>r.routedEth||0],
  ['Charters sold', r=>r.chartersSold?`${r.chartersSold} @ ${(r.charterEth/r.chartersSold).toFixed(2)}`:'–', r=>r.chartersSold||0],
  ['License close', r=>r.licClose?fmt.int(r.licClose):'–', r=>r.licClose||''],
  ['Licenses', r=>fmt.int(r.licCount||0), r=>r.licCount||0],
  ['Branches', r=>fmt.int(r.branches), r=>r.branches],
  ['Charters', r=>fmt.int(r.activeCharters), r=>r.activeCharters],
  ['Multiplier', r=>r.multiplier!=null?r.multiplier.toFixed(2)+'×':'–', r=>r.multiplier],
  ['Issued to banks', r=>fmt.n(r.issuance||0,1), r=>r.issuance||0],
  ['Buyback burn', r=>fmt.n(r.burnBuyback||0,1), r=>r.burnBuyback||0],
  ['POL buyback', r=>fmt.n(r.toIncentives||0,1), r=>r.toIncentives||0],
  ['Deposited by bankers', r=>fmt.n(r.deposits||0,1), r=>r.deposits||0],
  ['Withdrawn by closing branches', r=>fmt.n(r.wdGross||0,1), r=>r.wdGross||0],
  ['In banks', r=>fmt.n(r.pending,2), r=>r.pending],
  ['Resolution fee', r=>fmt.pct(r.exitFee,1), r=>r.exitFee],
  ['S-Bill rate', r=>r.sbRate!=null?(r.sbRate*100).toFixed(2)+'%':'–', r=>r.sbRate==null?'':r.sbRate],
  ['S-Bill principal', r=>fmt.n(r.sbLocked!=null?r.sbLocked:r.sbills,2), r=>r.sbLocked!=null?r.sbLocked:r.sbills],
  ['Team STANDARD', r=>fmt.n(r.teamStd,2), r=>r.teamStd],
  ['Pool volume', r=>fmt.usd(r.spVol||0,1), r=>r.spVol||0],
  ['Served by reserve', r=>fmt.usd(served(r),1), r=>served(r)],
  ['Reserve', r=>r.reserveUsd!=null?fmt.usd(r.reserveUsd):'–', r=>r.reserveUsd??''],
  ['Price to backing', r=>pbOf(r)!=null?pbOf(r).toFixed(2)+'×':'–', r=>pbOf(r)??''],
  ['Net buying', r=>r.mktNet!=null?fmt.sgn(-r.mktNet)+fmt.n(-r.mktNet,1):'–', r=>r.mktNet!=null?-r.mktNet:''],
  ['Depth ±2%, bid', r=>r.bid2!=null?fmt.usd(r.bid2,1):'–', r=>r.bid2??''],
  ['Regime', r=>regime[r.date]===undefined?'–':regime[r.date]?'expansion':'contraction', r=>regime[r.date]===undefined?'':regime[r.date]?'expansion':'contraction'],
];
let logOpen = false;
function renderLog(){
  const logRows = Sh.slice().reverse();
  document.getElementById('h_log').innerHTML = `${logRows.length} days`;
  document.getElementById('t_log').innerHTML = '<tr>'+cols.map(c=>'<th>'+c[0]+'</th>').join('')+'</tr>' +
    logRows.map((r,i)=>`<tr class="${r.date===L.date?'today':''}${i>=14?' more':''}">`+cols.map(c=>'<td>'+c[1](r)+'</td>').join('')+'</tr>').join('');
  document.getElementById('t_log').classList.toggle('open', logOpen);
  document.getElementById('more').textContent = logOpen ? 'Last 14 days' : `All ${logRows.length} days`;
}
document.getElementById('more').addEventListener('click',()=>{logOpen=!logOpen; renderLog();});
document.getElementById('csv').addEventListener('click',()=>{
  const esc = v=>{v=v==null?'':String(v); return /[",\n]/.test(v)?'"'+v.replace(/"/g,'""')+'"':v;};
  const csv = [cols.map(c=>esc(c[0])).join(',')].concat(Sh.map(r=>cols.map(c=>esc(c[2](r))).join(','))).join('\n');
  const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([csv],{type:'text/csv'})); a.download = 'standard-reserve-daily-'+L.date+'.csv'; a.click();
});
const fl = (r,i)=>{const p=i>0?Sh[i-1]:null; const mint=(r.mint||0)+(r.genesisMint||0), dep=r.depositBurn||0, bb=(r.burn||0)-dep;
  const dP=p?r.pool-p.pool:null, mkt=r.mktNet!=null?r.mktNet:null, prot=dP!=null&&mkt!=null?dP-mkt:null;
  return {p, dS:p?r.supply-p.supply:null, dP, dI:p?r.incentives-p.incentives:null, dF:p?r.float-p.float:null, mint, dep, bb, mkt, prot};};
const scl = (v,inv)=>v==null?'<td>–</td>':`<td class="${(inv?-v:v)>0?'pos':(inv?-v:v)<0?'neg':'mut'}">${Math.abs(v)<0.5?'0':fmt.sgn(v)+fmt.n(v,2)}</td>`;
let floatOpen = false;
function renderFloat(){
  const frows = Sh.map((r,i)=>({r, ...fl(r,i)})).reverse();
  document.getElementById('t_float').innerHTML = '<tr><th>Date</th><th>Circulating supply</th><th>Change</th><th>+ Withdrawals</th><th>− Deposits</th><th>− Burned</th><th>Protocol pool</th><th>Change</th><th>+ Market sales</th><th>− Protocol</th><th>Incentives vault, change</th><th>In wallets</th><th>Change</th><th>%</th><th>Price</th></tr>' +
    frows.map((x,i)=>`<tr class="${x.r.date===L.date?'today':''}${i>=10?' more':''}"><td>${x.r.date}</td><td>${fmt.n(x.r.supply,2)}</td>${scl(x.dS)}${scl(x.mint)}${scl(-x.dep)}${scl(-x.bb)}<td>${fmt.n(x.r.pool,2)}</td>${scl(x.dP,true)}${scl(x.mkt,true)}${scl(x.prot,true)}${scl(x.dI,true)}<td>${fmt.n(x.r.float,2)}</td>${scl(x.dF)}<td class="${x.dF>0?'pos':x.dF<0?'neg':''}">${x.p?fmt.sgn(x.dF)+fmt.pct(x.dF/x.p.float,2):'–'}</td><td>${x.r.price!=null?'$'+x.r.price.toFixed(4):'–'}</td></tr>`).join('');
  document.getElementById('t_float').classList.toggle('open', floatOpen);
  document.getElementById('fmore').textContent = floatOpen ? 'Last 10 days' : `All ${frows.length} days`;
}
document.getElementById('fmore').addEventListener('click',()=>{floatOpen=!floatOpen; renderFloat();});

// ---------- reconciliation and open data ----------
const RC = DATA.recon || []; let QA = null;
const rcUnit = (r, v, sg)=>{ if (v==null || !isFinite(v)) return '–'; const s = sg && v>0 ? '+' : '';
  if (r.unit==='USD') return s+fmt.usd(v); if (r.unit==='STANDARD') return s+fmt.n(v,2); if (r.unit==='s') return s+Math.round(v/60)+' min';
  if (r.unit) return s+(Math.abs(v)<1e-4 ? '0' : fmt.n(v,4))+' '+r.unit; if (/^price/.test(r.id)) return '$'+v.toFixed(4); if (r.id==='mcap_dexscreener') return fmt.usd(v); return fmt.int(v); };
const rcResidual = r=>(r.abs && r.ref===0) || /^reserve_(lp|today)$|_fresh$/.test(r.id);
function renderRecon(){
  const okN = RC.filter(r=>r.ok).length;
  document.getElementById('h_recon').innerHTML = `<em>${okN} of ${RC.length}</em> within tolerance` + (QA ? ` · ${fmt.int(QA.passed)} of ${fmt.int(QA.checked)} checks passed ${QA.checkedAt.slice(5)} UTC` : '');
  document.getElementById('t_recon').innerHTML = '<tr><th class="l">Figure</th><th>Monitor</th><th>Independent</th><th class="l">Independent source</th><th>Gap</th><th>Tolerance</th><th>Status</th></tr>' +
    RC.map(r=>{ const res = rcResidual(r), fr = /_fresh$/.test(r.id);
      const gap = r.ours==null||r.ref==null ? '–' : fr ? (r.ok?'none':'missing') : r.abs ? rcUnit(r, r.diff, true) : (r.ours/r.ref-1>=0?'+':'−')+(Math.abs(r.ours/r.ref-1)*100).toFixed(Math.abs(r.ours/r.ref-1)<0.001?3:2)+'%';
      const tol = fr ? '–' : r.abs ? '±'+rcUnit(r, r.tol) : '±'+(r.tol*100).toFixed(r.tol<0.001?2:1)+'%';
      const st = r.ok ? '<span class="chip exp">within</span>' : r.gate ? '<span class="chip con">outside</span>' : '<span class="chip">outside, watched</span>';
      return `<tr><td class="l">${r.label}</td><td>${res?'–':rcUnit(r, r.ours)}</td><td>${res?'–':rcUnit(r, r.ref)}</td><td class="l mut">${r.source}</td><td>${gap}</td><td class="mut">${tol}</td><td>${st}</td></tr>`; }).join('');
}
const FILES = [['api/daily.csv','Every daily observation on this page'], ['api/daily.json','The same, with field definitions'], ['api/summary.json','Every tile and panel headline, by tab'],
  ['api/recon.json','The reconciliation above'], ['api/qa.json','The last publication check, result by check']];
function renderFiles(){ document.getElementById('files').innerHTML = FILES.map(f=>`<div><a href="${f[0]}" target="_blank" rel="noopener">${f[0].slice(4)}</a></div><div>${f[1]}</div>`).join('');
  document.getElementById('h_files').innerHTML = 'every compile'; }
// the open data files are written from these functions, so every figure in them is the page's own
const API_FIELDS = [
  ['date', 'UTC day; the last row is the current, partial day', r=>r.date],
  ['price', 'STANDARD price in USD: GeckoTerminal daily close, the current day DexScreener live', r=>r.price],
  ['marketCap', 'Price times circulating supply, USD (as the protocol’s site and DexScreener show it)', r=>r.mcTotal],
  ['marketCapInWallets', 'Price times the STANDARD in wallets, USD', r=>r.mcFloat],
  ['circulatingSupply', 'Circulating supply, every STANDARD minted (ERC-20 total supply), the protocol’s own definition', r=>r.supply],
  ['inWallets', 'Circulating supply less protocol liquidity and the Incentives vault, STANDARD', r=>r.float],
  ['reserveUsd', 'Reserve assets at the day’s close, USD', r=>r.reserveUsd],
  ['backingPerToken', 'Reserve assets per STANDARD in wallets, USD', bkOf],
  ['priceToBacking', 'Market cap in wallets over reserve assets', pbOf],
  ['revenueUsd', 'What the protocol keeps: STANDARD trading fees, LP fees, the launchpad’s 50% and charter sales, USD', inc],
  ['standardTradingFeesUsd', 'STANDARD trading fees, the buy and sell tax, routed at settlement and spread over the epoch’s days, USD', tr],
  ['lpFeesUsd', 'LP fees earned by the reserve’s pool positions, USD', r=>r.spFee||0],
  ['launchpadRevenueUsd', 'The protocol’s 50% of the 1% launchpad base fee, USD', lpp],
  ['launchpadRewardPoolUsd', 'The King of the Markets reward pool’s 20%, USD', lpot],
  ['launchpadCreatorsUsd', 'Creators’ 30% plus hook-module fees, USD', lcr],
  ['launchpadVolumeUsd', 'Launchpad trading volume implied by the fee Safe’s 0.7%, USD', lvol],
  ['charterSalesUsd', 'Charter auction proceeds, USD', chs],
  ['volumeServedUsd', 'Volume served by the reserve’s own liquidity, USD', served],
  ['poolVolumeUsd', 'All volume in the reserve’s pools, USD', r=>r.spVol||0],
  ['launchpadRoutedLpFeesUsd', 'LP fees from swaps executed by the launchpad routers, USD (a floor)', r=>r.spFeeLpad||0],
  ['branches', 'Branches open at the day’s end', r=>r.branches],
  ['activeCharters', 'Active charters at the day’s end', r=>r.activeCharters],
  ['multiplier', 'Issuance multiplier in force', r=>r.multiplier],
  ['issued', 'STANDARD issued to bankers’ ledgers', r=>r.issuance||0],
  ['burned', 'STANDARD burned: licenses, the burned half of resolution and revocation fees, buybacks and other burns', burnAll],
  ['inBanks', 'STANDARD in banks: ledger balances owed to bankers, minted only on withdrawal, at the day’s end', r=>r.pending],
  ['resolutionFee', 'Exit fee on withdrawals at the day’s close', r=>r.exitFee],
  ['sbillsLocked', 'STANDARD locked in S-Bills at the day’s close', r=>r.sbLocked??r.sbills],
  ['sbillRate', 'S-Bill term rate at the day’s close', r=>r.sbRate],
  ['netBuying', 'STANDARD bought from the protocol pool less STANDARD sold into it; negative is net selling', r=>r.mktNet!=null?-r.mktNet:null],
  ['depositedByBankers', 'STANDARD bankers deposited into their banks from their wallets', r=>r.deposits||0],
  ['withdrawnByClosingBranches', 'STANDARD withdrawn from banks by closing branches, before the exit fee', r=>r.wdGross||0],
  ['bidDepth2pctUsd', 'ETH, in USD, that sellers receive taking the price down 2% at the close', r=>r.bid2],
  ['regime', 'Epoch regime: expansion or contraction', r=>regime[r.date]===undefined?null:regime[r.date]?'expansion':'contraction'],
];
const r6 = v=>typeof v==='number' ? (isFinite(v) ? +v.toPrecision(10) : null) : v ?? null;
window.SRM_EXPORT = ()=>({compiled:COMPILED+' UTC', source:'https://standardrsvmonitor.github.io/', fields:Object.fromEntries(API_FIELDS.map(f=>[f[0], f[1]])),
  rows:Sh.map(r=>Object.fromEntries(API_FIELDS.map(f=>[f[0], r6(f[2](r))]))), epochs:E});
function renderAll(){ renderKpis(); renderStatic(); renderBridge(); renderLeaders(); renderLog(); renderFloat(); renderRecon(); renderFiles(); }
fetch('api/qa.json', {cache:'no-store'}).then(r=>r.ok?r.json():null).then(q=>{ if (q && q.checked) { QA = q; renderRecon(); } }).catch(()=>{});
renderAll();
document.querySelectorAll('#tabs button[data-t]').forEach(b=>b.addEventListener('click',()=>{ history.replaceState(null,'','#'+b.dataset.t); show(b.dataset.t); window.scrollTo({top:0}); }));
document.querySelectorAll('#range button').forEach(b=>b.addEventListener('click',()=>{N=+b.dataset.n; document.querySelectorAll('#range button').forEach(x=>x.classList.toggle('on',x===b)); redrawAll();}));
window.addEventListener('hashchange', ()=>show(location.hash.slice(1)));
// links from table headers or elsewhere to a panel id switch to its tab first
document.addEventListener('click', e=>{const a=e.target.closest('a[href^="#p_"]'); if(!a) return; const el=document.querySelector(a.getAttribute('href')); if(!el) return; e.preventDefault(); show(el.closest('.tab').id.slice(2)); el.scrollIntoView({behavior:'smooth'});});
show((location.hash||'#overview').slice(1));

// ---------- live overlay ----------
// Between compiles the browser replays every block after the compile block. It reads the indexer's snapshot, takes that snapshot's block
// as the reference, reads balances there over the RPC, replays STANDARD transfer logs, charter purchases and indexer events up to it with
// the same rules as the compiler, and reads DexScreener's price. Tiles, the growth monitor, today's chart points and table rows, the supply
// reconciliation, the auctions and the top bankers then describe one block. Pool swaps, LP fees, the launchpad and the reserve stay as compiled.
const COMPILED = '__ASOF__', STD_ADDR = '0x88ad8DdF1E3898412146a534538d418c6F8A9062';
const RPCU = 'https://rpc.mainnet.chain.robinhood.com', IXU = 'https://indexer.standardreserve.xyz/v1/';
const TRF = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef', PURCH = '0x1c54748c22f6bf384e0cf9a6a4dfbc630c9ac343ba8a88a5769508bd2da18e50';
const A = DATA.addrs || null, TIP = DATA.tip, TIPTS = DATA.tipTs || DATA.pulledAt;
const clone = o=>JSON.parse(JSON.stringify(o));
const BASE = {L:clone(L), row:clone(Sh[Sh.length-1]||{}), n:Sh.length, sn:S.length, ch:clone(CH), lp:clone(LP), ld:clone(LD)};
const WN = A ? {[A.zero]:'zero', [A.poolManager]:'pool', [A.contractionVault]:'contraction', [A.polBuyback]:'polBuyback', [A.incentivesVault]:'incentives',
  [A.sbills]:'sbills', [A.centralBank]:'bank', [A.teamWallet]:'team', [A.reserveSafe]:'safe', [A.polManager]:'polManager', [A.feeSplitter]:'feeSplitter', [A.taxHook]:'taxHook', [A.expansionVault]:'expansion'} : {};
const MARKET = new Set(['team','other']);
const pad = a=>'0x'+a.slice(2).toLowerCase().padStart(64,'0');
const big = x=>Number(BigInt(x))/1e18;
function restore(){
  Object.keys(L).forEach(k=>{if(!(k in BASE.L)) delete L[k];}); Object.assign(L, clone(BASE.L));
  Sh.length = BASE.n; S.length = BASE.sn; const R0 = Sh[BASE.n-1];
  if (R0) { Object.keys(R0).forEach(k=>{if(!(k in BASE.row)) delete R0[k];}); Object.assign(R0, clone(BASE.row)); }
  CH.length = 0; CH.push(...clone(BASE.ch)); LP.length = 0; LP.push(...clone(BASE.lp)); LD = clone(BASE.ld);
}
async function rpc(calls){
  const r = await fetch(RPCU, {method:'POST', headers:{'content-type':'application/json'}, body:JSON.stringify(calls.map((c,i)=>({jsonrpc:'2.0', id:i, method:c[0], params:c[1]})))});
  const j = await r.json(), out = []; (Array.isArray(j)?j:[j]).forEach(x=>{out[x.id] = x.result;}); return out;
}
async function logsTo(B, q){
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
  const F = {}, f = (d)=>F[d] || (F[d] = {}), add = (d,k,v)=>{const o=f(d); o[k]=(o[k]||0)+v;};
  const seen = new Set();
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
  const R0 = Sh[Sh.length-1], dLive = fmt.dt(+s.blockTimestamp), rows = [R0];
  for (let t=Date.parse(R0.date+'T00:00:00Z')/1000+86400; fmt.dt(t)<=dLive; t+=86400) { const r = {date:fmt.dt(t), eth:R0.eth}; S.push(r); Sh.push(r); rows.push(r); }
  rows.forEach(r=>{ Object.entries(F[r.date]||{}).forEach(([k,v])=>{ if(k==='licClose') r[k]=v; else r[k]=(r[k]||0)+v; });
    r.burnBuyback = (r.burn_contraction||0)+(r.burn_polManager||0)+(r.burn_sbills||0); r.depositBurn = r.deposits||0;
    r.burnOther = Math.max(0, (r.burn_other||0)+(r.burn_bank||0)-(r.deposits||0)); });
  const tNow = +s.blockTimestamp, iss = (a,b)=>{ if(b<=a) return 0; const c=Math.min(Math.max(L.epochStart,a),b); return L.baseIssuance*(BASE.L.multiplier*(c-a)+L.multiplier*(b-c))/86400; };
  rows.forEach(r=>{const ds=Date.parse(r.date+'T00:00:00Z')/1000, a=iss(Math.max(ds,TIPTS), Math.min(ds+86400,tNow)); r.issuance=(r===R0?(BASE.row.issuance||0):0)+a; r._iss=a;});
  if (rows.length>1) { const x=F[R0.date]||{};
    R0.pending=(BASE.row.pending||0)+R0._iss+(x.deposits||0)+(x.exitFeeRedis||0)+(x.revokeFeeBurn||0)-(x.licBurn||0)-(x.wdGross||0)-(x.revokeGross||0); }
  let lv = {supply:big(st[0]), pool:big(st[1]), incentives:big(st[2]), sbills:big(st[3]), teamStd:big(st[4])};
  for (let k=rows.length-1; k>=0; k--) { const r=rows[k], x=F[r.date]||{}; Object.assign(r, lv); r.float = r.supply-r.pool-r.incentives;
    lv = {supply:lv.supply-((x.mint||0)+(x.genesisMint||0)-(x.burn||0)), pool:lv.pool-((x.poolIn||0)+(x.genesisPool||0)-(x.poolOut||0)),
          incentives:lv.incentives-((x.toIncentives||0)-(x.fromIncentives||0)), sbills:lv.sbills-((x.sbillIn||0)-(x.sbillOut||0)), teamStd:lv.teamStd-((x.teamIn||0)-(x.teamOut||0))}; }
  const RL = rows[rows.length-1];
  if (RL.reserveUsd==null) { RL.reserveUsd = L.reserve.totalUsd; RL.reserveParts = BASE.row.reserveParts; }
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
    if (Array.isArray(s.withdrawnByDay)) { const w7=sum(s.withdrawnByDay.map(W)); const P=w7/Math.max(L.pending+w7,1e7); L.w7=w7; L.exitPressure7d=P; L.exitFeeNow=0.02+0.58*Math.pow(Math.min(P/0.10,1),2); }
    if (sb && sb.current) { const q=sb.current, dps=q.drifting?W(q.driftPerSecond||'0'):0, cap=q.ceiling?W(q.ceiling):1;
      L.sbills.rate=Math.min(cap, W(q.rate)+dps*Math.max(0, I(s.blockTimestamp)-(q.rateUpdatedAt||I(s.blockTimestamp)))); L.sbills.locked=W(q.locked); L.sbills.principal=W(q.principal||q.locked);
      if(q.floor) L.sbills.floor=W(q.floor); if(q.ceiling) L.sbills.ceiling=W(q.ceiling); }
    if (dx && dx[0] && dx[0].priceUsd) { const p=dx[0]; L.price=parseFloat(p.priceUsd); L.priceChange24h=(p.priceChange||{}).h24; L.vol24=(p.volume||{}).h24; L.poolLiqUsd=(p.liquidity||{}).usd; }
    if (A && TIP) { try { await replay(s, I(s.blockNumber)); } catch(e) { restoreRows(); console.warn('replay unavailable', e); } }
    if (lb && Array.isArray(lb.bankers)) {
      const ens = {}; (BASE.ld.rows||[]).forEach(r=>{ens[r.owner]=r.ens;});
      const B_ = x=>BigInt(x||'0'), bk = lb.bankers.slice().sort((a,b)=>(+b.branches||0)-(+a.branches||0) || Number(B_(b.epochEmissions)-B_(a.epochEmissions)) || Number(B_(b.lifetimeEmissions)-B_(a.lifetimeEmissions)));
      const tb = sum(bk.map(r=>+r.branches||0)) || 1, te = sum(bk.map(r=>W(r.epochEmissions||'0'))) || 1;
      LD = {bankers:bk.length, banks:sum(bk.map(r=>+r.banks||0)), branches:tb, rows:bk.slice(0,25).map((r,i)=>({rank:i+1, owner:r.owner.toLowerCase(), ens:ens[r.owner.toLowerCase()]||'',
        banks:+r.banks||0, branches:+r.branches||0, branchShare:(+r.branches||0)/tb, epochShare:W(r.epochEmissions||'0')/te, epochEmissions:W(r.epochEmissions||'0'), lifetimeEmissions:W(r.lifetimeEmissions||'0'), prevRank:(r.previousRank||{}).epoch}))};
    }
    NOWTS = now; LIVE = true; LIVEHM = new Date(I(s.blockTimestamp)*1000).toISOString().slice(11,16); LIVEB = I(s.blockNumber);
    renderAll(); redrawAll();
  }catch(e){ console.warn('live overlay unavailable, showing compiled figures', e); }
}
function restoreRows(){
  const keep = {}; ['branches','multiplier','epoch','epochStart','epochEnd','epochNetFlow','previousEpochFlow','positiveStreak','pending','cumulativeIssued','cumulativeRecycled',
    'activeCharters','burnedCharters','chartersMinted','licensePriceNow','licenseLastSale','licenseFloor','licenseDayStart','licenseSoldToday','licenseCap','licenseRemaining',
    'charterPriceNow','charterLastSale','charterFloor','charterDayStart','charterSoldToday','charterCap','charterRemaining','licenseNextOpen','licenseNextStart','charterNextOpen',
    'charterNextStart','w7','exitPressure7d','exitFeeNow','price','priceChange24h','vol24','poolLiqUsd'].forEach(k=>{keep[k]=L[k];});
  const sbk = clone(L.sbills); restore(); Object.assign(L, keep); L.sbills = sbk;
}
goLive(); setInterval(goLive, 300000);
</script>
</body></html>
"""

html = (TEMPLATE.replace("__HERO__", HERO_IMG).replace("__NAV__", NAV).replace("__BODY__", BODY).replace("__ASOFHM__", built.strftime("%H:%M")).replace("__ASOF__", built.strftime("%Y-%m-%d %H:%M"))
        .replace("__DATA__", json.dumps({k: v for k, v in data.items() if k != "swaps"}, separators=(",", ":"))))
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html"), "w").write(html)
print("index.html", len(html) // 1024, "KB")
