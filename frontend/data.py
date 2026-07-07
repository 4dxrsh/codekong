"""Data layer for the CodeKong UI. Deliberately flask-free so it can be
unit-tested standalone. Reads ONLY real pipeline outputs — surviving_mutants
JSON, records_*.json, summary/cost CSVs, rq_answers.json — and never invents
numbers: every loader returns an empty structure when a file doesn't exist,
and the UI renders an explicit "no data yet" state for it.
"""
from __future__ import annotations

import ast
import difflib
import json
from pathlib import Path

from core.config import load_config, resolve


# ------------------------------------------------------------------ loading
def _read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def load_corpus(cfg: dict | None = None) -> dict:
    """Everything the UI needs, from disk, every call (cheap at this scale)."""
    cfg = cfg or load_config()
    results_dir = resolve(cfg, cfg["output"]["results_dir"])
    mutants = _read_json(resolve(cfg, cfg["output"]["surviving_mutants"])) or []

    records = []
    for p in sorted(results_dir.glob("records_*.json")):
        records += _read_json(p) or []
    # generate_tests.py reports also carry records
    for p in sorted((Path(cfg["_project_root"]) / "generated_test_suites")
                    .glob("report_*.json")):
        rep = _read_json(p)
        if rep:
            records += rep.get("records", [])

    rq = _read_json(results_dir / "rq_answers.json")
    return {"cfg": cfg, "mutants": mutants, "records": records,
            "rq_answers": rq, "results_dir": results_dir}


def raw_frames(results_dir: Path):
    """Concatenated raw_*.csv as a DataFrame, or None."""
    import pandas as pd
    frames = [pd.read_csv(p) for p in sorted(results_dir.glob("raw_*.csv"))]
    if not frames:
        return None
    return pd.concat(frames, ignore_index=True).drop_duplicates(
        subset=["mutant_id", "condition", "k", "subject"])


def cost_frames(results_dir: Path):
    import pandas as pd
    frames = [pd.read_csv(p) for p in sorted(results_dir.glob("cost_*.csv"))]
    return pd.concat(frames, ignore_index=True) if frames else None


# -------------------------------------------------------------- chart data
CLASS_ORDER = ["syntactic", "sdl", "semantic", "higher_order"]
CLASS_LABEL = {"syntactic": "Syntactic", "sdl": "Statement deletion",
               "semantic": "Semantic (LLM)", "higher_order": "Higher-order"}


def rq_chart_data(results_dir: Path) -> dict:
    """Compute RQ1-RQ4 chart payloads from real CSVs. Empty dict per RQ when
    the data doesn't exist yet."""
    out = {"rq1": {}, "rq2": {}, "rq3": {}, "rq4": {}}
    df = raw_frames(results_dir)
    if df is None or df.empty:
        return out

    g1 = df.groupby("condition")["killed"].agg(["mean", "count"])
    out["rq1"] = {c: {"kill_rate": round(float(g1.loc[c, "mean"]), 3),
                      "n": int(g1.loc[c, "count"])}
                  for c in g1.index}

    g2 = (df.groupby(["mutation_class", "condition"])["killed"].mean()
            .unstack("condition"))
    classes = [c for c in CLASS_ORDER if c in g2.index]
    out["rq2"] = {"classes": [CLASS_LABEL[c] for c in classes],
                  "rag": [round(float(g2.loc[c].get("RAG", float("nan"))), 3)
                          if "RAG" in g2.columns else None for c in classes],
                  "norag": [round(float(g2.loc[c].get("NO_RAG", float("nan"))), 3)
                            if "NO_RAG" in g2.columns else None for c in classes]}

    rag = df[(df["condition"] == "RAG") & df["k"].notna()]
    if not rag.empty:
        g3 = rag.groupby("k").agg(kill_rate=("killed", "mean"),
                                  valid_test_rate=("valid_test", "mean"))
        out["rq3"] = {"k": [int(k) for k in g3.index],
                      "kill_rate": [round(float(v), 3) for v in g3["kill_rate"]],
                      "valid_test_rate": [round(float(v), 3)
                                          for v in g3["valid_test_rate"]]}

    cost = cost_frames(results_dir)
    if cost is not None and not cost.empty and "mutation_class" in cost:
        kills = df.groupby(["condition", "mutation_class"])["killed"].sum()
        rows = []
        for _, r in cost.dropna(subset=["mutation_class"]).iterrows():
            key = (r["condition"], r["mutation_class"])
            kill_n = int(kills.get(key, 0))
            tokens = float((r.get("total_eval_tokens") or 0)
                           + (r.get("total_prompt_tokens") or 0))
            rows.append({"condition": r["condition"],
                         "mutation_class": CLASS_LABEL.get(r["mutation_class"],
                                                           r["mutation_class"]),
                         "tokens": int(tokens), "kills": kill_n,
                         "tokens_per_kill": round(tokens / kill_n)
                         if kill_n else None})
        out["rq4"] = {"rows": rows}
    return out


