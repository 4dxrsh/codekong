"""Statement-deletion (SDL) mutant generation via Python's ast module.

For each function, delete one deletable statement at a time. If deleting the
statement would empty its block, substitute `pass` so the result still parses.
Every candidate is ast.parse-validated before being returned; anything that
fails to parse is skipped and logged, never saved.
"""
from __future__ import annotations

import ast
import sys

# Statements whose deletion is a classic SDL mutation. Deliberately excludes
# def/class/import at function top level (deleting those mostly produces
# NameErrors that are trivially detected, which defeats the point of SDL as a
# "harder than syntactic" class).
_DELETABLE = (ast.Assign, ast.AugAssign, ast.AnnAssign, ast.Expr, ast.Return,
              ast.If, ast.For, ast.While, ast.Raise, ast.Assert, ast.Continue,
              ast.Break)


def _blocks(node: ast.AST):
    """Yield (parent, field, stmt_list) for every statement block under node."""
    for field in ("body", "orelse", "finalbody"):
        blk = getattr(node, field, None)
        if isinstance(blk, list) and blk and isinstance(blk[0], ast.stmt):
            yield node, field, blk
    for child in ast.iter_child_nodes(node):
        yield from _blocks(child)


def sdl_mutants_for_function(func_source: str, max_per_function: int = 5,
                             log=print) -> list[dict]:
    """Return [{mutated_code, deleted_statement, line_offset}] for one function.

    line_offset is the deleted statement's line number relative to the start
    of the function source (1-based), so callers can map to file line numbers.
    """
    try:
        tree = ast.parse(func_source)
    except SyntaxError:
        log(f"[sdl] source does not parse, skipping function", file=sys.stderr)
        return []
    func = tree.body[0]
    if not isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return []

    lines = func_source.splitlines(keepends=True)
    out: list[dict] = []
    seen: set[str] = set()

    for _parent, _field, blk in _blocks(func):
        for idx, stmt in enumerate(blk):
            if len(out) >= max_per_function:
                return out
            if not isinstance(stmt, _DELETABLE):
                continue
            # Never delete the docstring expression.
            if (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant)
                    and isinstance(stmt.value.value, str)):
                continue
            start, end = stmt.lineno - 1, (stmt.end_lineno or stmt.lineno) - 1
            indent = len(lines[start]) - len(lines[start].lstrip())
            deleted = "".join(lines[start:end + 1]).rstrip("\n")
            if len(blk) == 1:
                # Deleting would empty the block: replace with pass at same indent.
                replacement = [" " * indent + "pass\n"]
            else:
                replacement = []
            mutated = "".join(lines[:start] + replacement + lines[end + 1:])
            try:
                ast.parse(mutated)
            except SyntaxError:
                log(f"[sdl] deletion at line {start + 1} fails to parse, skipped",
                    file=sys.stderr)
                continue
            if mutated in seen or mutated.strip() == func_source.strip():
                continue
            seen.add(mutated)
            out.append({"mutated_code": mutated, "deleted_statement": deleted,
                        "line_offset": start + 1})
    return out
