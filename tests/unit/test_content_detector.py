"""Tests for content detection utilities."""

from utils.content_detector import (
    detect_content_type,
    extract_tags_from_html,
    extract_tags_from_url,
)


class TestDetectContentType:
    def test_wikipedia_domain(self):
        assert detect_content_type("https://en.wikipedia.org/wiki/Python") == "wiki"
        assert detect_content_type("https://de.wikipedia.org/wiki/Test") == "wiki"

    def test_wikimedia_domain(self):
        assert detect_content_type("https://commons.wikimedia.org/wiki/File:Test.jpg") == "wiki"

    def test_novel_pattern_chapter(self):
        assert detect_content_type("https://example.com/novel/123/chapter-1") == "novel"
        assert detect_content_type("https://example.com/chapter_42") == "novel"

    def test_novel_pattern_ch(self):
        assert detect_content_type("https://example.com/ch/12345") == "novel"

    def test_blog_domain_medium(self):
        assert detect_content_type("https://medium.com/@user/post-title") == "blog"

    def test_blog_domain_wordpress(self):
        assert detect_content_type("https://example.wordpress.com/blog/post") == "blog"

    def test_blog_path(self):
        assert detect_content_type("https://example.com/blog/my-post") == "blog"

    def test_article_default(self):
        assert detect_content_type("https://example.com/article/123") == "article"
        assert detect_content_type("https://example.com/page") == "article"

    def test_html_title_novel(self):
        assert (
            detect_content_type("https://example.com/page", "Chapter 1: The Beginning") == "novel"
        )

    def test_html_title_wiki(self):
        assert detect_content_type("https://example.com/page", "Python Wiki") == "wiki"


class TestExtractTagsFromUrl:
    def test_simple_path(self):
        tags = extract_tags_from_url("https://example.com/category/article-name")
        assert "category" in tags or "article" in tags

    def test_novel_path(self):
        tags = extract_tags_from_url("https://novelsite.com/novel/fantasy/123/chapter-1")
        assert "fantasy" in tags

    def test_empty_path(self):
        tags = extract_tags_from_url("https://example.com")
        assert tags == []

    def test_short_segments_excluded(self):
        tags = extract_tags_from_url("https://example.com/a/b/c/d/e")
        assert "a" not in tags
        assert "b" not in tags

    def test_numbers_stripped(self):
        tags = extract_tags_from_url("https://example.com/article-123")
        assert "article" in tags


class TestExtractTagsFromHtml:
    def test_meta_keywords(self):
        html = '<meta name="keywords" content="python, programming, tutorial">'
        tags = extract_tags_from_html(html)
        assert "python" in tags
        assert "programming" in tags

    def test_no_keywords(self):
        html = "<html><body>No meta tags here</body></html>"
        tags = extract_tags_from_html(html)
        assert tags == []

    def test_description_extraction(self):
        html = '<meta name="description" content="Learn Python programming language">'
        tags = extract_tags_from_html(html)
        assert "python" in tags
        assert "programming" in tags
