"""Tests for schema models."""

from datetime import datetime

from cds_mcp.schema import CDSAuthor, CDSFile, CDSRecord, CDSSearchResponse


class TestCDSFile:
    """Test cases for CDSFile model."""

    def test_cds_file_basic(self):
        """Test basic CDSFile creation."""
        file = CDSFile(name="document.pdf")

        assert file.name == "document.pdf"
        assert file.size is None
        assert file.checksum is None
        assert file.mime_type is None
        assert file.size_mb is None

    def test_cds_file_with_size(self):
        """Test CDSFile with size calculation."""
        file = CDSFile(
            name="large_document.pdf",
            size=5242880,  # 5 MB
            checksum="abc123",
            mime_type="application/pdf",
        )

        assert file.name == "large_document.pdf"
        assert file.size == 5242880
        assert file.size_mb == 5.0
        assert file.checksum == "abc123"
        assert file.mime_type == "application/pdf"


class TestCDSAuthor:
    """Test cases for CDSAuthor model."""

    def test_cds_author_basic(self):
        """Test basic CDSAuthor creation."""
        author = CDSAuthor(name="John Doe")

        assert author.name == "John Doe"
        assert author.affiliation is None
        assert author.orcid is None

    def test_cds_author_full(self):
        """Test CDSAuthor with all fields."""
        author = CDSAuthor(
            name="Jane Smith", affiliation="CERN", orcid="0000-0000-0000-0000"
        )

        assert author.name == "Jane Smith"
        assert author.affiliation == "CERN"
        assert author.orcid == "0000-0000-0000-0000"


class TestCDSRecord:
    """Test cases for CDSRecord model."""

    def test_cds_record_basic(self):
        """Test basic CDSRecord creation."""
        record = CDSRecord(
            cds_id="123456",
            title="Test Document",
            created=datetime(2023, 1, 1),
            updated=datetime(2023, 1, 2),
        )

        assert record.cds_id == "123456"
        assert record.title == "Test Document"
        assert record.mcp_id == "cds:123456"
        assert record.cds_url == "https://cds.cern.ch/record/123456"
        assert record.doc_type == "unknown"
        assert record.public is True
        assert len(record.authors) == 0
        assert len(record.files) == 0

    def test_cds_record_with_authors_and_files(self):
        """Test CDSRecord with authors and files."""
        authors = [
            CDSAuthor(name="John Doe", affiliation="CERN"),
            CDSAuthor(name="Jane Smith", affiliation="MIT"),
        ]

        files = [
            CDSFile(name="paper.pdf", size=1024),
            CDSFile(name="slides.pptx", size=2048),
        ]

        record = CDSRecord(
            cds_id="789012",
            title="Advanced Research",
            authors=authors,
            files=files,
            experiment="ATLAS",
            doc_type="Article",
            created=datetime(2023, 6, 1),
            updated=datetime(2023, 6, 2),
            abstract="This is a test abstract",
            keywords=["physics", "higgs"],
            subjects=["particle physics"],
            doi="10.1000/test.doi",
            arxiv_id="2306.12345",
        )

        assert len(record.authors) == 2
        assert len(record.files) == 2
        assert record.author_names == ["John Doe", "Jane Smith"]
        assert record.experiment == "ATLAS"
        assert record.doc_type == "Article"
        assert record.abstract == "This is a test abstract"
        assert record.keywords == ["physics", "higgs"]
        assert record.subjects == ["particle physics"]
        assert record.doi == "10.1000/test.doi"
        assert record.arxiv_id == "2306.12345"

    def test_to_mcp_dict(self):
        """Test conversion to MCP dictionary format."""
        record = CDSRecord(
            cds_id="123456",
            title="Test Document",
            authors=[CDSAuthor(name="John Doe")],
            experiment="CMS",
            doc_type="Report",
            created=datetime(2023, 1, 1, 12, 0, 0),
            updated=datetime(2023, 1, 2, 14, 30, 0),
            files=[CDSFile(name="doc.pdf")],
            keywords=["test", "example"],
        )

        mcp_dict = record.to_mcp_dict()

        assert mcp_dict["mcp_id"] == "cds:123456"
        assert mcp_dict["cds_id"] == "123456"
        assert mcp_dict["title"] == "Test Document"
        assert mcp_dict["authors"] == ["John Doe"]
        assert mcp_dict["experiment"] == "CMS"
        assert mcp_dict["doc_type"] == "Report"
        assert mcp_dict["created"] == "2023-01-01T12:00:00"
        assert mcp_dict["updated"] == "2023-01-02T14:30:00"
        assert mcp_dict["url"] == "https://cds.cern.ch/record/123456"
        assert mcp_dict["file_count"] == 1
        assert mcp_dict["keywords"] == ["test", "example"]

    def test_to_mcp_dict_long_abstract(self):
        """Test MCP dict with long abstract truncation."""
        long_abstract = "A" * 250  # 250 characters

        record = CDSRecord(
            cds_id="123456",
            title="Test Document",
            abstract=long_abstract,
            created=datetime(2023, 1, 1),
            updated=datetime(2023, 1, 2),
        )

        mcp_dict = record.to_mcp_dict()

        # Should be truncated to 200 chars + "..."
        assert len(mcp_dict["abstract"]) == 203
        assert mcp_dict["abstract"].endswith("...")

    def test_to_detailed_dict(self):
        """Test conversion to detailed dictionary format."""
        record = CDSRecord(
            cds_id="123456",
            title="Test Document",
            authors=[
                CDSAuthor(
                    name="John Doe", affiliation="CERN", orcid="0000-0000-0000-0000"
                )
            ],
            files=[CDSFile(name="doc.pdf", size=1024, checksum="abc123")],
            abstract="Full abstract text here",
            created=datetime(2023, 1, 1),
            updated=datetime(2023, 1, 2),
        )

        detailed_dict = record.to_detailed_dict()

        # Should include full abstract
        assert detailed_dict["abstract"] == "Full abstract text here"

        # Should include detailed author info
        assert len(detailed_dict["authors_detailed"]) == 1
        author_detail = detailed_dict["authors_detailed"][0]
        assert author_detail["name"] == "John Doe"
        assert author_detail["affiliation"] == "CERN"
        assert author_detail["orcid"] == "0000-0000-0000-0000"

        # Should include detailed file info
        assert len(detailed_dict["files"]) == 1
        file_detail = detailed_dict["files"][0]
        assert file_detail["name"] == "doc.pdf"
        assert file_detail["size_bytes"] == 1024
        assert file_detail["size_mb"] == 0.0
        assert file_detail["checksum"] == "abc123"
        assert file_detail["url"] == "https://cds.cern.ch/record/123456/files/doc.pdf"


