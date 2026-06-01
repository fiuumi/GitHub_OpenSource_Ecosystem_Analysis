"""
GitHub Crawler - Main Crawl Engine

Orchestrates the crawling process by coordinating:
- Fetcher (HTTP requests)
- Parser (HTML parsing)
- UrlManager (URL queue & dedup)
- KeywordAnalyzer (keyword scanning)
- Storage (data persistence)

Improvements:
  - Multi-seed URL support via generate_seed_urls()
  - Repo detail page crawling for richer descriptions
  - Better deduplication (per-source repo_name)
  - Detailed per-page logging

Design Document Reference: Section 4
"""

import time
from datetime import datetime
from typing import List, Dict, Optional, Any

try:
    from ..config.targets import TargetConfig
    from ..models.repository import RepositoryData, CrawlReport, PageMetrics
    from ..utils.logger import get_logger, ProgressTracker
    from ..utils.helpers import format_duration
    from .fetcher import Fetcher
    from .parser import GitHubParser
    from .url_manager import UrlManager
    from .keyword_analyzer import KeywordAnalyzer
    from .storage import Storage
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from config.targets import TargetConfig
    from models.repository import RepositoryData, CrawlReport, PageMetrics
    from utils.logger import get_logger, ProgressTracker
    from utils.helpers import format_duration
    from core.fetcher import Fetcher
    from core.parser import GitHubParser
    from core.url_manager import UrlManager
    from core.keyword_analyzer import KeywordAnalyzer
    from core.storage import Storage


