"""Unit tests for session_manager module."""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestSessionManager:
    """Tests for SessionManager class."""

    def test_init_creates_directory(self):
        """Test SessionManager creates sessions directory."""
        from scraper.core.session_manager import SessionManager

        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            manager = SessionManager(sessions_dir=sessions_dir)

            assert sessions_dir.exists()
            assert manager.sessions_dir == sessions_dir

    def test_get_session_file(self):
        """Test session file path generation."""
        from scraper.core.session_manager import SessionManager

        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            manager = SessionManager(sessions_dir=sessions_dir)

            session_file = manager._get_session_file("my-test-slug")

            assert session_file.name == "my-test-slug_cookies.json"
            assert session_file.parent == sessions_dir

    @patch("scraper.core.session_manager.logger")
    def test_load_session_not_found(self, mock_logger):
        """Test loading session that doesn't exist."""
        from scraper.core.session_manager import SessionManager

        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            manager = SessionManager(sessions_dir=sessions_dir)

            mock_context = MagicMock()
            result = manager.load_session(mock_context, "nonexistent")

            assert result is False

    @patch("scraper.core.session_manager.logger")
    def test_load_session_expired(self, mock_logger):
        """Test loading expired session."""
        from scraper.core.session_manager import SessionManager

        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            manager = SessionManager(sessions_dir=sessions_dir)

            session_file = manager._get_session_file("expired-slug")
            expired_date = (datetime.now() - timedelta(days=1)).isoformat()
            data = {
                "saved_at": expired_date,
                "expires_at": expired_date,
                "cookies": [{"name": "test", "value": "test"}]
            }
            session_file.write_text(json.dumps(data))

            mock_context = MagicMock()
            result = manager.load_session(mock_context, "expired-slug")

            assert result is False

    @patch("scraper.core.session_manager.logger")
    def test_load_session_valid(self, mock_logger):
        """Test loading valid session."""
        from scraper.core.session_manager import SessionManager

        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            manager = SessionManager(sessions_dir=sessions_dir)

            session_file = manager._get_session_file("valid-slug")
            future_date = (datetime.now() + timedelta(days=7)).isoformat()
            data = {
                "saved_at": datetime.now().isoformat(),
                "expires_at": future_date,
                "cookies": [{"name": "session", "value": "abc123"}]
            }
            session_file.write_text(json.dumps(data))

            mock_context = MagicMock()
            result = manager.load_session(mock_context, "valid-slug")

            assert result is True
            mock_context.add_cookies.assert_called_once_with(data["cookies"])

    @patch("scraper.core.session_manager.logger")
    def test_load_session_corrupted(self, mock_logger):
        """Test loading corrupted session file."""
        from scraper.core.session_manager import SessionManager

        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            manager = SessionManager(sessions_dir=sessions_dir)

            session_file = manager._get_session_file("corrupted-slug")
            session_file.write_text("not valid json{")

            mock_context = MagicMock()
            result = manager.load_session(mock_context, "corrupted-slug")

            assert result is False

    @patch("scraper.core.session_manager.logger")
    def test_save_session(self, mock_logger):
        """Test save_session gets cookies from context."""
        from scraper.core.session_manager import SessionManager

        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            manager = SessionManager(sessions_dir=sessions_dir)

            mock_context = MagicMock()
            mock_context.cookies.return_value = [{"name": "test", "value": "test"}]

            manager.save_session(mock_context, "test-save")

            mock_context.cookies.assert_called_once()

    @patch("scraper.core.session_manager.logger")
    def test_save_session_error(self, mock_logger):
        """Test save session handles error."""
        from scraper.core.session_manager import SessionManager

        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            manager = SessionManager(sessions_dir=sessions_dir)

            mock_context = MagicMock()
            mock_context.cookies.side_effect = Exception("Browser error")

            manager.save_session(mock_context, "error-slug")

            session_file = manager._get_session_file("error-slug")
            assert not session_file.exists()

    @patch("scraper.core.session_manager.logger")
    def test_delete_session_exists(self, mock_logger):
        """Test deleting existing session."""
        from scraper.core.session_manager import SessionManager

        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            manager = SessionManager(sessions_dir=sessions_dir)

            session_file = manager._get_session_file("to-delete")
            session_file.write_text("{}")

            result = manager.delete_session("to-delete")

            assert result is True
            assert not session_file.exists()

    @patch("scraper.core.session_manager.logger")
    def test_delete_session_not_exists(self, mock_logger):
        """Test deleting non-existent session."""
        from scraper.core.session_manager import SessionManager

        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            manager = SessionManager(sessions_dir=sessions_dir)

            result = manager.delete_session("nonexistent")

            assert result is False


class TestSessionManagerWaitDelay:
    """Tests for wait_delay method."""

    @patch("scraper.core.session_manager.logger")
    @patch("scraper.core.session_manager.random")
    def test_wait_delay(self, mock_random, mock_logger):
        """Test wait delay sleeps for random time."""
        from scraper.core.session_manager import SessionManager
        import time

        with patch.object(time, 'sleep') as mock_sleep:
            mock_random.randint.return_value = 5

            SessionManager.wait_delay(1, 10)

            mock_random.randint.assert_called_once_with(1, 10)
            mock_sleep.assert_called_once_with(5)
