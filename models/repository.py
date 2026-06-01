"""
GitHub Crawler - Data Models

Defines the data structures for crawled repository information.
All fields align with the Data Field Mapping in Design Document Section 2.3.

Output Format (JSON):
{
    "title": str,           # Page title (contains owner/repo)
    "description": str,     # Repository one-line description
    "word_count": int,      # Total word count of page text
    "link_count": int,      # Number of internal links
    "image_count": int,     # Number of images
    "script_count": int,    # Number of JS files
    "style_count": int,     # Number of CSS files
    "keywords": dict,       # {keyword: hit_count}
    "url": str,             # Page URL
    "crawl_time": str,      # ISO format timestamp
    "portal": str,          # 'Trending' or 'Topics'
    "subcategory": str,     # Sub-label (e.g., 'Python', 'AI')
}
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime
import json


@dataclass
class PageMetrics:
    """Page-level metrics extracted from HTML."""
    word_count: int = 0
    link_count: int = 0
    image_count: int = 0
    script_count: int = 0
    style_count: int = 0

    def to_dict(self) -> Dict[str, int]:
        return asdict(self)


@dataclass
class RepositoryData:
    """
    Single repository crawl result.
    Maps to the design document's data field specification (Section 2.3).
    """
    # Primary fields (from HTML)
    title: str = ""
    description: str = ""
    word_count: int = 0
    link_count: int = 0
    image_count: int = 0
    script_count: int = 0
    style_count: int = 0
    keywords: Dict[str, int] = field(default_factory=dict)
    url: str = ""

    # Metadata (added by crawler)
    crawl_time: str = ""
    portal: str = ""           # 'Trending' or 'Topics'
    subcategory: str = ""      # e.g., 'Python', 'AI'
    source_name: str = ""      # e.g., 'gh_trending_python'

    # Extracted fields (computed)
    repo_name: str = ""        # "owner/repo"
    owner: str = ""            # Repository owner
    repo: str = ""             # Repository name

    def __post_init__(self):
        """Auto-generate crawl timestamp if not provided."""
        if not self.crawl_time:
            self.crawl_time = datetime.now().isoformat()
        # Extract repo info from title
        self._extract_repo_info()

    def _extract_repo_info(self) -> None:
        """Extract owner/repo from title string like 'owner/repo GitHub'."""
        if not self.title:
            return
        # Title format: "owner/repo GitHub" or "owner/repo · GitHub"
        clean = self.title.replace(' GitHub', '').replace(' \xc2\xb7 GitHub', '').strip()
        parts = clean.split('/')
        if len(parts) >= 2:
            self.repo_name = clean
            self.owner = parts[0].strip()
            self.repo = parts[1].strip() if len(parts) > 1 else ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to flat dictionary for JSON serialization."""
        return {
            'title': self.title,
            'description': self.description,
            'word_count': self.word_count,
            'link_count': self.link_count,
            'image_count': self.image_count,
            'script_count': self.script_count,
            'style_count': self.style_count,
            'keywords': self.keywords,
            'url': self.url,
            'crawl_time': self.crawl_time,
            'portal': self.portal,
            'subcategory': self.subcategory,
            'source_name': self.source_name,
            'repo_name': self.repo_name,
            'owner': self.owner,
            'repo': self.repo,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RepositoryData':
        """Create instance from dictionary."""
        return cls(
            title=data.get('title', ''),
            description=data.get('description', ''),
            word_count=data.get('word_count', 0),
            link_count=data.get('link_count', 0),
            image_count=data.get('image_count', 0),
            script_count=data.get('script_count', 0),
            style_count=data.get('style_count', 0),
            keywords=data.get('keywords', {}),
            url=data.get('url', ''),
            crawl_time=data.get('crawl_time', ''),
            portal=data.get('portal', ''),
            subcategory=data.get('subcategory', ''),
            source_name=data.get('source_name', ''),
        )

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @property
    def has_valid_content(self) -> bool:
        """Check if the record has meaningful content."""
        return (
            len(self.title) > 0
            and not any(x in self.title.lower() for x in ['sign in', 'page not found', '404'])
            and self.word_count > 10
        )

    def __repr__(self) -> str:
        return f"RepositoryData({self.repo_name or self.url}, words={self.word_count}, links={self.link_count})"


class CrawlReport:
    """
    Aggregated crawl report containing multiple repository records.
    Maps to the 'crawl_report.json' output file in the design document.
    """

    def __init__(self, target_name: str = "", target_url: str = ""):
        self.target_name = target_name
        self.target_url = target_url
        self.records: List[RepositoryData] = []
        self.start_time: str = datetime.now().isoformat()
        self.end_time: str = ""
        self.total_pages_crawled: int = 0
        self.errors: List[str] = []

    def add_record(self, record: RepositoryData) -> None:
        """Add a repository record to the report."""
        self.records.append(record)

    def add_error(self, error_msg: str) -> None:
        """Record an error message."""
        self.errors.append(f"[{datetime.now().isoformat()}] {error_msg}")

    def finalize(self) -> None:
        """Mark the report as complete."""
        self.end_time = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert full report to dictionary."""
        return {
            'target_name': self.target_name,
            'target_url': self.target_url,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'total_pages_crawled': self.total_pages_crawled,
            'total_records': len(self.records),
            'errors': self.errors,
            'records': [r.to_dict() for r in self.records],
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize report to JSON."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def save(self, filepath: str) -> None:
        """Save report to JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.to_json())

    @classmethod
    def load(cls, filepath: str) -> 'CrawlReport':
        """Load report from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        report = cls(data.get('target_name', ''), data.get('target_url', ''))
        report.start_time = data.get('start_time', '')
        report.end_time = data.get('end_time', '')
        report.total_pages_crawled = data.get('total_pages_crawled', 0)
        report.errors = data.get('errors', [])
        for rec in data.get('records', []):
            report.add_record(RepositoryData.from_dict(rec))
        return report

    @property
    def valid_records(self) -> List[RepositoryData]:
        """Return only records with valid content."""
        return [r for r in self.records if r.has_valid_content]

    def __len__(self) -> int:
        return len(self.records)

    def __repr__(self) -> str:
        return f"CrawlReport({self.target_name}, records={len(self.records)}, pages={self.total_pages_crawled})"
