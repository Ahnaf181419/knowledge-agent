"""
Service Unit Tests

Tests for ScrapingService, AnalyticsService, and NovelService.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from app.services import ScrapingService, AnalyticsService, NovelService
from app.repositories import ScrapeResult
from scraper.engines.base_engine import EngineFactory


class TestAnalyticsService:
    """Tests for AnalyticsService."""
    
    def test_get_method_comparison_empty(self, stats_repo):
        """Test method comparison with no data."""
        service = AnalyticsService(stats_repo)
        comparison = service.get_method_comparison()
        assert comparison == {}
    
    def test_get_method_comparison_with_data(self, stats_repo):
        """Test method comparison with data."""
        for i in range(5):
            stats_repo.record_scrape(ScrapeResult(
                url=f"https://example.com/{i}",
                method="simple_http",
                success=True,
                time_ms=500,
                word_count=1000,
                domain="example.com"
            ))
        
        service = AnalyticsService(stats_repo)
        comparison = service.get_method_comparison()
        
        assert "simple_http" in comparison
        assert comparison["simple_http"]["success_rate"] == 100.0
    
    def test_get_efficiency_rankings(self, stats_repo):
        """Test efficiency rankings."""
        stats_repo.record_scrape(ScrapeResult(
            url="https://example.com/1",
            method="simple_http",
            success=True,
            time_ms=500,
            word_count=1000,
            domain="example.com"
        ))
        
        stats_repo.record_scrape(ScrapeResult(
            url="https://example.com/2",
            method="playwright",
            success=True,
            time_ms=2000,
            word_count=1500,
            domain="example.com"
        ))
        
        service = AnalyticsService(stats_repo)
        rankings = service.get_efficiency_rankings()
        
        assert len(rankings) == 2
        assert rankings[0]["rank"] == 1
    
    def test_get_recent_activity(self, stats_repo):
        """Test getting recent activity."""
        stats_repo.record_scrape(ScrapeResult(
            url="https://example.com",
            method="simple_http",
            success=True,
            time_ms=500,
            word_count=1000,
            domain="example.com"
        ))
        
        service = AnalyticsService(stats_repo)
        recent = service.get_recent_activity()
        
        assert len(recent) == 1
        assert recent[0]["url"] == "https://example.com"


class TestScrapingService:
    """Tests for ScrapingService."""
    
    def test_get_config(self, state_repo, stats_repo, history_repo):
        """Test getting scraping configuration."""
        factory = EngineFactory()
        service = ScrapingService(state_repo, stats_repo, history_repo, factory)
        
        config = service.get_config()
        
        assert config.respect_robots_txt is True
        assert config.retry_count == 2
        assert config.concurrent_jobs == 3
    
    def test_scrape_url_skips_youtube(self, state_repo, stats_repo, history_repo):
        """Test that YouTube URLs are skipped."""
        factory = EngineFactory()
        service = ScrapingService(state_repo, stats_repo, history_repo, factory)
        
        result = service.scrape_url("https://youtube.com/watch?v=123", [])
        
        assert result["status"] == "skipped"
        assert "YouTube" in result["error"]


class TestNovelService:
    """Tests for NovelService."""
    
    def test_get_config(self, state_repo, stats_repo, history_repo):
        """Test getting novel configuration."""
        service = NovelService(state_repo, stats_repo, history_repo)
        
        config = service.get_config()
        
        assert config["delay_min"] == 90
        assert config["delay_max"] == 120
        assert config["retry_count"] == 2
