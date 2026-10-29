#!/usr/bin/env python3
"""The deploy gate. Exit 1 when anything below fails; the workflow then keeps the last good page up and opens an issue.

  render        the page builds without script errors, every tab has its tiles, every chart has data
  consistency   every figure shown in more than one place reads the same
  recompute     headline figures match an independent recomputation from data/dash.json
  reconcile     each rebuilt figure agrees with an independent reading of the same thing (data/dash.json "recon", gate items)
  data          the compile is fresh and the last complete day has every core field
  drift         no figure for a day three or more days old has moved since the published page, beyond tolerance, unless qa/accept.json allows it
  rules         the house style, written down: every chart follows the range selector, no dashed series lines, legends bottom-centred, tooltips
                in index mode, no colons in titles, no banned words, no decorative marks, every panel explains its method, nothing clipped, no
                sideways page scroll, one compile time everywhere

usage: qa/check.py <render.json> <dash.json> [--live URL] [--accept qa/accept.json] [--out DIR] [--api DIR]
Writes DIR/report.json and DIR/report.md (DIR defaults to qa/out); with --api, also the published qa.json and recon.json."""
import sys, os, re, json, datetime as dt, urllib.request, argparse

ap = argparse.ArgumentParser(); ap.add_argument("render"); ap.add_argument("dash"); ap.add_argument("--live"); ap.add_argument("--accept"); ap.add_argument("--api"); ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "out"))
A = ap.parse_args()
V = json.load(open(A.render)); D = json.load(open(A.dash)); DK = V["desktop"]; T = DK.get("tabs", {})
RES = []                                       # [section, name, ok, detail, severity]  severity: fail | warn
def add(sec, name, ok, detail="", sev="fail"): RES.append({"section": sec, "check": name, "ok": bool(ok), "detail": detail, "severity": sev})

# ---------------------------------------------------------------- render
add("render", "page renders without script errors", not DK.get("errors") and not DK.get("fatal"), "; ".join(map(str, DK.get("errors") or []))[:600])
for w, r in V.get("layouts", {}).items(): add("render", f"page renders at {w}px without script errors", not r.get("errors") and not r.get("fatal"), "; ".join(map(str, r.get("errors") or []))[:400])
for t, X in T.items():
    if t != "data": add("render", f"{t}: six tiles", len(X.get("kpis", [])) == 6, f"{len(X.get('kpis', []))} tiles")
    for cid, c in (X.get("charts") or {}).items():
        add("render", f"{t}: chart {cid} has data", bool(c and c["labels"] and any(s["nonnull"] for s in c["sets"])), "" if c else "chart missing")

# ---------------------------------------------------------------- consistency (cross-panel)
def eq(name, *vals):
    ok_ = len(set(vals)) == 1 and vals[0] not in (None, "", "–")
    add("consistency", name, ok_, "" if ok_ else " | ".join(map(str, vals)))
def kpi(tab, label): return next((k for k in T[tab]["kpis"] if k[0] == label), None)
def kv(tab, label): k = kpi(tab, label); return k[1] if k else None
def head(tab, title): return T[tab]["heads"].get(title) or ""
def gm(label):
    for r in T["overview"]["tables"]["t_gm"]:
        if r and len(r) > 1 and r[0].replace("7d", "").strip() == label: return r   # group header rows have one cell
    return [None, None]
def em(tab, title, i=0):
    m = re.findall(r"(−?\+?\$?[\d,.]+[KMB%×]?)", head(tab, title)); return m[i] if len(m) > i else None
def rx(pat, s, g=1):
    m = re.search(pat, s or ""); return m.group(g) if m else None
def usd(v, d=None):
    s = "−" if v < 0 else ""; v = abs(v)
    if v >= 1e9: return f"{s}${v/1e9:.{2 if d is None else d}f}B"
    if v >= 1e6: return f"{s}${v/1e6:.{2 if d is None else d}f}M"
    if v >= 1e3: return f"{s}${v/1e3:.{1 if d is None else d}f}K"
    return f"{s}${v:.{2 if d is None else d}f}"
def row(tab, tid, first):
    return next((r for r in T[tab]["tables"].get(tid, []) if r and r[0] == first), [None] * 20)
