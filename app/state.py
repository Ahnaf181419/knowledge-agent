import json
import os
from pathlib import Path

CONFIG_DIR = Path(__file__).parent.parent
SETTINGS_FILE = CONFIG_DIR / "settings.json"
QUEUE_FILE = CONFIG_DIR / "queue.json"

DEFAULT_SETTINGS = {
    "theme": "dark",
    "export_format": "md",
    "output_folder": "output",
    "concurrent_jobs": 3,
    "retry_count": 2,
    "novel_delay_min": 90,
    "novel_delay_max": 120,
    "auto_save_queue": True,
    "respect_robots_txt": True
}

DEFAULT_QUEUE = {
    "urls": [],
    "novels": [],
    "retry_normal": [],
    "retry_novel": []
}


class State:
    def __init__(self):
        self.settings = self._load_settings()
        self.queue = self._load_queue()

    def _load_settings(self) -> dict:
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return {**DEFAULT_SETTINGS, **json.load(f)}
        return DEFAULT_SETTINGS.copy()

    def _load_queue(self) -> dict:
        if QUEUE_FILE.exists():
            with open(QUEUE_FILE, 'r', encoding='utf-8') as f:
                return {**DEFAULT_QUEUE, **json.load(f)}
        return DEFAULT_QUEUE.copy()

    def save_settings(self):
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, indent=2)

    def save_queue(self):
        with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.queue, f, indent=2)

    def _should_auto_save(self) -> bool:
        return self.settings.get('auto_save_queue', True)

    def _save_if_auto(self):
        if self._should_auto_save():
            self.save_queue()

    def get_setting(self, key: str, default=None):
        return self.settings.get(key, default)

    def set_setting(self, key: str, value):
        self.settings[key] = value
        self.save_settings()

    # ===== URL Management =====

    def url_in_queue(self, url: str) -> bool:
        return any(e["url"] == url for e in self.queue.get("urls", []))

    def novel_in_queue(self, url: str) -> bool:
        return any(e["url"] == url for e in self.queue.get("novels", []))

    def add_url(self, url: str, url_type: str = "normal", tags: list | None = None) -> bool:
        if self.url_in_queue(url):
            return False
        entry = {
            "url": url,
            "type": url_type,
            "tags": tags or [],
            "status": "pending",
            "error": None,
            "added_at": self._get_timestamp()
        }
        self.queue["urls"].append(entry)
        self._save_if_auto()
        return True

    def add_novel(self, url: str, start_chapter: int, end_chapter: int) -> bool:
        if self.novel_in_queue(url):
            return False
        entry = {
            "url": url,
            "start_chapter": start_chapter,
            "end_chapter": end_chapter,
            "status": "pending",
            "added_at": self._get_timestamp()
        }
        self.queue["novels"].append(entry)
        self._save_if_auto()
        return True

    def update_url_status(self, url: str, status: str, error: str | None = None):
        for entry in self.queue["urls"]:
            if entry["url"] == url:
                entry["status"] = status
                if error:
                    entry["error"] = error
                break
        self._save_if_auto()

    def update_novel_status(self, url: str, status: str, error: str | None = None):
        for entry in self.queue["novels"]:
            if entry["url"] == url:
                entry["status"] = status
                if error:
                    entry["error"] = error
                break
        self._save_if_auto()

    def remove_url(self, url: str):
        self.queue["urls"] = [e for e in self.queue["urls"] if e["url"] != url]
        self._save_if_auto()

    def remove_novel(self, url: str):
        self.queue["novels"] = [e for e in self.queue["novels"] if e["url"] != url]
        self._save_if_auto()

    def clear_completed(self):
        self.queue["urls"] = [e for e in self.queue["urls"] if e["status"] != "completed"]
        self.queue["novels"] = [e for e in self.queue["novels"] if e["status"] != "completed"]
        self._save_if_auto()

    # ===== Retry Queue Management =====

    def add_to_retry_normal(self, url: str, error: str, tags: list | None = None):
        entry = {
            "url": url,
            "error": error,
            "tags": tags or [],
            "failed_at": self._get_timestamp()
        }
        if not any(e["url"] == url for e in self.queue["retry_normal"]):
            self.queue["retry_normal"].append(entry)
            self._save_if_auto()

    def add_to_retry_novel(self, url: str, chapter: int, error: str):
        entry = {
            "url": url,
            "chapter": chapter,
            "error": error,
            "failed_at": self._get_timestamp()
        }
        if not any(e["url"] == url and e["chapter"] == chapter for e in self.queue["retry_novel"]):
            self.queue["retry_novel"].append(entry)
            self._save_if_auto()

    def remove_from_retry_normal(self, url: str):
        self.queue["retry_normal"] = [e for e in self.queue["retry_normal"] if e["url"] != url]
        self._save_if_auto()

    def remove_from_retry_novel(self, url: str, chapter: int):
        self.queue["retry_novel"] = [e for e in self.queue["retry_novel"] 
                                     if not (e["url"] == url and e.get("chapter") == chapter)]
        self._save_if_auto()

    def get_retry_normal(self) -> list:
        return self.queue.get("retry_normal", [])

    def get_retry_novel(self) -> list:
        return self.queue.get("retry_novel", [])

    @staticmethod
    def _get_timestamp():
        from datetime import datetime
        return datetime.now().isoformat()


state = State()
