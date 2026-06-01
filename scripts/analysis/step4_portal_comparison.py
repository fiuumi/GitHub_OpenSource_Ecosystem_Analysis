#!/usr/bin/env python3
"""
Step 4: Trending vs Topics Comparison + Domain-Language Cross Analysis
=======================================================================
Two analytical views:
  1. Portal-level structural comparison (radar + box plots)
  2. Technology-Domain × Programming-Language heat-map

Input : output/analysis/cleaned_data.pkl
Output: output/analysis/portal_radar.png
        output/analysis/portal_boxplot.png
        output/analysis/domain_language_heatmap.png
        output/analysis/structure_metrics.csv
        output/analysis/domain_language_matrix.csv
"""

import sys
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

OUTPUT_DIR = PROJECT_ROOT / "output" / "analysis"

# ---------------------------------------------------------------------------
# Domain keyword groupings (must be subsets of the crawler keyword dict)
# ---------------------------------------------------------------------------
TECH_DOMAINS = {
    "CloudNative": [
        "Kubernetes", "Docker", "container", "microservice", "serverless",
        "DevOps", "Istio", "Terraform", "service-mesh",
    ],
    "BigData": [
        "Hadoop", "Spark", "Flink", "Kafka", "data-warehouse", "data-lake",
        "ETL", "streaming", "MapReduce", "Elasticsearch",
    ],
    "AI": [
        "machine-learning", "deep-learning", "neural-network", "NLP",
        "computer-vision", "LLM", "GPT", "transformer", "OpenAI", "agent",
    ],
    "Blockchain": [
        "blockchain", "Ethereum", "Web3", "smart-contract", "DeFi",
        "cryptocurrency", "Solidity", "NFT",
    ],
    "Database": [
        "database", "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "NoSQL",
    ],
}

LANGUAGES = ["Python", "Go", "Rust", "TypeScript", "Java", "C++", "C"]


