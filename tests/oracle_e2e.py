"""Oracle end-to-end verification.

Replaces the LLM with a 'perfect model': for each REAL mutant of the demo
file, it executes the original and mutated module side by side, searches a
small input grid for behavioral divergence, and emits a test asserting the
ORIGINAL behavior at the divergent inputs. Those tests then flow through the
REAL pipeline path (generate_and_validate -> MutantApplier file swaps ->
subprocess test runs -> two-stage validation -> metrics).

What a PASS here proves: mutant generation, survival filtering, mutant
application, validation semantics, retry loop, curation, and metrics can and
do produce nonzero kill rates when the model's tests are behaviorally
correct. What it deliberately does NOT prove: that any particular local LLM
writes such tests — that is hardware/model-dependent and must be probed on
the target machine (see CLAUDE.md, open work).

Run:  python tests/oracle_e2e.py       (uses pytest if present, else a
                                        built-in lite runner)
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DEMO = ROOT / "demo_range_utils.py"

# Input grids per demo-file function (module-level names only).
GRIDS = {
    "clamp": [(x, 0, 5) for x in range(-3, 9)] + [(7, 2, 2), (-1, -5, -2)],
    "lerp": [(0, 10, t) for t in (-0.5, 0.0, 0.25, 0.5, 1.0, 1.5)]
            + [(5, -5, 0.5)],
    "letter_grade": [(s,) for s in (0, 55, 59, 60, 61, 69, 70, 71, 79, 80,
                                    81, 89, 90, 91, 100)],
    "running_total": [([1, 2, 3],), ([5],), ([-1, 1, -1],), ([],),
                      ([2, 2, 2, 2],)],
}


def _exec_module(src: str) -> dict:
    ns: dict = {}
    exec(src, ns)
    return ns


def divergent_inputs(module_src: str, mutant: dict, max_hits: int = 3):
    """Real behavioral diff: run original vs mutated module, return inputs
    where outputs (or exceptions) differ."""
    func = mutant["function"]
    if "." in func or func not in GRIDS:
        return None  # methods / unknown functions: out of oracle scope
    mut_src = module_src.replace(mutant["original_code"],
                                 mutant["mutated_code"], 1)
    try:
        orig_ns, mut_ns = _exec_module(module_src), _exec_module(mut_src)
    except Exception:
        return []
    hits = []
    for args in GRIDS[func]:
        def call(ns):
            try:
                return ("ok", ns[func](*[list(a) if isinstance(a, list) else a
                                         for a in args]))
            except Exception as exc:
                return ("exc", type(exc).__name__)
        o, m = call(orig_ns), call(mut_ns)
        if o != m and o[0] == "ok":
            hits.append((args, o[1]))
            if len(hits) >= max_hits:
                break
    return hits


def oracle_test_code(module_name: str, func: str, hits) -> str:
    lines = [f"from {module_name} import {func}", "", "def test_oracle():"]
    for args, expected in hits:
        argrepr = ", ".join(repr(a) for a in args)
        lines.append(f"    assert {func}({argrepr}) == {expected!r}")
    return "\n".join(lines) + "\n"


class OracleClient:
    """Stands in for OllamaClient: 'writes' the behaviorally-derived test."""
    temp_testgen = 0.0

    def __init__(self, test_code: str):
        self.test_code = test_code
        self.calls_made = 0

    def generate_python(self, *a, **kw):
        self.calls_made += 1
        return self.test_code


def main() -> int:
    module_src = DEMO.read_text(encoding="utf-8")

    # Optional lite runner when pytest is unavailable (sandbox environments).
    try:
        import pytest  # noqa: F401
        lite = False
    except ImportError:
        lite = True
        sys.path.insert(0, str(ROOT / "tests"))
        from smoke_all import _pytest_lite
        from agentic import validation_agent
        import module1_mutation.mutation_runner as mr
        validation_agent.run_tests = _pytest_lite
        mr.run_tests = _pytest_lite

    import module1_mutation.mutation_runner as mr
    import agentic.test_gen_agent as tga
    td = Path(tempfile.mkdtemp())
    mr.SCRATCH_ROOT = td / "_scratch"
    tga.SCRATCH_ROOT = td / "_scratch"

    from core.config import load_config
    from generate_tests import scaffold_subject
    from module1_mutation.mutant_normalizer import build_surviving_mutants
    from agentic.test_gen_agent import generate_and_validate
    from module4_eval.metrics_logger import results_to_frame, summarize

    cfg = load_config()
    key = scaffold_subject(cfg, DEMO, "numeric utilities (oracle e2e)")
    out = td / "mutants.json"
    mutants = build_surviving_mutants(cfg, key, client=None, out_path=out,
                                      skip_mutmut=True, skip_semantic=True)

    records, expected_kills, unkillable = [], 0, 0
    for m in mutants:
        hits = divergent_inputs(module_src, m)
        if hits is None:
            continue
        if not hits:
            unkillable += 1  # no divergence on grid: equivalent-ish mutant
            continue
        expected_kills += 1
        code = oracle_test_code(DEMO.stem, m["function"], hits)
        rec = generate_and_validate(cfg, key, m, None, "NO_RAG",
                                    OracleClient(code))
        records.append(rec)
        print(f"  {m['mutant_id']}: {rec['status']} "
              f"(divergent inputs: {len(hits)})")

    killed = sum(1 for r in records if r["status"] == "KILLED")
    df = summarize(results_to_frame(records))
    print(df.to_string(index=False))
    print(f"\noracle verdict: {killed}/{expected_kills} behaviorally-killable "
          f"mutants KILLED through the real pipeline; {unkillable} had no "
          f"divergence on the input grid (unkillable by these inputs — "
          f"correctly not counted).")

    # cleanup scaffold artifacts
    shutil.rmtree(ROOT / "subjects" / key, ignore_errors=True)
    gts = ROOT / "generated_test_suites"
    if gts.exists():
        for p in gts.glob(f"*{key}*"):
            p.unlink(missing_ok=True)

    if killed != expected_kills:
        print("ORACLE E2E: FAIL — the pipeline dropped kills a perfect model "
              "should have scored. Investigate before blaming the LLM.")
        return 1
    if killed == 0:
        print("ORACLE E2E: INCONCLUSIVE — no killable mutants found; widen "
              "the input grids.")
        return 1
    kr = df[df["condition"] == "NO_RAG"]["kill_rate"]
    assert float(kr.iloc[0]) > 0, "metrics reported 0.0 despite kills — bug"
    print("ORACLE E2E: PASS — pipeline provably produces nonzero kill rates "
          "with behaviorally-correct tests; metrics report them correctly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
