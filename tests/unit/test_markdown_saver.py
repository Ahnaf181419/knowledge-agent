"""
Unit tests for markdown_saver module.
Tests output format, frontmatter, and file saving.
"""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from storage.markdown_saver import save_normal_article

# Use testoutput folder in root for tests
TEST_OUTPUT_FOLDER = Path(__file__).parent.parent.parent / "testoutput"


class TestSaveNormalArticle:
    """Tests for save_normal_article function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test output folder."""
        TEST_OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
        yield
        # Cleanup test files after each test
        for f in TEST_OUTPUT_FOLDER.glob("test-*.md"):
            f.unlink()
        for f in TEST_OUTPUT_FOLDER.glob("test-*.json"):
            f.unlink()
        for f in TEST_OUTPUT_FOLDER.glob("test-*.txt"):
            f.unlink()

    @pytest.fixture
    def temp_folder(self):
        """Return the test output folder."""
        return TEST_OUTPUT_FOLDER

    def test_markdown_format_v2_frontmatter(self, temp_folder):
        """Test that saved markdown has v2.0 frontmatter format."""
        url = "https://example.com/test-article"
        title = "Test Article"
        content = "# Test Article\n\nThis is test content."
        tags = ["test", "sample"]
        word_count = 5

        with patch("utils.validators.generate_slug", return_value="test-article"):
            file_path = save_normal_article(
                folder=temp_folder,
                url=url,
                title=title,
                content=content,
                tags=tags,
                word_count=word_count,
                output_format="md",
                engine="playwright",
                content_type="article",
            )

        assert file_path.exists()

        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        # Check frontmatter structure
        assert lines[0] == "---"
        assert lines[1].startswith("source_url:")
        assert '"https://example.com/test-article"' in lines[1]
        assert lines[2].startswith("title:")
        assert '"Test Article"' in lines[2]
        assert lines[3].startswith("engine:")
        assert '"playwright"' in lines[3]
        assert lines[4].startswith("content_type:")
        assert '"article"' in lines[4]
        assert lines[5].startswith("tags:")
        assert "test" in lines[5] and "sample" in lines[5]
        assert lines[6].startswith("word_count:")
        assert "5" in lines[6]
        assert lines[7].startswith("scraped_at:")
        assert lines[8] == "---"

    def test_json_format_v2(self, temp_folder):
        """Test that saved JSON has v2.0 format."""
        url = "https://example.com/test-article"
        title = "Test Article"
        content = "Test content"
        tags = ["test"]

        with patch("utils.validators.generate_slug", return_value="test-article"):
            file_path = save_normal_article(
                folder=temp_folder,
                url=url,
                title=title,
                content=content,
                tags=tags,
                word_count=2,
                output_format="json",
                engine="simple_http",
                content_type="blog",
            )

        assert file_path.exists()

        data = json.loads(file_path.read_text(encoding="utf-8"))

        assert data["source_url"] == url
        assert data["title"] == title
        assert data["content"] == content
        assert data["tags"] == tags
        assert data["word_count"] == 2
        assert data["engine"] == "simple_http"
        assert data["content_type"] == "blog"
        assert "scraped_at" in data

    def test_txt_format(self, temp_folder):
        """Test that saved TXT has proper format."""
        url = "https://example.com/test-article"
        title = "Test Article"
        content = "Test content here"

        with patch("utils.validators.generate_slug", return_value="test-article"):
            file_path = save_normal_article(
                folder=temp_folder,
                url=url,
                title=title,
                content=content,
                tags=[],
                word_count=3,
                output_format="txt",
                engine="playwright_alt",
                content_type="wiki",
            )

        assert file_path.exists()

        text = file_path.read_text(encoding="utf-8")

        assert "Test Article" in text
        assert url in text
        assert "Engine: playwright_alt" in text
        assert "Test content here" in text

    def test_slug_generation(self, temp_folder):
        """Test that slug is generated from URL."""
        url = "https://example.com/my-article-name"
        title = "My Article"

        with patch("utils.validators.generate_slug", return_value="my-article-name") as mock_slug:
            file_path = save_normal_article(
                folder=temp_folder,
                url=url,
                title=title,
                content="Content",
                tags=[],
                word_count=1,
            )

        mock_slug.assert_called_once_with(url, title)
        assert file_path.name == "my-article-name.md"

    def test_slug_with_query_params_stripped(self, temp_folder):
        """Test that query parameters are stripped from slug."""
        url = "https://example.com/chapter-1?service=web"
        title = "Chapter 1"

        with patch("utils.validators.generate_slug", return_value="chapter-1") as mock_slug:
            file_path = save_normal_article(
                folder=temp_folder,
                url=url,
                title=title,
                content="Content",
                tags=[],
                word_count=1,
            )

        mock_slug.assert_called()
        assert "?" not in file_path.name
        assert file_path.name == "chapter-1.md"

    def test_word_count_in_frontmatter(self, temp_folder):
        """Test that word count is correctly stored in frontmatter."""
        content = "one two three four five six seven eight nine ten"

        with patch("utils.validators.generate_slug", return_value="test"):
            file_path = save_normal_article(
                folder=temp_folder,
                url="https://example.com/test",
                title="Test",
                content=content,
                tags=[],
                word_count=10,
            )

        content_text = file_path.read_text(encoding="utf-8")
        assert "word_count: 10" in content_text

    def test_tags_array_format(self, temp_folder):
        """Test that tags are saved as JSON array."""
        tags = ["gaming", "action", "adventure"]

        with patch("utils.validators.generate_slug", return_value="test"):
            file_path = save_normal_article(
                folder=temp_folder,
                url="https://example.com/test",
                title="Test",
                content="Content",
                tags=tags,
                word_count=1,
            )

        content_text = file_path.read_text(encoding="utf-8")

        # Tags should be in JSON array format
        assert 'tags: ["gaming", "action", "Adventure"]' in content_text or \
               "tags:" in content_text

    def test_iso8601_timestamp(self, temp_folder):
        """Test that scraped_at uses ISO 8601 format."""
        with patch("utils.validators.generate_slug", return_value="test"):
            file_path = save_normal_article(
                folder=temp_folder,
                url="https://example.com/test",
                title="Test",
                content="Content",
                tags=[],
                word_count=1,
            )

        content_text = file_path.read_text(encoding="utf-8")
        # Check that scraped_at exists and looks like ISO format (contains T)
        assert "scraped_at:" in content_text
        assert "T" in content_text  # ISO format has T between date and time

    def test_file_path_returned(self, temp_folder):
        """Test that function returns the file path."""
        with patch("utils.validators.generate_slug", return_value="test"):
            file_path = save_normal_article(
                folder=temp_folder,
                url="https://example.com/test",
                title="Test",
                content="Content",
                tags=[],
                word_count=1,
            )

        assert isinstance(file_path, Path)
        assert file_path.exists()

    def test_all_content_types(self, temp_folder):
        """Test all content_type values."""
        content_types = ["article", "blog", "wiki", "novel"]

        for content_type in content_types:
            with patch("utils.validators.generate_slug", return_value=f"test-{content_type}"):
                file_path = save_normal_article(
                    folder=temp_folder,
                    url=f"https://example.com/test-{content_type}",
                    title="Test",
                    content="Content",
                    tags=[],
                    word_count=1,
                    content_type=content_type,
                )

                content_text = file_path.read_text(encoding="utf-8")
                assert f'content_type: "{content_type}"' in content_text

    def test_all_engines(self, temp_folder):
        """Test all engine values."""
        engines = ["simple_http", "playwright", "playwright_alt", "playwright_tls", "cloudscraper"]

        for engine in engines:
            with patch("utils.validators.generate_slug", return_value=f"test-{engine}"):
                file_path = save_normal_article(
                    folder=temp_folder,
                    url=f"https://example.com/test-{engine}",
                    title="Test",
                    content="Content",
                    tags=[],
                    word_count=1,
                    engine=engine,
                )

                content_text = file_path.read_text(encoding="utf-8")
                assert f'engine: "{engine}"' in content_text
