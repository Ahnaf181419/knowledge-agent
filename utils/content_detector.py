"""
Content type detection and tag extraction utilities.
"""

import re
from typing import Literal
from urllib.parse import urlparse

ContentType = Literal["wiki", "novel", "blog", "article"]


WIKI_DOMAINS = {
    "wikipedia.org",
    "wikimedia.org",
    "wiktionary.org",
    "wikiquote.org",
    "wikibooks.org",
    "wikisource.org",
}

BLOG_DOMAINS = {
    "medium.com",
    "blogger.com",
    "wordpress.com",
    "substack.com",
    "dev.to",
    "hashnode.dev",
    "ghost.io",
}

NOVEL_PATTERNS = [
    r"/novel/",
    r"/chapter[-_]?\d+",
    r"/ch/\d+",
    r"/book-\d+",
    r"/read/\d+",
    r"/vip/\d+",
]


def detect_content_type(url: str, html_title: str | None = None) -> ContentType:
    """
    Detect content type from URL and optionally HTML title.

    Args:
        url: The URL to analyze
        html_title: Optional HTML title for additional context

    Returns:
        ContentType: wiki, novel, blog, or article
    """
    parsed = urlparse(url)
    domain = parsed.netloc.lower().replace("www.", "")
    path = parsed.path.lower()

    if (
        domain.endswith(".wikipedia.org")
        or domain.endswith(".wikimedia.org")
        or domain in WIKI_DOMAINS
    ):
        return "wiki"

    for pattern in NOVEL_PATTERNS:
        if re.search(pattern, path):
            return "novel"

    if domain in BLOG_DOMAINS or "/blog/" in path or "/post/" in path:
        return "blog"

    if html_title:
        title_lower = html_title.lower()
        if "chapter" in title_lower or "novel" in title_lower:
            return "novel"
        if "wiki" in title_lower or "encyclopedia" in title_lower:
            return "wiki"
        if "blog" in title_lower:
            return "blog"

    return "article"


def extract_tags_from_url(url: str) -> list[str]:
    """
    Extract potential tags from URL path segments.

    Args:
        url: The URL to extract tags from

    Returns:
        List of potential tags
    """
    parsed = urlparse(url)
    path = parsed.path.strip("/")

    if not path:
        return []

    segments = [s for s in path.split("/") if s and len(s) > 2]

    tags = []
    for seg in segments[-4:]:
        seg = re.sub(r"[-\d_]+", "", seg)
        if seg and len(seg) > 2:
            tags.append(seg.lower())

    return tags[:5]


def extract_tags_from_html(html: str) -> list[str]:
    """
    Extract tags from HTML meta tags.

    Args:
        html: HTML content

    Returns:
        List of extracted tags
    """
    tags = []

    meta_keywords = re.search(
        r'<meta[^>]*name=["\']keywords["\'][^>]*content=["\']([^"\']+)["\']', html, re.I
    )
    if meta_keywords:
        tags.extend([t.strip().lower() for t in meta_keywords.group(1).split(",")])

    meta_description = re.search(
        r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']', html, re.I
    )
    if meta_description:
        desc = meta_description.group(1).lower()
        words = re.findall(r"\b[a-z]{4,}\b", desc)
        tags.extend(words[:5])

    return list(set(tags))[:10]


def extract_author_from_html(html: str) -> str | None:
    """
    Extract author from HTML meta tags.

    Args:
        html: HTML content

    Returns:
        Author name if found, None otherwise
    """
    patterns = [
        r'<meta[^>]*property=["\']author["\'][^>]*content=["\']([^"\']+)["\']',
        r'<meta[^>]*name=["\']author["\'][^>]*content=["\']([^"\']+)["\']',
        r'<span[^>]*class=["\']?author["\']?[^>]*>([^<]+)</span>',
    ]

    for pattern in patterns:
        match = re.search(pattern, html, re.I)
        if match:
            return match.group(1).strip()

    return None


def extract_published_date_from_html(html: str) -> str | None:
    """
    Extract published date from HTML meta tags.

    Args:
        html: HTML content

    Returns:
        ISO date string if found, None otherwise
    """
    patterns = [
        r'<meta[^>]*property=["\']article:published_time["\'][^>]*content=["\']([^"\']+)["\']',
        r'<meta[^>]*name=["\']date["\'][^>]*content=["\']([^"\']+)["\']',
        r'<time[^>]*datetime=["\']([^"\']+)["\']',
    ]

    for pattern in patterns:
        match = re.search(pattern, html, re.I)
        if match:
            return match.group(1).strip()

    return None
