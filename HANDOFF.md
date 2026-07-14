# HANDOFF — CodeKong session continuation

You are picking up the CodeKong project mid-stream from a previous Claude Code session.
Working dir: `C:\CAPSTONE\CCBD\CodeKong` (Windows, git repo). Read `CLAUDE.md` and `README.md`
first for the project basics — but note **CLAUDE.md's "Current state / open work" section is
partly STALE** (it says research runs aren't done; they ARE done now). This file is the
authoritative current state.

## What CodeKong is (30s)
A mutation-testing research pipeline testing whether giving an LLM retrieved context from the
codebase under test (RAG) helps it write tests that kill more surviving mutants than closed-book
(NO_RAG / MuTAP-style). Four mutant classes (syntactic/mutmut, sdl, semantic/LLM, higher-order),
four RQs (RQ1 RAG-vs-NO_RAG, RQ2 per-class, RQ3 retrieval depth k=3/5/8, RQ4 tokens-per-kill).
Fully local: Ollama (qwen2.5-coder:7b), ChromaDB, sentence-transformers. No paid API by design.

## Git state
- Branch `main` and `experiment-results-ui-paper` **both at commit `a4637ff`** (all work committed).
- Working tree is clean. **No git remote is configured yet.**
- An OLDER version was already pushed to a GitHub repo (URL not in this repo). To push the new
  work: **close Cursor first** (its git watcher grabs `.git` locks — if you see "cannot lock ref",
  run `rm -f .git/*.lock`), then `git remote add origin <URL>`, `git fetch origin`, then
  `git push -u origin main` (or `git push --force-with-lease origin main` if it's rejected as
  non-fast-forward — safe, local is the complete superset). Default branch may be `main` OR `master`.

## What the previous session did
1. Fixed `tests/smoke_all.py`: the fork-guard test is now platform-aware (9/9 on Windows too).
2. Built the WSL run environment at `~/codekong` (venv with all deps incl. torch on Python 3.14;
   Ollama serving `qwen2.5-coder:7b`). The pipeline's **mutate** phase needs WSL because mutmut
   needs `fork()` — native Windows can't. `generate_tests.py` + SDL/semantic/HOM run fine on Windows.
3. **Fixed two real RAG bugs** (`module2_rag/rag_indexer.py` + `retriever.py`):
   (a) the indexer now chunks module-level **constants** (was functions/docstrings only), and
   (b) **dependency-aware retrieval**: for each mutant it fetches the **definitions** of the symbols
   the unit references (`retriever.referenced_symbols` / `_fetch_definitions`). Before these, RAG
   never retrieved the constant a context-dependent test needed and couldn't win.
4. Built `subjects/ctxlib` — a context-dependent **benchmark** (billing/grading/shipping functions
   whose correctness depends on constants in a separate `rates.py`; docstrings never state the
   values). Registered in `config.yaml` (also `sorts_focused`, a curated 10-file subset of
   TheAlgorithms sorts).
5. Ran the experiments and got **real results** (below).
6. Redesigned the Flask frontend (twilight-pastel, Times New Roman headers, lavender+matcha):
   new **"How It Works"** storybook tab (`/pipeline`), **Results** page (`/research-questions`)
   computes per-subject RQ1–4 **live** from the real CSVs, **"Caught Bugs"** page (`/passed-tests`)
   shows the real generated tests. `frontend/data.py` gained `results_overview()` + `resolve_test_file()`.
7. Wrote an IEEE conference paper: `paper/CodeKong_RAG_Mutation_Testing.docx` (also a rendered
   preview PDF in the user's Downloads). ~5 pages, figures, algorithm, worked example, ablation.

## The real results (in `module4_eval/results/` as `records_*.json` + raw/cost/summary CSVs)
Per-subject kill rate (NO_RAG → RAG):

| Subject | N | NO_RAG | RAG |
|---|---|---|---|
| ctxlib (context-dependent) | 24 | 12.5% | **77.8%** |
| sorts_focused (self-contained) | 9 | 22.2% | 22.2% (tie) |
| schedule (complex OO) | 6 | 0% | 0% (7B floors, all INVALID_TEST) |
| combined | 39 | 12.8% | 53.0% |

- ctxlib per class (NO_RAG→RAG): sdl 15.4%→82.1%, semantic 14.3%→61.9%, higher_order 0%→91.7%.
- ctxlib valid-test rate: NO_RAG 25%; RAG k=3 87.5%, k=5 87.5%, k=8 83.3%.
- ctxlib cost: NO_RAG 15,859 tokens/kill; RAG 2,246 tokens/kill.

**Finding (honest):** RAG helps ONLY when the fact needed lives elsewhere in the codebase. Verified
(project audit clean; kills are two-sided: pass on original AND fail on mutant).

## Integrity constraints — DO NOT VIOLATE (CLAUDE.md invariants #7, #9)
- The UI shows only real pipeline output; never hardcode numbers.
- Report results honestly incl. nulls/ties. `ctxlib` is **synthetic** and purpose-built to need
  context — this is disclosed in the paper's Threats section; keep it disclosed. The 7B model
  (not Claude) is a disclosed threat. **Do NOT p-hack or engineer results to make RAG "win"**; the
  tie and floor are what make the win credible.

## Known hazards / gotchas from this session
- **mutmut 3.6.0 is BROKEN** in this pipeline (`module1_mutation/mutant_normalizer.py`
  `_parse_survivors`): its `results` output changed to a flat `name: status` list, and with
  `source_paths=["."]` on a flat subject it also mutates the test file and mis-maps coverage
  ("no tests"). ALL runs used `--skip-mutmut`, so the **syntactic mutant class is currently MISSING**
  from results. Fixing this parser (and source_paths for flat subjects) would add the 4th class.
- Windows Python 3.12 runs the frontend (flask installed). **Restart** `python -m frontend.app`
  (port 5001) after code changes — Flask doesn't auto-reload. Screenshot tools time out on the
  animated pages; inject `*{animation:none!important}` via JS before capturing, or just view live.
- WSL `/tmp` is wiped when the WSL distro restarts — log long runs to `~/codekong`, not `/tmp`.
- Detached WSL background processes die when the launching command returns; use the Bash tool's
  `run_in_background` (keeps WSL alive + notifies) or `setsid`. A long overnight run got killed
  when the previous session ended, so don't tie multi-hour runs to the session lifetime.
- `config.yaml` and `subjects/ctxlib` now exist in BOTH Windows and WSL (they were WSL-only, synced).
  The RAG fixes are in both too. If you change code, keep Windows and WSL `~/codekong` in sync.

## How to run things
- Smoke (must print 9/9): `python tests/smoke_all.py`
- Frontend: `python -m frontend.app` → http://localhost:5001
- Pipeline (in WSL): `wsl` then `cd ~/codekong && source venv/bin/activate &&
  python run_pipeline.py --repo ctxlib --skip-mutmut --limit 25` (Ollama must be running:
  `ollama serve`; model `qwen2.5-coder:7b` is pulled in WSL).
- Inspect the RAG index: `chromadb.PersistentClient` at `module2_rag/chroma_db`, collections
  `codekong_<subject>`.

## Open work (prioritized)
1. Push to GitHub (see Git state above) — user's immediate need.
2. Fix the mutmut 3.6 integration to add the syntactic mutant class (real bug).
3. For publishability: replicate the RAG effect on a **real** codebase with genuine cross-module
   dependencies (ctxlib is synthetic); scale N for inferential stats. Paper's Future Work says this.
4. Paper: fill author names/affiliations; verify newer-citation venue/years.
5. Update CLAUDE.md's stale "Current state" section.

_Confirm you've read this, then ask the user what they want to tackle first._
