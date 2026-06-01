#!/usr/bin/env python3
"""
Step 5: Technology Keyword Co-occurrence Network
=================================================
Builds a weighted undirected graph from keyword co-occurrences,
computes centrality metrics, detects communities (connected components),
and generates publication-quality network plots.

Input : output/analysis/cleaned_data.pkl
Output: output/analysis/cooccurrence_network.png
        output/analysis/network_trending.png
        output/analysis/network_topics.png
        output/analysis/cooccurrence_edges.csv
        output/analysis/network_report.txt
"""

import sys
from pathlib import Path
from collections import Counter
from itertools import combinations

import pandas as pd
import numpy as np
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

OUTPUT_DIR = PROJECT_ROOT / "output" / "analysis"

# ---------------------------------------------------------------------------
# Keywords to include as network nodes (representative subset)
# ---------------------------------------------------------------------------
NETWORK_KEYWORDS = [
    # Languages
    "Python", "Go", "Rust", "TypeScript", "Java", "C++",
    # Cloud native
    "Kubernetes", "Docker", "microservice", "serverless",
    # Big data
    "Hadoop", "Spark", "Flink", "Kafka",
    # AI
    "machine-learning", "deep-learning", "LLM", "GPT", "NLP",
    # Blockchain
    "blockchain", "Web3", "smart-contract", "DeFi",
    # Database
    "PostgreSQL", "MongoDB", "Redis",
]


def build_network(df: pd.DataFrame, min_co: int = 2) -> tuple:
    """
    Count co-occurrences of NETWORK_KEYWORDS across all rows
    and build a NetworkX graph with edges >= min_co.
    Returns (graph, co_counter).
    """
    co = Counter()
    for _, rec in df.iterrows():
        kw = rec.get("keywords", {})
        if not isinstance(kw, dict):
            continue
        present = [k for k in NETWORK_KEYWORDS if kw.get(k, 0) > 0]
        for a, b in combinations(sorted(present), 2):
            co[(a, b)] += 1

    G = nx.Graph()
    for (a, b), w in co.items():
        if w >= min_co:
            G.add_edge(a, b, weight=w)

    G.remove_nodes_from(list(nx.isolates(G)))
    return G, co


def analyse_network(G: nx.Graph) -> dict:
    """Return topological metrics + centrality rankings."""
    if len(G.nodes) == 0:
        return {"nodes": 0, "edges": 0}

    metrics = {
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "density": nx.density(G),
        "avg_clustering": nx.average_clustering(G),
        "components": nx.number_connected_components(G),
    }

    deg = nx.degree_centrality(G)
    metrics["top_degree"] = sorted(deg.items(), key=lambda x: x[1], reverse=True)[:15]

    bet = nx.betweenness_centrality(G)
    metrics["top_betweenness"] = sorted(bet.items(), key=lambda x: x[1], reverse=True)[:10]

    return metrics


def plot_network(G: nx.Graph, out_path: Path) -> None:
    """Render the network with community colours and centrality-sized nodes."""
    if len(G.nodes) == 0:
        print(f"  [WARN] Empty graph — skipping {out_path.name}")
        return

    plt.figure(figsize=(18, 14))
    pos = nx.spring_layout(G, k=3.5, iterations=100, seed=42)

    degrees = dict(G.degree())
    node_sizes = [degrees[n] * 350 + 250 for n in G.nodes()]

    edge_weights = [G[u][v]["weight"] for u, v in G.edges()]
    ew_max = max(edge_weights) if edge_weights else 1
    edge_widths = [w / ew_max * 4 + 0.5 for w in edge_weights]

    # Colour by connected component (community)
    comps = list(nx.connected_components(G))
    cmap = plt.cm.Set3(np.linspace(0, 1, max(len(comps), 1)))
    nc_map = {}
    for i, comp in enumerate(comps):
        for n in comp:
            nc_map[n] = cmap[i % len(cmap)]
    node_colours = [nc_map[n] for n in G.nodes()]

    nx.draw_networkx_nodes(
        G, pos, node_size=node_sizes, node_color=node_colours,
        alpha=0.88, edgecolors="white", linewidths=1.5,
    )
    nx.draw_networkx_edges(
        G, pos, width=edge_widths, alpha=0.35, edge_color="gray",
    )
    nx.draw_networkx_labels(G, pos, font_size=11, font_weight="bold")

    plt.title("GitHub Open Source Technology Co-occurrence Network",
              fontsize=16, fontweight="bold", pad=20)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    print(f"[SAVE] {out_path}")
    plt.close()


def write_report(metrics: dict, out_path: Path) -> None:
    """Write a plain-text network-analysis report."""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("=" * 55 + "\n")
        f.write("   Technology Co-occurrence Network Report\n")
        f.write("=" * 55 + "\n\n")
        f.write("[Basic Metrics]\n")
        f.write(f"  Nodes:       {metrics.get('nodes', 0)}\n")
        f.write(f"  Edges:       {metrics.get('edges', 0)}\n")
        f.write(f"  Density:     {metrics.get('density', 0):.4f}\n")
        f.write(f"  Clustering:  {metrics.get('avg_clustering', 0):.4f}\n")
        f.write(f"  Components:  {metrics.get('components', 0)}\n\n")

        f.write("[Degree Centrality Top 15]\n")
        for i, (n, c) in enumerate(metrics.get("top_degree", []), 1):
            f.write(f"  {i:2d}. {n:<25s} {c:.4f}\n")

        f.write("\n[Betweenness Centrality Top 10]\n")
        for i, (n, c) in enumerate(metrics.get("top_betweenness", []), 1):
            f.write(f"  {i:2d}. {n:<25s} {c:.4f}\n")
    print(f"[SAVE] {out_path}")


def main() -> None:
    print("=" * 65)
    print("Step 5: Technology Keyword Co-occurrence Network")
    print("=" * 65)

    pkl_path = OUTPUT_DIR / "cleaned_data.pkl"
    if not pkl_path.exists():
        print(f"[ERROR] {pkl_path} not found. Run step1 first.")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_pickle(pkl_path)

    # ---- Full network ----
    G, co = build_network(df, min_co=2)
    print(f"[INFO] Full network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    metrics = analyse_network(G)

    # Save top edges
    edges_df = pd.DataFrame([
        {"kw1": a, "kw2": b, "weight": w}
        for (a, b), w in co.most_common(100)
    ])
    edges_df.to_csv(OUTPUT_DIR / "cooccurrence_edges.csv", index=False)
    print(f"[SAVE] {OUTPUT_DIR / 'cooccurrence_edges.csv'}")

    plot_network(G, OUTPUT_DIR / "cooccurrence_network.png")
    write_report(metrics, OUTPUT_DIR / "network_report.txt")

    # ---- Per-portal sub-networks ----
    for portal in ("Trending", "Topics"):
        sub = df[df["portal"] == portal]
        if len(sub) > 5:
            G_sub, _ = build_network(sub, min_co=1)
            if G_sub.number_of_nodes() > 0:
                plot_network(G_sub, OUTPUT_DIR / f"network_{portal.lower()}.png")

    print("[DONE] Step 5 complete.\n")


if __name__ == "__main__":
    main()
