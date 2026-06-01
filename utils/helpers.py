"""
GitHub Crawler - Helper Utilities

Common utility functions used across modules.
"""

import os
import re
import time
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse, urljoin, unquote


def sanitize_filename(name: str) -> str:
    """
    Convert a string to a safe filename.
    Removes/replaces characters that are invalid in file paths.
    """
    # Replace URL-encoded characters
    name = unquote(name)
    # Replace path separators and other unsafe chars
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)
    # Limit length
    return name[:100]


def ensure_dir(path: str) -> str:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path

    Returns:
        The directory path
    """
    os.makedirs(path, exist_ok=True)
    return path


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"


def is_same_domain(url1: str, url2: str) -> bool:
    """Check if two URLs belong to the same domain."""
    try:
        return urlparse(url1).netloc == urlparse(url2).netloc
    except Exception:
        return False


def normalize_url(base_url: str, link: str) -> Optional[str]:
    """
    Normalize a relative URL to absolute URL.

    Args:
        base_url: Base page URL
        link: Potentially relative link

    Returns:
        Absolute URL or None if invalid
    """
    try:
        absolute = urljoin(base_url, link)
        parsed = urlparse(absolute)
        # Only keep http/https URLs
        if parsed.scheme not in ('http', 'https'):
            return None
        # Remove fragment
        return absolute.split('#')[0]
    except Exception:
        return None


def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        return urlparse(url).netloc
    except Exception:
        return ""


def current_timestamp() -> str:
    """Return current ISO format timestamp."""
    return datetime.now().isoformat()


def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text with ellipsis if too long."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def rate_limit_delay(last_request_time: float, min_delay: float) -> float:
    """
    Calculate delay needed to maintain rate limit.

    Args:
        last_request_time: Timestamp of last request
        min_delay: Minimum delay between requests (seconds)

    Returns:
        Actual delay applied
    """
    if last_request_time <= 0:
        return 0.0

    elapsed = time.time() - last_request_time
    if elapsed < min_delay:
        sleep_time = min_delay - elapsed
        time.sleep(sleep_time)
        return sleep_time
    return 0.0


# === Validation ===
if __name__ == '__main__':
    print(f"sanitize: {sanitize_filename('hello/world<test>.txt')}")
    print(f"duration: {format_duration(125.5)}")
    print(f"normalize: {normalize_url('https://github.com/trending', '/repo/owner')}")
    print(f"timestamp: {current_timestamp()}")
