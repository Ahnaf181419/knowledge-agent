"""
Page Extractor Module

Shared XPath extraction logic for Playwright-based engines.
Provides common content extraction methods used by all scraper engines.
"""

import time
from typing import Any

from app.logger import logger


class PageExtractor:
    """Shared page extraction logic for Playwright-based engines."""

    CONTENT_SELECTOR = "//div[count(p) > 5]"
    FALLBACK_SELECTOR = "//p"
    MIN_CONTENT_LENGTH = 200

    @staticmethod
    def extract_content(page: Any) -> str | None:
        """
        Extract main content from page using XPath selectors.

        Args:
            page: Playwright page object

        Returns:
            Extracted text content or None if extraction failed
        """
        try:
            container = page.locator(f"xpath={PageExtractor.CONTENT_SELECTOR}").first

            if container.count() > 0:
                paragraphs = container.locator("p").all_text_contents()
                if paragraphs:
                    text = "\n\n".join(p.strip() for p in paragraphs if p.strip())
                    if len(text) > PageExtractor.MIN_CONTENT_LENGTH:
                        logger.debug("Content extracted via CONTENT_SELECTOR")
                        return text

            all_p = page.locator(f"xpath={PageExtractor.FALLBACK_SELECTOR}").all_text_contents()
            if all_p:
                text = "\n\n".join(p.strip() for p in all_p if p.strip())
                if len(text) > PageExtractor.MIN_CONTENT_LENGTH:
                    logger.debug("Content extracted via FALLBACK_SELECTOR")
                    return text

            return None

        except Exception as e:
            logger.error(f"Page extraction error: {e}")
            return None

    @staticmethod
    def extract_with_title(page: Any) -> tuple[str | None, str | None]:
        """
        Extract content along with title from page.

        Args:
            page: Playwright page object

        Returns:
            Tuple of (content, title) or (None, None) if extraction failed
        """
        try:
            container = page.locator(f"xpath={PageExtractor.CONTENT_SELECTOR}").first

            if container.count() > 0:
                paragraphs = container.locator("p").all_text_contents()
                if paragraphs:
                    text = "\n\n".join(p.strip() for p in paragraphs if p.strip())
                    if len(text) > PageExtractor.MIN_CONTENT_LENGTH:
                        title = None
                        try:
                            title_loc = container.locator("xpath=./h1 | ./h2 | .//h1 | .//h2").first
                            if title_loc.count() > 0:
                                title = title_loc.text_content(timeout=500).strip()
                        except Exception:
                            pass
                        return text, title

            all_p = page.locator(f"xpath={PageExtractor.FALLBACK_SELECTOR}").all_text_contents()
            if all_p:
                text = "\n\n".join(p.strip() for p in all_p if p.strip())
                if len(text) > PageExtractor.MIN_CONTENT_LENGTH:
                    return text, None

            return None, None

        except Exception as e:
            logger.error(f"Page extraction error: {e}")
            return None, None

    @staticmethod
    def extract_with_selector(page: Any, selector: str) -> str | None:
        """
        Extract content using custom XPath selector.

        Args:
            page: Playwright page object
            selector: XPath selector string

        Returns:
            Extracted text or None
        """
        try:
            elements = page.locator(f"xpath={selector}").all_text_contents()
            if elements:
                text = "\n\n".join(e.strip() for e in elements if e.strip())
                if len(text) > PageExtractor.MIN_CONTENT_LENGTH:
                    return text
            return None
        except Exception as e:
            logger.error(f"Custom selector extraction error: {e}")
            return None

    @staticmethod
    def extract_with_retry(
        page: Any, max_retries: int = 2, retry_delay: float = 2.0
    ) -> str | None:
        """
        Extract content with retry logic.

        Args:
            page: Playwright page object
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds

        Returns:
            Extracted text or None
        """
        for attempt in range(max_retries):
            content = PageExtractor.extract_content(page)
            if content:
                return content
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
        return None
