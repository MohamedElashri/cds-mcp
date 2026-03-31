"""Pydantic models and schema definitions for CDS records."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, computed_field


class CDSFile(BaseModel):
    """Represents a file attached to a CDS record."""
    
    name: str
    size: Optional[int] = None
    checksum: Optional[str] = None
    mime_type: Optional[str] = None
    
    @computed_field
    @property
    def size_mb(self) -> Optional[float]:
        """File size in megabytes."""
        if self.size is None:
            return None
        return round(self.size / (1024 * 1024), 2)


class CDSAuthor(BaseModel):
    """Represents an author of a CDS record."""
    
    name: str
    affiliation: Optional[str] = None
    orcid: Optional[str] = None


class CDSRecord(BaseModel):
    """Represents a CDS record with all relevant metadata."""
    
    cds_id: str = Field(description="CDS record ID")
    title: str
    authors: List[CDSAuthor] = Field(default_factory=list)
    abstract: Optional[str] = None
    experiment: Optional[str] = None
    doc_type: str = Field(default="unknown")
    created: datetime
    updated: datetime
    public: bool = True
    files: List[CDSFile] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    subjects: List[str] = Field(default_factory=list)
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    
    @computed_field
    @property
    def mcp_id(self) -> str:
        """Generate a deterministic MCP ID for this record."""
        return f"cds:{self.cds_id}"
    
    @computed_field
    @property
    def cds_url(self) -> str:
        """Generate the CDS URL for this record."""
        return f"https://cds.cern.ch/record/{self.cds_id}"
    
    @computed_field
    @property
    def author_names(self) -> List[str]:
        """Extract just the author names."""
        return [author.name for author in self.authors]
    
    def to_mcp_dict(self) -> dict:
        """Convert to a dictionary suitable for MCP tool responses."""
        return {
            "mcp_id": self.mcp_id,
            "cds_id": self.cds_id,
            "title": self.title,
            "authors": self.author_names,
            "abstract": self.abstract[:200] + "..." if self.abstract and len(self.abstract) > 200 else self.abstract,
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
    records: List[CDSRecord]
    facets: Optional[dict] = None
    
    def to_mcp_dict(self) -> dict:
        """Convert search response to MCP format."""
        return {
            "total_results": self.total,
            "returned_count": len(self.records),
            "documents": [record.to_mcp_dict() for record in self.records],
            "facets": self.facets,
        }
