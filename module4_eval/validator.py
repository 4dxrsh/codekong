"""Result-level sanity validation.

Distinct from agentic/validation_agent.py (which judges one test against one
mutant). This module audits whole result sets before they are reported,
because a number that looks too good is more often a validator bug than a
discovery — e.g. a 100% kill rate on higher-order mutants is a red flag, not
a headline.
"""
from __future__ import annotations

import sys

SUSPICIOUS_KILL_RATE = 0.95
SUSPICIOUS_MIN_N = 5


def audit_results(results: list[dict]) -> list[str]:
    warnings: list[str] = []
    by_class: dict[str, list[dict]] = {}
    for r in results:
        by_class.setdefault(r["mutation_class"], []).append(r)

    for mc, rs in sorted(by_class.items()):
        n = len(rs)
        kills = sum(1 for r in rs if r["status"] == "KILLED")
        if n >= SUSPICIOUS_MIN_N and kills / n >= SUSPICIOUS_KILL_RATE:
            warnings.append(
                f"SUSPICIOUS: kill rate {kills}/{n} for class '{mc}' — check "
                "the validator before reporting this (is stage 2 actually "
                "applying the mutant?).")
        gen_failed = sum(1 for r in rs if r["status"] == "GEN_FAILED")
        if n and gen_failed / n > 0.5:
            warnings.append(
                f"MODEL TOO WEAK? {gen_failed}/{n} generations for class "
                f"'{mc}' never produced parseable Python. The configured "
                "model tier likely needs to go up before the RAG-vs-NO_RAG "
                "comparison means anything.")

    for r in results:
        for v in r.get("validation", []):
            if (v.get("status") == "PASS" and v.get("stage") == "mutant"
                    and v.get("original_run_passed") is not True):
                warnings.append(
                    f"BUG: {r['mutant_id']} recorded a kill without a "
                    "passing original-code run. Validator logic error.")

    for w in warnings:
        print(f"[audit] {w}", file=sys.stderr)
    if not warnings:
        print("[audit] no anomalies detected")
    return warnings
