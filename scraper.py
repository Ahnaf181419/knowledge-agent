"""
Web Scraper - Dual Mode Edition
======================================
Features:
- Playwright mode (local browser, CAPTCHA support)
- WebScrapingAPI mode (cloud, faster, requires API key)
- REST API for job control (start/pause/resume/stop/status)
- Interactive CLI with mode selection
- Background scraping with real-time status
"""

import os
import sys
import time
import random
import logging
import json
import re
import argparse
import threading
from pathlib import Path
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Callable
from dataclasses import dataclass, field, asdict

from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout

# Import configuration
from config.py import (
    NOVEL_NAME,
    NOVEL_SLUG,
    AUTHOR,
    GENRE,
    CHAPTER_START,
    CHAPTER_END,
    WEBSCRAPINGAPI_KEY,
    BASE_URL,
    DELAY_MIN,
    DELAY_MAX,
    HEADLESS,
    RATE_LIMIT_MONTHLY,
    RATE_LIMIT_RESET_DAY,
    REQUEST_TIMEOUT_MS,
    API_REQUEST_TIMEOUT,
    RETRY_COUNT,
    SESSION_EXPIRY_DAYS,
)

# ── Optional Imports ──────────────────────────────────────────────────
HAS_STEALTH = False
stealth_sync = None
try:
    from playwright_stealth import stealth_sync

    HAS_STEALTH = True
except ImportError:
    pass

HAS_REQUESTS = False
try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    pass

HAS_LXML = False
lxml_html = None
try:
    from lxml import html as lxml_html

    HAS_LXML = True
except ImportError:
    pass

HAS_FASTAPI = False
FastAPI = None
HTTPException = None
uvicorn = None
try:
    from fastapi import FastAPI, HTTPException
    import uvicorn

    HAS_FASTAPI = True
except ImportError:
    pass

# ── Derived Paths ─────────────────────────────────────────────────────
DOWNLOADS_DIR = Path(__file__).parent / "output" / NOVEL_SLUG
SESSION_FILE = Path(__file__).parent / "sessions" / f"{NOVEL_SLUG}_cookies.json"
DEBUG_DIR = Path(__file__).parent / "debug"
API_USAGE_FILE = Path(__file__).parent / "sessions" / "webscrapingapi_usage.json"

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("scraper")


# ═══════════════════════════════════════════════════════════════════════
# RATE LIMITER
# ═══════════════════════════════════════════════════════════════════════


class RateLimiter:
    """Track WebScrapingAPI usage - only 200 responses count"""

    def __init__(self, monthly_limit: int, reset_day: int, usage_file: Path):
        self.monthly_limit = monthly_limit
        self.reset_day = reset_day
        self.usage_file = usage_file
        self._ensure_usage_file()

    def _ensure_usage_file(self):
        """Create usage file if it doesn't exist"""
        self.usage_file.parent.mkdir(exist_ok=True)
        if not self.usage_file.exists():
            self._save_usage(
                {"month": self._current_month(), "calls_made": 0, "last_call": None}
            )

    def _current_month(self) -> str:
        return datetime.now().strftime("%Y-%m")

    def _get_reset_date(self) -> str:
        now = datetime.now()
        if now.day >= self.reset_day:
            next_month = now.month + 1 if now.month < 12 else 1
            year = now.year if now.month < 12 else now.year + 1
        else:
            next_month = now.month
            year = now.year
        return f"{year}-{next_month:02d}-{self.reset_day:02d}"

    def _load_usage(self) -> dict:
        try:
            return json.loads(self.usage_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError, OSError):
            return {"month": self._current_month(), "calls_made": 0, "last_call": None}

    def _save_usage(self, data: dict):
        data["reset_date"] = self._get_reset_date()
        data["monthly_limit"] = self.monthly_limit
        self.usage_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def get_usage(self) -> dict:
        """Load current usage, reset if new month"""
        data = self._load_usage()
        if data.get("month") != self._current_month():
            data = {"month": self._current_month(), "calls_made": 0, "last_call": None}
            self._save_usage(data)
        return data

    def record_call(self):
        """Increment counter for successful 200 response"""
        data = self.get_usage()
        data["calls_made"] = data.get("calls_made", 0) + 1
        data["last_call"] = datetime.now().isoformat()
        self._save_usage(data)

    def can_make_call(self) -> bool:
        """Check if under limit"""
        data = self.get_usage()
        return data.get("calls_made", 0) < self.monthly_limit

    def get_remaining(self) -> int:
        """Return remaining calls this month"""
        data = self.get_usage()
        used = data.get("calls_made", 0)
        return max(0, self.monthly_limit - used)

    def get_reset_date(self) -> str:
        """Return date when limit resets"""
        return self._get_reset_date()

    def get_used(self) -> int:
        """Return calls made this month"""
        data = self.get_usage()
        return data.get("calls_made", 0)

    def display_status(self, requested_chapters: int = 0):
        """Print current usage status"""
        remaining = self.get_remaining()
        used = self.get_used()
        reset = self.get_reset_date()

        print("\n" + "=" * 60)
        print("  WEBSCRAPINGAPI RATE LIMIT STATUS")
        print("=" * 60)
        print(f"  Monthly Limit: {self.monthly_limit:,} calls")
        print(f"  Used This Month: {used:,} calls (200 responses only)")
        print(f"  Remaining: {remaining:,} calls")
        print(f"  Resets On: {reset}")

        if requested_chapters > 0:
            estimated_max = requested_chapters * 3
            print(f"\n  Requested: {requested_chapters} chapters")
            print(
                f"  Estimated Usage: {requested_chapters}-{estimated_max} calls (retries don't count)"
            )

            if remaining < requested_chapters:
                print(f"\n  WARNING: Not enough calls remaining!")
            else:
                after_remaining = remaining - requested_chapters
                print(f"  After this job: ~{after_remaining:,} remaining")
        print("=" * 60)


