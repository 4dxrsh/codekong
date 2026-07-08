# CLAUDE.md — session handover for AI assistants working on CodeKong

You are picking up a working research project. Read this before changing
anything. README.md explains the project to humans; this file carries the
invariants, hazards, and open work an AI session needs to continue safely.

## What this is (30 seconds)

A mutation-testing research pipeline testing one hypothesis: giving an LLM
retrieved context from the codebase under test (RAG) produces test rewrites
that kill more surviving mutants than closed-book generation (NO_RAG,
MuTAP-style) — and the benefit should grow with mutant difficulty
(syntactic < sdl/semantic < higher_order). Four RQs: RQ1 RAG-vs-NO_RAG
overall; RQ2 per-class hardness gradient; RQ3 retrieval depth k (3/5/8);
RQ4 tokens-per-kill cost. Everything is free and local (Ollama, ChromaDB,
sentence-transformers); the Anthropic/OpenAI SDKs are BANNED from this
codebase by design — that substitution is documented in
paper/codekong_notes.md as a threat to validity.

## Architecture map (dataflow order)

    core/                 config loader, platform guards, hardware probe,
                          mutant schema, MutantApplier + run_tests
    module1_mutation/     four mutant sources -> mutant_normalizer merges to
                          one schema -> survival-filtered surviving_mutants.json
    module2_rag/          AST-walk -> embeddings -> ChromaDB; class-aware retriever
    module3_llm/          ollama_client.py (THE only model touchpoint),
                          4 class-specific prompt templates, llm_rewriter
    agentic/              5 agents; test_gen_agent owns the ONE-retry loop;
                          validation_agent returns structured verdicts
    module4_eval/         metrics, RAG-vs-NO_RAG comparison, figures, audits
    run_pipeline.py       research entry point (per subject repo, from config)
    generate_tests.py     user-facing single-file flow (used by the web UI)
    frontend/             Flask UI; data.py is flask-free and unit-testable
    tests/smoke_all.py    offline test suite — MUST stay green (9/9)

## Invariants — do not break these

1. ollama_client.py is the single place that talks to any model. Provider &
   model come from config.yaml, never code.
2. Temperature 0.0 for ALL test generation; 0.7 for semantic mutant
   generation. Determinism is a design requirement.
3. A kill requires BOTH: test passes on original code AND fails on mutant.
   Never weaken this.
4. Exactly ONE retry per mutant, driven by structured validator feedback.
5. Every mutant carries the full schema (core/schema.py REQUIRED_FIELDS) and
   ast.parse-validates before saving.
6. progress= and on_event= in generate_tests_for_file are ADDITIVE no-op
   hooks. UI reads them; pipeline behavior must never depend on them.
7. The UI shows only real pipeline output. No placeholder numbers, ever —
   missing data renders explicit empty states.
8. User uploads write to generated_test_suites/mutants_<key>.json — NEVER to
   the shared module1_mutation/surviving_mutants.json (experiment data).
9. Report results honestly, including nulls. An inconclusive RQ2 gradient is
   a finding. Suspiciously good numbers mean check the validator first
   (module4_eval/validator.py audits this).

## Hazards we already hit — don't rediscover them

- In-place mutation + bytecode cache: a same-size source rewrite can make a
  stale __pycache__ entry look valid and silently run PRE-mutation code.
  MutantApplier purges caches and run_tests uses -B. Related: never run the
  pipeline from /mnt/<drive> in WSL (guard enforces) or an iCloud-synced dir.
- mutmut 3.x: config is [tool.mutmut] source_paths= / 
  pytest_add_cli_args_test_selection= (NOT paths_to_mutate); state in
  mutants/; needs fork() -> Linux/WSL2/macOS only (core/guards.py).
- Flask autoescape: the layout injects page HTML via {{ body|safe }} — if
  you touch templates, render-test them (see tests in git history) or the
  site shows escaped raw HTML.
- Method mutants need CLASS imports ('from mod import FilesArray'), not
  'from mod import __init__' (llm_rewriter.make_import_hint).
- --limit sampling is a seeded random sample; the alphabetical head of
  surviving_mutants.json is dominated by pathological I/O-heavy files.
- Ollama: local server, no key. Model 404 usually means the running server's
  model store doesn't have the pull (systemd service vs manual `ollama
  serve` use different stores). Cloud fallback exists but is rate-limited —
  documented exception only.

## Working norms for this repo

- After ANY change: python tests/smoke_all.py must print 9/9. Add checks
  there for new subsystems.
- Show real command output when verifying; never describe expected behavior
  as if observed. If a number looks too good, suspect a bug.
- Keep module boundaries: new features orchestrate existing modules (see
  generate_tests.py as the pattern), don't fork their logic.

## Current state / open work (update this section as you go)

- Model-tier question OPEN: qwen2.5-coder:7b on the original 4GB-VRAM laptop
  had not yet demonstrated kills at last update. Capability probe:
  `python generate_tests.py --file demo_range_utils.py --description
  "numeric utilities" --limit 8 --skip-semantic` (kills>0 = model OK), then
  `python run_pipeline.py --repo sorts --phase generate --limit 25`.
  If demo-file kills are zero, move config.yaml to qwen2.5-coder:14b.
- Full research runs (both subjects, both conditions, k sweep) not yet
  executed -> Research Questions page shows empty states until then.
- frontend/app.py ABOUT template has placeholder sections (marked # EDIT
  HERE) awaiting real team/course details.
- Demo mode timing (DEMO_LIMIT=5, DEMO_K=3 in frontend/app.py) assumes
  ~5 min on the original hardware — dry-run and tune per machine.
- Optional: a third subject repo (small, pure-Python, well-tested) may be
  added to config.yaml subjects; verify it clones before committing to it.

## Setup pointers

WSL2/Windows: README.md "Setting up WSL2 from zero". macOS: MACBOOK_SETUP.md.
Both end in `bash setup.sh`. Web UI: `python -m frontend.app` -> :5001.
