"""
Scraping Service Module

Business logic for URL scraping operations.
Orchestrates engines, repositories, and extraction.
"""

import time
import threading
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from app.repositories.interfaces import (
    IStateRepository, IStatsRepository, IHistoryRepository,
    ScrapeResult, ExtractionRecord
)
from app.logger import logger
from scraper.engines.base_engine import EngineFactory


@dataclass
class ScrapingConfig:
    """Configuration for scraping operations."""
    respect_robots_txt: bool = True
    retry_count: int = 2
    concurrent_jobs: int = 1
    export_format: str = 'md'


class ScrapingService:
    """
    Service for scraping normal URLs.
    
    Uses dependency injection for repositories and follows
    the 4-step scraping strategy:
    1. Simple HTTP + Trafilatura
    2. Playwright + XPath
    3. Playwright Alt config
    4. Add to retry queue
    """
    
    def __init__(
        self,
        state_repo: IStateRepository,
        stats_repo: IStatsRepository,
        history_repo: IHistoryRepository,
        engine_factory: EngineFactory
    ):
        self._state = state_repo
        self._stats = stats_repo
        self._history = history_repo
        self._engines = engine_factory
        self._lock = threading.Lock()
    
    def get_config(self) -> ScrapingConfig:
        """Get current scraping configuration."""
        return ScrapingConfig(
            respect_robots_txt=self._state.get_setting('respect_robots_txt', True),
            retry_count=self._state.get_setting('retry_count', 2),
            concurrent_jobs=self._state.get_setting('concurrent_jobs', 1),
            export_format=self._state.get_setting('export_format', 'md')
        )
    
    def scrape_url(self, url: str, tags: List[str]) -> Dict[str, Any]:
        """
        Scrape a single URL with fallback strategy.
        
        Args:
            url: The URL to scrape
            tags: Tags to associate with the extraction
            
        Returns:
            Result dictionary with status, method, word_count, etc.
        """
        start_time = time.time()
        config = self.get_config()
        
        result = {
            "url": url,
            "status": "pending",
            "method": None,
            "fallback_chain": [],
            "extraction_time_ms": 0,
            "word_count": 0,
            "error": None
        }
        
        try:
            from scraper.router import route_url
            route = route_url(url)
            
            if route == "skip":
                result["status"] = "skipped"
                result["error"] = "YouTube URL - skipped"
                return result
            
            if route == "novel":
                result["status"] = "skipped"
                result["error"] = "Novel URL - use novel scraper"
                return result
            
            if config.respect_robots_txt:
                from utils.robots_checker import can_fetch, get_crawl_delay
                allowed, reason = can_fetch(url)
                if not allowed:
                    result["status"] = "skipped"
                    result["error"] = reason
                    return result
                
                delay = get_crawl_delay(url)
                if delay > 0:
                    logger.info(f"Waiting {delay}s for crawl delay")
                    time.sleep(delay)
            
            content = None
            
            if route == "simple_http":
                content, method = self._try_simple_http(url, config, result)
                
                if not content:
                    content, method = self._try_playwright(url, config, result)
                
                if not content:
                    content, method = self._try_playwright_alt(url, config, result)
                
                if not content:
                    error_msg = "All methods failed (simple_http, playwright, playwright_alt)"
                    result["error"] = error_msg
                    result["status"] = "failed"
                    self._state.add_to_retry_normal(url, error_msg, tags)
                    return result
            
            elif route == "webscrapingapi":
                content, method = self._try_webscrapingapi(url, config, result)
            
            if content:
                self._process_content(content, url, method, tags, config, result, start_time)
            else:
                error_msg = "Failed to fetch content"
                result["error"] = error_msg
                result["status"] = "failed"
                self._state.add_to_retry_normal(url, error_msg, tags)
        
        except Exception as e:
            error_msg = str(e)
            result["status"] = "failed"
            result["error"] = error_msg
            self._state.add_to_retry_normal(url, error_msg, tags)
            logger.error(f"Error scraping {url}: {error_msg}")
        
        return result
    
    def _try_simple_http(self, url: str, config: ScrapingConfig, result: Dict) -> tuple:
        """Try SimpleHTTP engine."""
        result["fallback_chain"].append("simple_http")
        
        engine = self._engines.get_engine("simple_http")
        if engine:
            content = engine.scrape(url)
            if content:
                result["method"] = "simple_http"
                return content, "simple_http"
        return None, None
    
    def _try_playwright(self, url: str, config: ScrapingConfig, result: Dict) -> tuple:
        """Try Playwright engine."""
        result["fallback_chain"].append("playwright")
        
        try:
            from scraper.runner import PlaywrightFallback
            pw = PlaywrightFallback(max_retries=config.retry_count)
            pw.start()
            content, method = pw.scrape(url)
            pw.close()
            
            if content:
                result["method"] = method
                return content, method
        except Exception as e:
            logger.warning(f"Playwright fallback failed: {e}")
        
        return None, None
    
    def _try_playwright_alt(self, url: str, config: ScrapingConfig, result: Dict) -> tuple:
        """Try Playwright alt config."""
        result["fallback_chain"].append("playwright_alt")
        
        try:
            from scraper.runner import PlaywrightFallback
            pw = PlaywrightFallback(max_retries=config.retry_count)
            content, method = pw.scrape_alt(url)
            
            if content:
                result["method"] = method
                return content, method
        except Exception as e:
            logger.warning(f"Playwright alt config failed: {e}")
        
        return None, None
    
    def _try_webscrapingapi(self, url: str, config: ScrapingConfig, result: Dict) -> tuple:
        """Try WebScrapingAPI engine."""
        result["fallback_chain"].append("webscrapingapi")
        
        engine = self._engines.get_engine("webscrapingapi")
        if engine:
            content = engine.scrape(url)
            if content:
                result["method"] = "webscrapingapi"
                return content, "webscrapingapi"
        
        return None, None
    
    def _process_content(self, content: str, url: str, method: str, tags: List[str],
                         config: ScrapingConfig, result: Dict, start_time: float) -> None:
        """Process and save extracted content."""
        from scraper.extractors.text_extractor import TextExtractor
        from storage.folder_manager import get_normal_folder
        from storage.markdown_saver import save_normal_article
        
        if method in ("playwright", "playwright_alt"):
            text_content = content
        else:
            text_content = TextExtractor.extract_from_html(content, config.export_format)
        
        if not text_content:
            error_msg = "No content extracted"
            result["error"] = error_msg
            result["status"] = "failed"
            self._state.add_to_retry_normal(url, error_msg, tags)
            return
        
        folder = get_normal_folder(url)
        word_count = len(text_content.split())
        
        file_path = save_normal_article(
            folder=folder,
            url=url,
            title=url.split('/')[-1][:50],
            content=text_content,
            tags=tags,
            word_count=word_count,
            output_format=config.export_format
        )
        
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        result["status"] = "completed"
        result["file_path"] = str(file_path)
        result["word_count"] = word_count
        result["extraction_time_ms"] = elapsed_ms
        
        logger.info(f"Completed: {url} ({word_count} words) in {elapsed_ms}ms via {method}")
        
        self._history.add_extraction(ExtractionRecord(
            url=url,
            file_path=str(file_path),
            word_count=word_count,
            method=method
        ))
        
        self._stats.record_scrape(ScrapeResult(
            url=url,
            method=method,
            success=True,
            time_ms=elapsed_ms,
            word_count=word_count,
            domain=""
        ))
    
    def scrape_batch(self, urls: List[Dict[str, Any]], progress_callback=None) -> List[Dict]:
        """
        Scrape multiple URLs with optional concurrency.
        
        Args:
            urls: List of dicts with 'url' and 'tags' keys
            progress_callback: Optional callback(current, total, result)
            
        Returns:
            List of result dictionaries
        """
        config = self.get_config()
        results = []
        total = len(urls)
        
        if config.concurrent_jobs <= 1:
            for i, entry in enumerate(urls):
                result = self.scrape_url(entry['url'], entry.get('tags', []))
                results.append(result)
                if progress_callback:
                    progress_callback(i + 1, total, result)
                self._state.save_queue()
        else:
            with ThreadPoolExecutor(max_workers=config.concurrent_jobs) as executor:
                future_to_entry = {
                    executor.submit(self.scrape_url, entry['url'], entry.get('tags', [])): entry
                    for entry in urls
                }
                
                for i, future in enumerate(as_completed(future_to_entry)):
                    result = future.result()
                    with self._lock:
                        results.append(result)
                    if progress_callback:
                        progress_callback(i + 1, total, result)
                    self._state.save_queue()
        
        return results
