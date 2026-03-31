"""Pydantic models and schema definitions for CDS records."""

from datetime import datetime

from pydantic import BaseModel, Field, computed_field


class CDSFile(BaseModel):
    """Represents a file attached to a CDS record."""

    name: str
    size: int | None = None
    checksum: str | None = None
    mime_type: str | None = None

    @computed_field
    def size_mb(self) -> float | None:
        """File size in megabytes."""
        if self.size is None:
            return None
        return round(self.size / (1024 * 1024), 2)


class CDSAuthor(BaseModel):
    """Represents an author of a CDS record."""

    name: str | None = None
    affiliation: str | None = None
    orcid: str | None = None


class CDSRecord(BaseModel):
    """Represents a CDS record with all relevant metadata."""

    cds_id: str = Field(description="CDS record ID")
    title: str
    authors: list[CDSAuthor] = Field(default_factory=list)
    abstract: str | None = None
    experiment: str | None = None
    doc_type: str = Field(default="unknown")
    created: datetime
    updated: datetime
    public: bool = True
    files: list[CDSFile] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    subjects: list[str] = Field(default_factory=list)
    doi: str | None = None
    arxiv_id: str | None = None

    @computed_field
    def mcp_id(self) -> str:
        """Generate a deterministic MCP ID for this record."""
        return f"cds:{self.cds_id}"

    @computed_field
    def cds_url(self) -> str:
        """Generate the CDS URL for this record."""
        return f"https://cds.cern.ch/record/{self.cds_id}"

    @computed_field
    def author_names(self) -> list[str]:
        """Extract just the author names."""
        return [author.name or "Unknown" for author in self.authors]

    def to_mcp_dict(self) -> dict:
        """Convert to a dictionary suitable for MCP tool responses."""
        return {
            "mcp_id": self.mcp_id,
            "cds_id": self.cds_id,
            "title": self.title,
            "authors": self.author_names,
            "abstract": self.abstract[:200] + "..."
            if self.abstract and len(self.abstract) > 200
            else self.abstract,
            "experiment": self.experiment,
            "doc_type": self.doc_type,
            "created": self.created.isoformat(),
            "updated": self.updated.isoformat(),
            "url": self.cds_url,
            "file_count": len(self.files),
            "keywords": self.keywords,
            "subjects": self.subjects,
            "doi": self.doi,
            "arxiv_id": self.arxiv_id,
        }

    def to_detailed_dict(self) -> dict:
        """Convert to a detailed dictionary with all information."""
        return {
            **self.to_mcp_dict(),
            "abstract": self.abstract,  # Full abstract
            "authors_detailed": [
                {
                    "name": author.name,
                    "affiliation": author.affiliation,
                    "orcid": author.orcid,
                }
                for author in self.authors
            ],
            "files": [
                {
                    "name": file.name,
                    "size_bytes": file.size,
                    "size_mb": file.size_mb,
                    "checksum": file.checksum,
                    "mime_type": file.mime_type,
                    "url": f"{self.cds_url}/files/{file.name}",
                }
                for file in self.files
            ],
        }


class CDSSearchResponse(BaseModel):
    """Represents a search response from CDS API."""

    total: int
    records: list[CDSRecord]
    facets: dict | None = None

    def to_mcp_dict(self) -> dict:
        """Convert search response to MCP format."""
        return {
            "total_results": self.total,
            "returned_count": len(self.records),
            "documents": [record.to_mcp_dict() for record in self.records],
            "facets": self.facets,
        }


class CDSCollection(BaseModel):
    """Represents a CDS collection."""

    name: str = Field(
        description="Internal collection name (used in search or 'cc' parameter)"
    )
    display_name: str = Field(description="Human-readable name of the collection")
    subcollections: list["CDSCollection"] = Field(
        default_factory=list,
        description="List of sub-collections within this collection",
    )


# Resolve forward references for recursive model
CDSCollection.model_rebuild()


class CDSCollectionResponse(BaseModel):
    """Response containing a list of CDS collections."""

    collections: list[CDSCollection]
