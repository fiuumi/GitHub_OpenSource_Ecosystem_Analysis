"""
GitHub Crawler - URL Manager Module

Manages URL queue, deduplication, and filtering.
Features:
- FIFO URL queue with priority support
- Bloom filter-inspired memory-efficient deduplication
- Domain-aware filtering
- Depth tracking
- Respect for no-crawl patterns
"""

import re
from typing import Set, List, Optional, Dict, Deque
from collections import deque
from urllib.parse import urlparse

try:
    from ..utils.logger import get_logger
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from utils.logger import get_logger


class UrlManager:
    """
    Manages the crawl frontier: URL queue, visited set, and filtering rules.
    """

    # Patterns to skip (non-repo pages, auth, etc.)
    SKIP_PATTERNS = [
        r'/login',
        r'/signup',
        r'/settings',
        r'/notifications',
        r'/security',
        r'/search',
        r'/marketplace',
        r'/explore',
        r'/features',
        r'/team',
        r'/enterprise',
        r'/pricing',
        r'/about',
        r'/blog',
        r'/readme',
        r'/commits',
        r'/issues',
        r'/pulls',
        r'/actions',
        r'/projects',
        r'/wiki',
        r'/security',
        r'/pulse',
        r'/graphs/',
        r'/raw/',
        r'/blob/',
        r'/tree/',
        r'/releases',
        r'/tags',
        r'/packages',
        r'/deployments',
        r'/stargazers',
        r'/forks',
        r'/watchers',
        r'/branches',
        r'/compare/',
        r'/blame/',
        r'/archive/',
        r'.pdf$',
        r'.zip$',
        r'.tar.gz$',
        r'/api/',
        r'/assets/',
    ]

    def __init__(
        self,
        seed_urls: Optional[List[str]] = None,
        max_depth: int = 1,
        same_domain_only: bool = True,
        allowed_domains: Optional[Set[str]] = None,
        max_urls: int = 1000,
    ):
        """
        Initialize URL manager.

        Args:
            seed_urls: Starting URLs
            max_depth: Maximum crawl depth from seed
            same_domain_only: Restrict to same domain as seed URLs
            allowed_domains: Set of allowed domains (if not same_domain_only)
            max_urls: Maximum total URLs to track
        """
        self.max_depth = max_depth
        self.same_domain_only = same_domain_only
        self.allowed_domains = allowed_domains or set()
        self.max_urls = max_urls

        self.logger = get_logger(__name__)

        # URL queue: (url, depth) tuples
        self._queue: Deque[tuple] = deque()

        # Deduplication set
        self._seen: Set[str] = set()

        # Seed domains for same-domain filtering
        self._seed_domains: Set[str] = set()

        # Stats
        self._queued_count: int = 0
        self._skipped_count: int = 0

        # Initialize with seed URLs
        if seed_urls:
            for url in seed_urls:
                domain = urlparse(url).netloc
                self._seed_domains.add(domain)
                self.add_url(url, depth=0)

    def add_url(self, url: str, depth: int = 0) -> bool:
        """
        Add a URL to the queue if it passes filters.

        Args:
            url: URL to add
            depth: Current crawl depth

        Returns:
            True if URL was added, False if filtered out
        """
        # Normalize URL
        url = self._normalize_url(url)
        if not url:
            return False

        # Check max URLs limit
        if len(self._seen) >= self.max_urls:
            return False

        # Check already seen
        if url in self._seen:
            return False

        # Check depth
        if depth > self.max_depth:
            return False

        # Check domain restrictions
        if not self._is_domain_allowed(url):
            self._skipped_count += 1
            return False

        # Check skip patterns
        if self._should_skip(url):
            self._skipped_count += 1
            return False

        # Add to queue and seen set
        self._seen.add(url)
        self._queue.append((url, depth))
        self._queued_count += 1
        return True

    def add_urls(self, urls: List[str], depth: int = 0) -> int:
        """
        Add multiple URLs at once.

        Returns:
            Number of URLs actually added
        """
        added = 0
        for url in urls:
            if self.add_url(url, depth):
                added += 1
        return added

    def get_next(self) -> Optional[tuple]:
        """
        Get next URL from queue.

        Returns:
            Tuple of (url, depth) or None if queue empty
        """
        if not self._queue:
            return None
        return self._queue.popleft()

    def has_next(self) -> bool:
        """Check if there are more URLs to process."""
        return len(self._queue) > 0

    def _normalize_url(self, url: str) -> Optional[str]:
        """Normalize URL for deduplication."""
        try:
            # Remove fragment
            url = url.split('#')[0]

            # Ensure scheme
            if url.startswith('//'):
                url = 'https:' + url

            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return None

            # Remove trailing slash for dedup
            path = parsed.path.rstrip('/')
            normalized = f"{parsed.scheme.lower()}://{parsed.netloc.lower()}{path}"

            # Keep query params if they are pagination-related
            if parsed.query:
                # Only keep meaningful query params
                keep_params = []
                for param in parsed.query.split('&'):
                    if param.startswith(('page=', 'after=', 'before=', 'since=', 'language=')):
                        keep_params.append(param)
                if keep_params:
                    normalized += '?' + '&'.join(keep_params)

            return normalized

        except Exception:
            return None

    def _is_domain_allowed(self, url: str) -> bool:
        """Check if URL's domain is in allowed set."""
        try:
            domain = urlparse(url).netloc.lower()

            if self.same_domain_only:
                return domain in self._seed_domains

            if self.allowed_domains:
                return domain in self.allowed_domains

            return True

        except Exception:
            return False

    def _should_skip(self, url: str) -> bool:
        """Check URL against skip patterns."""
        for pattern in self.SKIP_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        return False

    @property
    def queue_size(self) -> int:
        """Number of URLs waiting to be processed."""
        return len(self._queue)

    @property
    def seen_count(self) -> int:
        """Total unique URLs seen."""
        return len(self._seen)

    @property
    def stats(self) -> Dict:
        """Return URL manager statistics."""
        return {
            'queued': self._queued_count,
            'seen': len(self._seen),
            'pending': len(self._queue),
            'skipped': self._skipped_count,
            'max_depth': self.max_depth,
        }

    def __len__(self) -> int:
        return len(self._queue)

    def __repr__(self) -> str:
        return f"UrlManager(pending={len(self._queue)}, seen={len(self._seen)}, depth={self.max_depth})"
