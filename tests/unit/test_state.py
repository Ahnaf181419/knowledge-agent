"""Unit tests for state module."""

import os as _os
import sys

sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))


class TestState:
    """Tests for State class."""

    def test_default_settings(self):
        """Test default settings values."""
        from app.state import DEFAULT_SETTINGS

        assert DEFAULT_SETTINGS["theme"] == "dark"
        assert DEFAULT_SETTINGS["concurrent_jobs"] == 2
        assert DEFAULT_SETTINGS["retry_count"] == 2

    def test_default_queue_structure(self):
        """Test default queue structure."""
        from app.state import DEFAULT_QUEUE

        assert "urls" in DEFAULT_QUEUE
        assert "novels" in DEFAULT_QUEUE
        assert "retry_normal" in DEFAULT_QUEUE
        assert "retry_novel" in DEFAULT_QUEUE

    def test_queue_stats(self):
        """Test queue statistics calculation."""
        from app.state import State

        # Create a state with mock data
        mock_state = State.__new__(State)
        mock_state.settings = {"auto_save_queue": False}
        mock_state.queue = {
            "urls": [
                {"url": "https://example.com/1", "status": "pending"},
                {"url": "https://example.com/2", "status": "completed"},
                {"url": "https://example.com/3", "status": "failed"},
            ],
            "novels": [
                {"url": "https://novel.com/1", "status": "pending"},
            ],
            "retry_normal": [
                {"url": "https://example.com/3"},
                {"url": "https://example.com/4"},
            ],
            "retry_novel": [],
        }

        stats = mock_state.get_queue_stats()

        assert stats["total_urls"] == 3
        assert stats["pending"] == 1
        assert stats["completed"] == 1
        assert stats["failed"] == 1
        assert stats["total_novels"] == 1
        assert stats["retry_normal"] == 2
        assert stats["retry_novel"] == 0


class TestTimestamp:
    """Tests for timestamp generation."""

    def test_timestamp_format(self):
        """Test timestamp is ISO format."""
        from app.state import State

        ts = State._get_timestamp()

        # Should be ISO format (contains T and Z or +)
        assert "T" in ts
        assert "202" in ts  # Year should be present