# ═══════════════════════════════════════════════════════════════════════
# JOB MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════


class JobStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ScraperMode(str, Enum):
    PLAYWRIGHT = "playwright"
    WEBSCRAPINGAPI = "webscrapingapi"


@dataclass
class ScrapingJob:
    status: JobStatus = JobStatus.IDLE
    mode: str = ScraperMode.PLAYWRIGHT.value
    start_chapter: int = 0
    end_chapter: int = 0
    current_chapter: int = 0
    total_chapters: int = 0
    success_count: int = 0
    failed_count: int = 0
    results: list = field(default_factory=list)
    error: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None

    def to_dict(self):
        return asdict(self)


job = ScrapingJob()
job_lock = threading.Lock()


def reset_job() -> None:
    global job
    with job_lock:
        job = ScrapingJob()


def update_job(**kwargs) -> None:
    with job_lock:
        for key, value in kwargs.items():
            if hasattr(job, key):
                setattr(job, key, value)


def get_job_state() -> dict:
    with job_lock:
        return job.to_dict()


# ═══════════════════════════════════════════════════════════════════════
# SESSION MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════


def save_session(cookies: list) -> None:
    SESSION_FILE.parent.mkdir(exist_ok=True)
    session_data = {
        "saved_at": datetime.now().isoformat(),
        "expires_at": (
            datetime.now() + timedelta(days=SESSION_EXPIRY_DAYS)
        ).isoformat(),
        "cookies": cookies,
    }
    SESSION_FILE.write_text(json.dumps(session_data, indent=2), encoding="utf-8")
    log.info(f"Session saved (valid until {session_data['expires_at'][:10]})")


def load_session() -> Optional[list]:
    if not SESSION_FILE.exists():
        return None
    try:
        data = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
        if datetime.now() > datetime.fromisoformat(data["expires_at"]):
            log.info("Session expired.")
            return None
        return data["cookies"]
    except (json.JSONDecodeError, KeyError, OSError):
        return None


# ═══════════════════════════════════════════════════════════════════════
# TEXT PROCESSING
# ═══════════════════════════════════════════════════════════════════════


def extract_chapter_text(page) -> tuple[Optional[str], Optional[str]]:
    """Extract text from Playwright page using XPath"""
    try:
        xpath_query = "//div[count(p) > 5]"
        container = page.locator(f"xpath={xpath_query}").first
        paragraphs = container.locator("p").all_text_contents()

        if paragraphs:
            text = "\n\n".join(p.strip() for p in paragraphs if p.strip())
            if len(text) > 200:
                title = None
                try:
                    title_loc = container.locator(
                        "xpath=./h1 | ./h2 | .//h1 | .//h2"
                    ).first
                    if title_loc.count() > 0:
                        title = title_loc.text_content(timeout=500).strip()
                except Exception:
                    pass
                return text, title
    except Exception as e:
        log.error(f"Extraction error: {e}")
    return None, None


def extract_chapter_text_from_html(
    html_content: str,
) -> tuple[Optional[str], Optional[str]]:
    """Extract text from HTML string using lxml (for WebScrapingAPI)"""
    if not HAS_LXML:
        log.error("lxml not installed. Run: pip install lxml")
        return None, None

    try:
        tree = lxml_html.fromstring(html_content)

        containers = tree.xpath("//div[count(p) > 5]")
        if not containers:
            return None, None

        container = containers[0]
        paragraphs = container.xpath(".//p/text()")

        if paragraphs:
            text = "\n\n".join(p.strip() for p in paragraphs if p.strip())
            if len(text) > 200:
                title = None
                title_elems = container.xpath(".//h1 | .//h2")
                if title_elems:
                    title = title_elems[0].text_content().strip()
                return text, title
    except Exception as e:
        log.error(f"HTML extraction error: {e}")

    return None, None


def clean_text(text: str) -> str:
    ad_patterns = [
        r"\bNext\s+Chapter\b",
        r"\bPrevious\s+Chapter\b",
        r"\bChapter\s+List\b",
        r"^\s*Translator:\s*.*$",
        r"^\s*Editor:\s*.*$",
        r"\[AD\]",
        r"\[Sponsored.*?\]",
        r"Click\s+to\s+read\s+next",
    ]
    for pattern in ad_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ═══════════════════════════════════════════════════════════════════════
# FILE I/O
# ═══════════════════════════════════════════════════════════════════════


def get_existing_chapter(chapter_num: int) -> Optional[Path]:
    path = DOWNLOADS_DIR / f"chapter_{chapter_num}.md"
    return path if path.exists() else None


