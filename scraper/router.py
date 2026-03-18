"""
URL Router Module

Determines which scraper to use for each URL.
Routes URLs based on site type and complexity.
"""

from typing import Literal
from urllib.parse import urlparse

from app.logger import logger
from utils.validators import is_novel_url, is_youtube_url

from scraper.core.engine_registry import DEFAULT_FALLBACK_CHAINS

# Type alias for router results
RouterResult = Literal[
    "skip", "novel", "simple_http", "playwright", "playwright_alt", "playwright_tls", "cloudscraper", "wikipedia"
]


# Wikipedia and wiki sites
WIKI_SITES = [
    "wikipedia.org",
    "wiktionary.org",
    "wikimedia.org",
    "wikibooks.org",
    "wikiversity.org",
    "wikiquote.org",
    "wikisource.org",
    "wikinews.org",
    "wikivoyage.org",
]


# List of sites that require headless browser (heavy/JS sites)
HEAVY_SITES = [
    "amazon.com",
    "aws.amazon.com",
    "twitter.com",
    "x.com",
    "facebook.com",
    "fb.com",
    "instagram.com",
    "linkedin.com",
    "netflix.com",
    "login",
    "signin",
    "/admin/",
    "/dashboard/",
]


# Sites that work better with playwright_alt (anti-detection)
ALTERNATE_UA_SITES = [
    "wikipedia.org",
    "wiktionary.org",
    "reddit.com",
]


# Sites protected by Cloudflare that need cloudscraper
CLOUDFLARE_SITES = [
    "cloudflare.com",
    "challenges.cloudflare.com",
]


# Sites that may need TLS fingerprinting (anti-bot protection)
TLS_CANDIDATE_SITES = [
    "bot detection",
    "protection",
]


def route_url(url: str) -> RouterResult:
    """
    Determines which scraper to use for a given URL.

    Priority order:
    1. YouTube -> skip
    2. Novel URLs -> novel handler
    3. Cloudflare protected -> cloudscraper
    4. Heavy/JS sites -> playwright
    5. Alternate UA sites -> playwright_alt
    6. TLS candidates -> playwright_tls
    7. Simple sites -> Simple HTTP

    Args:
        url: The URL to route

    Returns:
        RouterResult indicating which scraper to use
    """
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    path = parsed.path.lower()
    
    logger.info(f"[1/6] ROUTING: domain={domain}, path={path}")

    if is_youtube_url(url):
        return "skip"

    if is_novel_url(url):
        logger.info(f"[1/6] ROUTING: Detected as NOVEL route")
        return "novel"

    # Check for Wikipedia and wiki sites (before other checks)
    for wiki in WIKI_SITES:
        if wiki in domain:
            logger.info(f"[1/6] ROUTING: Detected as WIKIPEDIA route (matched '{wiki}')")
            return "wikipedia"

    for cf in CLOUDFLARE_SITES:
        if cf in domain:
            logger.info(f"[1/6] ROUTING: Detected as CLOUDFLARE route (matched '{cf}')")
            return "cloudscraper"

    for heavy in HEAVY_SITES:
        if heavy in domain or heavy in path:
            logger.info(f"[1/6] ROUTING: Detected as PLAYWRIGHT route (matched '{heavy}')")
            return "playwright"

    for alt in ALTERNATE_UA_SITES:
        if alt in domain:
            logger.info(f"[1/6] ROUTING: Detected as PLAYWRIGHT_ALT route (matched '{alt}')")
            return "playwright_alt"

    logger.info(f"[1/6] ROUTING: Detected as SIMPLE_HTTP route (default)")
    return "simple_http"


def get_route_reason(url: str) -> str:
    """
    Returns human-readable reason for routing decision.

    Args:
        url: The URL being routed

    Returns:
        String explaining why this URL was routed the way it was
    """
    if is_youtube_url(url):
        return "YouTube URL - skipped"

    if is_novel_url(url):
        return "Novel URL detected"

    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    path = parsed.path.lower()

    for cf in CLOUDFLARE_SITES:
        if cf in domain:
            return f"Cloudflare protected ({cf}) - using CloudScraper"

    for heavy in HEAVY_SITES:
        if heavy in domain or heavy in path:
            return f"Heavy/JS site detected ({heavy}) - using Playwright"

    for alt in ALTERNATE_UA_SITES:
        if alt in domain:
            return f"Anti-detection site ({alt}) - using Playwright Alt"

    return "Simple site - using Simple HTTP"


def get_fallback_chain_names(route: str) -> list[str]:
    """
    Get ordered list of engine names for fallback chain.

    Args:
        route: Route type (e.g., "simple_http", "playwright")

    Returns:
        List of engine names in fallback order
    """
    return DEFAULT_FALLBACK_CHAINS.get(route, ["simple_http"])
