"""
Method Optimizer Module

Self-optimizing scraper that analyzes success rates and promotes/demotes methods.
Uses stats from the database to make informed decisions about method selection.

The optimizer works as follows:
1. Track success/failure rates per domain and method
2. After N successful scrapes with a method, try promoting it for that domain
3. After M failures with a method, try demoting it
4. Provide method recommendations based on historical performance

This module requires Phase 0 validation (stable stats) before being enabled.
"""

import logging
from dataclasses import dataclass
from datetime import datetime

from app.services.stats_service import stats_service
from app.state import state

logger = logging.getLogger(__name__)


@dataclass
class MethodRecommendation:
    """Recommendation for which method to use."""

    method: str
    confidence: float  # 0.0 to 1.0
    reason: str


class MethodOptimizer:
    """
    Self-optimizing scraper method selector.

    Analyzes historical scraping data to recommend the best method
    for a given URL or domain.

    Features:
    - Per-domain method tracking
    - Success rate calculation
    - Automatic method promotion/demotion
    - Confidence scoring
    """

    def __init__(
        self,
        success_promotion_threshold: int = 5,
        failure_demotion_threshold: int = 3,
        min_samples_for_confidence: int = 10,
        optimization_enabled: bool = True,
    ):
        self.success_promotion_threshold = success_promotion_threshold
        self.failure_demotion_threshold = failure_demotion_threshold
        self.min_samples_for_confidence = min_samples_for_confidence
        self.enabled = optimization_enabled

    def get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        from urllib.parse import urlparse

        try:
            parsed = urlparse(url)
            return parsed.netloc or "unknown"
        except Exception:
            return "unknown"

    def get_method_stats(self, domain: str, method: str) -> dict:
        """
        Get statistics for a specific method on a domain.

        Returns:
            Dict with total, success_count, failure_count, success_rate, avg_time_ms
        """
        return stats_service.get_method_domain_stats(domain, method)

    def get_domain_methods(self, domain: str) -> list[dict]:
        """Get all method stats for a domain."""
        return stats_service.get_domain_stats(domain)

    def calculate_success_rate(self, stats: dict) -> float:
        """Calculate success rate from stats."""
        total = stats.get("total", 0)
        if total == 0:
            return 0.0
        success = stats.get("success_count", 0)
        return float(success / total)

    def get_recommendation(self, url: str) -> MethodRecommendation:
        """
        Get method recommendation for a URL.

        Args:
            url: URL to scrape

        Returns:
            MethodRecommendation with suggested method
        """
        if not self.enabled:
            return MethodRecommendation(
                method="simple_http",
                confidence=0.0,
                reason="Optimizer disabled",
            )

        domain = self.get_domain(url)
        domain_methods = self.get_domain_methods(domain)

        if not domain_methods:
            return MethodRecommendation(
                method="simple_http",
                confidence=0.1,
                reason="No historical data for domain",
            )

        best_method = None
        best_rate = 0.0
        best_confidence = 0.0
        total = 0

        for method_stats in domain_methods:
            method = method_stats.get("method", "unknown")
            total = method_stats.get("total", 0)
            success_rate = method_stats.get("success_rate", 0.0)

            if total >= self.min_samples_for_confidence:
                confidence = min(1.0, total / 50.0)  # Higher confidence with more samples
            elif total >= 3:
                confidence = 0.3
            else:
                confidence = 0.1

            if success_rate > best_rate or (
                success_rate == best_rate and confidence > best_confidence
            ):
                best_rate = success_rate
                best_method = method
                best_confidence = confidence

        if best_method is None:
            return MethodRecommendation(
                method="simple_http",
                confidence=0.1,
                reason="Insufficient data",
            )

        return MethodRecommendation(
            method=best_method,
            confidence=best_confidence,
            reason=f"Success rate: {best_rate:.1%} ({total} samples)",
        )

    def should_promote(self, domain: str, method: str) -> bool:
        """
        Check if a method should be promoted for a domain.

        Promotion criteria:
        - At least success_promotion_threshold successful scrapes
        - Success rate > 80%
        """
        stats = self.get_method_stats(domain, method)
        success_count = stats.get("success_count", 0)
        success_rate = self.calculate_success_rate(stats)

        if success_count >= self.success_promotion_threshold and success_rate > 0.8:
            logger.info(
                f"Method {method} should be promoted for {domain}: {success_count} successes, {success_rate:.1%} rate"
            )
            return True

        return False

    def should_demote(self, domain: str, method: str) -> bool:
        """
        Check if a method should be demoted for a domain.

        Demotion criteria:
        - At least failure_demotion_threshold failures
        - Success rate < 30%
        """
        stats = self.get_method_stats(domain, method)
        failure_count = stats.get("failure_count", 0)
        total = stats.get("total", 0)

        if total == 0:
            return False

        success_rate = self.calculate_success_rate(stats)

        if failure_count >= self.failure_demotion_threshold and success_rate < 0.3:
            logger.info(
                f"Method {method} should be demoted for {domain}: {failure_count} failures, {success_rate:.1%} rate"
            )
            return True

        return False

    def get_all_domains(self) -> list[str]:
        """Get all domains with stats."""
        return stats_service.get_all_domains()

    def get_optimization_report(self) -> dict:
        """
        Generate a full optimization report.

        Returns:
            Dict with domain analysis and recommendations
        """
        domains = self.get_all_domains()
        report = {
            "domains": [],
            "promotions": [],
            "demotions": [],
            "timestamp": datetime.now().isoformat(),
        }

        for domain in domains:
            domain_info = {
                "domain": domain,
                "methods": [],
            }

            for method_stats in self.get_domain_methods(domain):
                method = method_stats.get("method", "unknown")
                total = method_stats.get("total", 0)
                success_rate = method_stats.get("success_rate", 0.0)

                method_info = {
                    "method": method,
                    "total": total,
                    "success_rate": success_rate,
                    "recommend_promote": self.should_promote(domain, method),
                    "recommend_demote": self.should_demote(domain, method),
                }

                domain_info["methods"].append(method_info)  # type: ignore[attr-defined]

                if method_info["recommend_promote"]:
                    report["promotions"].append(  # type: ignore[attr-defined]
                        {
                            "domain": domain,
                            "method": method,
                        }
                    )

                if method_info["recommend_demote"]:
                    report["demotions"].append(  # type: ignore[attr-defined]
                        {
                            "domain": domain,
                            "method": method,
                        }
                    )

            report["domains"].append(domain_info)  # type: ignore[attr-defined]

        return report


def get_optimizer() -> MethodOptimizer:
    """Get the method optimizer instance."""
    settings = state.settings

    return MethodOptimizer(
        success_promotion_threshold=settings.get("success_promotion_threshold", 5),
        failure_demotion_threshold=settings.get("failure_demotion_threshold", 3),
        min_samples_for_confidence=settings.get("optimization_threshold", 10),
        optimization_enabled=settings.get("auto_optimize", True),
    )


method_optimizer = get_optimizer()
