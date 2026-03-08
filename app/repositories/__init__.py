"""
Repositories Package

Provides data access layer through repository pattern.
All repositories implement interfaces for testability.
"""

from .interfaces import (
    IStateRepository,
    IStatsRepository,
    IHistoryRepository,
    URLRecord,
    NovelRecord,
    RetryRecord,
    ScrapeResult,
    ExtractionRecord
)
from .state_repo import StateRepository, StatsRepository, HistoryRepository

__all__ = [
    'IStateRepository',
    'IStatsRepository',
    'IHistoryRepository',
    'StateRepository',
    'StatsRepository',
    'HistoryRepository',
    'URLRecord',
    'NovelRecord',
    'RetryRecord',
    'ScrapeResult',
    'ExtractionRecord'
]
