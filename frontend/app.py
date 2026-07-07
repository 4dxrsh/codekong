"""CodeKong UI — panel-facing site + a fully transparent "generate tests for
my file" demo. Read-only over real pipeline outputs (no invented numbers;
missing data renders an explicit empty state). The Generate flow streams REAL
pipeline events (functions found, mutant diffs, retrieved RAG chunks,
validation verdicts) into an animated storyboard, so a non-technical panel
can watch every step happen.

Run:  source venv/bin/activate && python -m frontend.app
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

from flask import (Flask, abort, jsonify, redirect, render_template_string,
                   request, send_file, url_for)

from frontend import data as D

app = Flask(__name__)
UPLOADS = PROJECT_ROOT / "frontend" / "uploads"
JOBS: dict[str, dict] = {}
_JOBS_LOCK = threading.Lock()

STAGES = ["Read code", "Plant bugs", "Build memory", "Write & check tests", "Package"]

# Panel-demo preset: chosen so a live run fits ~5 minutes on the target GPU.
# k=3 (fewer retrieved chunks -> shorter prompts -> faster model calls; the
# k-sweep belongs to the research page, not a live demo), 5 mutants, only the
# fast mutant sources. DRY-RUN THIS before presenting; drop to 3 if too slow.
DEMO_LIMIT, DEMO_K = 5, 3

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
nav{position:sticky;top:0;z-index:10;display:flex;gap:24px;align-items:center;
height:54px;padding:0 max(24px,calc(50vw - 540px));
background:rgba(19,16,16,.75);backdrop-filter:blur(20px);border-bottom:1px solid var(--line)}
nav .brand{font-weight:700;font-size:17px;color:var(--sand);
font-family:"New York",Georgia,"Times New Roman",serif}
nav a{color:var(--muted);text-decoration:none;font-size:13.5px;transition:color .15s}
nav a:hover{color:var(--ink)} nav a.active{color:var(--peach)}
main{max-width:1080px;margin:0 auto;padding:52px 24px 110px}
h1{font-size:42px;font-weight:600;letter-spacing:-.02em;line-height:1.12;margin:.1em 0 .4em;
font-family:"New York",Georgia,"Times New Roman",serif}
h2{font-size:25px;font-weight:600;margin-top:2.2em;
font-family:"New York",Georgia,"Times New Roman",serif;color:var(--sand)}
h3{font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;font-size:12px}
p{color:#d9d0c4} .muted{color:var(--muted)}
.lede{font-size:20px;line-height:1.5;color:var(--muted);max-width:46em}
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
pre .dl{color:var(--red)} pre .al{color:var(--green)}
table.diff{width:100%;border-collapse:collapse;font-size:12.5px;background:#100d0b;
border-radius:12px;overflow:hidden;border:1px solid var(--line)}
table.diff td{padding:1.5px 10px;white-space:pre;font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace}
table.diff td.ln{color:#514639;text-align:right;width:36px;user-select:none}
tr.del td.code{background:rgba(224,106,85,.15)} tr.add td.code{background:rgba(127,201,143,.11)}
tr.del td.code::before{content:"− ";color:var(--red)} tr.add td.code::before{content:"+ ";color:var(--green)}
.pass{color:var(--green);font-weight:600}.fail{color:var(--red);font-weight:600}
.pill-pass{background:rgba(127,201,143,.14);color:var(--green);padding:2px 11px;border-radius:980px;font-weight:600;font-size:12px}
.pill-fail{background:rgba(224,106,85,.15);color:var(--red);padding:2px 11px;border-radius:980px;font-weight:600;font-size:12px}
.pill-warn{background:rgba(217,185,110,.15);color:#d9b96e;padding:2px 11px;border-radius:980px;font-weight:600;font-size:12px}
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
.story .card{animation:rise .45s ease both}
@keyframes rise{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
.livebar{display:flex;align-items:center;gap:10px;color:var(--peach);font-size:13.5px}
.livedot{width:9px;height:9px;border-radius:50%;background:var(--accent);animation:pulse 1.2s infinite}
.dbar{height:6px;border-radius:4px;background:var(--line);overflow:hidden;margin-top:4px}
.dbar>i{display:block;height:100%;background:var(--accent)}
details.ast{margin-left:15px;font-size:13px}
details.ast>summary{cursor:pointer;padding:1px 6px;border-radius:6px;color:#cfc5b6;list-style:none}
details.ast>summary::before{content:"▸ ";color:var(--muted);font-size:10px}
details[open].ast>summary::before{content:"▾ "}
details.ast>summary.marked{background:rgba(217,185,110,.18);color:#d9b96e;font-weight:600}
details.ast>summary:hover{background:#221d18}
details.src>summary{cursor:pointer;color:var(--muted);font-size:12.5px}
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
.stat .v{font-size:27px;font-weight:700;color:var(--peach)}
.stat .l{font-size:12px;color:var(--muted)}
.plain{background:rgba(217,199,167,.07);border-left:3px solid var(--sand);border-radius:0 10px 10px 0;
padding:10px 16px;margin:10px 0;font-size:13.5px;color:var(--sand)}
a{color:var(--peach);text-decoration:none}
label{color:#d9d0c4;font-size:14px}
</style></head><body>
<nav><span class="brand">CodeKong</span>
<a href="/" class="{{ 'active' if page=='home' }}">Home</a>
<a href="/research-questions" class="{{ 'active' if page=='rq' }}">Research Questions</a>
<a href="/papers" class="{{ 'active' if page=='papers' }}">Papers</a>
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
keeps the ones the existing tests fail to catch, and measures whether showing an AI the
actual codebase (RAG) helps it write tests that kill them.</p>
<div class="plain">In plain words: we deliberately break code in tiny ways, check which
breaks nobody notices, and then see if an AI writes better bug-catching tests when it can
read the codebase instead of guessing blind.</div>

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
<tr><td>{{ badge('sdl')|safe }}</td><td>Removes one line of code outright — like a developer accidentally deleting a step</td></tr>
<tr><td>{{ badge('syntactic')|safe }}</td><td>Swaps an operator (<code>&gt;=</code> → <code>&gt;</code>) — a classic typo-style bug</td></tr>
<tr><td>{{ badge('semantic')|safe }}</td><td>An AI writes a realistic, natural-looking bug — the kind a tired developer ships</td></tr>
<tr><td>{{ badge('higher_order')|safe }}</td><td>Two bugs combined in one function — they can mask each other, making them the hardest to catch</td></tr>
</table></div>

<h2>The pipeline</h2>
<div class="card"><div class="pipeline">
<div class="stage"><b>1 · Ingest</b>Read the code and split it into functions</div><div class="arrow">→</div>
<div class="stage"><b>2 · Index</b>Store every function in a searchable AI memory (RAG)</div><div class="arrow">→</div>
<div class="stage"><b>3 · Mutate</b>Plant the four kinds of bugs</div><div class="arrow">→</div>
<div class="stage"><b>4 · Filter</b>Keep only bugs the existing tests miss</div><div class="arrow">→</div>
<div class="stage"><b>5 · Generate</b>AI writes a test aimed at each bug — with or without reading the codebase</div><div class="arrow">→</div>
<div class="stage"><b>6 · Validate</b>A test counts only if it passes on the real code AND fails on the buggy one</div>
</div>
<p class="muted">The research lives in the comparisons: identical generation runs closed-book
(NO_RAG) and with retrieved context (RAG) at K = 3/5/8, per bug class — answering whether
context helps, where it helps most, how much is right, and what a catch costs.</p>
<div class="plain">Want to see it live? The <a href="/generate">Generate</a> page runs this
whole pipeline on any Python file and shows every step as it happens.</div></div>

<h2>References</h2>
<div class="card"><p class="muted">Eight papers ground this work — see the
<a href="/papers">Papers</a> page for what each one did, what it concluded, the gap it
left, and how CodeKong covers that gap.</p></div>
<p style="text-align:center;margin-top:38px"><a class="btn" href="/generate">Run the live demo</a></p>
"""


