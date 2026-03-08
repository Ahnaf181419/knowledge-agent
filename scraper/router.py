"""
URL Router Module

Determines which scraper to use for each URL.
Routes URLs based on site type and complexity.
"""

from typing import Literal
from urllib.parse import urlparse
from utils.validators import is_youtube_url, is_novel_url


# Type alias for router results
RouterResult = Literal["skip", "novel", "simple_http", "webscrapingapi"]


# List of sites that require WebScrapingAPI (heavy/JS sites)
HEAVY_SITES = [
    'amazon.com', 'aws.amazon.com',
    'twitter.com', 'x.com',
    'facebook.com', 'fb.com',
    'instagram.com',
    'linkedin.com',
    'netflix.com',
    'cloudflare.com',
    'login', 'signin', '/admin/', '/dashboard/'
]


def route_url(url: str) -> RouterResult:
    """
    Determines which scraper to use for a given URL.
    
    Priority order:
    1. YouTube -> skip
    2. Novel URLs -> novel handler
    3. Heavy/JS sites -> WebScrapingAPI
    4. Simple sites -> Simple HTTP
    
    Args:
        url: The URL to route
        
    Returns:
        RouterResult indicating which scraper to use
    """
    # Skip YouTube URLs
    if is_youtube_url(url):
        return "skip"
    
    # Handle novel URLs separately
    if is_novel_url(url):
        return "novel"
    
    # Check if URL is from a heavy/JS site
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    path = parsed.path.lower()
    
    for heavy in HEAVY_SITES:
        if heavy in domain or heavy in path:
            return "webscrapingapi"
    
    # Default to Simple HTTP for simple sites
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
    
    for heavy in HEAVY_SITES:
        if heavy in domain or heavy in path:
            return f"Heavy/JS site detected ({heavy})"
    
    return "Simple site - using Simple HTTP"