class CrawlEngine:
    """Main crawling engine that orchestrates the entire crawl process."""

    def __init__(
        self,
        target: TargetConfig,
        output_base_dir: str = './output',
        custom_delay: Optional[float] = None,
        custom_max_pages: Optional[int] = None,
        custom_max_depth: Optional[int] = None,
        verbose: bool = False,
    ):
        self.target = target
        self.output_base_dir = output_base_dir
        self.verbose = verbose

        self.delay = custom_delay or target.delay
        self.max_pages = custom_max_pages or target.max_pages
        self.max_depth = custom_max_depth or target.max_depth

        self.logger = get_logger(__name__)

        # Generate seed URLs
        seed_urls = target.generate_seed_urls()
        self.logger.info(f"Generated {len(seed_urls)} seed URLs for {target.name}")

        self.fetcher = Fetcher(delay=self.delay)
        self.parser = GitHubParser()
        self.url_manager = UrlManager(
            seed_urls=seed_urls,
            max_depth=self.max_depth,
            same_domain_only=True,
            max_urls=self.max_pages * 10,
        )
        self.analyzer = KeywordAnalyzer()
        self.storage = Storage(
            output_dir=output_base_dir,
            target_name=target.name,
        )

        self.stats: Dict[str, Any] = {
            'pages_crawled': 0,
            'repos_found': 0,
            'repos_valid': 0,
            'repos_deduped': 0,
            'requests_failed': 0,
            'start_time': None,
            'end_time': None,
            'errors': [],
        }
        # In-memory repo dedup: track repo_names we've already stored
        self._seen_repos: set = set()

    def run(self) -> CrawlReport:
        """Execute the full crawl."""
        self.logger.info("=" * 60)
        self.logger.info(f"Starting crawl: {self.target.name}")
        self.logger.info(f"  URL:    {self.target.url}")
        self.logger.info(f"  Seeds:  {len(self.target.generate_seed_urls())}")
        self.logger.info(f"  Portal: {self.target.portal} / {self.target.subcategory}")
        self.logger.info(f"  Pages:  {self.max_pages}")
        self.logger.info(f"  Depth:  {self.max_depth}")
        self.logger.info(f"  Delay:  {self.delay}s")
        self.logger.info(f"  Output: {self.storage.target_dir}")
        self.logger.info("=" * 60)

        self.stats['start_time'] = time.time()

        # Backup existing report
        self.storage.backup_existing()

        progress = ProgressTracker(
            total=self.max_pages,
            logger_name=__name__,
            label=f"Crawl [{self.target.name}]",
        )

        try:
            while self.url_manager.has_next() and self.stats['pages_crawled'] < self.max_pages:
                url_info = self.url_manager.get_next()
                if not url_info:
                    break

                url, depth = url_info

                # Fetch page
                success, content = self.fetcher.fetch(url)

                if not success:
                    self.stats['requests_failed'] += 1
                    self.stats['errors'].append(f"Failed to fetch {url}: {content}")
                    self.logger.warning(f"Fetch failed: {url} - {content}")
                    continue

                # Parse page
                try:
                    repos, metrics, child_urls = self.parser.parse_page(url, content)
                except Exception as e:
                    self.logger.error(f"Parse error for {url}: {e}")
                    self.stats['errors'].append(f"Parse error: {url}: {e}")
                    continue

                self.stats['pages_crawled'] += 1
                self.stats['repos_found'] += len(repos)

                # Process each repository
                valid_count = 0
                new_count = 0
                for repo in repos:
                    # Deduplicate by repo_name within this target
                    if repo.repo_name in self._seen_repos:
                        self.stats['repos_deduped'] += 1
                        continue
                    self._seen_repos.add(repo.repo_name)

                    # Enrich with metadata
                    repo.portal = self.target.portal
                    repo.subcategory = self.target.subcategory
                    repo.source_name = self.target.name
                    repo.crawl_time = datetime.now().isoformat()

                    # Apply page metrics
                    repo.word_count = metrics.word_count
                    repo.link_count = metrics.link_count
                    repo.image_count = metrics.image_count
                    repo.script_count = metrics.script_count
                    repo.style_count = metrics.style_count

                    # Run keyword analysis
                    kw_results = self.analyzer.analyze_repository(
                        repo.title, repo.description
                    )
                    repo.keywords = kw_results

                    if repo.has_valid_content:
                        self.storage.save_record(repo)
                        self.stats['repos_valid'] += 1
                        valid_count += 1
                        new_count += 1

                self.logger.info(
                    f"Page {self.stats['pages_crawled']}/{self.max_pages}: "
                    f"{url.split('?')[-1] if '?' in url else url.split('/')[-1]} -> "
                    f"{len(repos)} repos found, {new_count} new, {valid_count} valid"
                )

                # Add child URLs for depth crawling
                if depth < self.max_depth:
                    added = self.url_manager.add_urls(child_urls, depth=depth + 1)
                    if added > 0:
                        self.logger.debug(f"Added {added} child URLs at depth {depth + 1}")

                progress.update()

            progress.finish()

        except KeyboardInterrupt:
            self.logger.warning("Crawl interrupted by user")
            self.stats['errors'].append("Interrupted by user")
        except Exception as e:
            self.logger.error(f"Crawl error: {e}")
            self.stats['errors'].append(f"Fatal error: {str(e)}")
        finally:
            self.fetcher.close()

        elapsed = time.time() - self.stats['start_time']
        self.stats['end_time'] = time.time()

        report = self.storage.finalize_report(
            target_url=self.target.url,
            errors=self.stats['errors'],
        )

        self._print_summary(report, elapsed)
        return report

    def _print_summary(self, report: CrawlReport, elapsed: float) -> None:
        """Print crawl summary."""
        self.logger.info("")
        self.logger.info("=" * 60)
        self.logger.info("CRAWL SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Target:         {self.target.name}")
        self.logger.info(f"URL:            {self.target.url}")
        self.logger.info(f"Duration:       {format_duration(elapsed)}")
        self.logger.info(f"Pages crawled:  {self.stats['pages_crawled']}")
        self.logger.info(f"Repos found:    {self.stats['repos_found']}")
        self.logger.info(f"Repos deduped:  {self.stats['repos_deduped']}")
        self.logger.info(f"Repos valid:    {self.stats['repos_valid']}")
        self.logger.info(f"Requests failed:{self.stats['requests_failed']}")
        self.logger.info(f"Errors:         {len(self.stats['errors'])}")
        self.logger.info(f"Output:         {self.storage.target_dir}")
        self.logger.info(f"Records saved:  {len(report.records)}")
        self.logger.info("=" * 60)

    def get_stats(self) -> Dict[str, Any]:
        return {
            **self.stats,
            'target': self.target.to_dict(),
            'url_manager': self.url_manager.stats,
            'fetcher': self.fetcher.get_stats(),
            'storage': {
                'output_dir': str(self.storage.target_dir),
                'records_saved': self.storage.record_count,
            },
        }

    def __repr__(self) -> str:
        return f"CrawlEngine({self.target.name}, pages={self.stats['pages_crawled']}/{self.max_pages})"


