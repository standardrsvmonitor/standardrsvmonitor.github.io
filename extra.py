"""Reserve history, pool flows by holder group, and STANDARD/ETH market depth, for pull.py.
Every scan is incremental or cheap enough to repeat; each reconstruction logs a check against today's on-chain state."""
import os, json, math, bisect, collections, datetime as dt

SAFE_RECEIVED = "0x3d0ce9bfc3ed7d6862dbb28b2dea94561fe714a1b4d019aa8af39730d1ad7c3d"   # SafeReceived(sender indexed, value)
SAFE_TX = "0x66753cd2356569ee081232e3be8909b950e0a76c1f8460c3a5e3c2be32b11bed"         # SafeMultiSigTransaction(to, value, data, operation, ...)
SAFE_OK = "0x442e715f626346e8c54381002da614f62bee8d27386535b2521ec8540898556e"         # ExecutionSuccess(txHash, payment)
CV_BUY = "0x8e8412cac6b961b95ef832e2bac486977bbd29eb9725f9eddd97f3380c31f649"          # contraction vault buyback: (ethIn, standardOut)
EV_FWD = "0x98c9bf0d2b79ecbf5d1527aee70d8b86d4761c9f5234c3ae6f73a8ef61fc6c54"          # expansion vault forward to the reserve: (value)
GM_FINAL = "0x9dd2a3de967ad06808d0896233a2f261db7cd96284bb119f9bcd1ae9e71fa584"        # genesis minter finalize: [charters, raised, team, pool, expansion seed, contraction seed, ...]
GENESIS_MINTER = "0xF54B589EADC2aaE98b96DaD58d89BCBF27503e46"
PROTOCOL = {"zero", "pool", "contraction", "polBuyback", "incentives", "sbills", "bank", "safe", "polManager", "feeSplitter", "taxHook", "expansion"}


def s256(h):
    x = int(h, 16); return x - (1 << 256) if x >= (1 << 255) else x


def words(data):
    d = data[2:]; return [d[i:i + 64] for i in range(0, len(d), 64)]


def day(ts): return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%d")


def day_end(d): return int(dt.datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp()) + 86400


class Ctx:
    """What pull.py hands over: RPC helpers, block-time interpolation, the compile block and the address book."""
    def __init__(self, **kw): self.__dict__.update(kw)
    def jl(self, name, default):
        p = os.path.join(self.cache, name)
        try: return json.load(open(p))
        except Exception: return default
    def js(self, name, o): json.dump(o, open(os.path.join(self.cache, name), "w"))


# ---------- daily closing sqrtPrice per pool, from Swap logs ----------
def pool_closes(x, pids_from):
    """{pid: {date: sqrtPriceX96 of the day's last swap}}; pids_from maps pool id to the block its scan starts at."""
    c = x.jl("pool_close.json", {})
    for pid, start in pids_from.items():
        e = c.setdefault(pid, {"last": start - 1, "close": {}}); x.log("pool closes", pid[:10], "from", e["last"] + 1)
        if e["last"] < x.tip:
            for l in x.getlogs({"address": x.PM, "topics": [x.SW, pid]}, e["last"] + 1, x.tip):
                e["close"][day(x.T(int(l["blockNumber"], 16)))] = str(int(words(l["data"])[2], 16))
            e["last"] = x.tip
    x.js("pool_close.json", c)
    return {pid: {d: int(v) for d, v in e["close"].items()} for pid, e in c.items()}


def close_on(closes, d, first=False):
    """Last close on or before date d; with first=True, the pool's first close for dates before it traded (equities held before their pool opened)."""
    ks = sorted(closes); i = bisect.bisect_right(ks, d)
    return closes[ks[i - 1]] if i else (closes[ks[0]] if first and ks else None)


def lp_amounts(L, tl, tu, sp):
    """Token amounts (raw) of a v4 position with liquidity L over [tl, tu) at sqrtPrice sp (raw units)."""
    a = math.sqrt(1.0001 ** tl); b = math.sqrt(1.0001 ** tu); s = min(max(sp, a), b)
    return L * (b - s) / (s * b), L * (s - a)


