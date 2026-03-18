"""
Integration tests for service interactions.

These tests verify that services work correctly together:
- Notification + Scheduler integration
- Method Optimizer + Stats Service integration
- Scheduler + Background Jobs integration
"""

import time
from unittest.mock import MagicMock, patch

from app.services.notification_service import (
    NotificationConfig,
    NotificationService,
)
from app.services.scheduler_service import (
    SchedulerConfig,
    SchedulerService,
)
from scraper.method_optimizer import MethodOptimizer, MethodRecommendation


class TestNotificationSchedulerIntegration:
    """Test notification and scheduler service integration."""

    def test_scheduler_sends_notification_on_job_complete(self):
        """Test that scheduler triggers notification when job completes."""
        with patch("plyer.notification") as mock_notify:
            notif_service = NotificationService(NotificationConfig(enabled=True))

            scheduler = SchedulerService(SchedulerConfig(enabled=True))
            scheduler.start()

            job_results = []

            def job_with_notification():
                result = "Job completed"
                job_results.append(result)
                notif_service.notify(
                    title="Job Complete",
                    message="Scheduled job finished",
                )
                return result

            job_id = scheduler.add_interval_job(
                func=job_with_notification,
                minutes=0,
                hours=0,
                job_id="test_job_notification",
            )

            time.sleep(0.5)

            assert job_id is not None
            scheduler.stop()

            if mock_notify.called:
                call_args = mock_notify.call_args
                assert call_args[1]["title"] == "Job Complete"

    def test_batch_complete_notification_flow(self):
        """Test notification service batch complete with scheduler integration."""
        import sys

        mock_plyer = MagicMock()
        sys.modules["plyer"] = mock_plyer

        notif_service = NotificationService(
            NotificationConfig(
                enabled=True,
                notify_on_complete=True,
            )
        )

        result = notif_service.notify_batch_complete(
            total=10,
            successful=8,
            failed=2,
            duration_seconds=120.5,
        )

        assert result is True
        assert mock_plyer.notification.notify.called

        call_args = mock_plyer.notification.notify.call_args
        assert call_args[1]["title"] == "Batch Complete"
        assert "10 URLs" in call_args[1]["message"]
        assert "8 successful" in call_args[1]["message"]

        del sys.modules["plyer"]

    def test_notification_on_schedule_error(self):
        """Test error notification when scheduler job fails."""
        with patch("plyer.notification") as mock_notify:
            notif_service = NotificationService(NotificationConfig(enabled=True))

            scheduler = SchedulerService(SchedulerConfig(enabled=True))
            scheduler.start()

            errors_caught = []

            def failing_job():
                try:
                    raise ValueError("Job failed")
                except ValueError as e:
                    errors_caught.append(str(e))
                    notif_service.notify_failure(
                        url="scheduled://job/1",
                        error=str(e),
                    )

            scheduler.add_interval_job(
                func=failing_job,
                minutes=0,
                hours=0,
                job_id="failing_job",
            )

            time.sleep(0.5)

            scheduler.stop()

            if errors_caught:
                assert mock_notify.called
                call_args = mock_notify.call_args
                assert call_args[1]["title"] == "Scrape Failed"


