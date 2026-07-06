"""Offline smoke suite — exercises every code path that doesn't need mutmut,
Ollama, chromadb, or network. Run from the repo root:

    python tests/smoke_all.py

Also pytest-compatible (each check is a test_* function).
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import textwrap
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

BUBBLE = textwrap.dedent('''\
    def bubble_sort(collection):
        """Sort a list.

        >>> bubble_sort([3, 1, 2])
        [1, 2, 3]
        """
        length = len(collection)
        for i in range(length - 1):
            swapped = False
            for j in range(length - 1 - i):
                if collection[j] > collection[j + 1]:
                    swapped = True
                    collection[j], collection[j + 1] = collection[j + 1], collection[j]
            if not swapped:
                break
        return collection
    ''')


# ---------------------------------------------------------------- SDL
def test_sdl_generator():
    from module1_mutation.sdl_generator import sdl_mutants_for_function
    import ast
    muts = sdl_mutants_for_function(BUBBLE, max_per_function=10)
    assert muts, "SDL produced no mutants for bubble_sort"
    for m in muts:
        ast.parse(m["mutated_code"])                       # all parse
        assert m["mutated_code"].strip() != BUBBLE.strip() # all differ
        assert '"""' in m["mutated_code"]                  # docstring never deleted
    print(f"  sdl: {len(muts)} mutants; first deletes: "
          f"{muts[0]['deleted_statement'].strip()!r}")


# ---------------------------------------------------------------- HOM
def test_hom_combiner():
    from module1_mutation.hom_combiner import combine_pair, generate_homs
    a = BUBBLE.replace("collection[j] > collection[j + 1]",
                       "collection[j] >= collection[j + 1]")
    b = BUBBLE.replace("range(length - 1)", "range(length)")
    combined = combine_pair(BUBBLE, a, b)
    assert combined and ">=" in combined and "range(length)" in combined

    def fo(mid, mut):
        return {"mutant_id": mid, "file": "sorts/bubble_sort.py",
                "function": "bubble_sort", "line": 1, "original_code": BUBBLE,
                "mutated_code": mut, "mutation_operator": "op",
                "mutation_description": f"desc {mid}"}
    homs = generate_homs([fo("m1", a), fo("m2", b)], max_per_function=3)
    assert len(homs) == 1 and homs[0]["parents"] == ["m1", "m2"]
    print(f"  hom: combined pair OK; generate_homs -> {len(homs)} HOM")


# ---------------------------------------------------------------- schema
def test_schema_roundtrip(tmpdir=None):
    from core import schema
    m = {"mutant_id": "x", "file": "f.py", "function": "g", "line": 3,
         "original_code": "def g():\n    return 1\n",
         "mutated_code": "def g():\n    return 2\n",
         "mutation_operator": "const", "mutation_source": "ast_sdl",
         "mutation_class": "sdl", "mutation_description": "d",
         "diff": "-1+2", "existing_test_file": "t.py"}
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "sm.json"
        schema.save_mutants([m], p)
        assert schema.load_mutants(p)[0]["mutant_id"] == "x"
    bad = dict(m, mutated_code="def g(:\n")
    try:
        schema.validate_mutant(bad)
        raise AssertionError("unparseable mutant accepted")
    except schema.SchemaError:
        pass
    print("  schema: roundtrip + reject-unparseable OK")


# ------------------------------------------------- mutmut results parser
def test_mutmut_results_parser():
    from module1_mutation.mutant_normalizer import _parse_survivors
    fake = textwrap.dedent("""\
        ⠇ 725/725  🎉 700  ⏰ 0  🤔 0  🙁 25  🔇 0

        Killed 🎉 (700)

        Survived 🙁 (3)
        ---- sorts/bubble_sort.py (2) ----
        sorts.bubble_sort.x_bubble_sort__mutmut_4
        sorts.bubble_sort.x_bubble_sort__mutmut_7
        ---- sorts/quick_sort.py (1) ----
        sorts.quick_sort.x_quick_sort__mutmut_2

        Skipped 🔇 (0)
        """)
    got = _parse_survivors(fake)
    assert got == ["sorts.bubble_sort.x_bubble_sort__mutmut_4",
                   "sorts.bubble_sort.x_bubble_sort__mutmut_7",
                   "sorts.quick_sort.x_quick_sort__mutmut_2"], got
    print(f"  mutmut parser: {len(got)} survivors parsed from simulated output")