# ------------------------------------------------------------ code visuals
def diff_rows(original: str, mutated: str) -> list[dict]:
    """Side-by-side-able diff rows: tag in {'same','del','add'}."""
    a, b = original.splitlines(), mutated.splitlines()
    rows = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b).get_opcodes():
        if tag == "equal":
            for off, line in enumerate(a[i1:i2]):
                rows.append({"tag": "same", "a": i1 + off + 1,
                             "b": j1 + off + 1, "text": line})
        else:
            for off, line in enumerate(a[i1:i2]):
                rows.append({"tag": "del", "a": i1 + off + 1, "b": None,
                             "text": line})
            for off, line in enumerate(b[j1:j2]):
                rows.append({"tag": "add", "a": None, "b": j1 + off + 1,
                             "text": line})
    return rows


def changed_original_lines(original: str, mutated: str) -> set[int]:
    return {r["a"] for r in diff_rows(original, mutated)
            if r["tag"] == "del" and r["a"]}


def ast_json(source: str, marked_lines: set[int] | None = None) -> dict | None:
    """Nested {label, line, marked, children} tree of the ORIGINAL function
    source, with nodes on mutated lines marked. Returns None if unparseable."""
    marked_lines = marked_lines or set()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None

    def node_label(n: ast.AST) -> str:
        name = getattr(n, "name", None) or getattr(n, "id", None)
        if isinstance(n, ast.Constant):
            name = repr(n.value)[:30]
        if isinstance(n, (ast.BinOp, ast.Compare, ast.BoolOp, ast.UnaryOp)):
            ops = getattr(n, "ops", None) or [getattr(n, "op", None)]
            name = "/".join(type(o).__name__ for o in ops if o is not None)
        return f"{type(n).__name__}" + (f": {name}" if name else "")

    def walk(n: ast.AST) -> dict:
        line = getattr(n, "lineno", None)
        children = [walk(c) for c in ast.iter_child_nodes(n)]
        marked = (line in marked_lines) or any(c["marked"] for c in children)
        return {"label": node_label(n), "line": line,
                "self_marked": line in marked_lines,
                "marked": marked, "children": children}

    return walk(tree)


# ------------------------------------------------------------- table views
def explore_rows(corpus: dict) -> list[dict]:
    by_id: dict[str, dict] = {}
    for r in corpus["records"]:
        e = by_id.setdefault(r["mutant_id"], {"conditions": set(),
                                              "killed": False, "runs": 0})
        e["conditions"].add(r["condition"])
        e["runs"] += 1
        e["killed"] = e["killed"] or r["status"] == "KILLED"
    rows = []
    for m in corpus["mutants"]:
        e = by_id.get(m["mutant_id"], {})
        rows.append({"mutant_id": m["mutant_id"], "file": m["file"],
                     "function": m["function"],
                     "mutation_class": m["mutation_class"],
                     "subject": _subject_of(m, corpus),
                     "conditions": sorted(e.get("conditions", [])),
                     "runs": e.get("runs", 0),
                     "killed": e.get("killed", False)})
    # Records may reference mutants not in the current surviving_mutants.json
    # (earlier runs); show them too rather than silently dropping data.
    known = {r["mutant_id"] for r in rows}
    for mid, e in by_id.items():
        if mid not in known:
            rec = next(r for r in corpus["records"] if r["mutant_id"] == mid)
            rows.append({"mutant_id": mid, "file": "(not in current mutant set)",
                         "function": "", "mutation_class": rec["mutation_class"],
                         "subject": rec.get("subject", "?"),
                         "conditions": sorted(e["conditions"]),
                         "runs": e["runs"], "killed": e["killed"]})
    return rows


def _subject_of(m: dict, corpus: dict) -> str:
    for r in corpus["records"]:
        if r["mutant_id"] == m["mutant_id"] and r.get("subject"):
            return r["subject"]
    return "unrun"


def mutant_detail(corpus: dict, mutant_id: str) -> dict | None:
    m = next((x for x in corpus["mutants"] if x["mutant_id"] == mutant_id), None)
    recs = [r for r in corpus["records"] if r["mutant_id"] == mutant_id]
    if m is None and not recs:
        return None
    tests = []
    for r in recs:
        for v in r.get("validation", []):
            test_code = None
            tf = r.get("test_file")
            if tf and Path(tf).exists():
                test_code = Path(tf).read_text(encoding="utf-8")[:2000]
            tests.append({"condition": r["condition"], "k": r.get("k"),
                          "attempt": v.get("attempt"),
                          "passed": v.get("status") == "PASS",
                          "stage": v.get("stage"), "reason": v.get("reason"),
                          "origin": "generated", "code": test_code})
    chunks = []
    for r in recs:
        for c in r.get("context_chunks", []):
            if c not in chunks:
                chunks.append(c)
    detail = {"mutant": m, "records": recs, "tests": tests, "chunks": chunks}
    if m:
        changed = changed_original_lines(m["original_code"], m["mutated_code"])
        detail["diff"] = diff_rows(m["original_code"], m["mutated_code"])
        detail["ast"] = ast_json(m["original_code"], changed)
    return detail


def passed_test_rows(corpus: dict) -> list[dict]:
    rows = []
    for r in corpus["records"]:
        if not r.get("valid_test_produced"):
            continue
        tf = r.get("test_file")
        snippet = ""
        if tf and Path(tf).exists():
            snippet = Path(tf).read_text(encoding="utf-8")[:800]
        rows.append({"mutant_id": r["mutant_id"], "subject": r.get("subject"),
                     "mutation_class": r["mutation_class"],
                     "condition": r["condition"], "k": r.get("k"),
                     "killed": r["status"] == "KILLED",
                     "origin": "generated", "snippet": snippet})
    return rows
