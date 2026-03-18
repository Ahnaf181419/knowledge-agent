"""
Simple HTTP Scraper - Fallback for simple sites without Playwright
Uses requests + trafilatura for basic web scraping
"""

import requests

from app.logger import logger
from scraper.engines.base import BaseEngine


class SimpleHTTPEngine(BaseEngine):
    """HTTP-based scraper using requests and trafilatura"""

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }

    @property
    def name(self) -> str:
        return "simple_http"

    @property
    def priority(self) -> int:
        return 1

    def scrape(self, url: str) -> str | None:
        """
        Fetch URL using requests and return HTML.

        Args:
            url: Target URL

        Returns:
            HTML content as string, or None on failure
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=30, allow_redirects=True)

            if response.status_code == 200:
                logger.info(f"SimpleHTTP successfully fetched: {url}")
                return response.text  # type: ignore[no-any-return]
            else:
                logger.warning(f"SimpleHTTP failed: {url} - Status {response.status_code}")
                return None

        except requests.exceptions.Timeout:
            logger.error(f"SimpleHTTP timeout for: {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"SimpleHTTP exception for {url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"SimpleHTTP error for {url}: {str(e)}")
            return None


def scrape_with_simple_http(url: str) -> str | None:
    """Simple wrapper function"""
    engine = SimpleHTTPEngine()
    return engine.scrape(url)