@app.route("/")
def home():
    return page("Home", "home", HOME)


# ----------------------------------------------------------------- Papers
_PAPERS = [
 ("Higher Order Mutation Testing", "Jia & Harman — Information and Software Technology, 2009",
  "Defined higher-order mutants: instead of planting one bug, combine two or more in the same program.",
  "Combined bugs can be subtler than single ones — they sometimes partially cancel each other out, so simple tests sail right past them.",
  "It defined the harder bug class but said little about how to actually WRITE tests that catch them — and nothing about modern AI doing that job.",
  "CodeKong implements their higher-order class as its hardest difficulty tier and measures whether giving the AI codebase context helps specifically on these."),
 ("μBERT: Mutation Testing using Pre-Trained Language Models", "Degiovanni & Papadakis — ICSTW 2022",
  "Used a language model (BERT) to invent mutants: mask a piece of code and let the model fill in something plausible-but-wrong.",
  "Model-generated mutants are realistic and useful for evaluating test suites.",
  "The AI is used only to CREATE bugs. Killing them — writing the tests — is left to humans or older tools.",
  "CodeKong flips the AI to the other side: it uses an LLM (with retrieval) to KILL surviving mutants, not to create them."),
 ("LLMorpheus: Mutation Testing using Large Language Models", "Tip, Bell & Schäfer — 2024",
  "Same direction as μBERT with modern LLMs: prompt an LLM to propose realistic code mutations.",
  "LLMs produce mutants that resemble real-world bugs better than rule-based mutation operators.",
  "Again, generation-side only — no answer to whether LLMs can reliably write the tests that catch such bugs.",
  "CodeKong uses an LLM for realistic mutants too (our 'semantic' class), but its core contribution is on the test-writing side."),
 ("MuTAP: Effective Test Generation Using Pre-trained LLMs and Mutation Testing", "Dakhel et al. — 2023",
  "Pioneered putting the surviving mutant INTO the prompt: 'here is a bug the tests missed — write a test that catches it.'",
  "Mutant-aware prompting produces stronger tests than plain 'write me tests' prompting.",
  "The model works closed-book: it sees the mutant and the old test, but never the rest of the codebase — no imports, no conventions, no related functions.",
  "This is CodeKong's direct baseline. Our NO_RAG condition mirrors MuTAP; our RAG condition adds retrieved codebase context on top, and the whole experiment measures exactly what that addition buys."),
 ("PRIMG: Efficient LLM-driven Test Generation Using Mutant Prioritization", "Bouafif, Hamdaqa & Zulkoski — EASE 2025",
  "Ranked mutants by how valuable they are to target, so the LLM's limited budget goes to the most useful bugs first.",
  "Prioritization saves significant generation budget for the same test-suite improvement.",
  "It decides WHICH bugs to aim at, but doesn't improve HOW the killing test gets written.",
  "Orthogonal to CodeKong: we keep the mutant set fixed and improve the generation step itself with retrieval. The two ideas could be combined."),
 ("SMART: Semantic Mutation with Adaptive Retrieval and Tuning", "from 'Boosting LLMs for Mutation Generation' — 2026",
  "Combined RAG with mutation work — retrieving real historical bug-fix pairs to help an LLM invent better mutants.",
  "Retrieval of real bug history makes generated mutants more realistic.",
  "Retrieval is aimed at bug CREATION. Whether retrieval helps bug CATCHING was untested.",
  "CodeKong retrieves codebase context to kill mutants that survive — the same tool pointed at the opposite, unanswered side."),
 ("Mutation-Guided LLM-based Test Generation at Meta (ACH)", "Foster et al. — FSE 2025",
  "An industrial system at Meta that hardens code against specific fault classes using LLM-generated tests, at company scale.",
  "The approach works in production: real faults get covered by generated tests that engineers accept.",
  "As an industrial deployment it doesn't isolate WHY it works — there's no controlled comparison of what codebase context contributes.",
  "CodeKong runs the equivalent idea as a small, controlled, ablation-driven study: same model, same prompts, context on vs. off, measured per bug class."),
 ("Test vs. Mutant: Adversarial LLM Agents for Robust Unit Test Generation (AdverTest)", "Chang et al. — 2026",
  "Two AI agents play against each other: one invents mutants, the other writes tests, co-evolving in a loop.",
  "The adversarial loop produces more robust test suites than one-shot generation.",
  "Because mutation and test generation evolve together, you can't attribute gains to any single ingredient.",
  "CodeKong fixes the mutation strategies and changes exactly one variable — retrieved context — so the measured effect is attributable."),
 ("Large Language Models for Unit Testing: A Systematic Literature Review", "2025",
  "Surveyed the whole field of LLMs for software testing.",
  "Maps what has been tried; notes retrieval-augmented approaches to TEST GENERATION are underexplored.",
  "A survey doesn't run experiments — it points at holes.",
  "The hole it points at — does RAG help LLMs write better tests, and when? — is precisely CodeKong's research question."),
]