# ---------- reserve value by day ----------
def reserve_history(x, lp_pools, closes, eth_day, epochs, dates, today_parts):
    """Reserve in USD at each day's close: ETH in the Safe and both policy vaults, USDG and equities held by the Safe, and the Safe's
    Uniswap v4 positions at the day's closing pool price. ETH and token balances are walked back from balances at the compile block;
    position liquidity is summed forward from ModifyLiquidity events. Returns ({date: {total, eth, usdg, stocks, lp}}, checks)."""
    H, G, tip = x.H, x.G, x.tip
    safe = H["reserveSafe"].lower()
    ev = []                                         # (ts, bucket, delta ETH)
    x.log("reserve: safe logs"); sl = x.getlogs({"address": H["reserveSafe"]}, G, tip, 4000000)
    ok = {l["transactionHash"] for l in sl if l["topics"][0] == SAFE_OK}
    fs_to_safe = []
    for l in sl:
        t0 = l["topics"][0]; ts = x.T(int(l["blockNumber"], 16))
        if t0 == SAFE_RECEIVED:
            v = int(l["data"], 16) / 1e18; ev.append((ts, "safe", v))
            if "0x" + l["topics"][1][-40:] == H["feeSplitter"].lower(): fs_to_safe.append(v)
        elif t0 == SAFE_TX and l["transactionHash"] in ok:
            w = words(l["data"]); to = "0x" + w[0][-40:]; val = int(w[1], 16); off = int(w[2], 16) // 32; op = int(w[3], 16)
            n = int(w[off], 16); data = l["data"][2:][(off + 1) * 64:(off + 1) * 64 + n * 2]
            if op == 1 and data[:8] == "8d80ff0a":       # MultiSend: operation(1) to(20) value(32) length(32) data
                p = data[8:]; o2 = int(p[:64], 16) * 2; n2 = int(p[o2:o2 + 64], 16) * 2; pk = p[o2 + 64:o2 + 64 + n2]; i = 0
                while i < len(pk):
                    ito = "0x" + pk[i + 2:i + 42]; ival = int(pk[i + 42:i + 106], 16); dl = int(pk[i + 106:i + 170], 16); i += 170 + dl * 2
                    if ito != safe: val += ival
            if to == safe and op == 0: val = 0
            if val: ev.append((ts, "safe", -val / 1e18))
    gm = x.getlogs({"address": GENESIS_MINTER, "topics": [GM_FINAL]}, G - 200000, G + 200000, 4000000)
    seed_x = seed_c = 0.0
    if gm:
        w = words(gm[0]["data"]); seed_x, seed_c = int(w[4], 16) / 1e18, int(w[5], 16) / 1e18
        ev += [(x.genesis_ts, "expansion", seed_x), (x.genesis_ts, "contraction", seed_c)]
    for e in epochs:
        exp = e["expansion"] in (True, "true", 1)
        if not exp: ev.append((e["settledAt"], "contraction", e["toVault"]))
        else:   # after the first expansion vault forward, expansion routing went to the Safe directly (SafeReceived from the fee splitter)
            m = next((i for i, v in enumerate(fs_to_safe) if abs(v - e["toVault"]) < 1e-6), None)
            if m is None: ev.append((e["settledAt"], "expansion", e["toVault"]))
            else: fs_to_safe.pop(m)
    x.log("reserve: vault logs")
    for l in x.getlogs({"address": H["contractionVault"], "topics": [CV_BUY]}, G, tip, 4000000):
        ev.append((x.T(int(l["blockNumber"], 16)), "contraction", -int(words(l["data"])[0], 16) / 1e18))
    for l in x.getlogs({"address": H["expansionVault"], "topics": [EV_FWD]}, G, tip, 4000000):
        ev.append((x.T(int(l["blockNumber"], 16)), "expansion", -int(l["data"], 16) / 1e18))
    now_eth = {"safe": x.bal["reserveSafe"]["ETH"], "contraction": x.bal["contractionVault"]["ETH"], "expansion": x.bal["expansionVault"]["ETH"]}
    fwd = collections.Counter()
    for _, k, v in ev: fwd[k] += v
    checks = {"eth_" + k: round(fwd[k] - now_eth[k], 6) for k in now_eth}   # forward from zero against the balance at the compile block
    # ERC-20 balances of the Safe: USDG and the equities
    toks = {"USDG": (x.USDG, 6)}
    for s, p in lp_pools.items():
        if not p["isEth"]: toks[s] = (p["stockAddr"], 18)
    tev = []; x.log("reserve: token transfers", list(toks))
    for s, (ta, dec) in toks.items():
        for direction, topics in ((1, [x.TR, None, x.pad(safe)]), (-1, [x.TR, x.pad(safe)])):
            for l in x.getlogs({"address": ta, "topics": topics}, G, tip, 4000000):
                tev.append((x.T(int(l["blockNumber"], 16)), s, direction * int(l["data"], 16) / 10 ** dec))
    tf = collections.Counter()
    for _, s, v in tev: tf[s] += v
    now_tok = {s: x.bal["reserveSafe"].get(s, 0.0) for s in toks}
    checks.update({"tok_" + s: round(tf[s] - now_tok[s], 6) for s in toks})
    # the Safe's positions: liquidity by ModifyLiquidity (salt = token id), range from the event
    ids = {"0x" + format(i, "064x") for i in x.pos_ids}
    pid_sym = {p["pool"]: s for s, p in lp_pools.items()}
    lm = x.jl("lp_mods.json", {"last": x.SEED_BLOCK - 1, "rows": []}); x.log("reserve: position liquidity from", lm["last"] + 1)
    if lm["last"] < tip:      # PositionManager liquidity changes in the reserve's pools, cached: [block, pool, tickLower, tickUpper, liquidityDelta, salt]
        for pid in pid_sym:   # one pool per query: the RPC limits OR-lists in a topic to 100k-block ranges
            for l in x.getlogs({"address": x.PM, "topics": [x.ML, pid, x.pad(x.POSM)]}, lm["last"] + 1, tip, 4000000):
                w = words(l["data"]); lm["rows"].append([int(l["blockNumber"], 16), l["topics"][1], s256(w[0]), s256(w[1]), str(s256(w[2])), "0x" + w[3]])
        lm["rows"].sort(key=lambda r: r[0])
        lm["last"] = tip; x.js("lp_mods.json", lm)
    mods = [(x.T(b), pid, tl, tu, int(dl)) for b, pid, tl, tu, dl, salt in lm["rows"] if salt in ids and pid in pid_sym]
    checks["lp_liquidity"] = round(sum(dl for *_, dl in mods) / max(1, x.lp_liq_now) - 1, 9)   # summed liquidity against the positions' liquidity now
    x.log("reserve: valuing", len(dates), "days"); # value by day
    out = {}
    for d in dates:
        t_end = day_end(d)
        eth_units = sum(now_eth.values()) - sum(v for ts, _, v in ev if ts >= t_end)
        tok_units = {s: now_tok[s] - sum(v for ts, s2, v in tev if s2 == s and ts >= t_end) for s in toks}
        px = {}
        for s, p in lp_pools.items():
            c = close_on(closes.get(p["pool"], {}), d, first=True)
            if c is None: px[s] = None; continue
            sp = c / 2 ** 96; P = sp * sp
            px[s] = (1e12 / P if P else 0) if p["usdg0"] else P * 1e18 / 1e6
        lp_usd = 0.0; lp_by = collections.Counter()
        rng = collections.defaultdict(int)
        for ts, pid, tl, tu, dl in mods:
            if ts < t_end: rng[(pid, tl, tu)] += dl
        for (pid, tl, tu), L in rng.items():
            s = pid_sym[pid]; p = lp_pools[s]; c = close_on(closes.get(pid, {}), d)
            if L <= 0 or c is None: continue
            a0, a1 = lp_amounts(L, tl, tu, c / 2 ** 96)
            usdg, stock = (a0 / 1e6, a1 / 1e18) if p["usdg0"] else (a1 / 1e6, a0 / 1e18)
            v = stock * (px[s] or 0) + usdg; lp_usd += v; lp_by[s] += v
        stock_usd = sum(tok_units[s] * (px.get(s) or 0) for s in toks if s != "USDG")
        e_px = eth_day.get(d)
        if e_px is None: continue
        out[d] = {"total": eth_units * e_px + tok_units["USDG"] + stock_usd + lp_usd, "eth": eth_units * e_px, "usdg": tok_units["USDG"], "stocks": stock_usd,
                  "lp": {s: lp_by.get(s, 0.0) for s in lp_pools}}
    if dates and today_parts is not None:       # today is the reserve read at the compile block, the same figures as the tile
        if dates[-1] in out: checks["today_rebuilt_vs_read"] = round(out[dates[-1]]["total"] / today_parts["total"] - 1, 6)
        out[dates[-1]] = today_parts
    return out, checks