def structure_comparison(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate page-structure metrics per portal."""
    metrics = df.groupby("portal").agg({
        "word_count":  ["mean", "median"],
        "link_count":  ["mean", "median"],
        "image_count": ["mean", "median"],
        "script_count":["mean", "median"],
        "style_count": ["mean", "median"],
    }).round(2)
    metrics.columns = ["_".join(c) for c in metrics.columns]
    return metrics


def plot_radar(df: pd.DataFrame) -> None:
    """Normalised radar chart comparing Trending vs Topics on 5 dimensions."""
    metrics = structure_comparison(df)
    portals = df["portal"].unique()

    categories = ["Avg Words", "Avg Links", "Avg Images", "Avg Scripts", "Avg Styles"]
    raw = {
        "Avg Words":   metrics["word_count_mean"].values,
        "Avg Links":   metrics["link_count_mean"].values,
        "Avg Images":  metrics["image_count_mean"].values,
        "Avg Scripts": metrics["script_count_mean"].values,
        "Avg Styles":  metrics["style_count_mean"].values,
    }

    # Min-max normalisation per axis
    norm = {}
    for c in categories:
        v = raw[c]
        lo, hi = v.min(), v.max()
        norm[c] = (v - lo) / (hi - lo) if hi > lo else np.zeros_like(v)

    N = len(categories)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(9, 9), subplot_kw=dict(polar=True))
    colours = ["#2dba4e", "#0969da"]

    for i, portal in enumerate(portals):
        vals = [norm[c][i] for c in categories] + [norm[categories[0]][i]]
        ax.plot(angles, vals, "o-", linewidth=2.5, label=portal, color=colours[i])
        ax.fill(angles, vals, alpha=0.15, color=colours[i])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=11)
    ax.set_ylim(0, 1)
    ax.set_title("Trending vs Topics: Content Feature Comparison",
                 fontsize=14, fontweight="bold", pad=30)
    ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.1), fontsize=11)
    plt.tight_layout()

    out_path = OUTPUT_DIR / "portal_radar.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    print(f"[SAVE] {out_path}")
    plt.close()


def build_domain_language_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    For each row, check which tech domains and languages are hit;
    emit one (domain, language, portal) record per co-occurrence.
    """
    rows = []
    for _, rec in df.iterrows():
        kw = rec.get("keywords", {})
        if not isinstance(kw, dict):
            continue
        for domain, d_kws in TECH_DOMAINS.items():
            domain_hit = any(kw.get(k, 0) > 0 for k in d_kws)
            if domain_hit:
                for lang in LANGUAGES:
                    if kw.get(lang, 0) > 0:
                        rows.append({
                            "domain": domain,
                            "language": lang,
                            "portal": rec.get("portal", "Unknown"),
                        })
    return pd.DataFrame(rows)


def plot_domain_heatmap(dl_df: pd.DataFrame) -> None:
    """Draw the Domain × Language heat-map."""
    if dl_df.empty:
        print("  [WARN] No domain-language co-occurrences to plot.")
        return

    pivot = dl_df.groupby(["domain", "language"]).size().unstack(fill_value=0)
    for lang in LANGUAGES:
        if lang not in pivot.columns:
            pivot[lang] = 0
    pivot = pivot[LANGUAGES]  # fix column order

    plt.figure(figsize=(12, 7))
    sns.heatmap(
        pivot, annot=True, fmt="d", cmap="YlOrRd",
        linewidths=0.5, cbar_kws={"label": "Co-occurrence Count"},
    )
    plt.title("Technology Domain × Programming Language Cross Analysis",
              fontsize=14, fontweight="bold")
    plt.ylabel("Technology Domain", fontsize=12)
    plt.xlabel("Programming Language", fontsize=12)
    plt.tight_layout()

    out_path = OUTPUT_DIR / "domain_language_heatmap.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    print(f"[SAVE] {out_path}")
    plt.close()


def plot_box_comparison(df: pd.DataFrame) -> None:
    """2×2 box-plot grid comparing portals on numeric features."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))

    for ax, metric, title in zip(
        axes.flat,
        ["word_count", "link_count", "image_count", "script_count"],
        ["Description Length", "Link Count", "Image Count", "Script Count"],
    ):
        data = [
            df[df["portal"] == p][metric].dropna().values
            for p in df["portal"].unique()
        ]
        labels = df["portal"].unique()
        bp = ax.boxplot(data, tick_labels=labels, patch_artist=True)
        for patch, colour in zip(bp["boxes"], ["#2dba4e", "#0969da"]):
            patch.set_facecolor(colour)
            patch.set_alpha(0.6)
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.set_ylabel("Count")

    plt.suptitle("Trending vs Topics: Distribution Comparison",
                 fontsize=14, fontweight="bold")
    plt.tight_layout()

    out_path = OUTPUT_DIR / "portal_boxplot.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    print(f"[SAVE] {out_path}")
    plt.close()


def main() -> None:
    print("=" * 65)
    print("Step 4: Trending vs Topics + Domain×Language Cross Analysis")
    print("=" * 65)

    pkl_path = OUTPUT_DIR / "cleaned_data.pkl"
    if not pkl_path.exists():
        print(f"[ERROR] {pkl_path} not found. Run step1 first.")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_pickle(pkl_path)

    # ---- Structural comparison ----
    metrics = structure_comparison(df)
    print("\n[Structure Metrics]")
    print(metrics)
    metrics.to_csv(OUTPUT_DIR / "structure_metrics.csv")
    print(f"[SAVE] {OUTPUT_DIR / 'structure_metrics.csv'}")

    plot_radar(df)
    plot_box_comparison(df)

    # ---- Domain × Language cross ----
    dl_df = build_domain_language_matrix(df)
    if not dl_df.empty:
        plot_domain_heatmap(dl_df)
        dl_df.to_csv(OUTPUT_DIR / "domain_language_matrix.csv", index=False)
        print(f"[SAVE] {OUTPUT_DIR / 'domain_language_matrix.csv'}")
    else:
        print("[WARN] No domain-language matrix data.")

    print("[DONE] Step 4 complete.\n")


if __name__ == "__main__":
    main()
