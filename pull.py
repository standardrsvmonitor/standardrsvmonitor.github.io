#!/usr/bin/env python3
"""Standard Reserve daily tracker: pull everything, keep caches, emit data/dash.json.
Run daily. First run backfills from genesis (several minutes); later runs are incremental."""
import json, urllib.request, time, datetime as dt, os, sys, math, bisect, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from k import keccak
import extra

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
C = os.path.join(D, "cache"); os.makedirs(C, exist_ok=True)
RPC = "https://rpc.mainnet.chain.robinhood.com"
IX = "https://indexer.standardreserve.xyz/v1/"
UA = {"User-Agent": "Mozilla/5.0 Chrome/154"}
CHAIN = 4663
STD = "0x88ad8DdF1E3898412146a534538d418c6F8A9062"
USDG = "0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168"
PM = "0x8366a39CC670B4001A1121B8F6A443A643e40951"          # v4 PoolManager
POSM = "0x58daec3116aae6d93017baaea7749052e8a04fa7"        # v4 PositionManager
SV = "0xF3334192D15450CdD385c8B70e03f9A6bD9E673b"          # StateView
STD_POOL = "0xc73f3cd3fb68288e63f008e08ef69caa0437224e420963c6aeb4526178e87ad9"
H = {"reserveSafe": "0x9a6F75AE9E8bdB68e1d12a9AdcCd0bB2958E3C22", "expansionVault": "0x6f457765035958725367a1D4C1f6064b047DAdB3",
     "contractionVault": "0x796e80E8ABcedc30c700A9587F7933d3342B8946", "incentivesVault": "0x9481404d30C296e57C93f05A49934A901719bbA9",
     "polBuyback": "0x50e4C444f71dF2Db8593c6c8ba4d493De618E147", "feeSplitter": "0xaa12DEda4aC19233A315777b17ff6ff5029D01b2",
     "centralBank": "0x5977B25419f9c0dDcB2F89fE204955622f4F57ea", "sbills": "0x163B36fD07622486CB889fEEf97BfBe2c1D7c05B",
     "polManager": "0x242F3e67BEf43470C2434d95E7D618E19f87c8f8"}   # teamWallet is read from feeSplitter.teamWallet() at runtime
ZERO = "0x0000000000000000000000000000000000000000"
TR = "0x" + keccak(b"Transfer(address,address,uint256)").hex()
SW = "0x" + keccak(b"Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)").hex()
ML = "0x" + keccak(b"ModifyLiquidity(bytes32,address,int24,int24,int256,bytes32)").hex()
SEED_BLOCK = 88451986   # first stock-pool seeding block (Oct 14 2026)

def sel(sig): return "0x" + keccak(sig.encode()).hex()[:8]
def pad(a): return "0x" + a[2:].lower().rjust(64, "0")
def u(x): return hex(x)[2:].rjust(64, "0")
def s128(h): x = int(h, 16); return x - (1 << 256) if x >= (1 << 255) else x
def jload(p, default):
    try: return json.load(open(p))
    except Exception: return default
def jsave(p, o): json.dump(o, open(p, "w"))
def log(*a): print(dt.datetime.utcnow().strftime("%H:%M:%S"), *a, flush=True)

