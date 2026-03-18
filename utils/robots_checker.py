"""
Robots.txt Checker Module

Checks if a URL can be fetched according to robots.txt rules.
"""

from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

_robots_cache: dict[str, RobotFileParser | None] = {}


def can_fetch(url: str, user_agent: str = "*") -> tuple[bool, str]:
    """
    Check if a URL can be fetched according to robots.txt.

    Args:
        url: The URL to check
        user_agent: User agent string (default: "*")

    Returns:
        Tuple of (can_fetch, reason)
    """
    parsed = urlparse(url)
    domain = parsed.netloc

    if domain not in _robots_cache:
        robots_url = f"{parsed.scheme}://{domain}/robots.txt"

        rp = RobotFileParser()
        rp.set_url(robots_url)

        try:
            rp.read()
            _robots_cache[domain] = rp
        except Exception as e:
            _robots_cache[domain] = None
            return True, f"Could not read robots.txt: {e}"

    robots_parser: RobotFileParser | None = _robots_cache.get(domain)

    if robots_parser is None:
        return True, "No robots.txt found"

    if robots_parser.can_fetch(user_agent, url):
        return True, "Allowed by robots.txt"
    else:
        return False, "Blocked by robots.txt"


def get_crawl_delay(url: str, user_agent: str = "*") -> float:
    """
    Get the crawl delay from robots.txt.

    Args:
        url: The URL to check
        user_agent: User agent string

    Returns:
        Crawl delay in seconds (0 if not specified)
    """
    parsed = urlparse(url)
    domain = parsed.netloc

    rp = _robots_cache.get(domain)

    if rp is None:
        return 0

    try:
        delay = rp.crawl_delay(user_agent)
        return float(delay) if delay else 0
    except Exception:
        return 0


def clear_cache():
    """Clear the robots.txt cache"""
    global _robots_cache
    _robots_cache = {}
