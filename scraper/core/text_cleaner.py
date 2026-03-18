"""
Text Cleaner Module

Text cleaning utilities for extracted content.
"""

import re


class TextCleaner:
    """Text cleaning utilities."""

    @staticmethod
    def clean(text: str) -> str:
        """
        Clean extracted text by removing extra whitespace.

        Args:
            text: Raw text content

        Returns:
            Cleaned text
        """
        text = re.sub(r"\n\s+", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def remove_empty_lines(text: str) -> str:
        """Remove empty lines from text."""
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        return "\n\n".join(lines)

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Normalize all whitespace to single spaces."""
        return re.sub(r"\s+", " ", text).strip()


text_cleaner = TextCleaner()
