"""
GitHub Crawler - Crawl Target Configurations

Defines the 12 data sources (7 Trending + 5 Topics) with their metadata,
crawl parameters, and categorization labels.

Improvements:
  - Multi-page seed URL generation for Topics (page=1..N)
  - Multi-period seed URLs for Trending (daily/weekly/monthly)
  - follow_repo_links option for richer descriptions

Source: GitHub Open Source Ecosystem Evolution Analysis Design Document
Section 3.1 & 4.2
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TargetConfig:
    """Configuration for a single crawl target."""
    name: str                          # Internal identifier
    portal: str                        # 'Trending' or 'Topics'
    portal_type: str                   # 'trending' or 'topics'
    subcategory: str                   # Sub-label
    url: str                           # Base target URL
    max_pages: int = 35                # Maximum pages to crawl
    max_depth: int = 1                 # Maximum crawl depth
    delay: float = 2.0                 # Inter-request delay
    description: str = ""              # Human-readable description
    follow_repo_links: bool = False    # Whether to crawl individual repo pages
    pages_per_seed: int = 1            # Number of pagination pages per seed
    time_periods: List[str] = field(default_factory=list)  # e.g. ['daily','weekly']

    def __post_init__(self):
        """Ensure URL has proper scheme."""
        if not self.url.startswith(('http://', 'https://')):
            self.url = 'https://' + self.url

    def generate_seed_urls(self) -> List[str]:
        """
        Generate all seed URLs for this target.

        - Trending: adds ?since=daily/weekly/monthly variations
        - Topics:   adds ?page=N pagination URLs
        """
        urls = []
        base = self.url.rstrip('/')

        if self.portal_type == 'trending':
            periods = self.time_periods or ['daily']
            for period in periods:
                sep = '&' if '?' in base else '?'
                urls.append(f"{base}{sep}since={period}")

        elif self.portal_type == 'topics':
            for page in range(1, self.pages_per_seed + 1):
                sep = '&' if '?' in base else '?'
                urls.append(f"{base}{sep}page={page}")

        else:
            urls.append(base)

        return urls

    @property
    def output_dir_name(self) -> str:
        """Generate output directory name."""
        return self.name

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            'name': self.name,
            'portal': self.portal,
            'portal_type': self.portal_type,
            'subcategory': self.subcategory,
            'url': self.url,
            'max_pages': self.max_pages,
            'max_depth': self.max_depth,
            'delay': self.delay,
            'follow_repo_links': self.follow_repo_links,
            'pages_per_seed': self.pages_per_seed,
            'seed_urls': self.generate_seed_urls(),
        }


# ============================================================================
# Trending Series (7 targets) — multi-period for richer data
# ============================================================================
TRENDING_TARGETS: List[TargetConfig] = [
    TargetConfig(
        name="gh_trending_all",
        portal="Trending", portal_type="trending", subcategory="all",
        url="https://github.com/trending",
        max_pages=8, max_depth=1, delay=2.0,
        pages_per_seed=1,
        time_periods=["daily", "weekly", "monthly"],
        description="Trending repositories across all languages (daily+weekly+monthly)"
    ),
    TargetConfig(
        name="gh_trending_python",
        portal="Trending", portal_type="trending", subcategory="Python",
        url="https://github.com/trending/python",
        max_pages=6, max_depth=1, delay=2.0,
        pages_per_seed=1,
        time_periods=["daily", "weekly", "monthly"],
        description="Trending Python repositories"
    ),
    TargetConfig(
        name="gh_trending_go",
        portal="Trending", portal_type="trending", subcategory="Go",
        url="https://github.com/trending/go",
        max_pages=6, max_depth=1, delay=2.0,
        pages_per_seed=1,
        time_periods=["daily", "weekly", "monthly"],
        description="Trending Go repositories"
    ),
    TargetConfig(
        name="gh_trending_rust",
        portal="Trending", portal_type="trending", subcategory="Rust",
        url="https://github.com/trending/rust",
        max_pages=6, max_depth=1, delay=2.0,
        pages_per_seed=1,
        time_periods=["daily", "weekly", "monthly"],
        description="Trending Rust repositories"
    ),
    TargetConfig(
        name="gh_trending_ts",
        portal="Trending", portal_type="trending", subcategory="TypeScript",
        url="https://github.com/trending/typescript",
        max_pages=6, max_depth=1, delay=2.0,
        pages_per_seed=1,
        time_periods=["daily", "weekly", "monthly"],
        description="Trending TypeScript repositories"
    ),
    TargetConfig(
        name="gh_trending_java",
        portal="Trending", portal_type="trending", subcategory="Java",
        url="https://github.com/trending/java",
        max_pages=6, max_depth=1, delay=2.0,
        pages_per_seed=1,
        time_periods=["daily", "weekly", "monthly"],
        description="Trending Java repositories"
    ),
    TargetConfig(
        name="gh_trending_cpp",
        portal="Trending", portal_type="trending", subcategory="C++",
        url="https://github.com/trending/c%2B%2B",
        max_pages=6, max_depth=1, delay=2.0,
        pages_per_seed=1,
        time_periods=["daily", "weekly", "monthly"],
        description="Trending C++ repositories"
    ),
]

# ============================================================================
# Topics Series (5 targets) — multi-page pagination
# ============================================================================
TOPICS_TARGETS: List[TargetConfig] = [
    TargetConfig(
        name="gh_topics_ai",
        portal="Topics", portal_type="topics", subcategory="AI",
        url="https://github.com/topics/artificial-intelligence",
        max_pages=8, max_depth=1, delay=2.0,
        pages_per_seed=3,
        description="Artificial Intelligence topic repositories (3 pages)"
    ),
    TargetConfig(
        name="gh_topics_blockchain",
        portal="Topics", portal_type="topics", subcategory="Blockchain",
        url="https://github.com/topics/blockchain",
        max_pages=8, max_depth=1, delay=2.0,
        pages_per_seed=3,
        description="Blockchain topic repositories (3 pages)"
    ),
    TargetConfig(
        name="gh_topics_cloud",
        portal="Topics", portal_type="topics", subcategory="Cloud",
        url="https://github.com/topics/cloud-computing",
        max_pages=8, max_depth=1, delay=2.0,
        pages_per_seed=3,
        description="Cloud Computing topic repositories (3 pages)"
    ),
    TargetConfig(
        name="gh_topics_bigdata",
        portal="Topics", portal_type="topics", subcategory="BigData",
        url="https://github.com/topics/big-data",
        max_pages=8, max_depth=1, delay=2.0,
        pages_per_seed=3,
        description="Big Data topic repositories (3 pages)"
    ),
    TargetConfig(
        name="gh_topics_ml",
        portal="Topics", portal_type="topics", subcategory="ML",
        url="https://github.com/topics/machine-learning",
        max_pages=8, max_depth=1, delay=2.0,
        pages_per_seed=3,
        description="Machine Learning topic repositories (3 pages)"
    ),
]

# === All 12 Targets Combined ===
CRAWL_TARGETS: List[TargetConfig] = TRENDING_TARGETS + TOPICS_TARGETS

# === Quick Lookup Maps ===
TARGET_BY_NAME: dict = {t.name: t for t in CRAWL_TARGETS}
TARGET_BY_URL: dict = {t.url: t for t in CRAWL_TARGETS}


def get_target_by_name(name: str) -> Optional[TargetConfig]:
    """Retrieve target configuration by name."""
    return TARGET_BY_NAME.get(name)


def get_targets_by_portal(portal: str) -> List[TargetConfig]:
    """Filter targets by portal type ('Trending' or 'Topics')."""
    return [t for t in CRAWL_TARGETS if t.portal == portal]


def get_all_target_names() -> List[str]:
    """Return all target names."""
    return [t.name for t in CRAWL_TARGETS]


# === Validation ===
if __name__ == '__main__':
    print(f"Total crawl targets: {len(CRAWL_TARGETS)}")
    print(f"  Trending: {len(TRENDING_TARGETS)} (x3 time periods each)")
    print(f"  Topics:   {len(TOPICS_TARGETS)} (x3 pagination pages each)")
    print("\nSeed URLs per target:")
    for t in CRAWL_TARGETS:
        urls = t.generate_seed_urls()
        print(f"\n  [{t.portal:8s}] {t.name:25s} ({len(urls)} seeds):")
        for u in urls:
            print(f"    {u}")
