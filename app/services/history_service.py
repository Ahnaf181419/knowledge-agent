"""
History service - SQLite-backed extraction history.
"""

import json
from datetime import datetime
from pathlib import Path

from sqlmodel import select

from app.db import Extraction, NovelExtraction, get_session_context

HISTORY_FILE = Path(__file__).parent.parent.parent / "history.json"

DEFAULT_HISTORY: dict[str, dict] = {"normal": {}, "novels": {}}


class HistoryService:
    """SQLite-backed extraction history service."""

    def __init__(self):
        self._ensure_tables()
        self._migrate_from_json_if_needed()

    def _ensure_tables(self):
        from app.db import init_db

        init_db()

    def _migrate_from_json_if_needed(self):
        """Migrate from JSON to SQLite if JSON file exists."""
        if not HISTORY_FILE.exists():
            return

        with get_session_context() as session:
            existing = session.exec(select(Extraction)).first()
            if existing:
                return

            try:
                with open(HISTORY_FILE, encoding="utf-8") as f:
                    data = json.load(f)

                for url, entry in data.get("normal", {}).items():
                    ext = Extraction(
                        url=url,
                        file_path=entry.get("file", ""),
                        word_count=entry.get("word_count", 0),
                        scraper=entry.get("scraper", "unknown"),
                        extracted_at=datetime.fromisoformat(
                            entry.get("extracted_at", datetime.now().isoformat())
                        ),
                    )
                    session.add(ext)

                for url, entry in data.get("novels", {}).items():
                    nov = NovelExtraction(
                        url=url,
                        folder=entry.get("folder", ""),
                        name=entry.get("name", ""),
                        author=entry.get("author", "Unknown"),
                        total_words=entry.get("total_words", 0),
                    )
                    session.add(nov)

                session.commit()
            except (json.JSONDecodeError, OSError):
                pass

    def is_extracted(self, url: str) -> bool:
        with get_session_context() as session:
            stmt = select(Extraction).where(Extraction.url == url)
            return session.exec(stmt).first() is not None

    def get_extracted_file(self, url: str) -> str | None:
        with get_session_context() as session:
            stmt = select(Extraction).where(Extraction.url == url)
            ext = session.exec(stmt).first()
            return ext.file_path if ext else None

    def add_normal(
        self,
        url: str,
        file_path: str,
        word_count: int,
        scraper: str,
        tags: list[str] | None = None,
        content_type: str = "article",
    ):
        with get_session_context() as session:
            stmt = select(Extraction).where(Extraction.url == url)
            existing = session.exec(stmt).first()

            if existing:
                existing.file_path = file_path
                existing.word_count = word_count
                existing.scraper = scraper
                existing.content_type = content_type
                existing.extracted_at = datetime.now()
            else:
                ext = Extraction(
                    url=url,
                    file_path=file_path,
                    word_count=word_count,
                    scraper=scraper,
                    content_type=content_type,
                    extracted_at=datetime.now(),
                )
                session.add(ext)
            session.commit()

    def is_novel_extracted(self, novel_url: str) -> bool:
        with get_session_context() as session:
            stmt = select(NovelExtraction).where(NovelExtraction.url == novel_url)
            return session.exec(stmt).first() is not None

    def get_novel_chapters(self, novel_url: str) -> list[int]:
        return []

    def set_novel_metadata(
        self,
        novel_url: str,
        folder: str,
        name: str,
        genre: list[str],
        tags: list[str],
        author: str = "Unknown",
    ):
        with get_session_context() as session:
            stmt = select(NovelExtraction).where(NovelExtraction.url == novel_url)
            nov = session.exec(stmt).first()

            if nov:
                nov.folder = folder
                nov.name = name
                nov.author = author
            else:
                nov = NovelExtraction(
                    url=novel_url,
                    folder=folder,
                    name=name,
                    author=author,
                    total_words=0,
                )
                session.add(nov)
            session.commit()

    def add_novel_chapter(self, novel_url: str, chapter: int, word_count: int):
        pass

    def get_novel_metadata(self, novel_url: str) -> dict | None:
        with get_session_context() as session:
            stmt = select(NovelExtraction).where(NovelExtraction.url == novel_url)
            nov = session.exec(stmt).first()
            if nov:
                return {
                    "folder": nov.folder,
                    "name": nov.name,
                    "author": nov.author,
                    "total_words": nov.total_words,
                }
            return None

    def get_stats(self) -> dict:
        with get_session_context() as session:
            normal_count = len(session.exec(select(Extraction)).all())
            novels = session.exec(select(NovelExtraction)).all()
            novel_count = len(novels)
            total_words = sum(n.total_words for n in novels)
            normal_words = sum(e.word_count for e in session.exec(select(Extraction)).all())

            return {
                "normal_links": normal_count,
                "novels": novel_count,
                "total_chapters": 0,
                "total_words": total_words + normal_words,
            }


history_service = HistoryService()
