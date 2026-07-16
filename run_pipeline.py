"""CodeKong — single entry point.

    python run_pipeline.py --repo sorts                 # full pipeline
    python run_pipeline.py --repo sorts --phase mutate  # one phase
    python run_pipeline.py --repo schedule --k 3 5 8 --limit 20

Phases: mutate -> index -> generate (both conditions, retrieval inside the
RAG arm per k) -> evaluate. Runs one subject repo at a time, per the design.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from core import schema
from core.config import load_config, resolve
from core.guards import assert_fork_capable_linux, assert_not_windows_mount
from core.hardware import recommend_model


def phase_mutate(cfg, args, client):
    from agentic import mutation_agent
    assert_fork_capable_linux()
    out = mutation_agent.run(cfg, args.repo, client,
                             skip_mutmut=args.skip_mutmut,
                             skip_semantic=args.skip_semantic)
    print(f"[pipeline] surviving mutants at {out}")


def phase_index(cfg, args):
    from agentic import knowledge_agent
    knowledge_agent.run(cfg, args.repo)


def phase_generate(cfg, args, client):
    from agentic import retrieval_agent
    from agentic.test_gen_agent import generate_and_validate
    from module2_rag.retriever import Retriever
    from module4_eval.metrics_logger import log_metrics
    from module4_eval.validator import audit_results
    from module4_eval.checkpoint import Checkpoint

    mutants = schema.load_mutants(resolve(cfg, cfg["output"]["surviving_mutants"]))
    if args.limit and args.limit < len(mutants):
        # Deterministic random sample, NOT mutants[:limit]: the head of the
        # list is alphabetical by file, so small probes used to land entirely
        # on one file's worst-case code (e.g. external_sort's I/O classes)
        # and measure the subject's pathology instead of the model.
        import random
        mutants = random.Random(42).sample(mutants, args.limit)
    print(f"[pipeline] generating tests for {len(mutants)} mutants")

    # Crash-safe checkpoint: each result is streamed to an append-only side-file
    # and a rerun of the SAME command resumes, skipping finished work. Vital for
    # the overnight run on a machine without Claude Code to babysit it.
    results_dir = resolve(cfg, cfg["output"]["results_dir"])
    ck = Checkpoint(results_dir / f"_checkpoint_{args.repo}.jsonl")
    all_results = ck.load()
    if all_results:
        print(f"[pipeline] resuming from {ck.path.name}: "
              f"{len(all_results)} results already recorded")
    conditions = (["NO_RAG", "RAG"] if args.conditions == "both"
                  else [args.conditions])

    if "NO_RAG" in conditions:
        for m in mutants:
            if ck.is_done(m["mutant_id"], "NO_RAG", None):
                continue
            r = generate_and_validate(cfg, args.repo, m, None, "NO_RAG", client)
            print(f"[NO_RAG] {m['mutant_id']}: {r['status']}")
            ck.record(r)
            all_results.append(r)

    if "RAG" in conditions:
        ks = args.k or cfg["rag"]["k_values"]
        retriever = Retriever(cfg, args.repo)
        for k in ks:
            # Persist the retrieval handoff for auditability (JSON file
            # protocol between Retrieval Agent and Test Generation Agent).
            retrieval_agent.run(cfg, args.repo, k=k)
            for m in mutants:
                if ck.is_done(m["mutant_id"], "RAG", k):
                    continue
                chunks = retriever.retrieve(m, k)
                r = generate_and_validate(cfg, args.repo, m, chunks, "RAG",
                                          client, k=k)
                print(f"[RAG k={k}] {m['mutant_id']}: {r['status']}")
                ck.record(r)
                all_results.append(r)

    tag = f"{args.repo}"
    log_metrics(cfg, all_results, tag)
    audit_results(all_results)
    raw = results_dir / f"records_{tag}.json"
    raw.write_text(json.dumps(all_results, indent=2), encoding="utf-8")
    ck.clear()  # consolidated into records_<tag>.json — drop the side-file


def phase_evaluate(cfg, args):
    from module4_eval import compare_conditions
    compare_conditions.main(cfg)


def main():
    ap = argparse.ArgumentParser(description="CodeKong pipeline")
    ap.add_argument("--repo", required=True, help="subject key from config.yaml")
    ap.add_argument("--phase", default="all",
                    choices=["all", "mutate", "index", "generate", "evaluate"])
    ap.add_argument("--conditions", default="both",
                    choices=["both", "RAG", "NO_RAG"])
    ap.add_argument("--k", type=int, nargs="*", default=None)
    ap.add_argument("--limit", type=int, default=None,
                    help="cap number of mutants (smoke runs)")
    ap.add_argument("--skip-mutmut", action="store_true")
    ap.add_argument("--skip-semantic", action="store_true")
    args = ap.parse_args()

    cfg = load_config()
    assert_not_windows_mount(cfg["_project_root"])
    if args.repo not in cfg["subjects"]:
        sys.exit(f"unknown --repo {args.repo!r}; configured: "
                 f"{list(cfg['subjects'])}")
    pinned = Path(cfg["_project_root"]) / cfg["subjects"][args.repo]["path"]
    if not pinned.exists():
        sys.exit(f"subject repo missing at {pinned} — run ./setup.sh first")

    hw = recommend_model()
    print(f"[pipeline] hardware probe: {json.dumps(hw)}")
    if hw["recommended_model"] != cfg["llm"]["model"]:
        print(f"[pipeline] note: config model is {cfg['llm']['model']}, probe "
              f"suggests {hw['recommended_model']} — config wins.")

    client = None
    if args.phase in ("all", "mutate", "generate"):
        from module3_llm.ollama_client import OllamaClient
        client = OllamaClient(cfg)

    if args.phase in ("all", "mutate"):
        phase_mutate(cfg, args, client)
    if args.phase in ("all", "index"):
        phase_index(cfg, args)
    if args.phase in ("all", "generate"):
        phase_generate(cfg, args, client)
    if args.phase in ("all", "evaluate"):
        phase_evaluate(cfg, args)


if __name__ == "__main__":
    main()
