import json
import time
import random
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Callable, Any
from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout, Browser, BrowserContext, Page, Playwright

from app.container import container
from app.logger import logger
from app.api_tracker import can_use_api, increment_api_calls
from scraper.engines.webscrapingapi_engine import WebScrapingAPIEngine
from scraper.extractors.text_extractor import TextExtractor
from storage.folder_manager import get_novel_folder
from storage.markdown_saver import save_chapter, save_chapters_index


try:
    from playwright_stealth import stealth_sync
    HAS_STEALTH: bool = True
except ImportError:
    stealth_sync: Callable[[Any], None] = lambda page: None
    HAS_STEALTH: bool = False


class NovelScraper:
    """
    Novel scraper using Playwright with WebScrapingAPI fallback.
    """
    
    def __init__(self, delay_min: int = 90, delay_max: int = 120, retry_count: int = 2):
        self.delay_min: int = delay_min
        self.delay_max: int = delay_max
        self.retry_count: int = retry_count
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self._playwright: Playwright | None = None
        self.metadata: dict = {"genre": [], "tags": [], "author": "Unknown", "title": None}
    
    def __enter__(self):
        self.start_browser()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_browser()
        return False
    
    def start_browser(self) -> None:
        self._playwright = sync_playwright().start()
        self.browser = self._playwright.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        self.context = self.browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        self.page = self.context.new_page()
        
        if HAS_STEALTH:
            stealth_sync(self.page)
        
        self._load_session()
    
    def close_browser(self) -> None:
        if self.context:
            self._save_session()
            self.context.close()
        if self.browser:
            self.browser.close()
        if self._playwright:
            self._playwright.stop()
    
    def _get_session_file(self, novel_slug: str) -> Path:
        sessions_dir = Path(__file__).parent.parent / "sessions"
        sessions_dir.mkdir(exist_ok=True)
        return sessions_dir / f"{novel_slug}_cookies.json"
    
    def _load_session(self) -> None:
        if self.context is None:
            return
        
        novel_slug = getattr(self, 'novel_slug', 'default')
        session_file = self._get_session_file(novel_slug)
        
        if session_file.exists():
            try:
                data = json.loads(session_file.read_text(encoding='utf-8'))
                expires = data.get("expires_at", "")
                if expires and datetime.now() < datetime.fromisoformat(expires):
                    self.context.add_cookies(data.get("cookies", []))
                    logger.info("Loaded session cookies")
            except Exception as e:
                logger.warning(f"Could not load session: {e}")
    
    def _save_session(self) -> None:
        if self.context is None:
            return
        
        novel_slug = getattr(self, 'novel_slug', 'default')
        session_file = self._get_session_file(novel_slug)
        
        cookies = self.context.cookies()
        data = {
            "saved_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=7)).isoformat(),
            "cookies": cookies
        }
        session_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
        logger.info("Session cookies saved")
    
    def extract_chapter_text(self, page) -> tuple[str | None, str | None]:
        try:
            xpath_query = "//div[count(p) > 5]"
            container = page.locator(f"xpath={xpath_query}").first
            
            paragraphs = container.locator("p").all_text_contents()
            if paragraphs:
                text = "\n\n".join(p.strip() for p in paragraphs if p.strip())
                if len(text) > 200:
                    title = None
                    try:
                        title_loc = container.locator("xpath=./h1 | ./h2 | .//h1 | .//h2").first
                        if title_loc.count() > 0:
                            title = title_loc.text_content(timeout=500).strip()
                    except:
                        pass
                    return text, title
        except Exception as e:
            logger.error(f"Extraction error: {e}")
        return None, None
    
    def extract_novel_metadata(self, novel_url: str) -> dict:
        result = {
            "genre": [],
            "tags": [],
            "author": "Unknown",
            "title": None
        }
        
        if self.page is None:
            return result
        
        try:
            self.page.goto(novel_url, wait_until="domcontentloaded", timeout=60000)
            self.page.wait_for_timeout(2000)
            
            try:
                genre_loc = self.page.locator("xpath=//div[contains(@class, 'genre') or contains(@class, 'genres')]")
                if genre_loc.count() > 0:
                    genre_text = genre_loc.first.text_content()
                    genres = [g.strip() for g in genre_text.split(',') if g.strip()]
                    result["genre"] = genres
                    
                    logger.info(f"Found genre(s): {genres}")
            except:
                logger.warning("Could not extract genre")
            
            try:
                tags_loc = self.page.locator("xpath=//div[contains(@class, 'tags') or contains(@class, 'tag')]")
                if tags_loc.count() > 0:
                    tags_text = tags_loc.first.text_content()
                    tags = [t.strip() for t in tags_text.split(',') if t.strip()]
                    result["tags"] = tags
                    logger.info(f"Found tag(s): {tags}")
            except:
                logger.warning("Could not extract tags")
            
            try:
                author_loc = self.page.locator("xpath=//div[contains(@class, 'author') or contains(@class, 'authors')]")
                if author_loc.count() > 0:
                    author = author_loc.first.text_content().strip()
                    result["author"] = author
                    logger.info(f"Found author: {author}")
            except:
                logger.warning("Could not extract author")
            
            if not result["genre"] and not result["tags"]:
                logger.warning("No genre/tags found. User may need to fill manually.")
            
        except Exception as e:
            logger.warning(f"Could not extract metadata: {e}")
        
        return result
    
    def detect_captcha(self) -> bool:
        if self.page is None:
            return False
        
        captcha_indicators = [
            "just a moment", "captcha", "verify you are human",
            "cloudflare", "checking your browser", "access denied"
        ]
        try:
            title = self.page.title().lower()
            content = self.page.content()[:3000].lower()
            return any(ind in title or ind in content for ind in captcha_indicators)
        except:
            return False
    
    def scrape_chapter_with_playwright(self, url: str) -> tuple[str | None, str | None, str | None]:
        try:
            if self.page:
                self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
                self.page.wait_for_timeout(random.randint(1000, 2000))
                
                if self.detect_captcha():
                    logger.warning(f"CAPTCHA detected for {url} - skipping silently")
                    return None, None, "captcha"
                
                text, title = self.extract_chapter_text(self.page)
                if text and len(text) > 100:
                    return self.clean_text(text), title, "playwright"
        except Exception as e:
            logger.warning(f"Playwright failed: {e}")
        
        return None, None, None
    
    def scrape_chapter_with_api(self, url: str) -> tuple[str | None, str | None, str | None]:
        can_use, message = can_use_api()
        if not can_use:
            logger.error(f"Cannot use API: {message}")
            return None, None, None
        
        logger.info(f"Trying WebScrapingAPI for: {url}")
        
        engine = WebScrapingAPIEngine()
        html_content = engine.scrape(url)
        
        if html_content:
            text = TextExtractor.extract_from_html(html_content, 'markdown')
            if text and len(text) > 100:
                return text, None, "webscrapingapi"
        
        return None, None, None
    
    def scrape_chapter_with_playwright_alt(self, url: str) -> tuple[str | None, str | None, str | None]:
        alt_browser = None
        alt_playwright = None
        try:
            alt_playwright = sync_playwright().start()
            alt_browser = alt_playwright.chromium.launch(headless=True)
            
            alt_ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            alt_context = alt_browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=alt_ua
            )
            alt_page = alt_context.new_page()
            
            alt_page.goto(url, wait_until="domcontentloaded", timeout=60000)
            alt_page.wait_for_timeout(random.randint(2000, 3000))
            
            if self.detect_captcha():
                logger.warning(f"CAPTCHA detected for {url} - alt config")
                alt_context.close()
                alt_browser.close()
                alt_playwright.stop()
                return None, None, "captcha"
            
            text, title = self.extract_chapter_text(alt_page)
            if text and len(text) > 100:
                alt_context.close()
                alt_browser.close()
                alt_playwright.stop()
                return self.clean_text(text), title, "playwright_alt"
            
            alt_context.close()
            alt_browser.close()
            alt_playwright.stop()
            
        except Exception as e:
            logger.warning(f"Playwright alt config failed: {e}")
            if alt_browser:
                alt_browser.close()
            if alt_playwright:
                alt_playwright.stop()
        
        return None, None, None
    
    def scrape_chapter(self, url: str, chapter_num: int) -> dict:
        """Scrape a single chapter with 4-step fallback"""
        start_time = time.time()
        result = {
            "chapter": chapter_num,
            "status": "failed",
            "word_count": 0,
            "error": None,
            "method": None,
            "extraction_time_ms": 0
        }
        
        for attempt in range(self.retry_count):
            text, title, method = self.scrape_chapter_with_playwright(url)
            
            if text:
                elapsed_ms = int((time.time() - start_time) * 1000)
                result["status"] = "success"
                result["method"] = method
                result["title"] = title
                result["word_count"] = len(text.split())
                result["text"] = text
                result["extraction_time_ms"] = elapsed_ms
                self._record_stats(url, method, True, elapsed_ms, result["word_count"])
                return result
            
            time.sleep(5)
        
        logger.info(f"Playwright stealth failed, trying alt config...")
        for attempt in range(self.retry_count):
            text, title, method = self.scrape_chapter_with_playwright_alt(url)
            
            if text:
                elapsed_ms = int((time.time() - start_time) * 1000)
                result["status"] = "success"
                result["method"] = method
                result["title"] = title
                result["word_count"] = len(text.split())
                result["text"] = text
                result["extraction_time_ms"] = elapsed_ms
                self._record_stats(url, method, True, elapsed_ms, result["word_count"])
                return result
            
            time.sleep(5)
        
        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.info(f"Both Playwright methods failed, adding to retry table...")
        result["error"] = "Both Playwright methods failed - added to retry table"
        result["extraction_time_ms"] = elapsed_ms
        self._record_stats(url, "playwright", False, elapsed_ms, 0)
        return result
    
    def _record_stats(self, url: str, method: str | None, success: bool, time_ms: int, word_count: int):
        """Record scraping stats to scraping_stats.json"""
        if not method:
            return
        try:
            from app.repositories.interfaces import ScrapeResult
            container.stats_repo.record_scrape(ScrapeResult(
                url=url,
                method=method,
                success=success,
                time_ms=time_ms,
                word_count=word_count,
                domain=""
            ))
        except Exception as e:
            logger.warning(f"Failed to record stats: {e}")
    
    def scrape_novel(
        self, 
        novel_url: str, 
        novel_name: str,
        start_chapter: int, 
        end_chapter: int,
        force: bool = False,
        progress_callback=None
    ) -> dict:
        """
        Scrape novel chapters with delay between each.

        Args:
            novel_url: Base URL for novel
            novel_name: Name for folder
            start_chapter: Starting chapter number
            end_chapter: Ending chapter number
            force: Overwrite existing chapters
            progress_callback: Function to call with progress
            
        Returns:
            Dictionary with results
        """
        self.novel_slug = novel_name.lower().replace(" ", "-")
        
        novel_folder = get_novel_folder(novel_url)
        
        self.start_browser()
        
        logger.info(f"Extracting metadata from {novel_url}...")
        self.metadata = self.extract_novel_metadata(novel_url)
        
        container.history_repo.set_novel_metadata(
            novel_url=novel_url,
            folder=str(novel_folder),
            name=novel_name,
            genre=self.metadata["genre"],
            tags=self.metadata["tags"],
            author=self.metadata["author"]
        )
        
        results = []
        
        try:
            for chapter_num in range(start_chapter, end_chapter + 1):
                chapter_file = novel_folder / f"chapter_{chapter_num}.md"
                
                if chapter_file.exists() and not force:
                    logger.info(f"Skipping chapter {chapter_num} (exists)")
                    results.append({
                        "chapter": chapter_num,
                        "status": "skipped",
                        "word_count": 0
                    })
                    if progress_callback:
                        progress_callback(chapter_num, end_chapter)
                    continue
                
                chapter_url = f"{novel_url}/chapter-{chapter_num}?service=web"
                
                logger.info(f"Scraping chapter {chapter_num}...")
                
                result = self.scrape_chapter(chapter_url, chapter_num)
                
                if result["status"] == "success":
                    save_chapter(
                        folder=novel_folder,
                        chapter_number=chapter_num,
                        title=result.get("title", f"Chapter {chapter_num}"),
                        text=result.get("text", ""),
                        word_count=result["word_count"],
                        source_url=chapter_url,
                        novel_name=novel_name,
                        genre=self.metadata["genre"],
                        tags=self.metadata["tags"]
                    )
                    logger.info(f"Chapter {chapter_num} saved ({result['word_count']} words)")
                    
                    container.history_repo.add_novel_chapter(novel_url, chapter_num, result["word_count"])
                else:
                    logger.error(f"Chapter {chapter_num} failed: {result.get('error')}")
                
                results.append(result)
                
                if progress_callback:
                    progress_callback(chapter_num, end_chapter)
                
                if chapter_num < end_chapter:
                    self.wait_delay()
        
        finally:
            self.close_browser()
        
        success_count = sum(1 for r in results if r["status"] == "success")
        if success_count > 0:
            chapters_data = [
                {"number": r["chapter"], "word_count": r["word_count"], "status": r["status"]}
                for r in results
                if r["status"] in ("success", "failed")
            ]
            save_chapters_index(
                folder=novel_folder,
                novel_name=novel_name,
                genre=self.metadata["genre"],
                tags=self.metadata["tags"],
                author=self.metadata["author"],
                chapters=chapters_data
            )
        
        return {
            "success": success_count,
            "failed": len(results) - success_count,
            "skipped": sum(1 for r in results if r["status"] == "skipped"),
            "total": end_chapter - start_chapter + 1,
            "results": results
        }
    
    def wait_delay(self):
        delay = random.randint(self.delay_min, self.delay_max)
        logger.info(f"Waiting {delay} seconds before next chapter...")
        time.sleep(delay)
    
    def clean_text(self, text: str) -> str:
        text = re.sub(r'\n\s+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
