"""Tests for CDS client functionality."""

import pytest
import responses
from datetime import datetime
from unittest.mock import patch

from cds_mcp.cds_client import CDSClient, CDSClientError
from cds_mcp.schema import CDSRecord, CDSFile, CDSAuthor


class TestCDSClient:
    """Test cases for CDSClient."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = CDSClient()
    
    @responses.activate
    def test_search_success(self):
        """Test successful search operation."""
        mock_response = {
            "hits": {
                "total": 1,
                "hits": [
                    {
                        "id": "123456",
                        "metadata": {
                            "title": {"title": "Test Document"},
                            "authors": [
                                {"full_name": "John Doe", "affiliation": {"value": "CERN"}}
                            ],
                            "creation_date": "2023-01-01T00:00:00Z",
                            "modification_date": "2023-01-02T00:00:00Z",
                            "experiment": [{"value": "ATLAS"}],
                            "document_type": [{"value": "Article"}],
                            "abstract": {"summary": "Test abstract"},
                        },
                        "access": {"record": "public"},
                        "files": [],
                    }
                ]
            }
        }
        
        responses.add(
            responses.GET,
            "https://cds.cern.ch/api/records",
            json=mock_response,
            status=200
        )
        
        result = self.client.search("test query")
        
        assert result.total == 1
        assert len(result.records) == 1
        assert result.records[0].title == "Test Document"
        assert result.records[0].experiment == "ATLAS"
    
    @responses.activate
    def test_search_with_filters(self):
        """Test search with filters."""
        responses.add(
            responses.GET,
            "https://cds.cern.ch/api/records",
            json={"hits": {"total": 0, "hits": []}},
            status=200
        )
        
        self.client.search(
            query="higgs",
            experiment="ATLAS",
            doc_type="Article",
            from_date="2023-01-01",
            until_date="2023-12-31"
        )
        
        # Verify the request was made with correct parameters
        assert len(responses.calls) == 1
        request_url = responses.calls[0].request.url
        assert "q=higgs" in request_url
        assert "f=experiment%3AATLAS" in request_url
    
    @responses.activate
    def test_get_record_success(self):
        """Test successful record retrieval."""
        mock_response = {
            "id": "123456",
            "metadata": {
                "title": {"title": "Test Document"},
                "authors": [{"full_name": "Jane Smith"}],
                "creation_date": "2023-01-01T00:00:00Z",
                "modification_date": "2023-01-02T00:00:00Z",
            },
            "access": {"record": "public"},
            "files": [
                {
                    "key": "document.pdf",
                    "size": 1024,
                    "checksum": "abc123",
                    "mimetype": "application/pdf"
                }
            ],
        }
        
        responses.add(
            responses.GET,
            "https://cds.cern.ch/api/records/123456",
            json=mock_response,
            status=200
        )
        
        result = self.client.get_record("123456")
        
        assert result.cds_id == "123456"
        assert result.title == "Test Document"
        assert len(result.files) == 1
        assert result.files[0].name == "document.pdf"
    
    @responses.activate
    def test_get_record_not_found(self):
        """Test record not found error."""
        responses.add(
            responses.GET,
            "https://cds.cern.ch/api/records/999999",
            status=404
        )
        
        with pytest.raises(CDSClientError, match="Record 999999 not found"):
            self.client.get_record("999999")
    
    @responses.activate
    def test_get_record_files_success(self):
        """Test successful file retrieval."""
        mock_response = {
            "entries": [
                {
                    "key": "paper.pdf",
                    "size": 2048,
                    "checksum": "def456",
                    "mimetype": "application/pdf"
                },
                {
                    "key": "slides.pptx",
                    "size": 4096,
                    "checksum": "ghi789",
                    "mimetype": "application/vnd.openxmlformats-officedocument.presentationml.presentation"
                }
            ]
        }
        
        responses.add(
            responses.GET,
            "https://cds.cern.ch/api/records/123456/files",
            json=mock_response,
            status=200
        )
        
        result = self.client.get_record_files("123456")
        
        assert len(result) == 2
        assert result[0].name == "paper.pdf"
        assert result[0].size == 2048
        assert result[1].name == "slides.pptx"
    
    def test_parse_date_formats(self):
        """Test date parsing with different formats."""
        # Test ISO format with microseconds
        date1 = self.client._parse_date("2023-01-01T12:30:45.123456Z")
        assert date1.year == 2023
        assert date1.month == 1
        assert date1.day == 1
        
        # Test ISO format without microseconds
        date2 = self.client._parse_date("2023-01-01T12:30:45Z")
        assert date2.year == 2023
        
        # Test date only
        date3 = self.client._parse_date("2023-01-01")
        assert date3.year == 2023
        
        # Test year only
        date4 = self.client._parse_date("2023")
        assert date4.year == 2023
        
        # Test invalid date (should return current time)
        date5 = self.client._parse_date("invalid")
        assert isinstance(date5, datetime)
    
    @responses.activate
    def test_search_network_error(self):
        """Test search with network error."""
        responses.add(
            responses.GET,
            "https://cds.cern.ch/api/records",
            body=Exception("Network error")
        )
        
        with pytest.raises(CDSClientError, match="Failed to search CDS"):
            self.client.search("test")
    
    def test_custom_base_url(self):
        """Test client with custom base URL."""
        custom_client = CDSClient(base_url="https://custom-cds.example.com/")
        assert custom_client.base_url == "https://custom-cds.example.com"
        assert custom_client.api_base == "https://custom-cds.example.com/api"
