"""
Stats service - SQLite-backed scraping statistics.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

from sqlmodel import func, select

from app.db import ScrapeMetric, get_session_context

STATS_FILE = Path(__file__).parent.parent.parent / "scraping_stats.json"

METHODS = ["simple_http", "playwright", "playwright_alt", "playwright_tls", "cloudscraper"]


class StatsService:
    """SQLite-backed scraping statistics service."""

    def __init__(self):
        self._ensure_tables()
        self._migrate_from_json_if_needed()

    def _ensure_tables(self):
        from app.db import init_db

        init_db()

    def _migrate_from_json_if_needed(self):
        """Migrate from JSON to SQLite if JSON file exists."""
        if not STATS_FILE.exists():
            return

        with get_session_context() as session:
            existing = session.exec(select(ScrapeMetric)).first()
            if existing:
                return

            try:
                with open(STATS_FILE, encoding="utf-8") as f:
                    data = json.load(f)

                for date, day_data in data.get("daily", {}).items():
                    for method, mdata in day_data.items():
                        for _ in range(mdata.get("success", 0)):
                            session.add(
                                ScrapeMetric(
                                    url="",
                                    domain="migrated",
                                    method=method,
                                    success=True,
                                    time_ms=mdata.get("time_ms", 0)
                                    // max(mdata.get("success", 1), 1),
                                    word_count=mdata.get("words", 0)
                                    // max(mdata.get("success", 1), 1),
                                    scraped_at=datetime.fromisoformat(date),
                                )
                            )
                        for _ in range(mdata.get("failed", 0)):
                            session.add(
                                ScrapeMetric(
                                    url="",
                                    domain="migrated",
                                    method=method,
                                    success=False,
                                    time_ms=mdata.get("time_ms", 0)
                                    // max(mdata.get("failed", 1), 1),
                                    scraped_at=datetime.fromisoformat(date),
                                )
                            )

                session.commit()
            except (json.JSONDecodeError, OSError):
                pass

    def record_scrape(
        self,
        url: str,
        method: str,
        success: bool,
        time_ms: int,
        word_count: int = 0,
        error_message: str | None = None,
    ):
        from urllib.parse import urlparse

        domain = urlparse(url).netloc if url else "unknown"
        method_key = method.replace("-", "_")
        if method_key not in METHODS:
            method_key = "simple_http"

        with get_session_context() as session:
            metric = ScrapeMetric(
                url=url,
                domain=domain,
                method=method_key,
                success=success,
                time_ms=time_ms,
                word_count=word_count,
                error_message=error_message,
                scraped_at=datetime.now(),
            )
            session.add(metric)
            session.commit()

    def get_method_stats(self, days: int | None = None) -> dict:
        with get_session_context() as session:
            query = select(ScrapeMetric)
            if days:
                cutoff = datetime.now() - timedelta(days=days)
                query = query.where(ScrapeMetric.scraped_at >= cutoff)

            metrics = session.exec(query).all()

            stats = {
                m: {
                    "success": 0,
                    "failed": 0,
                    "total_attempts": 0,
                    "total_time_ms": 0,
                    "total_words": 0,
                }
                for m in METHODS
            }

            for m in metrics:
                if m.method in stats:
                    stats[m.method]["total_attempts"] += 1
                    stats[m.method]["total_time_ms"] += m.time_ms
                    if m.success:
                        stats[m.method]["success"] += 1
                        stats[m.method]["total_words"] += m.word_count
                    else:
                        stats[m.method]["failed"] += 1

            result = {}
            for method, data in stats.items():
                attempts = data["success"] + data["failed"]
                if attempts > 0:
                    result[method] = {
                        "success": data["success"],
                        "failed": data["failed"],
                        "total_attempts": attempts,
                        "avg_time_ms": data["total_time_ms"] // attempts,
                        "total_words": data["total_words"],
                        "success_rate": (data["success"] / attempts * 100),
                        "efficiency_score": self._calc_efficiency(
                            {
                                "success_rate": (data["success"] / attempts * 100),
                                "avg_time_ms": data["total_time_ms"] // attempts,
                                "avg_words": data["total_words"] / attempts,
                            }
                        ),
                    }

            return result

    def _calc_efficiency(self, stats: dict) -> float:
        success_rate = stats.get("success_rate", 0)
        speed_score = max(0, 100 - (stats.get("avg_time_ms", 5000) / 50))
        word_score = min(stats.get("avg_words", 0) / 50 * 50, 50)
        return float(round((success_rate * 0.4) + (speed_score * 0.3) + (word_score * 0.3), 1))

    def get_daily_activity(self, days: int = 7) -> dict:
        result = {}
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            cutoff_start = datetime.strptime(date, "%Y-%m-%d")
            cutoff_end = cutoff_start + timedelta(days=1)

            with get_session_context() as session:
                stmt = select(ScrapeMetric).where(
                    ScrapeMetric.scraped_at >= cutoff_start, ScrapeMetric.scraped_at < cutoff_end
                )
                metrics = session.exec(stmt).all()

                day_stats = {m: {"success": 0, "failed": 0} for m in METHODS}
                total_words = 0

                for m in metrics:
                    if m.method in day_stats:
                        if m.success:
                            day_stats[m.method]["success"] += 1
                        else:
                            day_stats[m.method]["failed"] += 1
                        total_words += m.word_count

                total_success = sum(s["success"] for s in day_stats.values())
                total_failed = sum(s["failed"] for s in day_stats.values())

                result[date] = {
                    "urls": total_success + total_failed,
                    "success": total_success,
                    "failed": total_failed,
                    "words": total_words,
                    "by_method": day_stats,
                }

        return result

    def get_summary_stats(self, days: int | None = None) -> dict:
        method_stats = self.get_method_stats(days)

        total_attempts = sum(m.get("total_attempts", 0) for m in method_stats.values())
        total_success = sum(m.get("success", 0) for m in method_stats.values())
        total_words = sum(m.get("total_words", 0) for m in method_stats.values())

        with get_session_context() as session:
            query = select(func.sum(ScrapeMetric.time_ms))
            if days:
                cutoff = datetime.now() - timedelta(days=days)
                query = query.where(ScrapeMetric.scraped_at >= cutoff)
            total_time = session.exec(query).one() or 0

        return {
            "total_attempts": total_attempts,
            "total_success": total_success,
            "total_failed": total_attempts - total_success,
            "success_rate": (total_success / total_attempts * 100) if total_attempts > 0 else 0,
            "total_words": total_words,
            "avg_time_ms": total_time // total_attempts if total_attempts > 0 else 0,
            "method_count": len(
                [m for m in method_stats if method_stats[m].get("total_attempts", 0) > 0]
            ),
        }

    def get_recent(self, limit: int = 20) -> list:
        with get_session_context() as session:
            stmt = select(ScrapeMetric).order_by(ScrapeMetric.scraped_at.desc()).limit(limit)  # type: ignore[attr-defined]
            metrics = session.exec(stmt).all()
            return [
                {
                    "url": m.url,
                    "method": m.method,
                    "success": m.success,
                    "time_ms": m.time_ms,
                    "word_count": m.word_count,
                    "domain": m.domain,
                    "timestamp": m.scraped_at.isoformat(),
                }
                for m in metrics
            ]

    def get_errors(self, limit: int = 20) -> list:
        with get_session_context() as session:
            stmt = (
                select(ScrapeMetric)
                .where(not ScrapeMetric.success)
                .order_by(ScrapeMetric.scraped_at.desc())  # type: ignore[attr-defined]
                .limit(limit)
            )
            metrics = session.exec(stmt).all()
            return [
                {"url": m.url, "method": m.method, "timestamp": m.scraped_at.isoformat()}
                for m in metrics
            ]

    def get_method_domain_stats(self, domain: str, method: str, days: int | None = None) -> dict:
        """Get stats for a specific method on a specific domain."""
        with get_session_context() as session:
            query = select(ScrapeMetric).where(
                ScrapeMetric.domain == domain, ScrapeMetric.method == method
            )
            if days:
                cutoff = datetime.now() - timedelta(days=days)
                query = query.where(ScrapeMetric.scraped_at >= cutoff)

            metrics = session.exec(query).all()

            success_count = sum(1 for m in metrics if m.success)
            failure_count = sum(1 for m in metrics if not m.success)
            total = len(metrics)

            return {
                "domain": domain,
                "method": method,
                "total": total,
                "success_count": success_count,
                "failure_count": failure_count,
                "success_rate": (success_count / total * 100) if total > 0 else 0.0,
                "avg_time_ms": sum(m.time_ms for m in metrics) // max(total, 1),
            }

    def get_domain_stats(self, domain: str, days: int | None = None) -> list[dict]:
        """Get all method stats for a specific domain."""
        with get_session_context() as session:
            query = select(ScrapeMetric).where(ScrapeMetric.domain == domain)
            if days:
                cutoff = datetime.now() - timedelta(days=days)
                query = query.where(ScrapeMetric.scraped_at >= cutoff)

            metrics = session.exec(query).all()

            method_data: dict[str, dict] = {}
            for m in metrics:
                if m.method not in method_data:
                    method_data[m.method] = {
                        "method": m.method,
                        "total": 0,
                        "success_count": 0,
                        "failure_count": 0,
                        "total_time_ms": 0,
                    }
                method_data[m.method]["total"] += 1
                method_data[m.method]["total_time_ms"] += m.time_ms
                if m.success:
                    method_data[m.method]["success_count"] += 1
                else:
                    method_data[m.method]["failure_count"] += 1

            result = []
            for method, data in method_data.items():
                total = data["total"]
                result.append(
                    {
                        "method": method,
                        "total": total,
                        "success_count": data["success_count"],
                        "failure_count": data["failure_count"],
                        "success_rate": (data["success_count"] / total * 100) if total > 0 else 0.0,
                        "avg_time_ms": data["total_time_ms"] // max(total, 1),
                    }
                )

            return result

    def get_all_domains(self, days: int | None = None) -> list[str]:
        """Get all domains that have stats."""
        with get_session_context() as session:
            query = select(ScrapeMetric.domain).distinct()
            if days:
                cutoff = datetime.now() - timedelta(days=days)
                query = query.where(ScrapeMetric.scraped_at >= cutoff)
            domains = session.exec(query).all()
            return list(domains)


stats_service = StatsService()
