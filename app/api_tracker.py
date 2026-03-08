"""
API Usage Tracker Module

Tracks WebScrapingAPI call usage with monthly reset.
- Resets on 1st of each month
- Warning at 4500 calls (90%)
- Stops at 4998 calls (99.96%)
"""

import json
from pathlib import Path
from datetime import datetime


# Configuration
API_CALL_LIMIT = 5000
WARNING_THRESHOLD = 4500  # 90%
STOP_THRESHOLD = 4998      # 99.96%

# File to store API usage
USAGE_FILE = Path(__file__).parent.parent / "api_usage.json"


class APITracker:
    """Tracks API usage and handles monthly resets"""
    
    def __init__(self):
        self.usage = self._load_usage()
        self._check_monthly_reset()
    
    def _load_usage(self) -> dict:
        """Load usage data from file"""
        if USAGE_FILE.exists():
            try:
                with open(USAGE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Default structure
        return self._default_usage()
    
    def _default_usage(self) -> dict:
        """Returns default usage structure"""
        return {
            "current_month": datetime.now().strftime("%Y-%m"),
            "calls_used": 0,
            "calls_limit": API_CALL_LIMIT,
            "warning_at": WARNING_THRESHOLD,
            "stop_at": STOP_THRESHOLD,
            "last_reset": datetime.now().strftime("%Y-%m-%d")
        }
    
    def _check_monthly_reset(self):
        """Check if we need to reset for a new month"""
        current_month = datetime.now().strftime("%Y-%m")
        
        if self.usage.get("current_month") != current_month:
            # New month - reset the counter
            self.usage["current_month"] = current_month
            self.usage["calls_used"] = 0
            self.usage["last_reset"] = datetime.now().strftime("%Y-%m-%d")
            self.save()
    
    def save(self):
        """Save usage data to file"""
        with open(USAGE_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.usage, f, indent=2)
    
    def can_use_api(self) -> tuple[bool, str]:
        """
        Check if API can be used.
        
        Returns:
            (can_use, message)
        """
        calls_used = self.usage.get("calls_used", 0)
        
        if calls_used >= STOP_THRESHOLD:
            return False, f"API limit reached ({calls_used}/{API_CALL_LIMIT}). Please wait until next month."
        
        if calls_used >= WARNING_THRESHOLD:
            remaining = API_CALL_LIMIT - calls_used
            return True, f"WARNING: Almost at limit! {remaining} calls remaining."
        
        return True, "OK"
    
    def increment(self, count: int = 1):
        """Increment API call counter"""
        self.usage["calls_used"] = self.usage.get("calls_used", 0) + count
        self.save()
    
    def get_usage(self) -> dict:
        """Get current usage statistics"""
        calls_used = self.usage.get("calls_used", 0)
        return {
            "calls_used": calls_used,
            "calls_limit": API_CALL_LIMIT,
            "percentage": round((calls_used / API_CALL_LIMIT) * 100, 1),
            "remaining": API_CALL_LIMIT - calls_used,
            "warning_at": WARNING_THRESHOLD,
            "stop_at": STOP_THRESHOLD,
            "current_month": self.usage.get("current_month", ""),
            "last_reset": self.usage.get("last_reset", "")
        }
    
    def get_next_reset_date(self) -> str:
        """Get next month's reset date"""
        now = datetime.now()
        if now.month == 12:
            next_month = datetime(now.year + 1, 1, 1)
        else:
            next_month = datetime(now.year, now.month + 1, 1)
        return next_month.strftime("%B %d, %Y")


# Singleton instance
api_tracker = APITracker()


def can_use_api() -> tuple[bool, str]:
    """Check if API can be used"""
    return api_tracker.can_use_api()


def increment_api_calls(count: int = 1):
    """Increment API call counter"""
    api_tracker.increment(count)


def get_api_usage() -> dict:
    """Get API usage statistics"""
    return api_tracker.get_usage()


def get_next_reset_date() -> str:
    """Get next reset date"""
    return api_tracker.get_next_reset_date()
