"""
GitHub Crawler - HTML Parser Module

Parses GitHub Trending and Topics pages to extract repository information.
Uses BeautifulSoup for robust HTML parsing.

Target page structures:
- Trending: article.Box-row elements containing repo cards
- Topics: article.border rounded elements containing repo cards

Design Document Reference: Section 2.1 - Target Website Technical Verification
"""

import re
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag

try:
    from ..models.repository import RepositoryData, PageMetrics
    from ..utils.logger import get_logger
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from models.repository import RepositoryData, PageMetrics
    from utils.logger import get_logger


class GitHubParser:
    """
    Parser for GitHub Trending and Topics pages.
    Extracts repository cards with title, description, stars, language, etc.
    """

    # CSS selectors for different page types
    SELECTORS = {
        'trending': {
            'repo_cards': 'article.Box-row',
            'title': 'h2 a',
            'description': 'p[class*="col"]',
            'stars': 'a[href*="stargazers"]',
            'language': 'span[itemprop="programmingLanguage"]',
            'topic_tags': 'a.topic-tag',
        },
        'topics': {
            'repo_cards': 'article.border.rounded, article[class*="border"]',
            'title': 'h3 a, h2 a',
            'description': 'p[class*="color-fg-default"], .border-bottom p',
            'stars': 'a[href*="stargazers"]',
            'language': 'span[itemprop="programmingLanguage"]',
            'topic_tags': 'a[href*="/topics/"]',
        },
    }

    def __init__(self):
        self.logger = get_logger(__name__)

    def detect_page_type(self, url: str, soup: BeautifulSoup) -> str:
        """
        Detect whether the page is Trending or Topics type.

        Args:
            url: Page URL
            soup: Parsed HTML

        Returns:
            'trending' or 'topics'
        """
        path = urlparse(url).path.lower()

        if '/trending' in path:
            return 'trending'
        elif '/topics/' in path:
            return 'topics'

        # Fallback: check content structure
        if soup.select_one('article.Box-row'):
            return 'trending'
        elif soup.select_one('article.border.rounded'):
            return 'topics'

        return 'trending'  # Default

    def parse_page(self, url: str, html: str) -> Tuple[List[RepositoryData], PageMetrics, List[str]]:
        """
        Parse a full page and extract all repository cards.

        Args:
            url: Page URL
            html: Raw HTML content

        Returns:
            Tuple of (list of RepositoryData, page metrics, list of child URLs)
        """
        soup = BeautifulSoup(html, 'lxml')
        page_type = self.detect_page_type(url, soup)

        # Calculate page-level metrics
        metrics = self._calculate_page_metrics(soup)

        # Extract all repository cards
        repos = self._extract_repo_cards(url, soup, page_type)

        # Extract navigation/pagination links
        child_urls = self._extract_links(url, soup)

        self.logger.info(f"Parsed {url}: found {len(repos)} repos, {metrics.link_count} links")

        return repos, metrics, child_urls

    def _calculate_page_metrics(self, soup: BeautifulSoup) -> PageMetrics:
        """Calculate page-level metrics (links, images, scripts, styles, words)."""
        # Count links
        links = soup.find_all('a', href=True)
        link_count = len(links)

        # Count images
        images = soup.find_all('img')
        image_count = len(images)

        # Count scripts
        scripts = soup.find_all('script')
        script_count = len(scripts)

        # Count stylesheets and style tags
        styles = soup.find_all('link', rel='stylesheet')
        style_tags = soup.find_all('style')
        style_count = len(styles) + len(style_tags)

        # Count words (visible text only)
        visible_text = self._get_visible_text(soup)
        word_count = len(visible_text.split())

        return PageMetrics(
            word_count=word_count,
            link_count=link_count,
            image_count=image_count,
            script_count=script_count,
            style_count=style_count,
        )

    def _get_visible_text(self, soup: BeautifulSoup) -> str:
        """Extract visible text from HTML (excluding scripts, styles, etc.)."""
        # Remove script and style elements
        for script in soup(["script", "style", "noscript", "iframe", "canvas"]):
            script.decompose()

        # Get text
        text = soup.get_text(separator=' ')

        # Clean whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)

        return text

    def _extract_repo_cards(self, base_url: str, soup: BeautifulSoup, page_type: str) -> List[RepositoryData]:
        """Extract all repository cards from the page."""
        selectors = self.SELECTORS.get(page_type, self.SELECTORS['trending'])
        cards = soup.select(selectors['repo_cards'])

        repos: List[RepositoryData] = []
        for card in cards:
            try:
                repo = self._parse_repo_card(base_url, card, selectors)
                if repo and repo.repo_name:  # Only keep cards with valid repo names
                    repos.append(repo)
            except Exception as e:
                self.logger.debug(f"Failed to parse repo card: {e}")
                continue

        return repos

    def _parse_repo_card(self, base_url: str, card: Tag, selectors: Dict[str, str]) -> Optional[RepositoryData]:
        """Parse a single repository card element."""
        # Extract title and URL
        title_elem = card.select_one(selectors['title'])
        if not title_elem:
            return None

        # Title may be in format "owner / repo" or "owner/repo"
        raw_title = title_elem.get_text(strip=True)
        # Normalize title
        title = raw_title.replace(' / ', '/').replace('\n', '').replace('  ', ' ')

        # Repository URL
        href = title_elem.get('href', '')
        repo_url = urljoin(base_url, href) if href else base_url
        # Clean URL: remove query params
        repo_url = repo_url.split('?')[0]

        # Extract description
        desc_elem = card.select_one(selectors['description'])
        description = ''
        if desc_elem:
            description = desc_elem.get_text(strip=True)

        # Extract stars (optional)
        stars_elem = card.select_one(selectors['stars'])
        stars = ''
        if stars_elem:
            stars = stars_elem.get_text(strip=True)

        # Extract primary language (optional)
        lang_elem = card.select_one(selectors['language'])
        language = ''
        if lang_elem:
            language = lang_elem.get_text(strip=True)

        # Build repository data
        repo = RepositoryData(
            title=f"{title} GitHub",
            description=description,
            url=repo_url,
        )

        # Add language to description for keyword analysis
        if language:
            repo.description = f"{repo.description} {language}".strip()

        return repo

    def _extract_links(self, base_url: str, soup: BeautifulSoup) -> List[str]:
        """
        Extract all relevant links from the page.
        Filters to same-domain links only.
        """
        links: List[str] = []
        base_domain = urlparse(base_url).netloc

        for a in soup.find_all('a', href=True):
            href = a['href']
            # Skip anchors, javascript, mailto
            if href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                continue

            # Make absolute
            absolute = urljoin(base_url, href)
            parsed = urlparse(absolute)

            # Same domain only
            if parsed.netloc != base_domain:
                continue

            # Skip non-HTML resources
            path_lower = parsed.path.lower()
            if any(path_lower.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.css', '.js', '.ico']):
                continue

            # Clean URL
            clean = absolute.split('#')[0]
            if clean not in links:
                links.append(clean)

        return links

    def extract_repo_detail(self, url: str, html: str) -> RepositoryData:
        """
        Parse a repository detail page for full description.
        Used when following links to repo pages for more detailed info.
        """
        soup = BeautifulSoup(html, 'lxml')

        # Try to get description from meta tag first
        desc = ''
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            desc = meta_desc.get('content', '')

        # Fallback to about section
        if not desc:
            about = soup.select_one('.repository-content .BorderGrid-cell p')
            if about:
                desc = about.get_text(strip=True)

        # Topic tags
        topics = []
        for topic in soup.select('a[href*="/topics/"]'):
            topic_text = topic.get_text(strip=True)
            if topic_text:
                topics.append(topic_text)

        # Build description with topics
        full_desc = desc
        if topics:
            full_desc = f"{desc} {' '.join(topics)}"

        # Get title from page title
        title = ''
        title_elem = soup.find('title')
        if title_elem:
            title = title_elem.get_text(strip=True)

        return RepositoryData(
            title=title,
            description=full_desc.strip(),
            url=url,
        )

    @staticmethod
    def is_pagination_link(url: str) -> bool:
        """Check if URL is a pagination link."""
        return 'page=' in url or '?after=' in url

    @staticmethod
    def is_repo_page(url: str) -> bool:
        """Check if URL is a repository page."""
        path = urlparse(url).path.strip('/')
        parts = path.split('/')
        # Repo pages: github.com/owner/repo (2 parts after domain)
        return len(parts) == 2 and parts[0] and parts[1] and parts[1] not in [
            'trending', 'topics', 'search', 'explore', 'marketplace',
            'login', 'signup', 'settings', 'notifications',
        ]

    def get_next_page_url(self, base_url: str, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract next page URL from pagination.
        For Topics pages with 'Load more...' or pagination.
        """
        # Look for rel="next" link
        next_link = soup.find('a', attrs={'rel': 'next'})
        if next_link and next_link.get('href'):
            return urljoin(base_url, next_link['href'])

        # Look for pagination with 'after' cursor
        for link in soup.find_all('a', href=True):
            href = link['href']
            if 'after=' in href:
                return urljoin(base_url, href)

        return None
