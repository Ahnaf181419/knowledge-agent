"""
Fallback Chain Module

Execute scraping with automatic fallback through engine chain.
Tries each engine in sequence until success or all fail.
"""

import time
from dataclasses import dataclass, field

from app.logger import logger
from scraper.core.engine_registry import EngineRegistry


@dataclass
class FallbackResult:
    """Result from fallback chain execution."""

    success: bool
    content: str | None = None
    method: str | None = None
    error: str | None = None
    attempted_methods: list[str] = field(default_factory=list)
    extraction_time_ms: int = 0


class FallbackChain:
    """Execute scraping with automatic fallback through engine chain."""

    def __init__(self, registry: EngineRegistry | None = None):
        self.registry = registry or EngineRegistry()

    def execute(self, url: str, route: str) -> FallbackResult:
        """
        Try each engine in chain until success.

        Args:
            url: URL to scrape
            route: Route type determining fallback chain

        Returns:
            FallbackResult with success status and content
        """
        start_time = time.time()
        attempted: list[str] = []
        
        chain = list(self.registry.get_fallback_chain(route))
        logger.info(f"[3/6] FALLBACK CHAIN: Trying {len(chain)} engines in order: {[e.name for e in chain]}")

        for i, engine in enumerate(chain):
            attempted.append(engine.name)
            logger.info(f"  [{i+1}/{len(chain)}] Trying {engine.name}...")

            try:
                content = engine.scrape(url)
                
                is_challenge = False
                if content:
                    challenge_keywords = [
                        "having trouble with the challenge",
                        "please complete the challenge",
                        "detected unusual reading activity",
                        "please disable your ad blocker",
                    ]
                    content_lower = content.lower()
                    is_challenge = any(kw in content_lower for kw in challenge_keywords)
                
                if content and not is_challenge and len(content) > 1000:
                    elapsed_ms = int((time.time() - start_time) * 1000)
                    logger.info(f"  [SUCCESS] {engine.name} returned {len(content)} bytes")
                    return FallbackResult(
                        success=True,
                        content=content,
                        method=engine.name,
                        attempted_methods=attempted,
                        extraction_time_ms=elapsed_ms,
                    )
                elif is_challenge:
                    logger.info(f"  [BLOCKED] {engine.name}: Challenge page detected ({len(content)} bytes)")
                else:
                    logger.info(f"  [TOO_SHORT] {engine.name}: Only {len(content) if content else 0} bytes")
            except Exception as e:
                logger.info(f"  [FAILED] {engine.name}: {str(e)[:100]}")
                continue

        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.warning(f"All {len(chain)} engines failed for {url}")
        return FallbackResult(
            success=False,
            error="All engines failed",
            attempted_methods=attempted,
            extraction_time_ms=elapsed_ms,
        )

    def execute_with_timeout(self, url: str, route: str, timeout_seconds: float = 60) -> FallbackResult:
        """
        Execute with timeout support.

        Args:
            url: URL to scrape
            route: Route type
            timeout_seconds: Maximum time to wait

        Returns:
            FallbackResult
        """
        start_time = time.time()
        result = self.execute(url, route)

        if result.extraction_time_ms > timeout_seconds * 1000:
            return FallbackResult(
                success=False,
                error=f"Timeout after {timeout_seconds}s",
                attempted_methods=result.attempted_methods,
                extraction_time_ms=result.extraction_time_ms,
            )

        return result


_fallback_chain: FallbackChain | None = None


def get_fallback_chain(registry: EngineRegistry | None = None) -> FallbackChain:
    """Get or create the global fallback chain instance."""
    global _fallback_chain
    if _fallback_chain is None:
        _fallback_chain = FallbackChain(registry)
    return _fallback_chain
