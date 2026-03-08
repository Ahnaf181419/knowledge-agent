"""
Repository Unit Tests

Tests for StateRepository, StatsRepository, and HistoryRepository.
"""

import pytest
from app.repositories import (
    StateRepository, StatsRepository, HistoryRepository,
    URLRecord, NovelRecord, ScrapeResult, ExtractionRecord
)


class TestStateRepository:
    """Tests for StateRepository."""
    
    def test_get_setting_default(self, state_repo):
        """Test getting a setting with default value."""
        value = state_repo.get_setting("nonexistent", "default_value")
        assert value == "default_value"
    
    def test_set_and_get_setting(self, state_repo):
        """Test setting and getting a value."""
        state_repo.set_setting("test_key", "test_value")
        assert state_repo.get_setting("test_key") == "test_value"
    
    def test_add_url(self, state_repo):
        """Test adding a URL to queue."""
        result = state_repo.add_url("https://example.com", "normal", ["test"])
        assert result is True
        assert state_repo.url_in_queue("https://example.com")
    
    def test_add_duplicate_url(self, state_repo):
        """Test adding duplicate URL."""
        state_repo.add_url("https://example.com", "normal", [])
        result = state_repo.add_url("https://example.com", "normal", [])
        assert result is False
    
    def test_add_novel(self, state_repo):
        """Test adding a novel to queue."""
        result = state_repo.add_novel("", 1, 10)
        assert result is True
        assert state_repo.novel_in_queue("")
    
    def test_update_url_status(self, state_repo):
        """Test updating URL status."""
        state_repo.add_url("https://example.com", "normal", [])
        state_repo.update_url_status("https://example.com", "completed")
        
        pending = state_repo.get_pending_urls()
        assert len(pending) == 0
    
    def test_get_pending_urls(self, state_repo):
        """Test getting pending URLs."""
        state_repo.add_url("https://example.com/1", "normal", [])
        state_repo.add_url("https://example.com/2", "normal", [])
        
        pending = state_repo.get_pending_urls()
        assert len(pending) == 2
    
    def test_add_to_retry_normal(self, state_repo):
        """Test adding to retry queue."""
        state_repo.add_to_retry_normal("https://example.com", "Test error", [])
        
        retry = state_repo.get_retry_normal()
        assert len(retry) == 1
        assert retry[0].url == "https://example.com"
    
    def test_remove_from_retry_normal(self, state_repo):
        """Test removing from retry queue."""
        state_repo.add_to_retry_normal("https://example.com", "Test error", [])
        state_repo.remove_from_retry_normal("https://example.com")
        
        retry = state_repo.get_retry_normal()
        assert len(retry) == 0


class TestStatsRepository:
    """Tests for StatsRepository."""
    
    def test_record_scrape_success(self, stats_repo):
        """Test recording a successful scrape."""
        result = ScrapeResult(
            url="https://example.com",
            method="simple_http",
            success=True,
            time_ms=500,
            word_count=1000,
            domain="example.com"
        )
        
        stats_repo.record_scrape(result)
        
        method_stats = stats_repo.get_method_stats()
        assert "simple_http" in method_stats
        assert method_stats["simple_http"]["success"] == 1
        assert method_stats["simple_http"]["total_attempts"] == 1
    
    def test_record_scrape_failure(self, stats_repo):
        """Test recording a failed scrape."""
        result = ScrapeResult(
            url="https://example.com",
            method="playwright",
            success=False,
            time_ms=2000,
            word_count=0,
            domain="example.com"
        )
        
        stats_repo.record_scrape(result)
        
        method_stats = stats_repo.get_method_stats()
        assert "playwright" in method_stats
        assert method_stats["playwright"]["failed"] == 1
    
    def test_get_summary_stats(self, stats_repo):
        """Test getting summary statistics."""
        for i in range(3):
            stats_repo.record_scrape(ScrapeResult(
                url=f"https://example.com/{i}",
                method="simple_http",
                success=True,
                time_ms=500,
                word_count=1000,
                domain="example.com"
            ))
        
        summary = stats_repo.get_summary_stats()
        assert summary["total_attempts"] == 3
        assert summary["total_success"] == 3
        assert summary["success_rate"] == 100.0
    
    def test_get_recent(self, stats_repo):
        """Test getting recent activity."""
        stats_repo.record_scrape(ScrapeResult(
            url="https://example.com",
            method="simple_http",
            success=True,
            time_ms=500,
            word_count=1000,
            domain="example.com"
        ))
        
        recent = stats_repo.get_recent(10)
        assert len(recent) == 1
        assert recent[0].url == "https://example.com"


class TestHistoryRepository:
    """Tests for HistoryRepository."""
    
    def test_is_extracted_false(self, history_repo):
        """Test checking if URL is extracted (not yet)."""
        assert history_repo.is_extracted("https://example.com") is False
    
    def test_add_extraction(self, history_repo):
        """Test adding an extraction record."""
        record = ExtractionRecord(
            url="https://example.com",
            file_path="/output/example.md",
            word_count=1000,
            method="simple_http"
        )
        
        history_repo.add_extraction(record)
        
        assert history_repo.is_extracted("https:/ /example.com")
        assert history_repo.get_extracted_file("https:/ /example.com") == "/output/example.md"
    
    def test_get_stats(self, history_repo):
        """Test getting extraction statistics."""
        for i in range(3):
            history_repo.add_extraction(ExtractionRecord(
                url=f"https:/ /example.com/{i}",
                file_path=f"/output/{i}.md",
                word_count=1000,
                method="simple_http"
            ))
        
        stats = history_repo.get_stats()
        assert stats["normal_links"] == 3
        assert stats["total_words"] == 3000
    
    def test_novel_chapters(self, history_repo):
        """Test novel chapter tracking."""
        history_repo.set_novel_metadata(
            novel_url="https:/ /novel/123",
            folder="/output/novels/test",
            name="Test Novel",
            genre=["Fantasy"],
            tags=["Action"],
            author="Test Author"
        )
        
        history_repo.add_novel_chapter("https:/ /", 1, 2000)
        history_repo.add_novel_chapter("https:/ /", 2, 2500)
        
        chapters = history_repo.get_novel_chapters("https:// /novel/123")
        assert len(chapters) == 2
        assert 1 in chapters
        assert 2 in chapters
