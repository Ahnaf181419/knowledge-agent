"""Unit tests for engine_registry module."""

import pytest


class TestEngineRegistry:
    """Tests for EngineRegistry class."""

    def test_default_engines_registered(self):
        """Test that all 5 default engines are registered."""
        from scraper.core.engine_registry import EngineRegistry

        registry = EngineRegistry()

        assert registry.get_engine("simple_http") is not None
        assert registry.get_engine("playwright") is not None
        assert registry.get_engine("playwright_alt") is not None
        assert registry.get_engine("playwright_tls") is not None
        assert registry.get_engine("cloudscraper") is not None

    def test_get_fallback_chain_simple_http(self):
        """Test fallback chain for simple_http route."""
        from scraper.core.engine_registry import EngineRegistry

        registry = EngineRegistry()
        chain = registry.get_fallback_chain("simple_http")

        engine_names = [e.name for e in chain]
        assert "simple_http" in engine_names
        assert "playwright" in engine_names
        assert "playwright_alt" in engine_names
        assert "playwright_tls" in engine_names
        assert "cloudscraper" in engine_names

    def test_get_fallback_chain_heavy_site(self):
        """Test fallback chain for heavy/JS sites."""
        from scraper.core.engine_registry import EngineRegistry

        registry = EngineRegistry()
        chain = registry.get_fallback_chain("playwright")

        engine_names = [e.name for e in chain]
        assert "playwright" in engine_names
        assert "playwright_alt" in engine_names

    def test_get_fallback_chain_cloudflare(self):
        """Test fallback chain for Cloudflare sites."""
        from scraper.core.engine_registry import EngineRegistry

        registry = EngineRegistry()
        chain = registry.get_fallback_chain("cloudscraper")

        engine_names = [e.name for e in chain]
        assert "cloudscraper" in engine_names

    def test_get_fallback_chain_skip(self):
        """Test fallback chain for skip route."""
        from scraper.core.engine_registry import EngineRegistry

        registry = EngineRegistry()
        chain = registry.get_fallback_chain("skip")

        assert len(chain) == 0

    def test_get_fallback_chain_unknown(self):
        """Test fallback chain for unknown route defaults to simple_http."""
        from scraper.core.engine_registry import EngineRegistry

        registry = EngineRegistry()
        chain = registry.get_fallback_chain("unknown_route")

        assert len(chain) > 0
        assert chain[0].name == "simple_http"

    def test_get_all_engines(self):
        """Test getting all registered engines."""
        from scraper.core.engine_registry import EngineRegistry

        registry = EngineRegistry()
        engines = registry.get_all_engines()

        assert len(engines) == 5

    def test_get_all_routes(self):
        """Test getting all available routes."""
        from scraper.core.engine_registry import EngineRegistry

        registry = EngineRegistry()
        routes = registry.get_all_routes()

        assert "simple_http" in routes
        assert "playwright" in routes
        assert "skip" in routes
        assert "novel" in routes


class TestDefaultFallbackChains:
    """Tests for DEFAULT_FALLBACK_CHAINS."""

    def test_all_routes_defined(self):
        """Test that all expected routes are defined."""
        from scraper.core.engine_registry import DEFAULT_FALLBACK_CHAINS

        expected_routes = [
            "simple_http",
            "playwright",
            "playwright_alt",
            "playwright_tls",
            "cloudscraper",
            "skip",
            "novel",
        ]

        for route in expected_routes:
            assert route in DEFAULT_FALLBACK_CHAINS

    def test_simple_http_chain_order(self):
        """Test that simple_http chain tries simplest first."""
        from scraper.core.engine_registry import DEFAULT_FALLBACK_CHAINS

        chain = DEFAULT_FALLBACK_CHAINS["simple_http"]
        assert chain[0] == "simple_http"
        assert chain[-1] == "cloudscraper"