try:
    alloc = [x for x in T["revenue"]["blocks"].get("alloc", []) if x]
    eq("price", kv("overview", "STANDARD price"), kv("token", "STANDARD price"), gm("STANDARD price")[1], em("token", "Price and market capitalization, daily", 0))
    eq("market cap", kv("overview", "Market cap"), kv("token", "Market cap"), gm("Market cap")[1], em("token", "Price and market capitalization, daily", 1))
    eq("market cap, in wallets", kv("token", "Market cap, in wallets"), em("token", "Price and market capitalization, daily", 2), rx(r"in wallets (\S+)", (kpi("overview", "Market cap") or [""] * 3)[2]),
       gm("Market cap, in wallets")[1])
    eq("reserve assets", kv("overview", "Reserve assets"), kv("reserve", "Reserve assets"), gm("Reserve assets")[1], em("overview", "Reserve assets by component, daily"),
       em("reserve", "Reserve assets by component, daily"), row("reserve", "t_resd", "Total")[1])
    eq("price to backing", kv("reserve", "Price to backing"), gm("Price to backing")[1], em("overview", "Price and backing per token, daily"), em("reserve", "Price to backing, daily"),
       rx(r"([\d.]+×) P/B", (kpi("overview", "Reserve assets") or [""] * 3)[2]))
    eq("backing per token", kv("reserve", "Backing per token"), gm("Backing per STANDARD in wallets")[1], rx(r"backing (\$[\d.]+)", head("reserve", "Price to backing, daily")))
    eq("revenue, 7d", kv("overview", "Revenue, 7d"), kv("revenue", "Revenue, 7d"), gm("Revenue")[1], em("revenue", "Revenue by stream, daily"))
    eq("trading fees, 7d", kv("revenue", "Trading fees, 7d"), gm("Trading fees")[1])
    eq("LP fees, 7d", kv("revenue", "LP fees, 7d"), kv("liquidity", "LP fees, 7d"), gm("LP fees")[1], em("liquidity", "LP fees by pool, daily"),
       row("liquidity", "t_pools", "Total")[5], alloc[1] if len(alloc) > 1 else None)
    eq("launchpad revenue, 7d", kv("revenue", "Launchpad revenue, 7d"), kv("launchpad", "Launchpad revenue, 7d"), gm("Launchpad revenue")[1],
       alloc[alloc.index("Launchpad fee Safe") + 1] if "Launchpad fee Safe" in alloc else None)
    eq("charter sales, 7d", kv("revenue", "Charter sales, 7d"), gm("Charter sales")[1], rx(r"charter sales (\S+)", head("revenue", "Revenue by stream, daily")))
    eq("volume served, 7d", kv("liquidity", "Volume served, 7d"), gm("Volume served by the reserve")[1], em("liquidity", "Volume served by the reserve, by pool, daily"),
       row("liquidity", "t_pools", "Total")[4], rx(r"of (\S+) ·", head("liquidity", "Pool volume by counterparty, daily")))
    eq("organic share", kv("liquidity", "Organic share of volume"), em("liquidity", "Pool volume by counterparty, daily"), row("liquidity", "t_cpty", "All pools")[1])
    eq("launchpad volume, 7d", kv("launchpad", "Launchpad volume, 7d"), gm("Launchpad trading volume")[1])
    eq("launchpad revenue, to date", kv("launchpad", "Launchpad revenue, to date"), rx(r"protocol (\S+)", head("launchpad", "Launchpad fees by recipient, daily")))
    eq("launchpad fees, to date", rx(r"of (\S+) fees", (kpi("launchpad", "Launchpad revenue, to date") or [""] * 3)[2]), em("launchpad", "Launchpad fees by recipient, daily"))
    kp = T["launchpad"]["blocks"].get("kotm_pool", [])
    eq("reward pool fees", rx(r"(\S+) from fees", (kpi("launchpad", "Reward pool") or [""] * 3)[2]), kp[kp.index("Reward pool share of fees, 20%") + 1] if "Reward pool share of fees, 20%" in kp else None)
    eq("capital in pools", kv("liquidity", "Capital in pools"), kv("reserve", "In pools"), row("liquidity", "t_pools", "Total")[1])
    eq("branches", kv("overview", "Branches"), kv("banks", "Branches"), gm("Branches")[1], em("overview", "Branches and active charters, daily"), em("banks", "Branches and active charters, daily"),
       rx(r"([\d,]+) branches", head("banks", "Top bankers")))
    eq("active charters", kv("banks", "Active charters"), gm("Active charters")[1], rx(r"([\d,]+) charters", head("overview", "Branches and active charters, daily")),
       rx(r"([\d,]+) charters", (kpi("overview", "Branches") or [""] * 3)[2]))
    eq("in banks", kv("banks", "In banks"), gm("In banks, ledger balance")[1], em("banks", "Bank deposits, withdrawals and STANDARD in banks, daily"))
    eq("S-Bills locked", kv("banks", "S-Bills locked"), gm("S-Bills locked")[1], em("banks", "S-Bill principal and term rate, daily"))
    eq("issuance multiplier", kv("banks", "Issuance multiplier"), gm("Issuance multiplier")[1], em("banks", "Issuance multiplier and resolution fee, daily"))
    eq("resolution fee", kv("banks", "Resolution fee"), rx(r"resolution fee (\S+)", head("banks", "Bank deposits, withdrawals and STANDARD in banks, daily")))
    eq("burned", kv("token", "Burned"), em("token", "STANDARD burned by source, daily"))
    br = T["token"]["blocks"].get("bridge", [])
    eq("STANDARD in wallets", kv("token", "In wallets"), em("token", "STANDARD supply composition, daily"), br[br.index("= In wallets") + 1] if "= In wallets" in br else None)
    eq("free float", kv("token", "Free float"), br[br.index("= Free float") + 1] if "= Free float" in br else None)
    num = lambda s: float(re.sub(r"[^\d.]", "", s)) * (1e6 if s.endswith("M") else 1e3 if s.endswith("K") else 1)
    P = T["liquidity"]["tables"]["t_pools"]
    for col, nm in ((1, "position value"), (4, "volume, 7d"), (5, "fees, 7d")):
        rows_ = [num(r[col]) for r in P[1:-1]]; tot = num(P[-1][col])
        add("consistency", f"pools table rows sum to the total, {nm}", abs(sum(rows_) - tot) / tot < 0.01, f"{sum(rows_):.0f} vs {tot:.0f}")
    for r in T["liquidity"]["tables"]["t_cpty"][1:]:
        s_ = sum(int(x[:-1]) for x in r[1:]); add("consistency", f"counterparty shares sum to 100, {r[0]}", s_ == 100, str(s_))
