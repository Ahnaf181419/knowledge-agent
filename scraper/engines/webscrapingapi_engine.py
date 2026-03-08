"""
WebScrapingAPI Engine

Third-party API scraper with connection pooling.
Inherits from BaseScraperEngine for consistent interface.
"""

from typing import Optional
from urllib.parse import quote
import requests

from app.config import WEBSCRAPING_API_KEY
from app.logger import logger
from app.api_tracker import can_use_api, increment_api_calls
from scraper.engines.base_engine import BaseScraperEngine


class WebScrapingAPIEngine(BaseScraperEngine):
    """WebScrapingAPI scraper with connection pooling."""
    
    BASE_URL = "https://api.webscrapingapi.com/v2"
    
    def __init__(self, api_key: str = ""):
        self._api_key = api_key or WEBSCRAPING_API_KEY
    
    @property
    def method_name(self) -> str:
        return "webscrapingapi"
    
    @property
    def timeout(self) -> int:
        return 30
    
    def scrape(self, url: str) -> Optional[str]:
        """
        Scrape URL using WebScrapingAPI.
        
        Args:
            url: Target URL
            
        Returns:
            HTML content as string, or None on failure
        """
        can_use, message = can_use_api()
        if not can_use:
            logger.error(f"WebScrapingAPI: {message}")
            return None
        
        if message != "OK":
            logger.warning(f"WebScrapingAPI: {message}")
        
        try:
            encoded_url = quote(url, safe='')
            
            params = {
                'api_key': self._api_key,
                'url': encoded_url,
                'render_js': 1
            }
            
            session = self.get_session()
            response = session.get(
                self.BASE_URL,
                params=params,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                increment_api_calls(1)
                logger.info(f"{self.method_name} successfully scraped: {url}")
                return response.text
            elif response.status_code == 401:
                logger.error(f"{self.method_name}: Invalid API key")
                return None
            elif response.status_code == 429:
                logger.warning(f"{self.method_name}: Rate limit exceeded for {url}")
                return None
            else:
                logger.warning(f"{self.method_name} failed: {url} - Status {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"{self.method_name} error for {url}: {e}")
            return None
    
    def scrape_with_extraction(self, url: str, extract_rules: dict) -> Optional[dict]:
        """
        Scrape with structured extraction rules.
        
        Args:
            url: Target URL
            extract_rules: Rules for structured extraction
            
        Returns:
            Extracted data as dict, or None on failure
        """
        import json
        
        can_use, message = can_use_api()
        if not can_use:
            logger.error(f"WebScrapingAPI: {message}")
            return None
        
        try:
            encoded_url = quote(url, safe='')
            
            params = {
                'api_key': self._api_key,
                'url': encoded_url,
                'render_js': 1,
                'extract_rules': json.dumps(extract_rules)
            }
            
            session = self.get_session()
            response = session.get(
                self.BASE_URL,
                params=params,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                increment_api_calls(1)
                logger.info(f"{self.method_name} extraction successful: {url}")
                return response.json()
            else:
                logger.warning(f"{self.method_name} extraction failed: {url}")
                return None
            
        except Exception as e:
            logger.error(f"{self.method_name} extraction error: {e}")
            return None


def scrape_with_webscrapingapi(url: str, api_key: str = "") -> Optional[str]:
    """Convenience wrapper for WebScrapingAPIEngine."""
    engine = WebScrapingAPIEngine(api_key)
    return engine.scrape(url)
