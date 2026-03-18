"""
Engine Registry Module

Central registry for all scraper engines with configurable fallback chains.
Provides engine lookup and fallback chain configuration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scraper.engines.base import BaseEngine
    from scraper.engines.cloudscraper_engine import CloudScraperEngine
    from scraper.engines.hybrid_engine import HybridEngine
    from scraper.engines.playwright_alt_engine import PlaywrightAltEngine
    from scraper.engines.playwright_engine import PlaywrightEngine
    from scraper.engines.playwright_tls_engine import PlaywrightTLSEngine
    from scraper.engines.simple_http_engine import SimpleHTTPEngine


DEFAULT_FALLBACK_CHAINS: dict[str, list[str]] = {
    "simple_http": ["simple_http", "playwright", "playwright_alt", "playwright_tls", "cloudscraper"],
    "playwright": ["playwright", "playwright_alt", "playwright_tls", "cloudscraper"],
    "playwright_alt": ["playwright_alt", "playwright_tls", "cloudscraper", "playwright"],
    "playwright_tls": ["playwright_tls", "cloudscraper", "playwright", "playwright_alt"],
    "cloudscraper": ["cloudscraper", "playwright", "playwright_alt", "playwright_tls"],
    "skip": [],
    "novel": ["hybrid", "cloudscraper", "playwright", "playwright_alt", "playwright_tls"],
    "wikipedia": ["playwright", "playwright_alt", "playwright_tls", "cloudscraper"],
}


class EngineRegistry:
    """Central registry for all scraper engines."""

    def __init__(self) -> None:
        self._engines: dict[str, BaseEngine] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Register all default engines."""
        from scraper.engines.simple_http_engine import SimpleHTTPEngine
        from scraper.engines.playwright_engine import PlaywrightEngine
        from scraper.engines.playwright_alt_engine import PlaywrightAltEngine
        from scraper.engines.playwright_tls_engine import PlaywrightTLSEngine
        from scraper.engines.cloudscraper_engine import CloudScraperEngine
        from scraper.engines.hybrid_engine import HybridEngine

        self._engines["simple_http"] = SimpleHTTPEngine()
        self._engines["playwright"] = PlaywrightEngine()
        self._engines["playwright_alt"] = PlaywrightAltEngine()
        self._engines["playwright_tls"] = PlaywrightTLSEngine()
        self._engines["cloudscraper"] = CloudScraperEngine()
        self._engines["hybrid"] = HybridEngine()

    def get_engine(self, name: str) -> BaseEngine | None:
        """
        Get engine by name.

        Args:
            name: Engine name (e.g., "playwright", "simple_http")

        Returns:
            Engine instance or None if not found
        """
        return self._engines.get(name)

    def get_fallback_chain(self, route: str) -> list[BaseEngine]:
        """
        Get ordered list of engines for a given route.

        Args:
            route: Route type (e.g., "simple_http", "playwright")

        Returns:
            List of engines in fallback order
        """
        engine_names = DEFAULT_FALLBACK_CHAINS.get(route, ["simple_http"])
        return [
            self._engines[name]
            for name in engine_names
            if name in self._engines
        ]

    def register_engine(self, name: str, engine: BaseEngine) -> None:
        """
        Register a custom engine.

        Args:
            name: Engine name
            engine: Engine instance
        """
        self._engines[name] = engine

    def set_fallback_chain(self, route: str, engine_names: list[str]) -> None:
        """
        Set custom fallback chain for a route.

        Args:
            route: Route type
            engine_names: Ordered list of engine names
        """
        DEFAULT_FALLBACK_CHAINS[route] = engine_names

    def get_all_engines(self) -> dict[str, BaseEngine]:
        """Get all registered engines."""
        return self._engines.copy()

    def get_all_routes(self) -> list[str]:
        """Get all available routes."""
        return list(DEFAULT_FALLBACK_CHAINS.keys())


_engine_registry: EngineRegistry | None = None


def get_engine_registry() -> EngineRegistry:
    """Get or create the global engine registry instance."""
    global _engine_registry
    if _engine_registry is None:
        _engine_registry = EngineRegistry()
    return _engine_registry
