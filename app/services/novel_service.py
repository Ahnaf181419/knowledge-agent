"""
Novel Service Module

Business logic for novel scraping operations.
Handles multi-chapter extraction with delay and retry logic.
"""

import time
import random
import re
from typing import Dict, Any, Optional, Callable, List
from pathlib import Path

from app.repositories.interfaces import (
    IStateRepository, IStatsRepository, IHistoryRepository,
    ScrapeResult
)
from app.logger import logger


class NovelService:
    """
    Service for scraping novels.
    
    Features:
    - Chapter-by-chapter extraction
    - Configurable delays between chapters
    - Playwright stealth + alt fallback
    - Session management
    """
    
    def __init__(
        self,
        state_repo: IStateRepository,
        stats_repo: IStatsRepository,
        history_repo: IHistoryRepository
    ):
        self._state = state_repo
        self._stats = stats_repo
        self._history = history_repo
    
    def get_config(self) -> Dict[str, Any]:
        """Get novel scraping configuration."""
        return {
            "delay_min": self._state.get_setting('novel_delay_min', 90),
            "delay_max": self._state.get_setting('novel_delay_max', 120),
            "retry_count": self._state.get_setting('retry_count', 2)
        }
    
    def scrape_novel(
        self,
        novel_url: str,
        novel_name: str,
        start_chapter: int,
        end_chapter: int,
        force: bool = False,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Scrape a novel's chapters.
        
        Args:
            novel_url: Base URL for the novel
            novel_name: Display name for the novel
            start_chapter: First chapter to scrape
            end_chapter: Last chapter to scrape
            force: Overwrite existing chapters
            progress_callback: Optional callback(current, total)
            
        Returns:
            Dictionary with success/failed/skipped counts
        """
        config = self.get_config()
        
        from scraper.novel_scraper import NovelScraper
        
        scraper = NovelScraper(
            delay_min=config["delay_min"],
            delay_max=config["delay_max"],
            retry_count=config["retry_count"]
        )
        
        results = []
        
        with scraper:
            logger.info(f"Extracting metadata from {novel_url}...")
            metadata = scraper.extract_novel_metadata(novel_url)
            
            self._history.set_novel_metadata(
                novel_url=novel_url,
                folder=str(self._get_novel_folder(novel_url)),
                name=novel_name,
                genre=metadata.get("genre", []),
                tags=metadata.get("tags", []),
                author=metadata.get("author", "Unknown")
            )
            
            for chapter_num in range(start_chapter, end_chapter + 1):
                result = self._scrape_chapter(
                    scraper=scraper,
                    novel_url=novel_url,
                    novel_name=novel_name,
                    chapter_num=chapter_num,
                    force=force,
                    metadata=metadata
                )
                results.append(result)
                
                if progress_callback:
                    progress_callback(chapter_num, end_chapter)
                
                if chapter_num < end_chapter:
                    self._wait_delay(config["delay_min"], config["delay_max"])
        
        success_count = sum(1 for r in results if r["status"] == "success")
        failed_count = sum(1 for r in results if r["status"] == "failed")
        skipped_count = sum(1 for r in results if r["status"] == "skipped")
        
        if success_count > 0:
            self._save_chapters_index(novel_url, novel_name, metadata, results)
        
        return {
            "success": success_count,
            "failed": failed_count,
            "skipped": skipped_count,
            "total": end_chapter - start_chapter + 1,
            "results": results
        }
    
    def _scrape_chapter(
        self,
        scraper,
        novel_url: str,
        novel_name: str,
        chapter_num: int,
        force: bool,
        metadata: Dict
    ) -> Dict[str, Any]:
        """Scrape a single chapter."""
        from storage.folder_manager import get_novel_folder
        from storage.markdown_saver import save_chapter
        
        novel_folder = get_novel_folder(novel_url)
        chapter_file = novel_folder / f"chapter_{chapter_num}.md"
        
        if chapter_file.exists() and not force:
            logger.info(f"Skipping chapter {chapter_num} (exists)")
            return {"chapter": chapter_num, "status": "skipped", "word_count": 0}
        
        chapter_url = f"{novel_url}/chapter-{chapter_num}?service=web"
        start_time = time.time()
        
        result = scraper.scrape_chapter(chapter_url, chapter_num)
        
        if result["status"] == "success":
            save_chapter(
                folder=novel_folder,
                chapter_number=chapter_num,
                title=result.get("title", f"Chapter {chapter_num}"),
                text=result.get("text", ""),
                word_count=result["word_count"],
                source_url=chapter_url,
                novel_name=novel_name,
                genre=metadata.get("genre", []),
                tags=metadata.get("tags", [])
            )
            
            logger.info(f"Chapter {chapter_num} saved ({result['word_count']} words)")
            
            self._history.add_novel_chapter(novel_url, chapter_num, result["word_count"])
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            self._stats.record_scrape(ScrapeResult(
                url=chapter_url,
                method=result.get("method", "playwright"),
                success=True,
                time_ms=elapsed_ms,
                word_count=result["word_count"],
                domain=novel_url.split('/')[2] if '/' in novel_url else ""
            ))
        else:
            logger.error(f"Chapter {chapter_num} failed: {result.get('error')}")
            self._state.add_to_retry_novel(novel_url, chapter_num, result.get("error", "Unknown error"))
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            self._stats.record_scrape(ScrapeResult(
                url=chapter_url,
                method="playwright",
                success=False,
                time_ms=elapsed_ms,
                word_count=0,
                domain=novel_url.split('/')[2] if '/' in novel_url else ""
            ))
        
        return result
    
    def _get_novel_folder(self, novel_url: str) -> Path:
        """Get the folder for a novel."""
        from storage.folder_manager import get_novel_folder
        return get_novel_folder(novel_url)
    
    def _wait_delay(self, delay_min: int, delay_max: int) -> None:
        """Wait for a random delay."""
        delay = random.randint(delay_min, delay_max)
        logger.info(f"Waiting {delay} seconds before next chapter...")
        time.sleep(delay)
    
    def _save_chapters_index(
        self,
        novel_url: str,
        novel_name: str,
        metadata: Dict,
        results: List[Dict]
    ) -> None:
        """Save the chapters index file."""
        from storage.folder_manager import get_novel_folder
        from storage.markdown_saver import save_chapters_index
        
        novel_folder = get_novel_folder(novel_url)
        
        chapters_data = [
            {"number": r["chapter"], "word_count": r["word_count"], "status": r["status"]}
            for r in results
            if r["status"] in ("success", "failed")
        ]
        
        save_chapters_index(
            folder=novel_folder,
            novel_name=novel_name,
            genre=metadata.get("genre", []),
            tags=metadata.get("tags", []),
            author=metadata.get("author", "Unknown"),
            chapters=chapters_data
        )
