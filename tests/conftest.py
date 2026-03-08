"""
Pytest Configuration

Fixtures and configuration for tests.
"""

import pytest
from pathlib import Path
import tempfile
import json

from app.repositories import (
    StateRepository, StatsRepository, HistoryRepository,
    IStateRepository, IStatsRepository, IHistoryRepository
)
from app.services import ScrapingService, AnalyticsService, NovelService
from app.container import Container


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def state_repo(temp_dir) -> IStateRepository:
    """Create a state repository with temp storage."""
    return StateRepository(temp_dir)


@pytest.fixture
def stats_repo(temp_dir) -> IStatsRepository:
    """Create a stats repository with temp storage."""
    file_path = temp_dir / "scraping_stats.json"
    return StatsRepository(file_path)


@pytest.fixture
def history_repo(temp_dir) -> IHistoryRepository:
    """Create a history repository with temp storage."""
    file_path = temp_dir / "history.json"
    return HistoryRepository(file_path)


@pytest.fixture
def container(temp_dir) -> Container:
    """Create a container with temp storage."""
    Container.reset()
    container = Container(base_path=temp_dir)
    return container


@pytest.fixture
def sample_url():
    """Sample URL for testing."""
    return "https://example.com/article/123"


@pytest.fixture
def sample_settings():
    """Sample settings for testing."""
    return {
        "theme": "dark",
        "export_format": "md",
        "output_folder": "output",
        "concurrent_jobs": 3,
        "retry_count": 2,
        "novel_delay_min": 90,
        "novel_delay_max": 120,
        "auto_save_queue": True,
        "respect_robots_txt": True
    }
