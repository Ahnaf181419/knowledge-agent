"""
Scraper Service Module

Centralized service for handling scraping results and persistence.
Provides a single source of truth for scrape results.

This service handles:
- Success persistence (history + stats + queue status)
- Failure handling (retry queue + stats)
- State consistency
"""

from dataclasses import dataclass
from pathlib import Path

from app.services.history_service import history_service
from app.services.stats_service import stats_service
from app.state import state


@dataclass
class ScrapeResult:
    """Standardized scrape result container."""

    url: str
    status: str  # pending, completed, failed, skipped
    method: str | None = None
    file_path: str | None = None
    word_count: int = 0
    extraction_time_ms: int = 0
    error: str | None = None
    fallback_chain: list[str] | None = None

    def __post_init__(self):
        if self.fallback_chain is None:
            self.fallback_chain = []


class ScraperService:
    """
    Centralized service for scrape result handling.

    Ensures consistency between:
    - History (extraction tracking)
    - Stats (method performance)
    - Queue (URL status)
    """

    def __init__(self):
        self._lock_operations = True  # Enable for atomic ops

    def record_success(
        self,
        url: str,
        method: str,
        file_path: str | Path,
        word_count: int,
        extraction_time_ms: int,
        tags: list[str] | None = None,
    ) -> ScrapeResult:
        """
        Record a successful scrape across all persistence layers.

        Args:
            url: The scraped URL
            method: Scraping method used (e.g., "simple_http", "playwright")
            file_path: Path to saved file
            word_count: Number of words extracted
            extraction_time_ms: Time taken in milliseconds
            tags: Optional tags for the URL

        Returns:
            ScrapeResult with success status
        """
        file_path_str = str(file_path)

        # 1. Update history
        history_service.add_normal(
            url=url,
            file_path=file_path_str,
            word_count=word_count,
            scraper=method,
        )

        # 2. Update stats
        stats_service.record_scrape(
            url=url,
            method=method,
            success=True,
            time_ms=extraction_time_ms,
            word_count=word_count,
        )

        # 3. Update queue status
        state.update_url_status(url, "completed")
        state.remove_from_retry_normal(url)

        # 4. Save queue (ensure persistence)
        state.save_queue()

        return ScrapeResult(
            url=url,
            status="completed",
            method=method,
            file_path=file_path_str,
            word_count=word_count,
            extraction_time_ms=extraction_time_ms,
        )

    def record_failure(
        self,
        url: str,
        error: str,
        method: str | None = None,
        tags: list[str] | None = None,
    ) -> ScrapeResult:
        """
        Record a failed scrape and add to retry queue.

        Args:
            url: The URL that failed
            error: Error message
            method: Method that was attempted (if known)
            tags: Tags for the URL

        Returns:
            ScrapeResult with failed status
        """
        # 1. Update stats (even for failures)
        if method:
            stats_service.record_scrape(
                url=url,
                method=method,
                success=False,
                time_ms=0,
                word_count=0,
            )

        # 2. Add to retry queue
        state.add_to_retry_normal(url, error, tags)

        # 3. Update queue status
        state.update_url_status(url, "failed", error)

        # 4. Save queue
        state.save_queue()

        return ScrapeResult(
            url=url,
            status="failed",
            method=method,
            error=error,
        )

    def record_skipped(
        self,
        url: str,
        reason: str,
    ) -> ScrapeResult:
        """
        Record a skipped URL (e.g., YouTube, invalid).

        Args:
            url: The skipped URL
            reason: Reason for skipping

        Returns:
            ScrapeResult with skipped status
        """
        state.update_url_status(url, "skipped", reason)
        state.save_queue()

        return ScrapeResult(
            url=url,
            status="skipped",
            error=reason,
        )

    def is_duplicate(self, url: str) -> bool:
        """
        Check if URL has already been successfully scraped.

        Args:
            url: URL to check

        Returns:
            True if URL exists in history
        """
        return history_service.is_extracted(url)

    def get_extracted_file(self, url: str) -> str | None:
        """
        Get the file path for a previously extracted URL.

        Args:
            url: URL to look up

        Returns:
            File path if exists, None otherwise
        """
        return history_service.get_extracted_file(url)


scraper_service = ScraperService()
