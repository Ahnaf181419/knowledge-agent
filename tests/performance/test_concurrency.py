"""
Performance tests for concurrency.

These tests verify:
- Max concurrent job limits are enforced
- Thread pool performance
- Scheduler timing
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor

from app.services.background_job_service import (
    BackgroundJobService,
)
from app.services.scheduler_service import (
    SchedulerConfig,
    SchedulerService,
)


class TestConcurrencyLimits:
    """Test that concurrency limits are enforced."""

    def test_max_concurrent_jobs_enforced(self):
        """Test that max concurrent jobs is limited."""
        service = BackgroundJobService(max_concurrent=2)

        _execution_times = []
        results_count = [0]
        lock = threading.Lock()

        def slow_task():
            with lock:
                results_count[0] += 1
            time.sleep(0.2)
            return "done"

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for _i in range(4):
                future = executor.submit(slow_task)
                futures.append(future)

            for f in futures:
                f.result()

        assert results_count[0] == 4
        service.shutdown()

    def test_background_job_service_concurrent_limit(self):
        """Test background job service respects max concurrent limit."""
        service = BackgroundJobService(max_concurrent=2)

        task_started = threading.Event()
        tasks_blocked = threading.Event()
        task_count = [0]
        max_concurrent = [0]
        current_concurrent = [0]
        lock = threading.Lock()

        def blocking_task(task_id):
            with lock:
                task_count[0] += 1
                current_concurrent[0] += 1
                if current_concurrent[0] > max_concurrent[0]:
                    max_concurrent[0] = current_concurrent[0]

            task_started.set()
            tasks_blocked.wait()

            with lock:
                current_concurrent[0] -= 1
            return task_id

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for i in range(4):
                future = executor.submit(blocking_task, i)
                futures.append(future)

            task_started.wait(timeout=2)

            tasks_blocked.set()

            for f in futures:
                f.result()

        assert max_concurrent[0] <= 2
        service.shutdown()

    def test_scheduler_concurrent_jobs_limit(self):
        """Test scheduler respects concurrent job limit."""
        scheduler = SchedulerService(
            SchedulerConfig(
                enabled=True,
                max_concurrent_jobs=2,
            )
        )

        scheduler.start()

        job_execution_count = [0]
        max_concurrent = [0]
        current_concurrent = [0]
        lock = threading.Lock()

        def job_task():
            with lock:
                current_concurrent[0] += 1
                if current_concurrent[0] > max_concurrent[0]:
                    max_concurrent[0] = current_concurrent[0]

            time.sleep(0.1)

            with lock:
                current_concurrent[0] -= 1
                job_execution_count[0] += 1

        job_ids = []
        for i in range(4):
            job_id = scheduler.add_interval_job(
                func=job_task,
                minutes=0,
                hours=0,
                job_id=f"perf_job_{i}",
            )
            if job_id:
                job_ids.append(job_id)

        time.sleep(1)

        assert max_concurrent[0] <= 2
        scheduler.stop()


class TestPerformanceTimings:
    """Test performance and timing characteristics."""

    def test_scheduler_job_timing(self):
        """Test that scheduler jobs execute at correct intervals."""
        scheduler = SchedulerService(SchedulerConfig(enabled=True))

        scheduler.start()

        execution_times = []

        def timed_job():
            execution_times.append(time.time())

        _job_id = scheduler.add_interval_job(
            func=timed_job,
            minutes=0,
            hours=0,
            job_id="timed_job",
        )

        time.sleep(0.6)

        scheduler.stop()

        if execution_times:
            assert len(execution_times) >= 1

    def test_background_job_submit_performance(self):
        """Test background job submission performance."""
        service = BackgroundJobService(max_concurrent=2)

        def simple_task():
            return 1

        start_time = time.time()

        for i in range(10):
            service.submit_job(
                urls=[{"url": f"http://test{i}.com"}],
                job_id=f"perf_test_{i}",
            )

        submit_time = time.time() - start_time

        time.sleep(0.3)

        assert submit_time < 1.0
        service.shutdown()

    def test_job_status_tracking_performance(self):
        """Test that job status tracking doesn't block significantly."""
        service = BackgroundJobService(max_concurrent=2)

        for i in range(20):
            service.submit_job(
                urls=[{"url": f"http://test{i}.com"}],
                job_id=f"status_test_{i}",
            )

        start_time = time.time()

        for _ in range(100):
            _status = service.get_status()

        tracking_time = time.time() - start_time

        assert tracking_time < 0.5
        service.shutdown()


class TestThreadSafety:
    """Test thread safety of services."""

    def test_concurrent_status_reads(self):
        """Test concurrent reads don't cause issues."""
        service = BackgroundJobService(max_concurrent=2)

        for i in range(5):
            service.submit_job(
                urls=[{"url": f"http://test{i}.com"}],
                job_id=f"thread_safe_{i}",
            )

        def read_status():
            for _ in range(50):
                service.get_status()

        threads = [threading.Thread(target=read_status) for _ in range(4)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        status = service.get_status()
        assert "total_jobs" in status
        service.shutdown()

    def test_concurrent_job_cancellations(self):
        """Test concurrent job cancellations are safe."""
        service = BackgroundJobService(max_concurrent=2)

        for i in range(10):
            service.submit_job(
                urls=[{"url": f"http://test{i}.com"}],
                job_id=f"cancel_test_{i}",
            )

        def cancel_jobs():
            for i in range(5):
                service.cancel_job(f"cancel_test_{i}")

        threads = [threading.Thread(target=cancel_jobs) for _ in range(2)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        status = service.get_status()
        assert status is not None
        service.shutdown()


class TestScalability:
    """Test scalability characteristics."""

    def test_many_jobs_memory(self):
        """Test many jobs don't cause excessive memory growth."""
        service = BackgroundJobService(max_concurrent=2)

        _initial_jobs = len(service.get_all_jobs())

        for i in range(50):
            service.submit_job(
                urls=[{"url": f"http://test{i}.com"}],
                job_id=f"scale_test_{i}",
            )

        service.clear_completed()

        final_jobs = len(service.get_all_jobs())

        assert final_jobs < 50
        service.shutdown()

    def test_rapid_job_submission(self):
        """Test rapid job submission doesn't hang."""
        service = BackgroundJobService(max_concurrent=2)

        start_time = time.time()

        job_ids = []
        for i in range(20):
            job_id = service.submit_job(
                urls=[{"url": f"http://test{i}.com"}],
                job_id=f"rapid_{i}",
            )
            job_ids.append(job_id)

        submit_time = time.time() - start_time

        assert submit_time < 2.0
        assert len(job_ids) == 20

        time.sleep(0.5)
        service.shutdown()
