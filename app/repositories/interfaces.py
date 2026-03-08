"""
Repository Interfaces Module

Defines abstract interfaces for all repositories.
Following Interface Segregation Principle (ISP) - clients depend only on abstractions.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Sequence
from dataclasses import dataclass
from datetime import datetime


@dataclass
class URLRecord:
    """Represents a URL in the queue."""
    url: str
    url_type: str
    status: str
    tags: List[str]
    error: Optional[str] = None
    added_at: Optional[str] = None


@dataclass
class NovelRecord:
    """Represents a novel in the queue."""
    url: str
    start_chapter: int
    end_chapter: int
    status: str
    error: Optional[str] = None


@dataclass
class RetryRecord:
    """Represents a failed URL/novel for retry."""
    url: str
    error: str
    chapter: Optional[int] = None
    tags: Optional[Sequence[str]] = None
    failed_at: Optional[str] = None


@dataclass
class ScrapeResult:
    """Represents a scraping result for stats."""
    url: str
    method: str
    success: bool
    time_ms: int
    word_count: int
    domain: str
    timestamp: Optional[str] = None


@dataclass
class ExtractionRecord:
    """Represents a successful extraction."""
    url: str
    file_path: str
    word_count: int
    method: str
    extracted_at: Optional[str] = None


class IStateRepository(ABC):
    """Abstract interface for state/settings management."""
    
    @abstractmethod
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        pass
    
    @abstractmethod
    def set_setting(self, key: str, value: Any) -> None:
        """Set a setting value."""
        pass
    
    @abstractmethod
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings."""
        pass
    
    @abstractmethod
    def reset_settings(self) -> None:
        """Reset all settings to defaults."""
        pass
    
    @abstractmethod
    def url_in_queue(self, url: str) -> bool:
        """Check if URL is already in queue."""
        pass
    
    @abstractmethod
    def novel_in_queue(self, url: str) -> bool:
        """Check if novel is already in queue."""
        pass
    
    @abstractmethod
    def add_url(self, url: str, url_type: str, tags: List[str]) -> bool:
        """Add URL to queue. Returns True if added, False if duplicate."""
        pass
    
    @abstractmethod
    def add_novel(self, url: str, start_chapter: int, end_chapter: int) -> bool:
        """Add novel to queue. Returns True if added, False if duplicate."""
        pass
    
    @abstractmethod
    def update_url_status(self, url: str, status: str, error: Optional[str] = None) -> None:
        """Update URL status in queue."""
        pass
    
    @abstractmethod
    def update_novel_status(self, url: str, status: str, error: Optional[str] = None) -> None:
        """Update novel status in queue."""
        pass
    
    @abstractmethod
    def remove_url(self, url: str) -> None:
        """Remove URL from queue."""
        pass
    
    @abstractmethod
    def remove_novel(self, url: str) -> None:
        """Remove novel from queue."""
        pass
    
    @abstractmethod
    def get_pending_urls(self) -> List[URLRecord]:
        """Get all pending URLs."""
        pass
    
    @abstractmethod
    def get_pending_novels(self) -> List[NovelRecord]:
        """Get all pending novels."""
        pass
    
    @abstractmethod
    def add_to_retry_normal(self, url: str, error: str, tags: List[str]) -> None:
        """Add URL to retry queue."""
        pass
    
    @abstractmethod
    def add_to_retry_novel(self, url: str, chapter: int, error: str) -> None:
        """Add novel chapter to retry queue."""
        pass
    
    @abstractmethod
    def get_retry_normal(self) -> List[RetryRecord]:
        """Get all URLs in retry queue."""
        pass
    
    @abstractmethod
    def get_retry_novel(self) -> List[RetryRecord]:
        """Get all novels in retry queue."""
        pass
    
    @abstractmethod
    def remove_from_retry_normal(self, url: str) -> None:
        """Remove URL from retry queue."""
        pass
    
    @abstractmethod
    def remove_from_retry_novel(self, url: str, chapter: int) -> None:
        """Remove novel chapter from retry queue."""
        pass
    
    @abstractmethod
    def clear_completed(self) -> None:
        """Clear all completed items from queue."""
        pass
    
    @abstractmethod
    def save_queue(self) -> None:
        """Persist queue to storage."""
        pass
    
    @property
    @abstractmethod
    def queue(self) -> Dict[str, Any]:
        """Get the raw queue dictionary (for backward compatibility)."""
        pass


class IStatsRepository(ABC):
    """Abstract interface for scraping statistics."""
    
    METHODS = ["simple_http", "playwright", "playwright_alt", "webscrapingapi"]
    
    @abstractmethod
    def record_scrape(self, result: ScrapeResult) -> None:
        """Record a scraping result."""
        pass
    
    @abstractmethod
    def get_method_stats(self, days: Optional[int] = None) -> Dict[str, Any]:
        """Get statistics by method for a time period."""
        pass
    
    @abstractmethod
    def get_daily_activity(self, days: int = 7) -> Dict[str, Any]:
        """Get daily activity for the last N days."""
        pass
    
    @abstractmethod
    def get_method_timeline(self, days: int = 30) -> Dict[str, Any]:
        """Get method usage broken down by day."""
        pass
    
    @abstractmethod
    def get_domain_stats(self, limit: int = 10) -> Dict[str, Any]:
        """Get domain-level statistics."""
        pass
    
    @abstractmethod
    def get_method_comparison(self, days: Optional[int] = None) -> Dict[str, Any]:
        """Get comparison data for radar chart."""
        pass
    
    @abstractmethod
    def get_summary_stats(self, days: Optional[int] = None) -> Dict[str, Any]:
        """Get summary statistics for overview."""
        pass
    
    @abstractmethod
    def get_recent(self, limit: int = 20) -> List[ScrapeResult]:
        """Get recent scraping results."""
        pass
    
    @abstractmethod
    def get_error_analysis(self, days: Optional[int] = None) -> Dict[str, Any]:
        """Analyze errors by method and domain."""
        pass
    
    @property
    @abstractmethod
    def stats(self) -> Dict[str, Any]:
        """Get the raw stats dictionary (for backward compatibility)."""
        pass


class IHistoryRepository(ABC):
    """Abstract interface for extraction history."""
    
    @abstractmethod
    def is_extracted(self, url: str) -> bool:
        """Check if URL has been extracted."""
        pass
    
    @abstractmethod
    def get_extracted_file(self, url: str) -> Optional[str]:
        """Get file path for extracted URL."""
        pass
    
    @abstractmethod
    def add_extraction(self, record: ExtractionRecord) -> None:
        """Record a successful extraction."""
        pass
    
    @abstractmethod
    def is_novel_extracted(self, novel_url: str) -> bool:
        """Check if novel has been extracted."""
        pass
    
    @abstractmethod
    def get_novel_chapters(self, novel_url: str) -> List[int]:
        """Get list of extracted chapters for a novel."""
        pass
    
    @abstractmethod
    def set_novel_metadata(self, novel_url: str, folder: str, name: str, 
                           genre: List[str], tags: List[str], author: str) -> None:
        """Set metadata for a novel."""
        pass
    
    @abstractmethod
    def add_novel_chapter(self, novel_url: str, chapter: int, word_count: int) -> None:
        """Record a novel chapter extraction."""
        pass
    
    @abstractmethod
    def get_novel_metadata(self, novel_url: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a novel."""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get overall extraction statistics."""
        pass
    
    @property
    @abstractmethod
    def history(self) -> Dict[str, Any]:
        """Get the raw history dictionary (for backward compatibility)."""
        pass
