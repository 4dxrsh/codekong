"""Mutation Generation Agent — wraps Module 1.

Input : config + subject key
Output: module1_mutation/surviving_mutants.json (the shared JSON handoff)
"""
from __future__ import annotations

from pathlib import Path

from core.config import resolve
from module1_mutation.mutant_normalizer import build_surviving_mutants


def run(cfg: dict, subject_key: str, client,
        skip_mutmut: bool = False, skip_semantic: bool = False) -> Path:
    out = resolve(cfg, cfg["output"]["surviving_mutants"])
    build_surviving_mutants(cfg, subject_key, client, out,
                            skip_mutmut=skip_mutmut,
                            skip_semantic=skip_semantic)
    return out