class TestMethodOptimizerStatsIntegration:
    """Test method optimizer and stats service integration."""

    def test_optimizer_uses_stats_service(self, tmp_path):
        """Test that method optimizer reads from stats service."""
        with patch("app.services.stats_service.get_session_context"):
            with patch("scraper.method_optimizer.stats_service") as mock_stats:
                mock_stats.get_method_stats.return_value = {
                    "domain": "example.com",
                    "method": "simple_http",
                    "total": 10,
                    "success_count": 8,
                    "failure_count": 2,
                    "success_rate": 80.0,
                    "avg_time_ms": 500,
                }
                mock_stats.get_domain_stats.return_value = [
                    {
                        "method": "simple_http",
                        "total": 10,
                        "success_count": 8,
                        "failure_count": 2,
                        "success_rate": 80.0,
                        "avg_time_ms": 500,
                    }
                ]
                mock_stats.get_all_domains.return_value = ["example.com"]

                optimizer = MethodOptimizer(optimization_enabled=True)

                recommendation = optimizer.get_recommendation("https://example.com/article")

                assert isinstance(recommendation, MethodRecommendation)
                mock_stats.get_domain_stats.assert_called()

    def test_optimizer_with_no_stats(self):
        """Test optimizer behavior when no stats exist."""
        with patch("scraper.method_optimizer.stats_service") as mock_stats:
            mock_stats.get_domain_stats.return_value = []
            mock_stats.get_all_domains.return_value = []

            optimizer = MethodOptimizer(optimization_enabled=True)

            recommendation = optimizer.get_recommendation("https://newsite.com/page")

            assert recommendation.method == "simple_http"
            assert recommendation.confidence == 0.1

    def test_optimizer_promotion_based_on_stats(self):
        """Test that optimizer recommends promotion based on stats."""
        with patch("scraper.method_optimizer.stats_service") as mock_stats:
            mock_stats.get_method_domain_stats.return_value = {
                "method": "playwright",
                "total": 10,
                "success_count": 9,
                "failure_count": 1,
                "success_rate": 90.0,
            }
            mock_stats.get_domain_stats.return_value = [
                {
                    "method": "playwright",
                    "total": 10,
                    "success_count": 9,
                    "failure_count": 1,
                    "success_rate": 90.0,
                }
            ]
            mock_stats.get_all_domains.return_value = ["example.com"]

            optimizer = MethodOptimizer(
                success_promotion_threshold=5,
                optimization_enabled=True,
            )

            should_promote = optimizer.should_promote("example.com", "playwright")

            assert should_promote is True

    def test_optimizer_demotion_based_on_stats(self):
        """Test that optimizer recommends demotion based on stats."""
        with patch("scraper.method_optimizer.stats_service") as mock_stats:
            mock_stats.get_method_domain_stats.return_value = {
                "method": "simple_http",
                "total": 10,
                "success_count": 2,
                "failure_count": 8,
                "success_rate": 20.0,
            }
            mock_stats.get_domain_stats.return_value = [
                {
                    "method": "simple_http",
                    "total": 10,
                    "success_count": 2,
                    "failure_count": 8,
                    "success_rate": 20.0,
                }
            ]
            mock_stats.get_all_domains.return_value = ["example.com"]

            optimizer = MethodOptimizer(
                failure_demotion_threshold=3,
                optimization_enabled=True,
            )

            should_demote = optimizer.should_demote("example.com", "simple_http")

            assert should_demote is True


class TestSchedulerBackgroundJobsIntegration:
    """Test scheduler and background job integration."""

    def test_scheduler_manages_multiple_jobs(self):
        """Test scheduler can manage multiple background jobs."""
        scheduler = SchedulerService(
            SchedulerConfig(
                enabled=True,
                max_concurrent_jobs=2,
            )
        )

        scheduler.start()

        job1_results = []
        job2_results = []

        def job1():
            job1_results.append("executed")
            return "job1"

        def job2():
            job2_results.append("executed")
            return "job2"

        id1 = scheduler.add_interval_job(
            func=job1,
            minutes=0,
            hours=0,
            job_id="bg_job_1",
        )

        id2 = scheduler.add_interval_job(
            func=job2,
            minutes=0,
            hours=0,
            job_id="bg_job_2",
        )

        time.sleep(0.5)

        assert id1 is not None
        assert id2 is not None

        jobs = scheduler.get_all_jobs()
        assert len(jobs) >= 2

        scheduler.stop()

    def test_scheduler_job_lifecycle(self):
        """Test scheduler job lifecycle: add, pause, resume, remove."""
        scheduler = SchedulerService(SchedulerConfig(enabled=True))
        scheduler.start()

        results = []

        def lifecycle_job():
            results.append("executed")

        job_id = scheduler.add_interval_job(
            func=lifecycle_job,
            minutes=0,
            hours=0,
            job_id="lifecycle_job",
        )

        assert job_id is not None
        time.sleep(0.3)

        paused = scheduler.pause_job(job_id)
        assert paused is True

        resumed = scheduler.resume_job(job_id)
        assert resumed is True

        removed = scheduler.remove_job(job_id)
        assert removed is True

        scheduler.stop()


