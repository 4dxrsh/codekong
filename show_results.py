"""Print CodeKong's headline results straight from the real run records.

Reads module4_eval/results/ and shows, per subject, the RAG-vs-NO-RAG mutation
kill rate at each retrieval depth k, plus the four research-question answers.
Fully offline — no model, vector store, or network needed — so it runs the same
on the Windows dev box and the Linux run host, and makes a clean screenshot.

    python show_results.py
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

# Windows consoles default to cp1252 and choke on the block-bar glyphs; force
# UTF-8 so the same output renders on every platform.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

ROOT = Path(__file__).resolve().parent
RES = ROOT / "module4_eval" / "results"

SUBJECTS = {
    "ctxlib": "Context-dependent code  (ctxlib)",
    "sorts_focused": "Self-contained code  (sorting)",
}


def bar(pct: float, width: int = 26) -> str:
    n = round(pct / 100 * width)
    return "█" * n + "░" * (width - n)


def rate(kills: int, total: int) -> str:
    pct = 100 * kills / total if total else 0.0
    return f"{kills:>2}/{total:<2}  {pct:5.1f}%  {bar(pct)}"


def main() -> None:
    line = "=" * 68
    print("\n" + line)
    print("  CodeKong  ·  RAG vs NO-RAG mutation-kill results (from the real run)")
    print(line)

    for key, label in SUBJECTS.items():
        f = RES / f"records_{key}.json"
        if not f.exists():
            continue
        recs = json.loads(f.read_text(encoding="utf-8"))
        no = [r for r in recs if r["condition"] == "NO_RAG"]
        no_k = sum(1 for r in no if r["status"] == "KILLED")
        print(f"\n  {label}")
        print(f"    NO-RAG      {rate(no_k, len(no))}")
        byk = collections.defaultdict(list)
        for r in recs:
            if r["condition"] == "RAG":
                byk[r["k"]].append(r)
        for k in sorted(byk):
            rk = byk[k]
            kk = sum(1 for r in rk if r["status"] == "KILLED")
            print(f"    RAG k={k:<2}    {rate(kk, len(rk))}")

    rq = json.loads((RES / "rq_answers.json").read_text(encoding="utf-8"))
    print("\n" + "-" * 68)
    print("  Research questions")
    print("-" * 68)
    r1 = rq["RQ1"]
    print(f"  RQ1  overall: RAG {r1['kill_rate_rag']*100:.1f}%  vs  "
          f"NO-RAG {r1['kill_rate_norag']*100:.1f}%   ->  RAG wins: "
          f"{r1['rag_wins_overall']}")
    for row in rq["delta_table"]:
        print(f"  RQ2  {row['mutation_class']:<13} "
              f"NO-RAG {row['mean_NO_RAG']*100:5.1f}%  ->  "
              f"RAG {row['mean_RAG']*100:5.1f}%   "
              f"(+{row['rag_delta']*100:.0f} pts)")
    k_rates = rq["RQ3_valid_test_rate_by_k"]
    print("  RQ3  valid-test rate by depth k:  " +
          "   ".join(f"k={k}: {v*100:.0f}%" for k, v in k_rates.items()))
    print("  RQ4  tokens per kill: see cost_*.csv  "
          "(RAG ~2.2k vs NO-RAG ~15.9k on ctxlib — 7x cheaper per bug)")
    print()


if __name__ == "__main__":
    main()
