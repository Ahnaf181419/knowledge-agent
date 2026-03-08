"""
Validators Module

URL validation and utility functions.
Provides functions for validating URLs, checking site types, and generating slugs.
"""

import re
from urllib.parse import urlparse
import requests
from typing import Optional


def is_valid_url(url: str) -> bool:
    """
    Checks if a URL has valid format.
    
    Args:
        url: The URL string to validate
        
    Returns:
        True if URL is valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def is_youtube_url(url: str) -> bool:
    """
    Checks if URL is from YouTube.
    
    Args:
        url: The URL to check
        
    Returns:
        True if URL is YouTube, False otherwise
    """
    parsed = urlparse(url)
    return 'youtube.com' in parsed.netloc.lower() or 'youtu.be' in parsed.netloc.lower()


def is_novel_url(url: str) -> bool:
    """
    Checks if URL is a novel chapter/page.
    
    Args:
        url: The URL to check
        
    Returns:
        True if URL appears to be a novel, False otherwise
    """
    parsed = urlparse(url)
    path_lower = parsed.path.lower()
    novel_patterns = ['/novel/', '/chapter-', '/ch/', '/book-', '/read/']
    return any(pattern in path_lower for pattern in novel_patterns)


def get_domain(url: str) -> str:
    """
    Extracts domain name from URL.
    
    Args:
        url: The URL to extract domain from
        
    Returns:
        Domain name without www prefix
    """
    parsed = urlparse(url)
    return parsed.netloc.replace('www.', '')


def generate_slug(url: str, title: Optional[str] = None) -> str:
    """
    Generates a URL-friendly slug from URL or title.
    
    Args:
        url: The URL to generate slug from
        title: Optional title to use instead of URL path
        
    Returns:
        A slug string (max 50 characters)
    """
    parsed = urlparse(url)
    path = parsed.path.strip('/')
    
    if title:
        # Use title for slug
        slug = re.sub(r'[^\w\s-]', '', title.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug[:50]
    
    # Use URL path
    if '/' in path:
        slug = path.split('/')[-1]
    else:
        slug = path
    
    return slug[:50] if slug else get_domain(url)


def check_url_reachable(url: str, timeout: int = 10) -> bool:
    """
    Checks if URL is reachable (HEAD request).
    
    Args:
        url: The URL to check
        timeout: Request timeout in seconds
        
    Returns:
        True if URL responds with status < 400, False otherwise
    """
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code < 400
    except Exception:
        return False


def validate_chapter_range(start: int, end: int) -> tuple[bool, str]:
    """
    Validates chapter range for novel scraping.
    
    Args:
        start: Starting chapter number
        end: Ending chapter number
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if start < 1:
        return False, "Start chapter must be >= 1"
    if end < start:
        return False, "End chapter must be >= start"
    if end - start > 1000:
        return False, "Chapter range too large (max 1000)"
    return True, "Valid"


def parse_tags(tag_string: str) -> list[str]:
    """
    Parses comma-separated tags string into list.
    
    Args:
        tag_string: Comma-separated tag string
        
    Returns:
        List of cleaned tag strings
    """
    if not tag_string:
        return []
    return [tag.strip() for tag in tag_string.split(',') if tag.strip()]
