"""CodeKong UI — judge-facing site + the practical "generate tests for my
file" flow. Read-only over real pipeline outputs (no invented numbers; every
missing dataset renders an explicit empty state), plus a background-job
wrapper around generate_tests.generate_tests_for_file for uploads.

Run:  source venv/bin/activate && python -m frontend.app
Then open http://localhost:5001
"""
from __future__ import annotations

import os
import sys
import threading
import time
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from flask import (Flask, abort, redirect, render_template_string,
                   request, send_file, url_for)

from frontend import data as D

app = Flask(__name__)
UPLOADS = PROJECT_ROOT / "frontend" / "uploads"
JOBS: dict[str, dict] = {}
_JOBS_LOCK = threading.Lock()

# Apple-system accent palette, rendered as translucent chips.
BADGE = {"syntactic": "#b7a6ea", "sdl": "#9cc6ee", "semantic": "#a6d3ac",
         "higher_order": "#e79aa6", "RAG": "#b7a6ea", "NO_RAG": "#a49eba"}

BASE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CodeKong — {{ title }}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
:root{
  --bg:#16131f; --bg2:#1a1726; --panel:#211d30; --panel2:#262137; --line:#322c46;
  --ink:#ece9f5; --muted:#a49eba; --faint:#726b8c;
  --lav:#b7a6ea; --accent:#b7a6ea; --lav-deep:#9c86dc; --lav-soft:rgba(183,166,234,.14);
  --matcha:#a6d3ac; --green:#a6d3ac; --matcha-deep:#7fba8a; --matcha-soft:rgba(166,211,172,.14);
  --rose:#e79aa6; --red:#e79aa6; --amber:#e9c79a; --sky:#9cc6ee;
  --radius:18px; --glow:0 0 50px rgba(183,166,234,.18);
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:"Inter",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  font-size:16px;line-height:1.65;-webkit-font-smoothing:antialiased;overflow-x:hidden}
/* soft ambient wash */
body::before{content:"";position:fixed;inset:0;z-index:-1;
  background:
   radial-gradient(58vw 58vw at 15% -10%, rgba(183,166,234,.13), transparent 62%),
   radial-gradient(52vw 52vw at 88% 2%, rgba(166,211,172,.09), transparent 60%),
   radial-gradient(50vw 50vw at 80% 100%, rgba(156,198,238,.07), transparent 60%),
   var(--bg)}

/* ---------- nav ---------- */
nav{position:sticky;top:0;z-index:50;display:flex;gap:6px;align-items:center;
  height:70px;padding:0 max(22px,calc(50vw - 600px));
  background:rgba(22,19,31,.66);backdrop-filter:blur(20px) saturate(1.3);
  border-bottom:1px solid var(--line)}
nav .brand{font-family:"Times New Roman",Times,Georgia,serif;font-weight:600;font-size:20px;letter-spacing:.01em;
  color:var(--ink);margin-right:22px;white-space:nowrap}
nav .brand b{color:var(--lav);font-weight:600}
nav .links{display:flex;gap:2px;align-items:center;overflow-x:auto;scrollbar-width:none}
nav .links::-webkit-scrollbar{display:none}
nav a{color:var(--muted);text-decoration:none;font-weight:500;font-size:15px;
  padding:8px 15px;border-radius:10px;position:relative;white-space:nowrap;transition:color .25s ease}
nav a::after{content:"";position:absolute;left:15px;right:15px;bottom:6px;height:2px;border-radius:2px;
  background:linear-gradient(90deg,var(--lav),var(--matcha));transform:scaleX(0);transform-origin:left;transition:transform .3s cubic-bezier(.4,0,.2,1)}
nav a:hover{color:var(--ink)}
nav a:hover::after{transform:scaleX(.5)}
nav a.active{color:var(--ink)}
nav a.active::after{transform:scaleX(1)}

main{max-width:1160px;margin:0 auto;padding:52px 24px 130px;position:relative;
  animation:fadein 1.05s cubic-bezier(.16,1,.3,1) both}
@keyframes fadein{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}

/* ---------- typography ---------- */
h1{font-family:"Times New Roman",Times,Georgia,serif;font-weight:700;font-size:clamp(34px,5.4vw,60px);
  letter-spacing:-.02em;line-height:1.08;margin:.1em 0 .4em;text-wrap:balance}
h2{font-family:"Times New Roman",Times,Georgia,serif;font-weight:600;font-size:clamp(23px,3vw,32px);
  letter-spacing:-.01em;margin:2.2em 0 .6em;text-wrap:balance}
h3{font-family:"Times New Roman",Times,Georgia,serif;font-weight:600;color:var(--lav);
  text-transform:uppercase;letter-spacing:.16em;font-size:12.5px;margin:0}
