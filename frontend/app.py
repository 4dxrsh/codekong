"""CodeKong UI — judge-facing site + the practical "generate tests for my
file" flow. Read-only over real pipeline outputs (no invented numbers; every
missing dataset renders an explicit empty state), plus a background-job
wrapper around generate_tests.generate_tests_for_file for uploads.

Palette: warm dark (terracotta / peach / sand on brown-black), serif display
headings. Run:  source venv/bin/activate && python -m frontend.app
Then open http://localhost:5001
"""
from __future__ import annotations

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

# Pipeline stages shown in the Generate job stepper (must mirror the
# progress-callback stages in generate_tests.generate_tests_for_file).
STAGES = ["Scaffold", "Mutate & filter", "Index", "Generate & validate", "Package"]

# Warm translucent chips.
BADGE = {"syntactic": "#c9a0e8", "sdl": "#8fc8b5", "semantic": "#d9b96e",
         "higher_order": "#e06a55", "RAG": "#e0795a", "NO_RAG": "#9a8f82",
         "generated": "#9a8f82", "description": "#d9c7a7"}

BASE = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CodeKong — {{ title }}</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
:root{--bg:#131010;--panel:#1b1714;--line:#2b241e;--ink:#f2eae0;--muted:#9a8f82;
--accent:#e0795a;--peach:#f2b28c;--sand:#d9c7a7;--green:#7fc98f;--red:#e06a55;--radius:14px}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.65 -apple-system,BlinkMacSystemFont,"SF Pro Text","Segoe UI",Roboto,Helvetica,Arial,sans-serif;
-webkit-font-smoothing:antialiased}
nav{position:sticky;top:0;z-index:10;display:flex;gap:28px;align-items:center;
height:54px;padding:0 max(24px,calc(50vw - 540px));
background:rgba(19,16,16,.75);backdrop-filter:blur(20px);border-bottom:1px solid var(--line)}
nav .brand{font-weight:700;font-size:17px;letter-spacing:-.01em;color:var(--sand);
font-family:"New York",Georgia,"Times New Roman",serif}
nav a{color:var(--muted);text-decoration:none;font-size:13.5px;transition:color .15s}
nav a:hover{color:var(--ink)} nav a.active{color:var(--peach)}
main{max-width:1080px;margin:0 auto;padding:52px 24px 110px}
h1{font-size:42px;font-weight:600;letter-spacing:-.02em;line-height:1.12;margin:.1em 0 .4em;
font-family:"New York",Georgia,"Times New Roman",serif}
h2{font-size:25px;font-weight:600;letter-spacing:-.01em;margin-top:2.2em;
font-family:"New York",Georgia,"Times New Roman",serif;color:var(--sand)}
h3{font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;font-size:12px}
p{color:#d9d0c4} .muted{color:var(--muted)}
.lede{font-size:20px;line-height:1.5;color:var(--muted);max-width:46em;font-weight:400}
.card{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);
padding:24px 28px;margin:18px 0}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:800px){.grid2{grid-template-columns:1fr}}
.chip{display:inline-block;padding:2px 11px;border-radius:980px;font-size:12px;font-weight:600}
table.data{width:100%;border-collapse:collapse;font-size:13.5px}
table.data th{color:var(--muted);font-weight:500;font-size:11.5px;text-transform:uppercase;
letter-spacing:.06em;text-align:left;padding:10px;border-bottom:1px solid var(--line)}
table.data td{padding:10px;border-bottom:1px solid var(--line);vertical-align:top}
tr.rowlink{cursor:pointer;transition:background .12s} tr.rowlink:hover{background:#221d18}
pre,code,.mono{font-family:ui-monospace,"SF Mono",SFMono-Regular,Menlo,Consolas,monospace}
code{background:#241e19;padding:1px 6px;border-radius:6px;font-size:13px;color:var(--peach)}
pre{background:#100d0b;border:1px solid var(--line);color:#e9e1d5;padding:16px 18px;
border-radius:12px;overflow-x:auto;font-size:13px;line-height:1.55}
table.diff{width:100%;border-collapse:collapse;font-size:12.5px;background:#100d0b;
border-radius:12px;overflow:hidden;border:1px solid var(--line)}
table.diff td{padding:1.5px 10px;white-space:pre;font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace}
table.diff td.ln{color:#514639;text-align:right;width:36px;user-select:none}
tr.del td.code{background:rgba(224,106,85,.15)} tr.add td.code{background:rgba(127,201,143,.11)}
tr.del td.code::before{content:"− ";color:var(--red)} tr.add td.code::before{content:"+ ";color:var(--green)}
.pass{color:var(--green);font-weight:600}.fail{color:var(--red);font-weight:600}
.pill-pass{background:rgba(127,201,143,.14);color:var(--green);padding:2px 11px;border-radius:980px;font-weight:600;font-size:12px}
.pill-fail{background:rgba(224,106,85,.15);color:var(--red);padding:2px 11px;border-radius:980px;font-weight:600;font-size:12px}
.empty{padding:34px;text-align:center;color:var(--muted);background:var(--panel);
border:1px dashed var(--line);border-radius:var(--radius)}
.pipeline{display:flex;gap:8px;align-items:stretch;flex-wrap:wrap}
.stage{flex:1 1 150px;background:#100d0b;border:1px solid var(--line);border-radius:12px;
padding:12px 14px;font-size:12.5px;color:var(--muted)}
.stage b{display:block;color:var(--peach);font-size:13px;margin-bottom:3px}
.arrow{align-self:center;color:var(--muted)}
.stepper{display:flex;margin:8px 0 4px}
.step{flex:1;text-align:center;position:relative;color:var(--muted);font-size:12px;z-index:1}
.step .dot{width:28px;height:28px;border-radius:50%;margin:0 auto 8px;display:flex;
align-items:center;justify-content:center;background:#241e19;border:1.5px solid var(--line);
font-weight:700;font-size:12.5px}
.step.done{color:var(--sand)} .step.done .dot{background:var(--accent);border-color:var(--accent);color:#fff}
.step.active{color:var(--peach)} .step.active .dot{border-color:var(--accent);color:var(--peach);
animation:pulse 1.4s infinite}
.step:not(:first-child)::before{content:"";position:absolute;top:14px;left:-50%;width:100%;
height:2px;background:var(--line);z-index:-1}
.step.done:not(:first-child)::before,.step.active:not(:first-child)::before{background:var(--accent)}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(224,121,90,.35)}50%{box-shadow:0 0 0 8px rgba(224,121,90,0)}}
details.ast{margin-left:15px;font-size:13px}
details.ast>summary{cursor:pointer;padding:1px 6px;border-radius:6px;color:#cfc5b6;list-style:none}
details.ast>summary::before{content:"▸ ";color:var(--muted);font-size:10px}
details[open].ast>summary::before{content:"▾ "}
details.ast>summary.marked{background:rgba(217,185,110,.18);color:#d9b96e;font-weight:600}
details.ast>summary:hover{background:#221d18}
input[type=text],textarea,select{width:100%;padding:10px 13px;border:1px solid var(--line);
border-radius:10px;font-size:14px;background:#100d0b;color:var(--ink);outline:none}
input:focus,textarea:focus{border-color:var(--accent)}
select{width:auto}
button,.btn{background:var(--accent);color:#fff;border:0;border-radius:980px;
padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer;text-decoration:none;
display:inline-block;transition:opacity .15s}
button:hover,.btn:hover{opacity:.85}
.refs li{margin-bottom:11px;font-size:13.5px;color:#d9d0c4} .refs .why{color:var(--muted)}
.statgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}
.stat{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);
padding:16px;text-align:center}
.stat .v{font-size:27px;font-weight:700;letter-spacing:-.02em;color:var(--peach)}
.stat .l{font-size:12px;color:var(--muted)}
a{color:var(--peach);text-decoration:none}
label{color:#d9d0c4;font-size:14px}
</style></head><body>
<nav><span class="brand">CodeKong</span>
<a href="/" class="{{ 'active' if page=='home' }}">Home</a>
<a href="/research-questions" class="{{ 'active' if page=='rq' }}">Research Questions</a>
<a href="/explore" class="{{ 'active' if page=='explore' }}">Explore</a>
<a href="/passed-tests" class="{{ 'active' if page=='passed' }}">Passed Tests</a>
<a href="/generate" class="{{ 'active' if page=='generate' }}">Generate</a>
<a href="/about" class="{{ 'active' if page=='about' }}">About</a>
</nav><main>{{ body|safe }}</main>
<script>if (window.Chart){Chart.defaults.color='#9a8f82';
Chart.defaults.borderColor='#2b241e';Chart.defaults.font.family='-apple-system,Segoe UI,Roboto,sans-serif';}</script>
</body></html>"""


def page(title, pg, body, **ctx):
    inner = render_template_string(body, **ctx)
    return render_template_string(BASE, title=title, page=pg, body=inner)


def badge(kind: str) -> str:
    c = BADGE.get(kind, "#9a8f82")
    return (f'<span class="chip" style="background:{_rgba(c, .16)};'
            f'color:{c}">{kind}</span>')


def _rgba(hex_color: str, a: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{a})"


app.jinja_env.globals.update(badge=badge)


# ------------------------------------------------------------------- Home
HOME = """
<h1>Tests that hunt the bugs<br>your suite already missed.</h1>
<p class="lede">CodeKong plants four escalating classes of artificial bugs in real code,
keeps the ones the existing tests fail to catch, and measures whether showing an LLM the
actual codebase (RAG) helps it write tests that kill them.</p>

<h2>What is mutation testing?</h2>
<div class="card">
<p>Mutation testing plants small artificial bugs ("mutants") in working code and checks
whether the test suite notices. Every mutant the suite fails to catch is a measured blind spot.</p>
<div class="grid2">
<pre># Original
def is_valid_password(pw):
    return len(pw) &gt;= 8</pre>
<pre># Mutant (&gt;= becomes &gt;)
def is_valid_password(pw):
    return len(pw) <span style="background:rgba(224,106,85,.25);border-radius:4px;padding:0 5px">&gt;</span> 8</pre>
</div>
<p class="muted"><i>If the test suite never checks a password of exactly length 8, this
mutant survives — and that survival is exactly the blind spot mutation testing exists to find.</i></p>
<table class="data"><tr><th>Class</th><th>What it does</th></tr>
<tr><td>{{ badge('sdl')|safe }}</td><td>Removes a statement outright (Python <code>ast</code>)</td></tr>
<tr><td>{{ badge('syntactic')|safe }}</td><td>Swaps an operator or constant (<code>&gt;=</code> → <code>&gt;</code>), via mutmut</td></tr>
<tr><td>{{ badge('semantic')|safe }}</td><td>An LLM injects a realistic, natural-looking bug rather than a fixed rule</td></tr>
<tr><td>{{ badge('higher_order')|safe }}</td><td>Combines two first-order mutants in one function (Jia &amp; Harman), simulating interacting faults</td></tr>
</table></div>

<h2>The pipeline</h2>
<div class="card"><div class="pipeline">
<div class="stage"><b>1 · Ingest</b>Parse the subject repo's functions via AST</div><div class="arrow">→</div>
<div class="stage"><b>2 · Index</b>Embed function, docstring and test chunks into local ChromaDB</div><div class="arrow">→</div>
<div class="stage"><b>3 · Mutate</b>Four strategies generate candidate mutants</div><div class="arrow">→</div>
<div class="stage"><b>4 · Filter</b>Run the existing suite; keep only survivors</div><div class="arrow">→</div>
<div class="stage"><b>5 · Generate</b>Top-K chunks + diff + class-aware prompt → local LLM, one validator-guided retry</div><div class="arrow">→</div>
<div class="stage"><b>6 · Validate</b>Pass on original AND fail on mutant = kill; tokens, K, chunks logged</div>
</div>
<p class="muted">The research lives in the ablations: identical generation runs closed-book
(NO_RAG, MuTAP-style) and with retrieved context (RAG) at K = 3/5/8, per mutation class —
answering whether context helps, where it helps most, how much is right, and what a kill costs.</p></div>

<h2>References</h2>
<div class="card"><ul class="refs">
<li>Jia &amp; Harman, <i>Higher Order Mutation Testing</i>, IST 2009. <span class="why">— foundational definition of the higher-order strategy CodeKong implements.</span></li>
<li>Degiovanni &amp; Papadakis, <i>μBERT</i>, ICSTW 2022; Tip, Bell &amp; Schäfer, <i>LLMorpheus</i>, 2024. <span class="why">— LLMs to <i>generate</i> mutants; CodeKong instead uses RAG-augmented LLMs on the <i>test-generation</i> side, to kill them.</span></li>
<li>Bouafif, Hamdaqa &amp; Zulkoski, <i>PRIMG</i>, EASE 2025. <span class="why">— prioritizes which mutants to target; orthogonal to CodeKong's how-to-kill focus.</span></li>
<li>Dakhel et al., <i>MuTAP</i>, 2023. <span class="why">— pioneered prompting with surviving mutants, closed-book; CodeKong's RAG-vs-NO_RAG ablation directly tests what codebase context adds on top.</span></li>
<li><i>SMART</i> (Boosting LLMs for Mutation Generation), 2026. <span class="why">— retrieves historical bug-fix pairs to generate better mutants; CodeKong retrieves codebase context to kill surviving ones.</span></li>
<li>Foster et al., <i>Mutation-Guided LLM-based Test Generation at Meta</i> (ACH), FSE 2025. <span class="why">— the industrial-scale cousin; CodeKong runs the idea as a controlled, ablation-driven study.</span></li>
<li>Chang et al., <i>AdverTest</i>, 2026. <span class="why">— adversarial co-evolution of tests and mutants; CodeKong fixes the mutation strategies and isolates what RAG context does.</span></li>
<li><i>LLMs for Unit Testing: A Systematic Literature Review</i>, 2025. <span class="why">— survey situating RAG-for-testing.</span></li>
</ul></div>
<p style="text-align:center;margin-top:38px"><a class="btn" href="/research-questions">See the research questions answered</a></p>
"""


@app.route("/")
def home():
    return page("Home", "home", HOME)


# ------------------------------------------------------------------ About
# EDIT HERE: replace the placeholder strings below with the real details
# (project blurb, team members, course/institution, acknowledgements).
ABOUT = """
<h1>About</h1>
<p class="lede">CodeKong is a capstone research project on RAG-grounded mutation testing —
built end to end on free, local tooling.</p>
<div class="card"><h3>The project</h3>
<p class="muted">— details to be added —</p></div>
<div class="card"><h3>The team</h3>
<p class="muted">— details to be added —</p></div>
<div class="card"><h3>Course &amp; institution</h3>
<p class="muted">— details to be added —</p></div>
<div class="card"><h3>Acknowledgements</h3>
<p class="muted">— details to be added —</p></div>
"""


@app.route("/about")
def about():
    return page("About", "about", ABOUT)


# --------------------------------------------------------------------- RQs
RQ = """
<h1>Research Questions</h1>
{% if not have_data %}<div class="empty">No pipeline results found yet under
<code>module4_eval/results/</code>. Run <code>python run_pipeline.py --repo sorts</code>
(or a <code>--limit</code> smoke run) and reload — this page computes everything from
the real CSVs and never shows placeholder numbers.</div>{% endif %}

{% if d.rq1 %}<h2>RQ1 — Does RAG beat closed-book generation?</h2>
<div class="card"><canvas id="c1" height="100"></canvas><p>{{ rq1_take }}</p></div>{% endif %}

{% if d.rq2 %}<h2>RQ2 — Does the benefit vary by mutation class?</h2>
<div class="card"><canvas id="c2" height="110"></canvas><p>{{ rq2_take }}</p></div>{% endif %}

{% if d.rq3 %}<h2>RQ3 — How much retrieved context is right?</h2>
<div class="card"><canvas id="c3" height="100"></canvas><p>{{ rq3_take }}</p></div>{% endif %}

{% if d.rq4 and d.rq4.rows %}<h2>RQ4 — Is the cost worth it, per bug type?</h2>
<div class="card"><table class="data"><tr><th>Condition</th><th>Class</th>
<th>Total tokens</th><th>Kills</th><th>Tokens / kill</th></tr>
{% for r in d.rq4.rows %}<tr><td>{{ badge(r.condition)|safe }}</td><td>{{ r.mutation_class }}</td>
<td>{{ "{:,}".format(r.tokens) }}</td><td>{{ r.kills }}</td>
<td>{{ "{:,}".format(r.tokens_per_kill) if r.tokens_per_kill else "— (no kills yet)" }}</td></tr>{% endfor %}
</table><p class="muted">Token counts come from the Ollama call log (eval + prompt tokens);
a local model has no bill, so tokens are the cost-equivalent unit.</p></div>{% endif %}

<script>
const D = {{ d | tojson }};
if (D.rq1 && Object.keys(D.rq1).length) new Chart(document.getElementById('c1'), {type:'bar',
 data:{labels:Object.keys(D.rq1), datasets:[{label:'kill rate',
 data:Object.values(D.rq1).map(x=>x.kill_rate),
 backgroundColor:['#9a8f82','#e0795a'], borderRadius:8}]},
 options:{scales:{y:{min:0,max:1}},plugins:{legend:{display:false}}}});
if (D.rq2 && D.rq2.classes) new Chart(document.getElementById('c2'), {type:'bar',
 data:{labels:D.rq2.classes, datasets:[
 {label:'NO_RAG', data:D.rq2.norag, backgroundColor:'#9a8f82', borderRadius:8},
 {label:'RAG', data:D.rq2.rag, backgroundColor:'#e0795a', borderRadius:8}]},
 options:{scales:{y:{min:0,max:1,title:{display:true,text:'kill rate'}}}}});
if (D.rq3 && D.rq3.k) new Chart(document.getElementById('c3'), {type:'line',
 data:{labels:D.rq3.k, datasets:[
 {label:'kill rate', data:D.rq3.kill_rate, borderColor:'#e0795a', tension:.3},
 {label:'valid test rate', data:D.rq3.valid_test_rate, borderColor:'#d9c7a7', tension:.3}]},
 options:{scales:{y:{min:0,max:1},x:{title:{display:true,text:'retrieval depth K'}}}}});
</script>
"""


@app.route("/research-questions")
def rqs():
    corpus = D.load_corpus()
    d = D.rq_chart_data(corpus["results_dir"])
    have = any(bool(v) for v in d.values())

    def take1():
        if not d["rq1"]:
            return ""
        rag = d["rq1"].get("RAG", {}).get("kill_rate")
        nor = d["rq1"].get("NO_RAG", {}).get("kill_rate")
        if rag is None or nor is None:
            return "Only one condition has been run so far — no comparison yet."
        verdict = ("RAG kills more" if rag > nor else
                   "NO_RAG kills more" if nor > rag else "The conditions tie")
        return (f"{verdict}: RAG {rag:.1%} vs closed-book {nor:.1%} "
                f"(n={d['rq1'].get('RAG', {}).get('n', 0)} RAG runs). "
                "Reported as computed — no shading either way.")

    def take2():
        if not d["rq2"]:
            return ""
        pairs = [(c, (r or 0) - (n or 0)) for c, r, n in
                 zip(d["rq2"]["classes"], d["rq2"]["rag"], d["rq2"]["norag"])]
        deltas = [f"{c}: {v:+.1%}" for c, v in pairs]
        mono = all(b[1] >= a[1] for a, b in zip(pairs, pairs[1:]))
        return ("Per-class RAG deltas — " + "; ".join(deltas) + ". "
                + ("The hardness gradient holds (non-decreasing) on this data."
                   if mono else "The hardness gradient does NOT hold cleanly "
                   "on this data — an honest finding, not a failure."))

    def take3():
        if not d["rq3"]:
            return ""
        ks, vr = d["rq3"]["k"], d["rq3"]["valid_test_rate"]
        best = ks[vr.index(max(vr))]
        return (f"Valid-test rate peaks at K={best} on current data. Watch "
                "whether more context helps or drowns the model — both are "
                "reportable outcomes.")

    return page("Research Questions", "rq", RQ, d=d, have_data=have,
                rq1_take=take1(), rq2_take=take2(), rq3_take=take3())


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
<h1 class="mono" style="font-size:21px;font-family:ui-monospace,Menlo,monospace">{{ mid }}</h1>
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
{{ badge(t.origin)|safe }}
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
<h1>Passed Tests</h1>
<p class="muted">Every generated test that passed on the original code (valid tests),
across the whole corpus. KILLED additionally means it failed on its mutant — the full
kill criterion. Subjects' original suites gate mutant survival upstream and are not
itemized here (doctest-based suites don't decompose into named cases).</p>
{% if not rows %}<div class="empty">No validated tests yet.</div>{% else %}
<input type="text" id="q" placeholder="Search mutant, subject, class…"
 onkeyup="f()" style="margin-bottom:14px">
<table class="data" id="tbl"><tr><th>Mutant</th><th>Subject</th><th>Class</th>
<th>Condition</th><th>Killed?</th><th>Test snippet</th></tr>
{% for r in rows %}<tr>
<td class="mono"><a href="/explore/{{ r.mutant_id }}">{{ r.mutant_id }}</a></td>
<td>{{ r.subject }}</td><td>{{ badge(r.mutation_class)|safe }}</td>
<td>{{ badge(r.condition)|safe }}{% if r.k %} k={{ r.k }}{% endif %}</td>
<td>{% if r.killed %}<span class="pill-pass">KILLED</span>
{% else %}<span class="pill-fail">valid, no kill</span>{% endif %}</td>
<td><pre style="max-width:420px;max-height:150px;overflow:auto;margin:0">{{ r.snippet }}</pre></td>
</tr>{% endfor %}</table>
<script>function f(){const q=document.getElementById('q').value.toLowerCase();
document.querySelectorAll('#tbl tr').forEach((r,i)=>{if(!i)return;
r.style.display=r.textContent.toLowerCase().includes(q)?'':'none';});}</script>
{% endif %}
"""


@app.route("/passed-tests")
def passed():
    corpus = D.load_corpus()
    return page("Passed Tests", "passed", PASSED,
                rows=D.passed_test_rows(corpus))


# --------------------------------------------------- Generate (user flow)
GENERATE = """
<h1>Generate tests for your code.</h1>
<p class="lede">Upload one Python file, describe what it does, and get back only tests
that provably pass on your code and fail on a specific injected bug.</p>
<div class="card"><form method="post" enctype="multipart/form-data">
<p><label>Python file (.py)<br><input type="file" name="pyfile" accept=".py" required
 style="margin-top:6px;color:#d9d0c4"></label></p>
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

<div class="card"><div class="stepper">
{% for s in stages %}<div class="step {{ 'done' if (j.status != 'running') or loop.index0 < j.stage
 else ('active' if loop.index0 == j.stage else '') }}">
<div class="dot">{% if (j.status != 'running') or loop.index0 < j.stage %}✓{% else %}{{ loop.index }}{% endif %}</div>
{{ s }}</div>{% endfor %}
</div>
{% if j.status == 'running' %}<p style="text-align:center" class="muted">
{{ j.detail or 'starting…' }} · {{ j.age }}s elapsed · this page refreshes every 5 s</p>{% endif %}</div>

{% if j.status == 'running' %}
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

    def cb(stage: int, detail: str):
        with _JOBS_LOCK:
            if job_id in JOBS:
                JOBS[job_id].update(stage=stage, detail=detail)

    try:
        report = generate_tests_for_file(path, description, limit=limit,
                                         skip_semantic=skip_semantic,
                                         use_rag=use_rag, progress=cb)
        with _JOBS_LOCK:
            JOBS[job_id].update(status="done", report=report,
                                stage=len(STAGES) - 1)
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
                            "stage": 0, "detail": "",
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
    j.setdefault("stage", 0)
    j.setdefault("detail", "")
    preview = ""
    if j.get("report") and j["report"].get("output_test_file"):
        p = Path(j["report"]["output_test_file"])
        if p.exists():
            preview = p.read_text(encoding="utf-8")[:3000]
    return page(f"Job {job_id[:8]}", "generate", JOB, j=j, preview=preview,
                stages=STAGES)


@app.route("/generate/job/<job_id>/download")
def job_download(job_id):
    with _JOBS_LOCK:
        j = JOBS.get(job_id)
    if not j or not j.get("report") or not j["report"].get("output_test_file"):
        abort(404)
    return send_file(j["report"]["output_test_file"], as_attachment=True)


if __name__ == "__main__":
    # Local, single-user research UI. 5001 avoids clashing with common 5000 users.
    app.run(host="127.0.0.1", port=5001, debug=False)
