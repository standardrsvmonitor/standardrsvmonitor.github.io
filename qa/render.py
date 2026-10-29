#!/usr/bin/env python3
"""Render index.html in headless Chrome and dump what the checks need: every tile, panel head, table, chart (data, styling, and its labels
at each range setting), visible text, tooltips, and layout faults at desktop, laptop and phone widths.

usage: qa/render.py <index.html> <out.json> [live] [--api DIR]
With --api, the open data files (daily.json, daily.csv, summary.json) are written to DIR from the rendered page's own export.
Without 'live' the in-browser live overlay is switched off, so every figure is the compiled one and can be checked against data/dash.json.
Standard library only; Chrome is found from $CHROME, the PATH (google-chrome, chromium) or the macOS application bundle."""
import sys, os, re, json, html, shutil, subprocess, tempfile, threading, functools, http.server

LAYOUTS = (1280, 390)          # widths checked for layout faults in addition to the 1440px desktop render
CAP = ("<script>window.__err=[];window.addEventListener('error',e=>window.__err.push(String(e.message)+' @'+e.lineno));"
       "const __cw=console.warn;console.warn=(...a)=>{window.__err.push('warn: '+a.map(String).join(' '));__cw(...a);};</script>")
QA = r"""<script>
(function(){
const txt = e=>e?e.textContent.replace(/\s+/g,' ').trim():null;
const visible = e=>!!(e && e.offsetParent!==null);
function layout(sec){
  // text clipped by an ellipsis or overflow, tables that scroll sideways, panels wider than the viewport
  const trunc = [...sec.querySelectorAll('.kv,.kd,.kl .t,.pt,.pn,.hero h1,.hero p,.h-num p,.totals li,.how li')].filter(e=>visible(e) && e.scrollWidth>e.clientWidth+1)
    .map(e=>({cls:e.className, text:(txt(e)||'').slice(0,90), sw:e.scrollWidth, cw:e.clientWidth}));
  const tscroll = [...sec.querySelectorAll('.tw')].filter(e=>visible(e) && e.scrollWidth>e.clientWidth+1).map(e=>({id:(e.querySelector('table')||{}).id, sw:e.scrollWidth, cw:e.clientWidth}));
  const wide = [...sec.querySelectorAll('.panel,.kpi,.hero')].filter(e=>visible(e) && e.getBoundingClientRect().right>window.innerWidth+1).map(e=>(txt(e.querySelector('.pt,.kl .t,h1'))||e.className).slice(0,60));
  return {trunc, tscroll, wide, hscroll: document.documentElement.scrollWidth>window.innerWidth+1 ? document.documentElement.scrollWidth : 0};
}
function chartInfo(cv){ const ch=Chart.getChart(cv); if(!ch) return null; const op=ch.options, pl=op.plugins||{}, lg=pl.legend||{}, tt=pl.tooltip||{};
  return {labels:ch.data.labels.map(String), h:cv.clientHeight, w:cv.clientWidth, legend:{display:lg.display!==false, position:lg.position, align:lg.align},
    mode:(op.interaction||{}).mode, tmode:tt.mode,
    sets:ch.data.datasets.map(d=>({label:d.label, type:d.type||ch.config.type, dash:(d.borderDash||[]).length, n:d.data.length,
      nonnull:d.data.filter(v=>v!=null && !(typeof v==='number' && !isFinite(v))).length, data:d.data.map(v=>typeof v==='number' && isFinite(v) ? +v.toFixed(6) : null)}))}; }
async function run(){
  if (document.fonts) { try { await document.fonts.ready; } catch(e){} }
  const mobile = /[?&]m=1/.test(location.search);
  const tabs = [...document.querySelectorAll('#tabs button[data-t]')].map(b=>b.dataset.t);
  const o = {errors:window.__err, width:window.innerWidth, tabs:{}};
  if (!mobile) {
    o.title = document.title; o.nav = [...document.querySelectorAll('#tabs button[data-t]')].map(b=>({t:b.dataset.t, text:txt(b), marks:b.querySelectorAll('i,svg,img').length}));
    o.side = txt(document.querySelector('.side-foot')); o.foot = txt(document.querySelector('.foot')); o.status = txt(document.getElementById('status'));
    o.tips = [...document.querySelectorAll('.tip')].map(txt);
    // every chart at every range setting: the labels it shows
    o.sweep = {};
    for (const n of ['7','30','0']) { const b=document.querySelector(`#range button[data-n="${n}"]`); if(!b) continue; b.click(); const r={};
      tabs.forEach(t=>{ show(t); document.querySelectorAll('#t-'+t+' canvas').forEach(cv=>{ const ch=Chart.getChart(cv);
        r[cv.id] = ch ? {tab:t, n:ch.data.labels.length, last:String(ch.data.labels[ch.data.labels.length-1]), sig:ch.data.labels.join('|'),
          title:txt(cv.closest('.panel').querySelector('.pt'))} : null; }); });
      o.sweep[n] = r; }
    const b30 = document.querySelector('#range button[data-n="30"]'); if (b30) b30.click();
  }
  tabs.forEach(t=>{ show(t); const sec=document.getElementById('t-'+t), T={layout:layout(sec)};
    if (!mobile) {
      T.kpis=[]; T.heads={}; T.tables={}; T.charts={}; T.blocks={}; T.panels=[];
      sec.querySelectorAll('.kpi').forEach(k=>T.kpis.push([txt(k.querySelector('.kl .t')), txt(k.querySelector('.kv')), txt(k.querySelector('.kd'))]));
      sec.querySelectorAll('.panel').forEach(p=>{ const ti=txt(p.querySelector('.pt')); T.heads[ti]=txt(p.querySelector('.pn'));
        T.panels.push({title:ti, tip:txt(p.querySelector('.ph .tip')), id:p.id||null});
        p.querySelectorAll('table').forEach(tb=>{ T.tables[tb.id]=[...tb.querySelectorAll('tr')].map(r=>[...r.children].map(c=>txt(c))); });
        p.querySelectorAll('.bridge,.kv2,.alloc,.stmt').forEach(bl=>{ T.blocks[bl.id||ti]=[...bl.querySelectorAll('div,span')].filter(x=>!x.children.length).map(txt); });
        p.querySelectorAll('canvas').forEach(cv=>{ T.charts[cv.id]=chartInfo(cv); }); });
      T.hero = txt(sec.querySelector('.hero')); T.text = sec.innerText;
    }
    o.tabs[t]=T; });
  if (!mobile && window.SRM_EXPORT) o.export = SRM_EXPORT();
  const pre=document.createElement('pre'); pre.id='vfy'; pre.style.display='none'; pre.textContent=JSON.stringify(o); document.body.appendChild(pre);
}
window.addEventListener('load', ()=>setTimeout(()=>run().catch(e=>{ window.__err.push('qa: '+e); const pre=document.createElement('pre'); pre.id='vfy'; pre.textContent=JSON.stringify({errors:window.__err, fatal:String(e)}); document.body.appendChild(pre); }), 1500));
})();
</script>"""
WRAP = """<!doctype html><html><body style="margin:0"><iframe id="f" src="page.html?m=__M__#overview" style="width:__W__px;height:900px;border:0"></iframe>
<script>const f=document.getElementById('f'); const t=setInterval(()=>{ try { const p=f.contentDocument.getElementById('vfy'); if(!p) return; clearInterval(t);
  const q=document.createElement('pre'); q.id='vfy'; q.textContent=p.textContent; document.body.appendChild(q); } catch(e){} }, 200);</script></body></html>"""