def rpc(m, p, tries=6):
    for i in range(tries):
        try:
            r = urllib.request.Request(RPC, json.dumps({"jsonrpc": "2.0", "id": 1, "method": m, "params": p}).encode(),
                                       {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
            return json.load(urllib.request.urlopen(r, timeout=120))
        except Exception as e:
            err = e; time.sleep(2 + 2 * i)
    return {"error": {"message": str(err)}}
def rpcb(calls, tries=6):   # batched JSON-RPC, results in call order
    for i in range(tries):
        try:
            r = urllib.request.Request(RPC, json.dumps([{"jsonrpc": "2.0", "id": k, "method": m, "params": p} for k, (m, p) in enumerate(calls)]).encode(),
                                       {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
            res = json.load(urllib.request.urlopen(r, timeout=120)); return [x.get("result") for x in sorted(res, key=lambda x: x["id"])]
        except Exception as e:
            err = e; time.sleep(2 + 2 * i)
    raise RuntimeError(f"rpc batch failed: {err}")
def ecall(to, data, block="latest"):
    r = rpc("eth_call", [{"to": to, "data": data}, block]); return r.get("result")
def get(url, tries=4, backoff=3):
    for i in range(tries):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60))
        except Exception as e:
            err = e; time.sleep(backoff * (i + 1))
    return {"_error": str(err)}

def getlogs(q, lo, hi, step=400000):   # step halves when a range returns too many logs and grows back to the starting step
    out = []; b = lo; cap = step
    while b <= hi:
        e = min(b + step - 1, hi); qq = dict(q, fromBlock=hex(b), toBlock=hex(e))
        r = rpc("eth_getLogs", [qq], tries=3)
        if "error" in r:
            if step <= 2000: raise RuntimeError(r["error"])
            step //= 2; continue
        out += r["result"]; b = e + 1
        if step < cap: step = min(cap, step * 2)
    return out

# ---------- block timestamps (anchor cache, interpolation) ----------
ANCH = jload(os.path.join(C, "blocks.json"), {})
def block_ts(b):
    k = str(b)
    if k in ANCH: return ANCH[k]
    r = rpc("eth_getBlockByNumber", [hex(b), False]); t = int(r["result"]["timestamp"], 16); ANCH[k] = t; return t
def ts_block(ts):   # block at a timestamp, interpolated from the anchors (approximate; callers leave a margin)
    ks = sorted(int(k) for k in ANCH); ts_ = [ANCH[str(k)] for k in ks]
    i = bisect.bisect_left(ts_, ts)
    if i <= 0: return ks[0]
    if i >= len(ks): return ks[-1]
    b0, b1, t0, t1 = ks[i - 1], ks[i], ts_[i - 1], ts_[i]
    return int(b0 + (b1 - b0) * (ts - t0) / max(1, t1 - t0))
def ensure_anchors(lo, hi, every=100000):
    b = lo - lo % every
    while b <= hi + every:
        if str(b) not in ANCH:
            try: block_ts(b)
            except Exception: pass
        b += every
    jsave(os.path.join(C, "blocks.json"), ANCH)
_KEYS = []
def T(b):
    global _KEYS
    if len(_KEYS) != len(ANCH): _KEYS = sorted(int(x) for x in ANCH)
    keys = _KEYS
    i = bisect.bisect_left(keys, b)
    if i < len(keys) and keys[i] == b: return ANCH[str(b)]
    if i == 0: return ANCH[str(keys[0])]
    if i >= len(keys): return ANCH[str(keys[-1])]
    a, c = keys[i - 1], keys[i]; return ANCH[str(a)] + (ANCH[str(c)] - ANCH[str(a)]) * (b - a) / (c - a)
def day(ts): return dt.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
def find_block(ts, lo, hi):
    while lo < hi:
        mid = (lo + hi) // 2
        if block_ts(mid) < ts: lo = mid + 1
        else: hi = mid
    return lo

def main():
    t_start = time.time()
    tip = int(rpc("eth_blockNumber", [])["result"], 16); now = int(time.time()); today = day(now)
    out = {"pulledAt": now, "tip": tip}
    # reconciliations: each figure the page rebuilds, against an independent reading of the same thing. Gate items stop the deploy
    # when they fall outside tolerance (qa/check.py); watch items are published with their gap and reported but do not block.
    recon = []; out["recon"] = recon
    def reconcile(id_, label, ours, ref, source, tol, gate=True, absolute=False, unit="", note=""):
        if ours is None or ref is None:
            recon.append({"id": id_, "label": label, "ours": ours, "ref": ref, "source": source, "tol": tol, "abs": absolute, "gate": gate, "ok": False, "unit": unit, "note": note or "missing"}); return
        diff = ours - ref; rel = abs(diff) / abs(ref) if ref else (0.0 if diff == 0 else 1.0)
        recon.append({"id": id_, "label": label, "ours": ours, "ref": ref, "source": source, "diff": diff, "rel": rel, "tol": tol, "abs": absolute, "gate": gate,
                      "ok": (abs(diff) <= tol) if absolute else (rel <= tol), "unit": unit, "note": note})
    H["teamWallet"] = "0x" + ecall(H["feeSplitter"], sel("teamWallet()"))[-40:]
    log("tip", tip, "team wallet", H["teamWallet"])

    # ---------- indexer ----------
    home = get(IX + f"home?chainId={CHAIN}"); snap = home["snapshot"]
    H["taxHook"] = home["contracts"]["taxHook"]   # holds the live epoch's trading fees until they are routed

    # ---------- balances, read at one block; the transfer log and indexer events below are cut at the same block ----------
    # (balances read at "latest" after a minutes-long log scan picked up transfers the scan never saw, and the supply
    #  history, rebuilt backwards from these balances, carried the gap: 4,600 STANDARD on 26 Oct 2026)
    tip = int(rpc("eth_blockNumber", [])["result"], 16); out["tip"] = tip; BT = hex(tip)
    toks = {"STANDARD": (STD, 18), "USDG": (USDG, 6)}
    bal = {}
    for n, a in H.items():
        row = {"ETH": int(rpc("eth_getBalance", [a, BT])["result"], 16) / 1e18}
        for t, (ta, dec) in toks.items():
            r = ecall(ta, "0x70a08231" + pad(a)[2:], BT); v = int(r, 16) / 10 ** dec if r and r != "0x" else 0
            if v: row[t] = v
        bal[n] = row
    bal["poolManager"] = {"STANDARD": int(ecall(STD, "0x70a08231" + pad(PM)[2:], BT), 16) / 1e18}
    total_supply = int(ecall(STD, "0x18160ddd", BT), 16) / 1e18
    # S-Bill history: the full endpoint now stalls for minutes, so fetch the last seven days and merge into the cached points
    sb_old = jload(os.path.join(C, "sbills.json"), {})
    sb = get(IX + f"sbills/history?chainId={CHAIN}&range={'7d' if sb_old.get('points') else '30d'}", tries=2)
    if "current" not in sb: sb = dict(sb_old)
    key = lambda q: (q.get("t"), q.get("txHash"), q.get("kind"), q.get("amount"))
    pts = {key(q): q for q in (sb_old.get("points") or [])}; pts.update({key(q): q for q in (sb.get("points") or [])})
    sb["points"] = sorted(pts.values(), key=lambda q: (q.get("t") or 0)); sb.setdefault("deploymentBlock", sb_old.get("deploymentBlock"))
    lic = get(IX + f"auctions/license/periods?chainId={CHAIN}")
    act = {}
    for k in ["epoch-settled", "epoch-routed", "licenses-purchased", "withdrawn", "deposited", "charter-created", "revoked", "branches-opened", "checked-in"]:
        ev = []; cur = None
        while True:
            d = get(IX + f"activity?chainId={CHAIN}&since=0&limit=100&kind={k}" + (f"&cursor={cur}" if cur else ""))
            if "events" not in d: log("activity ERR", k, d); break
            ev += d["events"]; cur = d["page"].get("nextCursor")
            if not cur or not d["events"]: break
        act[k] = [e for e in ev if int(e.get("blockNumber") or 0) <= tip]; log("indexer activity", k, len(ev))
    jsave(os.path.join(C, "activity.json"), act); jsave(os.path.join(C, "home.json"), home)
    jsave(os.path.join(C, "sbills.json"), sb); jsave(os.path.join(C, "license_periods.json"), lic)
    genesis_ts = int(snap["bank"]["genesisTime"])
    log("indexer ok", {k: len(v) for k, v in act.items()})

    # ---------- genesis block and anchors ----------
    meta = jload(os.path.join(C, "meta.json"), {})
    if "genesisBlock" not in meta:
        meta["genesisBlock"] = find_block(genesis_ts, 55000000, 70000000); jsave(os.path.join(C, "meta.json"), meta)
    G = meta["genesisBlock"]; ensure_anchors(G, tip); block_ts(tip); log("genesis block", G, "anchors", len(ANCH))   # anchor the tip so the last hours interpolate

    # ---------- STANDARD protocol-side transfers (backfill + incremental) ----------
    tf = jload(os.path.join(C, "transfers.json"), {"last": G - 1, "rows": []})
    watch = {ZERO: "zero", PM: "pool", H["contractionVault"]: "contraction", H["polBuyback"]: "polBuyback", H["incentivesVault"]: "incentives",
             H["sbills"]: "sbills", H["centralBank"]: "bank", H["teamWallet"]: "team", H["reserveSafe"]: "safe", H["polManager"]: "polManager"}
    wl = {a.lower(): n for a, n in watch.items()}
    if tf["last"] < tip:
        lo = tf["last"] + 1; seen = set()
        la = getlogs({"address": STD, "topics": [TR, [pad(a) for a in watch]]}, lo, tip)
        lb = getlogs({"address": STD, "topics": [TR, None, [pad(a) for a in watch]]}, lo, tip)
        for l in la + lb:
            key = (l["transactionHash"], l["logIndex"])
            if key in seen: continue
            seen.add(key)
            f = "0x" + l["topics"][1][-40:]; t = "0x" + l["topics"][2][-40:]
            tf["rows"].append([int(l["blockNumber"], 16), wl.get(f, "other"), wl.get(t, "other"), int(l["data"], 16) / 1e18])
        tf["last"] = tip; jsave(os.path.join(C, "transfers.json"), tf)
    log("transfers rows", len(tf["rows"]))

    # ---------- reserve LP positions (owned by Safe) -> pools, holdings ----------
    pm = jload(os.path.join(C, "positions.json"), {"last": SEED_BLOCK - 1, "ids": []})
    if pm["last"] < tip:
        for l in getlogs({"address": POSM, "topics": [TR, None, pad(H["reserveSafe"])]}, pm["last"] + 1, tip):
            i = int(l["topics"][3], 16)
            if i not in pm["ids"]: pm["ids"].append(i)
        pm["last"] = tip; jsave(os.path.join(C, "positions.json"), pm)
    pools = {}; pos = []
    symcache = jload(os.path.join(C, "symbols.json"), {})
    def symbol(a):
        if a.lower() == ZERO: return "ETH"
        if a in symcache: return symcache[a]
        r = ecall(a, "0x95d89b41") or ""
        try: b = bytes.fromhex(r[2:]); n = int.from_bytes(b[32:64], "big"); s = b[64:64 + n].decode()
        except Exception: s = a[:8]
        symcache[a] = s; return s
    for i in sorted(pm["ids"]):
        own = ecall(POSM, sel("ownerOf(uint256)") + u(i))
        if not own or int(own, 16) != int(H["reserveSafe"], 16): continue
        liq = int(ecall(POSM, sel("getPositionLiquidity(uint256)") + u(i)), 16)
        r = ecall(POSM, sel("getPoolAndPositionInfo(uint256)") + u(i)); w = [r[2 + 64 * k:2 + 64 * (k + 1)] for k in range(6)]
        key = bytes.fromhex("".join(w[:5])); pid = "0x" + keccak(key).hex()
        c0 = "0x" + w[0][-40:]; c1 = "0x" + w[1][-40:]; info = int(w[5], 16)
        s24 = lambda x: x - (1 << 24) if x >= (1 << 23) else x
        tl = s24((info >> 8) & 0xFFFFFF); tu = s24((info >> 32) & 0xFFFFFF)
        if pid not in pools:
            usdg0 = c0.lower() == USDG.lower(); stock = c1 if usdg0 else c0
            pools[pid] = {"id": pid, "stock": symbol(stock), "stockAddr": stock, "usdg0": usdg0, "fee": int(w[2], 16), "spacing": int(w[3], 16), "liq": 0, "positions": 0}
        pools[pid]["positions"] += 1; pools[pid].setdefault("ranges", []).append([tl, tu, liq])
        pos.append({"id": i, "pool": pid, "liq": liq, "tl": tl, "tu": tu})
    jsave(os.path.join(C, "symbols.json"), symcache)
    lp = {}
    for pid, p in pools.items():
        r = ecall(SV, sel("getSlot0(bytes32)") + pid[2:]); sp = int(r[2:66], 16) / 2 ** 96; P = sp * sp
        x = y = 0.0
        for q in pos:
            if q["pool"] != pid or not q["liq"]: continue
            a = math.sqrt(1.0001 ** q["tl"]); b = math.sqrt(1.0001 ** q["tu"]); sc = min(max(sp, a), b); L = q["liq"]
            x += L * (b - sc) / (sc * b); y += L * (sc - a)
        if p["usdg0"]: usdg = x / 1e6; stock = y / 1e18; px = 1e12 / P if P else 0   # P = token1 raw per token0 raw; USDG 6dp, stock 18dp
        else: stock = x / 1e18; usdg = y / 1e6; px = P * 1e18 / 1e6
        tick_now = int(r[2 + 64:2 + 128], 16); tick_now = tick_now - (1 << 256) if tick_now >= (1 << 255) else tick_now
        pool_liq = int(ecall(SV, sel("getLiquidity(bytes32)") + pid[2:]), 16)
        mine_liq = sum(l_ for tl_, tu_, l_ in p.get("ranges", []) if tl_ <= tick_now < tu_)
        f0 = f1 = 0   # fees accrued in the positions and not yet withdrawn: liquidity x fee growth inside the range since the position's last update
        I24 = lambda v: format(v % (1 << 256), "064x")
        for q in pos:
            if q["pool"] != pid: continue
            fg = ecall(SV, sel("getFeeGrowthInside(bytes32,int24,int24)") + pid[2:] + I24(q["tl"]) + I24(q["tu"]), BT)
            pi = ecall(SV, sel("getPositionInfo(bytes32,address,int24,int24,bytes32)") + pid[2:] + pad(POSM)[2:] + I24(q["tl"]) + I24(q["tu"]) + u(q["id"]), BT)
            L_ = int(pi[2:66], 16)
            f0 += L_ * ((int(fg[2:66], 16) - int(pi[66:130], 16)) % (1 << 256)) >> 128; f1 += L_ * ((int(fg[66:130], 16) - int(pi[130:194], 16)) % (1 << 256)) >> 128
        ou, os_ = (f0 / 1e6, f1 / 1e18) if p["usdg0"] else (f1 / 1e6, f0 / 1e18)
        lp[p["stock"]] = {"pool": pid, "stock": stock, "usdg": usdg, "price": px, "valueUSD": stock * px + usdg, "positions": p["positions"], "feeTier": p["fee"], "isEth": p["stockAddr"].lower() == ZERO,
                          "share": (min(1.0, mine_liq / pool_liq) if pool_liq else 0.0), "poolLiqUsd": None,
                          "feesOwed": {"stock": os_, "usdg": ou, "usd": os_ * px + ou}}
        if p["stockAddr"].lower() != ZERO: toks[p["stock"]] = (p["stockAddr"], 18)
    for n, a in H.items():
        for t, (ta, dec) in toks.items():
            if t in ("STANDARD", "USDG"): continue
            r = ecall(ta, "0x70a08231" + pad(a)[2:], BT); v = int(r, 16) / 10 ** dec if r and r != "0x" else 0
            if v > 1e-6: bal[n][t] = v
    log("pools", {k: round(v["valueUSD"]) for k, v in lp.items()})

    # ---------- stock-pool swaps (incremental) ----------
    sw = jload(os.path.join(C, "swaps.json"), {"last": SEED_BLOCK - 1, "rows": []})
    for r in sw["rows"]:
        if r[1] == "": r[1] = "ETH"   # rows cached before the native-ETH pool got its symbol
    pids = list(pools.keys())
    if pids and sw["last"] < tip:
        byid = {p["id"]: p for p in pools.values()}
        for l in getlogs({"address": PM, "topics": [SW, pids]}, sw["last"] + 1, tip, 100000):   # OR-list in a topic: 100k-block ranges
            p = byid[l["topics"][1]]; idx = 0 if p["usdg0"] else 1
            usdg = abs(s128(l["data"][2 + 64 * idx:2 + 64 * (idx + 1)])) / 1e6
            fee = int(l["data"][2 + 64 * 5:2 + 64 * 6], 16); snd = "0x" + l["topics"][2][-40:]
            ev_liq = int(l["data"][2 + 64 * 3:2 + 64 * 4], 16); ev_tick = s128(l["data"][2 + 64 * 4:2 + 64 * 5])
            mine = sum(l_ for tl_, tu_, l_ in p.get("ranges", []) if tl_ <= ev_tick < tu_)   # the reserve's in-range liquidity at this swap
            share = min(1.0, mine / ev_liq) if ev_liq else 0.0                                    # its share of the fee
            sw["rows"].append([int(l["blockNumber"], 16), p["stock"], round(usdg, 2), fee, snd[:10], round(share, 4)])
        sw["last"] = tip; jsave(os.path.join(C, "swaps.json"), sw)
    log("swap rows", len(sw["rows"]))

    # ---------- charter sales (price from the auction's purchase event; tx value misses contract buyers) ----------
    ch = jload(os.path.join(C, "charters.json"), {})
    founding = int(snap["bank"]["foundingMinted"])
    CA = home["contracts"]["charterAuction"].lower()
    PURCH = "0x1c54748c22f6bf384e0cf9a6a4dfbc630c9ac343ba8a88a5769508bd2da18e50"   # CharterPurchased(charterId, buyer, day) data = price
    for e in act["charter-created"]:
        if int(e["charterId"]) <= founding: continue
        if e["txHash"] in ch and "buyer" in ch[e["txHash"]]: continue
        t = rpc("eth_getTransactionByHash", [e["txHash"]]).get("result") or {}
        rc = rpc("eth_getTransactionReceipt", [e["txHash"]]).get("result") or {}
        px = None; buyer = t.get("from", "")
        for l in rc.get("logs", []):
            if l["address"].lower() == CA and l["topics"][0] == PURCH:
                px = int(l["data"][2:66], 16) / 1e18; buyer = "0x" + l["topics"][2][-40:]
        if px is None: px = int(t.get("value", "0x0"), 16) / 1e18
        ch[e["txHash"]] = {"id": int(e["charterId"]), "ts": int(e["timestamp"]), "eth": px, "buyer": buyer, "viaContract": (t.get("to") or "").lower() != CA}
    jsave(os.path.join(C, "charters.json"), ch)
    charters = sorted(ch.values(), key=lambda x: x["ts"])

    # ---------- prices ----------
    ds = get("https://api.dexscreener.com/tokens/v1/robinhood/" + STD)
    dstd = ds[0] if isinstance(ds, list) and ds else {}
    eth = get("https://api.coinbase.com/v2/prices/ETH-USD/spot"); ethusd = float(eth["data"]["amount"])
    ohl = jload(os.path.join(C, "ohlcv.json"), None)
    if ohl is None: ohl = jload(os.path.join(os.path.dirname(D), "..", "industry", "std_ohlcv_daily.json"), [])
    g = get(f"https://api.geckoterminal.com/api/v2/networks/robinhood/pools/{STD_POOL}/ohlcv/day?limit=100&currency=usd", tries=3, backoff=15)
    try:
        rows = g["data"]["attributes"]["ohlcv_list"]   # fresh candles replace cached ones: a day first cached while in progress holds an early price, not its close
        byts = {r[0]: r for r in ohl}; byts.update({r[0]: list(r[:6]) + [now] for r in rows})   # the 7th field records when the candle was read
        ohl = sorted(byts.values(), key=lambda r: r[0])
    except Exception: log("geckoterminal unavailable, using cache", str(g)[:80])
    jsave(os.path.join(C, "ohlcv.json"), ohl)
    ed = jload(os.path.join(C, "eth_daily.json"), {})
    need_from = (dt.datetime.utcfromtimestamp(genesis_ts) - dt.timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z")
    cb = get(f"https://api.exchange.coinbase.com/products/ETH-USD/candles?granularity=86400&start={need_from}&end={dt.datetime.utcnow().strftime('%Y-%m-%dT%H:00:00Z')}")
    if isinstance(cb, list):
        for r in cb: ed[day(r[0])] = r[4]
    ed[today] = ethusd; jsave(os.path.join(C, "eth_daily.json"), ed)
    stock_ds = {}
    for s, (a, _) in list(toks.items()) + [("ETH", (ZERO, 18))]:
        if s in ("STANDARD", "USDG") or s not in lp: continue
        stock_ds[s] = get(f"https://api.dexscreener.com/token-pairs/v1/robinhood/{a}")
    jsave(os.path.join(C, "stock_pairs.json"), stock_ds)

    # ---------- compile ----------
    px = float(dstd.get("priceUsd") or 0)
    price_day = {day(r[0]): r[4] for r in ohl}; price_day[today] = px
    eth_day = ed
    base_issue = int(snap["bank"]["baseIssuancePerDay"]) / 1e18
    epoch_days = int(snap["bank"]["epochDays"])
    # epochs
    settled = sorted(act["epoch-settled"], key=lambda e: int(e["values"]["epoch"]))
    routed = sorted(act["epoch-routed"], key=lambda e: int(e["timestamp"]))
    epochs = []
    for i, (s, r) in enumerate(zip(settled, routed), 1):
        v = r["values"]; tot = (int(v["toPol"]) + int(v["toVault"]) + int(v["teamAccrued"])) / 1e18
        st = genesis_ts + (i - 1) * epoch_days * 86400; en = st + epoch_days * 86400
        ch_eth = sum(c["eth"] for c in charters if st <= c["ts"] < en)
        epochs.append({"epoch": i, "start": st, "end": en, "settledAt": int(r["timestamp"]), "netFlow": int(s["values"]["netFlow"]) / 1e18,
                       "expansion": v["expansion"], "routed": tot, "toVault": int(v["toVault"]) / 1e18, "toPol": int(v["toPol"]) / 1e18,
                       "team": int(v["teamAccrued"]) / 1e18, "charterEth": ch_eth, "multiplierAfter": int(s["values"]["multiplierWad"]) / 1e18})
    # multiplier by epoch index (applies during epoch k): epoch1 = M_START
    m_by_epoch = {1: int(snap["bank"]["M_START_WAD"]) / 1e18}
    for e in epochs: m_by_epoch[e["epoch"] + 1] = e["multiplierAfter"]
    cur_epoch = int(snap["bank"]["epochNumber"])
    # daily aggregates
    days = collections.defaultdict(lambda: collections.defaultdict(float))
    for e in act["licenses-purchased"]:
        d = day(int(e["timestamp"])); days[d]["licBurn"] += int(e["values"]["count"]) * int(e["values"]["unitPrice"]) / 1e18; days[d]["licCount"] += int(e["values"]["count"])
    for e in act["withdrawn"]:
        d = day(int(e["timestamp"])); g_, n_ = int(e["values"]["gross"]) / 1e18, int(e["values"]["net"]) / 1e18
        days[d]["wdGross"] += g_; days[d]["wdNet"] += n_; days[d]["exitFeeBurn"] += (g_ - n_) / 2; days[d]["exitFeeRedis"] += (g_ - n_) / 2; days[d]["exits"] += 1
    for e in act["revoked"]:
        d = day(int(e["timestamp"])); v = e["values"]; fee = (int(v["gross"]) - int(v["bounty"]) - int(v["ownerNet"])) / 1e18
        days[d]["revokeFeeBurn"] += fee / 2; days[d]["revoked"] += 1; days[d]["revokeGross"] += int(v["gross"]) / 1e18
    lc = {}
    for e in act["licenses-purchased"]:
        d = day(int(e["timestamp"])); ts_ = int(e["timestamp"])
        if ts_ >= lc.get(d, (0, 0))[0]: lc[d] = (ts_, int(e["values"]["unitPrice"]) / 1e18)
    for d, (_, px_) in lc.items(): days[d]["licClose"] = px_
    # branch and charter census replayed from events (matches the live census exactly as of 22 Oct 2026)
    brc = collections.defaultdict(int); evs = []
    for e in act["charter-created"]: evs.append((int(e["timestamp"]), 0, "c", e["charterId"], 1))
    for e in act["branches-opened"]: evs.append((int(e["timestamp"]), 1, "o", e["charterId"], int(e["values"]["count"])))
    for e in act["withdrawn"]: evs.append((int(e["timestamp"]), 2, "w", e["charterId"], int(e["values"].get("branchesDestroyed", 0))))
    for e in act["revoked"]: evs.append((int(e["timestamp"]), 2, "r", e["charterId"], 1))
    evs.sort(); c_act = c_burn = 0; census = {}
    for ts_, _, k, cid, n in evs:
        if k == "c": brc[cid] += n; c_act += 1
        elif k == "o": brc[cid] += n
        else:   # a withdrawal destroys the branches it names; a revocation destroys the whole charter (charters 641 and 492, 28 and 29 Oct 2026)
            was = brc[cid]; brc[cid] = 0 if k == "r" else was - n
            if was > 0 and brc[cid] <= 0: c_act -= 1; c_burn += 1
        census[day(ts_)] = (c_act, c_burn, sum(brc.values()))
    for e in act["deposited"]:
        d = day(int(e["timestamp"])); days[d]["deposits"] += int(e["values"]["amount"]) / 1e18
    for e in act["charter-created"]:
        if int(e["charterId"]) > founding: days[day(int(e["timestamp"]))]["chartersSold"] += 1
    for c in charters: days[day(c["ts"])]["charterEth"] += c["eth"]
    for r in tf["rows"]:
        b, f, t, a = r; d = day(T(b))
        if f == "zero":
            if a >= 50_000_000: days[d]["genesisMint"] += a          # the 100M protocol-owned liquidity mint
            else: days[d]["mint"] += a
        if t == "zero": days[d]["burn"] += a; days[d]["burn_" + f] += a
        if t == "pool":
            if f in ("zero", "polManager"): days[d]["genesisPool"] += a
            else: days[d]["poolIn"] += a
        if f == "pool": days[d]["poolOut"] += a
        if f == "pool" and t == "polManager": days[d]["feesToTeam"] += a   # the protocol position's STANDARD fees, forwarded by the POL manager to the team wallet
        if t == "incentives": days[d]["toIncentives"] += a
        if f == "incentives": days[d]["fromIncentives"] += a
        if t == "sbills": days[d]["sbillIn"] += a
        if f == "sbills": days[d]["sbillOut"] += a
        if t == "team": days[d]["teamIn"] += a
        if f == "team": days[d]["teamOut"] += a
        if f == "polBuyback" or t == "polBuyback": days[d]["polBuybackFlow"] += a if t == "polBuyback" else -a
    tier = {p_["stock"]: p_["fee"] for p_ in pools.values()}
    LPAD_SND = {r_[:10] for r_ in extra.LPAD["routers"]}   # the swap cache keeps the executor's first ten characters
    for r in sw["rows"]:
        b, s, usdg, fee, snd = r[:5]; share = r[5] if len(r) > 5 else 1.0; d = day(T(b))
        if tier.get(s, 1 << 23) < 1 << 23: fee = min(fee, tier[s])   # a fixed-tier pool's swap fee includes Uniswap's protocol fee (ETH/USDG: 125 of 625 pips); providers earn the tier
        days[d]["spVol"] += usdg; days[d]["spFee"] += usdg * fee / 1e6 * share; days[d]["spFeeGross"] += usdg * fee / 1e6; days[d]["spSwaps"] += 1
        days[d]["spVol_" + s] += usdg; days[d]["spFee_" + s] += usdg * fee / 1e6 * share; days[d]["spFeeGross_" + s] += usdg * fee / 1e6
        days[d]["spVolMine"] += usdg * share; days[d]["spVolMine_" + s] += usdg * share   # volume served by the reserve's own in-range liquidity
        if snd in LPAD_SND: days[d]["spFeeLpad"] += usdg * fee / 1e6 * share; days[d]["spVolLpad"] += usdg * share   # swaps executed by the launchpad's routers, exact
        if fee == 0: days[d]["spVolZeroFee"] += usdg
    # issuance accrued per day (ledger), by epoch multiplier
    d0 = dt.datetime.utcfromtimestamp(genesis_ts).date(); dn = dt.datetime.utcfromtimestamp(now).date()
    dd = d0
    ep_len = epoch_days * 86400
    while dd <= dn:   # issuance accrues per second at the multiplier of the epoch in force; epochs turn at genesis time, not midnight
        ds_ = dd.strftime("%Y-%m-%d"); d_start = int(dt.datetime(dd.year, dd.month, dd.day, tzinfo=dt.timezone.utc).timestamp())
        t_ = max(genesis_ts, d_start); t_stop = min(now, d_start + 86400)
        while t_ < t_stop:
            k = (t_ - genesis_ts) // ep_len + 1; seg = min(t_stop, genesis_ts + k * ep_len) - t_
            days[ds_]["issuance"] += base_issue * m_by_epoch.get(k, m_by_epoch[max(m_by_epoch)]) * seg / 86400; t_ += seg
        k_mid = max(1, (d_start + 43200 - genesis_ts) // ep_len + 1); days[ds_]["multiplier"] = m_by_epoch.get(k_mid, m_by_epoch[max(m_by_epoch)])
        dd += dt.timedelta(days=1)
    # token-loop routed per day (epoch routed spread evenly over its days), charter part separated
    for e in epochs:
        per = e["routed"] / epoch_days; cper = e["charterEth"] / epoch_days
        for j in range(epoch_days):
            d = day(e["start"] + j * 86400 + 3600)
            days[d]["routedEth"] += per; days[d]["tradingFeeEth"] += per - cper
    # live epoch: fees collected but not yet routed (tax hook + fee splitter balances), spread over the elapsed days
    # the fee splitter holds charter ETH forwarded this epoch; the tax hook holds trading fees. Charter ETH stays on its sale day,
    # trading fees (hook + any splitter balance beyond the epoch's charters) are spread evenly over elapsed time.
    ep_start = int(snap["bank"]["epochStart"]); elapsed = max(1, now - ep_start)
    live_ch = sum(c["eth"] for c in charters if c["ts"] >= ep_start)
    live_acc = bal["feeSplitter"]["ETH"] + bal.get("taxHook", {}).get("ETH", 0)
    live_tr = max(0.0, live_acc - live_ch); t_ = ep_start
    while t_ < now:
        seg = min(now, (t_ // 86400 + 1) * 86400) - t_; d = day(t_)
        days[d]["tradingFeeEth"] += live_tr * seg / elapsed; days[d]["routedLive"] = 1; t_ += seg
    for c in charters:
        if c["ts"] >= ep_start: days[day(c["ts"])]["charterLive"] += c["eth"]
    for d in list(days):
        if days[d].get("routedLive"): days[d]["routedEth"] += days[d]["tradingFeeEth"] + days[d]["charterLive"] if days[d]["routedEth"] == 0 else days[d]["charterLive"]
    # supply history reconstructed backwards from today's balances
    dl = sorted(days.keys())
    pool_now = bal["poolManager"]["STANDARD"]; inc_now = bal["incentivesVault"].get("STANDARD", 0); sb_now = bal["sbills"].get("STANDARD", 0)
    T_hist = {}; pool_hist = {}; inc_hist = {}; sb_hist = {}; tm_hist = {}
    Tn, pn, inn, sbn, tmn = total_supply, pool_now, inc_now, sb_now, bal["teamWallet"].get("STANDARD", 0)
    for d in reversed(dl):
        T_hist[d] = Tn; pool_hist[d] = pn; inc_hist[d] = inn; sb_hist[d] = sbn; tm_hist[d] = tmn
        x = days[d]
        Tn -= x["mint"] + x["genesisMint"] - x["burn"]; pn -= x["poolIn"] + x["genesisPool"] - x["poolOut"]
        inn -= x["toIncentives"] - x["fromIncentives"]; sbn -= x["sbillIn"] - x["sbillOut"]; tmn -= x["teamIn"] - x["teamOut"]
    # walked back to genesis, every balance must land on zero: the transfer log then accounts for every token in it
    # (the 100M genesis liquidity mint precedes the genesis block the scan starts from; its arrival in the pool is inside the scan)
    reconcile("supply_zero", "Circulating supply, rebuilt from the genesis mint and transfer logs", 100_000_000 + total_supply - Tn, total_supply, "ERC-20 totalSupply at the compile block", 1,
              absolute=True, unit="STANDARD")
    reconcile("pool_zero", "Protocol liquidity STANDARD, rebuilt from transfer logs", pool_now - pn, pool_now, "balance at the compile block", 1, absolute=True, unit="STANDARD")
    reconcile("incentives_zero", "Incentives vault STANDARD, rebuilt from transfer logs", inc_now - inn, inc_now, "balance at the compile block", 1, absolute=True, unit="STANDARD")
    # forward ledger: pending = issuance + deposits + recycled exit fees - licenses - gross withdrawals - gross revocations
    sb_pts = sorted([(int(p["t"]), int(p.get("after", 0)) / 1e18, int(p.get("locked", 0)) / 1e18) for p in (sb.get("points") or []) if p.get("t")])
    wd_ev = [(int(e["timestamp"]), int(e["values"]["gross"]) / 1e18) for e in act["withdrawn"]]
    sb_c = sb.get("current") or {}; sb_dps = int(sb_c.get("driftPerSecond", 0)) / 1e18 if sb_c.get("drifting") else 0.0; sb_cap = int(sb_c.get("ceiling", 0)) / 1e18 or 1.0
    pend = 0.0; pend_hist = {}; fee_hist = {}; rate_hist = {}; sbl_hist = {}; cen_last = (0, 0, 0); cen_hist = {}
    for i, d in enumerate(dl):
        x = days[d]
        pend += x["issuance"] + x["deposits"] + x["exitFeeRedis"] + x["revokeFeeBurn"] - x["licBurn"] - x["wdGross"] - x["revokeGross"]
        pend_hist[d] = pend
        d_end = int(dt.datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp()) + 86400
        t_end = min(now, d_end); pd_ = (t_end - genesis_ts) // 86400   # resolution fee at the day's close, over the contract's seven protocol-day buckets
        w7_ = sum(g for ts_, g in wd_ev if ts_ < t_end and (ts_ - genesis_ts) // 86400 >= pd_ - 6)
        P7 = w7_ / max(pend + w7_, 10_000_000); fee_hist[d] = 0.02 + 0.58 * min(P7 / 0.10, 1) ** 2
        j = bisect.bisect_right(sb_pts, (t_end, 9e9, 9e9)); sbl_hist[d] = sb_pts[j - 1][2] if j else None
        rate_hist[d] = min(sb_cap, sb_pts[j - 1][1] + sb_dps * (t_end - sb_pts[j - 1][0])) if j else None   # rate at the close, drift since the last update included
        if d in census: cen_last = census[d]
        cen_hist[d] = cen_last
    log("ledger check: pending reconstructed", round(pend), "live", round(int(snap["bank"]["totalPendingLive"]) / 1e18),
        "| issued", round(sum(days[d]["issuance"] for d in dl)), "live", round(int(snap["bank"]["cumulativeIssued"]) / 1e18))
    reconcile("ledger", "In banks (ledger balance), rebuilt from events", pend, int(snap["bank"]["totalPendingLive"]) / 1e18, "Standard Reserve indexer, totalPendingLive", 0.005, unit="STANDARD")
    reconcile("issued", "STANDARD issued to bankers, rebuilt by epoch", sum(days[d]["issuance"] for d in dl), int(snap["bank"]["cumulativeIssued"]) / 1e18,
       "Standard Reserve indexer, cumulativeIssued", 0.001, unit="STANDARD")
    reconcile("branches", "Branches, replayed from events", census[max(census)][2], int(snap["bank"]["totalBranches"]), "Standard Reserve indexer, totalBranches", 0.002)
    reconcile("charters", "Active charters, replayed from events", census[max(census)][0], int(snap["census"]["active"]), "Standard Reserve indexer, census", 0.002)
    series = []
    prev = None
    for d in dl:
        x = days[d]; p = price_day.get(d); e_ = eth_day.get(d)
        flt = T_hist[d] - pool_hist[d] - inc_hist[d]
        row = {"date": d, "price": p, "eth": e_, "supply": T_hist[d], "pool": pool_hist[d], "incentives": inc_hist[d], "sbills": sb_hist[d], "float": flt,
               "mcTotal": p * T_hist[d] if p else None, "mcFloat": p * flt if p else None}
        row.update({k: round(v, 6) for k, v in x.items()})
        row["burnBuyback"] = round(x["burn_contraction"] + x["burn_polManager"] + x["burn_sbills"], 6)   # tokens bought back and burned
        row["depositBurn"] = round(x["deposits"], 6)                                                     # deposits converted to ledger (burned), from deposited events
        row["burnOther"] = round(max(0.0, x["burn_other"] + x["burn_bank"] - x["deposits"]), 6)          # burns that are not deposits: the tax hook burning STANDARD it takes from the pool (26,801.5 lifetime to 27 Oct 2026)
        row.update({"pending": pend_hist[d], "exitFee": fee_hist[d], "sbRate": rate_hist[d], "sbLocked": sbl_hist[d], "teamStd": tm_hist[d],
                    "activeCharters": cen_hist[d][0], "burnedCharters": cen_hist[d][1], "branches": cen_hist[d][2]})
        if prev and p and prev.get("price"):
            row["dPrice"] = (p - prev["price"]) * prev["float"]; row["dSupply"] = (flt - prev["float"]) * p
        series.append(row); prev = row
    # license periods
    per_len = int(snap["licenseAuction"]["AUCTION_DAY"])
    lpd = {}
    for e in sorted(act["licenses-purchased"], key=lambda e: int(e["timestamp"])):
        k = int(e["values"]["day"]); v = e["values"]; q = lpd.setdefault(k, {"day": k, "start": int(e["timestamp"]), "sold": 0, "burned": 0.0, "close": 0.0, "sales": 0})
        q["sold"] += int(v["count"]); q["burned"] += int(v["count"]) * int(v["unitPrice"]) / 1e18; q["close"] = int(v["unitPrice"]) / 1e18; q["sales"] += 1
    lic_periods = [lpd[k] for k in sorted(lpd)]
    # stock pool market context
    pool_ctx = {}
    for s, pairs in stock_ds.items():
        if not isinstance(pairs, list): continue
        mine = lp[s]["pool"]; rows = []
        for pr in pairs:
            rows.append({"dex": pr.get("dexId"), "label": (pr.get("labels") or [""])[0], "quote": pr.get("quoteToken", {}).get("symbol"),
                         "liq": (pr.get("liquidity") or {}).get("usd") or 0, "vol24": (pr.get("volume") or {}).get("h24") or 0,
                         "pair": pr.get("pairAddress"), "sr": pr.get("pairAddress", "").lower() == mine.lower()})
        rows.sort(key=lambda r: -r["liq"]); tot_liq = sum(r["liq"] for r in rows); tot_vol = sum(r["vol24"] for r in rows)
        srrow = next((r for r in rows if r["sr"]), None); others = [r for r in rows if not r["sr"]]
        pool_ctx[s] = {"pools": len(rows), "totalLiq": tot_liq, "totalVol24": tot_vol, "srLiq": srrow["liq"] if srrow else 0, "srVol24": srrow["vol24"] if srrow else 0,
                       "nextLiq": others[0]["liq"] if others else 0, "nextDex": (others[0]["dex"] + " " + others[0]["label"]).strip() if others else "", "rank": (rows.index(srrow) + 1) if srrow else None}
    # reserve composition
    safe = bal["reserveSafe"]; stock_held = sum(safe.get(s, 0) * lp[s]["price"] for s in lp if not lp[s]["isEth"])
    reserve = {"safeEth": safe["ETH"], "safeUsdg": safe.get("USDG", 0), "safeStockUsd": stock_held, "lpUsd": sum(v["valueUSD"] for v in lp.values()),
               "contractionEth": bal["contractionVault"]["ETH"], "expansionEth": bal["expansionVault"]["ETH"], "polBuybackEth": bal["polBuyback"]["ETH"],
               "feeSplitterEth": bal["feeSplitter"]["ETH"], "incentivesStd": inc_now, "teamEth": bal["teamWallet"]["ETH"]}
    reserve["totalUsd"] = (safe["ETH"] + reserve["contractionEth"] + reserve["expansionEth"]) * ethusd + reserve["safeUsdg"] + stock_held + reserve["lpUsd"]
    # sbills
    sbc = sb.get("current", {})
    sb_drift = int(sbc.get("driftPerSecond", 0)) / 1e18 if sbc.get("drifting") else 0.0   # the term rate drifts up between deposits; the indexer reports it as of the last update
    sb_rate = int(sbc.get("rate", 0)) / 1e18 + sb_drift * max(0, now - int(sbc.get("rateUpdatedAt") or now))
    sb_rate = min(int(sbc.get("ceiling", 0)) / 1e18 or 1.0, sb_rate)
    sbills = {"rate": sb_rate, "locked": int(sbc.get("locked", 0)) / 1e18, "principal": int(sbc.get("principal", 0)) / 1e18,
              "floor": int(sb.get("start", {}).get("floor", 0)) / 1e18, "ceiling": int(sb.get("start", {}).get("ceiling", 0)) / 1e18,
              "points": [{"t": p.get("t"), "rate": int(p.get("after", 0)) / 1e18, "locked": int(p.get("locked", 0)) / 1e18, "kind": p.get("kind")}
                         for p in (sb.get("points") or sb.get("history") or sb.get("series") or []) if p.get("t")]}
    # exit fee now: 7-day exit pressure over the contract's own buckets (seven protocol days, today included, days roll at genesis time)
    if isinstance(snap.get("withdrawnByDay"), list): w7 = sum(int(x) for x in snap["withdrawnByDay"]) / 1e18
    else: w7 = sum(int(e["values"]["gross"]) for e in act["withdrawn"] if (int(e["timestamp"]) - genesis_ts) // 86400 >= (now - genesis_ts) // 86400 - 6) / 1e18
    held = int(snap["bank"].get("totalPendingLive", 0)) / 1e18
    P_ = w7 / max(held + w7, 10_000_000); exit_fee = 0.02 + 0.58 * min(P_ / 0.10, 1) ** 2
    def nxt(a):   # next auction period opening time and price
        anchor = int(a["auctionAnchor"]); per = int(a["AUCTION_DAY"]); k = (now - anchor) // per
        return anchor + (k + 1) * per, int(a["startMultiplier"]) * int(a["lastSalePrice"]) / 1e18
    ch_next, lic_next = nxt(snap["charterAuction"]), nxt(snap["licenseAuction"])
    live = {"date": today, "price": px, "priceChange24h": (dstd.get("priceChange") or {}).get("h24"), "vol24": (dstd.get("volume") or {}).get("h24"),
            "poolLiqUsd": (dstd.get("liquidity") or {}).get("usd"), "ethusd": ethusd, "totalSupply": total_supply, "poolStd": pool_now, "incentivesStd": inc_now,
            "sbillsStd": sb_now, "float": total_supply - pool_now - inc_now, "pending": held, "burnedForever": int(snap["token"]["burnedForever"]) / 1e18,
            "cumulativeIssued": int(snap["bank"]["cumulativeIssued"]) / 1e18, "maxSupply": int(snap["token"]["maxSupply"]) / 1e18,
            "multiplier": int(snap["bank"]["multiplierWad"]) / 1e18, "epoch": cur_epoch, "epochStart": int(snap["bank"]["epochStart"]), "epochEnd": int(snap["bank"]["epochEnd"]),
            "epochNetFlow": int(snap["tax"]["epochNetFlow"]) / 1e18, "feeSplitterEth": reserve["feeSplitterEth"], "branches": int(snap["bank"]["totalBranches"]),
            "activeCharters": int(snap["census"]["active"]), "burnedCharters": int(snap["census"]["burned"]), "chartersMinted": int(snap["charterNft"]["nextId"]) - 1,
            "charterPriceNow": int(snap["charterAuction"]["currentPrice"]) / 1e18, "charterLastSale": int(snap["charterAuction"]["lastSalePrice"]) / 1e18,
            "charterFloor": int(snap["charterAuction"]["dayFloorPrice"]) / 1e18, "charterSoldToday": int(snap["charterAuction"]["soldToday"]), "charterCap": int(snap["charterAuction"]["dayCap"]),
            "licensePriceNow": int(snap["licenseAuction"]["currentPrice"]) / 1e18, "licenseLastSale": int(snap["licenseAuction"]["lastSalePrice"]) / 1e18,
            "licenseFloor": int(snap["licenseAuction"]["dayFloorPrice"]) / 1e18, "licenseSoldToday": int(snap["licenseAuction"]["soldToday"]), "licenseCap": int(snap["licenseAuction"]["dayCap"]),
            "auctionPeriodHours": per_len / 3600, "exitFeeNow": exit_fee, "exitPressure7d": P_, "w7": w7, "sbills": sbills, "reserve": reserve, "lp": lp, "poolCtx": pool_ctx, "balances": bal,
            "baseIssuance": base_issue, "routedLifetime": sum(e["routed"] for e in epochs), "charterEthLifetime": sum(c["eth"] for c in charters),
            "positiveStreak": int(snap["bank"].get("positiveSignalStreak", 0)), "previousEpochFlow": int(snap["bank"].get("previousEpochFlow", 0)) / 1e18,
            "teamStd": bal["teamWallet"].get("STANDARD", 0), "teamEth": bal["teamWallet"]["ETH"], "cumulativeRecycled": int(snap["bank"].get("cumulativeRecycled", 0)) / 1e18,
            "charterDayStart": int(snap["charterAuction"]["dayStartPrice"]) / 1e18, "licenseDayStart": int(snap["licenseAuction"]["dayStartPrice"]) / 1e18,
            "charterRemaining": int(snap["charterAuction"].get("remainingToday", 0)), "licenseRemaining": int(snap["licenseAuction"].get("remainingToday", 0)),
            "charterNextOpen": ch_next[0], "charterNextStart": ch_next[1], "licenseNextOpen": lic_next[0], "licenseNextStart": lic_next[1],
            "charterHalfLife": int(snap["charterAuction"].get("decayHalfLife", 7200)) / 3600, "licenseHalfLife": int(snap["licenseAuction"].get("decayHalfLife", 7200)) / 3600,
            "accruedEth": live_acc, "taxHookEth": bal.get("taxHook", {}).get("ETH", 0), "mStepUp": int(snap["bank"]["M_STEP_UP_WAD"]) / 1e18, "mStepDown": int(snap["bank"]["M_STEP_DOWN_WAD"]) / 1e18, "mMin": int(snap["bank"]["M_MIN_WAD"]) / 1e18, "mMax": int(snap["bank"]["M_MAX_WAD"]) / 1e18}
    # ---------- top bankers (indexer leaderboard) with ENS primary names from Ethereum mainnet ----------
    lbd = get(IX + f"leaderboard?chainId={CHAIN}")
    # ranked as the protocol's own leaderboard ranks: by branches, which set each banker's share of issuance, then this epoch's emissions
    bankers = sorted(lbd.get("bankers", []), key=lambda r: (-int(r.get("branches", 0)), -int(r.get("epochEmissions", 0)), -int(r.get("lifetimeEmissions", 0))))
    tot_ep = sum(int(r.get("epochEmissions", 0)) for r in bankers) or 1
    ensc = jload(os.path.join(C, "ens.json"), {})
    ETH_RPC = "https://ethereum-rpc.publicnode.com"
    def erpc(m, p):
        r = urllib.request.Request(ETH_RPC, json.dumps({"jsonrpc": "2.0", "id": 1, "method": m, "params": p}).encode(), {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
        return json.load(urllib.request.urlopen(r, timeout=30)).get("result")
    def namehash(name):
        node = b"\x00" * 32
        for label in reversed(name.split(".")): node = keccak(node + keccak(label.encode()))
        return node
    def ens_name(addr):
        node = namehash(addr[2:].lower() + ".addr.reverse")
        res = erpc("eth_call", [{"to": "0x00000000000C2E074eC69A0dFb2997BA6C7d2e1e", "data": "0x0178b8bf" + node.hex()}, "latest"])
        if not res or int(res, 16) == 0: return ""
        out = erpc("eth_call", [{"to": "0x" + res[-40:], "data": "0x691f3431" + node.hex()}, "latest"])
        if not out or len(out) < 130: return ""
        n = int(out[66:130], 16); return bytes.fromhex(out[130:130 + 2 * n]).decode(errors="ignore")
    leaders = []
    tot_br = sum(int(r.get("branches", 0)) for r in bankers) or 1
    for i, r in enumerate(bankers[:25], 1):
        a = r["owner"].lower(); e = ensc.get(a)
        if not e or now - e.get("t", 0) > 7 * 86400:
            try: ensc[a] = {"name": ens_name(a), "t": now}
            except Exception: ensc.setdefault(a, {"name": "", "t": 0})
        leaders.append({"rank": i, "owner": a, "ens": ensc[a]["name"], "banks": int(r.get("banks", 0)), "branches": int(r.get("branches", 0)),
                        "branchShare": int(r.get("branches", 0)) / tot_br, "epochShare": int(r.get("epochEmissions", 0)) / tot_ep, "epochEmissions": int(r.get("epochEmissions", 0)) / 1e18,
                        "lifetimeEmissions": int(r.get("lifetimeEmissions", 0)) / 1e18, "topBank": r.get("topBank"), "prevRank": (r.get("previousRank") or {}).get("epoch")})
    jsave(os.path.join(C, "ens.json"), ensc)
    out["leaders"] = {"rows": leaders, "bankers": len(bankers), "banks": sum(int(r.get("banks", 0)) for r in bankers), "branches": tot_br}
    # branches replayed per charter, summed by the wallet that created it, against the leaderboard's per-banker counts
    owner_ = {e["charterId"]: (e.get("actor") or "").lower() for e in act["charter-created"]}; rep_ = collections.Counter()
    for cid_, n_ in brc.items():
        if n_ > 0: rep_[owner_.get(cid_, "")] += n_
    lbo_ = {r["owner"].lower(): int(r.get("branches", 0)) for r in bankers}
    off_ = sorted(o_ for o_ in set(rep_) | set(lbo_) if rep_.get(o_, 0) != lbo_.get(o_, 0))
    reconcile("branches_by_banker", "Bankers whose replayed branches differ from the leaderboard", float(len(off_)), 0.0, "Standard Reserve indexer, leaderboard", 0, gate=False,
              absolute=True, note=", ".join(o_[:10] for o_ in off_[:8]))
    log("leaderboard", len(bankers), "bankers; ENS names in top 25:", sum(1 for l in leaders if l["ens"]))
    # ---------- reserve history, pool flows by holder group, STANDARD/ETH depth (extra.py) ----------
    x = extra.Ctx(cache=C, H={k: v for k, v in H.items()}, G=G, tip=tip, tip_ts=block_ts(tip), genesis_ts=genesis_ts, getlogs=getlogs, rpcb=rpcb, T=T,
                  PM=PM, SW=SW, ML=ML, TR=TR, pad=pad, STD=STD, USDG=USDG, POSM=POSM, SEED_BLOCK=SEED_BLOCK, bal=bal,
                  pos_ids=[q["id"] for q in pos], lp_liq_now=sum(q["liq"] for q in pos), log=log, rpc=rpc, sel=sel, B=ts_block, SV=SV,
                  INIT="0x" + keccak(b"Initialize(bytes32,address,address,uint24,int24,address,uint160,int24)").hex())
    lp_pools = {p_["stock"]: {"pool": pid_, "isEth": p_["stockAddr"].lower() == ZERO, "stockAddr": p_["stockAddr"], "usdg0": p_["usdg0"], "tier": p_["fee"], "spacing": p_["spacing"]} for pid_, p_ in pools.items()}
    pfees = extra.pool_fees(x, lp_pools, extra.LPAD["routers"])   # the reserve's pool fees, replayed swap by swap; replaces the estimate from the swap cache
    for row in series:
        if "spFee" not in row and not any(row["date"] in pfees[s_]["days"] for s_ in lp_pools): continue
        f_ = {s_: (pfees[s_]["days"].get(row["date"]) or [0.0] * 4) for s_ in lp_pools}
        for s_, v_ in f_.items(): row["spFee_" + s_] = round(v_[2], 6)
        row["spFee"] = round(sum(v_[2] for v_ in f_.values()), 6); row["spFeeLpad"] = round(sum(v_[3] for v_ in f_.values()), 6)
    closes = extra.pool_closes(x, {**{pid_: SEED_BLOCK for pid_ in pools}, STD_POOL: G})
    today_parts = {"total": reserve["totalUsd"], "eth": (reserve["safeEth"] + reserve["contractionEth"] + reserve["expansionEth"]) * ethusd, "usdg": reserve["safeUsdg"],
                   "stocks": reserve["safeStockUsd"], "lp": {s_: v_["valueUSD"] for s_, v_ in lp.items()}}
    res_hist, res_chk = extra.reserve_history(x, lp_pools, closes, eth_day, epochs, dl, today_parts)
    log("reserve history", len(res_hist), "days; forward-from-zero checks (0 = ties):", res_chk)
    for k_, v_ in res_chk.items():
        if k_.startswith(("eth_", "tok_")):
            a_, s_ = k_.split("_", 1); unit_ = "ETH" if a_ == "eth" else s_
            reconcile("reserve_" + k_, f"Reserve {unit_}{'' if a_ == 'tok' else ' in the ' + ('Safe' if s_ == 'safe' else s_ + ' vault')}, summed from zero", v_, 0.0, "balance at the compile block",
               1e-4, absolute=True, unit=unit_)
    reconcile("reserve_lp", "Reserve position liquidity, summed from events", 1 + res_chk.get("lp_liquidity", 0), 1.0, "positions read at the compile block", 1e-6)
    reconcile("reserve_today", "Reserve assets today, rebuilt from events", 1 + res_chk.get("today_rebuilt_vs_read", 0), 1.0, "balances and positions read at the compile block", 0.005)
    for k_ in sorted(hist_prev := jload(os.path.join(D, "history.json"), {})):
        if hist_prev[k_].get("reserveUsd") and k_ in res_hist: log("  reserve", k_, "snapshot", round(hist_prev[k_]["reserveUsd"]), "rebuilt close", round(res_hist[k_]["total"]))
    pf = extra.pool_flows(x)
    bankers = {(e.get("actor") or "").lower() for k_ in ("charter-created", "deposited", "withdrawn", "licenses-purchased", "branches-opened", "checked-in") for e in act[k_]}
    bankers |= {r_["owner"].lower() for r_ in lbd.get("bankers", [])}; bankers.discard("")
    sbh = {"0x" + l_["topics"][1][-40:] for l_ in getlogs({"address": STD, "topics": [TR, None, pad(H["sbills"])]}, int(sb.get("deploymentBlock") or G), tip, 4_000_000)}
    names = dict(wl); names[PM.lower()] = "pool"; names.update({H["feeSplitter"].lower(): "feeSplitter", H["taxHook"].lower(): "taxHook", H["expansionVault"].lower(): "expansion"})
    grp, sellers, grp_stats = extra.flows_by_group(x, pf, names, bankers, sbh, H["teamWallet"].lower(), genesis_ts, dl)
    log("pool flows", len(pf["rows"]), "rows;", grp_stats, "| bankers", len(bankers), "S-Bill holders", len(sbh))
    fee_lp = 0.01; s0 = ecall(SV, sel("getSlot0(bytes32)") + STD_POOL[2:], BT); sp_now = int(s0[2:66], 16) / 2 ** 96
    depth = extra.std_depth(x, STD_POOL, sp_now, ethusd, closes, eth_day, dl, fee_lp, int(snap["tax"]["buyTaxNowBps"]) / 1e4, int(snap["tax"]["sellTaxNowBps"]) / 1e4, H["polManager"].lower())
    log("depth", {k_: (round(v_) if isinstance(v_, float) else v_) for k_, v_ in depth.items() if k_ in ("bid2", "ask2", "bid5", "ask5", "protocolShare", "positions")})
    # STANDARD price: DexScreener and GeckoTerminal against the pool's own price on chain, valued at Coinbase's ETH price
    reconcile("price_live", "STANDARD price, DexScreener", px, ethusd / (sp_now * sp_now), "STANDARD/ETH pool price at the compile block × Coinbase ETH", 0.02)
    std_c = closes.get(STD_POOL, {}); gt_days = {day(r_[0]) for r_ in ohl}; worst_ = None
    for d_ in [d_ for d_ in dl if d_ < today][-14:]:
        c_ = std_c.get(d_); e_ = eth_day.get(d_)
        if d_ not in gt_days or not c_ or not e_: continue
        g_ = abs(price_day[d_] / (e_ / (c_ / 2 ** 96) ** 2) - 1)
        if worst_ is None or g_ > worst_[0]: worst_ = (g_, d_, price_day[d_], e_ / (c_ / 2 ** 96) ** 2)
    if worst_: reconcile("price_closes", f"STANDARD daily close, GeckoTerminal, widest of 14 days ({worst_[1]})", worst_[2], worst_[3], "last pool trade of the day on chain × Coinbase ETH close", 0.025)
    yrow_ = next((r_ for r_ in ohl if day(r_[0]) == (dt.date.fromisoformat(today) - dt.timedelta(1)).isoformat()), None)
    reconcile("price_gt_fresh", "GeckoTerminal close for yesterday, read after the day ended", 1.0 if yrow_ and len(yrow_) > 6 and yrow_[6] >= yrow_[0] + 86400 else 0.0, 1.0,
              "GeckoTerminal daily candles", 0)
    reconcile("eth_fresh", "Coinbase has yesterday’s ETH close", 1.0 if (dt.date.fromisoformat(today) - dt.timedelta(1)).isoformat() in eth_day else 0.0, 1.0, "Coinbase daily candles", 0)
    reconcile("mcap_dexscreener", "Market cap, circulating supply", px * total_supply, dstd.get("marketCap") or dstd.get("fdv"), "DexScreener market cap", 0.02, gate=False)
    ix_lag = block_ts(tip) - int(snap.get("blockTimestamp") or 0)
    reconcile("indexer_lag", "Indexer snapshot age at the compile block, seconds", float(max(0, ix_lag)), 0.0, "Standard Reserve indexer", 1800, absolute=True, unit="s")
    for row in series:
        d_ = row["date"]; g_ = grp.get(d_, {})
        rp_ = res_hist.get(d_); row["reserveUsd"] = rp_["total"] if rp_ else None; row["reserveParts"] = rp_
        row["mktNet"] = round(g_.get("mktNet", 0.0), 6); row["protNet"] = round(g_.get("protNet", 0.0), 6)
        for k_ in ("team", "bankers", "sbills", "active", "launch", "other"): row["sell_" + k_] = round(g_.get("sell_" + k_, 0.0), 6)
        if d_ in depth["hist"]: row.update(depth["hist"][d_])
    out["sellers"] = sellers; out["depth"] = {k_: v_ for k_, v_ in depth.items() if k_ != "hist"}; out["checks"] = res_chk
    ids_ = {"0x" + format(i_, "064x") for i_ in pm["ids"]}   # the reserve's own liquidity changes: a withdrawal or fee collection is a zero or negative change
    mine_ = [r_ for r_ in jload(os.path.join(C, "lp_mods.json"), {"rows": []})["rows"] if r_[5] in ids_]
    wd_ = [r_ for r_ in mine_ if int(r_[4]) <= 0]
    out["lpChanges"] = {"adds": sum(1 for r_ in mine_ if int(r_[4]) > 0), "withdrawals": len(wd_), "lastAdd": day(T(max((r_[0] for r_ in mine_ if int(r_[4]) > 0), default=SEED_BLOCK))),
                        "lastWithdrawal": day(T(max(r_[0] for r_ in wd_))) if wd_ else None}
    # every venue for each reserve asset; the reserve's position against holding; who executes swaps in the reserve's pools
    reg, keys, vsw, vlq, vcu = extra.venue_scan(x, stock_ds, {p_["pool"] for p_ in lp_pools.values()})
    shares = extra.chain_shares(x, reg, keys, vsw, vlq, vcu, lp_pools, closes, eth_day, dl, res_hist)
    fee_tok = collections.defaultdict(dict)   # fees earned per day in token units, so the P&L marks them at each day's close
    for s_ in lp_pools:
        for d_, v_ in pfees[s_]["days"].items(): fee_tok[d_][s_] = (v_[0], v_[1])
    pnl = extra.lp_pnl(x, lp_pools, closes, dl, res_hist, fee_tok)
    for s_, p_ in lp_pools.items():   # the replay's fees not yet collected, at today's pool price, against the same fees read from the positions
        u0_, u1_ = pfees[s_]["uncollected"]; px_ = (lp.get(s_) or {}).get("price"); owed_ = ((lp.get(s_) or {}).get("feesOwed") or {}).get("usd")
        ours_ = (u0_ / 1e6 + u1_ / 1e18 * px_ if p_["usdg0"] else u0_ / 1e18 * px_ + u1_ / 1e6) if px_ else None
        last_ = max((d_ for d_ in pnl if s_ in pnl[d_]), default=None); c0_, c1_ = pfees[s_]["collected"]
        coll_ = (c0_ / 1e6 + c1_ / 1e18 * px_ if p_["usdg0"] else c0_ / 1e18 * px_ + c1_ / 1e6) if px_ else None
        reconcile("pnlfees_" + s_, f"{s_ if s_ != 'ETH' else 'ETH/USDG'} pool P&L, fees to date at the last close", pnl[last_][s_]["fees"] if last_ else None,
                  owed_ + coll_ if owed_ is not None and coll_ is not None else None, "uncollected fees read from the positions, plus fees settled to the Safe, at today’s pool price",
                  0.01, unit="USD")
        reconcile("poolfees_" + s_, f"{s_ if s_ != 'ETH' else 'ETH/USDG'} pool fees not yet collected, replayed from swaps, at today’s pool price", ours_, owed_,
           "uncollected fees read from the reserve’s positions", 0.02, unit="USD", note=f"{pfees[s_]['mismatch']} swaps whose reported liquidity differed from the replay")
    yday = (dt.datetime.fromtimestamp(x.tip_ts, dt.timezone.utc).date() - dt.timedelta(1)).isoformat()   # complete days only
    cp = extra.counterparties(x, reg, lp_pools, "2026-10-14", yday)
    cls = extra.cpty_classes(cp, {s_: p_["tier"] for s_, p_ in lp_pools.items()}, routers=set(extra.LPAD["routers"]))
    lpad, lpad_held = extra.launchpad(x, lp_pools, closes, eth_day)
    for row in series:
        d_ = row["date"]; row.update({k_: v_ for k_, v_ in (shares.get(d_) or {}).items()}); row.update(cls.get(d_, {})); row.update(lpad.get(d_, {}))
        for s_ in lp_pools:   # the reserve's share of chain volume is the volume its liquidity served, not the whole pool's (it shares the ETH/USDG pool)
            if row.get("chainVol_" + s_): row["volShare_" + s_] = (row.get("spVolMine_" + s_) or 0) / row["chainVol_" + s_]
        for s_, v_ in (pnl.get(d_) or {}).items(): row.update({f"lpVal_{s_}": v_["lp"], f"holdVal_{s_}": v_["hold"], f"lpCost_{s_}": v_["cost"], f"lpFees_{s_}": v_["fees"]})
    # King of the Markets standings and the indexer's own launchpad fee total (the markets API allows only standardreserve.xyz in the browser)
    MK = "https://markets.standardreserve.xyz/v1/"
    ks_, kp_ = get(MK + "pilot/summary", tries=2), get(MK + "pilot/pool?limit=1", tries=2)
    lp_px = {s_: v_["price"] for s_, v_ in lp.items()}; lp_px.update({"USDG": 1.0, "WETH": ethusd})
    out["launchpad"] = {"feeSafe": extra.LPAD["feeSafe"], "held": lpad_held, "heldUsd": sum(a_ * (lp_px.get(s_) or 0) for s_, a_ in lpad_held.items()),
                        "feeSafeEth": int(rpc("eth_getBalance", [extra.LPAD["feeSafe"], "latest"]).get("result") or "0x0", 16) / 1e18,
                        "indexerFeesUsd": kp_.get("feesUsd"), "indexerAsOf": kp_.get("asOfTime"),
                        "season": ks_.get("season"), "teams": ks_.get("countries"), "seedUsd": 1_100_000}
    log("launchpad: fee Safe", {k_: round(v_, 3) for k_, v_ in lpad_held.items()}, "| received, all days", round(sum(v_.get("lpadSafe", 0) for v_ in lpad.values())),
        "| indexer", kp_.get("feesUsd"))
    reconcile("launchpad_fees", "Launchpad fees received by the fee Safe, at daily closes", sum(v_.get("lpadSafe", 0) for v_ in lpad.values()), kp_.get("feesUsd"),
       "launchpad markets API, fees at trade time", 0.03, gate=False, unit="USD")
    chk_ = [(row["date"], s_, round(row.get("poolVolChain_" + s_) or 0), round(row.get("spVol_" + s_) or 0)) for row in series[-3:-1] for s_ in lp_pools]
    for row in series[-3:-1]:
        a_ = sum(row.get("poolVolChain_" + s_) or 0 for s_ in lp_pools); b_ = sum(row.get("spVol_" + s_) or 0 for s_ in lp_pools)
        reconcile("volume_" + row["date"], f"Reserve pool volume {row['date']}, swap cache", b_, a_, "independent scan of the same pools’ swap logs", 0.001, unit="USD")
    log("venues", len(reg), "| reserve pool volume, chain scan vs swap cache:", chk_, "| counterparty days", len(cp["days"]))
    hist = jload(os.path.join(D, "history.json"), {})
    hist[today] = {k: v for k, v in live.items() if k not in ("poolCtx", "balances", "lp", "sbills", "reserve")}
    hist[today]["lp"] = {s: {"stock": v["stock"], "usdg": v["usdg"], "valueUSD": v["valueUSD"], "price": v["price"], "feesOwedUsd": v["feesOwed"]["usd"]} for s, v in lp.items()}
    hist[today]["reserveUsd"] = reserve["totalUsd"]; hist[today]["sbillsRate"] = sbills["rate"]; hist[today]["sbillsLocked"] = sbills["locked"]; hist[today]["reserve"] = reserve
    hist[today]["srLiqShare"] = {s: (v["srLiq"] / v["totalLiq"] if v["totalLiq"] else None) for s, v in pool_ctx.items()}
    jsave(os.path.join(D, "history.json"), hist)
    # addresses and the compile block, so the page can replay the blocks after it (balances, transfers, indexer events) in the browser
    out["addrs"] = {**{k: v.lower() for k, v in H.items()}, "STANDARD": STD.lower(), "poolManager": PM.lower(), "charterAuction": CA, "zero": ZERO}
    out["tipTs"] = block_ts(tip); out["genesisTs"] = genesis_ts; out["foundingCharters"] = founding
    out.update({"live": live, "epochs": epochs, "charters": charters, "licensePeriods": lic_periods, "series": series, "history": hist,
                "swapsBySender": {}, "elapsed": round(time.time() - t_start)})
    # sender classes for stock pools (last 7d)
    cut = now - 7 * 86400; bys = collections.defaultdict(lambda: [0.0, 0.0, 0])
    for b, s, usdg, fee, snd, *rest in sw["rows"]:
        if T(b) < cut: continue
        cls = "zero-fee" if fee == 0 else snd
        bys[cls][0] += usdg; bys[cls][1] += usdg * fee / 1e6; bys[cls][2] += 1
    out["swapsBySender"] = {k: {"vol": v[0], "fee": v[1], "n": v[2]} for k, v in sorted(bys.items(), key=lambda x: -x[1][0])[:8]}
    jsave(os.path.join(D, "dash.json"), out)
    log("done in", out["elapsed"], "s; days", len(series))

if __name__ == "__main__":
    main()
