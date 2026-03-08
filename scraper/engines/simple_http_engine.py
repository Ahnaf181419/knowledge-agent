"""
Simple HTTP Scraper Engine

Fast HTTP-based scraper using requests library.
Inherits from BaseScraperEngine for connection pooling.
"""

from typing import Optional
from app.logger import logger
from scraper.engines.base_engine import BaseScraperEngine


class SimpleHTTPEngine(BaseScraperEngine):
    """HTTP-based scraper using requests library with connection pooling."""
    
    @property
    def method_name(self) -> str:
        return "simple_http"
    
    def scrape(self, url: str) -> Optional[str]:
        """
        Fetch URL using HTTP GET request.
        
        Args:
            url: Target URL
            
        Returns:
            HTML content as string, or None on failure
        """
        session = self.get_session()
        
        try:
            response = session.get(
                url,
                timeout=self.timeout,
                allow_redirects=True
            )
            
            return self.validate_response(response, url)
            
        except Exception as e:
            logger.error(f"{self.method_name} error for {url}: {e}")
            return None


def scrape_with_simple_http(url: str) -> Optional[str]:
    """Convenience wrapper for SimpleHTTPEngine."""
    engine = SimpleHTTPEngine()
    return engine.scrape(url)