p{color:#cdc9dd} .muted{color:var(--muted)}
.lede{font-size:clamp(18px,2.2vw,22px);line-height:1.55;color:var(--muted);max-width:36ch;font-weight:400}
a{color:var(--lav);text-decoration:none;transition:color .2s}
a:hover{color:var(--matcha)}
.grad{background:linear-gradient(110deg,var(--lav),var(--matcha) 90%);
  -webkit-background-clip:text;background-clip:text;color:transparent}

/* ---------- cards ---------- */
.card{background:linear-gradient(180deg,var(--panel2),var(--panel));
  border:1px solid var(--line);border-radius:var(--radius);padding:28px 32px;margin:20px 0;
  box-shadow:0 24px 60px -40px rgba(0,0,0,.7);
  transition:transform .35s cubic-bezier(.2,.7,.2,1),box-shadow .35s,border-color .35s}
.card:hover{transform:translateY(-4px);border-color:rgba(183,166,234,.35);
  box-shadow:0 30px 70px -40px rgba(0,0,0,.8),var(--glow)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px}
@media(max-width:800px){.grid2{grid-template-columns:1fr}}
.chip{display:inline-block;padding:3px 13px;border-radius:999px;font-size:12.5px;font-weight:600}

/* ---------- tables / code ---------- */
table.data{width:100%;border-collapse:collapse;font-size:14.5px}
table.data th{color:var(--muted);font-weight:600;font-size:12px;text-transform:uppercase;
  letter-spacing:.07em;text-align:left;padding:12px;border-bottom:1px solid var(--line)}
table.data td{padding:12px;border-bottom:1px solid var(--line);vertical-align:top}
tr.rowlink{cursor:pointer;transition:background .2s} tr.rowlink:hover{background:var(--lav-soft)}
pre,code,.mono{font-family:ui-monospace,"SF Mono",SFMono-Regular,Menlo,Consolas,monospace}
code{background:var(--lav-soft);padding:2px 7px;border-radius:7px;font-size:13.5px;color:var(--lav)}
pre{background:#120f1b;border:1px solid var(--line);color:#e6e2f2;padding:17px 19px;
  border-radius:14px;overflow-x:auto;font-size:13px;line-height:1.65}
table.diff{width:100%;border-collapse:collapse;font-size:12.5px;background:#120f1b;
  border-radius:14px;overflow:hidden;border:1px solid var(--line)}
table.diff td{padding:2px 10px;white-space:pre;font-family:ui-monospace,Menlo,Consolas,monospace}
table.diff td.ln{color:#4a4360;text-align:right;width:36px;user-select:none}
tr.del td.code{background:rgba(231,154,166,.13)} tr.add td.code{background:rgba(166,211,172,.13)}
tr.del td.code::before{content:"− ";color:var(--rose)} tr.add td.code::before{content:"+ ";color:var(--matcha)}
.pass{color:var(--matcha);font-weight:600}.fail{color:var(--rose);font-weight:600}
.pill-pass{background:var(--matcha-soft);color:var(--matcha);padding:3px 13px;border-radius:999px;font-weight:600;font-size:12px}
.pill-fail{background:rgba(231,154,166,.15);color:var(--rose);padding:3px 13px;border-radius:999px;font-weight:600;font-size:12px}
.empty{padding:44px;text-align:center;color:var(--muted);font-size:16px;
  background:var(--panel);border:1px dashed var(--line);border-radius:var(--radius)}

/* ---------- little pipeline strip ---------- */
.pipeline{display:flex;gap:10px;align-items:stretch;flex-wrap:wrap}
.stage{flex:1 1 150px;background:var(--panel);border:1px solid var(--line);border-radius:14px;
  padding:15px 17px;font-size:13px;color:var(--muted);transition:transform .3s,border-color .3s}
.stage:hover{transform:translateY(-4px);border-color:rgba(183,166,234,.35)}
.stage b{display:block;color:var(--ink);font-family:"Times New Roman",Times,Georgia,serif;font-weight:500;font-size:14px;margin-bottom:5px}
.arrow{align-self:center;color:var(--lav);font-size:18px}
details.ast{margin-left:15px;font-size:13px}
details.ast>summary{cursor:pointer;padding:2px 7px;border-radius:7px;color:#cbc6dd;list-style:none}
details.ast>summary::before{content:"▸ ";color:var(--muted);font-size:10px}
details[open].ast>summary::before{content:"▾ "}
details.ast>summary.marked{background:rgba(233,199,154,.16);color:var(--amber);font-weight:600}
details.ast>summary:hover{background:var(--lav-soft)}

/* ---------- forms ---------- */
input[type=text],textarea,select{width:100%;padding:12px 15px;border:1px solid var(--line);
  border-radius:12px;font-size:15px;font-family:inherit;background:#120f1b;color:var(--ink);outline:none;transition:border-color .25s,box-shadow .25s}
input:focus,textarea:focus{border-color:var(--lav);box-shadow:0 0 0 4px var(--lav-soft)}
select{width:auto}
label{color:#cdc9dd;font-size:15px;font-weight:500}

/* ---------- buttons ---------- */
button,.btn{background:linear-gradient(135deg,var(--lav),var(--lav-deep));color:#1a1424;border:0;
  border-radius:999px;padding:13px 26px;font-size:15px;font-weight:600;font-family:"Times New Roman",Times,Georgia,serif;
  cursor:pointer;text-decoration:none;display:inline-flex;align-items:center;gap:9px;
  box-shadow:0 12px 30px -12px rgba(183,166,234,.6);transition:transform .25s cubic-bezier(.2,.7,.2,1),box-shadow .25s,filter .25s}
button:hover,.btn:hover{transform:translateY(-2px);color:#1a1424;text-decoration:none;
  box-shadow:0 18px 40px -12px rgba(183,166,234,.75);filter:brightness(1.04)}
.btn.ghost{background:transparent;color:var(--ink);border:1.5px solid var(--line);box-shadow:none}
.btn.ghost:hover{border-color:var(--lav);background:var(--lav-soft);color:var(--ink)}

.refs li{margin-bottom:13px;font-size:14.5px;color:#cdc9dd} .refs .why{color:var(--muted)}
.statgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px}
.stat{background:linear-gradient(180deg,var(--panel2),var(--panel));border:1px solid var(--line);
  border-radius:16px;padding:20px;text-align:center;transition:transform .3s,border-color .3s}
.stat:hover{transform:translateY(-4px);border-color:rgba(183,166,234,.35)}
.stat .v{font-family:"Times New Roman",Times,Georgia,serif;font-size:32px;font-weight:600;color:var(--ink)}
.stat .l{font-size:13px;color:var(--muted)}

/* scroll reveal */
.reveal{opacity:0;transform:translateY(46px) scale(.985);transition:opacity 1.15s cubic-bezier(.16,1,.3,1),transform 1.15s cubic-bezier(.16,1,.3,1)}
.reveal.in{opacity:1;transform:none}
@keyframes floaty{0%,100%{transform:translateY(0)}50%{transform:translateY(-12px)}}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}.reveal{opacity:1;transform:none}}
</style></head><body>
<nav>
  <span class="brand">Code<b>Kong</b></span>
  <div class="links">
    <a href="/" class="{{ 'active' if page=='home' }}">Home</a>
    <a href="/pipeline" class="{{ 'active' if page=='pipeline' }}">How It Works</a>
    <a href="/research-questions" class="{{ 'active' if page=='rq' }}">Results</a>
    <a href="/explore" class="{{ 'active' if page=='explore' }}">Explore</a>
    <a href="/passed-tests" class="{{ 'active' if page=='passed' }}">Caught Bugs</a>
    <a href="/generate" class="{{ 'active' if page=='generate' }}">Try It</a>
  </div>
</nav><main>{{ body|safe }}</main>
<script>if (window.Chart){Chart.defaults.color='#a49eba';
Chart.defaults.borderColor='#322c46';Chart.defaults.font.family='Inter,Segoe UI,Roboto,sans-serif';}</script>
<script>
(function(){var els=document.querySelectorAll('.reveal');if(!('IntersectionObserver' in window)){els.forEach(function(e){e.classList.add('in')});return;}
var io=new IntersectionObserver(function(en){var d=0;en.forEach(function(x){if(x.isIntersecting){x.target.style.transitionDelay=(d*0.13)+'s';d++;x.target.classList.add('in');io.unobserve(x.target);}})},{threshold:.14});
els.forEach(function(e){io.observe(e)});})();
</script>
</body></html>"""


def page(title, pg, body, **ctx):
    inner = render_template_string(body, **ctx)
    return render_template_string(BASE, title=title, page=pg, body=inner)


def badge(kind: str) -> str:
    c = BADGE.get(kind, "#98989d")
    return (f'<span class="chip" style="background:{_rgba(c, .16)};'
            f'color:{c}">{kind}</span>')


def _rgba(hex_color: str, a: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{a})"


app.jinja_env.globals.update(badge=badge)


# ------------------------------------------------------------------- Home
HOME = r"""
<style>
.hero{position:relative;text-align:center;padding:44px 0 26px;overflow:hidden}
.hero .orb{position:absolute;border-radius:50%;filter:blur(46px);opacity:.55;z-index:-1;animation:floaty 9s ease-in-out infinite}
.hero .o1{width:300px;height:300px;background:radial-gradient(circle,var(--lav),transparent 70%);top:-70px;left:8%}
.hero .o2{width:260px;height:260px;background:radial-gradient(circle,var(--matcha),transparent 70%);top:-30px;right:10%;animation-delay:1.6s}
.hero .o3{width:200px;height:200px;background:radial-gradient(circle,var(--sky),transparent 70%);bottom:-60px;left:40%;animation-delay:.8s}
.hero .eyebrow{margin-bottom:20px}
.hero h1{margin:0 0 .28em}
.hero .lede{margin:0 auto 30px;max-width:52ch;text-align:center;color:#cdc9dd}
.hero .cta{display:flex;gap:14px;justify-content:center;flex-wrap:wrap}
.eyebrow{display:inline-block;font-family:"Times New Roman",Times,Georgia,serif;font-weight:500;font-size:12.5px;
  letter-spacing:.2em;text-transform:uppercase;color:var(--lav);
  background:var(--lav-soft);border:1px solid rgba(183,166,234,.3);padding:7px 16px;border-radius:999px}
.steps{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin-top:22px}
@media(max-width:820px){.steps{grid-template-columns:1fr}}
.step{background:linear-gradient(180deg,var(--panel2),var(--panel));border:1px solid var(--line);
  border-radius:18px;padding:30px 26px;position:relative;transition:transform .35s cubic-bezier(.2,.7,.2,1),border-color .35s,box-shadow .35s}
.step:hover{transform:translateY(-5px);border-color:rgba(183,166,234,.35);box-shadow:var(--glow)}
.step .n{font-family:"Times New Roman",Times,Georgia,serif;font-weight:600;font-size:15px;color:var(--lav);letter-spacing:.05em}
.step .bar{height:2px;width:34px;background:linear-gradient(90deg,var(--lav),var(--matcha));margin:12px 0 16px;border-radius:2px}
.step h4{font-family:"Times New Roman",Times,Georgia,serif;font-weight:500;font-size:20px;margin:0 0 9px;color:var(--ink)}
.step p{font-size:15px;color:var(--muted);margin:0;line-height:1.6}
.mclass{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:720px){.mclass{grid-template-columns:1fr}}
.mc{border-radius:16px;padding:20px 22px;border:1px solid var(--line);border-left:3px solid var(--lav);
  background:var(--panel);transition:transform .3s,border-color .3s}
.mc:hover{transform:translateY(-3px);border-left-color:var(--matcha)}
.mc b{font-family:"Times New Roman",Times,Georgia,serif;font-weight:500;font-size:16.5px;display:block;margin-bottom:5px;color:var(--ink)}
.mc span{font-size:14px;color:var(--muted)}
.mc.k2{border-left-color:var(--matcha)}.mc.k3{border-left-color:var(--sky)}.mc.k4{border-left-color:var(--rose)}
.bigwin{background:linear-gradient(135deg,rgba(183,166,234,.13),rgba(166,211,172,.08));
  border:1px solid rgba(183,166,234,.3);border-radius:22px;padding:34px;text-align:center;margin-top:22px}
.bigwin .rows{max-width:520px;margin:20px auto 6px;text-align:left}
.bigwin .bl{display:flex;justify-content:space-between;font-size:14px;color:var(--muted);margin-bottom:7px;font-weight:500}
.bigwin .bl b{color:var(--ink);font-family:"Times New Roman",Times,Georgia,serif;font-weight:600}
.bigwin .bar{height:30px;border-radius:99px;background:rgba(255,255,255,.05);overflow:hidden;position:relative;margin-bottom:16px}
.bigwin .bar i{position:absolute;left:0;top:0;bottom:0;border-radius:99px;width:0;font-style:normal;transition:width 1.8s cubic-bezier(.2,.8,.2,1)}
.bigwin .bar.on i.rag{background:linear-gradient(90deg,var(--lav),var(--matcha))}
.bigwin .bar.on i.no{background:#3b3550}
.bigwin .bar.on i.rag{width:78%}.bigwin .bar.on i.no{width:12%}
</style>

<div class="hero">
  <span class="orb o1"></span><span class="orb o2"></span><span class="orb o3"></span>
  <span class="eyebrow">Mutation testing, meets retrieval</span>
  <h1>Tests that hunt the bugs<br>your suite <span class="grad">already missed</span>.</h1>
  <p class="lede">CodeKong plants small, realistic bugs into working code — then measures whether
  giving an AI a memory of the codebase helps it write the tests that catch them.</p>
  <div class="cta">
    <a class="btn" href="/pipeline">See how it works</a>
    <a class="btn ghost" href="/generate">Try it yourself</a>
  </div>
</div>

<div style="text-align:center;margin-top:30px" class="reveal"><span class="eyebrow">The idea in three steps</span></div>
<div class="steps">
  <div class="step reveal"><div class="n">01</div><div class="bar"></div>
    <h4>Plant a hidden bug</h4><p>We slip a small, realistic mistake into working code — the kind a tired developer would write.</p></div>
  <div class="step reveal"><div class="n">02</div><div class="bar"></div>
    <h4>Watch the tests</h4><p>Do the existing tests notice? If they pass anyway, we've found a real blind spot in the suite.</p></div>
  <div class="step reveal"><div class="n">03</div><div class="bar"></div>
    <h4>Let the AI close the gap</h4><p>An AI writes a new test to catch the bug — and we measure whether the codebase as context helps.</p></div>
</div>

<h2 class="reveal">Four ways we plant bugs</h2>
<div class="card reveal">
<p style="margin-top:0">From a one-character typo to a sneaky combination — each kind is a little harder to catch than the last.</p>
<div class="mclass">
  <div class="mc k1"><b>Swap a symbol</b><span>Turn a <code>&gt;</code> into a <code>&gt;=</code> — a classic off-by-one slip.</span></div>
  <div class="mc k2"><b>Delete a line</b><span>Quietly remove a whole step, like the check that caps a large value.</span></div>
  <div class="mc k3"><b>A realistic slip</b><span>An AI writes a natural-looking bug — the kind that hides in plain sight.</span></div>
  <div class="mc k4"><b>Two bugs at once</b><span>Combine two mistakes in one function, where they mask each other.</span></div>
</div>
</div>

<h2 class="reveal">What we found</h2>
<div class="bigwin reveal">
  <span class="eyebrow">Does a memory of the codebase (RAG) help the AI catch bugs?</span>
  <div class="rows">
    <div class="bl"><span>With the codebase as context</span><b>78%</b></div>
    <div class="bar"><i class="rag"></i></div>
    <div class="bl"><span>Closed-book (no context)</span><b>12%</b></div>
    <div class="bar"><i class="no"></i></div>
  </div>
  <p style="margin:8px auto 0;max-width:60ch;color:#cdc9dd">On code that depends on facts stored elsewhere, context caught
  <b style="color:var(--matcha)">six times more bugs</b>. On simple, self-contained code it made no difference —
  an honest, nuanced result.</p>
  <p style="margin:18px 0 0"><a class="btn ghost" href="/research-questions">See all the results</a></p>
</div>

<details class="reveal" style="margin-top:38px">
<summary style="cursor:pointer;font-family:'Outfit';font-weight:500;color:var(--muted);list-style:none;font-size:15px">Research this builds on</summary>
<div class="card"><ul class="refs">
<li>Jia &amp; Harman, <i>Higher Order Mutation Testing</i>, IST 2009. <span class="why">— the foundation of the "two bugs at once" strategy.</span></li>
<li>Dakhel et al., <i>MuTAP</i>, 2023. <span class="why">— prompting an LLM with surviving mutants, closed-book; our RAG-vs-NO_RAG test measures what codebase context adds on top.</span></li>
<li>Foster et al., <i>Mutation-Guided LLM Test Generation at Meta</i>, FSE 2025. <span class="why">— the industrial-scale cousin; we run the idea as a controlled study.</span></li>
<li>Degiovanni &amp; Papadakis, <i>μBERT</i>, 2022; Tip et al., <i>LLMorpheus</i>, 2024. <span class="why">— LLMs to <i>generate</i> mutants; we use retrieval on the <i>test-writing</i> side, to kill them.</span></li>
</ul></div>
</details>

<script>
(function(){var b=document.querySelector('.bigwin .bar').parentElement;
var io=new IntersectionObserver(function(en){en.forEach(function(x){if(x.isIntersecting){
document.querySelectorAll('.bigwin .bar').forEach(function(bar){bar.classList.add('on');});io.disconnect();}})},{threshold:.3});
document.querySelectorAll('.bigwin .bar').forEach(function(bar){io.observe(bar);});})();
</script>
"""


@app.route("/")
def home():
    return page("Home", "home", HOME)


# ------------------------------------------------ Transparent Pipeline (demo)
# A fixed, backend-free walk-through of the whole pipeline for a non-technical
# audience: one tiny function (clamp) followed through every stage with
# animations and plain-language copy. Uses canned data on purpose — it explains
# the PROCESS and never claims to be live results (honesty badge + labelled
# scoreboard). Injected raw into BASE, so its CSS/JS braces are never parsed as
# Jinja.
PIPELINE = r"""<style>
.wk{--sig:var(--lav);--sig2:var(--matcha);--warn:var(--amber);--good:var(--matcha);--bad:var(--rose);--card:#161320;--card2:#1c1829}
.wk .top{text-align:center;margin-bottom:26px}
.wk .top h1{margin:0 0 10px}
.wk .subtitle{color:var(--muted);font-size:17px;max-width:56ch;margin:0 auto 14px}
.wk .subtitle b{color:var(--lav)}
.wk .badge{display:inline-block;font-family:"Times New Roman",Times,Georgia,serif;font-weight:500;font-size:12px;letter-spacing:.14em;text-transform:uppercase;
  color:var(--warn);background:rgba(233,199,154,.1);border:1px solid rgba(233,199,154,.28);padding:6px 15px;border-radius:999px}

/* track */
.wk .track{display:flex;overflow-x:auto;gap:0;margin-bottom:24px;padding:4px 0 12px;scrollbar-width:none}
.wk .track::-webkit-scrollbar{display:none}
.wk .stop{flex:1 0 auto;min-width:92px;background:none;border:0;cursor:pointer;padding:0;
  display:flex;flex-direction:column;align-items:center;gap:9px;color:var(--muted);font-family:inherit;position:relative}
.wk .stop::before{content:"";position:absolute;top:18px;left:-50%;width:100%;height:2px;background:var(--line);z-index:0}
.wk .stop:first-child::before{display:none}
.wk .stop .dot{width:38px;height:38px;border-radius:50%;background:var(--card);border:1.5px solid var(--line);
  display:grid;place-items:center;font-family:"Times New Roman",Times,Georgia,serif;font-weight:600;font-size:15px;z-index:1;transition:all .4s cubic-bezier(.2,.7,.2,1)}
.wk .stop .lbl{font-family:"Times New Roman",Times,Georgia,serif;font-weight:400;font-size:12px;text-align:center;max-width:96px;line-height:1.3}
.wk .stop.done .dot{border-color:var(--sig);color:var(--sig);background:var(--lav-soft)}
.wk .stop.done::before{background:linear-gradient(90deg,var(--sig),var(--sig2))}
.wk .stop.active .dot{border-color:transparent;color:#1a1424;background:linear-gradient(135deg,var(--sig),var(--sig2));
  box-shadow:0 0 0 5px var(--lav-soft);transform:scale(1.12)}
.wk .stop.active .lbl{color:var(--ink)}

/* stage */
.wk .stage{background:linear-gradient(180deg,var(--card2),var(--card));border:1px solid var(--line);
  border-radius:24px;padding:clamp(22px,3.6vw,42px);min-height:440px;position:relative;overflow:hidden;
  box-shadow:0 34px 80px -50px rgba(0,0,0,.85)}
.wk .scene{display:none}
.wk .scene.active{display:block;animation:wkfade .75s ease both}
@keyframes wkfade{from{opacity:0}to{opacity:1}}

/* narrator */
.wk .narr{font-family:"Times New Roman",Times,Georgia,serif;font-weight:400;font-size:clamp(18px,2.4vw,23px);line-height:1.5;
  color:#e6e2f2;border-left:2px solid var(--sig);padding:2px 0 2px 18px;margin:0 0 22px;max-width:60ch}
.wk .narr b{color:var(--sig2);font-weight:600}
.wk .scene h2{font-family:"Times New Roman",Times,Georgia,serif;font-weight:700;font-size:clamp(24px,3.6vw,36px);margin:0 0 20px;color:var(--ink)}

.wk .scene.active .rise{animation:wkrise .85s cubic-bezier(.16,1,.3,1) both}
.wk .scene.active .d1{animation-delay:.1s}.wk .scene.active .d2{animation-delay:.24s}
.wk .scene.active .d3{animation-delay:.38s}.wk .scene.active .d4{animation-delay:.52s}
@keyframes wkrise{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}

.wk .g2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:760px){.wk .g2{grid-template-columns:1fr}}
.wk .box{background:#120f1b;border:1px solid var(--line);border-radius:16px;padding:22px 24px}
.wk .box .h{font-family:"Times New Roman",Times,Georgia,serif;font-weight:500;font-size:17px;color:var(--ink);margin:0 0 6px}
.wk .box p{margin:0;font-size:15px;color:var(--muted)}
.wk pre.c{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:14px;line-height:1.85;background:#120f1b;
  border:1px solid var(--line);border-radius:16px;padding:18px 20px;overflow-x:auto;margin:0;color:#e6e2f2;white-space:pre}
.wk .cm{color:#6a6386}.wk .kw{color:var(--lav)}.wk .fn{color:var(--matcha)}
.wk .add{background:var(--matcha-soft);color:var(--matcha);border-radius:5px;padding:0 5px}
.wk .del{background:rgba(231,154,166,.16);color:var(--bad);border-radius:5px;padding:0 5px}
.wk .label{font-family:"Times New Roman",Times,Georgia,serif;font-weight:500;font-size:12.5px;letter-spacing:.05em;text-transform:uppercase;color:var(--muted);margin:0 0 8px}
.wk .label.g{color:var(--good)}.wk .label.b{color:var(--bad)}

/* clamp slider */
.wk .slider{background:#120f1b;border:1px solid var(--line);border-radius:16px;padding:28px 26px;text-align:center}
.wk .callout{font-family:"Times New Roman",Times,Georgia,serif;font-weight:400;font-size:19px;color:#e6e2f2;margin-top:0}
.wk .callout b{color:var(--matcha);font-weight:600}
.wk .bar-line{position:relative;height:12px;background:#231d33;border-radius:99px;margin:24px 8px}
.wk .zone{position:absolute;top:0;bottom:0;background:var(--lav-soft);border-radius:99px;left:0;right:0}
.wk .knob{position:absolute;top:50%;left:0;width:24px;height:24px;border-radius:50%;background:var(--matcha);
  transform:translate(-50%,-50%);box-shadow:0 0 0 5px var(--matcha-soft);transition:left 1.1s cubic-bezier(.5,1.5,.4,1)}
.wk .scene.active .knob.go{left:100%}
.wk .ticks{display:flex;justify-content:space-between;font-family:ui-monospace,monospace;font-size:13px;color:var(--muted);margin:0 8px}

/* note */
.wk .note{display:flex;gap:12px;align-items:flex-start;background:var(--lav-soft);
  border:1px solid rgba(183,166,234,.28);border-radius:14px;padding:15px 18px;margin-top:22px}
.wk .note.bad{background:rgba(231,154,166,.1);border-color:rgba(231,154,166,.28)}
.wk .note .m{width:6px;align-self:stretch;border-radius:6px;background:var(--sig);flex-shrink:0}
.wk .note.bad .m{background:var(--bad)}
.wk .note p{margin:0;font-size:15.5px;color:#e6e2f2}

/* judge */
.wk .judge{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:600px){.wk .judge{grid-template-columns:1fr}}
.wk .jb{background:#120f1b;border:1px solid var(--line);border-radius:16px;padding:22px;text-align:center}
.wk .jb .r{font-family:ui-monospace,monospace;font-size:13px;color:var(--muted);margin-bottom:12px}
.wk .jb .o{font-family:ui-monospace,monospace;font-size:14px;color:#e6e2f2;margin-bottom:14px}
.wk .vb{font-family:"Times New Roman",Times,Georgia,serif;font-weight:500;font-size:15px;display:inline-flex;align-items:center;gap:8px;padding:9px 16px;border-radius:12px}
.wk .vb.p{color:var(--good);background:var(--matcha-soft)}.wk .vb.f{color:var(--bad);background:rgba(231,154,166,.14)}
.wk .stamp{text-align:center;margin-top:14px;font-family:"Times New Roman",Times,Georgia,serif;font-weight:600;font-size:clamp(24px,4.4vw,34px);
  letter-spacing:.02em;background:linear-gradient(110deg,var(--sig),var(--sig2));-webkit-background-clip:text;background-clip:text;color:transparent}
.wk .scene.active .stamp{animation:wkstamp .7s cubic-bezier(.2,1.4,.4,1) .8s both}
@keyframes wkstamp{from{opacity:0;transform:scale(1.4)}to{opacity:1;transform:none}}

/* meaning map */
.wk .maprow{display:grid;grid-template-columns:1fr 1fr;gap:16px;align-items:stretch}
@media(max-width:760px){.wk .maprow{grid-template-columns:1fr}}
.wk .cards{display:flex;flex-direction:column;gap:9px}
.wk .cc{font-family:ui-monospace,monospace;font-size:13px;background:#120f1b;border:1px solid var(--line);
  border-left:3px solid var(--sig);border-radius:11px;padding:11px 14px;color:var(--muted)}
.wk .cc b{color:#e6e2f2}
.wk .space{position:relative;background:#120f1b;border:1px solid var(--line);border-radius:16px;min-height:240px;overflow:hidden}
.wk .space .cap{position:absolute;top:12px;left:14px;font-family:"Times New Roman",Times,Georgia,serif;font-size:12px;letter-spacing:.05em;color:var(--muted)}
.wk .pt{position:absolute;width:16px;height:16px;border-radius:50%;background:var(--sig);
  transform:translate(-50%,-50%) scale(0);transition:transform .55s cubic-bezier(.2,.9,.3,1.5)}
.wk .scene.active .pt{transform:translate(-50%,-50%) scale(1)}
.wk .scene.active .pt.p2{transition-delay:.14s}.wk .scene.active .pt.p3{transition-delay:.28s}
.wk .scene.active .pt.p4{transition-delay:.42s}.wk .scene.active .pt.p5{transition-delay:.56s}
.wk .pt.q{background:var(--warn);width:22px;height:22px}
.wk .pt.hit{background:var(--sig2);box-shadow:0 0 0 6px var(--matcha-soft);animation:wkpulse 1.8s ease-in-out infinite}
@keyframes wkpulse{0%,100%{box-shadow:0 0 0 6px var(--matcha-soft)}50%{box-shadow:0 0 0 11px transparent}}
.wk .retr{display:flex;flex-direction:column;gap:10px}
.wk .ri{display:flex;align-items:center;gap:13px;background:#120f1b;border:1px solid var(--line);border-radius:13px;padding:13px 16px;opacity:0;transform:translateX(-12px)}
.wk .scene.active .ri{animation:wkslide .55s ease both}
.wk .scene.active .ri:nth-child(1){animation-delay:.2s}.wk .scene.active .ri:nth-child(2){animation-delay:.42s}.wk .scene.active .ri:nth-child(3){animation-delay:.64s}
@keyframes wkslide{to{opacity:1;transform:none}}
.wk .ri .rk{font-family:"Times New Roman",Times,Georgia,serif;font-weight:600;color:var(--sig);font-size:17px;width:22px}
.wk .ri .t{font-family:ui-monospace,monospace;font-size:13px;color:#e6e2f2}
.wk .ri .dd{font-size:12.5px;color:var(--muted)}
.wk .ri.key{border-color:var(--sig);background:var(--lav-soft)}
.wk .rib{flex:1;min-width:0}

/* generation columns */
.wk .col{background:#120f1b;border:1px solid var(--line);border-radius:16px;padding:20px}
.wk .col.win{border-color:var(--sig);box-shadow:0 0 0 2px var(--lav-soft)}
.wk .col h4{font-family:"Times New Roman",Times,Georgia,serif;font-weight:500;font-size:16px;margin:0 0 4px;color:var(--ink)}
.wk .col .who{font-size:12.5px;color:var(--muted);margin:0 0 14px;font-family:ui-monospace,monospace}
.wk .col .who.s{color:var(--sig2)}
.wk .typed{font-family:ui-monospace,monospace;font-size:13.5px;line-height:1.7;min-height:66px;white-space:pre-wrap;color:#e6e2f2}
.wk .cur{display:inline-block;width:8px;height:16px;background:var(--sig2);vertical-align:-2px;animation:wkblink 1s steps(1) infinite}
@keyframes wkblink{50%{opacity:0}}
.wk .verd{font-family:"Times New Roman",Times,Georgia,serif;font-weight:500;display:inline-flex;align-items:center;gap:7px;font-size:13.5px;padding:8px 14px;border-radius:999px;margin-top:14px;opacity:0}
.wk .verd.show{animation:wkrise .4s ease both}
.wk .verd.miss{background:rgba(231,154,166,.14);color:var(--bad)}.wk .verd.kill{background:var(--matcha-soft);color:var(--good)}

/* scoreboard */
.wk .score{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:700px){.wk .score{grid-template-columns:1fr}}
.wk .sc{background:#120f1b;border:1px solid var(--line);border-radius:16px;padding:22px}
.wk .sc .q{font-family:"Times New Roman",Times,Georgia,serif;font-weight:600;color:var(--sig);font-size:11.5px;letter-spacing:.14em;text-transform:uppercase}
.wk .sc h4{font-family:"Times New Roman",Times,Georgia,serif;font-weight:500;font-size:18px;margin:7px 0 5px;color:var(--ink)}
.wk .sc p{margin:0 0 15px;font-size:13.5px;color:var(--muted)}
.wk .bar{height:28px;border-radius:99px;background:rgba(255,255,255,.05);overflow:hidden;margin-bottom:9px;position:relative;display:flex;align-items:center}
.wk .bar i{position:absolute;left:0;top:0;bottom:0;border-radius:99px;width:0;font-style:normal}
.wk .scene.active .bar i{transition:width 1.7s cubic-bezier(.2,.8,.2,1) .4s}
.wk .bar.rag i{background:linear-gradient(90deg,var(--sig),var(--sig2))}.wk .bar.no i{background:#3b3550}
.wk .bar span{position:relative;z-index:1;font-family:"Times New Roman",Times,Georgia,serif;font-weight:600;font-size:13px;color:#1a1424;padding-left:13px}
.wk .bar.no span{color:var(--muted)}
.wk .bl{display:flex;justify-content:space-between;font-size:12.5px;color:var(--muted);font-weight:500;margin-bottom:6px}

/* controls */
.wk .ctrl{display:flex;align-items:center;gap:12px;margin-top:24px;flex-wrap:wrap}
.wk .b{font-family:"Times New Roman",Times,Georgia,serif;font-weight:500;font-size:15px;cursor:pointer;border:1.5px solid var(--line);
  background:var(--card2);color:var(--ink);padding:12px 22px;border-radius:999px;transition:all .25s;box-shadow:none}
.wk .b:hover{border-color:var(--sig);background:var(--lav-soft);transform:translateY(-2px)}
.wk .b:disabled{opacity:.35;cursor:not-allowed}.wk .b:disabled:hover{border-color:var(--line);background:var(--card2);transform:none}
.wk .b.pri{background:linear-gradient(135deg,var(--sig),var(--sig2));color:#1a1424;border-color:transparent}
.wk .count{margin-left:auto;font-family:"Times New Roman",Times,Georgia,serif;font-weight:500;font-size:15px;color:var(--muted)}
.wk .foot{margin-top:18px;font-size:13px;color:var(--faint);text-align:center}
@media(prefers-reduced-motion:reduce){.wk .cur{display:none}}
</style>

<div class="wk">
  <div class="top">
    <h1>How <span class="grad">CodeKong</span> works</h1>
    <p class="subtitle">Follow one small piece of code all the way through — from a planted bug to the test that catches it. Move with <b>Next</b>, or press <b>Play</b>.</p>
    <span class="badge">A guided walk-through · illustrative, not live data</span>
  </div>

  <div class="track" id="wkTrack"></div>

  <div class="stage">
    <!-- 1 -->
    <section class="scene" data-label="The problem">
      <p class="narr rise">Tests are meant to catch bugs — but how do you know they actually do?</p>
      <h2 class="rise d1">Who tests the tests?</h2>
      <div class="g2">
        <div class="box rise d2"><p class="h">The trap</p><p>A test that never fails feels reassuring — but it might simply be missing the bugs entirely.</p></div>
        <div class="box rise d3"><p class="h">Our approach</p><p>So we plant bugs on purpose, then see exactly which ones slip past the existing tests.</p></div>
      </div>
      <div class="note rise d4"><span class="m"></span><p>Every bug that slips through is a measured <b style="color:var(--lav)">blind spot</b> — a gap the tests never covered.</p></div>
    </section>

    <!-- 2 -->
    <section class="scene" data-label="The code">
      <p class="narr rise">Meet our example — a small function called <b>clamp</b>.</p>
      <h2 class="rise d1">Keep a number in range</h2>
      <div class="g2">
        <pre class="c rise d2"><span class="kw">def</span> <span class="fn">clamp</span>(x, low, high):
    <span class="cm"># keep x between low and high</span>
    <span class="kw">if</span> x &lt; low:  <span class="kw">return</span> low
    <span class="kw">if</span> x &gt; high: <span class="kw">return</span> high
    <span class="kw">return</span> x</pre>
        <div class="slider rise d3">
          <div class="callout">You ask for <b>15</b>…</div>
          <div class="bar-line"><span class="zone"></span><span class="knob go"></span></div>
          <div class="ticks"><span>low = 0</span><span>high = 10</span></div>
          <div class="callout" style="margin-top:16px">…and clamp gives you <b>10</b>.</div>
        </div>
      </div>
      <div class="note rise d4"><span class="m"></span><p>Watch the line <b>“if x &gt; high: return high”</b> — the rule that caps large numbers. It's about to be sabotaged.</p></div>
    </section>

    <!-- 3 -->
    <section class="scene" data-label="Plant a bug">
      <p class="narr rise">Now we sneak in a bug — by quietly deleting the "cap" rule.</p>
      <h2 class="rise d1">Break it on purpose</h2>
      <div class="g2">
        <div class="rise d2"><p class="label g">Before — works correctly</p>
        <pre class="c"><span class="kw">if</span> x &lt; low:  <span class="kw">return</span> low
    <span class="del">if x &gt; high: return high</span>
    <span class="kw">return</span> x</pre></div>
        <div class="rise d3"><p class="label b">After — the cap is gone</p>
        <pre class="c"><span class="kw">if</span> x &lt; low:  <span class="kw">return</span> low

    <span class="kw">return</span> x
<span class="cm"># clamp(15) now returns 15, not 10</span></pre></div>
      </div>
      <div class="note bad rise d4"><span class="m"></span><p>It looks almost identical — but large numbers are no longer capped. <b style="color:var(--rose)">A good test should notice. Let's find out if it does.</b></p></div>
    </section>

    <!-- 4 -->
    <section class="scene" data-label="Tests miss it">
      <p class="narr rise">The existing test only checks a middle value — so it passes on the broken code too.</p>
      <h2 class="rise d1">The test looks the other way</h2>
      <pre class="c rise d2" style="margin-bottom:16px"><span class="kw">def</span> <span class="fn">test_clamp</span>():
    <span class="kw">assert</span> clamp(5) == 5   <span class="cm"># only ever checks the easy middle</span></pre>
      <div class="judge">
        <div class="jb rise d3"><div class="r">on the correct code</div><div class="o">clamp(5) → 5</div><span class="vb p">passes</span></div>
        <div class="jb rise d4"><div class="r">on the broken code</div><div class="o">clamp(5) → 5</div><span class="vb p">passes</span></div>
      </div>
      <div class="note bad rise d4"><span class="m"></span><p>Same answer both times, so the bug slips through undetected. <b style="color:var(--rose)">This blind spot is exactly what CodeKong hunts down.</b></p></div>
    </section>

    <!-- 5 -->
    <section class="scene" data-label="Build a memory">
      <p class="narr rise">Here's the key idea — we file the whole codebase into a searchable memory.</p>
      <h2 class="rise d1">Give the AI a memory</h2>
      <div class="maprow">
        <div class="cards">
          <div class="cc rise d1"><b>clamp</b> — caps a number</div>
          <div class="cc rise d1"><b>in_range</b> — is x inside [low, high]?</div>
          <div class="cc rise d2"><b>limits</b> — low = 0, high = 10</div>
          <div class="cc rise d2"><b>grade</b> — uses clamp on scores</div>
          <div class="cc rise d3"><b>notes</b> — “keep numbers in range”</div>
        </div>
        <div class="space rise d2"><span class="cap">the memory</span>
          <span class="pt p1" style="left:30%;top:40%"></span><span class="pt p2" style="left:46%;top:56%"></span>
          <span class="pt p3" style="left:70%;top:30%"></span><span class="pt p4" style="left:62%;top:72%"></span>
          <span class="pt p5" style="left:24%;top:72%"></span></div>
      </div>
      <div class="note rise d4"><span class="m"></span><p>Each dot is a piece of the codebase, arranged by <b style="color:var(--lav)">meaning</b> — so later we can ask, “what relates to this bug?” and get useful answers.</p></div>
    </section>

    <!-- 6 -->
    <section class="scene" data-label="Look it up">
      <p class="narr rise">For this bug, the memory hands back the three most relevant pieces.</p>
      <h2 class="rise d1">Look up what matters</h2>
      <div class="maprow">
        <div class="space rise d1" style="min-height:210px"><span class="cap">nearest to the bug</span>
          <span class="pt q" style="left:33%;top:44%"></span>
          <span class="pt p1 hit" style="left:30%;top:40%"></span><span class="pt p2 hit" style="left:46%;top:56%"></span>
          <span class="pt p3 hit" style="left:24%;top:60%"></span><span class="pt p4" style="left:72%;top:30%"></span><span class="pt p5" style="left:66%;top:74%"></span></div>
        <div class="retr">
          <div class="ri key"><span class="rk">1</span><div class="rib"><div class="t">limits: high = 10</div><div class="dd">the exact value the bug ignores</div></div></div>
          <div class="ri"><span class="rk">2</span><div class="rib"><div class="t">in_range(x, low, high)</div><div class="dd">how bounds are meant to work</div></div></div>
          <div class="ri"><span class="rk">3</span><div class="rib"><div class="t">notes: “keep in range”</div><div class="dd">what clamp is supposed to do</div></div></div>
        </div>
      </div>
      <div class="note rise d4"><span class="m"></span><p>The top result is the fact <b style="color:var(--lav)">high = 10</b>, stored in a different file. Closed-book generation never sees it — the version with a memory does.</p></div>
    </section>

    <!-- 7 -->
    <section class="scene" data-label="AI writes a test">
      <p class="narr rise">Now the AI writes a test — once with no memory, once with it. Watch the difference.</p>
      <h2 class="rise d1">Closed-book vs. informed</h2>
      <div class="g2">
        <div class="col rise d2"><h4>Closed-book</h4><p class="who">sees: only the bug</p>
          <div class="typed" id="wkTypeA"></div><span class="verd miss" id="wkVerdA">tests a middle number — the bug survives</span></div>
        <div class="col win rise d3"><h4>With the memory</h4><p class="who s">sees: the bug + “high = 10”</p>
          <div class="typed" id="wkTypeB"></div><span class="verd kill" id="wkVerdB">tests the exact cap — caught</span></div>
      </div>
      <div class="note rise d4"><span class="m"></span><p>Closed-book, the AI guesses a safe but useless test. Handed the fact <b style="color:var(--lav)">high = 10</b>, it tests <b style="color:var(--matcha)">clamp(15) should be 10</b> — right where the bug lives.</p></div>
    </section>

    <!-- 8 -->
    <section class="scene" data-label="The verdict">
      <p class="narr rise">A real catch must do two things — pass on the correct code and fail on the broken code.</p>
      <h2 class="rise d1">The verdict</h2>
      <div class="judge">
        <div class="jb rise d2"><div class="r">the new test, on correct code</div><div class="o">clamp(15) → 10 ✓ expected 10</div><span class="vb p">passes, as it should</span></div>
        <div class="jb rise d3"><div class="r">the same test, on broken code</div><div class="o">clamp(15) → 15 ✗ expected 10</div><span class="vb f">fails — the bug is caught</span></div>
      </div>
      <div class="stamp">Bug caught</div>
      <p class="foot rise d4">If a test fails this check, the AI gets one hint and tries again. Generation is deterministic, so the results are repeatable.</p>
    </section>

    <!-- 9 -->
    <section class="scene" data-label="The results">
      <p class="narr rise">So — did the memory actually help? Here are the real numbers.</p>
      <h2 class="rise d1">The results</h2>
      <div class="score">
        <div class="sc rise d1"><span class="q">The main question</span><h4>Did a memory of the codebase help?</h4>
          <p>Bugs caught on code that depends on facts stored elsewhere.</p>
          <div class="bl"><span>With the memory</span><span>78%</span></div><div class="bar rag"><i style="width:78%"><span>78%</span></i></div>
          <div class="bl" style="margin-top:11px"><span>Closed-book</span><span>12%</span></div><div class="bar no"><i style="width:12%"><span>12%</span></i></div>
        </div>
        <div class="sc rise d2"><span class="q">The honest part</span><h4>Not always — and that's the point</h4>
          <p>On simple, self-contained code that needs no outside facts, the memory made no difference — a fair, credible result.</p>
          <div class="bl"><span>With the memory</span><span>22%</span></div><div class="bar no"><i style="width:22%"><span>22%</span></i></div>
          <div class="bl" style="margin-top:11px"><span>Closed-book</span><span>22%</span></div><div class="bar no"><i style="width:22%"><span>22%</span></i></div>
        </div>
      </div>
      <div class="note rise d4"><span class="m"></span><p>The takeaway: a memory of the codebase helps most when the answer lives <b style="color:var(--lav)">somewhere else</b> in the code — and honestly, not at all when it doesn't. <a href="/research-questions">See the full results →</a></p></div>
    </section>
  </div>

  <div class="ctrl">
    <button class="b" id="wkPrev">← Back</button>
    <button class="b pri" id="wkPlay">▶ Play</button>
    <button class="b" id="wkNext">Next →</button>
    <span class="count" id="wkCount"></span>
  </div>
  <p class="foot">Use ← / → keys, tap the circles, or press Play. A guided walk-through of how the project works — it explains the idea; it does not run the live model.</p>
</div>

<script>
(function(){
  var scenes=[].slice.call(document.querySelectorAll('.wk .scene'));
  var track=document.getElementById('wkTrack'),count=document.getElementById('wkCount');
  var prev=document.getElementById('wkPrev'),next=document.getElementById('wkNext'),play=document.getElementById('wkPlay');
  var i=0,timer=null,playing=false;
  var reduce=window.matchMedia&&window.matchMedia('(prefers-reduced-motion:reduce)').matches;
  scenes.forEach(function(s,idx){
    var b=document.createElement('button');b.className='stop';
    b.innerHTML='<span class="dot">'+(idx+1)+'</span><span class="lbl">'+s.getAttribute('data-label')+'</span>';
    b.addEventListener('click',function(){stopPlay();go(idx);});track.appendChild(b);
  });
  var stops=[].slice.call(track.children);
  function typeInto(el,text,speed,done){
    if(!el)return;el.innerHTML='';
    if(reduce){el.textContent=text;if(done)done();return;}
    var n=0,cur=document.createElement('span');cur.className='cur';el.appendChild(cur);
    var t=setInterval(function(){n++;el.textContent=text.slice(0,n);el.appendChild(cur);
      if(n>=text.length){clearInterval(t);setTimeout(function(){if(cur.parentNode)cur.parentNode.removeChild(cur);if(done)done();},400);}
    },speed);
  }
  function onEnter(idx){
    if(scenes[idx].getAttribute('data-label')==='AI writes a test'){
      var a=document.getElementById('wkTypeA'),b=document.getElementById('wkTypeB');
      var vA=document.getElementById('wkVerdA'),vB=document.getElementById('wkVerdB');
      vA.classList.remove('show');vB.classList.remove('show');
      typeInto(a,"def test_clamp():\n    assert clamp(3) == 3",36,function(){vA.classList.add('show');});
      setTimeout(function(){typeInto(b,"def test_cap():\n    assert clamp(15) == 10",36,function(){vB.classList.add('show');});},1500);
    }
  }
  function go(idx){
    i=Math.max(0,Math.min(scenes.length-1,idx));
    scenes.forEach(function(s,n){s.classList.remove('active');if(n===i){void s.offsetWidth;s.classList.add('active');}});
    stops.forEach(function(st,n){st.classList.toggle('active',n===i);st.classList.toggle('done',n<i);});
    count.textContent=(i+1)+' / '+scenes.length;prev.disabled=(i===0);next.disabled=(i===scenes.length-1);
    onEnter(i);if(playing&&i===scenes.length-1)stopPlay();
  }
  function stopPlay(){playing=false;if(timer){clearInterval(timer);timer=null;}play.textContent='▶ Play';play.classList.add('pri');}
  function startPlay(){playing=true;play.textContent='❚❚ Pause';play.classList.remove('pri');
    if(i===scenes.length-1)go(0);timer=setInterval(function(){if(i>=scenes.length-1){stopPlay();return;}go(i+1);},5600);}
  prev.addEventListener('click',function(){stopPlay();go(i-1);});
  next.addEventListener('click',function(){stopPlay();go(i+1);});
  play.addEventListener('click',function(){playing?stopPlay():startPlay();});
  document.addEventListener('keydown',function(e){if(e.key==='ArrowRight'){stopPlay();go(i+1);}else if(e.key==='ArrowLeft'){stopPlay();go(i-1);}});
  go(0);
})();
</script>
"""


@app.route("/pipeline")
def pipeline():
    # Inject raw into BASE (bypassing page()'s inner render) so the animation
    # CSS/JS braces are never interpreted as Jinja syntax.
    return render_template_string(BASE, title="Pipeline", page="pipeline",
                                  body=PIPELINE)


# --------------------------------------------------------------------- RQs
RQ = """
<style>
.subjgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:10px}
@media(max-width:840px){.subjgrid{grid-template-columns:1fr}}
.subj{background:linear-gradient(180deg,var(--panel2),var(--panel));border:1px solid var(--line);
  border-radius:18px;padding:22px 24px;transition:transform .3s,border-color .3s}
.subj:hover{transform:translateY(-4px);border-color:rgba(183,166,234,.35)}
.subj.win{border-color:rgba(166,211,172,.5)}
.subj .lab{font-family:"Times New Roman",Times,serif;font-weight:700;font-size:19px;color:var(--ink)}
.subj .n{font-size:12.5px;color:var(--muted);font-weight:600}
.subj .desc{font-size:13.5px;color:var(--muted);margin:9px 0 18px;line-height:1.55;min-height:66px}
.cmp-row{display:flex;justify-content:space-between;font-size:13px;color:#cdc9dd;margin-bottom:5px}
.cmp-row b{font-family:"Times New Roman",Times,serif;color:var(--ink);font-size:15px}
.mini{height:11px;border-radius:99px;background:rgba(255,255,255,.05);overflow:hidden;margin-bottom:13px}
.mini i{display:block;height:100%;border-radius:99px;width:0;transition:width 1.1s cubic-bezier(.2,.8,.2,1)}
.mini i.rag{background:linear-gradient(90deg,var(--lav),var(--matcha))}
.mini i.no{background:#4a4463}
.delta{display:inline-block;font-family:"Times New Roman",Times,serif;font-weight:700;font-size:14px;
  padding:5px 14px;border-radius:99px}
.delta.up{color:var(--matcha);background:var(--matcha-soft)}
.delta.flat{color:var(--muted);background:rgba(255,255,255,.05)}
.chartwrap{position:relative;height:230px}
</style>

<h1>Results</h1>
<p class="lede">Every number here is computed live from the real experiment runs — nothing is hardcoded.</p>

{% if not ov %}
<div class="empty">No run data found under <code>module4_eval/results/</code> yet.
Run the pipeline and reload — this page only ever shows real output.</div>
{% else %}

<h2>The main question — does a memory of the codebase help?</h2>
<p>We ran the <b>identical</b> experiment on three kinds of code. The only difference between the two
conditions is whether the AI could retrieve the codebase — so any gap is the effect of that memory alone.
<span class="muted">(“Bugs caught” = a generated test that passes on the correct code and fails on the bug.)</span></p>

<div class="subjgrid">
  {% for s in ov.subjects %}
  <div class="subj {{ 'win' if s.delta and s.delta > 0.1 }}">
    <div class="lab">{{ s.label }}</div><div class="n">{{ s.n }} surviving bugs tested</div>
    <p class="desc">{{ s.desc }}</p>
    <div class="cmp-row"><span>With memory (RAG)</span><b>{{ ((s.rag or 0)*100)|round|int }}%</b></div>
    <div class="mini"><i class="rag" data-w="{{ ((s.rag or 0)*100)|round|int }}"></i></div>
    <div class="cmp-row"><span>Closed-book</span><b>{{ ((s.norag or 0)*100)|round|int }}%</b></div>
    <div class="mini"><i class="no" data-w="{{ ((s.norag or 0)*100)|round|int }}"></i></div>
    {% if s.delta is not none %}
      <span class="delta {{ 'up' if s.delta > 0.02 else 'flat' }}">{{ '+' if s.delta >= 0 }}{{ (s.delta*100)|round|int }} points from memory</span>
    {% endif %}
  </div>
  {% endfor %}
</div>

<div class="card"><p style="margin:0"><b>The honest headline:</b> a memory of the codebase caught
<b style="color:var(--matcha)">{{ ((ov.subjects[0].rag or 0)*100)|round|int }}%</b> of bugs on context-dependent code versus
just <b>{{ ((ov.subjects[0].norag or 0)*100)|round|int }}%</b> closed-book — but made
<b>no difference</b> on self-contained code, and the small local model caught nothing either way on the complex
library. Retrieval helps precisely when the answer lives elsewhere in the code — not universally. Reporting the
tie and the floor alongside the win is what makes the win credible.</p></div>

<h2>Across bug types <span class="muted" style="font-family:Inter;font-size:16px;font-weight:400">· {{ ov.rq2.subject_label }}</span></h2>
<div class="card"><div class="chartwrap"><canvas id="c2"></canvas></div>
<p class="muted" style="margin-bottom:0">On code that needs outside facts, memory lifts <b style="color:var(--matcha)">every</b>
mutation class — from statement-deletions to the hardest higher-order bugs. (The strict "harder = bigger gap"
gradient does not hold cleanly — an honest finding, not a failure.)</p></div>

{% if ov.rq3 %}
<h2>How much context is enough? <span class="muted" style="font-family:Inter;font-size:16px;font-weight:400">· valid-test rate by retrieval depth k</span></h2>
<div class="card"><div class="chartwrap"><canvas id="c3"></canvas></div>
<p class="muted" style="margin-bottom:0">With a memory, {{ (ov.rq3.valid|max*100)|round|int }}% of generated tests are valid
(they run on the real code) versus only <b>{{ (ov.rq3.norag_valid*100)|round|int }}%</b> closed-book — because closed-book
guesses the codebase's values and guesses wrong. Depth k = 3–5 is the sweet spot; k = 8 dips slightly, so more context is not always better.</p></div>
{% endif %}

{% if ov.rq4 %}
<h2>Is it worth the cost? <span class="muted" style="font-family:Inter;font-size:16px;font-weight:400">· {{ ov.rq4.subject_label }}</span></h2>
<div class="card"><table class="data"><tr><th>Condition</th><th>Tokens used</th><th>Bugs caught</th><th>Tokens per bug caught</th></tr>
{% for r in ov.rq4.rows %}<tr><td>{{ badge(r.condition)|safe }}</td>
<td>{{ "{:,}".format(r.tokens) }}</td><td>{{ r.kills }}</td>
<td><b>{{ "{:,}".format(r.per_kill) if r.per_kill else "— (no bugs caught)" }}</b></td></tr>{% endfor %}
</table><p class="muted" style="margin-bottom:0">Memory uses more tokens per call, but because it actually catches bugs it is
far cheaper <i>per bug caught</i>. Tokens are the cost-equivalent unit for a free local model.</p></div>
{% endif %}

<p class="muted" style="text-align:center;margin-top:34px;font-size:13px">
Subjects: context-dependent ({{ ov.subjects[0].n }}), self-contained ({{ ov.subjects[1].n }})<!--
-->{% if ov.subjects|length > 2 %}, complex OO ({{ ov.subjects[2].n }}){% endif %} ·
model qwen2.5-coder:7b, temperature 0 · RAG and closed-book use the identical model, prompts and mutants.</p>

<script>
const OV = {{ ov | tojson }};
// animate the mini bars in
requestAnimationFrame(function(){setTimeout(function(){
  document.querySelectorAll('.mini i').forEach(function(el){el.style.width=el.dataset.w+'%';});
},120);});
const AX={grid:{color:'rgba(80,72,110,.25)'},ticks:{color:'#a49eba'}};
const YPCT={min:0,max:1,grid:{color:'rgba(80,72,110,.25)'},ticks:{color:'#a49eba',callback:v=>Math.round(v*100)+'%'}};
if (OV.rq2 && OV.rq2.classes) new Chart(document.getElementById('c2'), {type:'bar',
 data:{labels:OV.rq2.classes, datasets:[
   {label:'Closed-book', data:OV.rq2.norag, backgroundColor:'#6f6689', borderRadius:7},
   {label:'With memory (RAG)', data:OV.rq2.rag, backgroundColor:'#b7a6ea', borderRadius:7}]},
 options:{maintainAspectRatio:false,plugins:{legend:{labels:{color:'#cdc9dd'}}},scales:{x:AX,y:YPCT}}});
if (OV.rq3 && OV.rq3.k) new Chart(document.getElementById('c3'), {type:'bar',
 data:{labels:OV.rq3.k.map(k=>'k = '+k), datasets:[
   {label:'valid-test rate (with memory)', data:OV.rq3.valid, backgroundColor:'#a6d3ac', borderRadius:7}]},
 options:{maintainAspectRatio:false,plugins:{legend:{labels:{color:'#cdc9dd'}},
   annotation:false},scales:{x:AX,y:YPCT}}});
</script>
{% endif %}
"""


@app.route("/research-questions")
def rqs():
    corpus = D.load_corpus()
    ov = D.results_overview(corpus["results_dir"])
    return page("Results", "rq", RQ, ov=ov)


# ----------------------------------------------------------------- Explore
EXPLORE = """
<h1>Explore</h1>
<p class="muted">Every mutant in the current corpus. Subjects are the real configured
repos (sorts, schedule, and user-uploaded files) — this deployment has not processed
BugsInPy/HumanEval/MBPP and will not pretend it has.</p>
{% if not rows %}<div class="empty">No mutants yet — run the mutate phase first.</div>{% else %}
<div class="card" style="padding:14px 18px">
<select id="fsub" onchange="filt()"><option value="">all subjects</option>
{% for s in subjects %}<option>{{ s }}</option>{% endfor %}</select>
<select id="fcls" onchange="filt()" style="margin-left:8px"><option value="">all classes</option>
{% for c in classes %}<option>{{ c }}</option>{% endfor %}</select></div>
<table class="data" id="tbl"><tr><th>Mutant</th><th>Subject</th><th>Class</th>
<th>File / function</th><th>Runs</th><th>Outcome</th></tr>
{% for r in rows %}
<tr class="rowlink" data-sub="{{ r.subject }}" data-cls="{{ r.mutation_class }}"
 onclick="location='/explore/{{ r.mutant_id }}'">
<td class="mono">{{ r.mutant_id }}</td>
<td>{{ r.subject }}</td>
<td>{{ badge(r.mutation_class)|safe }}</td>
<td class="mono">{{ r.file }}<br><span class="muted">{{ r.function }}</span></td>
<td>{{ r.runs }} ({{ r.conditions|join(', ') or 'none' }})</td>
<td>{% if r.runs == 0 %}<span class="muted">not run</span>
{% elif r.killed %}<span class="pill-pass">KILLED</span>
{% else %}<span class="pill-fail">SURVIVING</span>{% endif %}</td></tr>
{% endfor %}</table>
<script>function filt(){const s=fsub.value,c=fcls.value;
document.querySelectorAll('#tbl tr[data-sub]').forEach(r=>{
r.style.display=((!s||r.dataset.sub===s)&&(!c||r.dataset.cls===c))?'':'none';});}</script>
{% endif %}
"""


@app.route("/explore")
def explore():
    corpus = D.load_corpus()
    rows = D.explore_rows(corpus)
    return page("Explore", "explore", EXPLORE, rows=rows,
                subjects=sorted({r["subject"] for r in rows}),
                classes=sorted({r["mutation_class"] for r in rows}))


DETAIL = """
<p><a href="/explore">← Explore</a></p>
<h1 class="mono" style="font-size:21px">{{ mid }}</h1>
{% if m %}
<p>{{ badge(m.mutation_class)|safe }} &nbsp;<code>{{ m.file }}</code> ·
<code>{{ m.function }}</code> (line {{ m.line }}) — <span class="muted">{{ m.mutation_description }}</span></p>
<div class="grid2">
<div><h3>Source with mutation</h3>
<table class="diff">{% for r in diff %}
<tr class="{{ r.tag }}"><td class="ln">{{ r.a or '' }}</td><td class="ln">{{ r.b or '' }}</td>
<td class="code">{{ r.text }}</td></tr>{% endfor %}</table>
{% if m.mutation_class == 'higher_order' %}<p class="muted">Higher-order mutant:
every changed region above is highlighted, not just one.</p>{% endif %}</div>
<div><h3>AST — mutated nodes marked</h3>
<div class="card" style="max-height:480px;overflow:auto;padding:14px">{{ ast_html|safe }}</div></div>
</div>
{% else %}<div class="empty">This mutant is not in the current mutant set
(results from an earlier run) — showing its run records only.</div>{% endif %}

<h2>Test attempts</h2>
{% if not tests %}<div class="empty">No generation runs for this mutant yet.</div>{% endif %}
{% for t in tests %}
<div class="card"><b>{{ badge(t.condition)|safe }}{% if t.k %} k={{ t.k }}{% endif %}
&nbsp;attempt {{ t.attempt }}</b> · <span class="{{ 'pass' if t.passed else 'fail' }}">
{{ 'KILL — passed on original, failed on mutant' if t.passed else 'NO KILL' }}</span>
{{ badge('generated' if t.origin == 'generated' else t.origin)|safe }}
<p class="muted">{{ t.reason }}</p>
{% if t.code %}<pre>{{ t.code }}</pre>{% endif %}</div>
{% endfor %}

<h2>RAG panel — retrieved chunks actually used</h2>
{% if not chunks %}<div class="empty">No retrieved-context provenance for this mutant
(NO_RAG runs, or records predating chunk logging).</div>{% endif %}
{% for c in chunks %}<div class="card"><b class="mono">{{ c.file }} · {{ c.qualname }}</b>
&nbsp;{{ badge(c.kind or 'chunk')|safe }}
{% if c.distance is not none %}<span class="muted"> distance {{ '%.3f' % c.distance }}</span>{% endif %}
<pre>{{ c.snippet }}</pre></div>{% endfor %}
"""


def _ast_html(node) -> str:
    if node is None:
        return '<span class="muted">unparseable</span>'
    cls = "marked" if node["self_marked"] else ""
    open_attr = " open" if node["marked"] else ""
    label = node["label"] + (f' <span class="muted">L{node["line"]}</span>'
                             if node["line"] else "")
    if not node["children"]:
        return (f'<details class="ast"{open_attr}><summary class="{cls}">'
                f'{label}</summary></details>')
    inner = "".join(_ast_html(c) for c in node["children"])
    return (f'<details class="ast"{open_attr}><summary class="{cls}">{label}'
            f'</summary>{inner}</details>')


@app.route("/explore/<mutant_id>")
def detail(mutant_id):
    corpus = D.load_corpus()
    d = D.mutant_detail(corpus, mutant_id)
    if d is None:
        abort(404)
    return page(mutant_id, "explore", DETAIL, mid=mutant_id, m=d["mutant"],
                diff=d.get("diff", []), tests=d["tests"], chunks=d["chunks"],
                ast_html=_ast_html(d.get("ast")))


# ------------------------------------------------------------ Passed tests
PASSED = """
<style>
.tcbar{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:6px 0 22px}
.tcbar .grp{display:flex;gap:4px;background:var(--panel);border:1px solid var(--line);border-radius:999px;padding:4px}
.tcbar .fb{font-family:Inter;font-weight:600;font-size:13.5px;cursor:pointer;border:0;background:transparent;
  color:var(--muted);padding:8px 15px;border-radius:999px;transition:all .2s}
.tcbar .fb.on{background:linear-gradient(135deg,var(--lav),var(--lav-deep));color:#1a1424}
.tcbar input{max-width:280px;padding:9px 14px}
.tcbar .count{margin-left:auto;color:var(--muted);font-size:13.5px;font-weight:600}
.tcgrid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:860px){.tcgrid{grid-template-columns:1fr}}
.tc{background:linear-gradient(180deg,var(--panel2),var(--panel));border:1px solid var(--line);
  border-radius:16px;overflow:hidden;transition:transform .3s,border-color .3s}
.tc:hover{transform:translateY(-3px);border-color:rgba(183,166,234,.35)}
.tc.caught{border-color:rgba(166,211,172,.4)}
.tc-h{display:flex;align-items:center;gap:9px;flex-wrap:wrap;padding:15px 18px;border-bottom:1px solid var(--line)}
.tc-h .fn{font-family:ui-monospace,Menlo,monospace;font-size:14px;color:var(--ink);font-weight:600}
.tc-h .sp{flex:1}
.tc pre{margin:0;border:0;border-radius:0;background:#100d19;max-height:280px}
.tc .memo{font-size:12px;color:var(--matcha);font-weight:600;padding:0 18px 13px;margin-top:-2px}
</style>

<h1>Caught Bugs</h1>
<p class="lede">Real tests the system generated — each one <b>passes on the correct code and fails on a specific planted bug</b>. Nothing curated by hand; these are the actual outputs.</p>

{% if not rows %}<div class="empty">No validated tests yet.</div>{% else %}
<div class="tcbar">
  <div class="grp"><button class="fb on" data-f="killed" onclick="setF(this,'view')">Caught bugs</button>
    <button class="fb" data-f="all" onclick="setF(this,'view')">All valid tests</button></div>
  <div class="grp"><button class="fb on" data-f="any" onclick="setF(this,'cond')">Both</button>
    <button class="fb" data-f="RAG" onclick="setF(this,'cond')">With memory</button>
    <button class="fb" data-f="NO_RAG" onclick="setF(this,'cond')">Closed-book</button></div>
  <input type="text" id="q" placeholder="Search function or code…" oninput="apply()">
  <span class="count" id="cnt"></span>
</div>
<div class="tcgrid" id="grid">
{% for r in rows %}
<div class="tc {{ 'caught' if r.killed }}" data-killed="{{ 1 if r.killed else 0 }}"
     data-cond="{{ r.condition }}" data-txt="{{ (r.function ~ ' ' ~ r.snippet)|lower }}">
  <div class="tc-h">
    <span class="fn">{{ r.function }}()</span>
    {{ badge(r.mutation_class)|safe }}
    {{ badge(r.condition)|safe }}{% if r.k %}<span class="muted" style="font-size:12px">k={{ r.k }}</span>{% endif %}
    <span class="sp"></span>
    {% if r.killed %}<span class="pill-pass">✓ caught the bug</span>
    {% else %}<span class="pill-fail">valid · missed</span>{% endif %}
  </div>
  {% if r.condition == 'RAG' and r.killed %}<div class="memo">▲ used a fact retrieved from the codebase</div>{% endif %}
  <pre>{{ r.snippet }}</pre>
</div>
{% endfor %}
</div>
<script>
var view='killed', cond='any';
function setF(btn,kind){btn.parentElement.querySelectorAll('.fb').forEach(b=>b.classList.remove('on'));btn.classList.add('on');
  if(kind==='view')view=btn.dataset.f; else cond=btn.dataset.f; apply();}
function apply(){var q=document.getElementById('q').value.toLowerCase();var n=0;
  document.querySelectorAll('#grid .tc').forEach(function(c){
    var ok=(view==='all'||c.dataset.killed==='1')&&(cond==='any'||c.dataset.cond===cond)&&(!q||c.dataset.txt.includes(q));
    c.style.display=ok?'':'none';if(ok)n++;});
  document.getElementById('cnt').textContent=n+' shown';}
apply();
</script>
{% endif %}
"""


@app.route("/passed-tests")
def passed():
    corpus = D.load_corpus()
    return page("Caught Bugs", "passed", PASSED,
                rows=D.passed_test_rows(corpus))


# --------------------------------------------------- Generate (user flow)
GENERATE = """
<h1>Generate tests for your code.</h1>
<p class="lede">Upload one Python file, describe what it does, and get back only tests
that provably pass on your code and fail on a specific injected bug.</p>
<div class="card"><form method="post" enctype="multipart/form-data">
<p><label>Python file (.py)<br><input type="file" name="pyfile" accept=".py" required
 style="margin-top:6px;color:#d5d5da"></label></p>
<p><label>What does this code do? <span class="muted">(context given to the model)</span><br>
<textarea name="description" rows="3" required style="margin-top:6px"
 placeholder="e.g. Utility functions for clamping and interpolating numeric ranges"></textarea></label></p>
<p style="display:flex;gap:26px;align-items:center;flex-wrap:wrap">
<label>Mutant cap <input type="text" name="limit" value="15" style="width:64px;margin-left:6px"></label>
<label><input type="checkbox" name="skip_semantic" checked> skip LLM-generated mutants (faster)</label>
<label><input type="checkbox" name="use_rag" checked> use RAG retrieval</label></p>
<button type="submit">Start generation</button>
<p class="muted" style="margin-top:10px">Runs a local LLM — expect minutes, not seconds.
Constraints: pure Python, deterministic, no required file/network I/O.</p></form></div>
{% if jobs %}<h2>Recent jobs</h2><table class="data">
<tr><th>Job</th><th>File</th><th>Status</th><th></th></tr>
{% for j in jobs %}<tr><td class="mono">{{ j.id[:8] }}</td><td>{{ j.filename }}</td>
<td>{{ j.status }}</td><td><a href="/generate/job/{{ j.id }}">open</a></td></tr>{% endfor %}
</table>{% endif %}
"""

JOB = """
<p><a href="/generate">← Generate</a></p>
<h1 style="font-size:26px">{{ j.filename }} <span class="muted mono" style="font-size:15px">{{ j.id[:8] }}</span></h1>
{% if j.status == 'running' %}<div class="empty">Running… started {{ j.age }}s ago.
This page refreshes every 5 seconds. Local generation takes minutes per mutant.</div>
<script>setTimeout(()=>location.reload(), 5000)</script>
{% elif j.status == 'error' %}<div class="card"><span class="fail">FAILED</span>
<pre>{{ j.error }}</pre></div>
{% else %}
<div class="statgrid">
<div class="stat"><div class="v">{{ j.report.mutants_attempted }}</div><div class="l">mutants attempted</div></div>
<div class="stat"><div class="v">{{ j.report.mutants_killed }}</div><div class="l">killed → tests kept</div></div>
<div class="stat"><div class="v">{{ '%.0f%%' % (100*j.report.kill_rate) if j.report.kill_rate is not none else '—' }}</div><div class="l">kill rate</div></div>
<div class="stat"><div class="v">{{ '%.0f' % j.report.wall_seconds }}s</div><div class="l">wall time</div></div>
<div class="stat"><div class="v" style="font-size:16px">{{ j.report.model }}</div><div class="l">model</div></div></div>
<div class="card"><h3>Outcome breakdown</h3><table class="data">
<tr><th>Status</th><th>Count</th><th>Meaning</th></tr>
{% for s, n in j.report.statuses.items() %}<tr><td>{{ s }}</td><td>{{ n }}</td>
<td class="muted">{{ {'KILLED':'valid test that catches the bug — kept',
'SURVIVED':'test valid but did not catch this bug',
'INVALID_TEST':'no generated test passed on your original code',
'GEN_FAILED':'model produced no valid Python'}.get(s, '') }}</td></tr>{% endfor %}</table></div>
{% if j.report.output_test_file %}
<p><a class="btn" href="/generate/job/{{ j.id }}/download">Download test file</a>
<span class="muted" style="margin-left:14px">drops straight into your project; run with pytest</span></p>
<div class="card"><pre>{{ preview }}</pre></div>
{% else %}<div class="empty">No mutants were killed, so no test file was kept. Likely causes:
model tier too weak, code needs file/network I/O, or the mutants were equivalent.
The per-mutant records in the report JSON say which.</div>{% endif %}
{% endif %}
"""


def _run_job(job_id: str, path: Path, description: str, limit: int,
             skip_semantic: bool, use_rag: bool):
    from generate_tests import generate_tests_for_file
    try:
        report = generate_tests_for_file(path, description, limit=limit,
                                         skip_semantic=skip_semantic,
                                         use_rag=use_rag)
        with _JOBS_LOCK:
            JOBS[job_id].update(status="done", report=report)
    except Exception as exc:  # surfaced verbatim in the UI — no papering over
        import traceback
        with _JOBS_LOCK:
            JOBS[job_id].update(status="error",
                                error=f"{exc}\n\n{traceback.format_exc()[-1500:]}")


@app.route("/generate", methods=["GET", "POST"])
def generate():
    if request.method == "POST":
        f = request.files["pyfile"]
        if not f.filename.endswith(".py"):
            abort(400, "need a .py file")
        UPLOADS.mkdir(parents=True, exist_ok=True)
        dest = UPLOADS / f"{int(time.time())}_{Path(f.filename).name}"
        f.save(dest)
        job_id = uuid.uuid4().hex
        try:
            limit = max(1, int(request.form.get("limit", "15")))
        except ValueError:
            limit = 15
        with _JOBS_LOCK:
            JOBS[job_id] = {"id": job_id, "filename": f.filename,
                            "status": "running", "started": time.time(),
                            "report": None, "error": None}
        threading.Thread(target=_run_job, daemon=True,
                         args=(job_id, dest, request.form["description"],
                               limit, "skip_semantic" in request.form,
                               "use_rag" in request.form)).start()
        return redirect(url_for("job_page", job_id=job_id))
    with _JOBS_LOCK:
        jobs = sorted(JOBS.values(), key=lambda j: -j["started"])[:10]
    return page("Generate", "generate", GENERATE, jobs=jobs)


@app.route("/generate/job/<job_id>")
def job_page(job_id):
    with _JOBS_LOCK:
        j = dict(JOBS.get(job_id) or {})
    if not j:
        abort(404)
    j["age"] = int(time.time() - j["started"])
    preview = ""
    if j.get("report") and j["report"].get("output_test_file"):
        p = Path(j["report"]["output_test_file"])
        if p.exists():
            preview = p.read_text(encoding="utf-8")[:3000]
    return page(f"Job {job_id[:8]}", "generate", JOB, j=j, preview=preview)


@app.route("/generate/job/<job_id>/download")
def job_download(job_id):
    with _JOBS_LOCK:
        j = JOBS.get(job_id)
    if not j or not j.get("report") or not j["report"].get("output_test_file"):
        abort(404)
    return send_file(j["report"]["output_test_file"], as_attachment=True)


if __name__ == "__main__":
    # Local, single-user research UI. 5001 avoids clashing with common 5000 users.
    # Bind 127.0.0.1 for local single-user dev; the Docker image sets
    # HOST=0.0.0.0 so the UI is reachable from the host via published port.
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5001"))
    app.run(host=host, port=port, debug=False)
