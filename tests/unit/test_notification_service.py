"""Unit tests for notification_service module."""

from unittest.mock import patch


class TestNotificationLevel:
    """Tests for NotificationLevel enum."""

    def test_notification_levels(self):
        from app.services.notification_service import NotificationLevel

        assert NotificationLevel.INFO.value == "info"
        assert NotificationLevel.SUCCESS.value == "success"
        assert NotificationLevel.WARNING.value == "warning"
        assert NotificationLevel.ERROR.value == "error"


class TestNotificationConfig:
    """Tests for NotificationConfig dataclass."""

    def test_default_values(self):
        from app.services.notification_service import NotificationConfig

        config = NotificationConfig()

        assert config.enabled is True
        assert config.notify_on_success is True
        assert config.notify_on_failure is True
        assert config.notify_on_complete is True

    def test_custom_values(self):
        from app.services.notification_service import NotificationConfig

        config = NotificationConfig(
            enabled=False,
            notify_on_success=False,
            notify_on_failure=False,
            notify_on_complete=False,
        )

        assert config.enabled is False
        assert config.notify_on_success is False
        assert config.notify_on_failure is False
        assert config.notify_on_complete is False


class TestNotificationService:
    """Tests for NotificationService class."""

    @patch("plyer.notification")
    def test_init_with_notifications_enabled(self, mock_notification):
        from app.services.notification_service import NotificationConfig, NotificationService

        config = NotificationConfig(enabled=True)
        service = NotificationService(config)

        assert service._notifier is not None

    @patch("plyer.notification")
    def test_init_with_notifications_disabled(self, mock_notification):
        from app.services.notification_service import NotificationConfig, NotificationService

        config = NotificationConfig(enabled=False)
        service = NotificationService(config)

        assert service._notifier is None

    @patch("plyer.notification")
    def test_notify_disabled(self, mock_notification):
        from app.services.notification_service import NotificationConfig, NotificationService

        config = NotificationConfig(enabled=False)
        service = NotificationService(config)

        result = service.notify(title="Test", message="Message")

        assert result is False
        mock_notification.notify.assert_not_called()

    @patch("plyer.notification")
    def test_notify_success(self, mock_notification):
        from app.services.notification_service import NotificationConfig, NotificationService

        config = NotificationConfig(enabled=True)
        service = NotificationService(config)

        result = service.notify(title="Test", message="Message")

        assert result is True
        mock_notification.notify.assert_called_once()

    @patch("plyer.notification")
    def test_notify_with_level(self, mock_notification):
        from app.services.notification_service import (
            NotificationConfig,
            NotificationLevel,
            NotificationService,
        )

        config = NotificationConfig(enabled=True)
        service = NotificationService(config)

        service.notify(title="Test", message="Message", level=NotificationLevel.WARNING)

        call_kwargs = mock_notification.notify.call_args.kwargs
        assert call_kwargs["title"] == "Test"
        assert call_kwargs["message"] == "Message"
        assert call_kwargs["app_name"] == "KnowledgeAgent"

    @patch("plyer.notification")
    def test_notify_failure_exception(self, mock_notification):
        from app.services.notification_service import NotificationConfig, NotificationService

        mock_notification.notify.side_effect = Exception("Notification failed")

        config = NotificationConfig(enabled=True)
        service = NotificationService(config)

        result = service.notify(title="Test", message="Message")

        assert result is False

    @patch("plyer.notification")
    def test_notify_success_url(self, mock_notification):
        from app.services.notification_service import NotificationConfig, NotificationService

        config = NotificationConfig(enabled=True, notify_on_success=True)
        service = NotificationService(config)

        result = service.notify_success("https://example.com/article", 500)

        assert result is True
        mock_notification.notify.assert_called_once()

    @patch("plyer.notification")
    def test_notify_success_disabled(self, mock_notification):
        from app.services.notification_service import NotificationConfig, NotificationService

        config = NotificationConfig(enabled=True, notify_on_success=False)
        service = NotificationService(config)

        result = service.notify_success("https://example.com/article", 500)

        assert result is False
        mock_notification.notify.assert_not_called()

    @patch("plyer.notification")
    def test_notify_failure_url(self, mock_notification):
        from app.services.notification_service import NotificationConfig, NotificationService

        config = NotificationConfig(enabled=True, notify_on_failure=True)
        service = NotificationService(config)

        result = service.notify_failure("https://example.com/article", "Connection timeout")

        assert result is True

    @patch("plyer.notification")
    def test_notify_failure_disabled(self, mock_notification):
        from app.services.notification_service import NotificationConfig, NotificationService

        config = NotificationConfig(enabled=True, notify_on_failure=False)
        service = NotificationService(config)

        result = service.notify_failure("https://example.com/article", "Connection timeout")

        assert result is False

    @patch("plyer.notification")
    def test_notify_batch_complete_success(self, mock_notification):
        from app.services.notification_service import NotificationConfig, NotificationService

        config = NotificationConfig(enabled=True, notify_on_complete=True)
        service = NotificationService(config)

        result = service.notify_batch_complete(
            total=10,
            successful=10,
            failed=0,
            duration_seconds=60.0,
        )

        assert result is True
        mock_notification.notify.assert_called_once()

    @patch("plyer.notification")
    def test_notify_batch_complete_with_failures(self, mock_notification):
        from app.services.notification_service import NotificationConfig, NotificationService

        config = NotificationConfig(enabled=True, notify_on_complete=True)
        service = NotificationService(config)

        result = service.notify_batch_complete(
            total=10,
            successful=7,
            failed=3,
            duration_seconds=60.0,
        )

        assert result is True

    @patch("plyer.notification")
    def test_notify_batch_complete_disabled(self, mock_notification):
        from app.services.notification_service import NotificationConfig, NotificationService

        config = NotificationConfig(enabled=True, notify_on_complete=False)
        service = NotificationService(config)

        result = service.notify_batch_complete(
            total=10,
            successful=10,
            failed=0,
            duration_seconds=60.0,
        )

        assert result is False

    @patch("plyer.notification")
    def test_notify_queue_empty(self, mock_notification):
        from app.services.notification_service import NotificationConfig, NotificationService

        config = NotificationConfig(enabled=True)
        service = NotificationService(config)

        result = service.notify_queue_empty()

        assert result is True

    def test_truncate_url_short(self):
        from app.services.notification_service import NotificationService

        url = "https://example.com"
        result = NotificationService._truncate_url(url, max_length=50)

        assert result == url

    def test_truncate_url_long(self):
        from app.services.notification_service import NotificationService

        url = "https://example.com/very/long/path/that/needs/truncation/and/more/text"
        result = NotificationService._truncate_url(url, max_length=30)

        assert len(result) <= 30
        assert result.endswith("...")

    @patch("plyer.notification")
    def test_update_config(self, mock_notification):
        from app.services.notification_service import NotificationConfig, NotificationService

        service = NotificationService()

        new_config = NotificationConfig(enabled=False)
        service.update_config(new_config)

        assert service.config.enabled is False
