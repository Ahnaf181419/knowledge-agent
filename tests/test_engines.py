"""
Engine Unit Tests

Tests for scraper engines.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from scraper.engines.base_engine import BaseScraperEngine, EngineFactory
from scraper.engines.simple_http_engine import SimpleHTTPEngine
from scraper.engines.webscrapingapi_engine import WebScrapingAPIEngine


class TestBaseScraperEngine:
    """Tests for BaseScraperEngine."""
    
    def test_method_name_abstract(self):
        """Test that method_name is abstract."""
        with pytest.raises(TypeError):
            BaseScraperEngine()
    
    def test_shared_session(self):
        """Test that session is shared across instances."""
        engine1 = SimpleHTTPEngine()
        engine2 = SimpleHTTPEngine()
        
        session1 = engine1.get_session()
        session2 = engine2.get_session()
        
        assert session1 is session2
    
    def test_close_session(self):
        """Test closing session."""
        engine = SimpleHTTPEngine()
        engine.get_session()
        engine.close_session()
        
        assert SimpleHTTPEngine._shared_session is None


class TestSimpleHTTPEngine:
    """Tests for SimpleHTTPEngine."""
    
    def test_method_name(self):
        """Test method name."""
        engine = SimpleHTTPEngine()
        assert engine.method_name == "simple_http"
    
    @patch('requests.Session.get')
    def test_scrape_success(self, mock_get):
        """Test successful scrape."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Test content</body></html>"
        mock_get.return_value = mock_response
        
        engine = SimpleHTTPEngine()
        result = engine.scrape("https://example.com")
        
        assert result is not None
        assert "Test content" in result
    
    @patch('requests.Session.get')
    def test_scrape_failure(self, mock_get):
        """Test failed scrape."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        engine = SimpleHTTPEngine()
        result = engine.scrape("https://example.com")
        
        assert result is None


class TestWebScrapingAPIEngine:
    """Tests for WebScrapingAPIEngine."""
    
    def test_method_name(self):
        """Test method name."""
        engine = WebScrapingAPIEngine("test_key")
        assert engine.method_name == "webscrapingapi"
    
    @patch('app.api_tracker.can_use_api')
    def test_scrape_api_limit_reached(self, mock_can_use):
        """Test scrape when API limit is reached."""
        mock_can_use.return_value = (False, "API limit reached")
        
        engine = WebScrapingAPIEngine("test_key")
        result = engine.scrape("https://example.com")
        
        assert result is None


class TestEngineFactory:
    """Tests for EngineFactory."""
    
    def test_get_simple_http_engine(self):
        """Test getting SimpleHTTP engine."""
        factory = EngineFactory()
        engine = factory.get_engine("simple_http")
        
        assert engine is not None
        assert isinstance(engine, SimpleHTTPEngine)
    
    def test_get_unknown_engine(self):
        """Test getting unknown engine."""
        factory = EngineFactory()
        engine = factory.get_engine("unknown")
        
        assert engine is None
    
    def test_close_all(self):
        """Test closing all engines."""
        factory = EngineFactory()
        factory.get_engine("simple_http")
        factory.close_all()
        
        assert len(factory._engines) == 0
