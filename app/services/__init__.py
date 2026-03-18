"""Services module for KnowledgeAgent."""

from app.services.history_service import HistoryService, history_service
from app.services.retry_service import RetryPolicy, RetryService, retry_service, with_retry
from app.services.scraper_service import ScrapeResult, ScraperService, scraper_service
from app.services.stats_service import StatsService, stats_service

__all__ = [
    "scraper_service",
    "ScraperService",
    "ScrapeResult",
    "retry_service",
    "RetryService",
    "RetryPolicy",
    "with_retry",
    "history_service",
    "HistoryService",
    "stats_service",
    "StatsService",
    "queue_service",
    "QueueService",
    "QueueUrlEntry",
    "QueueNovelEntry",
    "QueueStats",
    "notification_service",
    "NotificationService",
    "NotificationConfig",
    "NotificationLevel",
    "scheduler_service",
    "SchedulerService",
    "SchedulerConfig",
    "JobInfo",
    "background_job_service",
    "BackgroundJobService",
    "BackgroundJob",
    "JobStatus",
]


def __getattr__(name: str):
    """Lazy load services to avoid circular imports."""
    if name == "notification_service":
        from app.services.notification_service import notification_service

        return notification_service
    elif name == "NotificationService":
        from app.services.notification_service import NotificationService

        return NotificationService
    elif name == "NotificationConfig":
        from app.services.notification_service import NotificationConfig

        return NotificationConfig
    elif name == "NotificationLevel":
        from app.services.notification_service import NotificationLevel

        return NotificationLevel
    elif name == "scheduler_service":
        from app.services.scheduler_service import scheduler_service

        return scheduler_service
    elif name == "SchedulerService":
        from app.services.scheduler_service import SchedulerService

        return SchedulerService
    elif name == "SchedulerConfig":
        from app.services.scheduler_service import SchedulerConfig

        return SchedulerConfig
    elif name == "JobInfo":
        from app.services.scheduler_service import JobInfo

        return JobInfo
    elif name == "background_job_service":
        from app.services.background_job_service import background_job_service

        return background_job_service
    elif name == "BackgroundJobService":
        from app.services.background_job_service import BackgroundJobService

        return BackgroundJobService
    elif name == "BackgroundJob":
        from app.services.background_job_service import BackgroundJob

        return BackgroundJob
    elif name == "JobStatus":
        from app.services.background_job_service import JobStatus

        return JobStatus
    elif name == "queue_service":
        from app.services.queue_service import queue_service

        return queue_service
    elif name == "QueueService":
        from app.services.queue_service import QueueService

        return QueueService
    elif name == "QueueUrlEntry":
        from app.services.queue_service import QueueUrlEntry

        return QueueUrlEntry
    elif name == "QueueNovelEntry":
        from app.services.queue_service import QueueNovelEntry

        return QueueNovelEntry
    elif name == "QueueStats":
        from app.services.queue_service import QueueStats

        return QueueStats
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
