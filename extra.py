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