PAPERS = """
<h1>The papers behind CodeKong</h1>
<p class="lede">Every design choice in this project traces to prior work. For each paper:
what they did, what they concluded, the gap they left, and what we did about it.</p>
{% for title, venue, did, concl, gap, ours in papers %}
<div class="card">
<h2 style="margin-top:0;font-size:20px">{{ title }}</h2>
<p class="muted" style="margin-top:-6px">{{ venue }}</p>
<p><b style="color:var(--sand)">What they did.</b> {{ did }}</p>
<p><b style="color:var(--sand)">What they concluded.</b> {{ concl }}</p>
<p><b style="color:var(--red)">The gap.</b> {{ gap }}</p>
<p><b style="color:var(--green)">What CodeKong does about it.</b> {{ ours }}</p>
</div>
{% endfor %}
"""


@app.route("/papers")
def papers():
    return page("Papers", "papers", PAPERS, papers=_PAPERS)


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
<div class="plain">Plain words: a "kill rate" is the share of planted bugs that the AI's
new tests successfully caught. Higher is better. RAG = the AI could read the codebase;
NO_RAG = it worked blind.</div>
{% if not have_data %}<div class="empty">No pipeline results found yet under
<code>module4_eval/results/</code>. Run <code>python run_pipeline.py --repo sorts</code>
(or a <code>--limit</code> smoke run) and reload — this page computes everything from
the real CSVs and never shows placeholder numbers.</div>{% endif %}

