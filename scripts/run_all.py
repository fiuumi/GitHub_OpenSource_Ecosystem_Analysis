#!/usr/bin/env python3
"""
GitHub Crawler — Full Pipeline: Crawl + Analysis
=================================================
Executes all 12 crawl tasks, then automatically runs all 5 analysis steps.

Usage:
    # Full pipeline (crawl + analysis)
    python scripts/run_all.py --analysis

    # Crawl only
    python scripts/run_all.py --no-analysis

    # Custom delay
    python scripts/run_all.py --analysis --delay 2.0

    # Partial crawl + analysis
    python scripts/run_all.py --analysis --limit 3
"""

import sys
import os
import argparse
import time
import subprocess
from pathlib import Path

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from core.crawler import MultiTargetCrawler
    from config.targets import CRAWL_TARGETS
    from utils.logger import setup_logging, get_logger
    from utils.helpers import ensure_dir, format_duration
except ImportError as e:
    print(f"Import error: {e}", file=sys.stderr)
    sys.exit(1)


def run_analysis_pipeline(output_dir: str) -> bool:
    """
    Run all 5 analysis scripts as separate subprocesses.
    Returns True if all succeeded.
    """
    print("\n" + "=" * 65)
    print("  AUTOMATIC ANALYSIS PIPELINE")
    print("=" * 65)

    script_dir = Path(__file__).resolve().parent / "analysis"
    steps = [
        ("Step 1: Data Integration & Cleaning",  "step1_data_integration.py"),
        ("Step 2: Language Heat Analysis",       "step2_language_analysis.py"),
        ("Step 3: TF-IDF & Word Cloud",          "step3_topic_wordcloud.py"),
        ("Step 4: Portal Comparison",            "step4_portal_comparison.py"),
        ("Step 5: Co-occurrence Network",        "step5_cooccurrence_network.py"),
    ]

    analysis_dir = Path(output_dir) / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)

    all_ok = True
    for label, script_name in steps:
        script_path = script_dir / script_name
        print(f"\n  [{label}]")
        print(f"  Script: {script_path}")

        if not script_path.exists():
            print(f"  [SKIP] Script not found: {script_path}")
            all_ok = False
            continue

        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(PROJECT_ROOT) if 'PROJECT_ROOT' in globals() else None,
                capture_output=False,
                text=True,
                timeout=300,
            )
            if result.returncode == 0:
                print(f"  [OK] {label} completed")
            else:
                print(f"  [FAIL] {label} exited with code {result.returncode}")
                all_ok = False
        except subprocess.TimeoutExpired:
            print(f"  [FAIL] {label} timed out")
            all_ok = False
        except Exception as e:
            print(f"  [FAIL] {label} error: {e}")
            all_ok = False

    print("\n" + "=" * 65)
    if all_ok:
        print("  All 5 analysis steps completed successfully!")
    else:
        print("  Some analysis steps failed. Check logs above.")
    print(f"  Results: {analysis_dir}")
    print("=" * 65)

    return all_ok


