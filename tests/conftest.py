"""Test fixtures for KnowledgeAgent tests."""

import json
import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)


@pytest.fixture
def mock_settings_file(temp_dir):
    """Create a mock settings.json file."""
    settings_file = temp_dir / "settings.json"
    settings = {
        "theme": "dark",
        "export_format": "md",
        "output_folder": "output",
        "concurrent_jobs": 2,
        "retry_count": 2,
    }
    settings_file.write_text(json.dumps(settings), encoding="utf-8")
    return settings_file


@pytest.fixture
def mock_queue_file(temp_dir):
    """Create a mock queue.json file."""
    queue_file = temp_dir / "queue.json"
    queue = {
        "urls": [],
        "novels": [],
        "retry_normal": [],
        "retry_novel": [],
    }
    queue_file.write_text(json.dumps(queue), encoding="utf-8")
    return queue_file


@pytest.fixture
def mock_history_file(temp_dir):
    """Create a mock history.json file."""
    history_file = temp_dir / "history.json"
    history = {
        "normal": {},
        "novels": {},
    }
    history_file.write_text(json.dumps(history), encoding="utf-8")
    return history_file


@pytest.fixture
def mock_stats_file(temp_dir):
    """Create a mock scraping_stats.json file."""
    stats_file = temp_dir / "scraping_stats.json"
    stats = {
        "metadata": {"version": "1.0.0"},
        "methods": {
            "simple_http": {"total_attempts": 0, "success": 0, "failed": 0},
            "playwright": {"total_attempts": 0, "success": 0, "failed": 0},
        },
        "daily": {},
        "domains": {},
        "recent": [],
        "errors": [],
    }
    stats_file.write_text(json.dumps(stats), encoding="utf-8")
    return stats_file


@pytest.fixture
def sample_urls():
    """Sample URLs for testing."""
    return {
        "valid": "https://example.com/article",
        "wiki": "https://en.wikipedia.org/wiki/Python_(programming_language)",
        "novel": "https://wtr-lab.com/novel/12281/chapter-177",
        "youtube": "https://youtube.com/watch?v=dQw4w9WgXcQ",
        "invalid": "not-a-url",
    }