{% if d.rq1 %}<h2>RQ1 — Does reading the codebase help at all?</h2>
<div class="card"><canvas id="c1" height="100"></canvas><p>{{ rq1_take }}</p></div>{% endif %}

{% if d.rq2 %}<h2>RQ2 — Does it help more as bugs get harder?</h2>
<div class="card"><canvas id="c2" height="110"></canvas><p>{{ rq2_take }}</p></div>{% endif %}

{% if d.rq3 %}<h2>RQ3 — How much context is the right amount?</h2>
<div class="card"><canvas id="c3" height="100"></canvas><p>{{ rq3_take }}</p></div>{% endif %}

{% if d.rq4 and d.rq4.rows %}<h2>RQ4 — Is the extra work worth it, per bug type?</h2>
<div class="card"><table class="data"><tr><th>Condition</th><th>Class</th>
<th>Total tokens</th><th>Kills</th><th>Tokens / kill</th></tr>
{% for r in d.rq4.rows %}<tr><td>{{ badge(r.condition)|safe }}</td><td>{{ r.mutation_class }}</td>
<td>{{ "{:,}".format(r.tokens) }}</td><td>{{ r.kills }}</td>
<td>{{ "{:,}".format(r.tokens_per_kill) if r.tokens_per_kill else "— (no kills yet)" }}</td></tr>{% endfor %}
</table><p class="muted">Tokens are the AI's unit of work — a local model has no bill,
so tokens-per-kill is the cost-equivalent measure.</p></div>{% endif %}

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
        verdict = ("Reading the codebase helped" if rag > nor else
                   "Working blind did better" if nor > rag else "The conditions tie")
        return (f"{verdict}: RAG caught {rag:.1%} of bugs vs {nor:.1%} closed-book "
                f"(n={d['rq1'].get('RAG', {}).get('n', 0)} RAG runs). "
                "Reported as computed — no shading either way.")

    def take2():
        if not d["rq2"]:
            return ""
        pairs = [(c, (r or 0) - (n or 0)) for c, r, n in
                 zip(d["rq2"]["classes"], d["rq2"]["rag"], d["rq2"]["norag"])]
        deltas = [f"{c}: {v:+.1%}" for c, v in pairs]
        mono = all(b[1] >= a[1] for a, b in zip(pairs, pairs[1:]))
        return ("How much RAG helped, per bug class — " + "; ".join(deltas) + ". "
                + ("The 'harder bugs benefit more' pattern holds on this data."
                   if mono else "The 'harder bugs benefit more' pattern does NOT "
                   "hold cleanly on this data — an honest finding, not a failure."))

    def take3():
        if not d["rq3"]:
            return ""
        ks, vr = d["rq3"]["k"], d["rq3"]["valid_test_rate"]
        best = ks[vr.index(max(vr))]
        return (f"Test quality peaks at K={best} on current data. More context is "
                "not automatically better — too much can drown the model.")

    return page("Research Questions", "rq", RQ, d=d, have_data=have,
                rq1_take=take1(), rq2_take=take2(), rq3_take=take3())


