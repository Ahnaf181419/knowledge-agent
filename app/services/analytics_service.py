"""
Analytics Service Module

Business logic for analytics and statistics.
Aggregates data from stats repository for UI display.
"""

from typing import Dict, Any, Optional, List
from app.repositories.interfaces import IStatsRepository
from app.logger import logger


class AnalyticsService:
    """
    Service for analytics operations.
    
    Provides:
    - Method comparison data
    - Efficiency rankings
    - Activity trends
    - Error analysis
    """
    
    def __init__(self, stats_repo: IStatsRepository):
        self._stats = stats_repo
    
    def get_method_comparison(self, days: Optional[int] = None) -> Dict[str, Any]:
        """Get comparison data for radar chart."""
        return self._stats.get_method_comparison(days)
    
    def get_efficiency_rankings(self, days: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get methods ranked by efficiency score."""
        method_stats = self._stats.get_method_stats(days)
        
        ranked = sorted(
            method_stats.items(),
            key=lambda x: x[1].get('efficiency_score', 0),
            reverse=True
        )
        
        return [
            {
                "method": method,
                "rank": i + 1,
                "efficiency_score": data.get('efficiency_score', 0),
                "success_rate": data.get('success_rate', 0),
                "avg_time_ms": data.get('avg_time_ms', 0),
                "total_attempts": data.get('total_attempts', 0)
            }
            for i, (method, data) in enumerate(ranked)
            if data.get('total_attempts', 0) > 0
        ]
    
    def get_summary(self, days: Optional[int] = None) -> Dict[str, Any]:
        """Get summary statistics."""
        return self._stats.get_summary_stats(days)
    
    def get_method_stats(self, days: Optional[int] = None) -> Dict[str, Any]:
        """Get statistics by method."""
        return self._stats.get_method_stats(days)
    
    def get_daily_activity(self, days: int = 7) -> Dict[str, Any]:
        """Get daily activity for the last N days."""
        return self._stats.get_daily_activity(days)
    
    def get_method_timeline(self, days: int = 30) -> Dict[str, Any]:
        """Get method usage broken down by day."""
        return self._stats.get_method_timeline(days)
    
    def get_domain_stats(self, limit: int = 10) -> Dict[str, Any]:
        """Get domain-level statistics."""
        return self._stats.get_domain_stats(limit)
    
    def get_error_analysis(self, days: Optional[int] = None) -> Dict[str, Any]:
        """Analyze errors by method and domain."""
        return self._stats.get_error_analysis(days)
    
    def get_recent_activity(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent scraping results formatted for display."""
        recent = self._stats.get_recent(limit)
        
        return [
            {
                "url": item.url,
                "method": item.method,
                "success": item.success,
                "time_ms": item.time_ms,
                "word_count": item.word_count,
                "domain": item.domain,
                "timestamp": item.timestamp
            }
            for item in recent
        ]
