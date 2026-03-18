from __future__ import annotations

import json
import random
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlparse

if TYPE_CHECKING:
    from playwright.sync_api import Browser, BrowserContext, Page, Playwright


STEALTH_AVAILABLE = False
_stealth_sync = None

try:
    from playwright_stealth import stealth_sync as _stealth_sync
    STEALTH_AVAILABLE = True
except ImportError:
    pass


SESSIONS_DIR = Path(__file__).parent.parent.parent / "sessions"
SESSIONS_DIR.mkdir(exist_ok=True)

_playwright_settings = None


def get_playwright_settings() -> dict:
    global _playwright_settings
    if _playwright_settings is None:
        try:
            from app.config import get_setting
            _playwright_settings = {
                "timeout": get_setting("playwright_timeout", 45000),
                "wait_after_load": get_setting("playwright_wait_after_load", 3000),
                "challenge_timeout": get_setting("playwright_challenge_timeout", 15000),
                "max_retries": get_setting("playwright_max_retries", 3),
            }
        except Exception:
            _playwright_settings = {
                "timeout": 45000,
                "wait_after_load": 3000,
                "challenge_timeout": 15000,
                "max_retries": 3,
            }
    return _playwright_settings


def get_session_file(domain: str) -> Path:
    safe_domain = domain.replace("://", "_").replace("/", "_").replace(".", "_")
    return SESSIONS_DIR / f"{safe_domain}_cookies.json"


def load_session_cookies(context: BrowserContext, url: str) -> bool:
    try:
        domain = urlparse(url).netloc
        session_file = get_session_file(domain)
        
        if session_file.exists():
            data = json.loads(session_file.read_text(encoding="utf-8"))
            expires_at = data.get("expires_at")
            
            if expires_at:
                if datetime.now() > datetime.fromisoformat(expires_at):
                    return False
            
            cookies = data.get("cookies", [])
            if cookies:
                context.add_cookies(cookies)
                return True
    except Exception:
        pass
    return False


def save_session_cookies(context: BrowserContext, url: str) -> None:
    try:
        domain = urlparse(url).netloc
        session_file = get_session_file(domain)
        
        cookies = context.cookies()
        expires_at = (datetime.now() + timedelta(days=30)).isoformat()
        
        data = {
            "saved_at": datetime.now().isoformat(),
            "expires_at": expires_at,
            "cookies": cookies,
        }
        
        session_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


def is_challenge_page(page: Page) -> bool:
    try:
        title = page.title().lower()
        challenge_keywords = [
            "just a moment",
            "challenge",
            "captcha",
            "verify",
            "cloudflare",
            "access denied",
            "ddos-guard",
            "checking your browser",
        ]
        return any(kw in title for kw in challenge_keywords)
    except Exception:
        return False


def wait_for_challenge(page: Page, timeout: int | None = None) -> bool:
    settings = get_playwright_settings()
    timeout = timeout or settings["challenge_timeout"]
    try:
        start_time = time.time()
        while time.time() - start_time < timeout / 1000:
            if not is_challenge_page(page):
                return True
            page.wait_for_timeout(1000)
        return False
    except Exception:
        return False


def apply_human_interactions(page: Page) -> None:
    settings = get_playwright_settings()
    wait_time = settings.get("wait_after_load", 3000)
    try:
        page.wait_for_timeout(random.randint(int(wait_time * 0.7), int(wait_time * 1.3)))
        
        viewport = page.viewport_size
        if viewport:
            x = random.randint(0, viewport["width"])
            y = random.randint(0, viewport["height"])
            page.mouse.move(x, y)
            page.wait_for_timeout(random.randint(800, 2000))
            
            for _ in range(random.randint(2, 4)):
                dx = random.randint(-150, 150)
                dy = random.randint(-150, 150)
                new_x = max(0, min(x + dx, viewport["width"]))
                new_y = max(0, min(y + dy, viewport["height"]))
                page.mouse.move(new_x, new_y)
                page.wait_for_timeout(random.randint(300, 800))
        
        for _ in range(random.randint(1, 2)):
            page.evaluate("window.scrollBy(0, Math.random() * document.body.scrollHeight / 3)")
            page.wait_for_timeout(random.randint(500, 1500))
            
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(random.randint(300, 800))
            
    except Exception:
        pass


def create_stealth_context(
    browser: Browser,
    viewport: dict | None = None,
    user_agent: str | None = None,
) -> BrowserContext:
    viewport = viewport or {"width": 1280, "height": 900}
    user_agent = user_agent or (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    
    context = browser.new_context(
        viewport=viewport,
        user_agent=user_agent,
        locale="en-US",
        timezone_id="America/New_York",
    )
    
    return context


def apply_stealth(page: Page) -> None:
    if STEALTH_AVAILABLE and _stealth_sync:
        try:
            _stealth_sync(page)
        except Exception:
            pass
    
    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });
    """)


def create_stealth_browser(
    playwright: Playwright,
    headless: bool = True,
    use_stealth: bool = True,
) -> tuple[Browser, BrowserContext, Page]:
    browser = playwright.chromium.launch(
        headless=headless,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--disable-setuid-sandbox",
        ],
    )
    
    context = create_stealth_context(browser)
    page = context.new_page()
    
    if use_stealth:
        apply_stealth(page)
    
    return browser, context, page
