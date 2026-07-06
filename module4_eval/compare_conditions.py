"""RAG vs NO_RAG comparison per mutation_class, plus the four figures.

RQ1: does RAG beat NO_RAG overall?
RQ2: does the RAG benefit grow with class hardness
     (syntactic < semantic < higher_order)? Reported EITHER WAY — an
     inconclusive or reversed gradient is a result, not a failure.
RQ3: retrieval depth k vs valid-test rate.
RQ4: cost per class (from the call-log token/duration accounting).
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from core.config import resolve
from module4_eval.metrics_logger import results_to_frame, summarize

HARDNESS_ORDER = ["syntactic", "sdl", "semantic", "higher_order"]


def load_all_results(cfg: dict, pattern: str = "raw_*.csv") -> pd.DataFrame:
    outdir = resolve(cfg, cfg["output"]["results_dir"])
    frames = [pd.read_csv(p) for p in sorted(outdir.glob(pattern))]
    if not frames:
        raise FileNotFoundError(f"no {pattern} under {outdir} — run the "
                                "pipeline first")
    return pd.concat(frames, ignore_index=True).drop_duplicates(
        subset=["mutant_id", "condition", "k", "subject"])


def rag_delta_per_class(df: pd.DataFrame) -> pd.DataFrame:
    s = (df.groupby(["condition", "mutation_class"])["killed"]
           .agg(["mean", "count"]).reset_index()
           .pivot(index="mutation_class", columns="condition",
                  values=["mean", "count"]))
    s.columns = [f"{a}_{b}" for a, b in s.columns]
    for col in ("mean_RAG", "mean_NO_RAG"):
        if col not in s:
            s[col] = float("nan")
    s["rag_delta"] = s["mean_RAG"] - s["mean_NO_RAG"]
    s = s.reindex([c for c in HARDNESS_ORDER if c in s.index])
    return s.reset_index()


def answer_rqs(cfg: dict, df: pd.DataFrame) -> dict:
    delta = rag_delta_per_class(df)
    overall = df.groupby("condition")["killed"].agg(["mean", "count"])

    rq1 = {
        "kill_rate_rag": float(overall.loc["RAG", "mean"]) if "RAG" in overall.index else None,
        "kill_rate_norag": float(overall.loc["NO_RAG", "mean"]) if "NO_RAG" in overall.index else None,
    }
    rq1["rag_wins_overall"] = (rq1["kill_rate_rag"] is not None
                               and rq1["kill_rate_norag"] is not None
                               and rq1["kill_rate_rag"] > rq1["kill_rate_norag"])

    # RQ2: is the delta monotonically nondecreasing along the hardness order
    # syntactic -> semantic -> higher_order? (sdl reported but the original
    # hypothesis names the three-class gradient.)
    grad_classes = [c for c in ("syntactic", "semantic", "higher_order")
                    if c in set(delta["mutation_class"])]
    deltas = [float(delta.loc[delta["mutation_class"] == c, "rag_delta"].iloc[0])
              for c in grad_classes]
    rq2 = {"classes": grad_classes, "deltas": deltas,
           "gradient_holds": len(deltas) >= 2
                             and all(b >= a for a, b in zip(deltas, deltas[1:])),
           "note": "Report honestly either way; an inconclusive gradient is a "
                   "finding, not a failure."}

    # RQ3: valid-test rate by k (RAG rows only; k is a RAG knob).
    rag = df[df["condition"] == "RAG"].dropna(subset=["k"])
    rq3 = (rag.groupby("k")["valid_test"].mean().to_dict() if not rag.empty
           else {})

    answers = {"RQ1": rq1, "RQ2": rq2,
               "RQ3_valid_test_rate_by_k": {int(k): float(v)
                                            for k, v in rq3.items()},
               "delta_table": delta.to_dict(orient="records")}
    outdir = resolve(cfg, cfg["output"]["results_dir"])
    (outdir / "rq_answers.json").write_text(json.dumps(answers, indent=2),
                                            encoding="utf-8")
    print(json.dumps({k: v for k, v in answers.items() if k != "delta_table"},
                     indent=2))
    return answers


# ------------------------------------------------------------------ figures
def _save(fig, cfg, name):
    outdir = resolve(cfg, cfg["output"]["figures_dir"])
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / name
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"[figures] wrote {path}")


def make_figures(cfg: dict, df: pd.DataFrame) -> None:
    order = [c for c in HARDNESS_ORDER if c in df["mutation_class"].unique()]

    # Fig 1: mutation score before/after generated tests, per class.
    # "Before" is 0 by construction (every mutant here survived the existing
    # suite); "after" is the kill rate of the better condition per class.
    fig, ax = plt.subplots(figsize=(7, 4))
    after = (df[df["killed"]].groupby("mutation_class")["mutant_id"].count()
             / df.groupby("mutation_class")["mutant_id"].count()).reindex(order)
    ax.bar([f"{c}\n(before)" for c in order], [0] * len(order), color="#bbb")
    ax.bar([f"{c}\n(after)" for c in order], after.fillna(0).values,
           color="#3b7dd8")
    ax.set_ylabel("mutation score contribution")
    ax.set_title("Mutation score before vs after generated tests")
    _save(fig, cfg, "fig1_mutation_score_before_after.png")

    # Fig 2: per-class kill rate, RAG vs NO_RAG.
    fig, ax = plt.subplots(figsize=(7, 4))
    piv = (df.groupby(["mutation_class", "condition"])["killed"].mean()
             .unstack("condition").reindex(order))
    piv.plot.bar(ax=ax, rot=0, color={"RAG": "#3b7dd8", "NO_RAG": "#d87d3b"})
    ax.set_ylabel("kill rate")
    ax.set_title("Kill rate per mutation class: RAG vs NO_RAG")
    _save(fig, cfg, "fig2_killrate_rag_vs_norag.png")

    # Fig 3: ablation by prompt variant — first-attempt kills vs kills that
    # needed the retry (the refinement layer's contribution), per class.
    fig, ax = plt.subplots(figsize=(7, 4))
    killed = df[df["killed"]]
    first = killed[~killed["retry_used"]].groupby("mutation_class")["mutant_id"].count()
    retry = killed[killed["retry_used"]].groupby("mutation_class")["mutant_id"].count()
    total = df.groupby("mutation_class")["mutant_id"].count()
    f = (first / total).reindex(order).fillna(0)
    r = (retry / total).reindex(order).fillna(0)
    ax.bar(order, f.values, label="first attempt", color="#3b7dd8")
    ax.bar(order, r.values, bottom=f.values, label="after 1 retry",
           color="#7db83b")
    ax.legend()
    ax.set_ylabel("kill rate")
    ax.set_title("Prompt/refinement ablation: first attempt vs one retry")
    _save(fig, cfg, "fig3_ablation_retry.png")

    # Fig 4: valid-test rate by retrieval depth k (RAG only).
    fig, ax = plt.subplots(figsize=(7, 4))
    rag = df[df["condition"] == "RAG"].dropna(subset=["k"])
    if not rag.empty:
        vt = rag.groupby("k")["valid_test"].mean()
        ax.plot(vt.index.astype(int), vt.values, marker="o", color="#3b7dd8")
    ax.set_xlabel("retrieval depth k")
    ax.set_ylabel("valid test rate")
    ax.set_title("Valid test rate by retrieval depth k (RQ3)")
    _save(fig, cfg, "fig4_validrate_by_k.png")


def main(cfg: dict) -> None:
    df = load_all_results(cfg)
    print(summarize_from_raw(df).to_string(index=False))
    answer_rqs(cfg, df)
    make_figures(cfg, df)


def summarize_from_raw(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby(["condition", "mutation_class"])
    return g.agg(n=("mutant_id", "count"), kill_rate=("killed", "mean"),
                 valid_test_rate=("valid_test", "mean")).reset_index()


if __name__ == "__main__":
    from core.config import load_config
    main(load_config())
