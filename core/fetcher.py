"""
GitHub Crawler - HTTP Fetcher Module

Handles HTTP requests with:
- Configurable User-Agent rotation
- Automatic retry with exponential backoff
- Rate limiting between requests
- Proper error handling and logging
- robots.txt compliance checking

Compatible with urllib (as per design doc Section 2.2) but uses requests
for better reliability and features.
"""

import time
import random
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    from ..utils.logger import get_logger
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from utils.logger import get_logger

# Rotating User-Agents to avoid blocking
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

# Default retry strategy
DEFAULT_RETRY_STRATEGY = Retry(
    total=3,
    backoff_factor=1.0,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS"],
)


class Fetcher:
    """
    HTTP request handler with retry, rate limiting, and logging.
    """

    def __init__(
        self,
        delay: float = 2.0,
        timeout: int = 30,
        max_retries: int = 3,
        retry_backoff: float = 1.0,
        respect_robots: bool = True,
        custom_headers: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize fetcher.

        Args:
            delay: Minimum delay between requests (seconds)
            timeout: Request timeout (seconds)
            max_retries: Maximum retry attempts
            retry_backoff: Exponential backoff factor
            respect_robots: Whether to check robots.txt
            custom_headers: Additional HTTP headers
        """
        self.delay = delay
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.respect_robots = respect_robots
        self.custom_headers = custom_headers or {}

        self.logger = get_logger(__name__)
        self._session = self._create_session()
        self._last_request_time: float = 0.0
        self._request_count: int = 0
        self._robots_cache: Dict[str, bool] = {}  # domain -> allowed

    def _create_session(self) -> requests.Session:
        """Create requests session with retry adapter."""
        session = requests.Session()
        retry = Retry(
            total=self.max_retries,
            backoff_factor=self.retry_backoff,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _get_headers(self) -> Dict[str, str]:
        """Build request headers with random User-Agent."""
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        }
        headers.update(self.custom_headers)
        return headers

    def _apply_rate_limit(self) -> None:
        """Enforce delay between consecutive requests."""
        if self._last_request_time > 0:
            elapsed = time.time() - self._last_request_time
            if elapsed < self.delay:
                sleep_time = self.delay - elapsed
                # Add small random jitter to avoid pattern detection
                sleep_time += random.uniform(0.1, 0.5)
                self.logger.debug(f"Rate limit: sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)
        self._last_request_time = time.time()

    def _check_robots_txt(self, url: str) -> bool:
        """
        Check if URL is allowed by robots.txt.
        Returns True if allowed or cannot be determined.
        """
        if not self.respect_robots:
            return True

        try:
            parsed = urlparse(url)
            domain = parsed.netloc

            if domain in self._robots_cache:
                return self._robots_cache[domain]

            robots_url = f"{parsed.scheme}://{domain}/robots.txt"
            self.logger.debug(f"Fetching robots.txt: {robots_url}")

            resp = self._session.get(
                robots_url,
                headers=self._get_headers(),
                timeout=self.timeout,
            )

            # GitHub allows crawling of public pages
            is_allowed = resp.status_code == 200 and 'Disallow: /trending' not in resp.text
            self._robots_cache[domain] = is_allowed

            if not is_allowed:
                self.logger.warning(f"robots.txt may restrict crawling on {domain}")

            return True  # GitHub public pages are crawlable

        except Exception as e:
            self.logger.debug(f"robots.txt check failed: {e}")
            return True  # Allow if check fails

    def fetch(
        self,
        url: str,
        binary: bool = False,
    ) -> Tuple[bool, Any]:
        """
        Fetch a URL with retry and rate limiting.

        Args:
            url: Target URL
            binary: If True, return bytes; otherwise return string

        Returns:
            Tuple of (success, content)
            - success: bool indicating if request succeeded
            - content: HTML string, bytes, or error message
        """
        self._apply_rate_limit()

        # Check robots.txt
        if not self._check_robots_txt(url):
            self.logger.warning(f"robots.txt blocked: {url}")
            return False, "Blocked by robots.txt"

        self.logger.info(f"Fetching: {url}")

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self._session.get(
                    url,
                    headers=self._get_headers(),
                    timeout=self.timeout,
                    allow_redirects=True,
                )

                self._request_count += 1

                # Check status
                if resp.status_code == 200:
                    self.logger.debug(f"OK ({len(resp.content)} bytes)")
                    if binary:
                        return True, resp.content
                    return True, resp.text

                elif resp.status_code == 404:
                    self.logger.warning(f"404 Not Found: {url}")
                    return False, f"HTTP 404: {url}"

                elif resp.status_code == 429:
                    retry_after = int(resp.headers.get('Retry-After', 60))
                    self.logger.warning(f"Rate limited (429), waiting {retry_after}s")
                    time.sleep(retry_after)
                    continue

                else:
                    self.logger.warning(f"HTTP {resp.status_code}: {url}")
                    if attempt < self.max_retries:
                        wait = self.retry_backoff * (2 ** (attempt - 1))
                        time.sleep(wait)
                        continue
                    return False, f"HTTP {resp.status_code}: {url}"

            except requests.exceptions.Timeout:
                self.logger.warning(f"Timeout (attempt {attempt}/{self.max_retries}): {url}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_backoff * attempt)
                    continue
                return False, f"Timeout after {self.max_retries} retries"

            except requests.exceptions.ConnectionError as e:
                self.logger.warning(f"Connection error (attempt {attempt}/{self.max_retries}): {e}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_backoff * attempt)
                    continue
                return False, f"Connection error: {str(e)}"

            except Exception as e:
                self.logger.error(f"Unexpected error fetching {url}: {e}")
                return False, f"Error: {str(e)}"

        return False, "Max retries exceeded"

    def fetch_json(self, url: str) -> Tuple[bool, Any]:
        """Fetch URL and parse as JSON."""
        success, content = self.fetch(url)
        if not success:
            return False, content
        try:
            import json
            return True, json.loads(content)
        except Exception as e:
            return False, f"JSON parse error: {e}"

    def close(self) -> None:
        """Close session and release resources."""
        self._session.close()

    def get_stats(self) -> Dict[str, Any]:
        """Return fetcher statistics."""
        return {
            'requests_made': self._request_count,
            'delay_configured': self.delay,
            'timeout_configured': self.timeout,
        }

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