class MultiTargetCrawler:
    """Crawls multiple targets sequentially, with optional post-crawl analysis."""

    def __init__(
        self,
        targets: List[TargetConfig],
        output_base_dir: str = './output',
        stop_on_error: bool = False,
        run_analysis: bool = False,
    ):
        self.targets = targets
        self.output_base_dir = output_base_dir
        self.stop_on_error = stop_on_error
        self.run_analysis = run_analysis
        self.logger = get_logger(__name__)

        self.results: Dict[str, CrawlReport] = {}
        self.errors: Dict[str, str] = {}
        self._analysis_errors: List[str] = []

    def run_all(self) -> Dict[str, CrawlReport]:
        """Run all targets sequentially."""
        total = len(self.targets)
        self.logger.info(f"Starting multi-target crawl: {total} targets")

        for i, target in enumerate(self.targets, 1):
            self.logger.info("")
            self.logger.info(f"{'='*60}")
            self.logger.info(f"[{i}/{total}] Processing: {target.name}")
            self.logger.info(f"{'='*60}")

            try:
                engine = CrawlEngine(
                    target=target,
                    output_base_dir=self.output_base_dir,
                )
                report = engine.run()
                self.results[target.name] = report

            except Exception as e:
                self.logger.error(f"Target failed: {target.name}: {e}")
                self.errors[target.name] = str(e)

                if self.stop_on_error:
                    self.logger.error("Stopping due to error (stop_on_error=True)")
                    break

        # Print crawl summary
        self._print_final_summary()

        # Run analysis if requested
        if self.run_analysis:
            self._run_analysis_pipeline()

        return self.results

    def _run_analysis_pipeline(self) -> None:
        """Execute all 5 analysis steps automatically."""
        print("\n" + "=" * 65)
        print("AUTOMATIC ANALYSIS PIPELINE")
        print("=" * 65)

        analysis_dir = Path(self.output_base_dir) / "analysis"
        analysis_dir.mkdir(parents=True, exist_ok=True)

        steps = [
            ("Step 1: Data Integration", "step1_data_integration"),
            ("Step 2: Language Heat",    "step2_language_analysis"),
            ("Step 3: TF-IDF & Word Cloud", "step3_topic_wordcloud"),
            ("Step 4: Portal Comparison",   "step4_portal_comparison"),
            ("Step 5: Co-occurrence Network", "step5_cooccurrence_network"),
        ]

        for label, module_name in steps:
            print(f"\n[{label}]")
            try:
                step_module = __import__(
                    f"scripts.analysis.{module_name}",
                    fromlist=["main"]
                )
                if hasattr(step_module, 'main'):
                    step_module.main()
                else:
                    # Fallback: run the module-level function
                    step_module.integrate_and_clean() if hasattr(step_module, 'integrate_and_clean') else None
                print(f"  [OK] {label} completed")
            except Exception as e:
                err_msg = f"{label} failed: {e}"
                self._analysis_errors.append(err_msg)
                print(f"  [FAIL] {err_msg}")

        # Print analysis summary
        print("\n" + "=" * 65)
        print("ANALYSIS PIPELINE COMPLETE")
        print("=" * 65)
        if self._analysis_errors:
            print(f"Errors: {len(self._analysis_errors)}")
            for e in self._analysis_errors:
                print(f"  - {e}")
        else:
            print("All 5 analysis steps completed successfully.")
        print(f"Results: {analysis_dir}")
        print("=" * 65)

    def _print_final_summary(self) -> None:
        """Print summary of all targets."""
        self.logger.info("")
        self.logger.info("=" * 60)
        self.logger.info("MULTI-TARGET CRAWL COMPLETE")
        self.logger.info("=" * 60)
        self.logger.info(f"Total targets:   {len(self.targets)}")
        self.logger.info(f"Successful:      {len(self.results)}")
        self.logger.info(f"Failed:          {len(self.errors)}")

        total_repos = sum(len(r.records) for r in self.results.values())
        self.logger.info(f"Total repos:     {total_repos}")

        if self.results:
            self.logger.info("\nSuccessful targets:")
            for name, report in self.results.items():
                self.logger.info(f"  {name:30s} - {len(report.records):4d} records")

        if self.errors:
            self.logger.info("\nFailed targets:")
            for name, error in self.errors.items():
                self.logger.info(f"  {name:30s} - {error}")

        self.logger.info("=" * 60)

    def __repr__(self) -> str:
        return f"MultiTargetCrawler(targets={len(self.targets)}, completed={len(self.results)})"