except Exception as e:
    add("consistency", "consistency checks ran", False, f"{type(e).__name__}: {e}")

# ---------------------------------------------------------------- recompute from dash.json
L = D["live"]; S = [r for r in D["series"] if r["date"] < L["date"]]; s7 = S[-7:]
eth = lambda r: r.get("eth") or L["ethusd"]
try:
    tr = sum((r.get("tradingFeeEth") or 0) * eth(r) for r in s7); pf = sum(r.get("spFee") or 0 for r in s7); lp = sum((r.get("lpadSafe") or 0) * 5 / 7 for r in s7)
    ch = sum((r.get("charterEth") or 0) * eth(r) for r in s7)
    for nm, a, b in (("revenue, 7d", usd(tr + pf + lp + ch), kv("revenue", "Revenue, 7d")), ("trading fees, 7d", usd(tr), kv("revenue", "Trading fees, 7d")),
                     ("LP fees, 7d", usd(pf), kv("revenue", "LP fees, 7d")), ("launchpad revenue, 7d", usd(lp), kv("revenue", "Launchpad revenue, 7d")),
                     ("charter sales, 7d", usd(ch), kv("revenue", "Charter sales, 7d")),
                     ("launchpad revenue, to date", usd(sum((r.get("lpadSafe") or 0) * 5 / 7 for r in D["series"])), kv("launchpad", "Launchpad revenue, to date")),
                     ("reserve assets", usd(L["reserve"]["totalUsd"]), kv("reserve", "Reserve assets")),
                     ("market cap, in wallets", usd(L["price"] * L["float"]), kv("token", "Market cap, in wallets")),
                     ("market cap", usd(L["price"] * L["totalSupply"]), kv("token", "Market cap"))):
        add("recompute", nm, a == b, f"recomputed {a}, page {b}")
except Exception as e:
    add("recompute", "recomputation ran", False, f"{type(e).__name__}: {e}")

# ---------------------------------------------------------------- reconciliations computed by pull.py
rec = D.get("recon") or []
add("reconcile", "reconciliations present", len(rec) >= 15, f"{len(rec)} items")
for r in rec:
    gap = (f"{r['diff']:+,.4g} {r.get('unit', '')}".strip() if r.get("abs") else f"{r['rel']:.3%}") if r.get("diff") is not None else r.get("note", "missing")
    add("reconcile", r["label"], r["ok"], f"ours {r['ours']!r} · {r['source']} {r['ref']!r} · gap {gap} · tolerance {r['tol']}", "fail" if r["gate"] else "warn")

