#!/usr/bin/env python3
"""gen_site.py — regenerate index.html for analytics.pentaho.space as a showcase of the
ACTUAL Pentaho dashboards (real screenshots from assets/dashboards/). A demonstration of
the platform's analytical value — Custom (self-contained HTML over CDA) and Framework
(true Pentaho CDF) dashboards built on live Pentaho Data Catalog metadata. Run after shots.js.
"""
import json, os, datetime, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
M = json.load(open(os.path.join(HERE, "dashboards.json")))
SHOT = "assets/dashboards/%s.jpg"
def has(stem): return os.path.exists(os.path.join(ROOT, SHOT % stem))
_now = datetime.datetime.now().astimezone()
updated = datetime.date.today().isoformat()
stamp = _now.strftime("%Y-%m-%d %H:%M %Z")        # precise "last refreshed" time (local tz)
ndash = sum(len(g["items"]) for g in M["groups"])

_CL_TRAILERS = ("co-authored-by", "generated with", "co-authored", "\U0001f916")
_CL_SKIP = ("refresh dashboard showcase", "merge ", "status:", "wip", "fixup")
def _cl_clean(text):
    return " ".join(str(text).split()).replace("->", "→").replace(" x ", " × ")
def changelog(n=24, limit=16):
    """Reverse-chron 'what's new' list, auto-built from the iteration commit history (the real dashboard
    improvements). Each entry = a friendly headline (de-jargoned commit subject) + a couple of plain-language
    detail bullets pulled from the commit body. Newest first; (when, headline, [bullets]). Never fails the build."""
    se = os.path.normpath(os.path.join(ROOT, "..", "solution-engineering"))
    try:
        out = subprocess.check_output(
            ["git", "-C", se, "log", "-n", str(n), "--no-merges",
             "--pretty=format:%cI\x1f%s\x1f%b\x1e", "--", "iteration/"],
            stderr=subprocess.DEVNULL).decode("utf-8", "replace")
    except Exception:
        return []
    items, seen = [], set()
    for rec in out.split("\x1e"):
        rec = rec.strip()
        if "\x1f" not in rec: continue
        p = rec.split("\x1f")
        iso, subj, body = p[0], (p[1] if len(p) > 1 else ""), (p[2] if len(p) > 2 else "")
        subj = subj.strip()
        if subj.lower().startswith(_CL_SKIP): continue
        head = subj
        if ": " in head:
            pre = head.split(": ", 1)[0]
            if " " not in pre and pre.replace("-", "").isalnum():     # strip a "stem:" prefix
                head = head.split(": ", 1)[1]
        head = _cl_clean(head[:1].upper() + head[1:])[:130]
        if head.lower() in seen: continue
        seen.add(head.lower())
        bullets, body_txt = [], " ".join(l.strip() for l in body.splitlines()
            if l.strip() and not any(t in l.lower() for t in _CL_TRAILERS))
        for s in body_txt.split(". "):
            s = _cl_clean(s).rstrip(".")
            if len(s) < 8: continue
            bullets.append(s[:160])
            if len(bullets) >= 2: break
        try:
            when = datetime.datetime.fromisoformat(iso).strftime("%Y-%m-%d %H:%M")
        except Exception:
            when = iso[:16]
        items.append((when, head, bullets))
        if len(items) >= limit: break
    return items

def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
_logs = changelog()
def _cl_li(w, head, bullets):
    sub = "".join("<li>%s</li>" % _esc(b) for b in bullets)
    sub = ('<ul class="clsub">%s</ul>' % sub) if sub else ""
    return ('<li><span class="when">%s</span><span class="what"><span class="clhl">%s</span>%s</span></li>'
            % (_esc(w), _esc(head), sub))
_log_items = "".join(_cl_li(w, h, b) for (w, h, b) in _logs)
changelog_html = (('<details class="changelog"><summary>What\'s new · recent platform &amp; dashboard improvements</summary>'
                   '<ul class="log">%s</ul></details>') % _log_items) if _logs else ""