# ------------------------------------------------ ollama client (REST)
class _FakeOllama(BaseHTTPRequestHandler):
    script: list[str] = []
    calls: list[dict] = []

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        type(self).calls.append(body)
        content = type(self).script.pop(0) if type(self).script else "pass"
        resp = {"message": {"role": "assistant", "content": content},
                "eval_count": 42, "prompt_eval_count": 100,
                "total_duration": 123456}
        data = json.dumps(resp).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass


def test_ollama_client_rest():
    server = HTTPServer(("127.0.0.1", 0), _FakeOllama)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    with tempfile.TemporaryDirectory() as td:
        cfg = {"_project_root": td,
               "llm": {"provider": "local", "model": "fake-model",
                       "local_host": f"http://127.0.0.1:{port}",
                       "cloud_host": "https://ollama.com",
                       "temperature_testgen": 0.0, "temperature_semantic": 0.7,
                       "request_timeout_seconds": 10,
                       "call_log": "llm_calls.jsonl"}}
        from module3_llm.ollama_client import OllamaClient
        c = OllamaClient(cfg)
        # 1) plain generate
        _FakeOllama.script = ["hello"]
        assert c.generate("s", "u", 0.0, "smoke") == "hello"
        # 2) generate_json: first reply invalid -> retry-once succeeds
        _FakeOllama.script = ["not json at all",
                              '```json\n{"a": 1}\n```']
        assert c.generate_json("s", "u") == {"a": 1}
        # 3) generate_python: first reply invalid -> retry-once succeeds
        _FakeOllama.script = ["def broken(:", "```python\ndef ok():\n    return 1\n```"]
        assert "def ok" in c.generate_python("s", "u")
        # temperature routed into options
        assert _FakeOllama.calls[-1]["options"]["temperature"] == 0.0
        assert _FakeOllama.calls[1]["options"]["temperature"] == 0.7
        # JSONL log written with token metadata
        log = Path(td) / "llm_calls.jsonl"
        lines = [json.loads(l) for l in log.read_text().splitlines()]
        assert len(lines) == 5 and lines[0]["eval_count"] == 42
        assert c.calls_made == 5
    server.shutdown()
    print(f"  ollama_client: REST path, retry-once (json+python), "
          f"temp routing, JSONL log ({len(lines)} calls) OK")


# ------------------------------------------------ rewriter prompt build
def _fake_mutant(mclass="syntactic"):
    return {"mutant_id": f"{mclass}_bubble_sort_abc123",
            "file": "sorts/bubble_sort.py", "function": "bubble_sort",
            "line": 1, "original_code": BUBBLE,
            "mutated_code": BUBBLE.replace(">", ">="),
            "mutation_operator": "op", "mutation_source": "mutmut",
            "mutation_class": mclass,
            "mutation_description": "swap > for >= | second component",
            "diff": "- if a > b\n+ if a >= b", "existing_test_file": "sorts/"}


def test_prompt_templates():
    from module3_llm import llm_rewriter
    for mc in ("syntactic", "sdl", "semantic", "higher_order"):
        p = llm_rewriter.build_prompt(_fake_mutant(mc), "existing tests here",
                                      None, "sorts")
        assert "bubble_sort" in p and "{" not in p.replace("{'", "")
        assert "Retrieved repository context" not in p     # NO_RAG: empty slot
    chunks = [{"document": "def merge_sort(): ...",
               "metadata": {"file": "sorts/merge_sort.py",
                            "qualname": "merge_sort", "kind": "function"}}]
    p = llm_rewriter.build_prompt(_fake_mutant(), "t", chunks, "sorts",
                                  feedback="previous test failed on original")
    assert "Retrieved repository context" in p and "Feedback from the previous" in p
    assert "from sorts.bubble_sort import bubble_sort" in p
    print("  prompts: all 4 templates format; RAG/NO_RAG + feedback slots OK")


# ------------------------------------- full agentic loop with mock LLM
class MockClient:
    """Scripted stand-in for OllamaClient: same generate_python surface."""
    temp_testgen = 0.0

    def __init__(self, scripted):
        self.scripted = list(scripted)
        self.calls_made = 0
        self.prompts = []

    def generate_python(self, system_prompt, user_prompt, temperature=None,
                        purpose=""):
        self.calls_made += 1
        self.prompts.append(user_prompt)
        return self.scripted.pop(0) if self.scripted else None


