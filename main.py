#!/usr/bin/env python3
"""
GitHub Open Source Ecosystem Crawler - Main Entry Point

A modular web crawler for collecting GitHub Trending and Topics data
to support big data analysis of open source technology evolution.

Usage:
    # Single target
    python main.py "https://github.com/trending/python" --max-pages 30 --delay 2.0

    # Named target
    python main.py --target gh_trending_python

    # All 12 targets
    python main.py --all

    # Topics only
    python main.py --topics

    # Trending only
    python main.py --trending

Design Document:
    GitHub Open Source Software Technology Ecological Evolution Trend Big Data Analysis
    -- Based on GitHub Trending & Topics Multi-source Data Collection and Mining Design
"""

import argparse
import sys
import os

# Add package to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from core.crawler import CrawlEngine, MultiTargetCrawler
    from config.targets import (
        CRAWL_TARGETS,
        TRENDING_TARGETS,
        TOPICS_TARGETS,
        get_target_by_name,
        get_all_target_names,
    )
    from utils.logger import setup_logging, get_logger
    from utils.helpers import ensure_dir
except ImportError as e:
    print(f"Import error: {e}", file=sys.stderr)
    print("Make sure you're running from the project root directory.", file=sys.stderr)
    sys.exit(1)


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description='GitHub Open Source Ecosystem Crawler',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Crawl single URL
  python main.py "https://github.com/trending/python" --max-pages 30

  # Crawl named target
  python main.py --target gh_trending_python

  # Crawl all 12 targets
  python main.py --all --delay 2.0

  # List available targets
  python main.py --list

  # Crawl with custom output directory
  python main.py --all --output-dir ./my_output
        """.strip(),
    )

    # Target specification (mutually exclusive group)
    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument(
        'url',
        nargs='?',
        help='Target URL to crawl (e.g., https://github.com/trending/python)',
    )
    target_group.add_argument(
        '--target',
        '-t',
        choices=get_all_target_names(),
        metavar='NAME',
        help='Crawl a predefined target by name',
    )
    target_group.add_argument(
        '--all',
        action='store_true',
        help='Crawl all 12 predefined targets',
    )
    target_group.add_argument(
        '--trending',
        action='store_true',
        help='Crawl all 7 Trending targets',
    )
    target_group.add_argument(
        '--topics',
        action='store_true',
        help='Crawl all 5 Topics targets',
    )
    target_group.add_argument(
        '--list',
        '-l',
        action='store_true',
        help='List all available targets and exit',
    )

    # Crawl parameters
    parser.add_argument(
        '--max-pages',
        '-p',
        type=int,
        default=30,
        help='Maximum pages to crawl (default: 30)',
    )
    parser.add_argument(
        '--max-depth',
        '-d',
        type=int,
        default=1,
        help='Maximum crawl depth (default: 1)',
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=2.0,
        help='Delay between requests in seconds (default: 2.0)',
    )

    # Output options
    parser.add_argument(
        '--output-dir',
        '-o',
        default='./output',
        help='Base output directory (default: ./output)',
    )
    parser.add_argument(
        '--name',
        '-n',
        help='Custom name for output subdirectory (used with URL mode)',
    )

    # Control options
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose/debug logging',
    )
    parser.add_argument(
        '--stop-on-error',
        action='store_true',
        help='Stop if a target fails (for --all mode)',
    )

    return parser


def list_targets() -> None:
    """Print all available targets."""
    print("\nAvailable Crawl Targets:")
    print("=" * 70)
    print(f"{'Name':<25} {'Portal':<8} {'Subcategory':<15} {'URL'}")
    print("-" * 70)

    for t in CRAWL_TARGETS:
        print(f"{t.name:<25} {t.portal:<8} {t.subcategory:<15} {t.url}")

    print("=" * 70)
    print(f"\nTotal: {len(CRAWL_TARGETS)} targets ({len(TRENDING_TARGETS)} Trending + {len(TOPICS_TARGETS)} Topics)")
    print()


def crawl_single_target(
    target,
    output_dir: str,
    max_pages: int,
    max_depth: int,
    delay: float,
    verbose: bool,
) -> None:
    """Crawl a single target."""
    engine = CrawlEngine(
        target=target,
        output_base_dir=output_dir,
        custom_max_pages=max_pages,
        custom_max_depth=max_depth,
        custom_delay=delay,
        verbose=verbose,
    )
    report = engine.run()

    print(f"\nCompleted: {target.name}")
    print(f"  Records: {len(report.records)}")
    print(f"  Output:  {output_dir}/{target.name}/crawl_report.json")


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # List mode
    if args.list:
        list_targets()
        return 0

    # Setup logging
    log_level = 'debug' if args.verbose else 'info'
    setup_logging(log_level)
    logger = get_logger(__name__)

    # Ensure output directory exists
    ensure_dir(args.output_dir)

    logger.info("GitHub Open Source Ecosystem Crawler")
    logger.info(f"Output directory: {args.output_dir}")

    # Determine targets
    targets = []

    if args.url:
        # Direct URL mode
        from config.targets import TargetConfig
        target_name = args.name or f"custom_{abs(hash(args.url)) % 10000}"
        target = TargetConfig(
            name=target_name,
            portal="Custom",
            portal_type="custom",
            subcategory="custom",
            url=args.url,
            max_pages=args.max_pages,
            max_depth=args.max_depth,
            delay=args.delay,
        )
        targets = [target]

    elif args.target:
        # Named target
        target = get_target_by_name(args.target)
        if not target:
            print(f"Error: Unknown target '{args.target}'", file=sys.stderr)
            return 1
        targets = [target]

    elif args.all:
        targets = CRAWL_TARGETS

    elif args.trending:
        targets = TRENDING_TARGETS

    elif args.topics:
        targets = TOPICS_TARGETS

    if not targets:
        print("Error: No targets specified", file=sys.stderr)
        return 1

    # Execute crawl
    if len(targets) == 1:
        # Single target
        target = targets[0]
        crawl_single_target(
            target=target,
            output_dir=args.output_dir,
            max_pages=args.max_pages if args.url else target.max_pages,
            max_depth=args.max_depth if args.url else target.max_depth,
            delay=args.delay if args.url else target.delay,
            verbose=args.verbose,
        )
    else:
        # Multiple targets
        crawler = MultiTargetCrawler(
            targets=targets,
            output_base_dir=args.output_dir,
            stop_on_error=args.stop_on_error,
        )
        results = crawler.run_all()

        # Summary
        total_records = sum(len(r.records) for r in results.values())
        print(f"\n{'='*60}")
        print(f"ALL CRAWLS COMPLETE")
        print(f"{'='*60}")
        print(f"Targets:        {len(targets)}")
        print(f"Total records:  {total_records}")
        print(f"Output dir:     {args.output_dir}")
        print(f"{'='*60}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
