#!/usr/bin/env python3
"""
Step 1: Data Integration & Cleaning (Optimized)
================================================
Integrates 12 crawl_report.json files, cleans data with smart dedup,
and produces a unified DataFrame. Key improvements:

  - Per-source dedup (keeps same repo from different sources)
  - Relaxed filtering to retain more records
  - Detailed cleaning statistics report

Input : output/<source_name>/crawl_report.json  (12 sources)
Output: output/analysis/cleaned_data.pkl
        output/analysis/cleaned_data.csv
        output/analysis/cleaning_report.txt
"""

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

DATA_SOURCES = {
    "gh_trending_all":       {"portal": "Trending", "sub": "all",        "type": "trending"},
    "gh_trending_python":    {"portal": "Trending", "sub": "Python",     "type": "trending"},
    "gh_trending_go":        {"portal": "Trending", "sub": "Go",         "type": "trending"},
    "gh_trending_rust":      {"portal": "Trending", "sub": "Rust",       "type": "trending"},
    "gh_trending_ts":        {"portal": "Trending", "sub": "TypeScript", "type": "trending"},
    "gh_trending_java":      {"portal": "Trending", "sub": "Java",       "type": "trending"},
    "gh_trending_cpp":       {"portal": "Trending", "sub": "C++",        "type": "trending"},
    "gh_topics_ai":          {"portal": "Topics",   "sub": "AI",         "type": "topics"},
    "gh_topics_blockchain":  {"portal": "Topics",   "sub": "Blockchain", "type": "topics"},
    "gh_topics_cloud":       {"portal": "Topics",   "sub": "Cloud",      "type": "topics"},
    "gh_topics_bigdata":     {"portal": "Topics",   "sub": "BigData",    "type": "topics"},
    "gh_topics_ml":          {"portal": "Topics",   "sub": "ML",         "type": "topics"},
}

OUTPUT_DIR = PROJECT_ROOT / "output" / "analysis"
RAW_DIR    = PROJECT_ROOT / "output"


def load_source(source_name: str, meta: dict) -> pd.DataFrame:
    """Load a single source's crawl_report.json and attach metadata."""
    path = RAW_DIR / source_name / "crawl_report.json"

    if not path.exists():
        print(f"  [WARN] File not found: {path}")
        return pd.DataFrame()

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    records = data.get("records", [])
    if not records:
        print(f"  [WARN] No records in: {path}")
        return pd.DataFrame()

    df = pd.DataFrame(records)

    # Attach metadata
    for key, val in meta.items():
        df[key] = val
    df["source_name"] = source_name

    # Derive repo identity
    if "repo_name" not in df.columns or df["repo_name"].isna().all():
        df["repo_name"] = df["title"].astype(str).str.replace(" GitHub", "", regex=False) \
                                     .str.replace(r"\s*\xc2\xb7\s*GitHub", "", regex=True) \
                                     .str.strip()
    if "owner" not in df.columns or df["owner"].isna().all():
        df["owner"] = df["repo_name"].str.split("/").str[0].str.strip()
    if "repo" not in df.columns or df["repo"].isna().all():
        df["repo"] = df["repo_name"].str.split("/").str[1].str.strip()

    print(f"  [OK] {source_name:<25s}  {len(df):4d} rows")
    return df