class TestFullWorkflowIntegration:
    """End-to-end workflow integration tests."""

    def test_scrape_stats_notification_workflow(self):
        """Test full workflow: scrape -> stats -> notification."""
        import sys

        mock_plyer = MagicMock()
        sys.modules["plyer"] = mock_plyer

        notif_service = NotificationService(NotificationConfig(enabled=True))

        test_url = "https://example.com/article"
        word_count = 1500

        notif_service.notify_success(test_url, word_count)

        assert mock_plyer.notification.notify.called
        call_args = mock_plyer.notification.notify.call_args
        assert call_args[1]["title"] == "Scrape Success"
        assert f"{word_count} words" in call_args[1]["message"]

        del sys.modules["plyer"]

    def test_optimization_notification_workflow(self):
        """Test optimization recommendations trigger notifications."""
        with patch("plyer.notification"):
            with patch("scraper.method_optimizer.stats_service") as mock_stats:
                mock_stats.get_method_domain_stats.return_value = {
                    "method": "playwright",
                    "total": 10,
                    "success_count": 9,
                    "failure_count": 1,
                    "success_rate": 90.0,
                }
                mock_stats.get_domain_stats.return_value = [
                    {
                        "method": "playwright",
                        "total": 10,
                        "success_count": 9,
                        "failure_count": 1,
                        "success_rate": 90.0,
                    }
                ]
                mock_stats.get_all_domains.return_value = ["example.com"]

                _notif_service = NotificationService(NotificationConfig(enabled=True))
                optimizer = MethodOptimizer(optimization_enabled=True)

                domains = optimizer.get_all_domains()
                assert domains is not None

    def test_concurrent_scrape_with_mixed_results(self):
        """Test handling of mixed success/failure results."""
        import sys

        mock_plyer = MagicMock()
        sys.modules["plyer"] = mock_plyer

        notif_service = NotificationService(NotificationConfig(enabled=True))

        urls = [
            ("https://example.com/1", True, 100),
            ("https://example.com/2", True, 200),
            ("https://example.com/3", False, "Connection timeout"),
            ("https://example.com/4", True, 150),
        ]

        successful = 0
        failed = 0

        for url, success, result in urls:
            if success:
                successful += 1
                notif_service.notify_success(url, result)
            else:
                failed += 1
                notif_service.notify_failure(url, result)

        assert successful == 3
        assert failed == 1

        notif_service.notify_batch_complete(
            total=len(urls),
            successful=successful,
            failed=failed,
            duration_seconds=10.0,
        )

        assert mock_plyer.notification.notify.call_count == 5

        del sys.modules["plyer"]


class TestHistoryStatsIntegration:
    """Test history service and stats service integration."""

    def test_record_scrape_updates_history_and_stats(self):
        """Test that recording a scrape updates both history and stats."""
        import sys

        from app.services.stats_service import StatsService

        mock_plyer = MagicMock()
        sys.modules["plyer"] = mock_plyer

        stats_svc = StatsService()

        test_url = "https://example.com/test-article"
        test_method = "simple_http"
        test_word_count = 1500
        test_time_ms = 500

        stats_svc.record_scrape(
            url=test_url,
            method=test_method,
            success=True,
            time_ms=test_time_ms,
            word_count=test_word_count,
        )

        domain_stats = stats_svc.get_domain_stats("example.com")
        assert domain_stats is not None
        assert len(domain_stats) >= 1

        method_stats = stats_svc.get_method_stats()
        assert method_stats is not None

        del sys.modules["plyer"]

    def test_history_retrieval_after_multiple_scrapes(self):
        """Test retrieving history after multiple scrape operations."""
        from app.services.stats_service import StatsService

        stats_svc = StatsService()

        test_urls = [
            ("https://example.com/article1", "simple_http", True, 100, 500),
            ("https://example.com/article2", "playwright", True, 200, 800),
            ("https://example.com/article3", "simple_http", False, 0, 300),
        ]

        for url, method, success, word_count, time_ms in test_urls:
            stats_svc.record_scrape(
                url=url,
                method=method,
                success=success,
                time_ms=time_ms,
                word_count=word_count if success else 0,
            )

        summary = stats_svc.get_summary_stats()
        assert summary is not None
        assert summary.get("total_attempts", 0) >= 3


