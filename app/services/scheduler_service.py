"""
Scheduler Service Module

Provides background job scheduling for KnowledgeAgent.
Supports scheduled scraping, periodic tasks, and job management.

Usage:
    from app.services.scheduler_service import scheduler_service

    # Add a scheduled job
    scheduler_service.add_scheduled_job(
        func=my_scrape_function,
        trigger="interval",
        minutes=30,
        job_id="periodic_scrape",
    )

    # Start scheduler
    scheduler_service.start()
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


class SchedulerConfig:
    """Configuration for the scheduler service."""

    def __init__(
        self,
        enabled: bool = True,
        max_concurrent_jobs: int = 2,
        coalesce: bool = True,
        max_instances: int = 1,
    ):
        self.enabled = enabled
        self.max_concurrent_jobs = max_concurrent_jobs
        self.coalesce = coalesce  # Run missed jobs together
        self.max_instances = max_instances


@dataclass
class JobInfo:
    """Information about a scheduled job."""

    job_id: str
    name: str
    trigger_type: str  # interval, cron, date
    next_run: datetime | None = None
    last_run: datetime | None = None
    status: str = "scheduled"  # scheduled, running, paused


class SchedulerService:
    """
    Background job scheduler using APScheduler.

    Features:
    - Interval-based jobs (e.g., every 30 minutes)
    - Cron-based jobs (e.g., daily at 2am)
    - One-time scheduled jobs
    - Job management (pause, resume, remove)
    - Max concurrent job limits
    """

    def __init__(self, config: SchedulerConfig | None = None):
        self.config = config or SchedulerConfig()
        self._scheduler: BackgroundScheduler | None = None
        self._jobs: dict[str, JobInfo] = {}
        self._job_results: dict[str, Any] = {}

    def start(self):
        """Start the background scheduler."""
        if not self.config.enabled:
            logger.info("Scheduler disabled")
            return

        if self._scheduler is not None and self._scheduler.running:
            logger.warning("Scheduler already running")
            return

        executors = {"default": ThreadPoolExecutor(self.config.max_concurrent_jobs)}

        job_defaults = {
            "coalesce": self.config.coalesce,
            "max_instances": self.config.max_instances,
        }

        self._scheduler = BackgroundScheduler(
            executors=executors,
            job_defaults=job_defaults,
        )
        self._scheduler.start()
        logger.info("Scheduler started")

    def stop(self):
        """Stop the background scheduler."""
        if self._scheduler is None:
            return

        if self._scheduler.running:
            self._scheduler.shutdown(wait=True)
            logger.info("Scheduler stopped")

    def add_interval_job(
        self,
        func: Callable,
        minutes: int = 0,
        hours: int = 0,
        job_id: str | None = None,
        name: str | None = None,
        **kwargs,
    ) -> str | None:
        """
        Add a job that runs at fixed intervals.

        Args:
            func: Function to execute
            minutes: Run every N minutes
            hours: Run every N hours
            job_id: Unique job identifier
            name: Human-readable job name
            **kwargs: Additional arguments passed to func

        Returns:
            Job ID if added successfully, None otherwise
        """
        if self._scheduler is None:
            logger.error("Scheduler not running")
            return None

        if job_id is None:
            job_id = f"job_{len(self._jobs)}"

        if name is None:
            name = job_id

        trigger = IntervalTrigger(minutes=minutes, hours=hours)

        try:
            job = self._scheduler.add_job(
                func=func,
                trigger=trigger,
                id=job_id,
                name=name,
                replace_existing=True,
                **kwargs,
            )

            self._jobs[job_id] = JobInfo(
                job_id=job_id,
                name=name,
                trigger_type="interval",
                next_run=job.next_run_time,
            )

            logger.info(f"Added interval job: {job_id} (every {hours}h {minutes}m)")
            return job_id

        except Exception as e:
            logger.error(f"Failed to add interval job: {e}")
            return None

    def add_cron_job(
        self,
        func: Callable,
        job_id: str | None = None,
        name: str | None = None,
        hour: int | None = None,
        minute: int | None = None,
        day_of_week: str | None = None,
        **kwargs,
    ) -> str | None:
        """
        Add a job that runs on a cron schedule.

        Args:
            func: Function to execute
            job_id: Unique job identifier
            name: Human-readable job name
            hour: Hour (0-23)
            minute: Minute (0-59)
            day_of_week: Day of week (mon-fri, sat, sun, etc.)
            **kwargs: Additional arguments passed to func

        Returns:
            Job ID if added successfully, None otherwise
        """
        if self._scheduler is None:
            logger.error("Scheduler not running")
            return None

        if job_id is None:
            job_id = f"cron_job_{len(self._jobs)}"

        if name is None:
            name = job_id

        trigger = CronTrigger(
            hour=hour,
            minute=minute,
            day_of_week=day_of_week,
        )

        try:
            job = self._scheduler.add_job(
                func=func,
                trigger=trigger,
                id=job_id,
                name=name,
                replace_existing=True,
                **kwargs,
            )

            self._jobs[job_id] = JobInfo(
                job_id=job_id,
                name=name,
                trigger_type="cron",
                next_run=job.next_run_time,
            )

            logger.info(f"Added cron job: {job_id}")
            return job_id

        except Exception as e:
            logger.error(f"Failed to add cron job: {e}")
            return None

    def add_one_time_job(
        self,
        func: Callable,
        run_at: datetime,
        job_id: str | None = None,
        name: str | None = None,
        **kwargs,
    ) -> str | None:
        """
        Add a one-time job.

        Args:
            func: Function to execute
            run_at: When to run the job
            job_id: Unique job identifier
            name: Human-readable job name
            **kwargs: Additional arguments passed to func

        Returns:
            Job ID if added successfully, None otherwise
        """
        if self._scheduler is None:
            logger.error("Scheduler not running")
            return None

        if job_id is None:
            job_id = f"one_time_{len(self._jobs)}"

        if name is None:
            name = job_id

        try:
            self._scheduler.add_job(
                func=func,
                trigger="date",
                run_date=run_at,
                id=job_id,
                name=name,
                replace_existing=True,
                **kwargs,
            )

            self._jobs[job_id] = JobInfo(
                job_id=job_id,
                name=name,
                trigger_type="date",
                next_run=run_at,
            )

            logger.info(f"Added one-time job: {job_id} at {run_at}")
            return job_id

        except Exception as e:
            logger.error(f"Failed to add one-time job: {e}")
            return None

    def remove_job(self, job_id: str) -> bool:
        """
        Remove a scheduled job.

        Args:
            job_id: Job identifier

        Returns:
            True if job was removed
        """
        if self._scheduler is None:
            return False

        try:
            self._scheduler.remove_job(job_id)
            self._jobs.pop(job_id, None)
            self._job_results.pop(job_id, None)
            logger.info(f"Removed job: {job_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to remove job {job_id}: {e}")
            return False

    def pause_job(self, job_id: str) -> bool:
        """Pause a scheduled job."""
        if self._scheduler is None:
            return False

        try:
            self._scheduler.pause_job(job_id)
            if job_id in self._jobs:
                self._jobs[job_id].status = "paused"
            logger.info(f"Paused job: {job_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to pause job {job_id}: {e}")
            return False

    def resume_job(self, job_id: str) -> bool:
        """Resume a paused job."""
        if self._scheduler is None:
            return False

        try:
            self._scheduler.resume_job(job_id)
            if job_id in self._jobs:
                self._jobs[job_id].status = "scheduled"
            logger.info(f"Resumed job: {job_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to resume job {job_id}: {e}")
            return False

    def get_job(self, job_id: str) -> JobInfo | None:
        """Get information about a job."""
        return self._jobs.get(job_id)

    def get_all_jobs(self) -> list[JobInfo]:
        """Get all scheduled jobs."""
        return list(self._jobs.values())

    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._scheduler is not None and self._scheduler.running

    def get_running_jobs(self) -> list[str]:
        """Get IDs of currently running jobs."""
        if self._scheduler is None:
            return []
        return [job.id for job in self._scheduler.get_jobs()]

    def update_config(self, config: SchedulerConfig):
        """Update scheduler configuration."""
        was_running = self.is_running()

        if was_running:
            self.stop()

        self.config = config

        if was_running and config.enabled:
            self.start()


scheduler_service = SchedulerService()
