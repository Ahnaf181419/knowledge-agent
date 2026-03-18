"""
Background Jobs Service Module

Manages background scraping jobs with concurrency control.
Integrates with the scheduler service for periodic scraping.

Usage:
    from app.services.background_job_service import background_job_service

    # Start background scraping
    background_job_service.start_batch(urls)

    # Check status
    status = background_job_service.get_status()
"""

import logging
import threading
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


class JobStatus:
    """Status of a background job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BackgroundJob:
    """Represents a background scraping job."""

    job_id: str
    urls: list[dict]
    status: str = JobStatus.PENDING
    results: list[dict] = field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    _future: Future | None = None


class BackgroundJobService:
    """
    Background job service with concurrency control.

    Manages scraping jobs in the background with:
    - Max 2-3 concurrent jobs (configurable)
    - Thread-safe job tracking
    - Progress reporting
    - Integration with scheduler service
    """

    def __init__(self, max_concurrent: int = 2):
        self._max_concurrent = max_concurrent
        self._executor = ThreadPoolExecutor(max_workers=max_concurrent)
        self._jobs: dict[str, BackgroundJob] = {}
        self._lock = threading.Lock()
        self._running_count = 0

    def submit_job(
        self,
        urls: list[dict],
        job_id: str | None = None,
        on_complete: Callable | None = None,
    ) -> str:
        """
        Submit a new scraping job.

        Args:
            urls: List of URL entries to scrape
            job_id: Optional job identifier (auto-generated if not provided)
            on_complete: Optional callback when job completes

        Returns:
            Job ID
        """
        if job_id is None:
            job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        job = BackgroundJob(
            job_id=job_id,
            urls=urls,
            status=JobStatus.PENDING,
        )

        with self._lock:
            self._jobs[job_id] = job

        future = self._executor.submit(
            self._run_job,
            job,
            on_complete,
        )
        job._future = future

        with self._lock:
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now()
            self._running_count += 1

        logger.info(f"Submitted job {job_id} with {len(urls)} URLs")
        return job_id

    def _run_job(self, job: BackgroundJob, on_complete: Callable | None):
        """Execute the scraping job."""
        from scraper.runner import ScraperRunner

        try:
            runner = ScraperRunner()
            result = runner.run(job.urls, force_sync=True)

            if not isinstance(result, list):
                logger.warning(f"Job {job.job_id} submitted as nested job: {result}")
                return

            results: list[dict] = result

            with self._lock:
                job.results = results
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.now()
                self._running_count = max(0, self._running_count - 1)

            logger.info(f"Job {job.job_id} completed with {len(results)} results")

            if on_complete:
                try:
                    on_complete(results)
                except Exception as e:
                    logger.warning(f"Job completion callback failed: {e}")

        except Exception as e:
            with self._lock:
                job.status = JobStatus.FAILED
                job.error = str(e)
                job.completed_at = datetime.now()
                self._running_count = max(0, self._running_count - 1)

            logger.error(f"Job {job.job_id} failed: {e}")

    def get_job(self, job_id: str) -> BackgroundJob | None:
        """Get job by ID."""
        with self._lock:
            return self._jobs.get(job_id)

    def get_all_jobs(self) -> list[BackgroundJob]:
        """Get all jobs."""
        with self._lock:
            return list(self._jobs.values())

    def get_status(self) -> dict:
        """Get overall job service status."""
        with self._lock:
            return {
                "max_concurrent": self._max_concurrent,
                "running": self._running_count,
                "total_jobs": len(self._jobs),
                "pending": sum(1 for j in self._jobs.values() if j.status == JobStatus.PENDING),
                "completed": sum(1 for j in self._jobs.values() if j.status == JobStatus.COMPLETED),
                "failed": sum(1 for j in self._jobs.values() if j.status == JobStatus.FAILED),
            }

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending/running job."""
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return False

            if job.status == JobStatus.PENDING:
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.now()
                logger.info(f"Job {job_id} cancelled")
                return True
            elif job.status == JobStatus.RUNNING and job._future:
                cancelled = job._future.cancel()
                if cancelled:
                    job.status = JobStatus.CANCELLED
                    job.completed_at = datetime.now()
                    self._running_count = max(0, self._running_count - 1)
                return cancelled

        return False

    def clear_completed(self):
        """Clear completed/failed/cancelled jobs."""
        with self._lock:
            self._jobs = {
                job_id: job
                for job_id, job in self._jobs.items()
                if job.status in (JobStatus.PENDING, JobStatus.RUNNING)
            }

    def shutdown(self, wait: bool = True):
        """Shutdown the executor."""
        self._executor.shutdown(wait=wait)


background_job_service = BackgroundJobService()