# ----------------------------------------------------------------- Explore
EXPLORE = """
<h1>Explore</h1>
<div class="plain">Every artificial bug we planted, and what happened to it. Click any
row to see the bug inside the code, what the AI looked up, and the tests it wrote.</div>
<p class="muted">Subjects are the real configured repos (sorts, schedule, and
user-uploaded files) — nothing here is mocked.</p>
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
<div class="plain">Red lines were removed by the bug, green lines were added.</div>
<table class="diff">{% for r in diff %}
<tr class="{{ r.tag }}"><td class="ln">{{ r.a or '' }}</td><td class="ln">{{ r.b or '' }}</td>
<td class="code">{{ r.text }}</td></tr>{% endfor %}</table>
{% if m.mutation_class == 'higher_order' %}<p class="muted">Higher-order mutant:
every changed region above is highlighted, not just one.</p>{% endif %}</div>
<div><h3>Code structure (AST) — bug location marked</h3>
<div class="plain">This is the code as the computer sees it — a tree. Highlighted nodes
are where the bug lives.</div>
<div class="card" style="max-height:440px;overflow:auto;padding:14px">{{ ast_html|safe }}</div></div>
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

<h2>RAG panel — what the AI looked up</h2>
<div class="plain">These are the actual pieces of code the AI retrieved from its memory
before writing the test. Smaller distance = closer match.</div>
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
<div class="plain">Every AI-written test that works on the real code. "KILLED" means it
also catches its target bug — the full proof. These are the tests you'd actually keep.</div>
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
<h1>Generate tests. Watch it happen.</h1>
<p class="lede">Upload one Python file and describe what it does. CodeKong will plant
bugs in it, look things up in its memory, write tests, check them — and show you every
step live.</p>
<div class="card"><form method="post" enctype="multipart/form-data">
<p><label>Python file (.py)<br><input type="file" name="pyfile" accept=".py" required
 style="margin-top:6px;color:#d9d0c4"></label></p>
<p><label>What does this code do? <span class="muted">(the AI reads this)</span><br>
<textarea name="description" rows="3" required style="margin-top:6px"
 placeholder="e.g. Utility functions for clamping and interpolating numeric ranges"></textarea></label></p>
<p><label><input type="checkbox" name="demo" checked onchange="adv.style.display=this.checked?'none':'block'">
<b>Panel demo mode (≈5 minutes)</b> — {{ demo_limit }} bugs, {{ demo_k }} memory look-ups per bug,
fast bug sources only</label></p>
<div id="adv" style="display:none">
<p style="display:flex;gap:26px;align-items:center;flex-wrap:wrap">
<label>Mutant cap <input type="text" name="limit" value="15" style="width:64px;margin-left:6px"></label>
<label>K <input type="text" name="k" value="5" style="width:50px;margin-left:6px"></label>
<label><input type="checkbox" name="skip_semantic" checked> skip AI-generated bugs (faster)</label>
<label><input type="checkbox" name="use_rag" checked> use RAG memory</label></p>
</div>
<button type="submit">Start — and watch every step</button>
<p class="muted" style="margin-top:10px">Runs a local AI model. Tip for presenting: do one
warm-up run first so the model is loaded, and dry-run the demo to confirm timing on your
machine.</p></form></div>
{% if jobs %}<h2>Recent jobs</h2><table class="data">
<tr><th>Job</th><th>File</th><th>Status</th><th></th></tr>
{% for j in jobs %}<tr><td class="mono">{{ j.id[:8] }}</td><td>{{ j.filename }}</td>
<td>{{ j.status }}</td><td><a href="/generate/job/{{ j.id }}">open</a></td></tr>{% endfor %}
</table>{% endif %}
"""

