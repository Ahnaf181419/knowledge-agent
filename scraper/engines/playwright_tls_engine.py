from __future__ import annotations

import time

from scraper.core.page_extractor import PageExtractor
from scraper.engines._playwright_utils import (
    apply_human_interactions,
    apply_stealth,
    create_stealth_context,
    get_playwright_settings,
    is_challenge_page,
    load_session_cookies,
    save_session_cookies,
    wait_for_challenge,
)
from scraper.engines.base import BaseEngine


class PlaywrightTLSEngine(BaseEngine):
    def __init__(self, max_retries: int | None = None):
        if max_retries is None:
            settings = get_playwright_settings()
            self.max_retries = int(settings.get("max_retries", 3))
        else:
            self.max_retries = max_retries

    @property
    def name(self) -> str:
        return "playwright_tls"

    @property
    def priority(self) -> int:
        return 4

    def scrape(self, url: str) -> str | None:
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
                    "--no-sandbox",
                ],
            )

            context = create_stealth_context(
                browser,
                viewport={"width": 1366, "height": 768},
            )
            page = context.new_page()
            apply_stealth(page)

            load_session_cookies(context, url)

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

                    wait_for_challenge(page)

                    apply_human_interactions(page)

                    if is_challenge_page(page):
                        continue

                    content = PageExtractor.extract_content(page)
                    if content and len(content) > 500:
                        save_session_cookies(context, url)
                        return content

                except Exception:
                    if attempt < max_attempts - 1:
                        time.sleep(4)

            return None

        except Exception:
            return None
        finally:
            if browser:
                browser.close()
            if playwright:
                playwright.stop()


def scrape_with_playwright_tls(url: str) -> str | None:
    engine = PlaywrightTLSEngine()
    return engine.scrape(url)
