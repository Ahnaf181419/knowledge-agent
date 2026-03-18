from __future__ import annotations

import time
from typing import Any

from scraper.core.page_extractor import PageExtractor
from scraper.engines._playwright_utils import (
    apply_human_interactions,
    apply_stealth,
    create_stealth_context,
    get_playwright_settings,
    is_challenge_page,
    save_session_cookies,
)
from scraper.engines.base import BaseEngine


class HybridEngine(BaseEngine):
    def __init__(self, max_retries: int | None = None):
        if max_retries is None:
            settings = get_playwright_settings()
            self.max_retries = int(settings.get("max_retries", 3))
        else:
            self.max_retries = max_retries

    @property
    def name(self) -> str:
        return "hybrid"

    @property
    def priority(self) -> int:
        return 1

    def scrape(self, url: str) -> str | None:
        cloudscraper_cookies = self._get_cookies_with_cloudscraper(url)
        if not cloudscraper_cookies:
            return None

        return self._scrape_with_playwright_cookies(url, cloudscraper_cookies)

    def _get_cookies_with_cloudscraper(self, url: str) -> list[dict[str, Any]] | None:
        try:
            import cloudscraper

            scraper = cloudscraper.create_scraper(
                browser={
                    "browser": "chrome",
                    "platform": "windows",
                    "desktop": True,
                }
            )

            response = scraper.get(url, timeout=30)
            if response.status_code != 200:
                return None

            cookies = scraper.cookies.get_dict()
            if not cookies:
                return None

            cloudflare_cookies = []
            for name, value in cookies.items():
                cloudflare_cookies.append({
                    "name": name,
                    "value": value,
                    "domain": self._extract_domain(url),
                    "path": "/",
                })

            return cloudflare_cookies

        except Exception:
            return None

    def _extract_domain(self, url: str) -> str:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc

    def _scrape_with_playwright_cookies(
        self, url: str, cookies: list[dict[str, Any]]
    ) -> str | None:
        browser = None
        playwright = None

        try:
            from playwright.sync_api import sync_playwright

            settings = get_playwright_settings()
            playwright = sync_playwright().start()
            browser = playwright.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                ],
            )

            context = create_stealth_context(browser)
            context.add_cookies(cookies)

            page = context.new_page()
            apply_stealth(page)

            max_attempts = self.max_retries
            for attempt in range(max_attempts):
                try:
                    timeout_ms = int(settings.get("timeout", 45000))
                    wait_time = int(settings.get("wait_after_load", 3000))

                    page.goto(
                        url,
                        wait_until="domcontentloaded",
                        timeout=timeout_ms
                    )
                    page.wait_for_timeout(wait_time)

                    apply_human_interactions(page)

                    if is_challenge_page(page):
                        continue

                    content = PageExtractor.extract_content(page)
                    if content and len(content) > 500:
                        save_session_cookies(context, url)
                        return content

                except Exception:
                    if attempt < max_attempts - 1:
                        time.sleep(3)

            return None

        except Exception:
            return None
        finally:
            if browser:
                browser.close()
            if playwright:
                playwright.stop()


def scrape_with_hybrid(url: str) -> str | None:
    engine = HybridEngine()
    return engine.scrape(url)
