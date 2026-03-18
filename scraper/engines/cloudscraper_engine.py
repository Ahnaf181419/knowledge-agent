from __future__ import annotations

import re
from typing import Any

from scraper.engines.base import BaseEngine


class CloudScraperEngine(BaseEngine):
    def __init__(self):
        pass

    @property
    def name(self) -> str:
        return "cloudscraper"

    @property
    def priority(self) -> int:
        return 5

    def scrape(self, url: str) -> str | None:
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

            if response.status_code == 200:
                html_content = response.text
                text_content = self._extract_text_from_html(html_content)
                if text_content and len(text_content) > 100:
                    return text_content
                return html_content
            elif response.status_code == 403:
                scraper = cloudscraper.create_scraper(
                    browser={
                        "browser": "chrome",
                        "platform": "windows",
                        "desktop": True,
                    },
                    interpreter="native",
                )
                response = scraper.get(url, timeout=30)
                if response.status_code == 200:
                    html_content = response.text
                    text_content = self._extract_text_from_html(html_content)
                    if text_content and len(text_content) > 100:
                        return text_content
                    return html_content

            return None

        except Exception as e:
            return None

    def _extract_text_from_html(self, html: str) -> str | None:
        try:
            from bs4 import BeautifulSoup
            import re

            soup = BeautifulSoup(html, "html.parser")

            for script in soup(["script", "style", "noscript"]):
                script.decompose()

            common_selectors = [
                "div.chapter-content",
                "div.content",
                "div[data-testid='chapter-content']",
                "div[class*='chapter']",
                "article",
                "div[class*='content']",
                "div[class*='novel']",
                "div#content",
                "div.container",
                "main",
                "div[class*='reader']",
            ]

            for selector in common_selectors:
                content_div = soup.select_one(selector)
                if content_div:
                    text = content_div.get_text(separator="\n", strip=True)
                    lines = [line.strip() for line in text.split("\n") if line.strip() and len(line.strip()) > 30]
                    if len(lines) > 5:
                        return "\n\n".join(lines)

            body = soup.find("body")
            if body:
                text = body.get_text(separator="\n", strip=True)
                lines = [line.strip() for line in text.split("\n") if line.strip() and len(line.strip()) > 30]
                if len(lines) > 10:
                    return "\n\n".join(lines[:100])

            return None

        except Exception:
            return None


def scrape_with_cloudscraper(url: str) -> str | None:
    engine = CloudScraperEngine()
    return engine.scrape(url)