KIND_BADGE = {
  "Custom": '<span class="badge custom" title="Self-contained HTML dashboard over Pentaho CDA">Simple HTML</span>',
  "Framework": '<span class="badge framework" title="True Pentaho CDF framework dashboard (CCC charts)">Framework · CDF</span>',
}

def esc(s):
    return str(s).replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")

def card(it, gname):
    stem = it["stem"]
    img = (SHOT % stem) if has(stem) else ""
    media = ('<a class="shot" href="%s"><img loading="lazy" src="%s" alt="%s"/></a>'
             % (img, img, esc(it["title"]))) if img else '<div class="shot empty">screenshot pending</div>'
    text = esc((it["title"] + " " + it.get("blurb", "") + " " + it.get("value", "") + " " + gname + " " + it["kind"]).lower())
    cv = ('<div class="cv">%s</div>' % esc(it["value"])) if it.get("value") else ""
    return ('<figure class="card" data-group="%s" data-kind="%s" data-text="%s">%s'
            '<figcaption><div class="ct">%s %s</div>%s<div class="cb">%s</div></figcaption></figure>'
            % (esc(gname), esc(it["kind"]), text, media, esc(it["title"]), KIND_BADGE.get(it["kind"], ""), cv, esc(it["blurb"])))

def group(g):
    gv = ('<p class="gv">%s</p>' % esc(g["value"])) if g.get("value") else ""
    return ('<section class="grp" data-group="%s"><h3>%s</h3>%s<div class="grid">%s</div></section>'
            % (esc(g["name"]), esc(g["name"]), gv, "".join(card(it, g["name"]) for it in g["items"])))

# Filter toolbar (mimics the in-product launcher console — search + area chips + build-type chips)
group_names = [g["name"] for g in M["groups"]]
kinds = []
for g in M["groups"]:
    for it in g["items"]:
        if it["kind"] not in kinds: kinds.append(it["kind"])
KIND_LABEL = {"Custom": "Simple HTML", "Framework": "Framework · CDF", "CDE": "CDE"}
area_chips = ('<button class="chip active" data-f="group" data-v="">All areas</button>'
              + "".join('<button class="chip" data-f="group" data-v="%s">%s</button>' % (esc(n), esc(n)) for n in group_names))
kind_chips = ('<button class="chip k active" data-f="kind" data-v="">All builds</button>'
              + "".join('<button class="chip k" data-f="kind" data-v="%s">%s</button>' % (esc(k), esc(KIND_LABEL.get(k, k))) for k in kinds))
toolbar = ('<div class="filter" id="filter">'
           '<input id="q" class="search" type="search" placeholder="Search dashboards…" aria-label="Search dashboards" autocomplete="off"/>'
           '<div class="chiprow">%s</div><div class="chiprow">%s</div>'
           '<div class="count" id="count"></div></div>') % (area_chips, kind_chips)

# Rotating-montage hero: a few standout shots that auto-crossfade to show the breadth
# of the suite. Falls back to the single launcher shot if the curated set isn't present.
MONTAGE = ["lineage-explorer", "pdc-command-center", "pdc-storage", "pdc-pipeline-obs",
           M["launcher"]["stem"]]
_mont = [s for s in dict.fromkeys(MONTAGE) if has(s)]   # de-dupe, keep only shot-present
if len(_mont) >= 2:
    _spacer = '<img class="m-spacer" src="%s" alt=""/>' % (SHOT % _mont[0])
    _layers = "".join('<img class="m-layer%s" src="%s" alt="%s"/>'
                      % (" on" if i == 0 else "", SHOT % s,
                         esc("Pentaho Data Catalog dashboard")) for i, s in enumerate(_mont))
    hero = ('<p class="hero-cap">Preview the context, visualize the detail — when you put '
            '<b>Pentaho</b> into action.</p>'
            '<a class="hero-shot montage" id="montage" href="%s">%s%s</a>'
            % (SHOT % _mont[0], _spacer, _layers))
