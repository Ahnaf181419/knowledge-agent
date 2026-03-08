"""
Scraping Statistics Tracker Module

Persistent analytics data source for the Analytics tab.
Tracks:
- Method performance (simple_http, playwright, playwright_alt, webscrapingapi)
- Daily activity breakdown by method
- Domain-level statistics
- Recent activity (last 100 items)
- Error tracking

Data is persisted to scraping_stats.json in the project root.
This file serves as the PRIMARY data source for statistical analysis.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

STATS_FILE = Path(__file__).parent.parent / "scraping_stats.json"

METHODS = ["simple_http", "playwright", "playwright_alt", "webscrapingapi"]

DEFAULT_STATS = {
    "metadata": {
        "created_at": None,
        "last_updated": None,
        "version": "1.0.0"
    },
    "methods": {
        "simple_http": {"total_attempts": 0, "success": 0, "failed": 0, "total_time_ms": 0, "total_words": 0},
        "playwright": {"total_attempts": 0, "success": 0, "failed": 0, "total_time_ms": 0, "total_words": 0},
        "playwright_alt": {"total_attempts": 0, "success": 0, "failed": 0, "total_time_ms": 0, "total_words": 0},
        "webscrapingapi": {"total_attempts": 0, "success": 0, "failed": 0, "total_time_ms": 0, "total_words": 0}
    },
    "daily": {},
    "domains": {},
    "recent": [],
    "errors": []
}


class ScrapingStats:
    """Manages scraping statistics persistence and retrieval."""
    
    def __init__(self):
        self.stats = self._load_stats()
        self._ensure_methods_exist()
    
    def _load_stats(self) -> dict:
        """Load stats from JSON file or return defaults."""
        if STATS_FILE.exists():
            try:
                with open(STATS_FILE, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    result = DEFAULT_STATS.copy()
                    for key in result:
                        if key in loaded:
                            if isinstance(result[key], dict):
                                result[key] = {**result[key], **loaded[key]}
                            else:
                                result[key] = loaded[key]
                    return result
            except Exception as e:
                print(f"Error loading stats: {e}")
        
        result = DEFAULT_STATS.copy()
        result["metadata"]["created_at"] = datetime.now().isoformat()
        return result
    
    def _ensure_methods_exist(self):
        """Ensure all methods exist in stats."""
        for method in METHODS:
            if method not in self.stats["methods"]:
                self.stats["methods"][method] = {"total_attempts": 0, "success": 0, "failed": 0, "total_time_ms": 0, "total_words": 0}
    
    def save(self):
        """Persist stats to JSON file."""
        self.stats["metadata"]["last_updated"] = datetime.now().isoformat()
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)
    
    def record_scrape(self, url: str, method: str, success: bool, 
                      time_ms: int, word_count: int = 0):
        """
        Record a scraping result.
        
        Args:
            url: The scraped URL
            method: Scraping method (simple_http, playwright, playwright_alt, webscrapingapi)
            success: Whether the scrape succeeded
            time_ms: Time taken in milliseconds
            word_count: Number of words extracted
        """
        from urllib.parse import urlparse
        
        domain = urlparse(url).netloc
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Normalize method name
        method_key = method.replace("-", "_")
        if method_key not in METHODS:
            method_key = "simple_http"
        
        # Update method stats
        self.stats["methods"][method_key]["total_attempts"] += 1
        self.stats["methods"][method_key]["total_time_ms"] += time_ms
        if success:
            self.stats["methods"][method_key]["success"] += 1
            self.stats["methods"][method_key]["total_words"] += word_count
        else:
            self.stats["methods"][method_key]["failed"] += 1
        
        # Update daily stats
        if today not in self.stats["daily"]:
            self.stats["daily"][today] = {m: {"success": 0, "failed": 0, "time_ms": 0, "words": 0} for m in METHODS}
        
        self.stats["daily"][today][method_key]["time_ms"] += time_ms
        self.stats["daily"][today][method_key]["words"] += word_count
        if success:
            self.stats["daily"][today][method_key]["success"] += 1
        else:
            self.stats["daily"][today][method_key]["failed"] += 1
        
        # Update domain stats
        if domain not in self.stats["domains"]:
            self.stats["domains"][domain] = {m: {"success": 0, "failed": 0} for m in METHODS}
        
        if success:
            self.stats["domains"][domain][method_key]["success"] += 1
        else:
            self.stats["domains"][domain][method_key]["failed"] += 1
        
        # Add to recent items (keep last 100)
        self.stats["recent"].insert(0, {
            "url": url,
            "method": method_key,
            "success": success,
            "time_ms": time_ms,
            "word_count": word_count,
            "domain": domain,
            "timestamp": datetime.now().isoformat()
        })
        self.stats["recent"] = self.stats["recent"][:100]
        
        # Track errors
        if not success:
            self.stats["errors"].insert(0, {
                "url": url,
                "method": method_key,
                "timestamp": datetime.now().isoformat()
            })
            self.stats["errors"] = self.stats["errors"][:50]
        
        self.save()
    
    def get_method_stats(self, days: int | None = None) -> dict:
        """Get aggregated statistics by method for a time period."""
        if days is None:
            # All time
            result = {}
            for method, data in self.stats["methods"].items():
                attempts = data.get("total_attempts", 0)
                if attempts > 0:
                    result[method] = {
                        "success": data.get("success", 0),
                        "failed": data.get("failed", 0),
                        "total_attempts": attempts,
                        "avg_time_ms": data.get("total_time_ms", 0) // attempts,
                        "total_words": data.get("total_words", 0),
                        "success_rate": (data.get("success", 0) / attempts * 100),
                        "efficiency_score": self._calc_efficiency({
                            "success_rate": (data.get("success", 0) / attempts * 100),
                            "avg_time_ms": data.get("total_time_ms", 0) // attempts,
                            "avg_words": data.get("total_words", 0) / attempts if attempts > 0 else 0
                        })
                    }
            return result
        
        # Filter by days
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        result = {m: {"success": 0, "failed": 0, "total_attempts": 0, "total_time_ms": 0, "total_words": 0} for m in METHODS}
        
        for date, day_data in self.stats["daily"].items():
            if date >= cutoff:
                for method in METHODS:
                    if method in day_data:
                        result[method]["success"] += day_data[method].get("success", 0)
                        result[method]["failed"] += day_data[method].get("failed", 0)
                        result[method]["total_time_ms"] += day_data[method].get("time_ms", 0)
                        result[method]["total_words"] += day_data[method].get("words", 0)
        
        # Calculate derived metrics
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
                    "efficiency_score": self._calc_efficiency({
                        "success_rate": (data["success"] / attempts * 100),
                        "avg_time_ms": data["total_time_ms"] // attempts,
                        "avg_words": data["total_words"] / attempts
                    })
                }
        
        return final
    
    def _calc_efficiency(self, stats: dict) -> float:
        """Calculate efficiency score (0-100)."""
        success_rate = stats.get("success_rate", 0)
        # Speed score: faster = higher (5000ms = 0, 500ms = 90)
        speed_score = max(0, 100 - (stats.get("avg_time_ms", 5000) / 50))
        # Word score: more words = higher (avg 50 words = 50)
        word_score = min(stats.get("avg_words", 0) / 50 * 50, 50)
        
        return round((success_rate * 0.4) + (speed_score * 0.3) + (word_score * 0.3), 1)
    
    def get_daily_activity(self, days: int = 7) -> dict:
        """Get daily activity for the last N days."""
        result = {}
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            day_data = self.stats["daily"].get(date, {})
            total_success = sum(day_data.get(m, {}).get("success", 0) for m in METHODS)
            total_failed = sum(day_data.get(m, {}).get("failed", 0) for m in METHODS)
            total_words = sum(day_data.get(m, {}).get("words", 0) for m in METHODS)
            result[date] = {
                "urls": total_success + total_failed,
                "success": total_success,
                "failed": total_failed,
                "words": total_words,
                "by_method": day_data
            }
        return result
    
    def get_method_timeline(self, days: int = 30) -> dict:
        """Get method usage broken down by day."""
        result = {}
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            day_data = self.stats["daily"].get(date, {})
            result[date] = {
                method: day_data.get(method, {"success": 0, "failed": 0})
                for method in METHODS
            }
        return result
    
    def get_domain_stats(self, limit: int = 10) -> dict:
        """Get domain-level statistics."""
        sorted_domains = sorted(
            self.stats["domains"].items(),
            key=lambda x: sum(m.get("success", 0) + m.get("failed", 0) for m in x[1].values()),
            reverse=True
        )[:limit]
        return dict(sorted_domains)
    
    def get_domain_method_breakdown(self, days: int | None = None) -> dict:
        """Get which methods work best for which domains."""
        return self.get_domain_stats(20)
    
    def get_recent(self, limit: int = 20) -> list:
        """Get recent scraping results."""
        return self.stats["recent"][:limit]
    
    def get_errors(self, limit: int = 20) -> list:
        """Get recent errors."""
        return self.stats["errors"][:limit]
    
    def get_error_analysis(self, days: int | None = None) -> dict:
        """Analyze errors by method and domain."""
        cutoff = None
        if days:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        errors_by_method = {m: 0 for m in METHODS}
        errors_by_domain = {}
        
        for error in self.stats["errors"]:
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
    
    def get_summary_stats(self, days: int | None = None) -> dict:
        """Get summary statistics for overview."""
        method_stats = self.get_method_stats(days)
        
        total_attempts = sum(m.get("total_attempts", 0) for m in method_stats.values())
        total_success = sum(m.get("success", 0) for m in method_stats.values())
        total_words = sum(m.get("total_words", 0) for m in method_stats.values())
        total_time = sum(
            self.stats["methods"][m].get("total_time_ms", 0) 
            for m in METHODS
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
    
    def get_method_comparison(self, days: int | None = None) -> dict:
        """Get comparison data for radar chart."""
        method_stats = self.get_method_stats(days)
        
        comparison = {}
        for method in METHODS:
            stats = method_stats.get(method, {})
            attempts = stats.get("total_attempts", 0)
            
            if attempts > 0:
                # Normalize metrics to 0-100 scale
                success_rate = stats.get("success_rate", 0)
                speed_score = max(0, 100 - (stats.get("avg_time_ms", 5000) / 50))
                efficiency = stats.get("efficiency_score", 0)
                
                comparison[method] = {
                    "success_rate": round(success_rate, 1),
                    "speed_score": round(speed_score, 1),
                    "efficiency_score": round(efficiency, 1)
                }
        
        return comparison
    
    def sync_from_history(self):
        """Sync stats from history.json (run once on first load)."""
        try:
            history_file = Path(__file__).parent.parent / "history.json"
            if not history_file.exists():
                return
            
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            # Sync normal links
            for url, data in history.get("normal", {}).items():
                scraper = data.get("scraper", "simple_http")
                word_count = data.get("word_count", 0)
                extracted_at = data.get("extracted_at")
                
                if extracted_at:
                    # Add to daily stats
                    date = extracted_at[:10]
                    method_key = scraper.replace("-", "_")
                    if method_key not in METHODS:
                        method_key = "simple_http"
                    
                    if date not in self.stats["daily"]:
                        self.stats["daily"][date] = {m: {"success": 0, "failed": 0, "time_ms": 0, "words": 0} for m in METHODS}
                    
                    self.stats["daily"][date][method_key]["success"] += 1
                    self.stats["daily"][date][method_key]["words"] += word_count
                    
                    # Update method stats
                    self.stats["methods"][method_key]["success"] += 1
                    self.stats["methods"][method_key]["total_attempts"] += 1
                    self.stats["methods"][method_key]["total_words"] += word_count
            
            self.save()
            
        except Exception as e:
            print(f"Error syncing from history: {e}")


scraping_stats = ScrapingStats()
