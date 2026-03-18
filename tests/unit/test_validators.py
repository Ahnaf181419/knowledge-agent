"""Unit tests for validators module."""

from utils.validators import (
    generate_slug,
    get_domain,
    is_novel_url,
    is_valid_url,
    is_youtube_url,
    parse_tags,
    validate_chapter_range,
)


class TestIsValidUrl:
    """Tests for is_valid_url function."""

    def test_valid_http_url(self):
        assert is_valid_url("https://example.com") is True

    def test_valid_https_url(self):
        assert is_valid_url("https://example.com/page") is True

    def test_valid_url_with_query(self):
        assert is_valid_url("https://example.com/search?q=test") is True

    def test_invalid_plain_string(self):
        assert is_valid_url("not-a-url") is False

    def test_invalid_missing_scheme(self):
        assert is_valid_url("example.com") is False

    def test_invalid_missing_netloc(self):
        assert is_valid_url("https://") is False


class TestIsYoutubeUrl:
    """Tests for is_youtube_url function."""

    def test_youtube_watch(self):
        url = "https://youtube.com/watch?v=dQw4w9WgXcQ"
        assert is_youtube_url(url) is True

    def test_youtube_short_link(self):
        url = "https://youtu.be/dQw4w9WgXcQ"
        assert is_youtube_url(url) is True

    def test_youtube_www(self):
        url = "https://www.youtube.com/watch?v=test"
        assert is_youtube_url(url) is True

    def test_non_youtube_url(self):
        url = "https://example.com/video"
        assert is_youtube_url(url) is False


class TestIsNovelUrl:
    """Tests for is_novel_url function."""

    def test_novel_chapter_pattern(self):
        url = "https://wtr-lab.com/novel/12281/chapter-177"
        assert is_novel_url(url) is True

    def test_novel_ch_pattern(self):
        url = "https://example.com/novel/123/ch-45"
        assert is_novel_url(url) is True

    def test_novel_book_pattern(self):
        url = "https://example.com/book-123/456"
        assert is_novel_url(url) is True

    def test_regular_article(self):
        url = "https://example.com/article/123"
        assert is_novel_url(url) is False

    def test_wikipedia(self):
        url = "https://en.wikipedia.org/wiki/Python"
        assert is_novel_url(url) is False


class TestGetDomain:
    """Tests for get_domain function."""

    def test_simple_domain(self):
        assert get_domain("https://example.com/page") == "example.com"

    def test_www_prefix(self):
        assert get_domain("https://www.example.com/page") == "example.com"

    def test_subdomain(self):
        assert get_domain("https://blog.example.com/page") == "blog.example.com"

    def test_with_port(self):
        assert get_domain("https://example.com:8080/page") == "example.com:8080"


class TestGenerateSlug:
    """Tests for generate_slug function."""

    def test_from_url_path(self):
        slug = generate_slug("https://example.com/articles/my-article")
        assert slug == "my-article"

    def test_from_title(self):
        slug = generate_slug("https://example.com/page", title="My Article Title")
        assert slug == "my-article-title"

    def test_truncate_long_slug(self):
        url = "https://example.com/" + "a" * 100
        slug = generate_slug(url)
        assert len(slug) == 50

    def test_special_characters_removed(self):
        slug = generate_slug("https://example.com/page", title="Test! @#$% Article")
        assert "!" not in slug
        assert "@" not in slug


class TestValidateChapterRange:
    """Tests for validate_chapter_range function."""

    def test_valid_range(self):
        is_valid, msg = validate_chapter_range(1, 10)
        assert is_valid is True
        assert msg == "Valid"

    def test_start_less_than_one(self):
        is_valid, msg = validate_chapter_range(0, 10)
        assert is_valid is False
        assert "Start chapter" in msg

    def test_end_less_than_start(self):
        is_valid, msg = validate_chapter_range(10, 5)
        assert is_valid is False
        assert "End chapter" in msg

    def test_range_too_large(self):
        is_valid, msg = validate_chapter_range(1, 2000)
        assert is_valid is False
        assert "too large" in msg

    def test_single_chapter(self):
        is_valid, msg = validate_chapter_range(5, 5)
        assert is_valid is True


class TestParseTags:
    """Tests for parse_tags function."""

    def test_single_tag(self):
        tags = parse_tags("python")
        assert tags == ["python"]

    def test_multiple_tags(self):
        tags = parse_tags("python, javascript, web")
        assert tags == ["python", "javascript", "web"]

    def test_whitespace_handling(self):
        tags = parse_tags("python ,  javascript  , web")
        assert tags == ["python", "javascript", "web"]

    def test_empty_string(self):
        tags = parse_tags("")
        assert tags == []

    def test_none(self):
        tags = parse_tags(None)
        assert tags == []

    def test_only_whitespace(self):
        tags = parse_tags("   ")
        assert tags == []
