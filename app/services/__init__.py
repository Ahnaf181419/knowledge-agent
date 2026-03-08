"""
Services Package

Business logic layer that orchestrates repositories and external services.
Follows Service Layer Pattern - thin controllers, fat services.
"""

from .scraping_service import ScrapingService, ScrapingConfig
from .analytics_service import AnalyticsService
from .novel_service import NovelService

__all__ = [
    'ScrapingService',
    'ScrapingConfig',
    'AnalyticsService',
    'NovelService'
]
