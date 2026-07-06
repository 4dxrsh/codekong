"""Collect mutants from all four sources and normalize into the unified schema.

Sources:
  1A syntactic     — mutmut 3.x (run/results/apply, verified against current docs:
                     config lives in [tool.mutmut] with source_paths +
                     pytest_add_cli_args_test_selection; state in mutants/)
  1B sdl           — AST statement-deletion (sdl_generator.py)
  1C semantic      — LLM-generated realistic bug, via the ONE shared
                     ollama_client (temperature 0.7, capped total calls).
                     NOTE: the original design used the Anthropic SDK here;
                     Ollama is a deliberate substitution — see README
                     "Threats to validity".
  1D higher_order  — hom_combiner.py, same-function pairs, capped per function

Every semantic and HOM mutant is ast.parse-validated before saving; failures
are skipped and logged. SDL/semantic/HOM survivors are confirmed by actually
running the subject's existing suite via mutation_runner; mutmut survivors are
survivors by construction.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from core import schema
from core.guards import assert_fork_capable_linux
from core.srcmap import extract_functions
from module1_mutation.sdl_generator import sdl_mutants_for_function
from module1_mutation.hom_combiner import generate_homs
from module1_mutation import mutation_runner

_MUTANT_NAME_RE = re.compile(r"[A-Za-z_][\w.\[\]<>-]*__mutmut_\d+")


# ---------------------------------------------------------------- 1A: mutmut
def _write_mutmut_config(scratch: Path, subdir: str, test_selection: list[str],
                         pytest_extra_args: list[str]) -> None:
    """Append a [tool.mutmut] section to the scratch repo's pyproject.toml
    (creating the file if absent). mutmut 3 pyproject config requires arrays."""
    pyproject = scratch / "pyproject.toml"
    existing = pyproject.read_text(encoding="utf-8") if pyproject.exists() else ""
    if "[tool.mutmut]" in existing:
        return  # respect repo's own config rather than corrupting the file
    def arr(xs): return "[" + ", ".join(f'"{x}"' for x in xs) + "]"
    section = (
        "\n[tool.mutmut]\n"
        f"source_paths = {arr([subdir + '/' if subdir else '.'])}\n"
        f"pytest_add_cli_args_test_selection = {arr(test_selection)}\n"
    )
    if pytest_extra_args:
        section += f"pytest_add_cli_args = {arr(pytest_extra_args)}\n"
    pyproject.write_text(existing + section, encoding="utf-8")


def _parse_survivors(results_output: str) -> list[str]:
    """Parse `mutmut results` output for surviving mutant names.

    Defensive by design: mutmut's human-readable output has changed across
    versions. We track the current status section by keyword and harvest
    anything shaped like a mutant name (…__mutmut_N) inside the survived
    section. If sectioning isn't recognizable at all, we fail loudly with the
    raw output rather than silently returning zero survivors.
    """
    survivors, section = [], None
    section_words = {"killed": "killed", "survived": "survived",
                     "timeout": "timeout", "suspicious": "suspicious",
                     "skipped": "skipped", "no tests": "notests"}
    saw_any_section = False
    for raw in results_output.splitlines():
        line = raw.strip().lower()
        for word, tag in section_words.items():
            if word in line and not _MUTANT_NAME_RE.search(raw):
                section, saw_any_section = tag, True
                break
        if section == "survived":
            survivors += _MUTANT_NAME_RE.findall(raw)
    if not saw_any_section and _MUTANT_NAME_RE.search(results_output):
        raise RuntimeError(
            "Could not recognize status sections in `mutmut results` output — "
            "mutmut's output format may have changed again. Raw output:\n"
            + results_output)
    return sorted(set(survivors))


def collect_syntactic_mutants(scratch: Path, subdir: str,
                              test_selection: list[str],
                              pytest_extra_args: list[str],
                              existing_test_file: str,
                              run_timeout: int = 3600,
                              max_mutants: int | None = None) -> list[dict]:
    """Run mutmut in the scratch repo, then for each survivor: apply it,
    capture which function changed, restore, and emit a schema mutant.

    Capture-by-apply is deliberately used instead of parsing `mutmut show`
    diffs: applying and ast-diffing the tree is self-verifying and immune to
    display-format drift.
    """
    assert_fork_capable_linux()
    _write_mutmut_config(scratch, subdir, test_selection, pytest_extra_args)

    print(f"[mutmut] running in {scratch} (this can take a while)…")
    run = subprocess.run(["mutmut", "run"], cwd=scratch, capture_output=True,
                         text=True, timeout=run_timeout)
    print(run.stdout[-3000:])
    if run.returncode not in (0, 2):  # mutmut exits nonzero when mutants survive
        print(run.stderr[-3000:], file=sys.stderr)

    res = subprocess.run(["mutmut", "results"], cwd=scratch,
                         capture_output=True, text=True, timeout=300)
    names = _parse_survivors(res.stdout)
    print(f"[mutmut] surviving mutants reported: {len(names)}")
    if max_mutants:
        names = names[:max_mutants]

    watched = {p: p.read_text(encoding="utf-8")
               for p in (scratch / subdir if subdir else scratch).rglob("*.py")}
    before_funcs = {(f.file, f.qualname): f.source
                    for f in extract_functions(scratch, subdir)}
    mutants: list[dict] = []
    for name in names:
        apply_proc = subprocess.run(["mutmut", "apply", name], cwd=scratch,
                                    capture_output=True, text=True, timeout=120)
        if apply_proc.returncode != 0:
            print(f"[mutmut] apply failed for {name}: "
                  f"{apply_proc.stderr.strip()[:300]}", file=sys.stderr)
            continue
        try:
            after_funcs = {(f.file, f.qualname): f.source
                           for f in extract_functions(scratch, subdir)}
            changed = [(k, before_funcs[k], after_funcs[k])
                       for k in before_funcs
                       if k in after_funcs and after_funcs[k] != before_funcs[k]]
            if len(changed) != 1:
                print(f"[mutmut] {name}: expected exactly 1 changed function, "
                      f"got {len(changed)} — skipped", file=sys.stderr)
                continue
            (file, qual), orig, mut = changed[0]
            lineno = next((f.lineno for f in extract_functions(scratch, subdir)
                           if f.file == file and f.qualname == qual), 0)
            m = {
                "mutant_id": schema.make_mutant_id("syntactic", file, qual, mut),
                "file": file, "function": qual, "line": lineno,
                "original_code": orig, "mutated_code": mut,
                "mutation_operator": f"mutmut:{name}",
                "mutation_source": "mutmut", "mutation_class": "syntactic",
                "mutation_description":
                    f"mutmut syntactic mutant {name} (mechanical operator swap)",
                "diff": schema.make_diff(orig, mut, file),
                "existing_test_file": existing_test_file,
            }
            try:
                schema.validate_mutant(m)
                mutants.append(m)
            except schema.SchemaError as exc:
                print(f"[mutmut] {name}: {exc}", file=sys.stderr)
        finally:
            for p, text in watched.items():
                if p.read_text(encoding="utf-8") != text:
                    p.write_text(text, encoding="utf-8")
    return mutants


# ------------------------------------------------------------------- 1B: SDL
def collect_sdl_mutants(scratch: Path, subdir: str, existing_test_file: str,
                        max_per_function: int = 5) -> list[dict]:
    mutants = []
    for fi in extract_functions(scratch, subdir):
        if fi.is_test:
            continue
        for cand in sdl_mutants_for_function(fi.source, max_per_function):
            m = {
                "mutant_id": schema.make_mutant_id("sdl", fi.file, fi.qualname,
                                                   cand["mutated_code"]),
                "file": fi.file, "function": fi.qualname,
                "line": fi.lineno + cand["line_offset"] - 1,
                "original_code": fi.source, "mutated_code": cand["mutated_code"],
                "mutation_operator": "statement_deletion",
                "mutation_source": "ast_sdl", "mutation_class": "sdl",
                "mutation_description":
                    "Deleted statement: " + cand["deleted_statement"].strip()[:200],
                "diff": schema.make_diff(fi.source, cand["mutated_code"], fi.file),
                "existing_test_file": existing_test_file,
            }
            try:
                schema.validate_mutant(m)
                mutants.append(m)
            except schema.SchemaError as exc:
                print(f"[sdl] skipped: {exc}", file=sys.stderr)
    return mutants


# -------------------------------------------------------------- 1C: semantic
SEMANTIC_SYSTEM = (
    "You are a mutation-testing assistant. You inject exactly ONE subtle, "
    "realistic bug into a Python function — the kind a tired developer would "
    "plausibly write (off-by-one, wrong boundary comparison, swapped "
    "arguments, wrong initial value, inverted condition on one branch). The "
    "bug must NOT be a syntax error and must NOT change the function's "
    "signature. Respond with ONLY a JSON object, no markdown fences, with "
    'keys: "mutated_function" (complete function source), "description" '
    '(one sentence), "operator" (short snake_case bug label).'
)


def collect_semantic_mutants(scratch: Path, subdir: str, existing_test_file: str,
                             client, max_calls: int = 50) -> list[dict]:
    """client is a module3_llm.ollama_client.OllamaClient — the single shared
    integration point. Passed in (not constructed here) to keep module1
    testable with a mock and free of provider knowledge."""
    import ast as _ast
    mutants, start_calls = [], client.calls_made
    for fi in extract_functions(scratch, subdir):
        if (client.calls_made - start_calls) >= max_calls:
            print(f"[semantic] call budget of {max_calls} exhausted, stopping",
                  file=sys.stderr)
            break
        if fi.is_test:
            continue
        obj = client.generate_json(
            system_prompt=SEMANTIC_SYSTEM,
            user_prompt="Inject one subtle realistic bug into this function:\n\n"
                        f"```python\n{fi.source}\n```",
            temperature=None,  # client uses its configured semantic temperature
            purpose="semantic_mutant",
        )
        if not obj or "mutated_function" not in obj:
            print(f"[semantic] {fi.qualname}: no usable JSON, skipped",
                  file=sys.stderr)
            continue
        mut_src = obj["mutated_function"]
        try:
            _ast.parse(mut_src)
        except SyntaxError as exc:
            print(f"[semantic] {fi.qualname}: generated code fails ast.parse "
                  f"({exc}), skipped", file=sys.stderr)
            continue
        m = {
            "mutant_id": schema.make_mutant_id("semantic", fi.file,
                                               fi.qualname, mut_src),
            "file": fi.file, "function": fi.qualname, "line": fi.lineno,
            "original_code": fi.source, "mutated_code": mut_src,
            "mutation_operator": "llm:" + str(obj.get("operator", "semantic_bug")),
            "mutation_source": "llm_semantic", "mutation_class": "semantic",
            "mutation_description": str(obj.get("description",
                                                "LLM-injected realistic bug")),
            "diff": schema.make_diff(fi.source, mut_src, fi.file),
            "existing_test_file": existing_test_file,
        }
        try:
            schema.validate_mutant(m)
            mutants.append(m)
        except schema.SchemaError as exc:
            print(f"[semantic] skipped: {exc}", file=sys.stderr)
    return mutants


# ------------------------------------------------------------------ 1D: HOM
def collect_hom_mutants(first_order: list[dict], existing_test_file: str,
                        max_per_function: int = 3) -> list[dict]:
    mutants = []
    for h in generate_homs(first_order, max_per_function):
        m = {
            "mutant_id": schema.make_mutant_id("higher_order", h["file"],
                                               h["function"], h["mutated_code"]),
            "file": h["file"], "function": h["function"], "line": h["line"],
            "original_code": h["original_code"], "mutated_code": h["mutated_code"],
            "mutation_operator": "hom:" + "+".join(h["parent_operators"])[:120],
            "mutation_source": "hom_combiner", "mutation_class": "higher_order",
            "mutation_description":
                "Higher-order combination of: "
                + " | ".join(d[:100] for d in h["parent_descriptions"]),
            "diff": schema.make_diff(h["original_code"], h["mutated_code"],
                                     h["file"]),
            "existing_test_file": existing_test_file,
            "parents": h["parents"],
        }
        try:
            schema.validate_mutant(m)
            mutants.append(m)
        except schema.SchemaError as exc:
            print(f"[hom] skipped: {exc}", file=sys.stderr)
    return mutants


# ---------------------------------------------------------------- normalize
def build_surviving_mutants(cfg: dict, subject_key: str, client,
                            out_path: Path,
                            skip_mutmut: bool = False,
                            skip_semantic: bool = False) -> list[dict]:
    sub = cfg["subjects"][subject_key]
    mcfg = cfg["mutation"]
    pinned = Path(cfg["_project_root"]) / sub["path"]
    scratch = mutation_runner.make_scratch_copy(pinned, subject_key)
    subdir = sub.get("subdir", "")
    tsel, textra = sub["test_selection"], sub.get("pytest_extra_args", [])
    etf = tsel[0]

    syntactic = [] if skip_mutmut else collect_syntactic_mutants(
        scratch, subdir, tsel, textra, etf,
        run_timeout=mcfg["mutmut_run_timeout_seconds"])
    sdl = collect_sdl_mutants(scratch, subdir, etf,
                              mcfg["max_sdl_per_function"])
    semantic = [] if skip_semantic else collect_semantic_mutants(
        scratch, subdir, etf, client, mcfg["max_semantic_llm_calls"])
    hom = collect_hom_mutants(syntactic + sdl + semantic, etf,
                              mcfg["max_hom_per_function"])

    # Survival confirmation for everything that didn't come from mutmut.
    needs_check = sdl + semantic + hom
    survivors, stats = mutation_runner.filter_survivors(
        scratch, needs_check, tsel, textra,
        suite_timeout=mcfg.get("suite_timeout_seconds", 120))
    print(f"[normalizer] survival filter: {stats}")

    merged = syntactic + survivors
    # De-duplicate by (file, function, mutated_code) across sources.
    seen, unique = set(), []
    for m in merged:
        key = (m["file"], m["function"], m["mutated_code"])
        if key not in seen:
            seen.add(key)
            unique.append(m)

    schema.save_mutants(unique, out_path)
    counts = {}
    for m in unique:
        counts[m["mutation_class"]] = counts.get(m["mutation_class"], 0) + 1
    print(f"[normalizer] wrote {len(unique)} mutants to {out_path}")
    print(f"[normalizer] per-class counts: {json.dumps(counts, indent=2)}")
    return unique