def chrome():
    for c in (os.environ.get("CHROME"), shutil.which("google-chrome"), shutil.which("google-chrome-stable"), shutil.which("chromium"), shutil.which("chromium-browser"),
              "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"):
        if c and os.path.exists(c): return c
    sys.exit("qa/render.py: Chrome not found; set $CHROME")


def dump(url, width, budget):
    args = [chrome(), "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars", "--no-first-run", f"--window-size={width},1000",
            f"--virtual-time-budget={budget}", "--dump-dom", url]
    for attempt in range(2):   # a CDN or font hiccup gets one retry
        r = subprocess.run(args, capture_output=True, text=True, timeout=300)
        m = re.search(r'<pre id="vfy"[^>]*>(.*?)</pre>', r.stdout, re.S)
        if m: return json.loads(html.unescape(m.group(1)))
    return {"errors": ["qa: no output from Chrome at width %d: %s" % (width, (r.stderr or "")[-300:])], "fatal": "no output", "tabs": {}}


def write_api(api, d):
    """The open data files, from the page's own export and its tiles and panel headlines."""
    ex = d.get("export")
    if not ex or not ex.get("rows"): print("no export from the page; open data files not written"); return
    os.makedirs(api, exist_ok=True)
    json.dump(ex, open(os.path.join(api, "daily.json"), "w"), separators=(",", ":"))
    keys = list(ex["fields"])
    esc = lambda v: "" if v is None else (('"' + str(v).replace('"', '""') + '"') if re.search(r'[",\n]', str(v)) else str(v))
    open(os.path.join(api, "daily.csv"), "w").write("\n".join([",".join(keys)] + [",".join(esc(r.get(k)) for k in keys) for r in ex["rows"]]) + "\n")
    summ = {"compiled": ex["compiled"], "source": ex["source"], "tabs": {t: {"tiles": [{"label": k[0], "value": k[1], "detail": k[2]} for k in X.get("kpis", [])],
            "panels": {p["title"]: X.get("heads", {}).get(p["title"]) for p in X.get("panels", [])}} for t, X in d.get("tabs", {}).items()}}
    json.dump(summ, open(os.path.join(api, "summary.json"), "w"), indent=1, ensure_ascii=False)
    print("open data:", len(ex["rows"]), "days,", len(keys), "fields ->", api)


