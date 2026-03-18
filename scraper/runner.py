"""
Scraper Runner Module

Handles the execution of web scraping tasks.
Uses unified 5-engine fallback chain with automatic failover:
  1. SimpleHTTPEngine (requests + trafilatura)
  2. PlaywrightEngine (basic headless)
  3. PlaywrightAltEngine (Mac user-agent)
  4. PlaywrightTLSEngine (anti-detection)
  5. CloudScraperEngine (Cloudflare bypass)
"""

import re
import sys
import time
from typing import Any

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from app.logger import logger
from app.services.background_job_service import background_job_service
from app.services.lint_service import LintService
from app.services.scraper_service import scraper_service
from app.state import state
from scraper.core.engine_registry import EngineRegistry
from scraper.core.fallback_chain import FallbackChain, FallbackResult
from scraper.extractors.text_extractor import TextExtractor
from scraper.router import route_url
from storage.folder_manager import get_normal_folder, get_novel_folder, get_novel_index_path
from storage.markdown_saver import save_normal_article
from utils.robots_checker import can_fetch, get_crawl_delay
from utils.validators import is_novel_url


class ScraperRunner:
    """Main scraper using unified 5-engine fallback chain."""

    def __init__(self) -> None:
        self.registry = EngineRegistry()
        self.fallback = FallbackChain(self.registry)
        self.settings = state.settings

    def scrape_normal_url(self, url: str, tags: list, chapter_range: tuple[int, int] | None = None) -> dict:
        """
        Scrape URL with automatic 5-engine fallback chain.

        Args:
            url: URL to scrape (base URL for chapter ranges)
            tags: Tags for categorization
            chapter_range: Tuple of (start_chapter, end_chapter) for novel scraping

        Returns:
            Dictionary with scrape result(s)
        """
        # Handle chapter range for novels
        if chapter_range and is_novel_url(url):
            return self._scrape_chapter_range(url, tags, chapter_range)
        
        return self._scrape_single_url(url, tags)

    def _scrape_chapter_range(self, base_url: str, tags: list, chapter_range: tuple[int, int]) -> dict:
        """Scrape multiple chapters from a novel."""
        start_ch, end_ch = chapter_range
        results = []
        chapter_list = []
        
        logger.info(f"[NOVEL] Scraping chapters {start_ch}-{end_ch} from {base_url}")
        
        # First, extract genre and tags from main novel page
        novel_metadata = self._extract_novel_metadata(base_url)
        genre_list = novel_metadata.get("genre", [])
        novel_tags = novel_metadata.get("tags", [])
        
        # Combine user tags with extracted tags
        combined_tags = list(tags) + novel_tags if tags else novel_tags
        combined_tags = list(set(combined_tags))  # Remove duplicates
        
        logger.info(f"[NOVEL] Extracted genre: {genre_list}")
        logger.info(f"[NOVEL] Extracted tags: {novel_tags}")
        
        # Generate chapter URLs and scrape each
        for chapter_num in range(start_ch, end_ch + 1):
            chapter_url = self._generate_chapter_url(base_url, chapter_num)
            logger.info(f"[NOVEL] Chapter {chapter_num}: {chapter_url}")
            
            # Pass genre to _scrape_single_url via a temporary attribute
            self._current_genre = genre_list
            result = self._scrape_single_url(chapter_url, combined_tags)
            self._current_genre = None
            
            results.append(result)
            
            # Track chapter for index
            if result.get("status") == "completed":
                chapter_list.append({
                    "chapter": chapter_num,
                    "title": result.get("title", f"Chapter {chapter_num}"),
                    "file_path": result.get("file_path", ""),
                    "word_count": result.get("word_count", 0),
                })
        
        # Create/update index.md
        if chapter_list:
            self._create_novel_index(base_url, chapter_list, combined_tags, genre_list)
        
        return {
            "status": "completed",
            "chapters_scraped": len([r for r in results if r.get("status") == "completed"]),
            "chapters_failed": len([r for r in results if r.get("status") == "failed"]),
            "chapter_details": results,
        }

    def _extract_novel_metadata(self, url: str) -> dict[str, list]:
        """Extract genre and tags from novel main page using Playwright."""
        from scraper.engines.playwright_engine import PlaywrightEngine
        
        genre_list: list[str] = []
        tags_list: list[str] = []
        
        try:
            # Use Playwright to get the main novel page HTML
            engine = PlaywrightEngine()
            html_content = engine.scrape(url)
            
            if not html_content:
                logger.warning(f"[NOVEL] Could not fetch main novel page: {url}")
                return {"genre": genre_list, "tags": tags_list}
            
            if BeautifulSoup:
                soup = BeautifulSoup(html_content, "html.parser")
                
                # Extract genre from .genres .genre
                genre_elements = soup.select(".genres .genre")
                for elem in genre_elements:
                    text = elem.get_text(strip=True).lower()
                    if text and text not in genre_list:
                        genre_list.append(text)
                
                # Extract tags from .tag elements
                tag_elements = soup.select(".tag")
                for elem in tag_elements:
                    text = elem.get_text(strip=True).lower()
                    if text and text not in tags_list:
                        tags_list.append(text)
                
                logger.info(f"[NOVEL] Extracted genre: {genre_list}")
                logger.info(f"[NOVEL] Extracted tags: {tags_list}")
            else:
                logger.warning("[NOVEL] BeautifulSoup not available, cannot parse genre/tags")
                
        except Exception as e:
            logger.warning(f"[NOVEL] Error extracting metadata: {e}")
        
        return {"genre": genre_list, "tags": tags_list}

    def _generate_chapter_url(self, base_url: str, chapter_num: int) -> str:
        """Generate chapter URL from base URL."""
        # Remove any existing chapter suffix
        url = base_url.split("?")[0]  # Remove query params
        
        # Common patterns: /chapter-1, /ch/1, /chapter_1
        if "/chapter-" in url.lower():
            # Already has chapter pattern, replace number
            url = re.sub(r'/chapter-\d+', f'/chapter-{chapter_num}', url, flags=re.IGNORECASE)
        elif "/ch/" in url.lower():
            url = re.sub(r'/ch/\d+', f'/ch/{chapter_num}', url, flags=re.IGNORECASE)
        elif "/chapter_" in url.lower():
            url = re.sub(r'/chapter_\d+', f'/chapter_{chapter_num}', url, flags=re.IGNORECASE)
        else:
            # Append chapter pattern
            url = f"{url.rstrip('/')}/chapter-{chapter_num}"
        
        return url

    def _create_novel_index(self, base_url: str, chapters: list, tags: list, genre: list | None = None) -> None:
        """Create or update novel index.md with chapter list."""
        index_path = get_novel_index_path(base_url)
        
        # Extract novel title from base URL
        novel_slug = base_url.split("/")[-1] if "/" in base_url else "Unknown"
        # Clean up slug (remove chapter numbers if present)
        novel_slug = re.sub(r'-chapter-\d+$', '', novel_slug, flags=re.IGNORECASE)
        novel_slug = novel_slug.replace("-", " ").title()
        
        # Build YAML frontmatter for index
        import json
        yaml_frontmatter = f"""---
title: "{novel_slug}"
source_url: "{base_url.split('?')[0]}"
"""
        # Use genre if available, otherwise use tags as genre
        display_genre = genre if genre else tags
        if display_genre:
            yaml_frontmatter += f"genre: {json.dumps(display_genre)}\n"
        
        yaml_frontmatter += f"""tags: {json.dumps(tags)}
content_type: "novel"
---
"""
        
        # Build index content
        index_content = yaml_frontmatter
        index_content += f"# {novel_slug}\n\n"
        index_content += f"**Total Chapters:** {len(chapters)}\n\n"
        index_content += "---\n\n"
        index_content += "## Chapter List\n\n"
        
        for ch in chapters:
            # Extract just the filename from the full path
            full_path = ch.get("file_path", "")
            ch_file = full_path.split("\\")[-1].split("/")[-1] if full_path else f"chapter-{ch.get('chapter')}.md"
            word_count = ch.get("word_count", 0)
            index_content += f"- [Chapter {ch.get('chapter')}]({ch_file}) ({word_count} words)\n"
        
        # Add tags
        if tags:
            index_content += f"\n---\n\n**Tags:** {', '.join(tags)}\n"
        
        # Write index file
        index_path.write_text(index_content, encoding="utf-8")
        logger.info(f"[NOVEL] Created index: {index_path}")

    def _scrape_single_url(self, url: str, tags: list) -> dict:
        """Scrape a single URL."""
        logger.info(f"[1/6] ROUTING: {url}")
        route = route_url(url)

        if route == "skip":
            logger.info(f"[SKIPPED] YouTube URL: {url}")
            return {
                "url": url,
                "status": "skipped",
                "error": "YouTube URL - skipped",
                "method": None,
            }

        logger.info(f"[2/6] ROBOTS.TXT: Checking {url}")
        if self.settings.get("respect_robots_txt", True):
            allowed, reason = can_fetch(url)
            if not allowed:
                logger.debug(f"Skipping {url}: {reason}")
                return {
                    "url": url,
                    "status": "skipped",
                    "error": reason,
                    "method": None,
                }

            delay = get_crawl_delay(url)
            if delay > 0:
                logger.info(f"Waiting {delay}s for crawl delay")
                time.sleep(delay)

        logger.info(f"[3/6] FALLBACK CHAIN: Starting for route '{route}' - {url}")
        result = self.fallback.execute(url, route)

        if result.success:
            return self._handle_success(url, result, tags)
        else:
            return self._handle_failure(url, result)

    def _handle_success(self, url: str, result: FallbackResult, tags: list) -> dict:
        """Process successful scrape."""
        start_time = time.time()

        logger.info(f"[4/6] EXTRACTING TEXT: Engine '{result.method}' returned {len(result.content or '')} bytes")

        # Playwright engines return plain text, no need for HTML extraction
        if result.method in ("playwright", "playwright_alt", "playwright_tls", "cloudscraper"):
            text_content: str = result.content or ""
        else:
            text_content = TextExtractor.extract_from_html(
                result.content or "", self.settings.get("export_format", "md")
            ) or ""

        if not text_content:
            logger.warning(f"[4/6] EXTRACTING TEXT: No content extracted!")
            return self._handle_failure(
                url,
                FallbackResult(
                    success=False,
                    error="No content extracted",
                    attempted_methods=result.attempted_methods,
                    extraction_time_ms=result.extraction_time_ms,
                ),
            )

        logger.info(f"[4/6] EXTRACTING TEXT: Extracted {len(text_content)} chars, {len(text_content.split())} words")

        # Determine if this is a novel URL
        url_is_novel = is_novel_url(url)
        
        # Select folder based on URL type
        if url_is_novel:
            folder = get_novel_folder(url)
        else:
            folder = get_normal_folder(url)
        
        word_count = len(text_content.split())

        # Extract title from content - look for # heading first
        title_from_url = url.split("/")[-1][:50]
        title_from_url = title_from_url.split("?")[0].replace("-", " ").replace("_", " ").strip()
        title_from_url = title_from_url.title() if title_from_url else "Untitled"
        
        extracted_title = title_from_url
        if text_content:
            lines = text_content.split("\n")
            for line in lines[:10]:
                line = line.strip()
                if line.startswith("# "):
                    # Found markdown heading
                    extracted_title = line[2:].strip()[:100]
                    break
                elif line and not line.startswith("---") and len(line) < 80:
                    # First non-empty line that's not frontmatter
                    # Only use if it looks like a title (short, no sentence-ending punctuation)
                    if len(line.split()) < 12 and not line.endswith("."):
                        extracted_title = line[:100]
                        break

        logger.info(f"[5/6] PROCESSING: Title='{extracted_title[:50]}...'")

        # Determine content type from URL
        url_lower = url.lower()
        if "wikipedia.org" in url_lower or "wiktionary.org" in url_lower:
            content_type = "wiki"
        elif "/novel/" in url_lower or "/chapter-" in url_lower or "/ch/" in url_lower or "/book-" in url_lower:
            content_type = "novel"
        elif "/blog/" in url_lower or "/post/" in url_lower or "/article/" in url_lower:
            content_type = "blog"
        else:
            content_type = "article"

        logger.info(f"[5/6] PROCESSING: Content type detected as '{content_type}'")

        # Extract tags based on content type
        extracted_tags = list(tags) if tags else []

        # Add wiki tag for Wikipedia content
        if content_type == "wiki":
            if "wiki" not in extracted_tags:
                extracted_tags.append("wiki")
            # Try to extract language from URL
            # e.g., en.wikipedia.org -> en, zh.wikipedia.org -> zh
            from urllib.parse import urlparse
            parsed = urlparse(url)
            netloc = parsed.netloc.lower()
            if "." in netloc:
                parts = netloc.split(".")
                if len(parts) >= 2:
                    potential_lang = parts[0]
                    # Make sure it's not "www" and is a valid language code (usually 2 chars)
                    if potential_lang != "www" and len(potential_lang) <= 5:
                        extracted_tags.append(potential_lang)

        # Extract genre for novels (from main page metadata)
        genre_list: list[str] = []
        if content_type == "novel":
            # Use genre extracted from main novel page (if available), otherwise use tags as genre
            if hasattr(self, '_current_genre') and self._current_genre:
                genre_list = self._current_genre
            elif extracted_tags:
                genre_list = extracted_tags.copy()

        # Add content type as tag
        if content_type not in extracted_tags:
            extracted_tags.append(content_type)

        logger.info(f"[5/6] PROCESSING: Tags={extracted_tags}, Genre={genre_list}")

        # Generate custom filename for novels
        custom_filename = None
        if content_type == "novel":
            # Extract chapter number from URL
            chapter_match = re.search(r'/chapter[-_]?(\d+)', url, re.IGNORECASE)
            if chapter_match:
                chapter_num = chapter_match.group(1)
                custom_filename = f"chapter-{chapter_num}"
            else:
                custom_filename = "chapter-1"
            logger.info(f"[6/6] SAVING: Novel filename = '{custom_filename}.md'")

        logger.info(f"[6/6] SAVING: Saving to folder '{folder}'")
        file_path = save_normal_article(
            folder=folder,
            url=url,
            title=extracted_title,
            content=text_content,
            tags=extracted_tags,
            word_count=word_count,
            output_format=self.settings.get("export_format", "md"),
            engine=result.method or "unknown",
            content_type=content_type,
            custom_filename=custom_filename,
            genre=genre_list if genre_list else extracted_tags,
        )

        # Apply markdown linting
        try:
            lint_service = LintService()
            lint_result = lint_service.lint_file(str(file_path), fix=True)
            if lint_result.fixed_issues > 0:
                logger.debug(f"Linted {file_path}: {lint_result.fixed_issues} fixes")
        except Exception as e:
            logger.debug(f"Linting skipped for {file_path}: {e}")

        scrape_result = scraper_service.record_success(
            url=url,
            method=result.method or "",
            file_path=str(file_path),
            word_count=word_count,
            extraction_time_ms=result.extraction_time_ms,
            tags=tags,
        )

        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.info(
            f"[DONE] Completed: {url} -> {file_path.name} ({word_count} words, {elapsed_ms}ms) via {result.method}"
        )

        return {
            "url": url,
            "status": "completed",
            "title": extracted_title,
            "method": result.method,
            "file_path": str(file_path),
            "word_count": word_count,
            "extraction_time_ms": result.extraction_time_ms,
            "fallback_chain": result.attempted_methods,
        }

    def _handle_failure(self, url: str, result: FallbackResult) -> dict:
        """Handle failed scrape."""
        error = result.error or "All engines failed"
        method = result.attempted_methods[-1] if result.attempted_methods else None

        logger.error(f"Failed to scrape {url}: {error}")

        scrape_result = scraper_service.record_failure(
            url=url,
            error=error,
            method=method,
        )

        return {
            "url": url,
            "status": "failed",
            "method": method,
            "error": error,
            "fallback_chain": result.attempted_methods,
        }

    def run(self, urls: list, force_sync: bool = False) -> list | str:
        """
        Run scraping for multiple URLs with concurrency.

        Args:
            urls: List of URL entries with 'url' and optional 'tags'
            force_sync: If True, skip concurrent job submission and run synchronously

        Returns:
            List of results
        """
        concurrent_jobs = int(self.settings.get("concurrent_jobs", 1))

        if force_sync or concurrent_jobs <= 1:
            results = []
            for entry in urls:
                result = self.scrape_normal_url(entry["url"], entry.get("tags", []))
                results.append(result)
                state.save_queue()
            return results
        else:
            return background_job_service.submit_job(urls)


def run_scraper(urls: list) -> list | str:
    """Main entry point for scraping."""
    runner = ScraperRunner()
    return runner.run(urls)
