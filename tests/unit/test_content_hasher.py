"""Tests for content hasher utilities."""

import os
import tempfile

from utils.content_hasher import compute_content_hash, compute_file_hash, compute_sha256


class TestComputeSha256:
    def test_empty_string(self):
        result = compute_sha256("")
        assert len(result) == 64

    def test_same_content_same_hash(self):
        content = "Hello, World!"
        assert compute_sha256(content) == compute_sha256(content)

    def test_different_content_different_hash(self):
        assert compute_sha256("hello") != compute_sha256("world")

    def test_unicode_content(self):
        result = compute_sha256("Hello 你好")
        assert len(result) == 64


class TestComputeContentHash:
    def test_normalize_whitespace(self):
        text = "Hello    World"
        text_normalized = "Hello  World"
        assert compute_content_hash(text) == compute_content_hash(text_normalized)

    def test_no_normalize(self):
        text = "Hello    World"
        text_no_norm = "Hello World"
        assert compute_content_hash(text, normalize=False) != compute_content_hash(
            text_no_norm, normalize=False
        )

    def test_consistency(self):
        text = "Test content with multiple   spaces"
        assert compute_content_hash(text) == compute_content_hash(text)


class TestComputeFileHash:
    def test_existing_file(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Test content")
            temp_path = f.name

        try:
            result = compute_file_hash(temp_path)
            assert result is not None
            assert len(result) == 64
        finally:
            os.unlink(temp_path)

    def test_nonexistent_file(self):
        result = compute_file_hash("/nonexistent/path/file.txt")
        assert result is None
