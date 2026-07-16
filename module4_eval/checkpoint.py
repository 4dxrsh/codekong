"""Crash-safe checkpointing for the (long) generate phase of run_pipeline.

The overnight run makes one LLM call per (mutant, condition, k) and only writes
records_<tag>.json at the very end — so a crash three hours in loses everything.
This streams each finished result to an append-only JSONL side-file and, on
restart, skips the work already recorded. No Claude Code or special tooling is
needed to resume: just rerun the exact same command and it picks up where it
stopped.

    ck = Checkpoint(results_dir / f"_checkpoint_{repo}.jsonl")
    done = ck.load()                          # results already finished
    if not ck.is_done(mid, cond, k):
        r = generate_and_validate(...)
        ck.record(r)                          # durably appended after each unit
    ...
    ck.clear()                                # once records_<tag>.json is written
"""
from __future__ import annotations

import json
import os
from pathlib import Path


def result_key(mutant_id, condition, k) -> str:
    """Stable identity of one unit of work (k is None for NO_RAG)."""
    return f"{mutant_id}|{condition}|{'' if k is None else k}"


class Checkpoint:
    def __init__(self, path):
        self.path = Path(path)
        self._keys: set[str] = set()

    def load(self) -> list[dict]:
        """Return results already recorded, remembering their keys so
        is_done() can skip them. Tolerates a half-written final line left by a
        hard crash."""
        results: list[dict] = []
        if not self.path.exists():
            return results
        with self.path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue  # truncated last line from a crash — drop it
                self._keys.add(result_key(r.get("mutant_id"),
                                          r.get("condition"), r.get("k")))
                results.append(r)
        return results

    def is_done(self, mutant_id, condition, k) -> bool:
        return result_key(mutant_id, condition, k) in self._keys

    def record(self, result: dict) -> None:
        """Append one result durably (flush + fsync) so a crash keeps it."""
        key = result_key(result.get("mutant_id"), result.get("condition"),
                         result.get("k"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(result) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        self._keys.add(key)

    def clear(self) -> None:
        """Remove the side-file (call once records_<tag>.json is consolidated)."""
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass
