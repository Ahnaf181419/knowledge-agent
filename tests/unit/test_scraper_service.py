"""Unit tests for scraper_service module."""

import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestScrapeResult:
    """Tests for ScrapeResult dataclass."""

    def test_default_values(self):
        from app.services.scraper_service import ScrapeResult

        result = ScrapeResult(url="https://example.com", status="pending")

        assert result.url == "https://example.com"
        assert result.status == "pending"
        assert result.method is None
        assert result.file_path is None
        assert result.word_count == 0
        assert result.extraction_time_ms == 0
        assert result.error is None
        assert result.fallback_chain == []

    def test_with_values(self):
        from app.services.scraper_service import ScrapeResult

        result = ScrapeResult(
            url="https://example.com",
            status="completed",
            method="simple_http",
            file_path="/output/example.md",
            word_count=500,
            extraction_time_ms=1500,
        )

        assert result.status == "completed"
        assert result.method == "simple_http"
        assert result.word_count == 500

    def test_fallback_chain_default(self):
        from app.services.scraper_service import ScrapeResult

        result = ScrapeResult(
            url="https://example.com",
            status="failed",
            fallback_chain=["simple_http", "playwright"],
        )

        assert result.fallback_chain == ["simple_http", "playwright"]


class TestScraperService:
    """Tests for ScraperService class."""

    @patch("app.services.scraper_service.history_service")
    @patch("app.services.scraper_service.stats_service")
    @patch("app.services.scraper_service.state")
    def test_record_success(self, mock_state, mock_stats, mock_history):
        """Test recording a successful scrape."""
        from app.services.scraper_service import ScraperService

        service = ScraperService()
        result = service.record_success(
            url="https://example.com/article",
            method="simple_http",
            file_path="/output/example.md",
            word_count=500,
            extraction_time_ms=1500,
            tags=["python", "tutorial"],
        )

        assert result.status == "completed"
        assert result.method == "simple_http"
        assert result.word_count == 500

        # Verify history was updated
        mock_history.add_normal.assert_called_once()

        # Verify stats were updated
        mock_stats.record_scrape.assert_called_once()

        # Verify queue was updated
        mock_state.update_url_status.assert_called_with("https://example.com/article", "completed")
        mock_state.remove_from_retry_normal.assert_called_with("https://example.com/article")
        mock_state.save_queue.assert_called()

    @patch("app.services.scraper_service.history_service")
    @patch("app.services.scraper_service.stats_service")
    @patch("app.services.scraper_service.state")
    def test_record_failure(self, mock_state, mock_stats, mock_history):
        """Test recording a failed scrape."""
        from app.services.scraper_service import ScraperService

        service = ScraperService()
        result = service.record_failure(
            url="https://example.com/article",
            error="Connection timeout",
            method="simple_http",
            tags=["python"],
        )

        assert result.status == "failed"
        assert result.error == "Connection timeout"

        # Verify stats were updated for failure
        mock_stats.record_scrape.assert_called_once()
        call_kwargs = mock_stats.record_scrape.call_args.kwargs
        assert call_kwargs["success"] is False

        # Verify retry queue was updated
        mock_state.add_to_retry_normal.assert_called_once()

        # Verify queue status
        mock_state.update_url_status.assert_called_with(
            "https://example.com/article", "failed", "Connection timeout"
        )

    @patch("app.services.scraper_service.history_service")
    def test_is_duplicate(self, mock_history):
        """Test checking for duplicate URLs."""
        from app.services.scraper_service import ScraperService

        mock_history.is_extracted.return_value = True

        service = ScraperService()
        result = service.is_duplicate("https://example.com/article")

        assert result is True
        mock_history.is_extracted.assert_called_once_with("https://example.com/article")

    @patch("app.services.scraper_service.history_service")
    def test_get_extracted_file(self, mock_history):
        """Test getting file path for extracted URL."""
        from app.services.scraper_service import ScraperService

        mock_history.get_extracted_file.return_value = "/output/example.md"

        service = ScraperService()
        result = service.get_extracted_file("https://example.com/article")

        assert result == "/output/example.md"
        mock_history.get_extracted_file.assert_called_once_with("https://example.com/article")
