"""
Queue Service Module

Centralized service for queue management with thread safety.
Provides typed dataclasses and atomic file operations.

Usage:
    from app.services.queue_service import queue_service

    # Add URLs
    queue_service.add_url("https://example.com", "normal", ["tag1"])

    # Get pending
    pending = queue_service.get_pending()

    # Start scraping
    job_id = queue_service.start_scrape()
"""

import json
import logging
import os
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from app.state import state
from app.services.background_job_service import (
    BackgroundJobService,
    background_job_service,
)

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).parent.parent.parent
QUEUE_FILE = CONFIG_DIR / "queue.json"


@dataclass
class QueueUrlEntry:
    """Typed representation of a URL entry in the queue."""

    url: str
    type: Literal["normal", "novel"]
    tags: list[str] = field(default_factory=list)
    status: Literal["pending", "processing", "completed", "failed", "skipped"] = "pending"
    error: str | None = None
    added_at: str = ""


@dataclass
class QueueNovelEntry:
    """Typed representation of a novel entry in the queue."""

    url: str
    start_chapter: int
    end_chapter: int
    tags: list[str] = field(default_factory=list)
    status: Literal["pending", "processing", "completed", "failed"] = "pending"
    error: str | None = None
    added_at: str = ""


@dataclass
class QueueStats:
    """Queue statistics."""

    total_urls: int = 0
    pending: int = 0
    processing: int = 0
    completed: int = 0
    failed: int = 0
    total_novels: int = 0
    retry_normal: int = 0
    retry_novel: int = 0