JOB = """
<p><a href="/generate">← Generate</a></p>
<h1 style="font-size:26px">{{ j.filename }} <span class="muted mono" style="font-size:15px">{{ j.id[:8] }}</span></h1>

<div class="card"><div class="stepper" id="stepper">
{% for s in stages %}<div class="step" data-i="{{ loop.index0 }}">
<div class="dot">{{ loop.index }}</div>{{ s }}</div>{% endfor %}
</div>
<p class="livebar" id="livebar" style="justify-content:center"><span class="livedot"></span>
<span id="livetext">connecting…</span></p></div>

<div class="story" id="story"></div>
<div id="finale"></div>

<script>
const JOB_ID = {{ j.id | tojson }};
const NSTAGE = {{ stages|length }};
let since = 0, done = false;
const story = document.getElementById('story');
const esc = s => (s??'').toString().replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
const diffHtml = d => esc(d).split('\\n').map(l =>
  l.startsWith('+') ? `<span class="al">${l}</span>` :
  l.startsWith('-') ? `<span class="dl">${l}</span>` : l).join('\\n');
const chipCls = {sdl:'#8fc8b5', syntactic:'#c9a0e8', semantic:'#d9b96e', higher_order:'#e06a55'};
const chip = c => `<span class="chip" style="background:${chipCls[c]||'#9a8f82'}26;color:${chipCls[c]||'#9a8f82'}">${esc(c)}</span>`;
function section(title, plain, inner){
  story.insertAdjacentHTML('beforeend',
    `<div class="card"><h2 style="margin-top:0;font-size:19px">${title}</h2>
     <div class="plain">${plain}</div>${inner}</div>`);
}
const RENDER = {
 scaffold: p => section('Step 1 — Your code, understood',
   'CodeKong read the file and split it into functions — the units it will protect with tests. It also stored your description, so the AI knows the intent, not just the syntax.',
   p.functions.map(f=>`<details class="src"><summary><code>${esc(f.name)}</code> · ${f.lines} lines</summary><pre>${esc(f.source)}</pre></details>`).join('')
   + `<p class="muted" style="margin-top:8px">Your description: “${esc(p.description)}”</p>`),
 mutants: p => section('Step 2 — Bugs planted (mutants)',
   `It created ${p.mutants.length} copies of your code, each with ONE deliberate small bug that your existing checks do not catch. Red = removed, green = added.`,
   p.mutants.map(m=>`<div style="margin:10px 0">${chip(m.mutation_class)}
     <b class="mono" style="font-size:12.5px">${esc(m.id)}</b>
     <div class="muted" style="font-size:13px">${esc(m.description)}</div>
     <details class="src"><summary>show the exact change</summary><pre>${diffHtml(m.diff)}</pre></details></div>`).join('')),
 indexed: p => section('Step 3 — The AI’s memory (RAG)',
   `Every function and docstring was converted into a numerical fingerprint (an “embedding”) and stored in a local search index — ${p.chunks} chunks, using the ${esc(p.embedding_model)} model. When the AI writes a test, it looks things up here instead of guessing.`,
   ''),
 retrieve: p => section(`Step 4 — What the AI looked up for <span class="mono" style="font-size:14px">${esc(p.mutant_id)}</span>`,
   `Before writing a test, the AI searched its memory and pulled the ${p.chunks.length} closest pieces of context (k=${p.k}, plus your description). Smaller distance = closer match.`,
   p.chunks.map(c=>{
     const d = c.distance==null ? null : Math.max(0, Math.min(1, 1-c.distance));
     return `<div style="margin:8px 0"><b class="mono" style="font-size:12.5px">${esc(c.qualname)}</b>
       ${chip(c.kind)} ${c.distance!=null?`<span class="muted">distance ${c.distance.toFixed(3)}</span>
       <div class="dbar"><i style="width:${(d*100).toFixed(0)}%"></i></div>`:''}
       <details class="src"><summary>show chunk</summary><pre>${esc(c.snippet)}</pre></details></div>`;
   }).join('')),
 result: p => {
   const pill = p.status==='KILLED' ? '<span class="pill-pass">BUG CAUGHT (killed)</span>'
     : p.status==='SURVIVED' ? '<span class="pill-fail">bug not caught</span>'
     : `<span class="pill-warn">${esc(p.status)}</span>`;
   const story_ = p.validations.map(v=>{
     const ok = v.status==='PASS';
     return `<p style="margin:4px 0"><b>Attempt ${v.attempt}:</b>
       <span class="${ok?'pass':'fail'}">${ok?'caught the bug':'did not work'}</span>
       <span class="muted">— ${esc(v.reason)}</span></p>`;}).join('');
   const retry = p.retry_used ? '<p class="muted">The first try failed, so the checker told the AI exactly why, and it got ONE retry — that feedback loop is the “agentic” part.</p>' : '';
   return section(`Verdict for <span class="mono" style="font-size:14px">${esc(p.mutant_id)}</span> ${pill}`,
     'A test only counts if it PASSES on your real code AND FAILS on the buggy copy — both checks actually ran, just now.',
     story_ + retry + (p.test_code?`<details class="src" open><summary>the winning test</summary><pre>${esc(p.test_code)}</pre></details>`:''));
 },
 done: p => {
   document.getElementById('finale').innerHTML = `
     <div class="card"><h2 style="margin-top:0">Done.</h2>
     <div class="statgrid">
     <div class="stat"><div class="v">${p.mutants_attempted}</div><div class="l">bugs planted</div></div>
     <div class="stat"><div class="v">${p.mutants_killed}</div><div class="l">bugs caught → tests kept</div></div>
     <div class="stat"><div class="v">${p.kill_rate!=null?Math.round(p.kill_rate*100)+'%':'—'}</div><div class="l">catch rate</div></div>
     <div class="stat"><div class="v">${Math.round(p.wall_seconds)}s</div><div class="l">total time</div></div></div>
     ${p.output_test_file?`<p style="margin-top:16px"><a class="btn" href="/generate/job/${JOB_ID}/download">Download the test file</a>
     <span class="muted" style="margin-left:12px">every test in it is proof-carrying: passes on your code, fails on its bug</span></p>`
     :`<div class="empty" style="margin-top:14px">No bugs were caught this run, so no test file was kept — the per-bug verdicts above say why.</div>`}
     </div>`;
 }
};
function setStage(stage, running){
  document.querySelectorAll('#stepper .step').forEach(el=>{
    const i = +el.dataset.i;
    el.className = 'step ' + (!running || i < stage ? (i<=stage||!running?'done':'') :
                              i === stage ? 'active' : '');
    el.querySelector('.dot').textContent = (!running || i < stage) ? '✓' : (i+1);
  });
}
async function poll(){
  if (done) return;
  try{
    const r = await fetch(`/generate/job/${JOB_ID}/events.json?since=${since}`);
    const j = await r.json();
    for (const ev of j.events){ since = ev.seq + 1; (RENDER[ev.kind]||(()=>{}))(ev.payload); }
    setStage(j.stage, j.status === 'running');
    document.getElementById('livetext').textContent =
      j.status === 'running' ? (j.detail || 'working…') :
      j.status === 'error' ? 'failed — see below' : 'finished';
    if (j.status === 'error'){
      story.insertAdjacentHTML('beforeend', `<div class="card"><span class="fail">FAILED</span><pre>${esc(j.error)}</pre></div>`);
      done = true;
    }
    if (j.status === 'done'){ done = true;
      document.getElementById('livebar').style.display='none'; }
  }catch(e){ /* transient; keep polling */ }
  if (!done) setTimeout(poll, 1500);
}
poll();
</script>
"""