def save_chapter(
    chapter_num: int, title: Optional[str], text: str, url: str
) -> tuple[Path, int]:
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    cleaned = clean_text(text)
    word_count = len(cleaned.split())

    filename = f"chapter_{chapter_num}.md"
    path = DOWNLOADS_DIR / filename

    title_safe = title or "N/A"
    title_safe = re.sub(r'[<>:"/\\|?*]', "", title_safe)

    front_matter = [
        "---",
        f"chapter_number: {chapter_num}",
        f'title: "{title_safe}"',
        f'novel: "{NOVEL_NAME}"',
        f'author: "{AUTHOR}"',
        f"word_count: {word_count}",
        f'source: "{url}"',
        f"scraped_at: {datetime.now().isoformat()}",
        "---",
    ]

    chapter_title = title or f"Chapter {chapter_num}"
    content = "\n".join(front_matter) + "\n\n" + f"# {chapter_title}\n\n" + cleaned
    path.write_text(content, encoding="utf-8")
    return path, word_count


def generate_index_file(start: int, end: int, results: list):
    index_file = DOWNLOADS_DIR / "chapters_index.md"

    lines = [
        f"# {NOVEL_NAME}",
        f"\n**Author:** {AUTHOR}",
        f"\n**Genre:** {', '.join(GENRE)}",
        f"\n**Total Chapters:** {sum(1 for r in results if r['status'] == 'SUCCESS')}",
        "\n---\n",
        "## Chapter List\n",
    ]

    for ch_num in range(start, end + 1):
        ch_file = DOWNLOADS_DIR / f"chapter_{ch_num}.md"
        if ch_file.exists():
            lines.append(f"- [Chapter {ch_num}]({ch_file.name})")
        else:
            status = next(
                (r["status"] for r in results if r["chapter"] == ch_num), "MISSING"
            )
            lines.append(f"- Chapter {ch_num} ({status})")

    index_file.write_text("\n".join(lines), encoding="utf-8")
    log.info(f"Generated chapters index: {index_file}")


def dump_debug_html(html_content: str, chapter_num: int):
    DEBUG_DIR.mkdir(exist_ok=True)
    path = DEBUG_DIR / f"fail_ch_{chapter_num}.html"
    path.write_text(html_content, encoding="utf-8")
    log.warning(f"Debug HTML saved to {path}")


# ═══════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════


def human_delay(current: int, total: int, check_pause: Optional[Callable] = None):
    if current >= total:
        return None

    wait = random.uniform(DELAY_MIN, DELAY_MAX)
    log.info(f"Waiting {wait / 60:.1f} minutes...")

    remaining = int(wait)
    while remaining > 0:
        if check_pause:
            state = check_pause()
            if state == JobStatus.PAUSED:
                return "paused"
            if state == JobStatus.CANCELLED:
                return "cancelled"

        mins, secs = divmod(remaining, 60)
        print(f"\r   Next chapter in {mins:02d}:{secs:02d} ", end="", flush=True)
        time.sleep(1)
        remaining -= 1

    print("\r" + " " * 40 + "\r", end="", flush=True)
    return None


def print_progress_row(chapter: int, status: str, details: str):
    status_str = "SUCCESS" if status == "SUCCESS" else "FAILED "
    print(f"{chapter:<10} {status_str:<10} {details:<40}")


def print_summary_table(results: list, session_valid_until: Optional[str] = None):
    print("\n" + "=" * 60)
    print("EXTRACTION SUMMARY")
    print("=" * 60)

    total = len(results)
    success = sum(1 for r in results if r["status"] == "SUCCESS")
    failed = total - success

    print(f"{'Chapter':<10} {'Status':<10} {'Details':<40}")
    print("-" * 60)

    for r in results:
        status_icon = "SUCCESS" if r["status"] == "SUCCESS" else "FAILED "
        print(f"{r['chapter']:<10} {status_icon:<10} {r['details']:<40}")

    print("-" * 60)
    print(f"TOTAL: {success}/{total} chapters saved | Failed: {failed}")

    if session_valid_until:
        print(f"Session valid until: {session_valid_until}")
    print(f"Output directory: {DOWNLOADS_DIR.absolute()}")
    print("=" * 60)


# ═══════════════════════════════════════════════════════════════════════
# CORE SCRAPER - PLAYWRIGHT MODE
# ═══════════════════════════════════════════════════════════════════════


def check_job_state():
    with job_lock:
        return job.status


