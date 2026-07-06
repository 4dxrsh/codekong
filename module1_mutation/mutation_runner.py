"""Apply a mutant to a scratch copy of the subject repo, run its existing test
suite, and classify the mutant as survived / killed / timeout_killed.

mutmut-sourced mutants are survivors by construction (mutmut already ran the
suite); this module exists to give the OTHER three sources (SDL, semantic,
HOM) the same survival semantics before they enter surviving_mutants.json.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from core.testexec import MutantApplier, run_tests

SCRATCH_ROOT = Path(__file__).resolve().parent / "_scratch"


def make_scratch_copy(pinned_repo: Path, name: str) -> Path:
    """Copy the pinned subject clone (minus .git) into a scratch dir we are
    free to mutate. Idempotent: re-copies fresh every time for isolation."""
    dst = SCRATCH_ROOT / name
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(pinned_repo, dst,
                    ignore=shutil.ignore_patterns(".git", "__pycache__",
                                                  "mutants", ".mutmut-cache"))
    return dst


def confirm_survival(scratch_repo: Path, mutant: dict,
                     test_selection: list[str], pytest_extra_args: list[str],
                     suite_timeout: int = 120) -> str:
    """Return 'survived' | 'killed' | 'timeout_killed' | 'apply_failed'.

    survived  = existing suite still passes with the mutant applied
    killed    = suite fails (the existing tests already detect this mutant,
                so it is NOT interesting for the RAG experiment)
    timeout   = mutant caused a hang; the timeout kills it (counts as killed)
    """
    try:
        with MutantApplier(scratch_repo, mutant):
            result = run_tests(test_selection, cwd=scratch_repo,
                               timeout=suite_timeout,
                               extra_args=pytest_extra_args)
            if result.timed_out:
                return "timeout_killed"
            return "survived" if result.passed else "killed"
    except RuntimeError as exc:
        print(f"[runner] apply failed: {exc}", file=sys.stderr)
        return "apply_failed"


def filter_survivors(scratch_repo: Path, mutants: list[dict],
                     test_selection: list[str], pytest_extra_args: list[str],
                     suite_timeout: int = 120) -> tuple[list[dict], dict]:
    survivors, stats = [], {"survived": 0, "killed": 0,
                            "timeout_killed": 0, "apply_failed": 0}
    for m in mutants:
        verdict = confirm_survival(scratch_repo, m, test_selection,
                                   pytest_extra_args, suite_timeout)
        stats[verdict] += 1
        if verdict == "survived":
            survivors.append(m)
        else:
            print(f"[runner] {m['mutant_id']}: {verdict}", file=sys.stderr)
    return survivors, stats
