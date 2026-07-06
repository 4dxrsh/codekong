"""Validation Agent — structured PASS/FAIL, never a bare bool.

A generated test is only a kill if BOTH:
  1. it PASSES against the original, unmutated code (otherwise the test is
     invalid — it fails for reasons unrelated to the mutant), AND
  2. it FAILS against the mutated code (otherwise the mutant survived it).

The returned dict carries which stage failed, the failing assertion extracted
from pytest output, and a human-readable reason — exactly the feedback the
Test Generation Agent injects into its single retry.
"""
from __future__ import annotations

import re
from pathlib import Path

from core.testexec import MutantApplier, run_tests

_ASSERT_RE = re.compile(r"^E\s+(.*)$", re.MULTILINE)
_FAILLINE_RE = re.compile(r"^(FAILED|ERROR)\s+(.*)$", re.MULTILINE)


def _extract_failure(output: str) -> str:
    asserts = _ASSERT_RE.findall(output)
    faillines = _FAILLINE_RE.findall(output)
    parts = []
    if asserts:
        parts.append("Failing assertion(s): " + " | ".join(a.strip() for a in asserts[:5]))
    if faillines:
        parts.append("pytest: " + " | ".join(f"{a} {b}".strip() for a, b in faillines[:3]))
    return "; ".join(parts) if parts else output.strip()[-500:]


def validate(scratch_repo: Path, mutant: dict, test_code: str,
             test_filename: str, timeout: int = 10) -> dict:
    """Write test into the scratch repo root, run both stages, clean up."""
    test_path = Path(scratch_repo) / test_filename
    test_path.write_text(test_code, encoding="utf-8")
    result = {"mutant_id": mutant["mutant_id"], "stage": None, "status": None,
              "reason": None, "failing_assertion": None,
              "original_run_passed": None, "mutant_run_failed": None}
    try:
        # Stage 1: against ORIGINAL code — must PASS.
        orig = run_tests(test_filename, cwd=scratch_repo, timeout=timeout)
        result["original_run_passed"] = orig.passed
        if orig.timed_out:
            result.update(stage="original", status="FAIL",
                          reason="Test timed out against the ORIGINAL code — "
                                 "the test itself hangs.",
                          failing_assertion="TIMEOUT")
            return result
        if not orig.passed:
            fa = _extract_failure(orig.tail())
            result.update(stage="original", status="FAIL",
                          reason="Test FAILS against the original, correct "
                                 "code, so it is invalid. It must pass on the "
                                 "original implementation. " + fa,
                          failing_assertion=fa)
            return result

        # Stage 2: against MUTATED code — must FAIL.
        with MutantApplier(scratch_repo, mutant):
            mut = run_tests(test_filename, cwd=scratch_repo, timeout=timeout)
        if mut.timed_out:
            # Mutant made the code hang and the timeout killed it: a kill.
            result.update(stage="mutant", status="PASS", mutant_run_failed=True,
                          reason="Mutant caused a timeout under the generated "
                                 "test — counted as KILLED.")
            return result
        result["mutant_run_failed"] = not mut.passed
        if mut.passed:
            result.update(stage="mutant", status="FAIL",
                          reason="Test passes on BOTH original and mutant — it "
                                 "does not exercise the mutated behavior. "
                                 "Target inputs where the diff changes the "
                                 "output.",
                          failing_assertion=None)
            return result
        fa = _extract_failure(mut.tail())
        result.update(stage="mutant", status="PASS", failing_assertion=fa,
                      reason="Test passes on original and fails on mutant: "
                             "mutant KILLED.")
        return result
    finally:
        test_path.unlink(missing_ok=True)
