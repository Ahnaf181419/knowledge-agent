"""
Dependency Injection Container

Simple manual DI container with cached property-based lazy initialization.
Provides centralized access to all repositories and services.
"""

from pathlib import Path
from functools import cached_property
from typing import Optional

from app.repositories import (
    IStateRepository, IStatsRepository, IHistoryRepository,
    StateRepository, StatsRepository, HistoryRepository
)
from app.services import ScrapingService, AnalyticsService, NovelService
from scraper.engines.base_engine import EngineFactory


class Container:
    """
    Simple DI container with cached singletons.
    
    Usage:
        from app.container import container
        
        # Get services
        scraping_service = container.scraping_service
        analytics_service = container.analytics_service
        
        # Get repos directly (not recommended, use services)
        state = container.state_repo
    """
    
    _instance: Optional['Container'] = None
    
    def __init__(self, base_path: Path = None):
        self._base_path = base_path or Path(__file__).parent.parent
    
    @classmethod
    def get_instance(cls) -> 'Container':
        """Get the singleton container instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset(cls) -> None:
        """Reset the singleton (useful for testing)."""
        cls._instance = None
    
    @cached_property
    def state_repo(self) -> IStateRepository:
        """Get the state repository singleton."""
        return StateRepository(self._base_path)
    
    @cached_property
    def stats_repo(self) -> IStatsRepository:
        """Get the stats repository singleton."""
        file_path = self._base_path / "scraping_stats.json"
        return StatsRepository(file_path)
    
    @cached_property
    def history_repo(self) -> IHistoryRepository:
        """Get the history repository singleton."""
        file_path = self._base_path / "history.json"
        return HistoryRepository(file_path)
    
    @cached_property
    def engine_factory(self) -> EngineFactory:
        """Get the engine factory with API key from config."""
        from app.config import WEBSCRAPING_API_KEY
        return EngineFactory(api_key=WEBSCRAPING_API_KEY)
    
    @cached_property
    def scraping_service(self) -> ScrapingService:
        """Get the scraping service singleton."""
        return ScrapingService(
            state_repo=self.state_repo,
            stats_repo=self.stats_repo,
            history_repo=self.history_repo,
            engine_factory=self.engine_factory
        )
    
    @cached_property
    def analytics_service(self) -> AnalyticsService:
        """Get the analytics service singleton."""
        return AnalyticsService(stats_repo=self.stats_repo)
    
    @cached_property
    def novel_service(self) -> NovelService:
        """Get the novel service singleton."""
        return NovelService(
            state_repo=self.state_repo,
            stats_repo=self.stats_repo,
            history_repo=self.history_repo
        )
    
    def close_all(self) -> None:
        """Close all resources (sessions, connections, etc.)."""
        self.engine_factory.close_all()


# Global container instance
container = Container.get_instance()