# ---------- STANDARD flows with the pool, by counterparty and by the wallet that sent the transaction ----------
def pool_flows(x):
    """Incremental scan of every STANDARD transfer, keeping those into and out of the PoolManager. Rows: [block, counterparty index,
    signed amount (+ into the pool), end-wallet index or -1]. When the pool's counterparty only passes STANDARD through (a router or
    aggregator), the same transaction also moves STANDARD between it and the wallet on the other side; that wallet is the end wallet,
    followed for up to three hops. No per-transaction lookups, so the public RPC's rate limit is not an issue."""
    c = x.jl("pool_flows3.json", {"last": x.G - 1, "addrs": [], "rows": []})
    idx = {a: i for i, a in enumerate(c["addrs"])}
    def ix(a):
        if a not in idx: idx[a] = len(c["addrs"]); c["addrs"].append(a)
        return idx[a]
    pm, zero = x.PM.lower(), "0x" + "0" * 40
    def process(logs):
        bytx = collections.defaultdict(list)
        for l in logs:
            bytx[l["transactionHash"]].append((int(l["blockNumber"], 16), int(l["logIndex"], 16), "0x" + l["topics"][1][-40:], "0x" + l["topics"][2][-40:], int(l["data"], 16) / 1e18))
        for h, ts in bytx.items():
            ts.sort(key=lambda t: t[1])
            for b, _, f, t, a in ts:
                if pm not in (f, t) or f == t: continue
                sell = t == pm; cp = f if sell else t; end = cp
                for _ in range(3):   # follow STANDARD through intermediaries: into cp for a sale, out of cp for a purchase
                    nxt = [(a2, f2 if sell else t2) for _, _, f2, t2, a2 in ts if (t2 == end if sell else f2 == end) and (f2 if sell else t2) not in (pm, zero, end)]
                    if not nxt: break
                    end = max(nxt)[1]
                c["rows"].append([b, ix(cp), round(a if sell else -a, 6), ix(end) if end != cp else -1])
    if c["last"] < x.tip:
        lo = c["last"] + 1; step = 1_000_000; x.log("pool flows from", lo)
        while lo <= x.tip:
            hi = min(lo + step - 1, x.tip); r = x.rpc("eth_getLogs", [{"address": x.STD, "topics": [x.TR], "fromBlock": hex(lo), "toBlock": hex(hi)}], tries=4)
            if "error" in r:
                if step <= 2000: raise RuntimeError(r["error"])
                step //= 2; continue
            process(r["result"]); lo = hi + 1
            if step < 1_000_000: step = min(1_000_000, step * 2)
        c["last"] = x.tip; x.js("pool_flows3.json", c)
    x.log("pool flows:", len(c["rows"]), "rows,", sum(1 for r in c["rows"] if r[3] >= 0), "through intermediaries")
    return c


