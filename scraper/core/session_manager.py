"""
Session Manager Module

Cookie/session management for authenticated scraping.
Handles saving and loading browser sessions.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable

from app.logger import logger

DEFAULT_SESSIONS_DIR = Path(__file__).parent.parent.parent / "sessions"


class SessionManager:
    """Cookie/session management for authenticated scraping."""

    def __init__(self, sessions_dir: Path | None = None):
        self.sessions_dir = sessions_dir or DEFAULT_SESSIONS_DIR
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def _get_session_file(self, slug: str) -> Path:
        """Get path to session file for a given slug."""
        return self.sessions_dir / f"{slug}_cookies.json"

    def load_session(self, context: Any, slug: str) -> bool:
        """
        Load cookies from file into browser context.

        Args:
            context: Playwright browser context
            slug: Unique identifier for the session

        Returns:
            True if session was loaded successfully
        """
        session_file = self._get_session_file(slug)

        if not session_file.exists():
            return False

        try:
            data = json.loads(session_file.read_text(encoding="utf-8"))
            expires = data.get("expires_at", "")

            if expires and datetime.now() < datetime.fromisoformat(expires):
                context.add_cookies(data.get("cookies", []))
                logger.info(f"Loaded session cookies for {slug}")
                return True
            else:
                logger.debug(f"Session expired for {slug}")
                return False

        except Exception as e:
            logger.warning(f"Could not load session for {slug}: {e}")
            return False

    def save_session(self, context: Any, slug: str) -> None:
        """
        Save cookies from browser context to file.

        Args:
            context: Playwright browser context
            slug: Unique identifier for the session
        """
        session_file = self._get_session_file(slug)

        try:
            cookies = context.cookies()
            data = {
                "saved_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(days=7)).isoformat(),
                "cookies": cookies,
            }
            session_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
            logger.info(f"Saved session cookies for {slug}")

        except Exception as e:
            logger.warning(f"Could not save session for {slug}: {e}")

    @staticmethod
    def wait_delay(min_seconds: int, max_seconds: int) -> None:
        """
        Wait a random delay between requests.

        Args:
            min_seconds: Minimum delay in seconds
            max_seconds: Maximum delay in seconds
        """
        delay = random.randint(min_seconds, max_seconds)
        logger.debug(f"Waiting {delay} seconds before next request...")
        import time
        time.sleep(delay)

    def delete_session(self, slug: str) -> bool:
        """
        Delete session file.

        Args:
            slug: Unique identifier for the session

        Returns:
            True if deleted, False if not found
        """
        session_file = self._get_session_file(slug)
        if session_file.exists():
            session_file.unlink()
            logger.info(f"Deleted session for {slug}")
            return True
        return False


session_manager = SessionManager()
