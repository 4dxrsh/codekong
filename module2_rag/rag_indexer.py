"""AST-walk the subject repo, embed chunks locally, load into ChromaDB.

Chunks: one per function body, one per docstring, one per test function.
Embeddings: sentence-transformers all-MiniLM-L6-v2, fully local, no API.
Store: chromadb.PersistentClient at module2_rag/chroma_db (gitignored).

API shapes verified against current docs: PersistentClient(path=...),
get_or_create_collection(name), collection.upsert(ids, documents,
embeddings, metadatas), collection.query(query_embeddings, n_results, where).
"""
from __future__ import annotations

from pathlib import Path

from core.config import resolve
from core.srcmap import extract_functions


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
                      "name": fi.name, "lineno": fi.lineno})
        if fi.docstring:
            ids.append(f"{fi.file}::{fi.qualname}::docstring")
            docs.append(f"{fi.qualname}: {fi.docstring}")
            metas.append({"file": fi.file, "qualname": fi.qualname,
                          "kind": "docstring", "name": fi.name,
                          "lineno": fi.lineno})
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
