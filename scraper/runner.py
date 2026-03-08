"""
Scraper Runner Module

Handles the execution of web scraping tasks.
4-Step Strategy for Normal Links:
  1. Simple HTTP + Trafilatura
  2. Playwright (headless, stealth) + XPath (3 retries)
  3. FAILED -> Add to Retry Table
  4. User chooses: Retry with WebScrapingAPI or Remove
"""

import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.sync_api import Browser, Page, Playwright

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from app.container import container
from app.logger import logger
from scraper.router import route_url
from scraper.engines.simple_http_engine import SimpleHTTPEngine
from scraper.engines.webscrapingapi_engine import WebScrapingAPIEngine
from scraper.extractors.text_extractor import TextExtractor
from storage.folder_manager import get_normal_folder
from storage.markdown_saver import save_normal_article
from utils.robots_checker import can_fetch, get_crawl_delay


class PlaywrightFallback:
    """Playwright fallback for normal links"""
    
    def __init__(self, max_retries: int = 2):
        self.browser: Browser | None = None
        self.page: Page | None = None
        self._playwright: Playwright | None = None
        self.max_retries: int = max_retries
    
    def start(self) -> None:
        from playwright.sync_api import sync_playwright
        self._playwright = sync_playwright().start()
        self.browser = self._playwright.chromium.launch(headless=True)
        self.page = self.browser.new_page()
    
    def close(self):
        if self.browser:
            self.browser.close()
        if self._playwright:
            self._playwright.stop()
    
    def scrape(self, url: str) -> tuple[str | None, str | None]:
        """Scrape using Playwright with XPath. Returns (text, method_name)."""
        if self.page is None:
            return None, None
        
        for attempt in range(self.max_retries):
            try:
                self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
                self.page.wait_for_timeout(2000)
                
                xpath_query = "//div[count(p) > 5]"
                container = self.page.locator(f"xpath={xpath_query}").first
                
                if container.count() > 0:
                    paragraphs = container.locator("p").all_text_contents()
                    if paragraphs:
                        text = "\n\n".join(p.strip() for p in paragraphs if p.strip())
                        if len(text) > 200:
                            logger.info(f"Playwright succeeded on attempt {attempt + 1}")
                            return text, "playwright"
                
                all_p = self.page.locator("p").all_text_contents()
                if all_p:
                    text = "\n\n".join(p.strip() for p in all_p if p.strip())
                    if len(text) > 200:
                        logger.info(f"Playwright succeeded on attempt {attempt + 1}")
                        return text, "playwright"
                    
            except Exception as e:
                logger.warning(f"Playwright attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2)
        
        logger.warning(f"Playwright failed after {self.max_retries} attempts")
        return None, None
    
    def scrape_alt(self, url: str) -> tuple[str | None, str | None]:
        """Scrape using Playwright with alternative config. Returns (text, method_name)."""
        alt_browser = None
        alt_playwright = None
        
        try:
            from playwright.sync_api import sync_playwright
            alt_playwright = sync_playwright().start()
            alt_browser = alt_playwright.chromium.launch(headless=True)
            
            alt_ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            alt_context = alt_browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=alt_ua
            )
            alt_page = alt_context.new_page()
            
            alt_page.goto(url, wait_until="domcontentloaded", timeout=30000)
            alt_page.wait_for_timeout(2000)
            
            xpath_query = "//div[count(p) > 5]"
            container = alt_page.locator(f"xpath={xpath_query}").first
            
            if container.count() > 0:
                paragraphs = container.locator("p").all_text_contents()
                if paragraphs:
                    text = "\n\n".join(p.strip() for p in paragraphs if p.strip())
                    if len(text) > 200:
                        logger.info(f"Playwright alt succeeded")
                        alt_context.close()
                        alt_browser.close()
                        alt_playwright.stop()
                        return text, "playwright_alt"
            
            all_p = alt_page.locator("p").all_text_contents()
            if all_p:
                text = "\n\n".join(p.strip() for p in all_p if p.strip())
                if len(text) > 200:
                    logger.info(f"Playwright alt succeeded")
                    alt_context.close()
                    alt_browser.close()
                    alt_playwright.stop()
                    return text, "playwright_alt"
            
            alt_context.close()
            alt_browser.close()
            alt_playwright.stop()
            
        except Exception as e:
            logger.warning(f"Playwright alt config failed: {e}")
            if alt_browser:
                try:
                    alt_browser.close()
                except:
                    pass
            if alt_playwright:
                try:
                    alt_playwright.stop()
                except:
                    pass
        
        return None, None


