"""The unified surviving-mutant schema, agreed in Phase 0.

Every mutant from every source (mutmut syntactic, AST statement-deletion,
LLM semantic, higher-order combiner) is normalized to exactly this shape
before anything downstream touches it. surviving_mutants.json is a JSON
list of these objects.
"""
from __future__ import annotations

import ast
import difflib
import hashlib
import json
from pathlib import Path

MUTATION_CLASSES = ("syntactic", "sdl", "semantic", "higher_order")
MUTATION_SOURCES = ("mutmut", "ast_sdl", "llm_semantic", "hom_combiner")

REQUIRED_FIELDS = (
    "mutant_id", "file", "function", "line",
    "original_code", "mutated_code",
    "mutation_operator", "mutation_source", "mutation_class",
    "mutation_description", "diff", "existing_test_file",
)


class SchemaError(ValueError):
    pass


def make_mutant_id(mutation_class: str, file: str, function: str, mutated_code: str) -> str:
    h = hashlib.sha1(f"{file}|{function}|{mutated_code}".encode()).hexdigest()[:10]
    return f"{mutation_class}_{function}_{h}"


def make_diff(original_code: str, mutated_code: str, file: str) -> str:
    return "".join(difflib.unified_diff(
        original_code.splitlines(keepends=True),
        mutated_code.splitlines(keepends=True),
        fromfile=f"a/{file}", tofile=f"b/{file}",
    ))


def validate_mutant(m: dict) -> None:
    missing = [f for f in REQUIRED_FIELDS if f not in m]
    if missing:
        raise SchemaError(f"mutant missing fields {missing}: {m.get('mutant_id', '<no id>')}")
    if m["mutation_class"] not in MUTATION_CLASSES:
        raise SchemaError(f"unknown mutation_class {m['mutation_class']!r}")
    if m["mutation_source"] not in MUTATION_SOURCES:
        raise SchemaError(f"unknown mutation_source {m['mutation_source']!r}")
    if m["original_code"].strip() == m["mutated_code"].strip():
        raise SchemaError(f"{m['mutant_id']}: mutated_code identical to original_code")
    # Every mutant must at least parse; semantic/HOM generators additionally
    # ast.parse-validate before saving, this is the last line of defense.
    try:
        ast.parse(m["mutated_code"])
    except SyntaxError as exc:
        raise SchemaError(f"{m['mutant_id']}: mutated_code does not parse: {exc}") from exc


def save_mutants(mutants: list[dict], path: Path | str) -> None:
    for m in mutants:
        validate_mutant(m)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(mutants, fh, indent=2)


def load_mutants(path: Path | str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as fh:
        mutants = json.load(fh)
    for m in mutants:
        validate_mutant(m)
    return mutants