elif has(M["launcher"]["stem"]):
    hi = SHOT % M["launcher"]["stem"]
    hero = ('<p class="hero-cap">Preview the context, visualize the detail — when you put '
            '<b>Pentaho</b> into action.</p>'
            '<a class="hero-shot" href="%s"><img src="%s" alt="The dashboard suite"/></a>'
            % (hi, hi))
else:
    hero = ""

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Pentaho Data Catalog Analytics — live dashboard showcase</title>
<meta name="description" content="A demonstration of the Pentaho platform: analytical dashboards built on live Pentaho Data Catalog metadata — observability, governance, lineage, cost, and data quality. Custom HTML over CDA and true Pentaho CDF framework dashboards."/>
<style>
:root{--pdc:#005bb5;--pdc2:#7d3c98;--ink:#10202f;--bg:#f5f7fb;--panel:#fff;--border:#e4e9f2;--muted:#5f7088;}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;background:var(--bg);color:var(--ink);line-height:1.5}
a{color:var(--pdc)}
.wrap{max-width:1200px;margin:0 auto;padding:0 22px}
header.top{background:linear-gradient(115deg,var(--pdc),var(--pdc2));color:#fff;padding:64px 0 54px}
.brand{display:flex;align-items:center;gap:12px;font-weight:800;letter-spacing:.3px;opacity:.95}
.logo{width:34px;height:34px;border-radius:9px;background:rgba(255,255,255,.18);display:inline-flex;align-items:center;justify-content:center;font-size:19px}
h1{font-size:40px;line-height:1.12;margin:22px 0 12px;max-width:18ch;font-weight:850}
.sub{font-size:18px;opacity:.94;max-width:60ch}
.stats{display:flex;flex-wrap:wrap;gap:30px;margin-top:26px}
.stat .n{font-size:30px;font-weight:850}.stat .l{font-size:12.5px;text-transform:uppercase;letter-spacing:.7px;opacity:.85}
.hero-shot{display:block;margin:14px auto -90px;max-width:1060px;border-radius:14px;overflow:hidden;box-shadow:0 24px 60px rgba(7,30,60,.34);border:1px solid rgba(255,255,255,.25);cursor:zoom-in}
.hero-shot img{display:block;width:100%}
.montage{position:relative}
.montage .m-spacer{opacity:0}
.montage .m-layer{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:top center;opacity:0;transition:opacity 1.1s ease}
.montage .m-layer.on{opacity:1}
.hero-cap{text-align:center;color:#fff;opacity:.94;font-size:15.5px;font-weight:600;margin:30px auto 0;max-width:62ch}
.hero-cap b{font-weight:850}
main{padding:120px 0 40px}
.lb{position:fixed;inset:0;background:rgba(8,18,32,.86);-webkit-backdrop-filter:blur(3px);backdrop-filter:blur(3px);display:none;align-items:center;justify-content:center;z-index:90;padding:30px;cursor:zoom-out}
.lb.on{display:flex}
.lb-img{max-width:96vw;max-height:92vh;border-radius:10px;box-shadow:0 30px 80px rgba(0,0,0,.55);cursor:default;animation:lbin .18s ease}
@keyframes lbin{from{transform:scale(.97);opacity:.4}to{transform:scale(1);opacity:1}}
.lb-x{position:fixed;top:18px;right:22px;width:42px;height:42px;border-radius:50%;border:0;background:rgba(255,255,255,.16);color:#fff;font-size:26px;line-height:1;cursor:pointer;z-index:91;transition:.14s}
.lb-x:hover{background:rgba(255,255,255,.32)}
.shot{cursor:zoom-in}
.lead{max-width:74ch;margin:0 auto 8px;font-size:17px;color:#26384b}
.lead b{color:var(--ink)}
.pills{display:flex;flex-wrap:wrap;gap:10px;justify-content:center;margin:26px 0 10px}
.pill{background:var(--panel);border:1px solid var(--border);border-radius:999px;padding:8px 15px;font-size:13px;font-weight:600;color:#2c3e54;box-shadow:0 1px 2px rgba(20,40,80,.05)}
.pill b{color:var(--pdc)}
.filter{background:var(--panel);border:1px solid var(--border);border-radius:14px;padding:16px 18px;margin:30px 0 8px;box-shadow:0 2px 10px rgba(20,40,80,.05)}
.search{width:100%;font-size:15px;padding:11px 14px;border:1px solid var(--border);border-radius:10px;background:#fbfcfe;color:var(--ink);margin-bottom:13px}
.search:focus{outline:none;border-color:var(--pdc);background:#fff}
.chiprow{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:9px}
.chip{border:1px solid var(--border);background:#fff;color:#2c3e54;border-radius:999px;padding:7px 14px;font-size:13px;font-weight:650;cursor:pointer;transition:.14s;line-height:1}
.chip:hover{border-color:var(--pdc)}
.chip.active{background:var(--pdc);color:#fff;border-color:var(--pdc)}
.chip.k.active{background:var(--pdc2);border-color:var(--pdc2)}
.count{font-size:12.5px;color:var(--muted);margin-top:4px}
.grp{margin:44px 0}
.grp.hidden{display:none}
.card.hidden{display:none}
.grp h3{font-size:13px;text-transform:uppercase;letter-spacing:1.1px;color:var(--muted);font-weight:800;border-bottom:1px solid var(--border);padding-bottom:10px;margin:0 0 10px}
.grp .gv{margin:0 0 20px;font-size:14.5px;line-height:1.5;color:var(--text);max-width:900px}
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:24px}
@media(max-width:760px){.grid{grid-template-columns:1fr}h1{font-size:30px}}
.card{margin:0;background:var(--panel);border:1px solid var(--border);border-radius:14px;overflow:hidden;box-shadow:0 2px 10px rgba(20,40,80,.06);transition:transform .16s,box-shadow .16s}
.card:hover{transform:translateY(-3px);box-shadow:0 16px 36px rgba(10,40,80,.16)}
.shot{display:block;background:#0b1f33;line-height:0;border-bottom:1px solid var(--border);max-height:360px;overflow:hidden}
.shot img{width:100%;display:block}
.shot.empty{display:flex;align-items:center;justify-content:center;height:200px;color:#8aa;line-height:1.4;font-size:13px}
figcaption{padding:15px 18px 18px}
.ct{font-weight:800;font-size:16px;display:flex;align-items:center;gap:9px;flex-wrap:wrap}
.cv{color:var(--ink);font-size:13.5px;line-height:1.45;margin-top:7px;font-weight:600}
.cb{color:var(--muted);font-size:12.5px;margin-top:6px}
.badge{font-size:10.5px;font-weight:800;letter-spacing:.4px;text-transform:uppercase;padding:3px 9px;border-radius:999px}
.badge.custom{background:#eaf1fb;color:var(--pdc)}
.badge.framework{background:#f1e9f7;color:var(--pdc2)}
.how{background:var(--panel);border:1px solid var(--border);border-radius:16px;padding:30px 32px;margin:48px 0}
.how h2{margin:0 0 14px;font-size:22px}
.how .row{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;margin-top:18px}
@media(max-width:760px){.how .row{grid-template-columns:1fr}}
.how h4{margin:0 0 6px;font-size:15px;color:var(--pdc)}
.how p{margin:0;font-size:14px;color:#3a4b60}
footer{text-align:center;color:var(--muted);font-size:13px;padding:40px 0 56px}
footer .ftln b{color:#3a4b60;font-variant-numeric:tabular-nums}
.changelog{max-width:680px;margin:18px auto 0;text-align:left;background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:6px 16px}
.changelog summary{cursor:pointer;font-weight:700;color:var(--pdc);padding:10px 2px;list-style:none;user-select:none;font-size:13.5px}
.changelog summary::-webkit-details-marker{display:none}
.changelog summary::before{content:"\\25B8  ";color:var(--muted)}
.changelog[open] summary::before{content:"\\25BE  "}
.changelog .log{list-style:none;margin:0;padding:2px 0 12px;max-height:360px;overflow:auto}
.changelog .log>li{display:flex;gap:14px;padding:10px 2px;border-top:1px solid var(--border);font-size:13px;line-height:1.45}
.changelog .log .when{color:var(--muted);white-space:nowrap;font-variant-numeric:tabular-nums;flex:0 0 116px}
.changelog .log .what{color:#2c3e54;flex:1;min-width:0}
.changelog .log .clhl{font-weight:700;color:#1f2d3d}
.changelog .log .clsub{list-style:none;margin:5px 0 0;padding:0 0 0 16px;color:var(--muted);font-size:12.5px;line-height:1.5}
.changelog .log .clsub li{margin:1px 0;position:relative}
.changelog .log .clsub li::before{content:"·";position:absolute;left:-12px;color:var(--pdc)}
.tag{display:inline-block;background:#eef3fb;border:1px solid var(--border);border-radius:6px;padding:1px 7px;font-size:12px;color:#2c3e54}
</style>
</head>
<body>
<header class="top"><div class="wrap">
  <div class="brand"><span class="logo">P</span> Pentaho Data Catalog Analytics</div>
  <h1>Your data catalog, made visible.</h1>
  <p class="sub">A Pentaho <b>solution-engineering demonstration</b> of what the platform can do: __N__ interactive dashboards — observability, governance, lineage, cost, and data quality — every one driven off a <b>solid, governed data foundation</b> in the Pentaho Data Catalog.</p>
  <div class="stats">
    <div class="stat"><div class="n">__N__</div><div class="l">Live dashboards</div></div>
    <div class="stat"><div class="n">CDA · CDF · CDE</div><div class="l">Pentaho-native</div></div>
    <div class="stat"><div class="n">__NG__</div><div class="l">Catalog domains</div></div>
    <div class="stat"><div class="n">Simple HTML + Framework</div><div class="l">Every dashboard, two builds</div></div>
  </div>
  __HERO__
</div></header>
<main><div class="wrap">
  <p class="lead">Every screen below is a <b>real, running demonstration dashboard sourced from Pentaho Data Catalog</b> — not mockups. Each exists in two builds you can switch between: <b>Simple HTML</b> (a self-contained HTML dashboard over Pentaho <b>CDA</b>) and <b>Framework</b> (a true Pentaho <b>CDF</b> dashboard with CCC charts), so the same insight is delivered the lightweight way and the fully platform-native way. A subset are also authored as native <b>CDE</b> dashboards in Pentaho's drag-and-drop editor.</p>
  <div class="pills">
    <span class="pill"><b>Observability</b> across the estate</span>
    <span class="pill"><b>Governance</b> &amp; sensitivity</span>
    <span class="pill"><b>Lineage</b> &amp; data movement</span>
    <span class="pill"><b>Cost</b> &amp; sustainability</span>
    <span class="pill"><b>Data quality</b> &amp; key discovery</span>
    <span class="pill">Cross-dashboard <b>drill-through</b></span>
  </div>
  __TOOLBAR__
  __GROUPS__
  <div class="how">
    <h2>How it's built — on the Pentaho platform</h2>
    <p>One metadata warehouse, three Pentaho delivery styles, fully interactive.</p>
    <div class="row">
      <div><h4>CDA — the data layer</h4><p>Every dashboard reads <span class="tag">Pentaho CDA</span> queries over a managed JDBC connection to the catalog warehouse. One governed data layer, many front-ends.</p></div>
      <div><h4>CDF &amp; CDE — the framework</h4><p>The <span class="tag">Framework</span> dashboards are true Pentaho <span class="tag">CDF</span> (CCC charts) and authored <span class="tag">CDE</span> (.wcdf/.cdfde) — editable in the Pentaho CDE designer.</p></div>
      <div><h4>Interactive by design</h4><p>Cascading filters, light/dark, and click-to-drill that carries the selected filters from one dashboard into the next — the platform connecting the story end to end.</p></div>
    </div>
  </div>
</div></main>
<footer><div class="wrap">
  <div class="ftln">Pentaho Data Catalog Analytics · live dashboards over real platform metadata · last refreshed <b>__STAMP__</b> · <a href="https://github.com/kevinrhaas/solution-engineering">source</a></div>
  __CHANGELOG__
</div></footer>
<div class="lb" id="lb" aria-hidden="true" role="dialog" aria-label="Dashboard preview">
  <button class="lb-x" id="lbx" aria-label="Close preview">&times;</button>
  <img class="lb-img" id="lbimg" src="" alt=""/>
</div>
<script>
(function(){
  // --- Rotating montage hero: auto-crossfade the stacked layers ---
  var layers=[].slice.call(document.querySelectorAll('#montage .m-layer'));
  if(layers.length>1){var mi=0;setInterval(function(){
    layers[mi].classList.remove('on'); mi=(mi+1)%layers.length; layers[mi].classList.add('on');
  },4200);}
  // --- Simple lightbox: pop a thumbnail open bigger; close via ×, backdrop, or Esc ---
  var lb=document.getElementById('lb'), lbimg=document.getElementById('lbimg');
  function openLb(src,alt){ if(!src)return; lbimg.src=src; lbimg.alt=alt||''; lb.classList.add('on'); lb.setAttribute('aria-hidden','false'); }
  function closeLb(){ lb.classList.remove('on'); lb.setAttribute('aria-hidden','true'); lbimg.src=''; }
  document.querySelectorAll('.shot[href]').forEach(function(a){
    a.addEventListener('click',function(e){ e.preventDefault(); var im=a.querySelector('img'); openLb(a.getAttribute('href'), im?im.alt:''); });
  });
  var heroA=document.querySelector('.hero-shot');
  if(heroA)heroA.addEventListener('click',function(e){ e.preventDefault();
    var on=document.querySelector('#montage .m-layer.on')||heroA.querySelector('img');
    if(on)openLb(on.getAttribute('src'), on.alt||'Demonstration dashboard'); });
  document.getElementById('lbx').addEventListener('click',closeLb);
  lb.addEventListener('click',function(e){ if(e.target===lb)closeLb(); });
  document.addEventListener('keydown',function(e){ if(e.key==='Escape'||e.key==='Esc')closeLb(); });

  var TOTAL=document.querySelectorAll('.card').length;
  var state={group:"",kind:"",q:""};
  var cards=[].slice.call(document.querySelectorAll('.card'));
  var grps=[].slice.call(document.querySelectorAll('.grp'));
  var countEl=document.getElementById('count');
  function apply(){
    var shown=0;
    cards.forEach(function(c){
      var ok=(!state.group||c.getAttribute('data-group')===state.group)
           &&(!state.kind||c.getAttribute('data-kind')===state.kind)
           &&(!state.q||c.getAttribute('data-text').indexOf(state.q)>=0);
      c.classList.toggle('hidden',!ok); if(ok)shown++;
    });
    grps.forEach(function(s){
      var any=s.querySelectorAll('.card:not(.hidden)').length>0;
      s.classList.toggle('hidden',!any);
    });
    countEl.textContent='Showing '+shown+' of '+TOTAL+' dashboards';
  }
  document.querySelectorAll('.chip').forEach(function(ch){
    ch.addEventListener('click',function(){
      var f=ch.getAttribute('data-f'), v=ch.getAttribute('data-v');
      state[f]=v;
      document.querySelectorAll('.chip[data-f="'+f+'"]').forEach(function(x){x.classList.toggle('active',x===ch);});
      apply();
    });
  });
  var q=document.getElementById('q');
  q.addEventListener('input',function(){state.q=q.value.trim().toLowerCase();apply();});
  apply();
})();
</script>
</body>
</html>
"""

html = (HTML.replace("__N__", str(ndash))
            .replace("__NG__", str(len(M["groups"])))
            .replace("__HERO__", hero)
            .replace("__TOOLBAR__", toolbar)
            .replace("__GROUPS__", "".join(group(g) for g in M["groups"]))
            .replace("__STAMP__", stamp)
            .replace("__CHANGELOG__", changelog_html)
            .replace("__DATE__", updated))
open(os.path.join(ROOT, "index.html"), "w").write(html)
print("index.html regenerated: %d dashboards, %d changelog entries, refreshed %s" % (ndash, len(_logs), stamp))