def run_scraper_playwright(chapters: list, force: bool = False, is_api: bool = False):
    """Playwright-based scraper with CAPTCHA support and delays"""
    total = len(chapters)
    results = []
    session_valid_until = None

    update_job(
        status=JobStatus.RUNNING,
        mode=ScraperMode.PLAYWRIGHT.value,
        start_chapter=chapters[0] if chapters else 0,
        end_chapter=chapters[-1] if chapters else 0,
        current_chapter=chapters[0] if chapters else 0,
        total_chapters=total,
        started_at=datetime.now().isoformat(),
        results=[],
    )

    log.info(f"Starting Playwright mode: {NOVEL_NAME} - {total} chapters")

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                headless=HEADLESS,
                args=["--disable-blink-features=AutomationControlled"],
            )
            context = browser.new_context(
                viewport={"width": 1280, "height": 900},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            )
            page = context.new_page()

            if HAS_STEALTH:
                stealth_sync(page)

            session_cookies = load_session()
            if session_cookies:
                context.add_cookies(session_cookies)
                try:
                    data = json.loads(SESSION_FILE.read_text())
                    session_valid_until = data["expires_at"][:10]
                except (json.JSONDecodeError, KeyError, OSError):
                    pass
                log.info("Loaded session cookies")

            first_url = BASE_URL.format(n=chapters[0] if chapters else 1)
            page.goto(
                first_url, wait_until="domcontentloaded", timeout=REQUEST_TIMEOUT_MS
            )

            if any(
                x in page.title().lower()
                for x in ["just a moment", "captcha", "verify"]
            ):
                if HEADLESS:
                    log.warning("CAPTCHA detected but running in headless mode!")
                    log.warning(
                        "Set HEADLESS=False in config.py to solve CAPTCHA manually"
                    )
                    log.warning("Attempting to continue (may fail)...")
                    time.sleep(5)
                elif is_api:
                    log.warning("CAPTCHA detected! Please solve in browser window...")
                    for _ in range(120):
                        time.sleep(1)
                        if "just a moment" not in page.title().lower():
                            break
                else:
                    print("\n" + "=" * 60)
                    print("  CAPTCHA DETECTED - Please solve it in the browser")
                    print("=" * 60)
                    input(">>> Press ENTER here after solving...")

                save_session(context.cookies())
                session_valid_until = (
                    datetime.now() + timedelta(days=SESSION_EXPIRY_DAYS)
                ).strftime("%Y-%m-%d")

            if not SESSION_FILE.exists():
                save_session(context.cookies())
                session_valid_until = (
                    datetime.now() + timedelta(days=SESSION_EXPIRY_DAYS)
                ).strftime("%Y-%m-%d")

            if not is_api:
                print("\n" + "=" * 60)
                print(f"{'Chapter':<10} {'Status':<10} {'Details':<40}")
                print("-" * 60)

            for i, ch in enumerate(chapters, start=1):
                state = check_job_state()
                if state == JobStatus.PAUSED:
                    log.info(f"Job paused at chapter {ch}")
                    update_job(status=JobStatus.PAUSED)
                    if not is_api:
                        print("\n[PAUSED] Job paused. Use 'resume' to continue.")
                    browser.close()
                    return
                if state == JobStatus.CANCELLED:
                    log.info(f"Job cancelled at chapter {ch}")
                    update_job(
                        status=JobStatus.CANCELLED,
                        finished_at=datetime.now().isoformat(),
                    )
                    browser.close()
                    return

                update_job(current_chapter=ch)
                url = BASE_URL.format(n=ch)

                if not force:
                    existing = get_existing_chapter(ch)
                    if existing:
                        if not is_api:
                            print_progress_row(
                                ch, "SKIPPED", "File exists (use --force)"
                            )
                        continue

                success = False
                is_first_chapter = i == 1
                for attempt in range(RETRY_COUNT):
                    try:
                        if not is_first_chapter:
                            page.goto(
                                url,
                                wait_until="domcontentloaded",
                                timeout=REQUEST_TIMEOUT_MS,
                            )

                        page.mouse.move(random.randint(0, 1200), random.randint(0, 800))
                        page.wait_for_timeout(random.randint(1000, 2000))

                        text, title = extract_chapter_text(page)

                        if text and len(text) > 100:
                            path, word_count = save_chapter(ch, title, text, url)
                            result = {
                                "chapter": ch,
                                "status": "SUCCESS",
                                "details": f"Saved ({word_count:,} words)",
                            }
                            results.append(result)
                            update_job(
                                results=results.copy(),
                                success_count=len(
                                    [r for r in results if r["status"] == "SUCCESS"]
                                ),
                            )
                            if not is_api:
                                print_progress_row(
                                    ch, "SUCCESS", f"Saved ({word_count:,} words)"
                                )
                            success = True
                            break
                        else:
                            dump_debug_html(page.content(), ch)

                    except PwTimeout:
                        pass
                    except Exception as e:
                        log.error(f"Attempt {attempt + 1} Error: {e}")

                    time.sleep(5)

                if not success:
                    result = {
                        "chapter": ch,
                        "status": "FAILED",
                        "details": "Extraction failed after 3 attempts",
                    }
                    results.append(result)
                    update_job(
                        results=results.copy(),
                        failed_count=len(
                            [r for r in results if r["status"] == "FAILED"]
                        ),
                    )
                    if not is_api:
                        print_progress_row(
                            ch, "FAILED", "Extraction failed after 3 attempts"
                        )

                delay_result = human_delay(
                    i, total, check_job_state if is_api else None
                )
                if delay_result in ["paused", "cancelled"]:
                    browser.close()
                    return

            browser.close()

    except Exception as e:
        update_job(status=JobStatus.CANCELLED, error=str(e))
        log.error(f"Scraper error: {e}")
        return

    update_job(
        status=JobStatus.COMPLETED,
        finished_at=datetime.now().isoformat(),
        results=results,
    )

    if not is_api:
        print_summary_table(results, session_valid_until)

    if any(r["status"] == "SUCCESS" for r in results):
        start = chapters[0]
        end = chapters[-1]
        generate_index_file(start, end, results)
        log.info("Project documentation complete!")


