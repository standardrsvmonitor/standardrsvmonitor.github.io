"""Regression checks for investor accounting and recoverable collector failures."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import extra
import pull


class CollectorTests(unittest.TestCase):
    def test_partial_json_write_keeps_the_last_good_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "cache.json"
            extra.write_json(p, {"day": 1})
            with self.assertRaises(ValueError):
                extra.write_json(p, {"day": float("nan")})
            self.assertEqual(extra.read_json(p, {}), {"day": 1})
            p.write_text("{")
            with self.assertRaises(json.JSONDecodeError):
                extra.read_json(p, {})

    def test_reorg_keeps_old_generation_and_resets_anchors(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(pull, "D", directory), patch.object(pull, "C"), patch.object(pull, "ANCH"), patch.object(pull, "_KEYS"):
            root = Path(directory) / "cache"
            root.mkdir()
            pull.select_cache(7, "0xaa")
            extra.write_json(root / "blocks.json", {"7": 500})
            with patch.object(pull, "rpc", return_value={"result":{"hash":"0xbb"}}):
                pull.select_cache(9, "0xcc")
            self.assertEqual(Path(pull.C), root / "chain-cc")
            self.assertEqual(pull.ANCH, {})
            self.assertEqual(extra.read_json(root / "blocks.json", {}), {"7": 500})
            with patch.object(pull, "rpc", return_value={"result":{"hash":"0xcc"}}):
                pull.select_cache(10, "0xdd")
            self.assertEqual(Path(pull.C), root / "chain-cc")

    def test_exit_scenarios_include_matured_positions_once(self):
        one = 10**18
        schedule = {"due":[[99,100], [100+7*86400,100], [101+7*86400,10000]]}
        rows = extra.bill_exits(schedule,100,[(.5,2,150*one)],1,2,.01,.03)
        self.assertEqual([x["principal"] for x in rows], [50,100,200])
        self.assertLess(rows[0]["proceeds"], rows[0]["mark"])
        self.assertGreater(rows[0]["proceeds"], 0)
        self.assertIsNone(rows[-1]["proceeds"])

    def test_liquidity_cost_uses_log_order_including_identical_modifications(self):
        words = lambda *items: "0x" + "".join(pull.u(x % (1 << 256)) for x in items)
        pid, salt = "pool", "0x"+pull.u(1)
        q96 = 2**96
        mod = [100,pid,-10,10,"50",salt]
        def event(index, topic, data):
            return {"logIndex":hex(index), "topics":[topic,pid,pull.pad(pull.POSM)], "data":data}
        logs = [event(2,"mod",words(-10,10,50,1)), event(3,"swap",words(0,0,2*q96)),
                event(4,"mod",words(-10,10,50,1)), event(1,"init",words(0,0,0,q96))]
        with tempfile.TemporaryDirectory() as directory:
            x = extra.Ctx(cache=directory, pos_ids=[1], INIT="init", ML="mod", SW="swap", PM=pull.PM,
                          POSM=pull.POSM, pad=pull.pad, T=lambda b: 0, getlogs=lambda *args: logs)
            x.js("lp_mods.json", {"rows":[mod,mod]})
            extra.lp_pnl(x, {"A":{"pool":pid,"usdg0":False}}, {}, [], {}, {})
            self.assertEqual(list(x.jl("lp_cost_ordered.json",{}).values()), [[str(q96),str(2*q96)]])


if __name__ == "__main__":
    unittest.main()
