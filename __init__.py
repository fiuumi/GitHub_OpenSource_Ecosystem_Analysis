"""
GitHub Open Source Ecosystem Crawler

A modular web crawler for collecting GitHub Trending and Topics data
to support big data analysis of open source technology evolution.

Modules:
    core:       Crawling engine components
    config:     Target URLs and keyword dictionaries
    models:     Data structures
    utils:      Logging and helper utilities
    scripts:    Batch execution scripts

Usage:
    from core.crawler import CrawlEngine
    from config.targets import get_target_by_name

    target = get_target_by_name('gh_trending_python')
    engine = CrawlEngine(target)
    report = engine.run()
"""

__version__ = '1.0.0'
__author__ = 'GitHub Open Source Analysis Project'