# ═══════════════════════════════════════════════════════════════════════
# CORE SCRAPER - WEBSCRAPINGAPI MODE
# ═══════════════════════════════════════════════════════════════════════


def validate_api_key(api_key: str) -> tuple[bool, str]:
    """Validate WebScrapingAPI key by making a test request"""
    if not HAS_REQUESTS:
        return False, "requests not installed"

    test_url = "https://example.com"
    api_url = "https://api.webscrapingapi.com/v2"

    try:
        params = {"api_key": api_key, "url": test_url}
        response = requests.get(api_url, params=params, timeout=30)

        if response.status_code == 200:
            return True, "Valid"

        try:
            error_data = response.json()
            error_msg = error_data.get("error", f"HTTP {response.status_code}")
        except json.JSONDecodeError:
            error_msg = f"HTTP {response.status_code}"

        return False, error_msg
    except Exception as e:
        return False, str(e)


def run_scraper_api(
    chapters: list, api_key: str, force: bool = False, is_api: bool = False
):
    """WebScrapingAPI-based scraper - fast, no delays, cloud-based

    API Docs: https://docs.webscrapingapi.com/webscrapingapi/getting-started/api-parameters
    Rate Limit: Only 200 responses count toward monthly limit
    """
    if not HAS_REQUESTS:
        log.error("requests not installed. Run: pip install requests")
        return

    if not HAS_LXML:
        log.error("lxml not installed. Run: pip install lxml")
        return

    valid, error = validate_api_key(api_key)
    if not valid:
        log.error("=" * 60)
        log.error("  API KEY VALIDATION FAILED")
        log.error("=" * 60)
        log.error(f"  Error: {error}")
        log.error("")
        log.error("  The API key is invalid or your account is not active.")
        log.error("  Please check:")
        log.error("  1. API key is correct in config.py")
        log.error("  2. Account is active at https://app.webscrapingapi.com/")
        log.error("  3. Trial/subscription has not expired")
        log.error("=" * 60)
        return

    total = len(chapters)
    results = []

    limiter = RateLimiter(RATE_LIMIT_MONTHLY, RATE_LIMIT_RESET_DAY, API_USAGE_FILE)

    remaining = limiter.get_remaining()
    if remaining < total:
        log.error(f"Rate limit too low: {remaining} remaining, {total} requested")
        if not is_api:
            limiter.display_status(total)
            confirm = input("\nContinue anyway? [y/N]: ").strip().lower()
            if confirm not in ["y", "yes"]:
                print("Cancelled.")
                return
        else:
            return

    if not is_api:
        limiter.display_status(total)

    update_job(
        status=JobStatus.RUNNING,
        mode=ScraperMode.WEBSCRAPINGAPI.value,
        start_chapter=chapters[0] if chapters else 0,
        end_chapter=chapters[-1] if chapters else 0,
        current_chapter=chapters[0] if chapters else 0,
        total_chapters=total,
        started_at=datetime.now().isoformat(),
        results=[],
    )

    log.info(f"Starting WebScrapingAPI mode: {NOVEL_NAME} - {total} chapters")
    log.info(
        f"Rate Limit: {limiter.get_remaining():,}/{RATE_LIMIT_MONTHLY:,} calls remaining"
    )

    api_url = "https://api.webscrapingapi.com/v2"

    if not is_api:
        print("\n" + "=" * 60)
        print(f"{'Chapter':<10} {'Status':<10} {'Details':<40}")
        print("-" * 60)

    try:
        for i, ch in enumerate(chapters, start=1):
            if not limiter.can_make_call():
                log.error(
                    f"Rate limit reached! {limiter.get_remaining()} calls remaining"
                )
                log.error(f"Resets on: {limiter.get_reset_date()}")
                break

            state = check_job_state()
            if state == JobStatus.PAUSED:
                log.info(f"Job paused at chapter {ch}")
                update_job(status=JobStatus.PAUSED)
                if not is_api:
                    print("\n[PAUSED] Job paused. Use 'resume' to continue.")
                return
            if state == JobStatus.CANCELLED:
                log.info(f"Job cancelled at chapter {ch}")
                update_job(
                    status=JobStatus.CANCELLED, finished_at=datetime.now().isoformat()
                )
                return

            update_job(current_chapter=ch)
            target_url = BASE_URL.format(n=ch)

            if not force:
                existing = get_existing_chapter(ch)
                if existing:
                    if not is_api:
                        print_progress_row(ch, "SKIPPED", "File exists (use --force)")
                    continue

            success = False
            api_auth_error = False
            for attempt in range(RETRY_COUNT):
                try:
                    params = {
                        "api_key": api_key,
                        "url": target_url,
                        "render_js": 1,
                        "country": "us",
                        "timeout": 60000,
                    }

                    response = requests.get(
                        api_url, params=params, timeout=API_REQUEST_TIMEOUT
                    )

                    if response.status_code == 200:
                        limiter.record_call()

                        text, title = extract_chapter_text_from_html(response.text)

                        if text and len(text) > 100:
                            path, word_count = save_chapter(ch, title, text, target_url)
                            remaining_now = limiter.get_remaining()
                            result = {
                                "chapter": ch,
                                "status": "SUCCESS",
                                "details": f"Saved ({word_count:,} words) [{remaining_now:,} left]",
                            }
                            results.append(result)
                            update_job(
                                results=results.copy(),
                                success_count=len(
                                    [r for r in results if r["status"] == "SUCCESS"]
                                ),
                            )
                            if not is_api:
                                print_progress_row(
                                    ch,
                                    "SUCCESS",
                                    f"Saved ({word_count:,} words) [{remaining_now:,} left]",
                                )
                            success = True
                            break
                        else:
                            dump_debug_html(response.text, ch)
                    else:
                        error_msg = f"HTTP {response.status_code}"
                        try:
                            error_data = response.json()
                            if "error" in error_data:
                                error_msg = error_data["error"]
                        except json.JSONDecodeError:
                            pass

                        log.warning(f"API error for chapter {ch}: {error_msg}")

                        if (
                            response.status_code == 403
                            and "not allowed" in error_msg.lower()
                        ):
                            log.error("=" * 60)
                            log.error("  API AUTHENTICATION ERROR")
                            log.error("=" * 60)
                            log.error(f"  Error: {error_msg}")
                            log.error("")
                            log.error("  Possible causes:")
                            log.error("  - Invalid or expired API key")
                            log.error("  - Trial expired")
                            log.error("  - Subscription not active")
                            log.error("")
                            log.error(
                                "  Check your account at: https://app.webscrapingapi.com/"
                            )
                            log.error("=" * 60)
                            api_auth_error = True
                            break

                except Exception as e:
                    log.error(f"Attempt {attempt + 1} Error: {e}")

                time.sleep(2)

            if api_auth_error:
                log.error("Stopping due to API authentication error")
                break

            if not success:
                result = {
                    "chapter": ch,
                    "status": "FAILED",
                    "details": "Extraction failed after 3 attempts",
                }
                results.append(result)
                update_job(
                    results=results.copy(),
                    failed_count=len([r for r in results if r["status"] == "FAILED"]),
                )
                if not is_api:
                    print_progress_row(
                        ch, "FAILED", "Extraction failed after 3 attempts"
                    )

            time.sleep(0.5)

    except Exception as e:
        update_job(status=JobStatus.CANCELLED, error=str(e))
        log.error(f"WebScrapingAPI error: {e}")
        return

    update_job(
        status=JobStatus.COMPLETED,
        finished_at=datetime.now().isoformat(),
        results=results,
    )

    if not is_api:
        print_summary_table(results)
        print(
            f"\nRate Limit Remaining: {limiter.get_remaining():,}/{RATE_LIMIT_MONTHLY:,}"
        )

    if any(r["status"] == "SUCCESS" for r in results):
        start = chapters[0]
        end = chapters[-1]
        generate_index_file(start, end, results)
        log.info("Project documentation complete!")