def _pytest_lite(test_targets, cwd, timeout=10, extra_args=None):
    """Stand-in for core.testexec.run_tests in environments without pytest:
    executes the test file and calls every test_* function."""
    import subprocess
    from core.testexec import TestRun
    target = test_targets if isinstance(test_targets, str) else test_targets[0]
    code = (f"import sys; sys.path.insert(0, {str(cwd)!r}); ns = {{}}; "
            f"exec(open({str(Path(cwd) / target)!r}).read(), ns); "
            "[v() for k, v in list(ns.items()) "
            "if k.startswith('test_') and callable(v)]")
    try:
        proc = subprocess.run([sys.executable, "-B", "-c", code], cwd=str(cwd),
                              capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return TestRun(False, True, None, "", "TIMEOUT")
    return TestRun(proc.returncode == 0, False, proc.returncode,
                   proc.stdout, proc.stderr)


def test_agentic_retry_loop():
    from agentic import validation_agent, test_gen_agent
    from module1_mutation import mutation_runner

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        mini = td / "mini_repo"
        mini.mkdir()
        (mini / "mathx.py").write_text(
            "def add(a, b):\n    return a + b\n", encoding="utf-8")
        (mini / "test_existing.py").write_text(
            "from mathx import add\n\ndef test_zero():\n    assert add(0, 0) == 0\n",
            encoding="utf-8")

        cfg = {"_project_root": str(td),
               "subjects": {"mini": {"path": "mini_repo", "subdir": "",
                                     "test_selection": ["test_existing.py"],
                                     "pytest_extra_args": []}},
               "mutation": {"test_timeout_seconds": 10},
               "agentic": {"max_retries": 1},
               "output": {"generated_tests_dir": "generated_tests"}}

        mutant = {"mutant_id": "semantic_add_deadbeef", "file": "mathx.py",
                  "function": "add", "line": 1,
                  "original_code": "def add(a, b):\n    return a + b\n",
                  "mutated_code": "def add(a, b):\n    return a - b\n",
                  "mutation_operator": "llm:swapped_op",
                  "mutation_source": "llm_semantic",
                  "mutation_class": "semantic",
                  "mutation_description": "plus became minus",
                  "diff": "- return a + b\n+ return a - b",
                  "existing_test_file": "test_existing.py"}

        # Swap in pytest-lite (sandbox has no pytest; production uses real pytest).
        real = validation_agent.run_tests
        validation_agent.run_tests = _pytest_lite
        # Point the scratch root into the tempdir.
        real_scratch = mutation_runner.SCRATCH_ROOT
        mutation_runner.SCRATCH_ROOT = td / "_scratch"
        test_gen_agent.SCRATCH_ROOT = td / "_scratch"
        try:
            # Attempt 1: passes on BOTH original and mutant (add(0,0)==0) ->
            # validator FAIL -> one retry with feedback -> killing test.
            weak = ("from mathx import add\n\n"
                    "def test_weak():\n    assert add(0, 0) == 0\n")
            strong = ("from mathx import add\n\n"
                      "def test_strong():\n    assert add(2, 3) == 5\n")
            client = MockClient([weak, strong])
            rec = test_gen_agent.generate_and_validate(
                cfg, "mini", mutant, None, "NO_RAG", client)
            assert rec["status"] == "KILLED", rec
            assert rec["attempts"] == 2 and rec["retry_used"], rec
            assert "does not exercise the mutated behavior" in client.prompts[1]
            v1, v2 = rec["validation"]
            assert v1["status"] == "FAIL" and v1["stage"] == "mutant"
            assert v2["status"] == "PASS" and v2["failing_assertion"]

            # Scenario 2: invalid test both attempts (fails on original).
            bad = ("from mathx import add\n\n"
                   "def test_bad():\n    assert add(1, 1) == 3\n")
            rec2 = test_gen_agent.generate_and_validate(
                cfg, "mini", mutant, None, "NO_RAG", MockClient([bad, bad]))
            assert rec2["status"] == "INVALID_TEST", rec2

            # Scenario 3: model never produces Python.
            rec3 = test_gen_agent.generate_and_validate(
                cfg, "mini", mutant, None, "NO_RAG", MockClient([]))
            assert rec3["status"] == "GEN_FAILED", rec3

            # Original file must be intact after all applies.
            scratch_file = td / "_scratch" / "mini" / "mathx.py"
            assert scratch_file.read_text() == mutant["original_code"]
        finally:
            validation_agent.run_tests = real
            mutation_runner.SCRATCH_ROOT = real_scratch
        print("  agentic loop: KILLED-after-retry, INVALID_TEST, GEN_FAILED, "
              "feedback injection, clean restore — all OK")
        return rec


# ------------------------------------------------ metrics + figures
def _synthetic_results():
    import random
    random.seed(7)
    out = []
    base = {"syntactic": (0.7, 0.75), "sdl": (0.55, 0.65),
            "semantic": (0.45, 0.62), "higher_order": (0.30, 0.55)}
    for mc, (p_norag, p_rag) in base.items():
        for cond, p in (("NO_RAG", p_norag), ("RAG", p_rag)):
            for k in ([None] if cond == "NO_RAG" else [3, 5, 8]):
                for i in range(20):
                    killed = random.random() < p
                    out.append({"mutant_id": f"{mc}_{i}", "subject": "sorts",
                                "condition": cond, "k": k,
                                "mutation_class": mc,
                                "status": "KILLED" if killed else "SURVIVED",
                                "valid_test_produced": killed or random.random() < 0.8,
                                "retry_used": random.random() < 0.3,
                                "wall_seconds": random.uniform(5, 40),
                                "validation": []})
    return out


def test_metrics_and_figures():
    from module4_eval.metrics_logger import results_to_frame, summarize
    from module4_eval.compare_conditions import (rag_delta_per_class,
                                                 answer_rqs, make_figures)
    from module4_eval.validator import audit_results

    results = _synthetic_results()
    df = results_to_frame(results)
    s = summarize(df)
    assert {"condition", "mutation_class", "kill_rate"} <= set(s.columns)

    with tempfile.TemporaryDirectory() as td:
        cfg = {"_project_root": td,
               "output": {"results_dir": "results", "figures_dir": "figures"}}
        delta = rag_delta_per_class(df)
        assert "rag_delta" in delta.columns
        Path(td, "results").mkdir()
        ans = answer_rqs(cfg, df)
        assert "RQ1" in ans and "RQ2" in ans
        make_figures(cfg, df)
        figs = sorted(p.name for p in Path(td, "figures").glob("*.png"))
        assert len(figs) == 4, figs
        audit_results(results)
    print(f"  metrics/figures: summary, deltas, RQ answers, 4 figures OK "
          f"({figs})")


# ------------------------------------------------ misc core
def test_core_misc():
    from core.hardware import recommend_model
    from core.guards import assert_fork_capable_linux
    from core.srcmap import extract_functions
    from core.config import load_config
    hw = recommend_model()
    assert hw["recommended_model"].startswith("qwen")
    assert_fork_capable_linux()  # sandbox is Linux; must not raise
    cfg = load_config()
    assert cfg["llm"]["provider"] == "local"
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "m.py").write_text(BUBBLE, encoding="utf-8")
        fns = extract_functions(Path(td))
        assert len(fns) == 1 and fns[0].qualname == "bubble_sort"
        assert fns[0].docstring and not fns[0].is_test
    print(f"  core: hardware={hw['recommended_model']}, guard, config, "
          "srcmap OK")


ALL = [test_sdl_generator, test_hom_combiner, test_schema_roundtrip,
       test_mutmut_results_parser, test_ollama_client_rest,
       test_prompt_templates, test_agentic_retry_loop,
       test_metrics_and_figures, test_core_misc]

if __name__ == "__main__":
    failed = 0
    for t in ALL:
        print(f"[smoke] {t.__name__}")
        try:
            t()
        except Exception as exc:  # show, count, continue
            failed += 1
            import traceback
            traceback.print_exc()
            print(f"[smoke] FAILED: {t.__name__}: {exc}")
    print(f"\n[smoke] {len(ALL) - failed}/{len(ALL)} passed")
    sys.exit(1 if failed else 0)
# end of smoke suite
