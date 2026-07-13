"""Retrieval Agent — wraps Module 2's class-aware retriever.

Input : surviving_mutants.json + k
Output: module2_rag/rag_context.json  {mutant_id: [chunk, ...]}
"""
from __future__ import annotations

import json
from pathlib import Path

from core import schema
from core.config import resolve
from module2_rag.retriever import retrieve_for_mutants


def run(cfg: dict, subject_key: str, k: int | None = None,
        mutants_path: Path | None = None) -> Path:
    k = k or cfg["rag"]["default_k"]
    mutants = schema.load_mutants(
        mutants_path or resolve(cfg, cfg["output"]["surviving_mutants"]))
    context = retrieve_for_mutants(cfg, subject_key, mutants, k)
    out = resolve(cfg, cfg["output"]["rag_context"])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"subject": subject_key, "k": k,
                               "contexts": context}, indent=2),
                   encoding="utf-8")
    print(f"[retrieval] wrote context for {len(context)} mutants (k={k}) to {out}")
    return out