# ---------------------------------------------------------------- data freshness and completeness
pulled = dt.datetime.fromtimestamp(D["pulledAt"], dt.timezone.utc)
add("data", "live date is the compile date", L["date"] == pulled.date().isoformat(), f"live {L['date']} compiled {pulled:%Y-%m-%d %H:%M}")
Y = S[-1] if S else {}
add("data", "last complete day is yesterday", Y.get("date") == (pulled.date() - dt.timedelta(1)).isoformat(), f"last complete day {Y.get('date')}")
for k in ("price", "eth", "mcFloat", "mcTotal", "reserveUsd", "spFee", "branches", "activeCharters", "float", "supply", "pending", "multiplier", "exitFee", "issuance"):
    add("data", f"yesterday has {k}", Y.get(k) is not None, "")
for k in ("lpadSafe", "volOrg_SPCX"):
    add("data", f"yesterday has {k}", Y.get(k) is not None, "", "warn")
add("data", "compile is under two hours old", (dt.datetime.now(dt.timezone.utc) - pulled).total_seconds() < 7200, f"compiled {pulled:%Y-%m-%d %H:%M} UTC", "warn")

# ---------------------------------------------------------------- drift against the published page
CPK = ("Org", "Arb", "Bot", "Fx")
def flat(r):
    o = {}
    for k, v in r.items():
        if isinstance(v, bool) or k == "date": continue
        if isinstance(v, (int, float)): o[k] = float(v)
        elif isinstance(v, dict):
            for k2, v2 in v.items():
                if isinstance(v2, (int, float)) and not isinstance(v2, bool): o[f"{k}.{k2}"] = float(v2)
                elif isinstance(v2, dict):
                    for k3, v3 in v2.items():
                        if isinstance(v3, (int, float)): o[f"{k}.{k2}.{k3}"] = float(v3)
    return o
def tol_for(k):   # (relative, absolute floor); None = judged another way
    if re.match(r"(vol|fee)(Org|Arb|Bot|Fx)_", k): return None                        # counterparty mix: judged by share below
    if k.startswith("sell_"): return None                                              # holder groups are today's membership; the day's total, mktNet, is held
    if re.match(r"(venues|rank)_", k): return (0, 2)                                   # venue counts move as new pools are found
    if re.match(r"(chainVol|chainTvl|otherTvl|liqShare|volShare|poolVolChain)_", k): return (0.15, 1e-3)
    if re.match(r"(lpVal|holdVal|lpCost)_", k): return (0.03, 1e-3)
    if k in ("dPrice", "dSupply"): return (0.02, 1e-3)
    return (0.005, 1e-3)
def accepted(k, d, acc):
    today = dt.date.today().isoformat()
    for a in acc:
        if a.get("until", "9999") < today: continue
        if d < a.get("from", "0000") or d > a.get("to", "9999"): continue
        if any(re.fullmatch(p, k) for p in a.get("fields", [])): return a.get("why", "accepted")
    return None
if A.live:
    try:
        req = urllib.request.Request(A.live + ("&" if "?" in A.live else "?") + "qa=" + str(int(dt.datetime.now().timestamp())), headers={"User-Agent": "Mozilla/5.0"})
        page = urllib.request.urlopen(req, timeout=60).read().decode()
        m = re.search(r"const DATA = (\{.*?\});\nconst L = DATA\.live", page, re.S)
        P_ = json.loads(m.group(1)); acc = json.load(open(A.accept)) if A.accept and os.path.exists(A.accept) else []
        old = {r["date"]: r for r in P_["series"]}; cut = (dt.date.fromisoformat(L["date"]) - dt.timedelta(3)).isoformat()
        ep0 = dt.datetime.fromtimestamp(min(L.get("epochStart", 9e9), P_["live"].get("epochStart", 9e9)), dt.timezone.utc).date().isoformat()   # days in the live epoch move until it settles
        moved, waived = [], []
        for r in D["series"]:
            d = r["date"]
            if d > cut or d not in old: continue
            a, b = flat(old[d]), flat(r)
            for k in set(a) & set(b):
                if k in ("tradingFeeEth", "routedEth", "routedLive") and d >= ep0: continue
                t = tol_for(k)
                if t is None: continue
                den = max(abs(a[k]), abs(b[k]))
                if den < 1e-6 or abs(a[k] - b[k]) <= max(t[0] * den, t[1]): continue
                why = accepted(k, d, acc)
                (waived if why else moved).append(f"{d} {k} {a[k]:.6g} → {b[k]:.6g} ({(b[k] - a[k]) / den:+.2%})" + (f" [{why}]" if why else ""))
            pools = {k.split("_", 1)[1] for k in b if k.startswith("volOrg_")}
            for p in pools:                                                                  # counterparty mix: organic share may move 5 points
                ta = sum(a.get(f"vol{c}_{p}", 0) for c in CPK); tb = sum(b.get(f"vol{c}_{p}", 0) for c in CPK)
                if ta and tb:
                    sa, sb = a.get(f"volOrg_{p}", 0) / ta, b.get(f"volOrg_{p}", 0) / tb
                    if abs(sa - sb) > 0.05:
                        why = accepted(f"volOrg_{p}", d, acc)
                        (waived if why else moved).append(f"{d} organic share {p} {sa:.1%} → {sb:.1%}" + (f" [{why}]" if why else ""))
        add("drift", "figures for days three or more days old match the published page", not moved, "; ".join(moved[:25]) + (f" … {len(moved)} in all" if len(moved) > 25 else ""))
        if waived: add("drift", "moves allowed by qa/accept.json", True, "; ".join(waived[:15]) + (f" … {len(waived)} in all" if len(waived) > 15 else ""), "warn")
    except Exception as e:
        add("drift", "published page readable for the drift check", False, f"{type(e).__name__}: {e}", "warn")