class TestCDSSearchResponse:
    """Test cases for CDSSearchResponse model."""

    def test_search_response_basic(self):
        """Test basic CDSSearchResponse creation."""
        records = [
            CDSRecord(
                cds_id="123456",
                title="Document 1",
                created=datetime(2023, 1, 1),
                updated=datetime(2023, 1, 2),
            ),
            CDSRecord(
                cds_id="789012",
                title="Document 2",
                created=datetime(2023, 2, 1),
                updated=datetime(2023, 2, 2),
            ),
        ]

        response = CDSSearchResponse(total=10, records=records)

        assert response.total == 10
        assert len(response.records) == 2
        assert response.facets is None

    def test_search_response_with_facets(self):
        """Test CDSSearchResponse with facets."""
        records = [
            CDSRecord(
                cds_id="123456",
                title="Document 1",
                created=datetime(2023, 1, 1),
                updated=datetime(2023, 1, 2),
            )
        ]

        facets = {
            "experiment": {
                "buckets": [
                    {"key": "ATLAS", "doc_count": 5},
                    {"key": "CMS", "doc_count": 3},
                ]
            }
        }

        response = CDSSearchResponse(total=8, records=records, facets=facets)

        assert response.total == 8
        assert len(response.records) == 1
        assert response.facets == facets

    def test_to_mcp_dict(self):
        """Test conversion to MCP dictionary format."""
        records = [
            CDSRecord(
                cds_id="123456",
                title="Document 1",
                created=datetime(2023, 1, 1),
                updated=datetime(2023, 1, 2),
            )
        ]

        response = CDSSearchResponse(total=5, records=records)
        mcp_dict = response.to_mcp_dict()

        assert mcp_dict["total_results"] == 5
        assert mcp_dict["returned_count"] == 1
        assert len(mcp_dict["documents"]) == 1
        assert mcp_dict["documents"][0]["mcp_id"] == "cds:123456"
        assert mcp_dict["facets"] is None
