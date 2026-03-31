"""Tests for CDS client functionality."""

import pytest
import responses

from cds_mcp.cds_client import CDSClient, CDSClientError


class TestCDSClient:
    """Test cases for CDSClient."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = CDSClient()

    @responses.activate
    def test_search_success(self):
        """Test successful search."""
        mock_search_response = [
            {
                "recid": 123456,
                "title": {"title": "Test Document"},
                "authors": [{"full_name": "Test Author"}],
                "accelerator_experiment": [{"experiment": "ATLAS"}],
                "collection": [{"primary": "ARTICLE"}],
                "creation_date": "2023-01-01",
                "files": [],
            }
        ]

        responses.add(
            responses.GET,
            "https://cds.cern.ch/search",
            json=mock_search_response,
            status=200,
        )

        result = self.client.search("test query")

        assert len(result.records) == 1
        assert result.records[0].title == "Test Document"
        assert result.records[0].experiment == "ATLAS"

    @responses.activate
    def test_search_with_filters(self):
        """Test search with filters."""
        responses.add(responses.GET, "https://cds.cern.ch/search", json=[], status=200)

        result = self.client.search(
            "test",
            experiment="ATLAS",
            doc_type="Article",
            from_date="2023-01-01",
            until_date="2023-12-31",
        )

        assert len(result.records) == 0

    @responses.activate
    def test_get_record_success(self):
        """Test successful record retrieval."""
        mock_record = {
            "recid": 123456,
            "title": {"title": "Test Document"},
            "authors": [{"full_name": "Test Author"}],
            "accelerator_experiment": [{"experiment": "ATLAS"}],
            "collection": [{"primary": "ARTICLE"}],
            "creation_date": "2023-01-01",
            "files": [
                {
                    "full_name": "test.pdf",
                    "size": 1024,
                    "magic": ["application/pdf", "PDF document"],
                }
            ],
        }

        responses.add(
            responses.GET, "https://cds.cern.ch/search", json=[mock_record], status=200
        )

        result = self.client.get_record("123456")

        assert result.cds_id == "123456"
        assert result.title == "Test Document"
        assert len(result.files) == 1
        assert result.files[0].name == "test.pdf"

    @responses.activate
    def test_get_record_not_found(self):
        """Test record not found."""
        responses.add(responses.GET, "https://cds.cern.ch/search", json=[], status=200)

        with pytest.raises(CDSClientError, match="Record 999999 not found"):
            self.client.get_record("999999")

    @responses.activate
    def test_get_record_files_success(self):
        """Test successful file retrieval."""
        mock_record = {
            "recid": 123456,
            "title": {"title": "Test Document"},
            "authors": [{"full_name": "Test Author"}],
            "accelerator_experiment": [{"experiment": "ATLAS"}],
            "collection": [{"primary": "ARTICLE"}],
            "creation_date": "2023-01-01",
            "files": [
                {
                    "full_name": "test.pdf",
                    "size": 1024,
                    "magic": ["application/pdf", "PDF document"],
                }
            ],
        }

        responses.add(
            responses.GET, "https://cds.cern.ch/search", json=[mock_record], status=200
        )

        result = self.client.get_record_files("123456")

        assert len(result) == 1
        assert result[0].name == "test.pdf"
        assert result[0].size == 1024

    @responses.activate
    def test_search_network_error(self):
        """Test network error handling."""
        responses.add(
            responses.GET,
            "https://cds.cern.ch/search",
            json={"error": "Network error"},
            status=500,
        )

        with pytest.raises(CDSClientError, match="Failed to search CDS"):
            self.client.search("test")

    def test_custom_base_url(self):
        """Test client with custom base URL."""
        custom_client = CDSClient(base_url="https://custom-cds.example.com/")
        assert custom_client.base_url == "https://custom-cds.example.com"

    @responses.activate
    def test_parse_record_with_list_affiliation(self):
        """Test parsing record with list affiliation."""
        mock_record = {
            "recid": 123456,
            "title": {"title": "Test Document"},
            "authors": [
                {
                    "full_name": "Test Author",
                    "affiliation": ["CERN", "University of Test"],
                }
            ],
            "accelerator_experiment": [{"experiment": "ATLAS"}],
            "collection": [{"primary": "ARTICLE"}],
            "creation_date": "2023-01-01",
            "files": [],
        }

        responses.add(
            responses.GET, "https://cds.cern.ch/search", json=[mock_record], status=200
        )

        result = self.client.get_record("123456")

        assert result.authors[0].affiliation == "CERN, University of Test"
