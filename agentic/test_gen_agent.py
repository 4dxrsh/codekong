"""Test Generation Agent — owns the one-retry refinement loop.

Flow per mutant:
  1. Build class-specific prompt (module3_llm.llm_rewriter), condition-aware:
     NO_RAG gets no context section, RAG gets retrieved chunks.
  2. Generate test (temperature 0, ollama_client retries once on non-Python).
  3. Validate structurally (validation_agent): must pass on original, fail on
     mutant.
  4. If validation FAILS: exactly ONE retry, with the validator's structured
     feedback appended to the prompt. A second failure is recorded as-is.

Result statuses:
  KILLED       — a generated test passed on original and failed on mutant
  SURVIVED     — test(s) valid or invalid, but mutant never killed
  INVALID_TEST — no generated test even passed on the original code
  GEN_FAILED   — the model never produced parseable Python (2 client attempts
                 x up to 2 loop attempts)
"""
from __future__ import annotations

import time
from pathlib import Path

from core.config import resolve
from module1_mutation.mutation_runner import SCRATCH_ROOT, make_scratch_copy
from module3_llm import llm_rewriter
from agentic import validation_agent

_MAX_EXISTING_TEST_CHARS = 4000


def _existing_tests_text(scratch_repo: Path, mutant: dict) -> str:
    p = scratch_repo / mutant["existing_test_file"]
    if p.is_file():
        text = p.read_text(encoding="utf-8")
        return (text[:_MAX_EXISTING_TEST_CHARS] + "\n# …truncated"
                if len(text) > _MAX_EXISTING_TEST_CHARS else text)
    return ("(tests are doctests embedded in the function docstrings shown "
            "above)")


def _ensure_scratch(cfg: dict, subject_key: str) -> Path:
    scratch = SCRATCH_ROOT / subject_key
    if not scratch.exists():
        pinned = Path(cfg["_project_root"]) / cfg["subjects"][subject_key]["path"]
        scratch = make_scratch_copy(pinned, subject_key)
    return scratch


def generate_and_validate(cfg: dict, subject_key: str, mutant: dict,
                          context_chunks: list[dict] | None, condition: str,
                          client, k: int | None = None) -> dict:
    scratch = _ensure_scratch(cfg, subject_key)
    subdir = cfg["subjects"][subject_key].get("subdir", "")
    timeout = cfg["mutation"]["test_timeout_seconds"]
    max_retries = cfg["agentic"]["max_retries"]
    existing = _existing_tests_text(scratch, mutant)

    record = {"mutant_id": mutant["mutant_id"],
              "mutation_class": mutant["mutation_class"],
              "condition": condition, "k": k, "subject": subject_key,
              "status": None, "attempts": 0, "retry_used": False,
              "valid_test_produced": False, "validation": [],
              "wall_seconds": None, "test_file": None,
              # Additive: retrieved-context provenance, so the RAG claim is
              # inspectable per mutant (UI RAG panel) rather than asserted.
              "context_chunks": [
                  {"id": c.get("id"),
                   "file": c.get("metadata", {}).get("file"),
                   "qualname": c.get("metadata", {}).get("qualname"),
                   "kind": c.get("metadata", {}).get("kind"),
                   "distance": c.get("distance"),
                   "snippet": (c.get("document") or "")[:400]}
                  for c in (context_chunks or [])]}
    t0 = time.time()
    feedback = None

    for attempt in range(1 + max_retries):
        record["attempts"] = attempt + 1
        record["retry_used"] = attempt > 0
        test_code = llm_rewriter.rewrite_test(client, mutant, existing,
                                              context_chunks, subdir,
                                              feedback=feedback)
        if test_code is None:
            record["validation"].append({"attempt": attempt + 1,
                                         "status": "GEN_FAILED",
                                         "reason": "model produced no "
                                                   "parseable Python"})
            feedback = ("Your previous reply was not valid Python source. "
                        "Output only a runnable pytest file.")
            continue

        fname = f"test_codekong_{mutant['mutant_id']}_{condition.lower()}.py"
        v = validation_agent.validate(scratch, mutant, test_code, fname,
                                      timeout=timeout)
        v["attempt"] = attempt + 1
        record["validation"].append(v)
        if v["original_run_passed"]:
            record["valid_test_produced"] = True

        # Persist every generated test for auditability.
        outdir = resolve(cfg, cfg["output"]["generated_tests_dir"])
        outdir.mkdir(parents=True, exist_ok=True)
        tpath = outdir / f"{mutant['mutant_id']}_{condition}_a{attempt + 1}.py"
        tpath.write_text(test_code, encoding="utf-8")
        record["test_file"] = str(tpath)

        if v["status"] == "PASS":
            record["status"] = "KILLED"
            break
        feedback = v["reason"]
    else:
        if not record["validation"]:
            record["status"] = "GEN_FAILED"
        elif all(x.get("status") == "GEN_FAILED" for x in record["validation"]):
            record["status"] = "GEN_FAILED"
        elif record["valid_test_produced"]:
            record["status"] = "SURVIVED"
        else:
            record["status"] = "INVALID_TEST"

    record["wall_seconds"] = round(time.time() - t0, 2)
    return record
