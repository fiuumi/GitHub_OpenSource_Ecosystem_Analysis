#!/usr/bin/env bash
# =============================================================================
# GitHub Open Source Ecosystem — One-shot Analysis Pipeline
# =============================================================================
# Runs all 5 analysis steps sequentially:
#   Step 1: Data integration & cleaning
#   Step 2: Programming language heat analysis
#   Step 3: TF-IDF & word-cloud generation
#   Step 4: Trending vs Topics comparison + domain×language cross
#   Step 5: Co-occurrence network analysis
#
# Prerequisites:
#   - Crawler output exists in ../../output/<source_name>/crawl_report.json
#   - Python dependencies installed: pandas, numpy, matplotlib, seaborn,
#     nltk, scikit-learn, wordcloud, networkx
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================"
echo "  GitHub Open Source Ecosystem Analysis"
echo "============================================"
echo ""

# ---- Step 1 ----
echo "[1/5] Data Integration & Cleaning ..."
python step1_data_integration.py
echo ""

# ---- Step 2 ----
echo "[2/5] Programming Language Heat Analysis ..."
python step2_language_analysis.py
echo ""

# ---- Step 3 ----
echo "[3/5] TF-IDF & Word Cloud Analysis ..."
python step3_topic_wordcloud.py
echo ""

# ---- Step 4 ----
echo "[4/5] Trending vs Topics + Domain×Language Cross Analysis ..."
python step4_portal_comparison.py
echo ""

# ---- Step 5 ----
echo "[5/5] Co-occurrence Network Analysis ..."
python step5_cooccurrence_network.py
echo ""

# ---- Summary ----
echo "============================================"
echo "  All 5 analysis steps complete!"
echo "  Results: ../../output/analysis/"
echo "============================================"