# ---------------------------------------------------------------- rules (the house style)
BANNED = ["income", "recurring revenue", "revolutionary", "game-changing", "game changing", "notably", "comprehensive", "robust", "landscape", "delve", "banking", "scorecard", "thesis progress",
          "seamless", "cutting-edge", "unlock the", "leverage the power"]
JUNK = re.compile(r"\b(undefined|NaN|Infinity|null)\b|\[object")
TICKER = re.compile(r"\$STD\b|\bSTD\b|\$SRT\b|\bSRT\b")
sw = DK.get("sweep", {})
for cid, c in (sw.get("0") or {}).items():
    if not c: continue
    a7, a30 = (sw.get("7") or {}).get(cid), (sw.get("30") or {}).get(cid)
    follows = not (c["n"] > 8 and a7 and a7["sig"] == c["sig"])
    add("rules", f"chart follows the range selector: {c['title']}", follows, f"7D {a7 and a7['n']} · 30D {a30 and a30['n']} · All {c['n']} points")
    add("rules", f"range keeps the latest point: {c['title']}", not a7 or a7["last"] == c["last"], f"7D ends {a7 and a7['last']}, All ends {c['last']}")
for t, X in T.items():
    for cid, c in (X.get("charts") or {}).items():
        if not c: continue
        dashed = [s["label"] for s in c["sets"] if s["dash"]]
        add("rules", f"no dashed series lines: {cid}", not dashed, ", ".join(map(str, dashed)))
        lg = c["legend"]
        add("rules", f"legend bottom-centred: {cid}", not lg["display"] or (lg["position"] == "bottom" and lg["align"] == "center"), json.dumps(lg))
        add("rules", f"tooltips in index mode: {cid}", c["mode"] == "index" and c["tmode"] == "index", f"interaction {c['mode']}, tooltip {c['tmode']}")
    for p in X.get("panels", []):
        add("rules", f"no colon in panel title: {p['title']}", ":" not in (p["title"] or ""), "")
        add("rules", f"panel explains its method: {p['title']}", bool(p["tip"] and len(p["tip"]) > 40), (p["tip"] or "")[:60])
    for k in X.get("kpis", []):
        add("rules", f"no colon in tile label: {k[0]}", ":" not in (k[0] or ""), "")
        add("rules", f"tile reads a value: {k[0]}", k[1] not in (None, "", "–"), str(k[1]))
    blob = " ".join([X.get("text") or ""] + [" ".join(map(str, r)) for tb in (X.get("tables") or {}).values() for r in tb] + [str(h or "") for h in (X.get("heads") or {}).values()])
    bad = sorted({w for w in BANNED if re.search(r"\b" + re.escape(w) + r"\b", blob, re.I)})
    add("rules", f"{t}: no banned words", not bad, ", ".join(bad))
    junk = sorted({m.group(0) for m in JUNK.finditer(blob)})
    add("rules", f"{t}: no undefined or NaN text", not junk, ", ".join(junk))
    tick = sorted({m.group(0) for m in TICKER.finditer(blob)})
    add("rules", f"{t}: ticker written STANDARD", not tick, ", ".join(tick))
