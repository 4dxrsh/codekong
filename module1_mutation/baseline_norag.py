"""NO_RAG condition driver — the MuTAP-style closed-book baseline.

The LLM sees ONLY the mutant diff and the original test material; no
retrieved repository context. Everything else (model, temperature 0, prompt
template skeleton, one-retry refinement, validation) is IDENTICAL to the RAG
condition, so the measured delta is attributable to retrieved context alone.
"""
from __future__ import annotations

import json
from pathlib import Path

from core import schema
from core.config import load_config, resolve


def run_norag_condition(cfg: dict, subject_key: str, client,
                        mutants_path: Path | None = None,
                        limit: int | None = None) -> list[dict]:
    # Imported here (not at module top) to keep module1 importable without the
    # agentic layer, e.g. during Phase 1 smoke tests.
    from agentic.test_gen_agent import generate_and_validate

    mutants = schema.load_mutants(
        mutants_path or resolve(cfg, cfg["output"]["surviving_mutants"]))
    if limit:
        mutants = mutants[:limit]

    results = []
    for m in mutants:
        r = generate_and_validate(cfg, subject_key, m, context_chunks=None,
                                  condition="NO_RAG", client=client)
        results.append(r)
        print(f"[norag] {m['mutant_id']}: {r['status']}")

    out = resolve(cfg, cfg["output"]["results_dir"]) / f"norag_{subject_key}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"[norag] wrote {len(results)} results to {out}")
    return results


if __name__ == "__main__":
    import argparse
    from module3_llm.ollama_client import OllamaClient

    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    cfg = load_config()
    run_norag_condition(cfg, args.repo, OllamaClient(cfg), limit=args.limit)