def flows_by_group(x, c, names, bankers, sbill_holders, team, genesis_ts, dates):
    """Daily net STANDARD sold into the pool by holder group (market counterparties only), the protocol's own net flow, and the
    trailing seven-day largest net sellers. Groups are exclusive, in priority order."""
    A = c["addrs"]; nrows = collections.Counter()
    def who(cp, e): return e if e >= 0 else cp
    first_buy = {}
    for b, cp, a, e in c["rows"]:
        if names.get(A[cp]) in PROTOCOL: continue
        w = who(cp, e); nrows[w] += 1
        if a < 0 and w not in first_buy: first_buy[w] = x.T(b)
    routers = {cp for b, cp, a, e in c["rows"] if e >= 0}
    def group(w, cp):
        aw, ac = A[w], A[cp]
        if team in (aw, ac): return "team"
        if aw in bankers or ac in bankers: return "bankers"
        if aw in sbill_holders or ac in sbill_holders: return "sbills"
        if nrows[w] >= 300: return "active"
        if first_buy.get(w, 9e18) < genesis_ts + 3 * 86400: return "launch"
        return "other"
    daily = collections.defaultdict(lambda: collections.defaultdict(float))
    seven = collections.defaultdict(lambda: [0.0, 0, 0, None])
    d7 = set(dates[-8:-1]) if len(dates) > 1 else set()                     # the last seven complete days
    for b, cp, a, e in c["rows"]:
        d = day(x.T(b)); nm = names.get(A[cp])
        if nm in PROTOCOL:
            daily[d]["protNet"] += a
            if nm == "polManager": daily[d]["feesToTeam"] += -a
            continue
        w = who(cp, e); g = group(w, cp)
        daily[d]["mktNet"] += a; daily[d]["sell_" + g] += a
        if d in d7:
            r = seven[w]; r[0] += a; r[1 if a > 0 else 2] += 1; r[3] = g
    top = sorted(seven.items(), key=lambda kv: -kv[1][0])[:10]
    top = [{"addr": A[w], "group": r[3], "net": r[0], "sells": r[1], "buys": r[2]} for w, r in top if r[0] > 0]
    stats = {"routers": len(routers), "wallets": len(nrows)}
    return daily, top, stats


# ---------- STANDARD/ETH depth and slippage ----------
def std_positions(x, pid):
    """All open liquidity in the STANDARD/ETH pool by range, from ModifyLiquidity events (every provider), with their timestamps."""
    out = []
    for l in x.getlogs({"address": x.PM, "topics": [x.ML, pid]}, x.G, x.tip, 4000000):
        w = words(l["data"]); out.append((x.T(int(l["blockNumber"], 16)), s256(w[0]), s256(w[1]), s256(w[2]), "0x" + l["topics"][2][-40:]))
    return out


def ranges_at(mods, t_end):
    r = collections.defaultdict(int)
    for ts, tl, tu, dl, _ in mods:
        if ts < t_end: r[(tl, tu)] += dl
    return [(math.sqrt(1.0001 ** tl), math.sqrt(1.0001 ** tu), L) for (tl, tu), L in r.items() if L > 0]


def _active(rng, s, down):
    """Liquidity in force just below (down) or above s."""
    return sum(L for a, b, L in rng if (a < s <= b if down else a <= s < b))


def swap(rng, sp, amount, eth_in):
    """Walk a swap through the ranges. eth_in: ETH (token0) in, price falls; else STANDARD (token1) in, price rises.
    Returns (amount out, sqrtPrice after). Amounts are raw (both tokens have 18 decimals)."""
    bounds = sorted({v for a, b, L in rng for v in (a, b)})
    s, rem, out = sp, amount, 0.0
    while rem > 1e-9:
        L = _active(rng, s, eth_in)
        if eth_in:
            nxt = max([v for v in bounds if v < s], default=None)
            if L <= 0:
                if nxt is None: break
                s = nxt; continue
            need = L * (1 / nxt - 1 / s) if nxt else float("inf")
            if rem >= need: out += L * (s - nxt); rem -= need; s = nxt
            else: s2 = 1 / (1 / s + rem / L); out += L * (s - s2); s = s2; rem = 0
        else:
            nxt = min([v for v in bounds if v > s], default=None)
            if L <= 0:
                if nxt is None: break
                s = nxt; continue
            need = L * (nxt - s) if nxt else float("inf")
            if rem >= need: out += L * (1 / s - 1 / nxt); rem -= need; s = nxt
            else: s2 = s + rem / L; out += L * (1 / s - 1 / s2); s = s2; rem = 0
    return out, s


def depth_usd(rng, sp, pct, ethusd):
    """USD of ETH that moves STANDARD's price by pct: bid (sellers receive) and ask (buyers pay)."""
    s_dn = sp * math.sqrt(1 / (1 - pct))     # STANDARD price down pct: STANDARD per ETH up
    s_up = sp * math.sqrt(1 / (1 + pct))     # STANDARD price up pct
    bid = ask = 0.0
    for a, b, L in rng:
        lo, hi = max(a, sp), min(b, s_dn)
        if hi > lo: bid += L * (1 / lo - 1 / hi)
        lo, hi = max(a, s_up), min(b, sp)
        if hi > lo: ask += L * (1 / lo - 1 / hi)
    return bid / 1e18 * ethusd, ask / 1e18 * ethusd


