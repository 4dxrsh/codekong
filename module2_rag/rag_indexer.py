"""AST-walk the subject repo, embed chunks locally, load into ChromaDB.

Chunks: one per function body, one per docstring, one per test function.
Embeddings: sentence-transformers all-MiniLM-L6-v2, fully local, no API.
Store: chromadb.PersistentClient at module2_rag/chroma_db (gitignored).

API shapes verified against current docs: PersistentClient(path=...),
get_or_create_collection(name), collection.upsert(ids, documents,
embeddings, metadatas), collection.query(query_embeddings, n_results, where).
"""
from __future__ import annotations

import ast
from pathlib import Path

from core.config import resolve
from core.srcmap import extract_functions


def module_constant_chunks(repo: Path, subdir: str):
    """Yield (file, qualname, text) chunks for MODULE-LEVEL constants/config.

    The AST function walk indexes functions/classes only, so a module that is
    just a table of constants (rates, thresholds, lookup dicts — a codebase's
    'source of truth') was invisible to retrieval. Any test whose correctness
    depends on such a value could never be helped by RAG. This surfaces those
    module-level assignments (with the module docstring for context) as their
    own retrievable chunks.
    """
    base = repo / subdir if subdir else repo
    for py in sorted(base.rglob("*.py")):
        try:
            src = py.read_text(encoding="utf-8")
            tree = ast.parse(src)
        except (SyntaxError, UnicodeDecodeError):
            continue
        lines = src.splitlines()
        rel = py.relative_to(repo).as_posix()
        mod_doc = (ast.get_docstring(tree) or "").replace("\n", " ")
        # ONE chunk PER module-level constant so each embeds near queries about
        # that specific value (a single blob of every table embeds too diffusely
        # to be retrieved for any one of them).
        for node in tree.body:
            if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue
            seg = ast.get_source_segment(src, node)
            if not seg:
                continue
            targets = (node.targets if isinstance(node, ast.Assign)
                       else [node.target])
            names = [t.id for t in targets if isinstance(t, ast.Name)]
            if not names:
                continue
            # pull the comment block immediately above the assignment (it
            # describes what the constant means — key retrieval signal).
            comment, i = [], node.lineno - 2
            while i >= 0 and lines[i].strip().startswith("#"):
                comment.insert(0, lines[i].strip().lstrip("#").strip())
                i -= 1
            desc = " ".join(comment)
            name = names[0]
            text = (f"{rel} defines constant {name}"
                    + (f" — {desc}" if desc else "")
                    + (f" (from module: {mod_doc[:100]})" if mod_doc else "")
                    + f"\n{seg}")
            yield rel, f"const:{name}", text


def _lazy_imports():
    try:
        import chromadb
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "module2_rag needs chromadb + sentence-transformers. "
            "Run: pip install -r requirements.txt") from exc
    return chromadb, SentenceTransformer


def collection_name(subject_key: str) -> str:
    return f"codekong_{subject_key}"


def build_index(cfg: dict, subject_key: str) -> int:
    """Index the subject repo. Returns number of chunks indexed."""
    chromadb, SentenceTransformer = _lazy_imports()
    sub = cfg["subjects"][subject_key]
    repo = Path(cfg["_project_root"]) / sub["path"]
    subdir = sub.get("subdir", "")

    ids, docs, metas = [], [], []
    for fi in extract_functions(repo, subdir):
        kind = "test" if fi.is_test else "function"
        ids.append(f"{fi.file}::{fi.qualname}::{kind}")
        docs.append(fi.source)
        metas.append({"file": fi.file, "qualname": fi.qualname, "kind": kind,
                      "name": fi.name, "symbol": fi.name, "lineno": fi.lineno})
        if fi.docstring:
            ids.append(f"{fi.file}::{fi.qualname}::docstring")
            docs.append(f"{fi.qualname}: {fi.docstring}")
            metas.append({"file": fi.file, "qualname": fi.qualname,
                          "kind": "docstring", "name": fi.name,
                          "symbol": fi.name, "lineno": fi.lineno})
    # For subjects whose tests live outside subdir (e.g. dbader/schedule's
    # test_schedule.py at repo root), index root-level test files too.
    if subdir:
        for fi in extract_functions(repo, ""):
            if fi.is_test and not fi.file.startswith(subdir):
                cid = f"{fi.file}::{fi.qualname}::test"
                if cid not in ids:
                    ids.append(cid)
                    docs.append(fi.source)
                    metas.append({"file": fi.file, "qualname": fi.qualname,
                                  "kind": "test", "name": fi.name,
                                  "lineno": fi.lineno})

    # Module-level constants/config (rates, thresholds, lookup tables) — the
    # 'source of truth' values a function references but doesn't itself contain.
    for rel, qual, text in module_constant_chunks(repo, subdir):
        cid = f"{rel}::{qual}::constants"
        if cid not in ids:
            ids.append(cid)
            docs.append(text)
            metas.append({"file": rel, "qualname": qual, "kind": "constants",
                          "name": qual, "symbol": qual.split(":", 1)[-1],
                          "lineno": 0})

    if not ids:
        raise RuntimeError(f"No chunks extracted from {repo}/{subdir} — wrong "
                           "path or empty subject?")

    model = SentenceTransformer(cfg["rag"]["embedding_model"])
    embeddings = model.encode(docs, show_progress_bar=False,
                              batch_size=32).tolist()

    client = chromadb.PersistentClient(path=str(resolve(cfg, cfg["rag"]["chroma_path"])))
    coll = client.get_or_create_collection(collection_name(subject_key))
    coll.upsert(ids=ids, documents=docs, embeddings=embeddings, metadatas=metas)
    print(f"[indexer] indexed {len(ids)} chunks for '{subject_key}' "
          f"into {cfg['rag']['chroma_path']}")
    return len(ids)


if __name__ == "__main__":
    import argparse
    from core.config import load_config

    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    args = ap.parse_args()
    build_index(load_config(), args.repo)
