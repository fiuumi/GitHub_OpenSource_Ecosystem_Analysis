#!/usr/bin/env python3
"""
Step 2: Programming Language Heat Analysis
==========================================
Analyses the frequency of 15 programming languages across Trending & Topics.

Input : output/analysis/cleaned_data.pkl
Output: output/analysis/language_heat.png
        output/analysis/language_report.txt
"""

import sys
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless backend
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

OUTPUT_DIR = PROJECT_ROOT / "output" / "analysis"

# 15 programming languages tracked by the keyword dictionary
LANGUAGES = [
    "Python", "Go", "Rust", "TypeScript", "JavaScript", "Java",
    "C++", "C", "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R", "Dart"
]


def extract_language_hits(df: pd.DataFrame) -> pd.DataFrame:
    """
    Expand each row into one record per language hit.
    Returns DataFrame: language | portal | sub | count | url
    """
    rows = []
    for _, rec in df.iterrows():
        kw = rec.get("keywords", {})
        if not isinstance(kw, dict):
            continue
        for lang in LANGUAGES:
            cnt = kw.get(lang, 0)
            if cnt > 0:
                rows.append({
                    "language": lang,
                    "portal":   rec.get("portal", "Unknown"),
                    "sub":      rec.get("sub", "Unknown"),
                    "count":    cnt,
                    "url":      rec["url"],
                })
    return pd.DataFrame(rows)


def plot_results(lang_df: pd.DataFrame, global_top: pd.Series) -> None:
    """Draw two charts: global TOP15 + Trending-vs-Topics grouped bar."""
    if lang_df.empty:
        print("[WARN] No language data to plot.")
        return

    fig, axes = plt.subplots(2, 1, figsize=(14, 16))

    # ---- Chart 1: Global TOP 15 ----
    top15 = global_top.head(15)
    colours = plt.cm.viridis(np.linspace(0.2, 0.9, len(top15)))
    ax1 = axes[0]
    bars = ax1.barh(
        range(len(top15)), top15.values,
        color=colours, edgecolor="white", linewidth=0.5
    )
    ax1.set_yticks(range(len(top15)))
    ax1.set_yticklabels(top15.index, fontsize=12)
    ax1.invert_yaxis()
    ax1.set_xlabel("Total Keyword Hits", fontsize=12)
    ax1.set_title(
        "Top 15 Programming Languages on GitHub\n(Trending + Topics Combined)",
        fontsize=14, fontweight="bold"
    )
    for i, v in enumerate(top15.values):
        ax1.text(v + 0.3, i, str(int(v)), va="center", fontsize=10)

    # ---- Chart 2: Trending vs Topics ----
    ax2 = axes[1]
    pivot = lang_df.groupby(["language", "portal"])["count"].sum().unstack(fill_value=0)
    for col in ("Trending", "Topics"):
        if col not in pivot.columns:
            pivot[col] = 0

    pivot["total"] = pivot.sum(axis=1)
    top10 = pivot.sort_values("total", ascending=False).head(10).drop(columns=["total"])

    x = np.arange(len(top10))
    w = 0.35
    ax2.bar(x - w / 2, top10["Trending"], w, label="Trending",
            color="#2dba4e", edgecolor="white")
    ax2.bar(x + w / 2, top10["Topics"], w, label="Topics",
            color="#0969da", edgecolor="white")
    ax2.set_xticks(x)
    ax2.set_xticklabels(top10.index, rotation=45, ha="right", fontsize=11)
    ax2.set_ylabel("Keyword Hits", fontsize=12)
    ax2.set_title("Trending vs Topics: Language Heat Comparison",
                  fontsize=14, fontweight="bold")
    ax2.legend(fontsize=11)

    plt.tight_layout()
    out_path = OUTPUT_DIR / "language_heat.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    print(f"[SAVE] {out_path}")
    plt.close()


def generate_report(global_top: pd.Series, lang_df: pd.DataFrame) -> None:
    """Write a plain-text summary report."""
    out_path = OUTPUT_DIR / "language_report.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("=" * 55 + "\n")
        f.write("     Programming Language Heat Analysis\n")
        f.write("=" * 55 + "\n\n")

        f.write("[Global Top 15]\n")
        for i, (lang, cnt) in enumerate(global_top.head(15).items(), 1):
            f.write(f"  {i:2d}. {lang:<15s} {cnt:>4.0f} hits\n")

        f.write("\n[Trending vs Topics]\n")
        pivot = lang_df.groupby(["language", "portal"])["count"].sum().unstack(fill_value=0)
        for col in ("Trending", "Topics"):
            if col not in pivot.columns:
                pivot[col] = 0
        pivot["total"] = pivot.sum(axis=1)
        for lang, row in pivot.sort_values("total", ascending=False).head(10).iterrows():
            tr = row.get("Trending", 0)
            tp = row.get("Topics", 0)
            ratio = tr / (tr + tp) * 100 if (tr + tp) > 0 else 0
            f.write(f"  {lang:<15s}  Trending:{tr:>3.0f}  Topics:{tp:>3.0f}  "
                    f"Trending%:{ratio:>5.1f}%\n")

    print(f"[SAVE] {out_path}")


def main() -> None:
    print("=" * 65)
    print("Step 2: Programming Language Heat Analysis")
    print("=" * 65)

    pkl_path = OUTPUT_DIR / "cleaned_data.pkl"
    if not pkl_path.exists():
        print(f"[ERROR] {pkl_path} not found. Run step1 first.")
        sys.exit(1)

    df = pd.read_pickle(pkl_path)
    lang_df = extract_language_hits(df)

    if lang_df.empty:
        print("[ERROR] No language keyword hits found.")
        sys.exit(1)

    global_top = lang_df.groupby("language")["count"].sum().sort_values(ascending=False)

    plot_results(lang_df, global_top)
    generate_report(global_top, lang_df)

    print("[DONE] Step 2 complete.\n")


if __name__ == "__main__":
    main()