class QueueService:
    """
    Thread-safe queue management service.

    Provides a single source of truth for queue operations with:
    - Typed dataclasses for validation
    - Thread-safe operations using locks
    - Atomic file writes for crash safety
    """

    def __init__(self, background_job_svc: BackgroundJobService | None = None):
        self._lock = threading.RLock()
        self._background_job_service = background_job_svc or background_job_service

    def _atomic_write(self, data: dict[str, Any]) -> None:
        """Write data to queue.json atomically using temp file + rename."""
        temp_file = QUEUE_FILE.with_suffix(".json.tmp")
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(temp_file, QUEUE_FILE)
        except OSError as e:
            logger.error(f"Failed to write queue.json: {e}")
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except OSError:
                    pass
            raise

    def add_url(self, url: str, url_type: Literal["normal"] = "normal", tags: list[str] | None = None) -> bool:
        """
        Add a URL to the queue.

        Args:
            url: The URL to add
            url_type: Type of URL (normal, novel)
            tags: Optional tags for categorization

        Returns:
            True if added, False if already in queue
        """
        with self._lock:
            return state.add_url(url, url_type, tags)

    def add_novel(
        self, url: str, start_chapter: int, end_chapter: int, tags: list[str] | None = None
    ) -> bool:
        """
        Add a novel to the queue.

        Args:
            url: The novel URL
            start_chapter: Starting chapter number
            end_chapter: Ending chapter number
            tags: Optional tags

        Returns:
            True if added, False if already in queue
        """
        with self._lock:
            return state.add_novel(url, start_chapter, end_chapter, tags)

    def get_pending(self) -> list[QueueUrlEntry]:
        """
        Get all pending URL entries.

        Returns:
            List of pending URL entries
        """
        with self._lock:
            urls = state.queue.get("urls", [])
            return [
                QueueUrlEntry(
                    url=u["url"],
                    type=u.get("type", "normal"),
                    tags=u.get("tags", []),
                    status=u.get("status", "pending"),
                    error=u.get("error"),
                    added_at=u.get("added_at", ""),
                )
                for u in urls
                if u.get("status") == "pending"
            ]

    def get_all_urls(self) -> list[QueueUrlEntry]:
        """Get all URL entries regardless of status."""
        with self._lock:
            urls = state.queue.get("urls", [])
            return [
                QueueUrlEntry(
                    url=u["url"],
                    type=u.get("type", "normal"),
                    tags=u.get("tags", []),
                    status=u.get("status", "pending"),
                    error=u.get("error"),
                    added_at=u.get("added_at", ""),
                )
                for u in urls
            ]

    def get_all_novels(self) -> list[QueueNovelEntry]:
        """Get all novel entries."""
        with self._lock:
            novels = state.queue.get("novels", [])
            return [
                QueueNovelEntry(
                    url=n["url"],
                    start_chapter=n.get("start_chapter", 1),
                    end_chapter=n.get("end_chapter", 1),
                    tags=n.get("tags", []),
                    status=n.get("status", "pending"),
                    error=n.get("error"),
                    added_at=n.get("added_at", ""),
                )
                for n in novels
            ]

    def get_retry_normal(self) -> list[dict]:
        """Get URLs in retry queue."""
        with self._lock:
            return state.get_retry_normal()

    def get_retry_novel(self) -> list[dict]:
        """Get novels in retry queue."""
        with self._lock:
            return state.get_retry_novel()

    def update_status(
        self, url: str, status: Literal["pending", "processing", "completed", "failed", "skipped"], error: str | None = None
    ) -> None:
        """
        Update the status of a URL in the queue.

        Args:
            url: The URL to update
            status: New status
            error: Optional error message
        """
        with self._lock:
            state.update_url_status(url, status, error)

    def update_novel_status(self, url: str, status: str, error: str | None = None) -> None:
        """Update the status of a novel in the queue."""
        with self._lock:
            state.update_novel_status(url, status, error)

    def remove_url(self, url: str) -> None:
        """Remove a URL from the queue."""
        with self._lock:
            state.remove_url(url)

    def remove_novel(self, url: str) -> None:
        """Remove a novel from the queue."""
        with self._lock:
            state.remove_novel(url)

    def start_scrape(self) -> str | None:
        """
        Start scraping pending URLs in the background.

        Returns:
            Job ID if started, None if no pending URLs
        """
        with self._lock:
            pending = self.get_pending()
            if not pending:
                logger.info("No pending URLs to scrape")
                return None

            pending_data: list[tuple[str, list[str]]] = [(p.url, p.tags) for p in pending]

            for url, _tags in pending_data:
                state.update_url_status(url, "processing")

            def run_scrape() -> None:
                from scraper.runner import ScraperRunner

                runner = ScraperRunner()
                for url, tags in pending_data:
                    try:
                        result = runner.scrape_normal_url(url, tags)
                        if result.get("status") == "completed":
                            state.update_url_status(url, "completed")
                        else:
                            error = result.get("error", "Unknown error")
                            state.update_url_status(url, "failed", error)
                    except Exception as e:
                        logger.error(f"Error scraping {url}: {e}")
                        state.update_url_status(url, "failed", str(e))

            thread = threading.Thread(target=run_scrape, daemon=True)
            thread.start()

            return f"scrape_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def get_stats(self) -> QueueStats:
        """
        Get current queue statistics.

        Returns:
            QueueStats object with current counts
        """
        with self._lock:
            return QueueStats(
                total_urls=len(state.queue.get("urls", [])),
                pending=len([e for e in state.queue.get("urls", []) if e.get("status") == "pending"]),
                processing=len([e for e in state.queue.get("urls", []) if e.get("status") == "processing"]),
                completed=len([e for e in state.queue.get("urls", []) if e.get("status") == "completed"]),
                failed=len([e for e in state.queue.get("urls", []) if e.get("status") == "failed"]),
                total_novels=len(state.queue.get("novels", [])),
                retry_normal=len(state.queue.get("retry_normal", [])),
                retry_novel=len(state.queue.get("retry_novel", [])),
            )

    def clear_completed(self) -> None:
        """Remove all completed entries from the queue."""
        with self._lock:
            state.clear_completed()

    def url_in_queue(self, url: str) -> bool:
        """Check if a URL is already in the queue."""
        with self._lock:
            return state.url_in_queue(url)

    def novel_in_queue(self, url: str) -> bool:
        """Check if a novel is already in the queue."""
        with self._lock:
            return state.novel_in_queue(url)


queue_service = QueueService()