class ScraperRunner:
    """Main scraper execution class."""
    
    def __init__(self):
        self.settings = container.state_repo.get_all_settings()
        self.results = []
        self.progress = 0
        self.total = 0
        self.current_url = ""
        self._lock = threading.Lock()

    def scrape_normal_url(self, url: str, tags: list) -> dict:
        """Scrape normal URL with fallback priority"""
        start_time = time.time()
        fallback_chain = []
        retry_count = int(self.settings.get('retry_count', 2))
        
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
            route = route_url(url)
            self.current_url = url
            logger.info(f"Scraping {url} with route: {route}")
            
            if self.settings.get('respect_robots_txt', True):
                allowed, reason = can_fetch(url)
                if not allowed:
                    logger.info(f"Skipping {url}: {reason}")
                    result["status"] = "skipped"
                    result["error"] = reason
                    return result
                
                delay = get_crawl_delay(url)
                if delay > 0:
                    logger.info(f"Waiting {delay}s for crawl delay")
                    time.sleep(delay)

            html_content = None
            
            if route == "simple_http":
                fallback_chain.append("simple_http")
                result["fallback_chain"] = fallback_chain
                
                engine = SimpleHTTPEngine()
                html_content = engine.scrape(url)
                
                if html_content:
                    result["method"] = "simple_http"
                    logger.info(f"SimpleHTTP successfully fetched: {url}")
                
                if not html_content:
                    logger.info(f"Simple HTTP failed, trying Playwright...")
                    fallback_chain.append("playwright")
                    result["fallback_chain"] = fallback_chain
                    
                    try:
                        pw = PlaywrightFallback(max_retries=retry_count)
                        pw.start()
                        text_content, method = pw.scrape(url)
                        pw.close()
                        
                        if text_content:
                            html_content = text_content
                            result["method"] = method
                            logger.info(f"Playwright fallback succeeded for: {url}")
                    except Exception as e:
                        logger.warning(f"Playwright fallback failed: {e}")
                
                if not html_content:
                    logger.info(f"Playwright failed, trying Playwright alt config...")
                    fallback_chain.append("playwright_alt")
                    result["fallback_chain"] = fallback_chain
                    
                    try:
                        pw_alt = PlaywrightFallback(max_retries=retry_count)
                        text_content, method = pw_alt.scrape_alt(url)
                        
                        if text_content:
                            html_content = text_content
                            result["method"] = method
                            logger.info(f"Playwright alt config succeeded for: {url}")
                    except Exception as e:
                        logger.warning(f"Playwright alt config failed: {e}")
                
                if not html_content:
                    error_msg = "All methods failed (simple_http, playwright, playwright_alt)"
                    result["error"] = error_msg
                    result["status"] = "failed"
                    container.state_repo.add_to_retry_normal(url, error_msg, tags)
                    logger.error(f"{error_msg}: {url}")
                    return result

            elif route == "webscrapingapi":
                fallback_chain.append("webscrapingapi")
                result["fallback_chain"] = fallback_chain
                
                engine = WebScrapingAPIEngine()
                html_content = engine.scrape(url)
                
                if html_content:
                    result["method"] = "webscrapingapi"
                    logger.info(f"WebScrapingAPI successfully fetched: {url}")

            elif route == "skip":
                result["status"] = "skipped"
                result["error"] = "YouTube URL - skipped"
                return result
            
            elif route == "novel":
                result["status"] = "skipped"
                result["error"] = "Novel URL - use novel scraper"
                return result

            if html_content:
                export_format = self.settings.get('export_format', 'md')
                
                if result["method"] == "playwright":
                    text_content = html_content
                else:
                    text_content = TextExtractor.extract_from_html(html_content, export_format)
                
                if not text_content:
                    error_msg = "No content extracted"
                    result["error"] = error_msg
                    result["status"] = "failed"
                    container.state_repo.add_to_retry_normal(url, error_msg, tags)
                    return result

                folder = get_normal_folder(url)
                word_count = len(text_content.split())

                file_path = save_normal_article(
                    folder=folder,
                    url=url,
                    title=url.split('/')[-1][:50],
                    content=text_content,
                    tags=tags,
                    word_count=word_count,
                    output_format=export_format
                )

                elapsed_ms = int((time.time() - start_time) * 1000)
                
                result["status"] = "completed"
                result["file_path"] = str(file_path)
                result["word_count"] = word_count
                result["extraction_time_ms"] = elapsed_ms
                
                logger.info(f"Completed: {url} ({word_count} words) in {elapsed_ms}ms via {result['method']}")
                
                if result["method"]:
                    from app.repositories.interfaces import ExtractionRecord
                    container.history_repo.add_extraction(ExtractionRecord(
                        url=url,
                        file_path=str(file_path),
                        word_count=word_count,
                        method=result["method"]
                    ))
                    
                    try:
                        from app.repositories.interfaces import ScrapeResult
                        container.stats_repo.record_scrape(ScrapeResult(
                            url=url,
                            method=result["method"],
                            success=True,
                            time_ms=elapsed_ms,
                            word_count=word_count,
                            domain=""
                        ))
                    except Exception as e:
                        logger.warning(f"Failed to record stats: {e}")
            else:
                error_msg = "Failed to fetch HTML"
                result["error"] = error_msg
                result["status"] = "failed"
                container.state_repo.add_to_retry_normal(url, error_msg, tags)

        except Exception as e:
            error_msg = str(e)
            result["status"] = "failed"
            result["error"] = error_msg
            container.state_repo.add_to_retry_normal(url, error_msg, tags)
            logger.error(f"Error scraping {url}: {error_msg}")

        return result

    def run(self, urls: list) -> list:
        """Run scraping for multiple URLs with optional concurrency"""
        self.total = len(urls)
        self.progress = 0
        self.results = []
        
        concurrent_jobs = int(self.settings.get('concurrent_jobs', 1))
        
        if concurrent_jobs <= 1:
            for entry in urls:
                result = self.scrape_normal_url(entry['url'], entry.get('tags', []))
                self.results.append(result)
                self.progress += 1
                container.state_repo.save_queue()
        else:
            with ThreadPoolExecutor(max_workers=concurrent_jobs) as executor:
                future_to_entry = {
                    executor.submit(self.scrape_normal_url, entry['url'], entry.get('tags', [])): entry
                    for entry in urls
                }
                
                for future in as_completed(future_to_entry):
                    result = future.result()
                    with self._lock:
                        self.results.append(result)
                        self.progress += 1
                    container.state_repo.save_queue()
        
        return self.results


def run_scraper(urls: list) -> list:
    """Main entry point"""
    runner = ScraperRunner()
    return runner.run(urls)
