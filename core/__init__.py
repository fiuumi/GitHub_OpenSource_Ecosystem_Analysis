"""
GitHub Crawler Core Package

Contains the main crawling engine and its components:
- fetcher: HTTP request handler
- parser: HTML content parser
- url_manager: URL queue and deduplication
- keyword_analyzer: Technology keyword scanner
- storage: Data persistence layer
- crawler: Main crawl engine orchestrator
"""

__all__ = [
    'Fetcher',
    'GitHubParser',
    'UrlManager',
    'KeywordAnalyzer',
    'Storage',
    'CrawlEngine',
]
