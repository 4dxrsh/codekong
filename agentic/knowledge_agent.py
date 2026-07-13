"""Repository Knowledge Agent — wraps Module 2's indexer.

Input : config + subject key
Output: populated ChromaDB collection + a small manifest JSON so downstream
        agents can verify the index exists without importing chromadb.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from core.config import resolve
from module2_rag.rag_indexer import build_index

MANIFEST = "index_manifest.json"


def run(cfg: dict, subject_key: str) -> Path:
    n = build_index(cfg, subject_key)
    manifest_path = resolve(cfg, cfg["rag"]["chroma_path"]).parent / MANIFEST
    manifest = {}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest[subject_key] = {"chunks": n, "indexed_at": time.time(),
                             "embedding_model": cfg["rag"]["embedding_model"]}
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path
