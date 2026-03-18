"""Unit tests for text_cleaner module."""

from scraper.core.text_cleaner import TextCleaner, text_cleaner


class TestTextCleaner:
    """Tests for TextCleaner class."""

    def test_clean_removes_extra_whitespace(self):
        """Test that clean removes extra whitespace."""
        text = "Hello    World"
        result = TextCleaner.clean(text)

        assert result == "Hello World"

    def test_clean_removes_newline_whitespace(self):
        """Test that clean handles newlines."""
        text = "Hello\n\nWorld"
        result = TextCleaner.clean(text)

        assert "\n" not in result

    def test_clean_strips_edges(self):
        """Test that clean strips leading/trailing whitespace."""
        text = "   Hello World   "
        result = TextCleaner.clean(text)

        assert result == "Hello World"

    def test_clean_multiple_lines(self):
        """Test cleaning multiple lines."""
        text = "Line 1\n\n\nLine 2"
        result = TextCleaner.clean(text)

        assert "Line 1" in result
        assert "Line 2" in result


class TestTextCleanerStatic:
    """Tests for static cleaner methods."""

    def test_remove_empty_lines(self):
        """Test removing empty lines."""
        text = "Line 1\n\n\nLine 2\n  \nLine 3"
        result = TextCleaner.remove_empty_lines(text)

        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result

    def test_normalize_whitespace(self):
        """Test normalizing whitespace."""
        text = "Hello    \n  World   \t  !"
        result = TextCleaner.normalize_whitespace(text)

        assert result == "Hello World !"


class TestTextCleanerSingleton:
    """Tests for text_cleaner singleton."""

    def test_singleton_exists(self):
        """Test that text_cleaner singleton exists."""
        assert text_cleaner is not None
        assert hasattr(text_cleaner, "clean")
