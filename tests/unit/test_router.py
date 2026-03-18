"""Unit tests for router module."""

from scraper.router import get_route_reason, route_url


class TestRouteUrl:
    """Tests for route_url function."""

    def test_youtube_skipped(self):
        url = "https://youtube.com/watch?v=test"
        assert route_url(url) == "skip"

    def test_youtube_short_link_skipped(self):
        url = "https://youtu.be/test"
        assert route_url(url) == "skip"

    def test_novel_route(self):
        url = "https://wtr-lab.com/novel/12281/chapter-177"
        assert route_url(url) == "novel"

    def test_novel_ch_pattern(self):
        url = "https://example.com/novel/123/chapter-5"
        assert route_url(url) == "novel"

    def test_amazon_uses_playwright(self):
        url = "https://amazon.com/product/123"
        assert route_url(url) == "playwright"

    def test_twitter_uses_playwright(self):
        url = "https://twitter.com/user/status/123"
        assert route_url(url) == "playwright"

    def test_x_uses_playwright(self):
        url = "https://x.com/user/status/123"
        assert route_url(url) == "playwright"

    def test_facebook_uses_playwright(self):
        url = "https://facebook.com/profile"
        assert route_url(url) == "playwright"

    def test_linkedin_uses_playwright(self):
        url = "https://linkedin.com/in/user"
        assert route_url(url) == "playwright"

    def test_simple_site_uses_simple_http(self):
        url = "https://example.com/article"
        assert route_url(url) == "simple_http"

    def test_wikipedia_uses_playwright_alt(self):
        url = "https://en.wikipedia.org/wiki/Python"
        assert route_url(url) == "playwright_alt"

    def test_blog_uses_simple_http(self):
        url = "https://blog.example.com/post/123"
        assert route_url(url) == "simple_http"


class TestGetRouteReason:
    """Tests for get_route_reason function."""

    def test_youtube_reason(self):
        url = "https://youtube.com/watch?v=test"
        reason = get_route_reason(url)
        assert "YouTube" in reason

    def test_novel_reason(self):
        url = "https://wtr-lab.com/novel/12281/chapter-177"
        reason = get_route_reason(url)
        assert "Novel" in reason

    def test_heavy_site_reason(self):
        url = "https://amazon.com/product/123"
        reason = get_route_reason(url)
        assert "Heavy" in reason or "JS" in reason

    def test_simple_site_reason(self):
        url = "https://example.com/article"
        reason = get_route_reason(url)
        assert "Simple" in reason