tips = " ".join(DK.get("tips") or [])
bad = sorted({w for w in BANNED if re.search(r"\b" + re.escape(w) + r"\b", tips, re.I)}); add("rules", "method notes: no banned words", not bad, ", ".join(bad))
add("rules", "navigation carries no bullets or icons", all(n["marks"] == 0 for n in DK.get("nav", [])), json.dumps([n for n in DK.get("nav", []) if n["marks"]]))
add("rules", "page title is plain", (DK.get("title") or "") == "Standard Reserve Monitor", DK.get("title") or "")
stamps = {rx(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}) UTC", DK.get("side") or ""), rx(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}) UTC", DK.get("foot") or "")}
add("rules", "one compile time on the page, in UTC", len(stamps) == 1 and None not in stamps and pulled.strftime("%Y-%m-%d %H:%M") in stamps, f"{stamps} vs {pulled:%Y-%m-%d %H:%M}")
add("rules", "status shows the compile time", pulled.strftime("%H:%M") in (DK.get("status") or ""), DK.get("status") or "")
for w, src in [("1440", DK)] + list(V.get("layouts", {}).items()):
    for t, X in (src.get("tabs") or {}).items():
        lay = X.get("layout") or {}
        add("rules", f"{w}px {t}: nothing clipped", not lay.get("trunc"), "; ".join(f"{x['text'][:40]} ({x['sw']}>{x['cw']})" for x in lay.get("trunc", []))[:300])
        add("rules", f"{w}px {t}: no sideways page scroll", not lay.get("hscroll"), f"page {lay.get('hscroll')}px wide")
        add("rules", f"{w}px {t}: no panel wider than the screen", not lay.get("wide"), ", ".join(lay.get("wide", []))[:200])
        if w != "390":   # the daily log, epoch ledger and supply table are meant to scroll; every other table must fit
            ts = [x for x in lay.get("tscroll", []) if x["id"] not in ("t_log", "t_epochs", "t_float")]
            add("rules", f"{w}px {t}: tables fit their panels", not ts, ", ".join(f"{x['id']} {x['sw']}>{x['cw']}" for x in ts))

# ---------------------------------------------------------------- report
fails = [r for r in RES if not r["ok"] and r["severity"] == "fail"]; warns = [r for r in RES if not r["ok"] and r["severity"] == "warn"]
os.makedirs(A.out, exist_ok=True)
summary = {"ok": not fails, "checked": len(RES), "passed": sum(r["ok"] for r in RES), "fails": len(fails), "warnings": len(warns),
           "compiled": pulled.strftime("%Y-%m-%d %H:%M"), "checkedAt": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M"),
           "sections": {s: {"checked": sum(1 for r in RES if r["section"] == s), "passed": sum(1 for r in RES if r["section"] == s and r["ok"])} for s in dict.fromkeys(r["section"] for r in RES)}}
json.dump({**summary, "results": RES}, open(os.path.join(A.out, "report.json"), "w"), indent=1)
md = [f"## QA gate {'passed' if not fails else 'FAILED'}: compile {summary['compiled']} UTC", "",
      f"{summary['passed']} of {summary['checked']} checks passed · {len(fails)} failing · {len(warns)} warnings · checked {summary['checkedAt']} UTC", "",
      "| Section | Passed |", "|---|---|"] + [f"| {s} | {v['passed']} / {v['checked']} |" for s, v in summary["sections"].items()]
if fails: md += ["", "### Failing", ""] + [f"- **{r['section']}**: {r['check']}" + (f": {r['detail']}" if r["detail"] else "") for r in fails]
if warns: md += ["", "### Warnings", ""] + [f"- **{r['section']}**: {r['check']}" + (f": {r['detail']}" if r["detail"] else "") for r in warns]
open(os.path.join(A.out, "report.md"), "w").write("\n".join(md) + "\n")
if A.api:
    os.makedirs(A.api, exist_ok=True)
    json.dump({**summary, "results": [{k: r[k] for k in ("section", "check", "ok", "severity")} for r in RES]}, open(os.path.join(A.api, "qa.json"), "w"), indent=1, ensure_ascii=False)
    json.dump({"compiled": summary["compiled"] + " UTC", "items": rec}, open(os.path.join(A.api, "recon.json"), "w"), indent=1, ensure_ascii=False)
print("\n".join(md[:3]))
for r in fails: print("FAIL", r["section"], "|", r["check"], "|", r["detail"][:300])
for r in warns: print("WARN", r["section"], "|", r["check"], "|", r["detail"][:200])
sys.exit(1 if fails else 0)
