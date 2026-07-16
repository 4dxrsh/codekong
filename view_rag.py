"""Show what's stored in the RAG memory (ChromaDB) for a subject."""
import sys, chromadb, collections
from pathlib import Path
from core.config import load_config

subject = sys.argv[1] if len(sys.argv) > 1 else "ctxlib"
cfg = load_config()
client = chromadb.PersistentClient(
    path=str(Path(cfg["_project_root"]) / cfg["rag"]["chroma_path"]))

print("Collections in the RAG store:")
for c in client.list_collections():
    print("  -", c.name)

coll = client.get_or_create_collection(f"codekong_{subject}")
got = coll.get(include=["documents", "metadatas"])
n = len(got["ids"])
print(f"\n=== codekong_{subject}: {n} chunks stored ===")
by_file = collections.Counter(m.get("file") for m in got["metadatas"])
by_kind = collections.Counter(m.get("kind") for m in got["metadatas"])
print("by file:", dict(by_file))
print("by kind:", dict(by_kind))

print("\n--- every chunk (file | kind | qualname) ---")
for m in sorted(got["metadatas"], key=lambda x: (x.get("file"), x.get("kind"))):
    print(f"  {m.get('file'):16} {m.get('kind'):10} {m.get('qualname')}")

# show the full stored text of the 'constants' chunks — the codebase facts RAG retrieves
print("\n--- FULL TEXT of the constant chunks (the facts that let RAG win) ---")
for doc, m in zip(got["documents"], got["metadatas"]):
    if m.get("kind") == "constants":
        print(f"\n[{m.get('file')} :: {m.get('qualname')}]")
        print(doc)
