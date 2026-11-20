"""Exercise the deployment gate against controlled historical baselines and broken candidates."""
import argparse
import contextlib
import functools
import http.server
import json
import pathlib
import subprocess
import sys
import tempfile
import threading


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("render", type=pathlib.Path)
    parser.add_argument("dash", type=pathlib.Path)
    args = parser.parse_args()
    data = json.loads(args.dash.read_text())
    day = data["series"][len(data["series"]) // 2]
    baseline = {"series": data["series"], "live": data["live"], "genesisTs": data["genesisTs"]}
    script = pathlib.Path(__file__).with_name("check.py")
    with tempfile.TemporaryDirectory() as temp:
        folder = pathlib.Path(temp)
        class Handler(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *args): pass
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Handler, directory=temp))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        with contextlib.ExitStack() as stack:
            stack.callback(server.server_close)
            stack.callback(server.shutdown)
            for name in ("unchanged", "empty baseline", "truncated baseline", "missing date", "null field", "unavailable baseline"):
                page = folder / "index.html"
                source = baseline
                if name == "empty baseline": source = {}
                if name == "truncated baseline": source = {**baseline, "series": baseline["series"][1:]}
                page.write_text("const DATA = " + json.dumps(source) + ";\nconst L = DATA.live")
                if name == "unavailable baseline": page.unlink()
                candidate = dict(data)
                candidate["series"] = [dict(row) for row in data["series"]]
                if name == "missing date":
                    candidate["series"] = [row for row in candidate["series"] if row["date"] != day["date"]]
                if name == "null field":
                    next(row for row in candidate["series"] if row["date"] == day["date"])["supply"] = None
                path = folder / "candidate.json"
                path.write_text(json.dumps(candidate))
                (folder / "report.json").unlink(missing_ok=True)
                result = subprocess.run([sys.executable, "-I", str(script), str(args.render), str(path),
                                         "--live", f"http://127.0.0.1:{server.server_port}/index.html", "--out", temp],
                                        capture_output=True, text=True)
                if not (folder / "report.json").exists() or result.returncode not in (0,1): raise AssertionError(result.stderr)
                checks = [r for r in json.loads((folder / "report.json").read_text())["results"] if r["section"] == "drift"]
                assert checks and all(r["ok"] for r in checks) == (name == "unchanged"), (name, checks)
                if name != "unchanged": assert result.returncode == 1
                print("PASS", name)


if __name__ == "__main__":
    main()