def _run_job(job_id: str, path: Path, description: str, limit: int,
             k: int | None, skip_semantic: bool, use_rag: bool):
    from generate_tests import generate_tests_for_file

    def cb(stage: int, detail: str):
        with _JOBS_LOCK:
            if job_id in JOBS:
                JOBS[job_id].update(stage=stage, detail=detail)

    def ev(kind: str, payload: dict):
        with _JOBS_LOCK:
            if job_id in JOBS:
                seq = len(JOBS[job_id]["events"])
                JOBS[job_id]["events"].append({"seq": seq, "kind": kind,
                                               "payload": payload})

    try:
        report = generate_tests_for_file(path, description, limit=limit, k=k,
                                         skip_semantic=skip_semantic,
                                         use_rag=use_rag, progress=cb,
                                         on_event=ev)
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
        if "demo" in request.form:
            limit, k = DEMO_LIMIT, DEMO_K
            skip_semantic, use_rag = True, True
        else:
            try:
                limit = max(1, int(request.form.get("limit", "15")))
            except ValueError:
                limit = 15
            try:
                k = max(1, int(request.form.get("k", "5")))
            except ValueError:
                k = None
            skip_semantic = "skip_semantic" in request.form
            use_rag = "use_rag" in request.form
        with _JOBS_LOCK:
            JOBS[job_id] = {"id": job_id, "filename": f.filename,
                            "status": "running", "started": time.time(),
                            "stage": 0, "detail": "", "events": [],
                            "report": None, "error": None}
        threading.Thread(target=_run_job, daemon=True,
                         args=(job_id, dest, request.form["description"],
                               limit, k, skip_semantic, use_rag)).start()
        return redirect(url_for("job_page", job_id=job_id))
    with _JOBS_LOCK:
        jobs = sorted(JOBS.values(), key=lambda j: -j["started"])[:10]
    return page("Generate", "generate", GENERATE, jobs=jobs,
                demo_limit=DEMO_LIMIT, demo_k=DEMO_K)


@app.route("/generate/job/<job_id>")
def job_page(job_id):
    with _JOBS_LOCK:
        j = dict(JOBS.get(job_id) or {})
    if not j:
        abort(404)
    return page(f"Job {job_id[:8]}", "generate", JOB, j=j, stages=STAGES)


@app.route("/generate/job/<job_id>/events.json")
def job_events(job_id):
    since = request.args.get("since", 0, type=int)
    with _JOBS_LOCK:
        j = JOBS.get(job_id)
        if not j:
            abort(404)
        return jsonify({"status": j["status"], "stage": j.get("stage", 0),
                        "detail": j.get("detail", ""),
                        "error": j.get("error"),
                        "events": [e for e in j["events"] if e["seq"] >= since]})


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
