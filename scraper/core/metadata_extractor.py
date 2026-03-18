"""
Metadata Extractor Module

Extract novel/section metadata from pages including genre, tags, and author.
"""

from typing import Any, Callable

from app.logger import logger


class MetadataExtractor:
    """Extract metadata from pages (genre, tags, author, title)."""

    @staticmethod
    def extract(page: Any, url: str) -> dict[str, Any]:
        """
        Extract metadata from page.

        Args:
            page: Playwright page object
            url: URL of the page

        Returns:
            Dictionary with extracted metadata
        """
        result: dict[str, Any] = {
            "genre": [],
            "tags": [],
            "author": "Unknown",
            "title": None,
        }

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(2000)

            result["genre"] = MetadataExtractor._extract_genre(page)
            result["tags"] = MetadataExtractor._extract_tags(page)
            result["author"] = MetadataExtractor._extract_author(page)

            if not result["genre"] and not result["tags"]:
                logger.warning("No genre/tags found. User may need to fill manually.")

        except Exception as e:
            logger.warning(f"Could not extract metadata: {e}")

        return result

    @staticmethod
    def _extract_genre(page: Any) -> list[str]:
        """Extract genre from page."""
        try:
            genre_loc = page.locator(
                "xpath=//div[contains(@class, 'genre') or contains(@class, 'genres')]"
            )
            if genre_loc.count() > 0:
                genre_text = genre_loc.first.text_content()
                if genre_text:
                    genres = [g.strip() for g in genre_text.split(",") if g.strip()]
                    logger.debug(f"Found genre(s): {genres}")
                    return genres
        except Exception:
            logger.debug("Could not extract genre")
        return []

    @staticmethod
    def _extract_tags(page: Any) -> list[str]:
        """Extract tags from page."""
        try:
            tags_loc = page.locator(
                "xpath=//div[contains(@class, 'tags') or contains(@class, 'tag')]"
            )
            if tags_loc.count() > 0:
                tags_text = tags_loc.first.text_content()
                if tags_text:
                    tags = [t.strip() for t in tags_text.split(",") if t.strip()]
                    logger.debug(f"Found tag(s): {tags}")
                    return tags
        except Exception:
            logger.debug("Could not extract tags")
        return []

    @staticmethod
    def _extract_author(page: Any) -> str:
        """Extract author from page."""
        try:
            author_loc = page.locator(
                "xpath=//div[contains(@class, 'author') or contains(@class, 'authors')]"
            )
            if author_loc.count() > 0:
                author_text: Any = author_loc.first.text_content()
                if author_text:
                    stripped = str(author_text).strip()
                    logger.debug(f"Found author: {stripped}")
                    return stripped
        except Exception:
            logger.debug("Could not extract author")
        return "Unknown"


metadata_extractor = MetadataExtractor()