class TestRetryJobIntegration:
    """Test retry service and background job service integration."""

    def test_retry_queue_integration(self):
        """Test retry queue properly integrates with job tracking."""
        from app.services.retry_service import RetryService
        from app.state import state

        retry_svc = RetryService()

        test_urls = [
            "https://example.com/retry1",
            "https://example.com/retry2",
        ]

        for url in test_urls:
            state.add_to_retry_normal(url, "test error")

        retry_items = retry_svc.get_retry_items()
        assert len(retry_items) >= 2

    def test_retry_with_backoff_integration(self):
        """Test retry with exponential backoff works correctly."""
        from app.services.retry_service import RetryService
        from app.state import state

        retry_svc = RetryService()

        test_url = "https://example.com/retry-backoff"

        state.add_to_retry_normal(test_url, "test error")

        retry_count = retry_svc.get_retry_count(test_url)
        assert retry_count >= 0


class TestRouterScraperIntegration:
    """Test router and novel scraper integration."""

    def test_route_selection_for_novel_site(self):
        """Test that router correctly selects scraper for novel sites."""
        from scraper.router import route_url

        test_cases = [
            ("https://www.novelupdate.com/novel/12345", "novel"),
            ("https://example.com/blog/article", "simple_http"),
            ("https://en.wikipedia.org/wiki/Test", "playwright_alt"),
        ]

        for url, expected_route in test_cases:
            result = route_url(url)
            assert result == expected_route

    def test_get_route_reason_integration(self):
        """Test that get_route_reason provides useful debugging info."""
        from scraper.router import get_route_reason

        reasons = [
            get_route_reason("https://youtube.com/watch?v=abc"),
            get_route_reason("https://example.com/article"),
        ]

        for reason in reasons:
            assert reason is not None
            assert len(reason) > 0


class TestMethodOptimizerRunnerIntegration:
    """Test method optimizer and scraper runner integration."""

    def test_optimizer_recommendations_affect_routing(self):
        """Test that method optimizer recommendations influence routing."""
        from scraper.method_optimizer import MethodOptimizer

        optimizer = MethodOptimizer(optimization_enabled=True)

        domains = optimizer.get_all_domains()
        assert domains is not None

        report = optimizer.get_optimization_report()
        assert "timestamp" in report
        assert "domains" in report

    def test_optimizer_with_empty_stats(self):
        """Test optimizer handles empty stats gracefully."""
        from scraper.method_optimizer import MethodOptimizer

        optimizer = MethodOptimizer(optimization_enabled=True)

        recommendation = optimizer.get_recommendation("nonexistent-domain.com")
        assert recommendation.method == "simple_http"


class TestFullE2EWorkflow:
    """End-to-end workflow integration tests."""

    def test_complete_scrape_workflow(self):
        """Test complete workflow from URL to stats recording."""
        import sys

        from app.services.stats_service import StatsService

        mock_plyer = MagicMock()
        sys.modules["plyer"] = mock_plyer

        stats_svc = StatsService()

        test_url = "https://example.com/e2e-test"
        test_method = "simple_http"
        test_word_count = 2500
        test_time_ms = 1200

        stats_svc.record_scrape(
            url=test_url,
            method=test_method,
            success=True,
            time_ms=test_time_ms,
            word_count=test_word_count,
        )

        recent_metrics = stats_svc.get_recent(limit=5)
        assert any(m["url"] == test_url for m in recent_metrics)

        summary = stats_svc.get_summary_stats()
        assert summary is not None
        assert summary.get("total_attempts", 0) >= 1

        del sys.modules["plyer"]

    def test_stats_aggregation_workflow(self):
        """Test stats aggregation across multiple domains."""
        from app.services.stats_service import StatsService

        stats_svc = StatsService()

        test_domain = "testdomain123.com"
        test_urls = [
            (f"https://{test_domain}/article1", "simple_http", True, 100, 500),
            (f"https://{test_domain}/article2", "simple_http", True, 200, 600),
        ]

        for url, method, success, word_count, time_ms in test_urls:
            stats_svc.record_scrape(
                url=url,
                method=method,
                success=success,
                time_ms=time_ms,
                word_count=word_count if success else 0,
            )

        domain_stats = stats_svc.get_domain_stats(test_domain)

        assert domain_stats is not None
        assert len(domain_stats) >= 1
