"""Unit tests for fallback_chain module."""

from unittest.mock import MagicMock, patch


class TestFallbackResult:
    """Tests for FallbackResult dataclass."""

    def test_default_values(self):
        """Test FallbackResult default values."""
        from scraper.core.fallback_chain import FallbackResult

        result = FallbackResult(success=False)

        assert result.success is False
        assert result.content is None
        assert result.method is None
        assert result.error is None
        assert result.attempted_methods == []
        assert result.extraction_time_ms == 0

    def test_with_values(self):
        """Test FallbackResult with values."""
        from scraper.core.fallback_chain import FallbackResult

        result = FallbackResult(
            success=True,
            content="test content",
            method="playwright",
            attempted_methods=["simple_http", "playwright"],
            extraction_time_ms=1500,
        )

        assert result.success is True
        assert result.content == "test content"
        assert result.method == "playwright"
        assert len(result.attempted_methods) == 2
        assert result.extraction_time_ms == 1500


class TestFallbackChain:
    """Tests for FallbackChain class."""

    @patch("scraper.core.fallback_chain.EngineRegistry")
    def test_first_engine_succeeds(self, mock_registry):
        """Test that first successful engine is returned."""
        from scraper.core.fallback_chain import FallbackChain

        mock_engine1 = MagicMock()
        mock_engine1.name = "simple_http"
        mock_engine1.scrape.return_value = "content"

        mock_engine2 = MagicMock()
        mock_engine2.name = "playwright"

        mock_registry_instance = MagicMock()
        mock_registry_instance.get_fallback_chain.return_value = [mock_engine1, mock_engine2]
        mock_registry.return_value = mock_registry_instance

        chain = FallbackChain(mock_registry_instance)
        result = chain.execute("https://example.com", "simple_http")

        assert result.success is True
        assert result.content == "content"
        assert result.method == "simple_http"
        assert "simple_http" in result.attempted_methods

    @patch("scraper.core.fallback_chain.EngineRegistry")
    def test_fallback_on_first_failure(self, mock_registry):
        """Test fallback to second engine when first fails."""
        from scraper.core.fallback_chain import FallbackChain

        mock_engine1 = MagicMock()
        mock_engine1.name = "simple_http"
        mock_engine1.scrape.return_value = None

        mock_engine2 = MagicMock()
        mock_engine2.name = "playwright"
        mock_engine2.scrape.return_value = "content"

        mock_registry_instance = MagicMock()
        mock_registry_instance.get_fallback_chain.return_value = [mock_engine1, mock_engine2]
        mock_registry.return_value = mock_registry_instance

        chain = FallbackChain(mock_registry_instance)
        result = chain.execute("https://example.com", "simple_http")

        assert result.success is True
        assert result.content == "content"
        assert result.method == "playwright"
        assert result.attempted_methods == ["simple_http", "playwright"]

    @patch("scraper.core.fallback_chain.EngineRegistry")
    def test_all_engines_fail(self, mock_registry):
        """Test result when all engines fail."""
        from scraper.core.fallback_chain import FallbackChain

        mock_engine1 = MagicMock()
        mock_engine1.name = "simple_http"
        mock_engine1.scrape.return_value = None

        mock_engine2 = MagicMock()
        mock_engine2.name = "playwright"
        mock_engine2.scrape.return_value = None

        mock_registry_instance = MagicMock()
        mock_registry_instance.get_fallback_chain.return_value = [mock_engine1, mock_engine2]
        mock_registry.return_value = mock_registry_instance

        chain = FallbackChain(mock_registry_instance)
        result = chain.execute("https://example.com", "simple_http")

        assert result.success is False
        assert result.content is None
        assert result.error == "All engines failed"
        assert result.attempted_methods == ["simple_http", "playwright"]

    @patch("scraper.core.fallback_chain.EngineRegistry")
    def test_engine_exception_caught(self, mock_registry):
        """Test that engine exceptions are caught and fallback continues."""
        from scraper.core.fallback_chain import FallbackChain

        mock_engine1 = MagicMock()
        mock_engine1.name = "simple_http"
        mock_engine1.scrape.side_effect = Exception("Network error")

        mock_engine2 = MagicMock()
        mock_engine2.name = "playwright"
        mock_engine2.scrape.return_value = "content"

        mock_registry_instance = MagicMock()
        mock_registry_instance.get_fallback_chain.return_value = [mock_engine1, mock_engine2]
        mock_registry.return_value = mock_registry_instance

        chain = FallbackChain(mock_registry_instance)
        result = chain.execute("https://example.com", "simple_http")

        assert result.success is True
        assert result.content == "content"

    @patch("scraper.core.fallback_chain.EngineRegistry")
    def test_records_extraction_time(self, mock_registry):
        """Test that extraction time is recorded."""
        from scraper.core.fallback_chain import FallbackChain
        import time

        mock_engine1 = MagicMock()
        mock_engine1.name = "simple_http"

        def slow_scrape(url):
            time.sleep(0.01)
            return "content"

        mock_engine1.scrape.side_effect = slow_scrape

        mock_registry_instance = MagicMock()
        mock_registry_instance.get_fallback_chain.return_value = [mock_engine1]
        mock_registry.return_value = mock_registry_instance

        chain = FallbackChain(mock_registry_instance)
        result = chain.execute("https://example.com", "simple_http")

        assert result.extraction_time_ms >= 10


class TestFallbackChainSingleton:
    """Tests for fallback_chain singleton."""

    def test_singleton_exists(self):
        """Test that fallback_chain singleton exists."""
        from scraper.core.fallback_chain import get_fallback_chain

        fallback_chain = get_fallback_chain()
        assert fallback_chain is not None
        assert hasattr(fallback_chain, "execute")
