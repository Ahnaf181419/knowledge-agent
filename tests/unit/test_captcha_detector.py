"""Unit tests for captcha_detector module."""

from unittest.mock import MagicMock

from scraper.core.captcha_detector import CaptchaDetector, captcha_detector


class TestCaptchaDetector:
    """Tests for CaptchaDetector class."""

    def test_default_indicators(self):
        """Test default CAPTCHA indicators."""
        expected = [
            "just a moment",
            "captcha",
            "verify you are human",
            "cloudflare",
            "checking your browser",
            "access denied",
        ]

        assert CaptchaDetector.INDICATORS == expected

    def test_detect_just_a_moment(self):
        """Test detecting 'just a moment' challenge."""
        mock_page = MagicMock()
        mock_page.title.return_value = "Just a moment..."
        mock_page.content.return_value = "<html>...</html>"

        result = CaptchaDetector.detect(mock_page)

        assert result is True

    def test_detect_cloudflare(self):
        """Test detecting Cloudflare challenge."""
        mock_page = MagicMock()
        mock_page.title.return_value = "Checking your browser"
        mock_page.content.return_value = "Cloudflare"

        result = CaptchaDetector.detect(mock_page)

        assert result is True

    def test_detect_captcha_text(self):
        """Test detecting CAPTCHA text."""
        mock_page = MagicMock()
        mock_page.title.return_value = "Verify you are human"
        mock_page.content.return_value = "<html>...</html>"

        result = CaptchaDetector.detect(mock_page)

        assert result is True

    def test_detect_no_captcha(self):
        """Test normal page returns False."""
        mock_page = MagicMock()
        mock_page.title.return_value = "Example Domain"
        mock_page.content.return_value = "<html><body><p>Welcome</p></body></html>"

        result = CaptchaDetector.detect(mock_page)

        assert result is False

    def test_detect_none_page(self):
        """Test None page returns False."""
        result = CaptchaDetector.detect(None)

        assert result is False

    def test_detect_exception(self):
        """Test exception handling."""
        mock_page = MagicMock()
        mock_page.title.side_effect = Exception("Test")

        result = CaptchaDetector.detect(mock_page)

        assert result is False


class TestCaptchaDetectorStatic:
    """Tests for static check_response method."""

    def test_check_response_with_captcha(self):
        """Test checking response content for CAPTCHA."""
        content = "<html>Just a moment...</html>"

        result = CaptchaDetector.check_response(content)

        assert result is True

    def test_check_response_without_captcha(self):
        """Test normal content returns False."""
        content = "<html><body><p>Hello World</p></body></html>"

        result = CaptchaDetector.check_response(content)

        assert result is False

    def test_check_response_none(self):
        """Test None content returns False."""
        result = CaptchaDetector.check_response(None)

        assert result is False


class TestCaptchaDetectorSingleton:
    """Tests for captcha_detector singleton."""

    def test_singleton_exists(self):
        """Test that captcha_detector singleton exists."""
        assert captcha_detector is not None
        assert hasattr(captcha_detector, "detect")
