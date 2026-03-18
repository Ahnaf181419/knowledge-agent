"""Unit tests for metadata_extractor module."""

from unittest.mock import MagicMock, patch


class TestMetadataExtractor:
    """Tests for MetadataExtractor class."""

    @patch("scraper.core.metadata_extractor.logger")
    def test_extract_genre_found(self, mock_logger):
        """Test extracting genre from page."""
        from scraper.core.metadata_extractor import MetadataExtractor

        mock_page = MagicMock()
        
        mock_locator = MagicMock()
        mock_locator.count.return_value = 1
        
        mock_text_mock = MagicMock()
        mock_text_mock.text_content.return_value = "Fantasy, Adventure"
        
        mock_page.locator.return_value.first = mock_text_mock
        mock_page.locator.return_value.count.return_value = 1

        genre = MetadataExtractor._extract_genre(mock_page)

        assert genre == ["Fantasy", "Adventure"]

    @patch("scraper.core.metadata_extractor.logger")
    def test_extract_genre_not_found(self, mock_logger):
        """Test extracting genre when not present."""
        from scraper.core.metadata_extractor import MetadataExtractor

        mock_page = MagicMock()
        mock_page.locator.return_value.count.return_value = 0

        genre = MetadataExtractor._extract_genre(mock_page)

        assert genre == []

    @patch("scraper.core.metadata_extractor.logger")
    def test_extract_genre_exception(self, mock_logger):
        """Test genre extraction handles exception."""
        from scraper.core.metadata_extractor import MetadataExtractor

        mock_page = MagicMock()
        mock_page.locator.side_effect = Exception("Error")

        genre = MetadataExtractor._extract_genre(mock_page)

        assert genre == []

    @patch("scraper.core.metadata_extractor.logger")
    def test_extract_tags_found(self, mock_logger):
        """Test extracting tags from page."""
        from scraper.core.metadata_extractor import MetadataExtractor

        mock_page = MagicMock()
        
        mock_locator = MagicMock()
        mock_locator.count.return_value = 1
        
        mock_text_mock = MagicMock()
        mock_text_mock.text_content.return_value = "isekai, magic, school"
        
        mock_page.locator.return_value.first = mock_text_mock
        mock_page.locator.return_value.count.return_value = 1

        tags = MetadataExtractor._extract_tags(mock_page)

        assert tags == ["isekai", "magic", "school"]

    @patch("scraper.core.metadata_extractor.logger")
    def test_extract_tags_not_found(self, mock_logger):
        """Test extracting tags when not present."""
        from scraper.core.metadata_extractor import MetadataExtractor

        mock_page = MagicMock()
        mock_page.locator.return_value.count.return_value = 0

        tags = MetadataExtractor._extract_tags(mock_page)

        assert tags == []

    @patch("scraper.core.metadata_extractor.logger")
    def test_extract_author_found(self, mock_logger):
        """Test extracting author from page."""
        from scraper.core.metadata_extractor import MetadataExtractor

        mock_page = MagicMock()
        
        mock_text_mock = MagicMock()
        mock_text_mock.text_content.return_value = "John Doe"
        
        mock_page.locator.return_value.first = mock_text_mock
        mock_page.locator.return_value.count.return_value = 1

        author = MetadataExtractor._extract_author(mock_page)

        assert author == "John Doe"

    @patch("scraper.core.metadata_extractor.logger")
    def test_extract_author_not_found(self, mock_logger):
        """Test extracting author when not present."""
        from scraper.core.metadata_extractor import MetadataExtractor

        mock_page = MagicMock()
        mock_page.locator.return_value.count.return_value = 0

        author = MetadataExtractor._extract_author(mock_page)

        assert author == "Unknown"

    @patch("scraper.core.metadata_extractor.logger")
    def test_extract_full_metadata(self, mock_logger):
        """Test extracting full metadata."""
        from scraper.core.metadata_extractor import MetadataExtractor

        mock_page = MagicMock()

        def mock_locator(selector):
            mock_loc = MagicMock()
            mock_loc.count.return_value = 1
            
            mock_text = MagicMock()
            if "genre" in selector:
                mock_text.text_content.return_value = "Fantasy"
            elif "tag" in selector:
                mock_text.text_content.return_value = "magic"
            elif "author" in selector:
                mock_text.text_content.return_value = "Jane Author"
            
            mock_loc.first = mock_text
            return mock_loc

        mock_page.locator.side_effect = mock_locator

        result = MetadataExtractor.extract(mock_page, "http://test.com")

        assert result["genre"] == ["Fantasy"]
        assert result["tags"] == ["magic"]
        assert result["author"] == "Jane Author"

    @patch("scraper.core.metadata_extractor.logger")
    def test_extract_metadata_empty(self, mock_logger):
        """Test extracting metadata with no data."""
        from scraper.core.metadata_extractor import MetadataExtractor

        mock_page = MagicMock()
        mock_page.locator.return_value.count.return_value = 0

        result = MetadataExtractor.extract(mock_page, "http://test.com")

        assert result["genre"] == []
        assert result["tags"] == []
        assert result["author"] == "Unknown"
        assert result["title"] is None


class TestMetadataExtractorSingleton:
    """Tests for singleton instance."""

    def test_singleton_exists(self):
        """Test that singleton instance exists."""
        from scraper.core.metadata_extractor import metadata_extractor

        assert metadata_extractor is not None
        assert hasattr(metadata_extractor, 'extract')
