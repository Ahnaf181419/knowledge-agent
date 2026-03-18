import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).parent.parent
SETTINGS_FILE = CONFIG_DIR / "settings.json"
QUEUE_FILE = CONFIG_DIR / "queue.json"

DEFAULT_SETTINGS: dict[str, Any] = {
    "theme": "dark",
    "export_format": "md",
    "output_folder": "output",
    "concurrent_jobs": 2,
    "retry_count": 2,
    "novel_delay_min": 90,
    "novel_delay_max": 120,
    "auto_save_queue": True,
    "respect_robots_txt": False,
    "notifications_enabled": True,
    "notify_on_success": True,
    "notify_on_failure": True,
    "notify_on_complete": True,
    "scheduler_enabled": False,
    "auto_optimize": True,
    "optimization_threshold": 10,
    "success_promotion_threshold": 5,
    "failure_demotion_threshold": 3,
}

DEFAULT_QUEUE: dict[str, list] = {"urls": [], "novels": [], "retry_normal": [], "retry_novel": []}


class State:
    def __init__(self) -> None:
        self.settings = self._load_settings()
        self.queue = self._load_queue()

    def _load_settings(self) -> dict[str, Any]:
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, encoding="utf-8") as f:
                    return {**DEFAULT_SETTINGS, **json.load(f)}
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Failed to load settings.json: {e}")
        return DEFAULT_SETTINGS.copy()

    def _load_queue(self) -> dict[str, list]:
        if QUEUE_FILE.exists():
            try:
                with open(QUEUE_FILE, encoding="utf-8") as f:
                    return {**DEFAULT_QUEUE, **json.load(f)}
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Failed to load queue.json: {e}")
        return DEFAULT_QUEUE.copy()

    def save_settings(self) -> None:
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=2)
        except OSError as e:
            logger.error(f"Failed to save settings.json: {e}")
            raise

    def save_queue(self) -> None:
        try:
            with open(QUEUE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.queue, f, indent=2)
        except OSError as e:
            logger.error(f"Failed to save queue.json: {e}")
            raise

    def reload(self) -> None:
        """Reload settings and queue from disk."""
        self.settings = self._load_settings()
        self.queue = self._load_queue()

    def _should_auto_save(self) -> bool:
        return bool(self.settings.get("auto_save_queue", True))

    def _save_if_auto(self) -> bool:
        """Save queue if auto-save is enabled.

        Returns:
            True if saved, False if skipped
        """
        if self._should_auto_save():
            self.save_queue()
            return True
        return False

    def get_setting(self, key: str, default: Any = None) -> Any:
        return self.settings.get(key, default)

    def set_setting(self, key: str, value: Any) -> None:
        self.settings[key] = value
        self.save_settings()

    # ===== URL Management =====

    def url_in_queue(self, url: str) -> bool:
        return any(e["url"] == url for e in self.queue.get("urls", []))

    def novel_in_queue(self, url: str) -> bool:
        return any(e["url"] == url for e in self.queue.get("novels", []))

    def add_url(self, url: str, url_type: str = "normal", tags: list[str] | None = None) -> bool:
        if self.url_in_queue(url):
            return False
        entry = {
            "url": url,
            "type": url_type,
            "tags": tags or [],
            "status": "pending",
            "error": None,
            "added_at": self._get_timestamp(),
        }
        self.queue["urls"].append(entry)
        self._save_if_auto()
        return True

    def add_novel(self, url: str, start_chapter: int, end_chapter: int, tags: list[str] | None = None) -> bool:
        if self.novel_in_queue(url):
            return False
        entry = {
            "url": url,
            "start_chapter": start_chapter,
            "end_chapter": end_chapter,
            "tags": tags or [],
            "status": "pending",
            "added_at": self._get_timestamp(),
        }
        self.queue["novels"].append(entry)
        self._save_if_auto()
        return True

    def update_url_status(self, url: str, status: str, error: str | None = None) -> None:
        for entry in self.queue["urls"]:
            if entry["url"] == url:
                entry["status"] = status
                if error:
                    entry["error"] = error
                break
        self._save_if_auto()

    def update_novel_status(self, url: str, status: str, error: str | None = None) -> None:
        for entry in self.queue["novels"]:
            if entry["url"] == url:
                entry["status"] = status
                if error:
                    entry["error"] = error
                break
        self._save_if_auto()

    def remove_url(self, url: str) -> None:
        self.queue["urls"] = [e for e in self.queue["urls"] if e["url"] != url]
        self._save_if_auto()

    def remove_novel(self, url: str) -> None:
        self.queue["novels"] = [e for e in self.queue["novels"] if e["url"] != url]
        self._save_if_auto()

    def clear_completed(self) -> None:
        self.queue["urls"] = [e for e in self.queue["urls"] if e["status"] != "completed"]
        self.queue["novels"] = [e for e in self.queue["novels"] if e["status"] != "completed"]
        self._save_if_auto()

    # ===== Retry Queue Management =====

    def add_to_retry_normal(self, url: str, error: str, tags: list[str] | None = None) -> None:
        entry = {"url": url, "error": error, "tags": tags or [], "failed_at": self._get_timestamp()}
        if not any(e["url"] == url for e in self.queue["retry_normal"]):
            self.queue["retry_normal"].append(entry)
            self._save_if_auto()

    def add_to_retry_novel(self, url: str, chapter: int, error: str) -> None:
        entry = {"url": url, "chapter": chapter, "error": error, "failed_at": self._get_timestamp()}
        if not any(e["url"] == url and e["chapter"] == chapter for e in self.queue["retry_novel"]):
            self.queue["retry_novel"].append(entry)
            self._save_if_auto()

    def remove_from_retry_normal(self, url: str) -> None:
        self.queue["retry_normal"] = [e for e in self.queue["retry_normal"] if e["url"] != url]
        self._save_if_auto()

    def remove_from_retry_novel(self, url: str, chapter: int) -> None:
        self.queue["retry_novel"] = [
            e
            for e in self.queue["retry_novel"]
            if not (e["url"] == url and e.get("chapter") == chapter)
        ]
        self._save_if_auto()

    def get_retry_normal(self) -> list[dict]:
        return self.queue.get("retry_normal", [])

    def get_retry_novel(self) -> list[dict]:
        return self.queue.get("retry_novel", [])

    @staticmethod
    def _get_timestamp() -> str:
        from datetime import datetime

        return datetime.now().isoformat()

    def get_queue_stats(self) -> dict:
        """Get statistics about the queue state."""
        return {
            "total_urls": len(self.queue.get("urls", [])),
            "pending": len([e for e in self.queue.get("urls", []) if e.get("status") == "pending"]),
            "completed": len(
                [e for e in self.queue.get("urls", []) if e.get("status") == "completed"]
            ),
            "failed": len([e for e in self.queue.get("urls", []) if e.get("status") == "failed"]),
            "total_novels": len(self.queue.get("novels", [])),
            "retry_normal": len(self.queue.get("retry_normal", [])),
            "retry_novel": len(self.queue.get("retry_novel", [])),
        }


state = State()