def main():
    av = sys.argv[1:]; api = av[av.index("--api") + 1] if "--api" in av else None
    if api: i_ = av.index("--api"); del av[i_:i_ + 2]
    src, out = av[0], av[1]; live = len(av) > 2 and av[2] == "live"
    s = open(src).read().replace("<head>", "<head>" + CAP, 1)
    if not live: s = s.replace("goLive(); setInterval(goLive, 300000);", "")
    s = s.replace("</body>", QA + "</body>")
    tmp = tempfile.mkdtemp(prefix="srqa-")
    open(os.path.join(tmp, "page.html"), "w").write(s)
    for w in LAYOUTS: open(os.path.join(tmp, f"wrap{w}.html"), "w").write(WRAP.replace("__W__", str(w)).replace("__M__", "1"))
    if api and os.path.isdir(api): shutil.copytree(api, os.path.join(tmp, "api"))   # the page reads its own published qa.json when present
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(type("Q", (http.server.SimpleHTTPRequestHandler,), {"log_message": lambda *a: None}), directory=tmp))
    threading.Thread(target=srv.serve_forever, daemon=True).start(); base = f"http://127.0.0.1:{srv.server_address[1]}/"
    try:
        res = {"desktop": dump(base + "page.html#overview", 1440, 40000 if live else 30000), "layouts": {}}
        for w in LAYOUTS: res["layouts"][str(w)] = dump(base + f"wrap{w}.html", max(w + 40, 520), 30000)
    finally:
        srv.shutdown(); shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True); json.dump(res, open(out, "w"), indent=1)
    d = res["desktop"]; print("errors:", d.get("errors"))
    if api: write_api(api, d)
    for t, T in d.get("tabs", {}).items():
        empty = [k for k, v in (T.get("charts") or {}).items() if not v or not v["labels"]]
        print(f"  {t:10s} kpis {len(T.get('kpis', [])):2d}  charts {len(T.get('charts', {})):2d}  empty {empty}  tables {len(T.get('tables', {}))}")
    for w, r in res["layouts"].items(): print(f"  layout {w}px errors {len(r.get('errors') or [])} tabs {len(r.get('tabs', {}))}")


if __name__ == "__main__":
    main()