# ═══════════════════════════════════════════════════════════════════════
# FASTAPI ROUTES
# ═══════════════════════════════════════════════════════════════════════

if HAS_FASTAPI:
    app = FastAPI(
        title="Novel Scraper API",
        description="REST API for controlling web novel scraper (Playwright or WebScrapingAPI)",
        version="3.0.0",
    )

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "novel": NOVEL_NAME}

    @app.get("/scrape/status")
    async def get_status():
        state = get_job_state()
        if state["mode"] == ScraperMode.WEBSCRAPINGAPI.value:
            limiter = RateLimiter(
                RATE_LIMIT_MONTHLY, RATE_LIMIT_RESET_DAY, API_USAGE_FILE
            )
            state["rate_limit"] = {
                "monthly_limit": RATE_LIMIT_MONTHLY,
                "used": limiter.get_used(),
                "remaining": limiter.get_remaining(),
                "resets_on": limiter.get_reset_date(),
            }
        return state

    @app.post("/scrape/start")
    async def start_scraping(
        start: int,
        end: int,
        force: bool = False,
        mode: str = "playwright",
        api_key: Optional[str] = None,
    ):
        current = get_job_state()

        if current["status"] in [JobStatus.RUNNING.value, JobStatus.PAUSED.value]:
            raise HTTPException(400, f"Job already {current['status']}")

        if mode == "webscrapingapi":
            if not api_key and not WEBSCRAPINGAPI_KEY:
                raise HTTPException(400, "api_key required for webscrapingapi mode")
            if not HAS_REQUESTS:
                raise HTTPException(400, "requests not installed")
            if not HAS_LXML:
                raise HTTPException(400, "lxml not installed")

        reset_job()

        effective_api_key = api_key or WEBSCRAPINGAPI_KEY or ""
        if mode == "webscrapingapi" and not effective_api_key:
            raise HTTPException(400, "API key required for webscrapingapi mode")

        def run_in_background():
            if mode == "webscrapingapi":
                run_scraper_api(start, end, effective_api_key, force, is_api=True)
            else:
                run_scraper_playwright(start, end, force, is_api=True)

        thread = threading.Thread(target=run_in_background, daemon=True)
        thread.start()

        return {
            "message": "Scraping started",
            "start": start,
            "end": end,
            "force": force,
            "mode": mode,
        }

    @app.post("/scrape/pause")
    async def pause_scraping():
        current = get_job_state()

        if current["status"] != JobStatus.RUNNING.value:
            raise HTTPException(400, f"Cannot pause: job is {current['status']}")

        update_job(status=JobStatus.PAUSED)
        return {
            "message": "Scraping paused",
            "current_chapter": current["current_chapter"],
        }

    @app.post("/scrape/resume")
    async def resume_scraping():
        current = get_job_state()

        if current["status"] != JobStatus.PAUSED.value:
            raise HTTPException(400, f"Cannot resume: job is {current['status']}")

        def run_in_background():
            if current["mode"] == ScraperMode.WEBSCRAPINGAPI.value:
                run_scraper_api(
                    current["current_chapter"],
                    current["end_chapter"],
                    WEBSCRAPINGAPI_KEY,
                    force=False,
                    is_api=True,
                )
            else:
                run_scraper_playwright(
                    current["current_chapter"],
                    current["end_chapter"],
                    force=False,
                    is_api=True,
                )

        update_job(status=JobStatus.RUNNING)
        thread = threading.Thread(target=run_in_background, daemon=True)
        thread.start()

        return {
            "message": "Scraping resumed",
            "from_chapter": current["current_chapter"],
        }

    @app.post("/scrape/stop")
    async def stop_scraping():
        current = get_job_state()

        if current["status"] not in [JobStatus.RUNNING.value, JobStatus.PAUSED.value]:
            raise HTTPException(400, f"Cannot stop: job is {current['status']}")

        update_job(status=JobStatus.CANCELLED, finished_at=datetime.now().isoformat())
        return {
            "message": "Scraping stopped",
            "chapters_completed": current["success_count"],
        }

    @app.on_event("startup")
    async def startup_event():
        log.info(f"API Server started for: {NOVEL_NAME}")
        log.info(f"Output directory: {DOWNLOADS_DIR.absolute()}")


