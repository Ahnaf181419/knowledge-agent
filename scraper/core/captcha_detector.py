"""
CAPTCHA Detector Module

Detect CAPTCHA/challenge pages to avoid wasting resources.
"""

from typing import Any

from app.logger import logger


class CaptchaDetector:
    """Detect CAPTCHA and challenge pages."""

    INDICATORS = [
        "just a moment",
        "captcha",
        "verify you are human",
        "cloudflare",
        "checking your browser",
        "access denied",
    ]

    @staticmethod
    def detect(page: Any) -> bool:
        """
        Check if page contains CAPTCHA/challenge indicators.

        Args:
            page: Playwright page object

        Returns:
            True if CAPTCHA detected, False otherwise
        """
        if page is None:
            return False

        try:
            title = page.title().lower()
            content = page.content()[:3000].lower()

            for indicator in CaptchaDetector.INDICATORS:
                if indicator in title or indicator in content:
                    logger.warning(f"CAPTCHA detected: {indicator}")
                    return True

            return False

        except Exception:
            return False

    @staticmethod
    def check_response(content: str | None) -> bool:
        """
        Check response content for CAPTCHA indicators.

        Args:
            content: HTML content string

        Returns:
            True if CAPTCHA detected
        """
        if not content:
            return False

        content_lower = content[:3000].lower()
        return any(indicator in content_lower for indicator in CaptchaDetector.INDICATORS)


captcha_detector = CaptchaDetector()