def std_depth(x, pid, sp_now, ethusd, closes, eth_day, dates, fee, tax_buy, tax_sell, protocol_lp):
    mods = std_positions(x, pid)
    rng = ranges_at(mods, x.tip_ts + 1)
    mid = 1 / (sp_now * sp_now)                                    # ETH per STANDARD
    sizes = [10_000, 50_000, 100_000, 250_000, 500_000, 1_000_000]
    slip = []
    for usd in sizes:
        e_in = usd / ethusd * 1e18
        out_b, _ = swap(rng, sp_now, e_in * (1 - fee) * (1 - tax_buy), True)
        out_b_raw, _ = swap(rng, sp_now, e_in, True)
        std_in = usd / ethusd / mid * 1e18
        out_s, _ = swap(rng, sp_now, std_in * (1 - fee), False)
        out_s_raw, _ = swap(rng, sp_now, std_in, False)
        slip.append({"usd": usd,
                     "buyImpact": (e_in / out_b_raw) / mid - 1 if out_b_raw else None, "buyAllIn": (e_in / out_b) / mid - 1 if out_b else None,
                     "sellImpact": 1 - (out_s_raw / std_in) / mid if std_in else None, "sellAllIn": 1 - (out_s * (1 - tax_sell) / std_in) / mid if std_in else None})
    b2, a2 = depth_usd(rng, sp_now, 0.02, ethusd); b5, a5 = depth_usd(rng, sp_now, 0.05, ethusd)
    in_range = sum(L for a, b, L in rng if a <= sp_now < b)
    prot = collections.defaultdict(int)
    for ts, tl, tu, dl, sender in mods:
        if sender == protocol_lp: prot[(tl, tu)] += dl
    prot_in = sum(L for (tl, tu), L in prot.items() if L > 0 and math.sqrt(1.0001 ** tl) <= sp_now < math.sqrt(1.0001 ** tu))
    hist = {}
    for d in dates:
        c = close_on(closes.get(pid, {}), d); e = eth_day.get(d)
        if c is None or e is None: continue
        rg = ranges_at(mods, day_end(d)); bd, ak = depth_usd(rg, c / 2 ** 96, 0.02, e); b5_, a5_ = depth_usd(rg, c / 2 ** 96, 0.05, e)
        hist[d] = {"bid2": bd, "ask2": ak, "bid5": b5_, "ask5": a5_}
    return {"bid2": b2, "ask2": a2, "bid5": b5, "ask5": a5, "slip": slip, "fee": fee, "taxBuy": tax_buy, "taxSell": tax_sell,
            "protocolShare": prot_in / in_range if in_range else None, "positions": sum(1 for _ in rng), "hist": hist}


# ---------- every venue for each reserve asset: daily volume and liquidity, from the chain ----------
def _bytes25(pid): return pid[2:52] + "00" * 7


def v4_keys(x, ids):
    """Pool keys for Uniswap v4 pool ids, via PositionManager.poolKeys(bytes25); cached."""
    import time
    c = x.jl("v4_keys.json", {})
    need = [i for i in ids if i not in c]
    for k in range(0, len(need), 10):
        part = need[k:k + 10]
        for t in range(6):
            try: res = x.rpcb([("eth_call", [{"to": x.POSM, "data": x.sel("poolKeys(bytes25)") + _bytes25(i)}, "latest"]) for i in part]); break
            except Exception: time.sleep(5 * (t + 1))
        else: continue
        for i, r in zip(part, res):
            if r and len(r) >= 2 + 64 * 5:
                w = words(r); c[i] = ["0x" + w[0][-40:], "0x" + w[1][-40:], int(w[2], 16), s256(w[3]), "0x" + w[4][-40:]]
        time.sleep(0.3)
    x.js("v4_keys.json", c)
    return c


def decimals(x, toks):
    import time
    c = x.jl("decimals.json", {"0x" + "0" * 40: 18})
    need = [t for t in toks if t not in c]
    for k in range(0, len(need), 10):
        part = need[k:k + 10]
        try: res = x.rpcb([("eth_call", [{"to": t, "data": "0x313ce567"}, "latest"]) for t in part])
        except Exception: time.sleep(5); continue
        for t, r in zip(part, res): c[t] = int(r, 16) if r and r != "0x" else 18
        time.sleep(0.3)
    x.js("decimals.json", c)
    return c


