"""Mutation-class-aware retrieval from the local ChromaDB index.

Query construction per class (the design's hardness-aware strategy):
  syntactic    — function name + the mutation diff (the change is local and
                 mechanical; nearby code and the function itself matter most)
  sdl          — function name + the deleted statement text
  semantic     — FULL function body + the mutation description (the bug is
                 behavioral; we want semantically similar code and tests)
  higher_order — TWO queries, one per component mutation, results merged and
                 deduplicated, best-distance-first, truncated to k
"""
from __future__ import annotations

from core.config import resolve
from module2_rag.rag_indexer import collection_name, _lazy_imports


class Retriever:
    def __init__(self, cfg: dict, subject_key: str):
        chromadb, SentenceTransformer = _lazy_imports()
        self._model = SentenceTransformer(cfg["rag"]["embedding_model"])
        client = chromadb.PersistentClient(
            path=str(resolve(cfg, cfg["rag"]["chroma_path"])))
        self._coll = client.get_or_create_collection(collection_name(subject_key))

    # ------------------------------------------------------ query building
    @staticmethod
    def build_queries(mutant: dict) -> list[str]:
        mc = mutant["mutation_class"]
        func = mutant["function"]
        if mc == "syntactic":
            return [f"{func}\n{mutant['diff']}"]
        if mc == "sdl":
            return [f"{func}\n{mutant['mutation_description']}"]
        if mc == "semantic":
            return [f"{mutant['original_code']}\n{mutant['mutation_description']}"]
        if mc == "higher_order":
            descs = mutant.get("mutation_description", "").split(" | ")
            if len(descs) >= 2:
                return [f"{func}\n{descs[0]}", f"{func}\n{descs[1]}"]
            return [f"{func}\n{mutant['mutation_description']}",
                    f"{func}\n{mutant['diff']}"]
        raise ValueError(f"unknown mutation_class {mc!r}")

    # ------------------------------------------------------------ retrieval
    def retrieve(self, mutant: dict, k: int) -> list[dict]:
        queries = self.build_queries(mutant)
        per_query_k = k if len(queries) == 1 else max(1, (k + 1) // 2 + 1)
        embeddings = self._model.encode(queries, show_progress_bar=False).tolist()
        res = self._coll.query(query_embeddings=embeddings,
                               n_results=per_query_k)
        merged: dict[str, dict] = {}
        for qi in range(len(queries)):
            for cid, doc, meta, dist in zip(res["ids"][qi], res["documents"][qi],
                                            res["metadatas"][qi],
                                            res["distances"][qi]):
                if cid not in merged or dist < merged[cid]["distance"]:
                    merged[cid] = {"id": cid, "document": doc,
                                   "metadata": meta, "distance": dist}
        chunks = sorted(merged.values(), key=lambda c: c["distance"])[:k]
        # Never hand the model the mutant's own function verbatim as "context"
        # for free — it is already in the prompt. Drop exact-self chunks.
        chunks = [c for c in chunks
                  if not (c["metadata"].get("qualname") == mutant["function"]
                          and c["metadata"].get("file") == mutant["file"]
                          and c["metadata"].get("kind") == "function")]
        return chunks


def retrieve_for_mutants(cfg: dict, subject_key: str, mutants: list[dict],
                         k: int) -> dict[str, list[dict]]:
    r = Retriever(cfg, subject_key)
    return {m["mutant_id"]: r.retrieve(m, k) for m in mutants}
