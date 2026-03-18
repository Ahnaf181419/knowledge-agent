"""Unit tests for method_optimizer module."""

from unittest.mock import patch


class TestMethodRecommendation:
    """Tests for MethodRecommendation dataclass."""

    def test_default_values(self):
        from scraper.method_optimizer import MethodRecommendation

        rec = MethodRecommendation(method="simple_http", confidence=0.5, reason="Test")

        assert rec.method == "simple_http"
        assert rec.confidence == 0.5
        assert rec.reason == "Test"


class TestMethodOptimizer:
    """Tests for MethodOptimizer class."""

    def test_init_default(self):
        from scraper.method_optimizer import MethodOptimizer

        optimizer = MethodOptimizer()

        assert optimizer.success_promotion_threshold == 5
        assert optimizer.failure_demotion_threshold == 3
        assert optimizer.min_samples_for_confidence == 10
        assert optimizer.enabled is True

    def test_init_custom(self):
        from scraper.method_optimizer import MethodOptimizer

        optimizer = MethodOptimizer(
            success_promotion_threshold=10,
            failure_demotion_threshold=5,
            min_samples_for_confidence=20,
            optimization_enabled=False,
        )

        assert optimizer.success_promotion_threshold == 10
        assert optimizer.failure_demotion_threshold == 5
        assert optimizer.min_samples_for_confidence == 20
        assert optimizer.enabled is False

    def test_get_domain(self):
        from scraper.method_optimizer import MethodOptimizer

        optimizer = MethodOptimizer()

        assert optimizer.get_domain("https://example.com/page") == "example.com"
        assert optimizer.get_domain("https://en.wikipedia.org/wiki/Python") == "en.wikipedia.org"
        assert optimizer.get_domain("invalid") == "unknown"

    @patch("scraper.method_optimizer.stats_service")
    def test_get_method_stats(self, mock_stats):
        from scraper.method_optimizer import MethodOptimizer

        mock_stats.get_method_domain_stats.return_value = {
            "total": 10,
            "success_count": 8,
            "failure_count": 2,
            "success_rate": 0.8,
        }

        optimizer = MethodOptimizer()
        stats = optimizer.get_method_stats("example.com", "simple_http")

        assert stats["total"] == 10
        assert stats["success_rate"] == 0.8

    @patch("scraper.method_optimizer.stats_service")
    def test_get_domain_methods(self, mock_stats):
        from scraper.method_optimizer import MethodOptimizer

        mock_stats.get_domain_stats.return_value = [
            {"method": "simple_http", "total": 10, "success_rate": 0.8},
            {"method": "playwright", "total": 5, "success_rate": 0.6},
        ]

        optimizer = MethodOptimizer()
        methods = optimizer.get_domain_methods("example.com")

        assert len(methods) == 2

    def test_calculate_success_rate(self):
        from scraper.method_optimizer import MethodOptimizer

        optimizer = MethodOptimizer()

        stats = {"total": 10, "success_count": 8}
        rate = optimizer.calculate_success_rate(stats)

        assert rate == 0.8

    def test_calculate_success_rate_zero_total(self):
        from scraper.method_optimizer import MethodOptimizer

        optimizer = MethodOptimizer()

        stats = {"total": 0, "success_count": 0}
        rate = optimizer.calculate_success_rate(stats)

        assert rate == 0.0

    @patch("scraper.method_optimizer.stats_service")
    def test_get_recommendation_disabled(self, mock_stats):
        from scraper.method_optimizer import MethodOptimizer

        optimizer = MethodOptimizer(optimization_enabled=False)

        rec = optimizer.get_recommendation("https://example.com/page")

        assert rec.method == "simple_http"
        assert rec.confidence == 0.0
        assert rec.reason == "Optimizer disabled"

    @patch("scraper.method_optimizer.stats_service")
    def test_get_recommendation_no_data(self, mock_stats):
        from scraper.method_optimizer import MethodOptimizer

        mock_stats.get_domain_stats.return_value = []

        optimizer = MethodOptimizer(optimization_enabled=True)

        rec = optimizer.get_recommendation("https://example.com/page")

        assert rec.method == "simple_http"
        assert rec.confidence == 0.1
        assert rec.reason == "No historical data for domain"

    @patch("scraper.method_optimizer.stats_service")
    def test_get_recommendation_with_data(self, mock_stats):
        from scraper.method_optimizer import MethodOptimizer

        mock_stats.get_domain_stats.return_value = [
            {"method": "simple_http", "total": 10, "success_rate": 0.8},
            {"method": "playwright", "total": 5, "success_rate": 0.6},
        ]

        optimizer = MethodOptimizer(optimization_enabled=True)

        rec = optimizer.get_recommendation("https://example.com/page")

        assert rec.method == "simple_http"
        assert rec.confidence > 0

    @patch("scraper.method_optimizer.stats_service")
    def test_should_promote_true(self, mock_stats):
        from scraper.method_optimizer import MethodOptimizer

        mock_stats.get_method_domain_stats.return_value = {
            "total": 10,
            "success_count": 9,
            "failure_count": 1,
            "success_rate": 0.9,
        }

        optimizer = MethodOptimizer(success_promotion_threshold=5)

        result = optimizer.should_promote("example.com", "simple_http")

        assert result is True

    @patch("scraper.method_optimizer.stats_service")
    def test_should_promote_false_low_success_rate(self, mock_stats):
        from scraper.method_optimizer import MethodOptimizer

        mock_stats.get_method_domain_stats.return_value = {
            "total": 10,
            "success_count": 5,
            "failure_count": 5,
            "success_rate": 0.5,
        }

        optimizer = MethodOptimizer(success_promotion_threshold=5)

        result = optimizer.should_promote("example.com", "simple_http")

        assert result is False

    @patch("scraper.method_optimizer.stats_service")
    def test_should_promote_false_low_count(self, mock_stats):
        from scraper.method_optimizer import MethodOptimizer

        mock_stats.get_method_domain_stats.return_value = {
            "total": 3,
            "success_count": 3,
            "failure_count": 0,
            "success_rate": 1.0,
        }

        optimizer = MethodOptimizer(success_promotion_threshold=5)

        result = optimizer.should_promote("example.com", "simple_http")

        assert result is False

    @patch("scraper.method_optimizer.stats_service")
    def test_should_demote_true(self, mock_stats):
        from scraper.method_optimizer import MethodOptimizer

        mock_stats.get_method_domain_stats.return_value = {
            "total": 10,
            "success_count": 2,
            "failure_count": 8,
            "success_rate": 0.2,
        }

        optimizer = MethodOptimizer(failure_demotion_threshold=3)

        result = optimizer.should_demote("example.com", "simple_http")

        assert result is True

    @patch("scraper.method_optimizer.stats_service")
    def test_should_demote_false_high_success_rate(self, mock_stats):
        from scraper.method_optimizer import MethodOptimizer

        mock_stats.get_method_domain_stats.return_value = {
            "total": 10,
            "success_count": 5,
            "failure_count": 5,
            "success_rate": 0.5,
        }

        optimizer = MethodOptimizer(failure_demotion_threshold=3)

        result = optimizer.should_demote("example.com", "simple_http")

        assert result is False

    @patch("scraper.method_optimizer.stats_service")
    def test_should_demote_false_zero_total(self, mock_stats):
        from scraper.method_optimizer import MethodOptimizer

        mock_stats.get_method_domain_stats.return_value = {
            "total": 0,
            "success_count": 0,
            "failure_count": 0,
            "success_rate": 0.0,
        }

        optimizer = MethodOptimizer(failure_demotion_threshold=3)

        result = optimizer.should_demote("example.com", "simple_http")

        assert result is False

    @patch("scraper.method_optimizer.stats_service")
    def test_get_all_domains(self, mock_stats):
        from scraper.method_optimizer import MethodOptimizer

        mock_stats.get_all_domains.return_value = ["example.com", "wikipedia.org"]

        optimizer = MethodOptimizer()

        domains = optimizer.get_all_domains()

        assert len(domains) == 2

    @patch("scraper.method_optimizer.stats_service")
    def test_get_optimization_report(self, mock_stats):
        from scraper.method_optimizer import MethodOptimizer

        mock_stats.get_all_domains.return_value = ["example.com"]
        mock_stats.get_domain_stats.return_value = [
            {"method": "simple_http", "total": 10, "success_rate": 0.8},
        ]
        mock_stats.get_method_domain_stats.return_value = {
            "total": 10,
            "success_count": 8,
            "failure_count": 2,
            "success_rate": 0.8,
        }

        optimizer = MethodOptimizer(success_promotion_threshold=5)

        report = optimizer.get_optimization_report()

        assert "domains" in report
        assert "promotions" in report
        assert "demotions" in report
        assert "timestamp" in report


class TestGetOptimizer:
    """Tests for get_optimizer function."""

    @patch("scraper.method_optimizer.state")
    def test_get_optimizer(self, mock_state):
        from scraper.method_optimizer import MethodOptimizer, get_optimizer

        mock_state.settings = {
            "success_promotion_threshold": 10,
            "failure_demotion_threshold": 5,
            "optimization_threshold": 20,
            "auto_optimize": True,
        }

        optimizer = get_optimizer()

        assert isinstance(optimizer, MethodOptimizer)
        assert optimizer.success_promotion_threshold == 10
        assert optimizer.failure_demotion_threshold == 5
        assert optimizer.min_samples_for_confidence == 20

    @patch("scraper.method_optimizer.state")
    def test_get_optimizer_defaults(self, mock_state):
        from scraper.method_optimizer import get_optimizer

        mock_state.settings = {}

        optimizer = get_optimizer()

        assert optimizer.success_promotion_threshold == 5
        assert optimizer.failure_demotion_threshold == 3
