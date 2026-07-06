"""Compute and persist metrics per (condition, mutation_class):

  kill_rate            = KILLED / total mutants attempted
  valid_test_rate      = mutants for which at least one generated test passed
                         on the original code / total
  mutation_score_delta = kill_rate of generated tests (all these mutants
                         survived the existing suite, so baseline score
                         contribution was 0 — the delta IS the kill rate,
                         reported per class for clarity)
  cost metrics (RQ4)   = wall seconds + token counts summed from the
                         ollama_client JSONL log (eval_count /
                         prompt_eval_count when Ollama reports them)
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from core.config import resolve


def results_to_frame(results: list[dict]) -> pd.DataFrame:
    rows = []
    for r in results:
        rows.append({
            "mutant_id": r["mutant_id"], "subject": r.get("subject"),
            "condition": r["condition"], "k": r.get("k"),
            "mutation_class": r["mutation_class"], "status": r["status"],
            "killed": r["status"] == "KILLED",
            "valid_test": bool(r.get("valid_test_produced")),
            "retry_used": bool(r.get("retry_used")),
            "killed_first_attempt": r["status"] == "KILLED"
                                    and not r.get("retry_used"),
            "wall_seconds": r.get("wall_seconds"),
        })
    return pd.DataFrame(rows)


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby(["condition", "mutation_class"], dropna=False)
    out = g.agg(n=("mutant_id", "count"), kills=("killed", "sum"),
                kill_rate=("killed", "mean"),
                valid_test_rate=("valid_test", "mean"),
                retry_rate=("retry_used", "mean"),
                first_attempt_kill_rate=("killed_first_attempt", "mean"),
                mean_wall_seconds=("wall_seconds", "mean")).reset_index()
    out["mutation_score_delta"] = out["kill_rate"]
    return out


def cost_from_call_log(cfg: dict) -> pd.DataFrame:
    """Token-cost-equivalent metrics from the JSONL call log (RQ4)."""
    path = resolve(cfg, cfg["llm"]["call_log"])
    if not path.exists():
        return pd.DataFrame()
    rows = [json.loads(line) for line in
            path.read_text(encoding="utf-8").splitlines() if line.strip()]
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["mutation_class"] = df["purpose"].str.extract(
        r"testgen:(?:RAG|NO_RAG):(\w+)")
    df["condition"] = df["purpose"].str.extract(r"testgen:(RAG|NO_RAG):")
    keep = df.dropna(subset=["condition"])
    return keep.groupby(["condition", "mutation_class"]).agg(
        calls=("model", "count"),
        total_wall_seconds=("wall_seconds", "sum"),
        total_eval_tokens=("eval_count", "sum"),
        total_prompt_tokens=("prompt_eval_count", "sum")).reset_index()


def log_metrics(cfg: dict, results: list[dict], tag: str) -> Path:
    outdir = resolve(cfg, cfg["output"]["results_dir"])
    outdir.mkdir(parents=True, exist_ok=True)
    df = results_to_frame(results)
    df.to_csv(outdir / f"raw_{tag}.csv", index=False)
    summary = summarize(df)
    summary.to_csv(outdir / f"summary_{tag}.csv", index=False)
    cost = cost_from_call_log(cfg)
    if not cost.empty:
        cost.to_csv(outdir / f"cost_{tag}.csv", index=False)
    print(summary.to_string(index=False))
    return outdir / f"summary_{tag}.csv"
