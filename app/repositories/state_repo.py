"""
Repository Implementations Module

Concrete implementations of repository interfaces.
Uses JSON file storage for persistence.
"""

from .interfaces import (
    IStateRepository, IStatsRepository, IHistoryRepository,
    URLRecord, NovelRecord, RetryRecord, ScrapeResult, ExtractionRecord
)
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json
from app.logger import logger


class StateRepository(IStateRepository):
    """JSON-based state repository implementation.
    
    Uses separate files for backward compatibility:
    - settings.json for user preferences
    - queue.json for URL/novel queue
    """
    
    SETTINGS_FILE = "settings.json"
    QUEUE_FILE = "queue.json"
    
    def __init__(self, base_path: Optional[Path] = None):
        self._base_path = base_path or Path(__file__).parent.parent.parent
        self._settings_file = self._base_path / self.SETTINGS_FILE
        self._queue_file = self._base_path / self.QUEUE_FILE
        self._settings: Dict[str, Any] = {}
        self._queue: Dict[str, Any] = {}
        self._load()
    
    def _load(self) -> None:
        """Load settings and queue from separate files."""
        if self._settings_file.exists():
            try:
                with open(self._settings_file, 'r', encoding='utf-8') as f:
                    self._settings = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Could not load settings file: {e}")
        
        if self._queue_file.exists():
            try:
                with open(self._queue_file, 'r', encoding='utf-8') as f:
                    self._queue = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Could not load queue file: {e}")
        
        if not self._settings:
            self._settings = self._default_settings()
        if not self._queue:
            self._queue = self._default_queue()
    
    def _default_settings(self) -> Dict[str, Any]:
        return {
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
    
    def _default_queue(self) -> Dict[str, Any]:
        return {
            "urls": [],
            "novels": [],
            "retry_normal": [],
            "retry_novel": []
        }
    
    def _save_settings(self) -> None:
        """Persist settings to settings.json."""
        with open(self._settings_file, 'w', encoding='utf-8') as f:
            json.dump(self._settings, f, indent=2)
    
    def _save_queue(self) -> None:
        """Persist queue to queue.json."""
        with open(self._queue_file, 'w', encoding='utf-8') as f:
            json.dump(self._queue, f, indent=2)
    
    def _save(self) -> None:
        """Persist both settings and queue."""
        self._save_settings()
        self._save_queue()
    
    def _should_auto_save(self) -> bool:
        return self._settings.get('auto_save_queue', True)
    
    def _get_timestamp(self) -> str:
        return datetime.now().isoformat()
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        return self._settings.get(key, default)
    
    def set_setting(self, key: str, value: Any) -> None:
        self._settings[key] = value
        self._save_settings()
    
    def get_all_settings(self) -> Dict[str, Any]:
        return self._settings.copy()
    
    def reset_settings(self) -> None:
        self._settings = self._default_settings()
        self._save_settings()
    
    def url_in_queue(self, url: str) -> bool:
        return any(e["url"] == url for e in self._queue.get("urls", []))
    
    def novel_in_queue(self, url: str) -> bool:
        return any(e["url"] == url for e in self._queue.get("novels", []))
    
    def add_url(self, url: str, url_type: str, tags: List[str]) -> bool:
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
        self._queue.setdefault("urls", []).append(entry)
        if self._should_auto_save():
            self._save()
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
        self._queue.setdefault("novels", []).append(entry)
        if self._should_auto_save():
            self._save()
        return True
    
    def update_url_status(self, url: str, status: str, error: Optional[str] = None) -> None:
        for entry in self._queue.get("urls", []):
            if entry["url"] == url:
                entry["status"] = status
                if error:
                    entry["error"] = error
                break
        if self._should_auto_save():
            self._save()
    
    def update_novel_status(self, url: str, status: str, error: Optional[str] = None) -> None:
        for entry in self._queue.get("novels", []):
            if entry["url"] == url:
                entry["status"] = status
                if error:
                    entry["error"] = error
                break
        if self._should_auto_save():
            self._save()
    
    def remove_url(self, url: str) -> None:
        self._queue["urls"] = [e for e in self._queue.get("urls", []) if e["url"] != url]
        if self._should_auto_save():
            self._save()
    
    def remove_novel(self, url: str) -> None:
        self._queue["novels"] = [e for e in self._queue.get("novels", []) if e["url"] != url]
        if self._should_auto_save():
            self._save()
    
    def get_pending_urls(self) -> List[URLRecord]:
        urls = [u for u in self._queue.get("urls", []) if u.get("status") == "pending"]
        return [
            URLRecord(
                url=u["url"],
                url_type=u.get("type", "normal"),
                status=u["status"],
                tags=u.get("tags", []),
                error=u.get("error"),
                added_at=u.get("added_at")
            )
            for u in urls
        ]
    
    def get_pending_novels(self) -> List[NovelRecord]:
        novels = [n for n in self._queue.get("novels", []) if n.get("status") == "pending"]
        return [
            NovelRecord(
                url=n["url"],
                start_chapter=n["start_chapter"],
                end_chapter=n["end_chapter"],
                status=n["status"],
                error=n.get("error")
            )
            for n in novels
        ]
    
    def add_to_retry_normal(self, url: str, error: str, tags: List[str]) -> None:
        entry = {
            "url": url,
            "error": error,
            "tags": tags or [],
            "failed_at": self._get_timestamp()
        }
        retry_list = self._queue.setdefault("retry_normal", [])
        if not any(e["url"] == url for e in retry_list):
            retry_list.append(entry)
            if self._should_auto_save():
                self._save()
    
    def add_to_retry_novel(self, url: str, chapter: int, error: str) -> None:
        entry = {
            "url": url,
            "chapter": chapter,
            "error": error,
            "failed_at": self._get_timestamp()
        }
        retry_list = self._queue.setdefault("retry_novel", [])
        if not any(e["url"] == url and e.get("chapter") == chapter for e in retry_list):
            retry_list.append(entry)
            if self._should_auto_save():
                self._save()
    
    def get_retry_normal(self) -> List[RetryRecord]:
        retry_list = self._queue.get("retry_normal", [])
        return [
            RetryRecord(
                url=e["url"],
                error=e["error"],
                chapter=None,
                tags=e.get("tags", []),
                failed_at=e.get("failed_at")
            )
            for e in retry_list
        ]
    
    def get_retry_novel(self) -> List[RetryRecord]:
        retry_list = self._queue.get("retry_novel", [])
        return [
            RetryRecord(
                url=e["url"],
                error=e["error"],
                chapter=e.get("chapter"),
                tags=[],
                failed_at=e.get("failed_at")
            )
            for e in retry_list
        ]
    
    def remove_from_retry_normal(self, url: str) -> None:
        self._queue["retry_normal"] = [
            e for e in self._queue.get("retry_normal", []) if e["url"] != url
        ]
        if self._should_auto_save():
            self._save()
    
    def remove_from_retry_novel(self, url: str, chapter: int) -> None:
        self._queue["retry_novel"] = [
            e for e in self._queue.get("retry_novel", [])
            if not (e["url"] == url and e.get("chapter") == chapter)
        ]
        if self._should_auto_save():
            self._save()
    
    def clear_completed(self) -> None:
        self._queue["urls"] = [e for e in self._queue.get("urls", []) if e.get("status") != "completed"]
        self._queue["novels"] = [e for e in self._queue.get("novels", []) if e.get("status") != "completed"]
        if self._should_auto_save():
            self._save()
    
    def save_queue(self) -> None:
        self._save()
    
    @property
    def queue(self) -> Dict[str, Any]:
        return self._queue


class StatsRepository(IStatsRepository):
    """JSON-based stats repository implementation."""
    
    def __init__(self, file_path: Path):
        self._file_path = file_path
        self._stats: Dict[str, Any] = {}
        self._load()
    
    def _load(self) -> None:
        """Load stats from file."""
        if self._file_path.exists():
            try:
                with open(self._file_path, 'r', encoding='utf-8') as f:
                    self._stats = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Could not load stats file: {e}")
        
        if not self._stats:
            self._stats = self._default_stats()
    
    def _default_stats(self) -> Dict[str, Any]:
        now = datetime.now().isoformat()
        return {
            "metadata": {"created_at": now, "last_updated": None, "version": "2.0.0"},
            "methods": {
                m: {"total_attempts": 0, "success": 0, "failed": 0, "total_time_ms": 0, "total_words": 0}
                for m in self.METHODS
            },
            "daily": {},
            "domains": {},
            "recent": [],
            "errors": []
        }
    
    def _save(self) -> None:
        """Persist stats to file."""
        self._stats["metadata"]["last_updated"] = datetime.now().isoformat()
        with open(self._file_path, 'w', encoding='utf-8') as f:
            json.dump(self._stats, f, indent=2, ensure_ascii=False)
    
    def record_scrape(self, result: ScrapeResult) -> None:
        from urllib.parse import urlparse
        
        domain = result.domain or urlparse(result.url).netloc
        today = datetime.now().strftime("%Y-%m-%d")
        method = result.method.replace("-", "_")
        
        if method not in self.METHODS:
            method = "simple_http"
        
        if method not in self._stats["methods"]:
            self._stats["methods"][method] = {"total_attempts": 0, "success": 0, "failed": 0, "total_time_ms": 0, "total_words": 0}
        
        self._stats["methods"][method]["total_attempts"] += 1
        self._stats["methods"][method]["total_time_ms"] += result.time_ms
        if result.success:
            self._stats["methods"][method]["success"] += 1
            self._stats["methods"][method]["total_words"] += result.word_count
        else:
            self._stats["methods"][method]["failed"] += 1
        
        if today not in self._stats["daily"]:
            self._stats["daily"][today] = {
                m: {"success": 0, "failed": 0, "time_ms": 0, "words": 0}
                for m in self.METHODS
            }
        
        self._stats["daily"][today][method]["time_ms"] += result.time_ms
        self._stats["daily"][today][method]["words"] += result.word_count
        if result.success:
            self._stats["daily"][today][method]["success"] += 1
        else:
            self._stats["daily"][today][method]["failed"] += 1
        
        if domain not in self._stats["domains"]:
            self._stats["domains"][domain] = {m: {"success": 0, "failed": 0} for m in self.METHODS}
        
        if result.success:
            self._stats["domains"][domain][method]["success"] += 1
        else:
            self._stats["domains"][domain][method]["failed"] += 1
        
        self._stats["recent"].insert(0, {
            "url": result.url,
            "method": method,
            "success": result.success,
            "time_ms": result.time_ms,
            "word_count": result.word_count,
            "domain": domain,
            "timestamp": result.timestamp or datetime.now().isoformat()
        })
        self._stats["recent"] = self._stats["recent"][:100]
        
        if not result.success:
            self._stats["errors"].insert(0, {
                "url": result.url,
                "method": method,
                "timestamp": datetime.now().isoformat()
            })
            self._stats["errors"] = self._stats["errors"][:50]
        
        self._save()
    
    def get_method_stats(self, days: Optional[int] = None) -> Dict[str, Any]:
        if days is None:
            result = {}
            for method, data in self._stats["methods"].items():
                attempts = data.get("total_attempts", 0)
                if attempts > 0:
                    result[method] = {
                        "success": data.get("success", 0),
                        "failed": data.get("failed", 0),
                        "total_attempts": attempts,
                        "avg_time_ms": data.get("total_time_ms", 0) // attempts,
                        "total_words": data.get("total_words", 0),
                        "success_rate": (data.get("success", 0) / attempts * 100),
                        "efficiency_score": self._calc_efficiency(data)
                    }
            return result
        
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        result = {m: {"success": 0, "failed": 0, "total_attempts": 0, "total_time_ms": 0, "total_words": 0} for m in self.METHODS}
        
        for date, day_data in self._stats["daily"].items():
            if date >= cutoff:
                for method in self.METHODS:
                    if method in day_data:
                        result[method]["success"] += day_data[method].get("success", 0)
                        result[method]["failed"] += day_data[method].get("failed", 0)
                        result[method]["total_time_ms"] += day_data[method].get("time_ms", 0)
                        result[method]["total_words"] += day_data[method].get("words", 0)
        
        final = {}
        for method, data in result.items():
            attempts = data["success"] + data["failed"]
            if attempts > 0:
                final[method] = {
                    "success": data["success"],
                    "failed": data["failed"],
                    "total_attempts": attempts,
                    "avg_time_ms": data["total_time_ms"] // attempts,
                    "total_words": data["total_words"],
                    "success_rate": (data["success"] / attempts * 100),
                    "efficiency_score": self._calc_efficiency(data)
                }
        return final
    
    def _calc_efficiency(self, data: Dict) -> float:
        attempts = data.get("total_attempts", 1)
        if attempts == 0:
            attempts = 1
        success_rate = (data.get("success", 0) / attempts * 100) if attempts > 0 else 0
        speed_score = max(0, 100 - (data.get("total_time_ms", 0) // attempts / 50))
        word_score = min((data.get("total_words", 0) / attempts / 50 * 50), 50)
        return round((success_rate * 0.4) + (speed_score * 0.3) + (word_score * 0.3), 1)
    
    def get_daily_activity(self, days: int = 7) -> Dict[str, Any]:
        result = {}
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            day_data = self._stats["daily"].get(date, {})
            total_success = sum(day_data.get(m, {}).get("success", 0) for m in self.METHODS)
            total_failed = sum(day_data.get(m, {}).get("failed", 0) for m in self.METHODS)
            total_words = sum(day_data.get(m, {}).get("words", 0) for m in self.METHODS)
            result[date] = {
                "urls": total_success + total_failed,
                "success": total_success,
                "failed": total_failed,
                "words": total_words,
                "by_method": day_data
            }
        return result
    
    def get_method_timeline(self, days: int = 30) -> Dict[str, Any]:
        result = {}
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            day_data = self._stats["daily"].get(date, {})
            result[date] = {
                method: day_data.get(method, {"success": 0, "failed": 0})
                for method in self.METHODS
            }
        return result
    
    def get_domain_stats(self, limit: int = 10) -> Dict[str, Any]:
        sorted_domains = sorted(
            self._stats["domains"].items(),
            key=lambda x: sum(m.get("success", 0) + m.get("failed", 0) for m in x[1].values()),
            reverse=True
        )[:limit]
        return dict(sorted_domains)
    
    def get_method_comparison(self, days: Optional[int] = None) -> Dict[str, Any]:
        method_stats = self.get_method_stats(days)
        comparison = {}
        for method in self.METHODS:
            stats = method_stats.get(method, {})
            attempts = stats.get("total_attempts", 0)
            if attempts > 0:
                success_rate = stats.get("success_rate", 0)
                speed_score = max(0, 100 - (stats.get("avg_time_ms", 5000) / 50))
                efficiency = stats.get("efficiency_score", 0)
                comparison[method] = {
                    "success_rate": round(success_rate, 1),
                    "speed_score": round(speed_score, 1),
                    "efficiency_score": round(efficiency, 1)
                }
        return comparison
    
    def get_summary_stats(self, days: Optional[int] = None) -> Dict[str, Any]:
        method_stats = self.get_method_stats(days)
        total_attempts = sum(m.get("total_attempts", 0) for m in method_stats.values())
        total_success = sum(m.get("success", 0) for m in method_stats.values())
        total_words = sum(m.get("total_words", 0) for m in method_stats.values())
        total_time = sum(
            self._stats["methods"].get(m, {}).get("total_time_ms", 0)
            for m in self.METHODS
        )
        return {
            "total_attempts": total_attempts,
            "total_success": total_success,
            "total_failed": total_attempts - total_success,
            "success_rate": (total_success / total_attempts * 100) if total_attempts > 0 else 0,
            "total_words": total_words,
            "avg_time_ms": total_time // total_attempts if total_attempts > 0 else 0,
            "method_count": len([m for m in method_stats if method_stats[m].get("total_attempts", 0) > 0])
        }
    
    def get_recent(self, limit: int = 20) -> List[ScrapeResult]:
        recent = self._stats.get("recent", [])[:limit]
        return [
            ScrapeResult(
                url=item["url"],
                method=item["method"],
                success=item["success"],
                time_ms=item["time_ms"],
                word_count=item["word_count"],
                domain=item.get("domain", ""),
                timestamp=item.get("timestamp")
            )
            for item in recent
        ]
    
    def get_error_analysis(self, days: Optional[int] = None) -> Dict[str, Any]:
        cutoff = None
        if days:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        errors_by_method = {m: 0 for m in self.METHODS}
        errors_by_domain = {}
        
        for error in self._stats.get("errors", []):
            if cutoff and error.get("timestamp", "") < cutoff:
                continue
            method = error.get("method", "unknown")
            domain = error.get("domain", "unknown")
            
            if method in errors_by_method:
                errors_by_method[method] += 1
            errors_by_domain[domain] = errors_by_domain.get(domain, 0) + 1
        
        return {
            "by_method": errors_by_method,
            "by_domain": dict(sorted(errors_by_domain.items(), key=lambda x: x[1], reverse=True)[:10])
        }
    
    @property
    def stats(self) -> Dict[str, Any]:
        return self._stats


class HistoryRepository(IHistoryRepository):
    """JSON-based history repository implementation."""
    
    def __init__(self, file_path: Path):
        self._file_path = file_path
        self._history: Dict[str, Any] = {}
        self._load()
    
    def _load(self) -> None:
        """Load history from file."""
        if self._file_path.exists():
            try:
                with open(self._file_path, 'r', encoding='utf-8') as f:
                    self._history = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Could not load history file: {e}")
        
        if not self._history:
            self._history = {"normal": {}, "novels": {}}
    
    def _save(self) -> None:
        """Persist history to file."""
        with open(self._file_path, 'w', encoding='utf-8') as f:
            json.dump(self._history, f, indent=2, ensure_ascii=False)
    
    def is_extracted(self, url: str) -> bool:
        return url in self._history.get("normal", {})
    
    def get_extracted_file(self, url: str) -> Optional[str]:
        entry = self._history.get("normal", {}).get(url)
        return entry.get("file") if entry else None
    
    def add_extraction(self, record: ExtractionRecord) -> None:
        self._history.setdefault("normal", {})[record.url] = {
            "file": str(record.file_path),
            "word_count": record.word_count,
            "scraper": record.method,
            "extracted_at": record.extracted_at or datetime.now().isoformat()
        }
        self._save()
    
    def is_novel_extracted(self, novel_url: str) -> bool:
        return novel_url in self._history.get("novels", {})
    
    def get_novel_chapters(self, novel_url: str) -> List[int]:
        entry = self._history.get("novels", {}).get(novel_url)
        return entry.get("chapters", []) if entry else []
    
    def set_novel_metadata(self, novel_url: str, folder: str, name: str,
                           genre: List[str], tags: List[str], author: str) -> None:
        existing = self._history.get("novels", {}).get(novel_url, {})
        self._history.setdefault("novels", {})[novel_url] = {
            "folder": folder,
            "name": name,
            "author": author,
            "genre": genre,
            "tags": tags,
            "chapters": existing.get("chapters", []),
            "total_words": existing.get("total_words", 0),
            "first_extracted": existing.get("first_extracted", datetime.now().isoformat()),
            "last_extracted": None
        }
        self._save()
    
    def add_novel_chapter(self, novel_url: str, chapter: int, word_count: int) -> None:
        entry = self._history.get("novels", {}).get(novel_url)
        if entry:
            if chapter not in entry.get("chapters", []):
                entry.setdefault("chapters", []).append(chapter)
            entry["total_words"] = entry.get("total_words", 0) + word_count
            entry["last_extracted"] = datetime.now().isoformat()
            self._save()
    
    def get_novel_metadata(self, novel_url: str) -> Optional[Dict[str, Any]]:
        return self._history.get("novels", {}).get(novel_url)
    
    def get_stats(self) -> Dict[str, Any]:
        normal_count = len(self._history.get("normal", {}))
        novels = self._history.get("novels", {})
        novel_count = len(novels)
        total_chapters = sum(len(n.get("chapters", [])) for n in novels.values())
        total_words = sum(n.get("total_words", 0) for n in novels.values())
        normal_words = sum(n.get("word_count", 0) for n in self._history.get("normal", {}).values())
        return {
            "normal_links": normal_count,
            "novels": novel_count,
            "total_chapters": total_chapters,
            "total_words": total_words + normal_words
        }
    
    @property
    def history(self) -> Dict[str, Any]:
        return self._history
