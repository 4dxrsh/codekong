"""AST helpers shared by the mutation and RAG modules: enumerate functions in
a repo subtree and extract exact function source segments."""
from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FunctionInfo:
    file: str          # path relative to repo root, posix style
    qualname: str
    name: str
    lineno: int
    end_lineno: int
    source: str        # exact source segment
    docstring: str | None
    is_test: bool


def iter_python_files(repo_root: Path, subdir: str = "") -> list[Path]:
    base = repo_root / subdir if subdir else repo_root
    return sorted(p for p in base.rglob("*.py")
                  if "__pycache__" not in p.parts and ".git" not in p.parts)


def extract_functions(repo_root: Path, subdir: str = "") -> list[FunctionInfo]:
    out: list[FunctionInfo] = []
    for path in iter_python_files(Path(repo_root), subdir):
        try:
            src = path.read_text(encoding="utf-8")
            tree = ast.parse(src)
        except (SyntaxError, UnicodeDecodeError):
            continue  # skip unparseable files, never crash the walk
        rel = path.relative_to(repo_root).as_posix()

        class V(ast.NodeVisitor):
            def __init__(self):
                self.stack: list[str] = []

            def _visit_func(self, node):
                qual = ".".join(self.stack + [node.name])
                seg = ast.get_source_segment(src, node)
                if seg:
                    out.append(FunctionInfo(
                        file=rel, qualname=qual, name=node.name,
                        lineno=node.lineno, end_lineno=node.end_lineno or node.lineno,
                        source=seg, docstring=ast.get_docstring(node),
                        is_test=node.name.startswith("test_") or "test" in Path(rel).name,
                    ))
                self.stack.append(node.name)
                self.generic_visit(node)
                self.stack.pop()

            visit_FunctionDef = _visit_func
            visit_AsyncFunctionDef = _visit_func

            def visit_ClassDef(self, node):
                self.stack.append(node.name)
                self.generic_visit(node)
                self.stack.pop()

        V().visit(tree)
    return out


def find_function(repo_root: Path, file: str, function: str) -> FunctionInfo | None:
    for fi in extract_functions(Path(repo_root)):
        if fi.file == file and (fi.qualname == function or fi.name == function):
            return fi
    return None
