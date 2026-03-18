"""Unit tests for page_extractor module."""

from unittest.mock import MagicMock, patch


class TestPageExtractor:
    """Tests for PageExtractor class."""

    def test_default_selectors(self):
        """Test default selector values."""
        from scraper.core.page_extractor import PageExtractor

        assert PageExtractor.CONTENT_SELECTOR == "//div[count(p) > 5]"
        assert PageExtractor.FALLBACK_SELECTOR == "//p"
        assert PageExtractor.MIN_CONTENT_LENGTH == 200

    @patch("scraper.core.page_extractor.logger")
    def test_extract_content_success(self, mock_logger):
        """Test successful content extraction."""
        from scraper.core.page_extractor import PageExtractor

        mock_page = MagicMock()
        
        mock_first_locator = MagicMock()
        mock_first_locator.count.return_value = 1
        
        mock_paragraph_locator = MagicMock()
        mock_paragraph_texts = [
            "Paragraph 1 with enough content to exceed minimum length requirement",
            "Paragraph 2 with enough content to exceed minimum length requirement",
            "Paragraph 3 with enough content to exceed minimum length requirement"
        ]
        mock_paragraph_locator.all_text_contents.return_value = mock_paragraph_texts
        
        mock_first_locator.locator.return_value.all_text_contents.return_value = mock_paragraph_texts
        mock_page.locator.return_value.first.count.return_value = 1
        mock_page.locator.return_value.first.locator.return_value.all_text_contents.return_value = mock_paragraph_texts
        
        result = PageExtractor.extract_content(mock_page)

        assert result is not None
        assert "Paragraph 1" in result

    @patch("scraper.core.page_extractor.logger")
    def test_extract_content_fallback(self, mock_logger):
        """Test fallback extraction when main selector fails."""
        from scraper.core.page_extractor import PageExtractor

        mock_page = MagicMock()

        mock_first_locator = MagicMock()
        mock_first_locator.count.return_value = 0
        
        mock_page.locator.return_value.first = mock_first_locator
        
        mock_page.locator.return_value.all_text_contents.return_value = [
            "Fallback paragraph 1 with enough content to exceed minimum length threshold",
            "Fallback paragraph 2 with enough content to exceed minimum length threshold",
            "Fallback paragraph 3 with enough content to exceed minimum length threshold"
        ]

        result = PageExtractor.extract_content(mock_page)

        assert result is not None
        assert "Fallback paragraph" in result

    @patch("scraper.core.page_extractor.logger")
    def test_extract_content_too_short(self, mock_logger):
        """Test content too short returns None."""
        from scraper.core.page_extractor import PageExtractor

        mock_page = MagicMock()
        mock_container = MagicMock()
        mock_container.count.return_value = 1
        mock_container.locator.return_value.all_text_contents.return_value = [
            "Short",
        ]

        mock_page.locator.return_value.first.return_value = mock_container

        result = PageExtractor.extract_content(mock_page)

        assert result is None

    @patch("scraper.core.page_extractor.logger")
    def test_extract_content_exception(self, mock_logger):
        """Test exception handling."""
        from scraper.core.page_extractor import PageExtractor

        mock_page = MagicMock()
        mock_page.locator.side_effect = Exception("Test error")

        result = PageExtractor.extract_content(mock_page)

        assert result is None

    @patch("scraper.core.page_extractor.logger")
    def test_extract_with_selector(self, mock_logger):
        """Test extraction with custom selector."""
        from scraper.core.page_extractor import PageExtractor

        mock_page = MagicMock()

        selector_texts = [
            "Custom paragraph content that is long enough to pass minimum length threshold for testing purposes extra padding",
            "More custom content that is long enough to pass minimum length threshold for testing purposes extra padding"
        ]
        mock_page.locator.return_value.all_text_contents.return_value = selector_texts

        result = PageExtractor.extract_with_selector(mock_page, "//article")

        assert result is not None
        assert "Custom paragraph" in result


class TestPageExtractorWithRetry:
    """Tests for PageExtractor retry functionality."""

    @patch("scraper.core.page_extractor.PageExtractor.extract_content")
    @patch("scraper.core.page_extractor.time")
    def test_extract_with_retry_success_first(self, mock_time, mock_extract):
        """Test retry succeeds on first attempt."""
        from scraper.core.page_extractor import PageExtractor

        mock_extract.return_value = "content"

        result = PageExtractor.extract_with_retry(MagicMock(), max_retries=3)

        assert result == "content"
        mock_extract.assert_called_once()

    @patch("scraper.core.page_extractor.PageExtractor.extract_content")
    @patch("scraper.core.page_extractor.time")
    def test_extract_with_retry_eventually_succeeds(self, mock_time, mock_extract):
        """Test retry eventually succeeds."""
        from scraper.core.page_extractor import PageExtractor

        mock_extract.side_effect = [None, None, "content"]

        result = PageExtractor.extract_with_retry(MagicMock(), max_retries=3)

        assert result == "content"
        assert mock_extract.call_count == 3

    @patch("scraper.core.page_extractor.PageExtractor.extract_content")
    @patch("scraper.core.page_extractor.time")
    def test_extract_with_retry_all_fail(self, mock_time, mock_extract):
        """Test all retries fail."""
        from scraper.core.page_extractor import PageExtractor

        mock_extract.return_value = None

        result = PageExtractor.extract_with_retry(MagicMock(), max_retries=3)

        assert result is None
        assert mock_extract.call_count == 3
