"""
GitHub Crawler - Keyword Analyzer Module

Scans text content (titles, descriptions) against the unified keyword dictionary
to count technology keyword occurrences.

Supports:
- Case-insensitive matching
- Whole-word matching (avoiding partial matches)
- Keyword categorization by dimension
- Co-occurrence tracking

Design Document Reference: Section 4.1 - Unified Keyword Dictionary
"""

import re
from typing import Dict, List, Set, Tuple, Optional
from collections import Counter

try:
    from ..config.keywords import ALL_KEYWORDS, KEYWORD_CATEGORIES, get_keyword_category
    from ..utils.logger import get_logger
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from config.keywords import ALL_KEYWORDS, KEYWORD_CATEGORIES, get_keyword_category
    from utils.logger import get_logger


class KeywordAnalyzer:
    """
    Analyzes text content for technology keyword occurrences.
    """

    def __init__(self, keywords: Optional[List[str]] = None):
        """
        Initialize analyzer with keyword list.

        Args:
            keywords: Custom keyword list (defaults to ALL_KEYWORDS from config)
        """
        self.keywords = keywords or ALL_KEYWORDS
        self.logger = get_logger(__name__)

        # Build optimized regex patterns for each keyword
        self._patterns: Dict[str, re.Pattern] = {}
        for kw in self.keywords:
            # Escape special regex chars, handle variants
            escaped = re.escape(kw)
            # Create word-boundary pattern for whole-word matching
            # Allow hyphens within words (e.g., "machine-learning")
            pattern = r'(?:^[\s\b\-]|\b)' + escaped + r'(?:[\s\b\-]$|\b)'
            self._patterns[kw] = re.compile(pattern, re.IGNORECASE)

        # Category mapping cache
        self._category_cache: Dict[str, str] = {}

    def analyze_text(self, text: str) -> Dict[str, int]:
        """
        Scan text for all keyword occurrences.

        Args:
            text: Input text to analyze

        Returns:
            Dictionary of {keyword: hit_count}
        """
        if not text:
            return {kw: 0 for kw in self.keywords}

        results: Dict[str, int] = {}

        for kw, pattern in self._patterns.items():
            matches = len(pattern.findall(text))
            results[kw] = matches

        return results

    def analyze_repository(self, title: str, description: str) -> Dict[str, int]:
        """
        Analyze a repository's title and description.

        Args:
            title: Repository title
            description: Repository description

        Returns:
            Dictionary of {keyword: hit_count}
        """
        combined = f"{title} {description}"
        return self.analyze_text(combined)

    def get_active_keywords(self, results: Dict[str, int]) -> Dict[str, int]:
        """
        Filter to only keywords with positive counts.

        Args:
            results: Full keyword results dict

        Returns:
            Dictionary of {keyword: count} for hits only
        """
        return {k: v for k, v in results.items() if v > 0}

    def get_category_distribution(self, results: Dict[str, int]) -> Dict[str, int]:
        """
        Aggregate keyword hits by category.

        Args:
            results: Keyword results dict

        Returns:
            Dictionary of {category: total_hits}
        """
        distribution: Dict[str, int] = {}
        for kw, count in results.items():
            if count > 0:
                cat = self._get_category(kw)
                distribution[cat] = distribution.get(cat, 0) + count
        return distribution

    def get_top_keywords(self, results: Dict[str, int], n: int = 10) -> List[Tuple[str, int]]:
        """
        Get top N keywords by hit count.

        Args:
            results: Keyword results dict
            n: Number of top keywords to return

        Returns:
            List of (keyword, count) tuples, sorted descending
        """
        active = self.get_active_keywords(results)
        return Counter(active).most_common(n)

    def find_cooccurrences(self, results: Dict[str, int]) -> List[Tuple[str, str]]:
        """
        Find pairs of keywords that co-occur (both have hits).

        Args:
            results: Keyword results dict

        Returns:
            List of (keyword1, keyword2) tuples
        """
        active = list(self.get_active_keywords(results).keys())
        from itertools import combinations
        return list(combinations(sorted(active), 2))

    def _get_category(self, keyword: str) -> str:
        """Get cached category for a keyword."""
        if keyword not in self._category_cache:
            self._category_cache[keyword] = get_keyword_category(keyword)
        return self._category_cache[keyword]

    def batch_analyze(self, texts: List[Tuple[str, str, str]]) -> List[Dict[str, int]]:
        """
        Analyze multiple repositories in batch.

        Args:
            texts: List of (url, title, description) tuples

        Returns:
            List of keyword result dictionaries
        """
        results = []
        for url, title, desc in texts:
            kw_results = self.analyze_repository(title, desc)
            results.append(kw_results)
        return results

    def get_summary_stats(self, all_results: List[Dict[str, int]]) -> Dict:
        """
        Compute summary statistics across multiple documents.

        Args:
            all_results: List of keyword result dicts from multiple pages

        Returns:
            Summary statistics dictionary
        """
        total_hits = Counter()
        doc_frequency = Counter()

        for result in all_results:
            for kw, count in result.items():
                if count > 0:
                    total_hits[kw] += count
                    doc_frequency[kw] += 1

        return {
            'total_keywords_tracked': len(self.keywords),
            'total_documents': len(all_results),
            'unique_keywords_found': len(total_hits),
            'total_keyword_hits': sum(total_hits.values()),
            'top_keywords': total_hits.most_common(20),
            'keyword_by_category': {
                cat: sum(total_hits[kw] for kw in kws)
                for cat, kws in KEYWORD_CATEGORIES.items()
            },
            'document_frequency': doc_frequency.most_common(20),
        }

    def __repr__(self) -> str:
        return f"KeywordAnalyzer(keywords={len(self.keywords)}, categories={len(KEYWORD_CATEGORIES)})"
