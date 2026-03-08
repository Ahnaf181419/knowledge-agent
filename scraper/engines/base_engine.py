"""
Base Scraper Engine Module

Provides:
- Abstract base class for all scraper engines
- Connection pooling via requests.Session
- Consistent interface for stats tracking
"""

import requests
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from app.logger import logger


class BaseScraperEngine(ABC):
    """
    Abstract base class for all scraper engines.
    
    Features:
    - Connection pooling via shared Session
    - Consistent interface for all engines
    - Built-in retry support
    - Stats tracking hooks
    """
    
    _shared_session: Optional[requests.Session] = None
    DEFAULT_TIMEOUT = 30
    DEFAULT_RETRY = 2
    
    @classmethod
    def get_session(cls) -> requests.Session:
        """Get or create shared requests session for connection pooling."""
        if cls._shared_session is None:
            cls._shared_session = requests.Session()
            cls._shared_session.headers.update(cls._get_default_headers())
            logger.debug("Created new shared session for connection pooling")
        return cls._shared_session
    
    @classmethod
    def close_session(cls) -> None:
        """Close the shared session."""
        if cls._shared_session is not None:
            cls._shared_session.close()
            cls._shared_session = None
            logger.debug("Closed shared session")
    
    @classmethod
    def _get_default_headers(cls) -> Dict[str, str]:
        """Return default headers for requests."""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
    
    @property
    @abstractmethod
    def method_name(self) -> str:
        """Return the method identifier for stats tracking."""
        pass
    
    @property
    def timeout(self) -> int:
        """Request timeout in seconds."""
        return self.DEFAULT_TIMEOUT
    
    @property
    def max_retries(self) -> int:
        """Maximum retry attempts."""
        return self.DEFAULT_RETRY
    
    def scrape_with_retry(self, url: str) -> Optional[str]:
        """
        Scrape URL with automatic retry on failure.
        
        Args:
            url: The URL to scrape
            
        Returns:
            Content as string, or None on failure
        """
        for attempt in range(self.max_retries):
            result = self.scrape(url)
            if result is not None:
                return result
            if attempt < self.max_retries - 1:
                logger.warning(f"{self.method_name} attempt {attempt + 1} failed, retrying...")
        return None
    
    @abstractmethod
    def scrape(self, url: str) -> Optional[str]:
        """
        Scrape the given URL.
        
        Args:
            url: The URL to scrape
            
        Returns:
            Content as string, or None on failure
        """
        pass
    
    def validate_response(self, response: requests.Response, url: str) -> Optional[str]:
        """
        Validate HTTP response and return content if valid.
        
        Args:
            response: The HTTP response
            url: The original URL for logging
            
        Returns:
            Content as string, or None if invalid
        """
        if response.status_code == 200:
            logger.info(f"{self.method_name} successfully fetched: {url}")
            return response.text
        else:
            logger.warning(f"{self.method_name} failed: {url} - Status {response.status_code}")
            return None


class EngineFactory:
    """Factory for creating scraper engines based on URL routing."""
    
    def __init__(self, api_key: str = ""):
        self._api_key = api_key
        self._engines: Dict[str, BaseScraperEngine] = {}
    
    def get_engine(self, method: str) -> Optional[BaseScraperEngine]:
        """
        Get or create an engine for the given method.
        
        Args:
            method: The scraping method name
            
        Returns:
            Engine instance or None if unknown method
        """
        from scraper.engines.simple_http_engine import SimpleHTTPEngine
        from scraper.engines.webscrapingapi_engine import WebScrapingAPIEngine
        
        if method not in self._engines:
            if method == "simple_http":
                self._engines[method] = SimpleHTTPEngine()
            elif method == "webscrapingapi":
                if not self._api_key:
                    logger.error("WebScrapingAPI key not configured")
                    return None
                self._engines[method] = WebScrapingAPIEngine(api_key=self._api_key)
            else:
                return None
        
        return self._engines.get(method)
    
    def close_all(self) -> None:
        """Close all engine sessions."""
        for engine in self._engines.values():
            if hasattr(engine, 'close_session'):
                engine.close_session()
        self._engines.clear()
        BaseScraperEngine.close_session()