# ═══════════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════════


def parse_args():
    parser = argparse.ArgumentParser(
        description="Web Novel Scraper - Download chapters from wtr-lab.com",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                              Interactive mode
  %(prog)s --start 1 --end 100          Scrape chapters 1-100 (Playwright)
  %(prog)s --start 1 --end 100 --mode webscrapingapi --api-key XXX
  %(prog)s --api --port 8000            Start REST API server
        """,
    )
    parser.add_argument(
        "--start", type=int, default=None, help="Start chapter number (for range mode)"
    )
    parser.add_argument(
        "--end", type=int, default=None, help="End chapter number (for range mode)"
    )
    parser.add_argument(
        "--chapters",
        type=str,
        default=None,
        help="Specific chapters to scrape, comma-separated (e.g., '24,58,304')",
    )
    parser.add_argument(
        "--selection-mode",
        choices=["range", "specific"],
        default="range",
        help="Selection mode: range (start-end) or specific chapter numbers",
    )
    parser.add_argument(
        "--force", action="store_true", help="Overwrite existing chapters"
    )
    parser.add_argument("--api", action="store_true", help="Start REST API server")
    parser.add_argument(
        "--port", type=int, default=8000, help="API server port (default: 8000)"
    )
    parser.add_argument(
        "--host", default="127.0.0.1", help="API server host (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--mode",
        choices=["playwright", "webscrapingapi"],
        default="playwright",
        help="Scraping mode (default: playwright)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="WebScrapingAPI key (overrides config.py)",
    )
    return parser.parse_args()


def interactive_prompt():
    print("\n" + "=" * 60)
    print("  WEB NOVEL SCRAPER")
    print("=" * 60)
    print(f"  Novel: {NOVEL_NAME}")
    print(f"  Source: wtr-lab.com")
    print("=" * 60)

    print("\nSelect scraping mode:")
    print("  [1] Playwright (local browser, CAPTCHA support, slower)")
    print("  [2] WebScrapingAPI (cloud, faster, requires API key)")

    while True:
        mode_input = input("\nMode [1-2]: ").strip()
        if mode_input == "1":
            mode = "playwright"
            api_key = None
            break
        elif mode_input == "2":
            if not HAS_REQUESTS:
                print("   requests not installed. Run: pip install requests")
                print("   Falling back to Playwright mode.")
                mode = "playwright"
                api_key = None
                break
            if not HAS_LXML:
                print("   lxml not installed. Run: pip install lxml")
                print("   Falling back to Playwright mode.")
                mode = "playwright"
                api_key = None
                break

            if WEBSCRAPINGAPI_KEY:
                use_config_key = (
                    input(f"   Use API key from config.py? [Y/n]: ").strip().lower()
                )
                if use_config_key not in ["n", "no"]:
                    api_key = WEBSCRAPINGAPI_KEY
                else:
                    api_key = input("   Enter WebScrapingAPI key: ").strip()
            else:
                api_key = input("   Enter WebScrapingAPI key: ").strip()

            if not api_key:
                print("   API key is required for WebScrapingAPI mode.")
                continue
            mode = "webscrapingapi"
            break
        else:
            print("   Please enter 1 or 2")

    print("\nSelect chapter selection mode:")
    print("  [1] Range mode (e.g., 1-100)")
    print("  [2] Specific chapters (e.g., 24,58,304)")

    while True:
        selection_input = input("\nSelection mode [1-2]: ").strip()
        if selection_input == "1":
            selection_mode = "range"
            break
        elif selection_input == "2":
            selection_mode = "specific"
            break
        else:
            print("   Please enter 1 or 2")

    if selection_mode == "range":
        default_start = CHAPTER_START or 1
        while True:
            try:
                start_input = input(f"\nStart chapter [{default_start}]: ").strip()
                start = int(start_input) if start_input else default_start
                if start < 1:
                    print("   Start must be >= 1")
                    continue
                break
            except ValueError:
                print("   Please enter a valid number")

        default_end = CHAPTER_END
        while True:
            try:
                end_prompt = f"End chapter" + (
                    f" [{default_end}]" if default_end else ""
                )
                end_input = input(f"   {end_prompt}: ").strip()
                if not end_input and default_end:
                    end = default_end
                    break
                if not end_input:
                    print("   End chapter is required")
                    continue
                end = int(end_input)
                if end < start:
                    print(f"   End must be >= start ({start})")
                    continue
                break
            except ValueError:
                print("   Please enter a valid number")

        chapters = list(range(start, end + 1))
    else:
        while True:
            chapters_input = input(
                "\nEnter chapters (comma-separated, e.g., 24,58,304): "
            ).strip()
            if not chapters_input:
                print("   Chapter numbers are required")
                continue
            try:
                chapters = [int(x.strip()) for x in chapters_input.split(",")]
                chapters = sorted(set(chapters))
                if any(c < 1 for c in chapters):
                    print("   All chapter numbers must be >= 1")
                    continue
                break
            except ValueError:
                print("   Please enter valid chapter numbers separated by commas")

    total = len(chapters)

    selection_type = f"{selection_mode.title()} mode ({total} chapters)"
    if mode == "playwright":
        estimated_min = (total * DELAY_MIN) / 60
        estimated_max = (total * DELAY_MAX) / 60
        print(f"\nMode: Playwright (local browser)")
        print(f"Selection: {selection_type}")
        print(f"Estimated time: {estimated_min:.1f} - {estimated_max:.1f} hours")
    else:
        limiter = RateLimiter(RATE_LIMIT_MONTHLY, RATE_LIMIT_RESET_DAY, API_USAGE_FILE)
        limiter.display_status(total)
        print(f"\nMode: WebScrapingAPI (cloud)")
        print(f"Selection: {selection_type}")
        print(f"Estimated time: ~{total * 3 / 60:.1f} minutes (no delays)")

    confirm = input("\nProceed? [Y/n]: ").strip().lower()
    if confirm in ["n", "no"]:
        print("Cancelled.")
        sys.exit(0)

    force = input("Force overwrite existing? [y/N]: ").strip().lower() in ["y", "yes"]

    return chapters, force, mode, api_key


def main():
    args = parse_args()

    if args.api:
        if not HAS_FASTAPI:
            print("FastAPI not installed. Run: pip install fastapi uvicorn")
            sys.exit(1)

        print("\n" + "=" * 60)
        print("  NOVEL SCRAPER API SERVER")
        print("=" * 60)
        print(f"  Novel: {NOVEL_NAME}")
        print(f"  URL: http://{args.host}:{args.port}")
        print(f"  Docs: http://{args.host}:{args.port}/docs")
        print("=" * 60)
        print("\nEndpoints:")
        print("  POST /scrape/start?start=1&end=100&mode=playwright")
        print("  POST /scrape/start?start=1&end=100&mode=webscrapingapi&api_key=XXX")
        print("  POST /scrape/pause")
        print("  POST /scrape/resume")
        print("  POST /scrape/stop")
        print("  GET  /scrape/status")
        print("  GET  /health")
        print("=" * 60 + "\n")

        uvicorn.run(app, host=args.host, port=args.port)
        return

    if args.selection_mode == "specific" and args.chapters:
        chapters = [int(x.strip()) for x in args.chapters.split(",")]
        chapters = sorted(set(chapters))
        force = args.force
        mode = args.mode
        api_key = args.api_key or WEBSCRAPINGAPI_KEY or ""
    elif args.end is not None:
        start = args.start or CHAPTER_START or 1
        end = args.end
        chapters = list(range(start, end + 1))
        force = args.force
        mode = args.mode
        api_key = args.api_key or WEBSCRAPINGAPI_KEY or ""
    else:
        chapters, force, mode, api_key = interactive_prompt()

    if mode == "webscrapingapi" and not api_key:
        print(
            "Error: --api-key required for webscrapingapi mode (or set WEBSCRAPINGAPI_KEY in config.py)"
        )
        sys.exit(1)

    reset_job()

    if mode == "webscrapingapi":
        run_scraper_api(chapters, api_key, force, is_api=False)
    else:
        run_scraper_playwright(chapters, force, is_api=False)

    print("\nNEXT STEPS:")
    print(f"  - View chapters: {DOWNLOADS_DIR.absolute()}")
    print("  - Resume later: run script again (skips existing)")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        update_job(status=JobStatus.CANCELLED)
        sys.exit(1)