def main() -> int:
    """Run full pipeline: crawl + optional analysis."""
    parser = argparse.ArgumentParser(
        description='GitHub Crawler — Full Pipeline (Crawl + Analysis)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full pipeline: crawl all + analysis
  python scripts/run_all.py --analysis

  # Crawl only (skip analysis)
  python scripts/run_all.py --no-analysis

  # Fast test: first 2 targets + analysis
  python scripts/run_all.py --analysis --limit 2 --delay 1.5

  # Topics only + analysis
  python scripts/run_all.py --analysis --topics
        """.strip(),
    )

    # Target selection
    target_group = parser.add_mutually_exclusive_group()
    target_group.add_argument(
        '--topics', action='store_true',
        help='Crawl only 5 Topics targets'
    )
    target_group.add_argument(
        '--trending', action='store_true',
        help='Crawl only 7 Trending targets'
    )

    # Crawl parameters
    parser.add_argument(
        '--output-dir', '-o', default='./output',
        help='Base output directory'
    )
    parser.add_argument(
        '--delay', '-d', type=float, default=2.0,
        help='Request delay in seconds'
    )
    parser.add_argument(
        '--stop-on-error', action='store_true',
        help='Stop if any target fails'
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true',
        help='Verbose logging'
    )
    parser.add_argument(
        '--skip', type=int, default=0,
        help='Skip first N targets'
    )
    parser.add_argument(
        '--limit', type=int, default=0,
        help='Limit to N targets (0 = all)'
    )

    # Analysis control
    analysis_group = parser.add_mutually_exclusive_group()
    analysis_group.add_argument(
        '--analysis', '-a', action='store_true', default=True,
        help='Run analysis after crawl (default: True)'
    )
    analysis_group.add_argument(
        '--no-analysis', action='store_true',
        help='Skip analysis, crawl only'
    )

    args = parser.parse_args()

    # Determine if analysis should run
    run_analysis = args.analysis and not args.no_analysis

    # Setup
    setup_logging('debug' if args.verbose else 'info')
    logger = get_logger(__name__)

    ensure_dir(args.output_dir)

    # Select targets
    if args.topics:
        from config.targets import TOPICS_TARGETS as TARGETS
        target_label = "Topics (5)"
    elif args.trending:
        from config.targets import TRENDING_TARGETS as TARGETS
        target_label = "Trending (7)"
    else:
        TARGETS = list(CRAWL_TARGETS)
        target_label = "All (12)"

    targets = list(TARGETS)
    if args.skip > 0:
        targets = targets[args.skip:]
    if args.limit > 0:
        targets = targets[:args.limit]

    print("=" * 60)
    print("  GitHub Open Source Ecosystem — Full Pipeline")
    print("=" * 60)
    print(f"  Targets:     {target_label} -> {len(targets)} selected")
    print(f"  Output:      {args.output_dir}")
    print(f"  Delay:       {args.delay}s")
    print(f"  Analysis:    {'YES' if run_analysis else 'NO'}")
    print("=" * 60)
    print()

    # Override delays
    for t in targets:
        t.delay = args.delay

    # ---- Phase 1: Crawl ----
    start_time = time.time()

    crawler = MultiTargetCrawler(
        targets=targets,
        output_base_dir=args.output_dir,
        stop_on_error=args.stop_on_error,
        run_analysis=False,  # We'll handle analysis separately
    )
    results = crawler.run_all()

    crawl_elapsed = time.time() - start_time
    total_repos = sum(len(r.records) for r in results.values())

    print()
    print("=" * 60)
    print("  PHASE 1: CRAWL COMPLETE")
    print("=" * 60)
    print(f"  Duration:      {format_duration(crawl_elapsed)}")
    print(f"  Targets:       {len(targets)}")
    print(f"  Successful:    {len(results)}")
    print(f"  Total repos:   {total_repos}")
    print(f"  Output:        {args.output_dir}")
    print("=" * 60)

    # Per-target breakdown
    print("\n  Per-target results:")
    print(f"  {'#':>3} {'Target':<30} {'Records':>8} {'Status':>10}")
    print("  " + "-" * 55)
    for i, target in enumerate(targets, 1):
        name = target.name
        if name in results:
            count = len(results[name].records)
            status = "OK"
        else:
            count = 0
            status = "FAILED"
        print(f"  {i:>3} {name:<30} {count:>8} {status:>10}")

    # ---- Phase 2: Analysis ----
    if run_analysis and total_repos > 0:
        print()
        analysis_ok = run_analysis_pipeline(args.output_dir)

        total_elapsed = time.time() - start_time
        print(f"\n{'='*60}")
        print(f"  FULL PIPELINE COMPLETE")
        print(f"{'='*60}")
        print(f"  Total time:    {format_duration(total_elapsed)}")
        print(f"  Crawl:         {format_duration(crawl_elapsed)}")
        print(f"  Analysis:      {format_duration(total_elapsed - crawl_elapsed)}")
        print(f"  Repos:         {total_repos}")
        print(f"  Output:        {args.output_dir}/")
        print(f"  Analysis:      {args.output_dir}/analysis/")
        print(f"{'='*60}")
    elif run_analysis:
        print("\n[SKIP] No repository data to analyse.")
    else:
        print(f"\n[INFO] Analysis skipped (--no-analysis).")

    return 0 if len(results) == len(targets) else 1


if __name__ == '__main__':
    sys.exit(main())
