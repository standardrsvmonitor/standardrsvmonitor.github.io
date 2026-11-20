"""Treasury authority at the compile block, and attributable management actions."""
from collections import Counter
from k import keccak
import extra


def authority(block, address, call, selector):
    owners = extra.words(call(address, selector("getOwners()"), block))
    if len(owners) < 2 or int(owners[0], 16) != 32 or len(owners) != int(owners[1], 16) + 2:
        raise ValueError("Incomplete Safe owner list")
    signers = ["0x" + word[-40:] for word in owners[2:]]
    threshold = int(call(address, selector("getThreshold()"), block), 16)
    if not 0 < threshold <= len(set(signers)):
        raise ValueError("Invalid Safe threshold")
    sentinel = 1
    cursor = sentinel
    modules = []
    visited = set()
    while cursor not in visited:
        visited.add(cursor)
        data = selector("getModulesPaginated(address,uint256)") + f"{cursor:064x}{32:064x}"
        page = extra.words(call(address, data, block))
        if len(page)<3 or int(page[0],16)!=64 or int(page[2],16)!=len(page)-3: raise ValueError("Incomplete Safe module page")
        modules.extend("0x"+word[-40:] for word in page[3:])
        cursor = int(page[1],16)
        if cursor == sentinel: break
    else: raise ValueError("Repeated Safe module cursor")
    owner = call(extra.REGISTRY, selector("owner()"), block)
    if not owner or len(owner)!=66: raise ValueError("Incomplete registry owner")
    return {"address": address, "block": int(block, 16), "owners": signers, "threshold": threshold,
            "modules": modules, "registryOwner": "0x"+owner[-40:]}


def changes(x, keys, pools):
    checkpoint = x.jl("stewardship.json", {"last": x.G - 200001, "rows": []})
    start = checkpoint["last"] + 1
    if start > x.tip + 1:
        raise ValueError("Stewardship cache ahead of selected block")
    rows = checkpoint["rows"]
    def add(log, kind, detail):
        rows.append({"block": int(log["blockNumber"], 16), "index": int(log["logIndex"], 16),
                     "tx": log["transactionHash"], "kind": kind, "detail": detail})
    event = lambda signature: "0x" + keccak(signature.encode()).hex()
    config = {event("AddedOwner(address)"): "Signer added", event("RemovedOwner(address)"): "Signer removed",
              event("ChangedThreshold(uint256)"): "Threshold changed"}
    for log in x.safe_logs:
        if int(log["blockNumber"], 16) < start: continue
        topic = log["topics"][0]
        if topic in config:
            arg = (log["topics"][1:] or extra.words(log["data"]))[0]
            detail = str(int(arg, 16)) if config[topic] == "Threshold changed" else "0x" + arg[-40:]
            add(log, config[topic], detail)
    # Net ERC20 transfers per successful Safe transaction. Keep asset units and direction.
    net = Counter()
    representative = {}
    for sym, direction, log in x.safe_tok:
        if int(log["blockNumber"], 16) < start: continue
        key = (log["transactionHash"], sym)
        net[key] += direction * int(log["data"], 16)
        representative[key] = log
    for key, amount in net.items():
        _, sym = key
        if amount:
            add(representative[key], "Safe token flow", f"{amount / 10**(6 if sym == 'USDG' else 18):+,.4f} {sym}")
    ok = {log["transactionHash"] for log in x.safe_logs if log["topics"][0] == extra.SAFE_OK}
    for log in x.safe_logs:
        if int(log["blockNumber"], 16) < start: continue
        if log["topics"][0] == extra.SAFE_TX and log["transactionHash"] in ok:
            sent = sum(value for to, value in extra._safe_items(log) if to != x.H["reserveSafe"].lower())
            if sent: add(log, "Safe ETH sent", f"{sent:,.4f} ETH")
        if log["topics"][0] == extra.SAFE_RECEIVED:
            add(log, "Safe ETH received", f"{int(log['data'],16)/1e18:,.4f} ETH")
    for log in x.getlogs({"address": extra.REGISTRY, "topics": [extra.REG_SET]}, start, x.tip, 4000000):
        role = bytes.fromhex(log["topics"][1][2:]).rstrip(b"\0")
        name = role.decode() if role.isascii() and role.replace(b"_", b"").isalnum() else log["topics"][1]
        add(log, "Registry assignment", name + " → 0x" + log["topics"][2][-40:])
    hooks = {keys[p["pool"]][4] for p in pools.values() if not p["isEth"]}
    for hook in hooks:
        for log in x.getlogs({"address": hook, "topics": [event("FeeExemptSet(address,bool)")]}, start, x.tip, 4000000):
            add(log, "Fee exemption " + ("enabled" if int(log["data"], 16) else "removed"), "0x" + log["topics"][1][-40:])
    rows.sort(key=lambda row: (row["block"], row["index"]), reverse=True)
    x.js("stewardship.json", {"last": x.tip, "rows": rows})
    return rows


