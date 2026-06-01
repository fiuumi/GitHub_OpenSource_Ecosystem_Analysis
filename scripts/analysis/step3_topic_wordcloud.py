#!/usr/bin/env python3
"""
Step 3: TF-IDF & Word Cloud Analysis
====================================
Performs English NLP on repository descriptions:
  - Pre-processing (lower-case, regex cleaning, stop-word removal)
  - TF-IDF (unigram + bigram)
  - Word-cloud generation (one per portal)

Input : output/analysis/cleaned_data.pkl
Output: output/analysis/wordcloud_trending.png
        output/analysis/wordcloud_topics.png
        output/analysis/tfidf_comparison.png
        output/analysis/tfidf_trending.csv
        output/analysis/tfidf_topics.csv
"""

import re
import sys
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from sklearn.feature_extraction.text import TfidfVectorizer

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

OUTPUT_DIR = PROJECT_ROOT / "output" / "analysis"

# ---------------------------------------------------------------------------
# Expanded English stop-word list (general + technology-flavoured filler)
# ---------------------------------------------------------------------------
STOPWORDS = set([
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of",
    "with", "by", "from", "as", "is", "was", "are", "be", "been", "have", "has",
    "had", "do", "does", "did", "will", "would", "could", "should", "may", "can",
    "this", "that", "these", "those", "i", "you", "he", "she", "it", "we", "they",
    "me", "him", "her", "us", "them", "my", "your", "his", "its", "our", "their",
    "github", "com", "http", "https", "www", "io", "org", "net", "co",
    "open", "source", "free", "software", "project", "tool", "library", "framework",
    "app", "application", "based", "using", "built", "made", "simple", "easy", "fast",
    "lightweight", "powerful", "modern", "new", "support", "supports", "supported",
    "api", "cli", "ui", "gui", "version", "amp", "lt", "gt", "quot", "nbsp",
    "all", "any", "each", "every", "some", "more", "most", "other", "such", "only",
    "own", "same", "so", "than", "too", "very", "just", "also", "back", "still",
    "well", "even", "much", "many", "up", "out", "down", "off", "over", "under",
    "not", "no", "yes", "get", "use", "used", "one", "two", "three", "first",
    "like", "way", "make", "see", "know", "take", "come", "go", "think", "say",
    "help", "build", "create", "add", "set", "run", "write", "read", "need", "want",
])


def preprocess(text: str) -> str:
    """Normalise and tokenise English description text."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    # Keep hyphens and slashes (common in tech terms), drop other punctuation
    text = re.sub(r"[^a-z0-9\s\-/]", " ", text)
    tokens = text.split()
    tokens = [t for t in tokens if len(t) > 2 and t not in STOPWORDS and not t.isdigit()]
    return " ".join(tokens)


def generate_wordcloud(df: pd.DataFrame, portal_name: str, out_path: Path) -> None:
    """Create and save a word-cloud image for the given portal."""
    subset = df[df["portal"] == portal_name]
    texts = subset["description"].apply(preprocess)
    all_text = " ".join(texts)

    if not all_text.strip():
        print(f"  [WARN] Empty text for portal={portal_name}, skipping word-cloud.")
        return

    wc = WordCloud(
        width=1600, height=900,
        background_color="white",
        max_words=200,
        colormap="tab10",
        relative_scaling=0.5,
        min_font_size=10,
        max_font_size=150,
    ).generate(all_text)

    plt.figure(figsize=(16, 9))
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    plt.title(f"GitHub {portal_name} — Technology Topic Cloud",
              fontsize=18, fontweight="bold", pad=20)
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    print(f"[SAVE] {out_path}")
    plt.close()


def compute_tfidf(df: pd.DataFrame, portal_name: str, top_n: int = 25) -> pd.DataFrame:
    """Compute mean TF-IDF scores for unigrams+bigrams on a portal subset."""
    subset = df[df["portal"] == portal_name]
    texts = subset["description"].apply(preprocess)
    texts = texts[texts.str.len() > 0]

    if len(texts) < 5:
        print(f"  [WARN] Too few documents for portal={portal_name} TF-IDF.")
        return pd.DataFrame()

    vectorizer = TfidfVectorizer(
        max_features=500,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.8,
    )
    matrix = vectorizer.fit_transform(texts)
    names = vectorizer.get_feature_names_out()
    scores = matrix.mean(axis=0).A1

    words = list(zip(names, scores))
    words.sort(key=lambda x: x[1], reverse=True)
    return pd.DataFrame(words[:top_n], columns=["keyword", "tfidf_score"])


def plot_tfidf_compare(trending: pd.DataFrame, topics: pd.DataFrame) -> None:
    """Side-by-side horizontal bar chart of top TF-IDF keywords."""
    fig, axes = plt.subplots(1, 2, figsize=(18, 10))

    for ax, df, name, colour in zip(
        axes, [trending, topics],
        ["Trending", "Topics"], ["#2dba4e", "#0969da"]
    ):
        if df.empty:
            ax.text(0.5, 0.5, "No Data", ha="center", va="center",
                    transform=ax.transAxes)
            continue
        top = df.head(20)
        ax.barh(range(len(top)), top["tfidf_score"],
                color=colour, edgecolor="white")
        ax.set_yticks(range(len(top)))
        ax.set_yticklabels(top["keyword"], fontsize=10)
        ax.invert_yaxis()
        ax.set_title(f"{name} — Top 20 TF-IDF Keywords",
                     fontsize=13, fontweight="bold")
        ax.set_xlabel("TF-IDF Score")

    plt.tight_layout()
    out_path = OUTPUT_DIR / "tfidf_comparison.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    print(f"[SAVE] {out_path}")
    plt.close()


def main() -> None:
    print("=" * 65)
    print("Step 3: TF-IDF & Word Cloud Analysis")
    print("=" * 65)

    pkl_path = OUTPUT_DIR / "cleaned_data.pkl"
    if not pkl_path.exists():
        print(f"[ERROR] {pkl_path} not found. Run step1 first.")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_pickle(pkl_path)

    # ---- Word clouds ----
    generate_wordcloud(df, "Trending", OUTPUT_DIR / "wordcloud_trending.png")
    generate_wordcloud(df, "Topics",   OUTPUT_DIR / "wordcloud_topics.png")

    # ---- TF-IDF ----
    t_tfidf = compute_tfidf(df, "Trending")
    p_tfidf = compute_tfidf(df, "Topics")

    if not t_tfidf.empty:
        t_tfidf.to_csv(OUTPUT_DIR / "tfidf_trending.csv", index=False)
        print(f"[SAVE] {OUTPUT_DIR / 'tfidf_trending.csv'}")
    if not p_tfidf.empty:
        p_tfidf.to_csv(OUTPUT_DIR / "tfidf_topics.csv", index=False)
        print(f"[SAVE] {OUTPUT_DIR / 'tfidf_topics.csv'}")

    plot_tfidf_compare(t_tfidf, p_tfidf)

    print("[DONE] Step 3 complete.\n")


if __name__ == "__main__":
    main()
