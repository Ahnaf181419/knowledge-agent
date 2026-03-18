"""
Notification Service Module

Provides system notifications for scraping events.
Supports Windows toast notifications, macOS notification center, and Linux libnotify.

Usage:
    from app.services.notification_service import notification_service

    # Send notification on scrape completion
    notification_service.notify(
        title="Scrape Complete",
        message=f"Successfully scraped {url}",
    )
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class NotificationLevel(Enum):
    """Notification priority levels."""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class NotificationConfig:
    """Configuration for notification service."""

    enabled: bool = True
    notify_on_success: bool = True
    notify_on_failure: bool = True
    notify_on_complete: bool = True  # Batch complete notification


class NotificationService:
    """
    System notification service for scraping events.

    Uses plyer for cross-platform notifications:
    - Windows: Toast notifications
    - macOS: Notification Center
    - Linux: libnotify
    """

    def __init__(self, config: NotificationConfig | None = None):
        self.config = config or NotificationConfig()
        self._notifier: Any = None
        self._init_notifier()

    def _init_notifier(self):
        """Initialize the notification backend."""
        if not self.config.enabled:
            logger.debug("Notifications disabled")
            return

        try:
            from plyer import notification

            self._notifier = notification
            logger.debug("Notification service initialized")
        except ImportError:
            logger.warning("plyer not installed. Install with: pip install plyer")
            self._notifier = None
        except Exception as e:
            logger.warning(f"Failed to initialize notifications: {e}")
            self._notifier = None

    def notify(
        self,
        title: str,
        message: str,
        level: NotificationLevel = NotificationLevel.INFO,
        timeout: int = 5,
    ) -> bool:
        """
        Send a system notification.

        Args:
            title: Notification title
            message: Notification message
            level: Notification priority level
            timeout: How long to show the notification (seconds)

        Returns:
            True if notification was sent, False otherwise
        """
        if not self.config.enabled:
            return False

        notifier = self._notifier
        if notifier is None:
            return False

        assert notifier is not None
        try:
            notifier.notify(
                title=title,
                message=message,
                app_name="KnowledgeAgent",
                timeout=timeout,
            )
            logger.debug(f"Notification sent: {title}")
            return True
        except Exception as e:
            logger.warning(f"Failed to send notification: {e}")
            return False

    def notify_success(self, url: str, word_count: int) -> bool:
        """
        Notify about successful scrape.

        Args:
            url: The scraped URL
            word_count: Number of words extracted

        Returns:
            True if notification was sent
        """
        if not self.config.notify_on_success:
            return False

        title = "Scrape Success"
        message = f"Extracted {word_count} words from {self._truncate_url(url)}"
        return self.notify(title, message, NotificationLevel.SUCCESS)

    def notify_failure(self, url: str, error: str) -> bool:
        """
        Notify about scrape failure.

        Args:
            url: The URL that failed
            error: Error message

        Returns:
            True if notification was sent
        """
        if not self.config.notify_on_failure:
            return False

        title = "Scrape Failed"
        message = f"{self._truncate_url(url)}: {error}"
        return self.notify(title, message, NotificationLevel.ERROR)

    def notify_batch_complete(
        self,
        total: int,
        successful: int,
        failed: int,
        duration_seconds: float,
    ) -> bool:
        """
        Notify about batch scrape completion.

        Args:
            total: Total URLs processed
            successful: Number of successful scrapes
            failed: Number of failed scrapes
            duration_seconds: Time taken for batch

        Returns:
            True if notification was sent
        """
        if not self.config.notify_on_complete:
            return False

        success_rate = (successful / total * 100) if total > 0 else 0
        title = "Batch Complete"
        message = (
            f"Processed {total} URLs: "
            f"{successful} successful, {failed} failed "
            f"({success_rate:.0f}% success rate)"
        )

        level = NotificationLevel.SUCCESS if failed == 0 else NotificationLevel.WARNING
        return self.notify(title, message, level)

    def notify_queue_empty(self) -> bool:
        """Notify when queue becomes empty."""
        return self.notify(
            title="Queue Complete",
            message="All URLs have been processed",
            level=NotificationLevel.SUCCESS,
        )

    @staticmethod
    def _truncate_url(url: str, max_length: int = 50) -> str:
        """Truncate URL for display in notifications."""
        if len(url) <= max_length:
            return url
        return url[: max_length - 3] + "..."

    def update_config(self, config: NotificationConfig):
        """Update notification configuration."""
        self.config = config
        self._init_notifier()


notification_service = NotificationService()