def venue_scan(x, pairs, reserve_pids):
    """Incremental per-venue daily aggregates. v4 pools: swap amounts and last sqrtPrice by day, net liquidity by range by day; for the
    reserve's own pools also the swap callers with sample transactions. Custodial pools (v2, v3, Solidly-type, Metric and others): the
    asset's and quote token's flows in and out of the pool contract, split into swaps (opposite directions in one transaction) and
    liquidity changes (same direction)."""
    reg = []
    for sym, plist in pairs.items():
        if not isinstance(plist, list): continue
        for p in plist:
            a = (p.get("pairAddress") or "").lower()
            if not a: continue
            cts = (p.get("pairCreatedAt") or 0) / 1000
            cb = x.B(cts - 86400) if cts - 86400 >= x.genesis_ts else 0          # anchors begin at genesis; older pools' liquidity is scanned from block 0
            reg.append({"sym": sym, "id": a, "v4": len(a) == 66, "liqStart": max(0, cb), "start": max(cb, x.SEED_BLOCK - 3_000_000), "dex": p.get("dexId"), "label": ((p.get("labels") or [""]) or [""])[0],
                        "base": (p.get("baseToken") or {}).get("address", "").lower(), "quote": (p.get("quoteToken") or {}).get("address", "").lower(),
                        "bsym": (p.get("baseToken") or {}).get("symbol"), "qsym": (p.get("quoteToken") or {}).get("symbol")})
    keys = v4_keys(x, [r["id"] for r in reg if r["v4"]])
    sw = x.jl("venue_v4.json", {}); lq = x.jl("venue_v4liq.json", {}); cu = x.jl("venue_cust.json", {})
    for r in reg:
        if not r["v4"] or r["id"] not in keys: continue
        e = sw.setdefault(r["id"], {"last": r["start"] - 1, "d": {}, "snd": {}})
        if e["last"] < r["start"]: x.log("venue v4 backfill", r["sym"], r["id"][:10], "from", r["start"])
        if e["last"] < x.tip:
            mine = r["id"] in reserve_pids
            for l in x.getlogs({"address": x.PM, "topics": [x.SW, r["id"]]}, e["last"] + 1, x.tip, 4000000):
                w = words(l["data"]); d = day(x.T(int(l["blockNumber"], 16)))
                v = e["d"].setdefault(d, [0.0, 0.0, None]); v[0] += abs(s256(w[0])); v[1] += abs(s256(w[1])); v[2] = str(int(w[2], 16))
                if mine:
                    s = "0x" + l["topics"][2][-40:]; q = e["snd"].setdefault(s, [0, []]); q[0] += 1
                    if len(q[1]) < 12 and (not q[1] or q[0] % max(1, q[0] // 12 + 1) == 0): q[1].append(l["transactionHash"])
            e["last"] = x.tip
        f = lq.setdefault(r["id"], {"last": r["liqStart"] - 1, "d": {}})
        if f["last"] < x.tip:
            for l in x.getlogs({"address": x.PM, "topics": [x.ML, r["id"]]}, f["last"] + 1, x.tip, 4000000):
                w = words(l["data"]); d = day(x.T(int(l["blockNumber"], 16))); k = f"{s256(w[0])},{s256(w[1])}"
                dd = f["d"].setdefault(d, {}); dd[k] = str(int(dd.get(k, "0")) + s256(w[2]))
                if dd[k] == "0": dd.pop(k)
            f["last"] = x.tip
    import time
    quiet = [r["id"] for r in reg if r["v4"] and r["id"] in sw and not sw[r["id"]]["d"]]   # no swaps since the reserve's launch: price from slot0 now
    for k in range(0, len(quiet), 10):
        try: res = x.rpcb([("eth_call", [{"to": x.SV, "data": x.sel("getSlot0(bytes32)") + i[2:]}, "latest"]) for i in quiet[k:k + 10]])
        except Exception: time.sleep(5); continue
        for i, v in zip(quiet[k:k + 10], res):
            if v and len(v) >= 66: sw[i]["spNow"] = str(int(v[2:66], 16))
        time.sleep(0.3)
    x.js("venue_v4.json", sw); x.js("venue_v4liq.json", lq)
    cust = [r for r in reg if not r["v4"]]; calls = [(r["id"], t) for r in cust for t in {r["base"], r["quote"]}]
    for k in range(0, len(calls), 10):
        part = calls[k:k + 10]
        for t_ in range(6):
            try: res = x.rpcb([("eth_call", [{"to": t, "data": "0x70a08231" + x.pad(pid)[2:]}, hex(x.tip)]) for pid, t in part]); break
            except Exception: time.sleep(5 * (t_ + 1))
        else: res = [None] * len(part)
        for (pid, t), v in zip(part, res): cu.setdefault(pid, {"last": None, "d": {}}).setdefault("now", {})[t] = str(int(v, 16)) if v and v != "0x" else "0"
        time.sleep(0.3)
    for r in reg:
        if r["v4"]: continue
        e = cu.setdefault(r["id"], {"last": r["start"] - 1, "d": {}})
        if e.get("last") is None: e["last"] = r["start"] - 1
        if e["last"] < r["start"]: x.log("venue pool backfill", r["sym"], r["dex"], r["id"][:10], "from", r["start"])
        if e["last"] < x.tip:
            logs = []
            for tok in {r["base"], r["quote"]}:
                for topics in ([x.TR, x.pad(r["id"])], [x.TR, None, x.pad(r["id"])]):
                    logs += [(l, tok) for l in x.getlogs({"address": tok, "topics": topics}, e["last"] + 1, x.tip, 4000000)]
            bytx = collections.defaultdict(lambda: collections.defaultdict(float)); txd = {}
            for l, tok in logs:
                a = int(l["data"], 16); f_ = "0x" + l["topics"][1][-40:]; t_ = "0x" + l["topics"][2][-40:]
                sgn = 1 if t_ == r["id"] else -1 if f_ == r["id"] else 0
                if not sgn or f_ == t_: continue
                bytx[l["transactionHash"]][tok] += sgn * a; txd[l["transactionHash"]] = int(l["blockNumber"], 16)
            for h, fl in bytx.items():
                d = day(x.T(txd[h])); v = e["d"].setdefault(d, {})
                for tok, a in fl.items(): v["net_" + tok] = str(int(v.get("net_" + tok, "0")) + int(a))
                vals = list(fl.values())
                if len(vals) == 2 and vals[0] * vals[1] < 0:      # one token in, the other out: a swap through this pool
                    for tok, a in fl.items(): v["sw_" + tok] = str(int(v.get("sw_" + tok, "0")) + abs(int(a)))
            e["last"] = x.tip
    x.js("venue_v4.json", sw); x.js("venue_v4liq.json", lq); x.js("venue_cust.json", cu)
    return reg, keys, sw, lq, cu


def chain_shares(x, reg, keys, sw, lq, cu, lp_pools, closes, eth_day, dates, res_hist):
    """Per reserve asset and day: every listed venue's volume and liquidity in USD, the reserve pool's share of chain volume and the
    reserve position's share of chain liquidity, the reserve pool's rank by liquidity and the largest other venue."""
    zero = "0x" + "0" * 40; usdg = x.USDG.lower()
    sym_of = {}
    for r in reg: sym_of[r["base"]] = r["bsym"]; sym_of[r["quote"]] = r["qsym"]
    eth_like = {zero} | {a for a, s in sym_of.items() if s in ("WETH", "ETH")}
    dec = decimals(x, sorted({t for k in keys.values() for t in k[:2]} | {r["base"] for r in reg} | {r["quote"] for r in reg}))
    def asset_px(sym, d):
        if sym == "ETH": return eth_day.get(d)
        p = lp_pools.get(sym); c = close_on(closes.get(p["pool"], {}), d, first=True) if p else None
        if c is None: return None
        sp = c / 2 ** 96; P = sp * sp
        return (1e12 / P if P else None) if p["usdg0"] else P * 1e18 / 1e6
    def is_asset(tok, sym): return tok in eth_like if sym == "ETH" else tok == (lp_pools.get(sym) or {}).get("stockAddr", "").lower()
    def usd_of(tok, sym, d):
        if tok == usdg: return 1.0
        if tok in eth_like: return eth_day.get(d)
        if is_asset(tok, sym): return asset_px(sym, d)
        return None
    def priced(t, sym): return t == usdg or t in eth_like or is_asset(t, sym)
    def is_venue(r):   # a pool pairing the asset with USDG or ETH; memecoins quoted in an equity and exotic quotes are not venues for the asset
        if r["v4"]:
            k = keys.get(r["id"])
            if not k or k[0].lower() == k[1].lower(): return False
            toks = [k[0].lower(), k[1].lower()]
        else: toks = [r["base"], r["quote"]]
        return all(priced(t, r["sym"]) for t in toks) and any(is_asset(t, r["sym"]) for t in toks)
    out = collections.defaultdict(dict)
    for sym in sorted({r["sym"] for r in reg}):
        venues = [r for r in reg if r["sym"] == sym and is_venue(r)]; mine = (lp_pools.get(sym) or {}).get("pool", "").lower()
        cum_rng = {r["id"]: collections.defaultdict(int) for r in venues if r["v4"]}
        after = {}                                     # custodial: balance at a day's close = balance now less every net flow after that day
        for r in venues:
            if r["v4"]: continue
            e = cu.get(r["id"], {}); tot = collections.defaultdict(int)
            for dd in sorted(e.get("d", {}), reverse=True):
                after[(r["id"], dd)] = dict(tot)
                for kk, v in e["d"][dd].items():
                    if kk.startswith("net_"): tot[kk[4:]] += int(v)
            after[(r["id"], "_all")] = dict(tot)
        last_sp = {}
        for d in dates:
            if d < "2026-10-14": continue                 # the reserve's pools opened on 14 October
            ap = asset_px(sym, d)
            if ap is None: continue
            vol = {}; tvl = {}
            for r in venues:
                vid = r["id"]
                if r["v4"]:
                    k = keys.get(vid)
                    if not k: continue
                    c0, c1 = k[0].lower(), k[1].lower(); d0, d1 = dec.get(c0, 18), dec.get(c1, 18)
                    for rk, L in (lq.get(vid, {}).get("d", {}).get(d) or {}).items(): cum_rng[vid][rk] += int(L)
                    dv = sw.get(vid, {}).get("d", {}).get(d)
                    if dv and dv[2]: last_sp[vid] = int(dv[2]) / 2 ** 96
                    elif vid not in last_sp and sw.get(vid, {}).get("spNow"): last_sp[vid] = int(sw[vid]["spNow"]) / 2 ** 96
                    sp = last_sp.get(vid)
                    if sp is None: continue
                    p10 = sp * sp * 10 ** (d0 - d1)                    # token1 per token0
                    u0, u1 = usd_of(c0, sym, d), usd_of(c1, sym, d)
                    if u0 is None and u1 is not None: u0 = u1 * p10
                    if u1 is None and u0 is not None and p10: u1 = u0 / p10
                    if u0 is None or u1 is None: continue
                    a0 = a1 = 0.0
                    for rk, L in cum_rng[vid].items():
                        if L > 0:
                            tl, tu = map(int, rk.split(",")); q0, q1 = lp_amounts(L, tl, tu, sp); a0 += q0; a1 += q1
                    tvl[vid] = a0 / 10 ** d0 * u0 + a1 / 10 ** d1 * u1
                    vol[vid] = (dv[0] / 10 ** d0 * u0 if c0 == usdg or (c1 != usdg and is_asset(c0, sym)) else dv[1] / 10 ** d1 * u1) if dv else 0.0
                else:
                    cv = cu.get(vid, {}); e = (cv.get("d", {}).get(d)) or {}; now_ = cv.get("now", {})
                    aft = after.get((vid, d))
                    if aft is None:                            # no flow that day: everything after the last flow day on or before it
                        later = [dd for dd in cv.get("d", {}) if dd > d]; aft = after.get((vid, min(later)), {}) if later else {}
                        if later: aft = {t_: aft.get(t_, 0) + sum(int(v) for kk, v in cv["d"][min(later)].items() if kk == "net_" + t_) for t_ in set(aft) | {k_[4:] for k_ in cv["d"][min(later)] if k_.startswith("net_")}}
                    b, q = r["base"], r["quote"]; ub, uq = usd_of(b, sym, d), usd_of(q, sym, d)
                    bb, qb = (int(now_.get(b, 0)) - aft.get(b, 0)) / 10 ** dec.get(b, 18), (int(now_.get(q, 0)) - aft.get(q, 0)) / 10 ** dec.get(q, 18)
                    if ub is None and uq is None: continue
                    tvl[vid] = (bb * ub if ub is not None else qb * uq) + (qb * uq if uq is not None else bb * ub)   # an unpriced side is valued like the priced one
                    stok = q if q == usdg else (b if ub is not None else q)
                    vol[vid] = int(e.get("sw_" + stok, "0")) / 10 ** dec.get(stok, 18) * (usd_of(stok, sym, d) or 0)
            tv, vv = sum(tvl.values()), sum(vol.values())
            pos = ((res_hist.get(d) or {}).get("lp") or {}).get(sym)
            ranked = sorted(tvl.items(), key=lambda kv: -kv[1])
            rk = next((i + 1 for i, (vid, _) in enumerate(ranked) if vid == mine), None)
            other = next(((vid, v) for vid, v in ranked if vid != mine), (None, 0))
            out[d].update({f"chainTvl_{sym}": tv, f"chainVol_{sym}": vv, f"poolTvl_{sym}": tvl.get(mine), f"poolVolChain_{sym}": vol.get(mine),
                           f"liqShare_{sym}": (pos / tv if pos is not None and tv else None), f"volShare_{sym}": (vol.get(mine, 0) / vv if vv else None),
                           f"rank_{sym}": rk, f"venues_{sym}": sum(1 for v in tvl.values() if v >= 100)})
            ov = next((r for r in venues if r["id"] == other[0]), None)
            out[d][f"otherTvl_{sym}"] = other[1]; out[d][f"otherDex_{sym}"] = (ov["dex"] + (" " + ov["label"] if ov["label"] else "")) if ov else ""
    return out


def lp_pnl(x, lp_pools, closes, dates, res_hist, fees_by_day):
    """The reserve's positions against holding what was deposited. Deposits and withdrawals are each liquidity change of the Safe's
    positions valued at the pool price just before it; holding value marks those token amounts at each day's close. Returns per pool and
    day: position value, holding value, cost in USD, cumulative fees earned."""
    import time
    lm = x.jl("lp_mods.json", {"rows": []}); cache = x.jl("lp_cost.json", {})
    ids = {"0x" + format(i, "064x") for i in x.pos_ids}
    INIT = x.INIT
    def price_before(pid, b):
        for span in (20000, 200000, 2000000):
            lg = x.getlogs({"address": x.PM, "topics": [x.SW, pid]}, max(x.G, b - span), b - 1, 4000000)
            if lg: return int(words(lg[-1]["data"])[2], 16)
        lg = x.getlogs({"address": x.PM, "topics": [INIT, pid]}, max(x.G, b - 2000000), b, 4000000)
        return int(words(lg[-1]["data"])[3], 16) if lg else None
    pid_sym = {p["pool"]: s for s, p in lp_pools.items()}
    ev = []
    for b, pid, tl, tu, dl, salt in lm["rows"]:
        if salt not in ids or pid not in pid_sym: continue
        k = f"{b}:{pid}:{tl}:{tu}:{dl}"
        if k not in cache:
            sp = price_before(pid, b); cache[k] = str(sp) if sp else None; time.sleep(0.2)
        if not cache[k]: continue
        sp = int(cache[k]) / 2 ** 96; a0, a1 = lp_amounts(abs(int(dl)), tl, tu, sp); sg = 1 if int(dl) > 0 else -1
        ev.append((day(x.T(b)), pid_sym[pid], sg * a0, sg * a1, sp))
    x.js("lp_cost.json", cache)
    out = collections.defaultdict(dict)
    for s, p in lp_pools.items():
        d0, d1 = (6, 18) if p["usdg0"] else (18, 6)
        def usd(a0, a1, sp):
            P = sp * sp
            if p["usdg0"]: return a0 / 1e6 + a1 / 1e18 * (1e12 / P if P else 0)
            return a0 / 1e18 * (P * 1e18 / 1e6) + a1 / 1e6
        h0 = h1 = cost = fees = 0.0
        for d in dates:
            for dd, s2, a0, a1, sp in ev:
                if dd == d and s2 == s: h0 += a0; h1 += a1; cost += usd(a0, a1, sp)
            fees += fees_by_day.get(d, {}).get(s, 0.0)
            c = close_on(closes.get(p["pool"], {}), d, first=True)
            pos = ((res_hist.get(d) or {}).get("lp") or {}).get(s)
            if c is None or pos is None or (h0 == 0 and h1 == 0): continue
            out[d][s] = {"lp": pos, "hold": usd(h0, h1, c / 2 ** 96), "cost": cost, "fees": fees}
    return out


def swap_callers(x, sw, reserve_pids):
    """Classify the contracts that executed swaps in the reserve's pools. A contract with fewer than 20 swaps is occasional (a wallet's own
    contract or a one-off route) and counts as organic. For the rest, six transactions are sampled: three or more distinct sending wallets
    make it a router or aggregator (organic); one or two make it a single-operator bot (arbitrage, market-making, other automation)."""
    import time
    c = x.jl("swap_callers.json", {})
    todo = []
    for pid in reserve_pids:
        for s, (n, txs) in (sw.get(pid, {}).get("snd") or {}).items():
            if s in c: continue
            if n < 20: c[s] = {"wallets": None, "kind": "router", "swaps": n}; continue
            if txs: todo.append((s, txs[:6]))
    for s, txs in todo:
        frm = set()
        for k in range(0, len(txs), 5):
            for t in range(6):
                try: res = x.rpcb([("eth_getTransactionByHash", [h]) for h in txs[k:k + 5]]); break
                except Exception: time.sleep(5 * (t + 1))
            else: res = []
            frm |= {(r or {}).get("from", "").lower() for r in res if r}
            time.sleep(0.3)
        c[s] = {"wallets": len(frm), "kind": "router" if len(frm) >= 3 else "bot"}
        if len(c) % 20 == 0: x.js("swap_callers.json", c)
    x.js("swap_callers.json", c)
    return c