def reserve_flows(snapshot, pool_config, closes, receipts, date_of_block, posm, pool_manager, usdg, weth):
    """Value identifiable external transfers at the same UTC marks used by reserve history."""
    addrs = snapshot["addrs"]
    safe = addrs["reserveSafe"]
    fee_safe = extra.LPAD["feeSafe"].lower()
    internal = set(addrs.values()) | {posm.lower(), pool_manager.lower(), safe, fee_safe}
    token_addr = {usdg.lower(): ("USDG", 6), weth.lower(): ("WETH", 18)}
    token_addr.update({p["stockAddr"].lower(): (p["stock"], 18) for p in pool_config.values() if p["stock"] != "ETH"})
    pool_by_asset = {p["stock"]: (pid,p) for pid,p in pool_config.items()}
    daily = {row["date"]:row for row in snapshot["series"]}
    tagged = []
    transfer = "0x"+keccak(b"Transfer(address,address,uint256)").hex()
    for receipt in receipts:
        if not receipt or receipt["status"] != "0x1": raise ValueError("Treasury receipt unavailable or unsuccessful")
        tx = receipt["transactionHash"]
        block = int(receipt["blockNumber"],16)
        date = date_of_block(block)
        if block > snapshot["tip"] or date not in daily: raise ValueError("Treasury receipt outside snapshot")
        legs = []
        for log in receipt["logs"]:
            addr = log["address"].lower()
            topics = log["topics"]
            if not topics: continue
            topic = topics[0]
            if addr in token_addr and topic == transfer and len(topics)==3:
                src, dst = ("0x"+t[-40:] for t in topics[1:])
                if src == safe or dst == safe:
                    asset, decimals = token_addr[addr]
                    qty = int(log["data"],16)/10**decimals
                    if qty and src!=dst: legs.append((asset, qty if dst==safe else -qty, src if dst==safe else dst))
            elif addr == safe and topic == extra.SAFE_TX:
                legs.extend(("ETH",-qty,to) for to,qty in extra._safe_items(log) if qty and to!=safe)
            elif addr == safe and topic == extra.SAFE_RECEIVED:
                legs.append(("ETH",int(log["data"],16)/1e18,"0x"+topics[1][-40:]))
        paid_out = all(qty<0 for _,qty,_ in legs)
        for asset,qty,who in legs:
            if qty>0 and who==fee_safe: kind = "feeSafeIn"
            elif paid_out and who not in internal: kind = "externalOut"
            else: continue
            if asset == "USDG": price=1
            elif asset in ("ETH","WETH"): price=daily[date]["eth"]
            else:
                pid,cfg=pool_by_asset[asset]
                close=extra.close_on(closes[pid],date,first=True)
                if not close: raise ValueError("Missing treasury transfer closing mark")
                ratio=(int(close)/2**96)**2
                price=1e12/ratio if cfg["usdg0"] else ratio*1e12
            tagged.append({"date":date,"block":block,"tx":tx,"kind":kind,"asset":asset,"units":qty,"usd":qty*price})
    for row in daily.values():
        parts = row.get("reserveParts")
        if parts:
            parts["externalOut"] = 0.
            parts["feeSafeIn"] = 0.
    for leg in tagged:
        daily[leg["date"]]["reserveParts"][leg["kind"]] += leg["usd"]
    return tagged