def integrate_and_clean() -> pd.DataFrame:
    """Load all sources, merge, clean, and save."""
    print("=" * 65)
    print("Step 1: Data Integration & Cleaning")
    print("=" * 65)

    # --- Load all sources ---
    dfs = []
    for name, meta in DATA_SOURCES.items():
        df = load_source(name, meta)
        if not df.empty:
            dfs.append(df)

    if not dfs:
        raise ValueError("No data found! Run the crawler first.")

    all_df = pd.concat(dfs, ignore_index=True)
    before = len(all_df)
    print(f"\n[INFO] Combined raw rows   : {before}")

    # --- Cleaning steps ---
    cleaning_log = []
    cleaning_log.append(f"Combined raw rows: {before}")

    # 1. Coerce keywords to dict
    def _ensure_dict(x):
        if isinstance(x, dict):
            return x
        if isinstance(x, str):
            try:
                return json.loads(x)
            except Exception:
                return {}
        return {}

    all_df["keywords"] = all_df["keywords"].apply(_ensure_dict)

    # 2. Drop duplicates BY SOURCE + REPO (keep same repo from different sources)
    # This is the key fix: per-source dedup, not global URL dedup
    dup_mask = all_df.duplicated(subset=["source_name", "repo_name"], keep="first")
    dup_count = dup_mask.sum()
    all_df = all_df[~dup_mask]
    cleaning_log.append(f"Per-source dedup    : dropped {dup_count} (same repo within same source)")
    print(f"[CLEAN] Per-source dedup   : -{dup_count} rows")

    # 3. Filter out junk pages (login, 404, etc.)
    mask_junk = all_df["title"].str.contains(
        "Sign in|Page not found|404|403 Forbidden",
        case=False, na=False, regex=True
    )
    junk_count = mask_junk.sum()
    all_df = all_df[~mask_junk]
    cleaning_log.append(f"Junk page filter    : dropped {junk_count}")
    print(f"[CLEAN] Junk page filter   : -{junk_count} rows")

    # 4. Keep records with any meaningful content
    # Relaxed: word_count > 5 OR has description OR has keywords hits
    def _has_content(row) -> bool:
        if row.get("word_count", 0) > 5:
            return True
        desc = str(row.get("description", "")).strip()
        if len(desc) > 5:
            return True
        kw = row.get("keywords", {})
        if isinstance(kw, dict) and any(v > 0 for v in kw.values()):
            return True
        return False

    content_mask = all_df.apply(_has_content, axis=1)
    content_dropped = (~content_mask).sum()
    all_df = all_df[content_mask]
    cleaning_log.append(f"Content filter      : dropped {content_dropped}")
    print(f"[CLEAN] Content filter     : -{content_dropped} rows")

    # 5. Derive active_keywords
    all_df["active_keywords"] = all_df["keywords"].apply(
        lambda d: {k: v for k, v in d.items() if v > 0} if isinstance(d, dict) else {}
    )

    after = len(all_df)
    cleaning_log.append(f"Final rows          : {after} (retention: {after/before*100:.1f}%)")
    print(f"\n[INFO] After cleaning      : {after} (retained {after/before*100:.1f}%)")

    # --- Distributions ---
    print(f"\n[INFO] Portal distribution:\n{all_df['portal'].value_counts().to_string()}")
    print(f"\n[INFO] Sub distribution:\n{all_df['sub'].value_counts().to_string()}")

    # Unique repos across all sources
    unique_repos = all_df["repo_name"].nunique()
    cross_source = all_df.groupby("repo_name")["source_name"].nunique()
    multi_source = (cross_source > 1).sum()
    print(f"\n[INFO] Unique repositories : {unique_repos}")
    print(f"[INFO] Cross-source repos  : {multi_source} (appear in 2+ sources)")

    # --- Save ---
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    pkl_path = OUTPUT_DIR / "cleaned_data.pkl"
    csv_path = OUTPUT_DIR / "cleaned_data.csv"

    all_df.to_pickle(pkl_path)
    df_csv = all_df.copy()
    df_csv["keywords"] = df_csv["keywords"].apply(json.dumps, ensure_ascii=False)
    df_csv["active_keywords"] = df_csv["active_keywords"].apply(json.dumps, ensure_ascii=False)
    df_csv.to_csv(csv_path, index=False, encoding="utf-8-sig")

    print(f"\n[SAVE] {pkl_path}")
    print(f"[SAVE] {csv_path}")

    # --- Write cleaning report ---
    report_path = OUTPUT_DIR / "cleaning_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("=" * 55 + "\n")
        f.write("       Data Cleaning Report\n")
        f.write("=" * 55 + "\n\n")
        for line in cleaning_log:
            f.write(f"  {line}\n")
        f.write(f"\n  Unique repositories : {unique_repos}\n")
        f.write(f"  Cross-source repos  : {multi_source}\n")
        f.write(f"\n  Portal distribution:\n")
        for portal, cnt in all_df["portal"].value_counts().items():
            f.write(f"    {portal:<12s} {cnt:>4d}\n")
    print(f"[SAVE] {report_path}")

    print("[DONE] Step 1 complete.\n")
    return all_df


if __name__ == "__main__":
    integrate_and_clean()
