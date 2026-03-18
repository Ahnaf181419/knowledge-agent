"""Unit tests for scheduler_service module."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch


class TestSchedulerConfig:
    """Tests for SchedulerConfig class."""

    def test_default_values(self):
        from app.services.scheduler_service import SchedulerConfig

        config = SchedulerConfig()

        assert config.enabled is True
        assert config.max_concurrent_jobs == 2
        assert config.coalesce is True
        assert config.max_instances == 1

    def test_custom_values(self):
        from app.services.scheduler_service import SchedulerConfig

        config = SchedulerConfig(
            enabled=False,
            max_concurrent_jobs=4,
            coalesce=False,
            max_instances=3,
        )

        assert config.enabled is False
        assert config.max_concurrent_jobs == 4
        assert config.coalesce is False
        assert config.max_instances == 3


class TestJobInfo:
    """Tests for JobInfo dataclass."""

    def test_default_values(self):
        from app.services.scheduler_service import JobInfo

        job = JobInfo(job_id="test_job", name="Test Job", trigger_type="interval")

        assert job.job_id == "test_job"
        assert job.name == "Test Job"
        assert job.trigger_type == "interval"
        assert job.next_run is None
        assert job.last_run is None
        assert job.status == "scheduled"

    def test_custom_values(self):
        from app.services.scheduler_service import JobInfo

        now = datetime.now()
        job = JobInfo(
            job_id="test_job",
            name="Test Job",
            trigger_type="cron",
            next_run=now,
            last_run=now - timedelta(hours=1),
            status="running",
        )

        assert job.next_run == now
        assert job.last_run == now - timedelta(hours=1)
        assert job.status == "running"


class TestSchedulerService:
    """Tests for SchedulerService class."""

    def test_init_default(self):
        from app.services.scheduler_service import SchedulerService

        service = SchedulerService()

        assert service.config.enabled is True
        assert service._scheduler is None
        assert service._jobs == {}

    def test_init_custom_config(self):
        from app.services.scheduler_service import SchedulerConfig, SchedulerService

        config = SchedulerConfig(enabled=False)
        service = SchedulerService(config)

        assert service.config.enabled is False

    @patch("app.services.scheduler_service.BackgroundScheduler")
    def test_start_scheduler_disabled(self, mock_scheduler_class):
        from app.services.scheduler_service import SchedulerConfig, SchedulerService

        config = SchedulerConfig(enabled=False)
        service = SchedulerService(config)

        service.start()

        mock_scheduler_class.assert_not_called()

    @patch("app.services.scheduler_service.BackgroundScheduler")
    def test_start_scheduler(self, mock_scheduler_class):
        from app.services.scheduler_service import SchedulerService

        mock_scheduler = MagicMock()
        mock_scheduler.running = True
        mock_scheduler_class.return_value = mock_scheduler

        service = SchedulerService()
        service.start()

        assert service.is_running() is True
        mock_scheduler.start.assert_called_once()

    @patch("app.services.scheduler_service.BackgroundScheduler")
    def test_start_already_running(self, mock_scheduler_class):
        from app.services.scheduler_service import SchedulerService

        mock_scheduler = MagicMock()
        mock_scheduler.running = True
        mock_scheduler_class.return_value = mock_scheduler

        service = SchedulerService()
        service.start()
        service.start()

        mock_scheduler.start.assert_called_once()

    @patch("app.services.scheduler_service.BackgroundScheduler")
    def test_stop_scheduler(self, mock_scheduler_class):
        from app.services.scheduler_service import SchedulerService

        mock_scheduler = MagicMock()
        mock_scheduler.running = True
        mock_scheduler_class.return_value = mock_scheduler

        service = SchedulerService()
        service._scheduler = mock_scheduler
        service.stop()

        mock_scheduler.shutdown.assert_called_once()

    def test_stop_scheduler_not_started(self):
        from app.services.scheduler_service import SchedulerService

        service = SchedulerService()
        service.stop()

        assert service.is_running() is False

    @patch("app.services.scheduler_service.BackgroundScheduler")
    @patch("app.services.scheduler_service.IntervalTrigger")
    def test_add_interval_job(self, mock_trigger_class, mock_scheduler_class):
        from app.services.scheduler_service import SchedulerService

        mock_scheduler = MagicMock()
        mock_scheduler.running = False
        mock_job = MagicMock()
        mock_job.next_run_time = datetime.now() + timedelta(minutes=30)
        mock_scheduler.add_job.return_value = mock_job
        mock_scheduler_class.return_value = mock_scheduler

        service = SchedulerService()
        service.start()

        def dummy_func():
            pass

        job_id = service.add_interval_job(dummy_func, minutes=30, job_id="test_job")

        assert job_id == "test_job"
        assert "test_job" in service._jobs

    @patch("app.services.scheduler_service.BackgroundScheduler")
    @patch("app.services.scheduler_service.CronTrigger")
    def test_add_cron_job(self, mock_trigger_class, mock_scheduler_class):
        from app.services.scheduler_service import SchedulerService

        mock_scheduler = MagicMock()
        mock_scheduler.running = False
        mock_job = MagicMock()
        mock_job.next_run_time = datetime.now() + timedelta(hours=1)
        mock_scheduler.add_job.return_value = mock_job
        mock_scheduler_class.return_value = mock_scheduler

        service = SchedulerService()
        service.start()

        def dummy_func():
            pass

        job_id = service.add_cron_job(dummy_func, job_id="cron_job", hour=2, minute=0)

        assert job_id == "cron_job"

    @patch("app.services.scheduler_service.BackgroundScheduler")
    def test_add_one_time_job(self, mock_scheduler_class):
        from app.services.scheduler_service import SchedulerService

        mock_scheduler = MagicMock()
        mock_scheduler.running = False
        mock_job = MagicMock()
        mock_scheduler.add_job.return_value = mock_job
        mock_scheduler_class.return_value = mock_scheduler

        service = SchedulerService()
        service.start()

        def dummy_func():
            pass

        run_at = datetime.now() + timedelta(hours=1)
        job_id = service.add_one_time_job(dummy_func, run_at=run_at, job_id="one_time_job")

        assert job_id == "one_time_job"

    @patch("app.services.scheduler_service.BackgroundScheduler")
    def test_add_job_scheduler_not_running(self, mock_scheduler_class):
        from app.services.scheduler_service import SchedulerService

        service = SchedulerService()

        def dummy_func():
            pass

        job_id = service.add_interval_job(dummy_func, minutes=30)

        assert job_id is None

    @patch("app.services.scheduler_service.BackgroundScheduler")
    def test_remove_job(self, mock_scheduler_class):
        from app.services.scheduler_service import SchedulerService

        mock_scheduler = MagicMock()
        mock_scheduler.running = False
        mock_scheduler_class.return_value = mock_scheduler

        service = SchedulerService()
        service.start()

        mock_scheduler.remove_job = MagicMock()

        service._jobs["test_job"] = MagicMock()

        result = service.remove_job("test_job")

        assert result is True
        assert "test_job" not in service._jobs

    @patch("app.services.scheduler_service.BackgroundScheduler")
    def test_pause_job(self, mock_scheduler_class):
        from app.services.scheduler_service import SchedulerService

        mock_scheduler = MagicMock()
        mock_scheduler.running = False
        mock_scheduler_class.return_value = mock_scheduler

        service = SchedulerService()
        service.start()

        mock_scheduler.pause_job = MagicMock()

        from app.services.scheduler_service import JobInfo

        service._jobs["test_job"] = JobInfo(job_id="test_job", name="Test", trigger_type="interval")

        result = service.pause_job("test_job")

        assert result is True
        assert service._jobs["test_job"].status == "paused"

    @patch("app.services.scheduler_service.BackgroundScheduler")
    def test_resume_job(self, mock_scheduler_class):
        from app.services.scheduler_service import SchedulerService

        mock_scheduler = MagicMock()
        mock_scheduler.running = False
        mock_scheduler_class.return_value = mock_scheduler

        service = SchedulerService()
        service.start()

        mock_scheduler.resume_job = MagicMock()

        from app.services.scheduler_service import JobInfo

        service._jobs["test_job"] = JobInfo(
            job_id="test_job", name="Test", trigger_type="interval", status="paused"
        )

        result = service.resume_job("test_job")

        assert result is True
        assert service._jobs["test_job"].status == "scheduled"

    @patch("app.services.scheduler_service.BackgroundScheduler")
    def test_get_job(self, mock_scheduler_class):
        from app.services.scheduler_service import JobInfo, SchedulerService

        service = SchedulerService()

        job_info = JobInfo(job_id="test_job", name="Test", trigger_type="interval")
        service._jobs["test_job"] = job_info

        result = service.get_job("test_job")

        assert result == job_info

    @patch("app.services.scheduler_service.BackgroundScheduler")
    def test_get_all_jobs(self, mock_scheduler_class):
        from app.services.scheduler_service import JobInfo, SchedulerService

        service = SchedulerService()

        job1 = JobInfo(job_id="job1", name="Job 1", trigger_type="interval")
        job2 = JobInfo(job_id="job2", name="Job 2", trigger_type="cron")
        service._jobs["job1"] = job1
        service._jobs["job2"] = job2

        result = service.get_all_jobs()

        assert len(result) == 2

    @patch("app.services.scheduler_service.BackgroundScheduler")
    def test_get_running_jobs(self, mock_scheduler_class):
        from app.services.scheduler_service import SchedulerService

        mock_scheduler = MagicMock()
        mock_scheduler.running = True
        mock_job = MagicMock()
        mock_job.id = "test_job"
        mock_scheduler.get_jobs.return_value = [mock_job]
        mock_scheduler_class.return_value = mock_scheduler

        service = SchedulerService()
        service._scheduler = mock_scheduler

        result = service.get_running_jobs()

        assert "test_job" in result

    def test_is_running_not_started(self):
        from app.services.scheduler_service import SchedulerService

        service = SchedulerService()

        assert service.is_running() is False

    @patch("app.services.scheduler_service.BackgroundScheduler")
    def test_update_config(self, mock_scheduler_class):
        from app.services.scheduler_service import SchedulerConfig, SchedulerService

        mock_scheduler = MagicMock()
        mock_scheduler.running = True
        mock_scheduler_class.return_value = mock_scheduler

        service = SchedulerService()
        service.start()

        new_config = SchedulerConfig(enabled=False)
        service.update_config(new_config)

        assert service.config.enabled is False
