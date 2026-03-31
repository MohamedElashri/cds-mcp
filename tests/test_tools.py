"""Tests for MCP tools functionality."""

import pytest
from unittest.mock import patch, MagicMock

from cds_mcp.tools import (
    search_cds_documents,
    get_cds_document_details,
    get_cds_document_files,
    get_cds_experiments,
    get_cds_document_types,
)
from cds_mcp.cds_client import CDSClientError
from cds_mcp.schema import CDSRecord, CDSFile, CDSAuthor, CDSSearchResponse


class TestTools:
    """Test cases for MCP tools."""
    
    @patch('cds_mcp.tools.CDSClient')
    def test_search_cds_documents_success(self, mock_client_class):
        """Test successful document search."""
        # Mock the client and its methods
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Create mock search response
        mock_record = CDSRecord(
            cds_id="123456",
            title="Test Document",
            authors=[CDSAuthor(name="John Doe")],
            experiment="ATLAS",
            doc_type="Article",
            created="2023-01-01T00:00:00Z",
            updated="2023-01-02T00:00:00Z",
        )
        
        mock_search_response = CDSSearchResponse(
            total=1,
            records=[mock_record]
        )
        
        mock_client.search.return_value = mock_search_response
        
        # Call the tool
        result = search_cds_documents(
            query="higgs boson",
            experiment="ATLAS",
            doc_type="Article",
            size=5
        )
        
        # Verify the result
        assert result["total_results"] == 1
        assert result["returned_count"] == 1
        assert len(result["documents"]) == 1
        assert result["documents"][0]["title"] == "Test Document"
        assert result["search_parameters"]["query"] == "higgs boson"
        assert result["search_parameters"]["experiment"] == "ATLAS"
        
        # Verify the client was called correctly
        mock_client.search.assert_called_once_with(
            query="higgs boson",
            experiment="ATLAS",
            doc_type="Article",
            from_date=None,
            until_date=None,
            size=5,
            sort="mostrecent"
        )
    
    @patch('cds_mcp.tools.CDSClient')
    def test_search_cds_documents_error(self, mock_client_class):
        """Test document search with error."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.search.side_effect = CDSClientError("API error")
        
        result = search_cds_documents(query="test")
        
        assert "error" in result
        assert result["error"] == "API error"
        assert result["total_results"] == 0
        assert result["returned_count"] == 0
        assert result["documents"] == []
    
    @patch('cds_mcp.tools.CDSClient')
    def test_get_cds_document_details_success(self, mock_client_class):
        """Test successful document details retrieval."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_record = CDSRecord(
            cds_id="123456",
            title="Test Document",
            authors=[CDSAuthor(name="Jane Smith", affiliation="CERN")],
            abstract="This is a test abstract",
            experiment="CMS",
            doc_type="Report",
            created="2023-01-01T00:00:00Z",
            updated="2023-01-02T00:00:00Z",
            files=[CDSFile(name="document.pdf", size=1024)]
        )
        
        mock_client.get_record.return_value = mock_record
        
        result = get_cds_document_details(mcp_id="cds:123456")
        
        assert result["mcp_id"] == "cds:123456"
        assert result["cds_id"] == "123456"
        assert result["title"] == "Test Document"
        assert result["abstract"] == "This is a test abstract"
        assert len(result["authors_detailed"]) == 1
        assert result["authors_detailed"][0]["name"] == "Jane Smith"
        assert result["authors_detailed"][0]["affiliation"] == "CERN"
        
        mock_client.get_record.assert_called_once_with("123456")
    
    def test_get_cds_document_details_invalid_mcp_id(self):
        """Test document details with invalid MCP ID."""
        result = get_cds_document_details(mcp_id="invalid:123456")
        
        assert "error" in result
        assert "Invalid MCP ID format" in result["error"]
        assert result["mcp_id"] == "invalid:123456"
    
    @patch('cds_mcp.tools.CDSClient')
    def test_get_cds_document_details_error(self, mock_client_class):
        """Test document details with client error."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get_record.side_effect = CDSClientError("Record not found")
        
        result = get_cds_document_details(mcp_id="cds:999999")
        
        assert "error" in result
        assert result["error"] == "Record not found"
        assert result["mcp_id"] == "cds:999999"
    
    @patch('cds_mcp.tools.CDSClient')
    def test_get_cds_document_files_success(self, mock_client_class):
        """Test successful document files retrieval."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_files = [
            CDSFile(name="paper.pdf", size=2048, checksum="abc123", mime_type="application/pdf"),
            CDSFile(name="slides.pptx", size=4096, checksum="def456", mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation")
        ]
        
        mock_client.get_record_files.return_value = mock_files
        
        result = get_cds_document_files(mcp_id="cds:123456")
        
        assert result["mcp_id"] == "cds:123456"
        assert result["cds_id"] == "123456"
        assert result["file_count"] == 2
        assert len(result["files"]) == 2
        
        # Check first file
        file1 = result["files"][0]
        assert file1["name"] == "paper.pdf"
        assert file1["size_bytes"] == 2048
        assert file1["size_mb"] == 0.0  # 2048 bytes = 0.002 MB, rounded to 0.0
        assert file1["checksum"] == "abc123"
        assert file1["mime_type"] == "application/pdf"
        assert file1["download_url"] == "https://cds.cern.ch/record/123456/files/paper.pdf"
        
        mock_client.get_record_files.assert_called_once_with("123456")
    
    def test_get_cds_document_files_invalid_mcp_id(self):
        """Test document files with invalid MCP ID."""
        result = get_cds_document_files(mcp_id="wrong:123456")
        
        assert "error" in result
        assert "Invalid MCP ID format" in result["error"]
        assert result["file_count"] == 0
        assert result["files"] == []
    
    @patch('cds_mcp.tools.CDSClient')
    def test_get_cds_document_files_error(self, mock_client_class):
        """Test document files with client error."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get_record_files.side_effect = CDSClientError("Files not accessible")
        
        result = get_cds_document_files(mcp_id="cds:123456")
        
        assert "error" in result
        assert result["error"] == "Files not accessible"
        assert result["file_count"] == 0
        assert result["files"] == []
    
    def test_get_cds_experiments(self):
        """Test experiments list retrieval."""
        result = get_cds_experiments()
        
        assert "experiments" in result
        assert "usage_note" in result
        
        experiments = result["experiments"]
        assert "LHC Experiments" in experiments
        assert "Other Experiments" in experiments
        assert "Theoretical" in experiments
        
        # Check some specific experiments
        lhc_experiments = experiments["LHC Experiments"]
        experiment_names = [exp["name"] for exp in lhc_experiments]
        assert "ATLAS" in experiment_names
        assert "CMS" in experiment_names
        assert "LHCb" in experiment_names
        assert "ALICE" in experiment_names
    
    def test_get_cds_document_types(self):
        """Test document types list retrieval."""
        result = get_cds_document_types()
        
        assert "document_types" in result
        assert "usage_note" in result
        
        doc_types = result["document_types"]
        assert "Publications" in doc_types
        assert "Reports" in doc_types
        assert "Academic" in doc_types
        assert "Other" in doc_types
        
        # Check some specific document types
        publications = doc_types["Publications"]
        pub_types = [dt["type"] for dt in publications]
        assert "Article" in pub_types
        assert "Conference Paper" in pub_types
        assert "Preprint" in pub_types
