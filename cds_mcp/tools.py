"""MCP tool definitions for CDS operations."""

import logging
import os
from typing import Any

from .cds_client import CDSClient, CDSClientError
from .auth import is_authenticated

logger = logging.getLogger(__name__)


def search_cds_documents(
    query: str,
    experiment: str | None = None,
    doc_type: str | None = None,
    from_date: str | None = None,
    until_date: str | None = None,
    size: int = 10,
    sort: str = "mostrecent",
) -> dict[str, Any]:
    """Search CDS documents with various filters.

    Args:
        query: Search query string (required)
        experiment: Filter by experiment (e.g., "ATLAS", "CMS", "LHCb", "ALICE")
        doc_type: Filter by document type (e.g., "Article", "Thesis", "Report")
        from_date: Start date filter in YYYY-MM-DD format
        until_date: End date filter in YYYY-MM-DD format
        size: Number of results to return (max 100, default 10)
        sort: Sort order - "mostrecent", "bestmatch", or "mostcited"

    Returns:
        Dictionary containing search results and metadata
    """
    try:
        # Modern CERN SSO authentication
        client = CDSClient(use_authentication=True)
        search_response = client.search(
            query=query,
            experiment=experiment,
            doc_type=doc_type,
            from_date=from_date,
            until_date=until_date,
            size=size,
            sort=sort,
        )

        result = search_response.to_mcp_dict()

        # Add search parameters for context
        result["search_parameters"] = {
            "query": query,
            "experiment": experiment,
            "doc_type": doc_type,
            "from_date": from_date,
            "until_date": until_date,
            "size": size,
            "sort": sort,
        }

        logger.info(
            f"Search completed: {result['returned_count']} of {result['total_results']} results"
        )
        return result

    except CDSClientError as e:
        logger.error(f"CDS search failed: {e}")
        return {
            "error": str(e),
            "total_results": 0,
            "returned_count": 0,
            "documents": [],
            "search_parameters": {
                "query": query,
                "experiment": experiment,
                "doc_type": doc_type,
                "from_date": from_date,
                "until_date": until_date,
                "size": size,
                "sort": sort,
            },
        }


def get_cds_document_details(mcp_id: str) -> dict[str, Any]:
    """Get detailed information about a specific CDS document.

    Args:
        mcp_id: MCP ID of the document (format: "cds:123456")

    Returns:
        Dictionary containing detailed document information
    """
    try:
        # Extract CDS ID from MCP ID
        if not mcp_id.startswith("cds:"):
            return {
                "error": f"Invalid MCP ID format: {mcp_id}. Expected format: 'cds:123456'"
            }

        cds_id = mcp_id.split(":", 1)[1]

        # Modern CERN SSO authentication
        client = CDSClient(use_authentication=True)
        record = client.get_record(cds_id)

        result = record.to_detailed_dict()
        logger.info(f"Retrieved detailed information for record {cds_id}")
        return result

    except CDSClientError as e:
        logger.error(f"Failed to get document details for {mcp_id}: {e}")
        return {
            "error": str(e),
            "mcp_id": mcp_id,
        }


def get_cds_document_files(mcp_id: str) -> dict[str, Any]:
    """Get file information for a specific CDS document.

    Args:
        mcp_id: MCP ID of the document (format: "cds:123456")

    Returns:
        Dictionary containing file information and download URLs
    """
    try:
        # Extract CDS ID from MCP ID
        if not mcp_id.startswith("cds:"):
            return {
                "error": f"Invalid MCP ID format: {mcp_id}. Expected format: 'cds:123456'"
            }

        cds_id = mcp_id.split(":", 1)[1]

        # Modern CERN SSO authentication
        client = CDSClient(use_authentication=True)
        files = client.get_record_files(cds_id)

        result = {
            "mcp_id": mcp_id,
            "cds_id": cds_id,
            "file_count": len(files),
            "files": [
                {
                    "name": file.name,
                    "size_bytes": file.size,
                    "size_mb": file.size_mb,
                    "checksum": file.checksum,
                    "mime_type": file.mime_type,
                    "download_url": f"https://cds.cern.ch/record/{cds_id}/files/{file.name}",
                }
                for file in files
            ],
            "base_url": f"https://cds.cern.ch/record/{cds_id}",
        }

        logger.info(f"Retrieved {len(files)} files for record {cds_id}")
        return result

    except CDSClientError as e:
        logger.error(f"Failed to get files for {mcp_id}: {e}")
        return {
            "error": str(e),
            "mcp_id": mcp_id,
            "file_count": 0,
            "files": [],
        }


def get_cds_experiments() -> dict[str, Any]:
    """Get a list of common CERN experiments for filtering.

    Returns:
        Dictionary containing experiment information
    """
    experiments = {
        "LHC Experiments": [
            {"name": "ATLAS", "description": "A Toroidal LHC ApparatuS"},
            {"name": "CMS", "description": "Compact Muon Solenoid"},
            {"name": "LHCb", "description": "Large Hadron Collider beauty"},
            {"name": "ALICE", "description": "A Large Ion Collider Experiment"},
        ],
        "Other Experiments": [
            {"name": "NA61", "description": "NA61/SHINE"},
            {"name": "NA62", "description": "NA62 experiment"},
            {
                "name": "COMPASS",
                "description": "Common Muon and Proton Apparatus for Structure and Spectroscopy",
            },
            {"name": "nTOF", "description": "Neutron Time-of-Flight facility"},
        ],
        "Theoretical": [
            {"name": "TH", "description": "Theoretical Physics"},
            {"name": "LPCC", "description": "LHC Physics Centre at CERN"},
        ],
    }

    return {
        "experiments": experiments,
        "usage_note": "Use experiment names (e.g., 'ATLAS', 'CMS') as filters in search_cds_documents",
    }


def get_cds_document_types() -> dict[str, Any]:
    """Get a list of common CDS document types for filtering.

    Returns:
        Dictionary containing document type information
    """
    doc_types = {
        "Publications": [
            {"type": "Article", "description": "Journal articles and papers"},
            {
                "type": "Conference Paper",
                "description": "Conference proceedings and presentations",
            },
            {"type": "Preprint", "description": "Preprints and draft papers"},
        ],
        "Reports": [
            {"type": "Report", "description": "Technical reports and documentation"},
            {"type": "Internal Note", "description": "Internal collaboration notes"},
            {"type": "Public Note", "description": "Public notes and documentation"},
        ],
        "Academic": [
            {"type": "Thesis", "description": "PhD theses and dissertations"},
            {"type": "Lecture", "description": "Lectures and educational material"},
        ],
        "Other": [
            {"type": "Book", "description": "Books and monographs"},
            {"type": "Poster", "description": "Conference posters"},
            {"type": "Slides", "description": "Presentation slides"},
        ],
    }

    return {
        "document_types": doc_types,
        "usage_note": "Use document type names (e.g., 'Article', 'Thesis') as filters in search_cds_documents",
    }


# Tool registry for MCP server
MCP_TOOLS = {
    "search_cds_documents": {
        "function": search_cds_documents,
        "description": "Search CDS documents with various filters including experiment, document type, and date range",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query string (required)",
                },
                "experiment": {
                    "type": "string",
                    "description": "Filter by experiment (e.g., 'ATLAS', 'CMS', 'LHCb', 'ALICE')",
                },
                "doc_type": {
                    "type": "string",
                    "description": "Filter by document type (e.g., 'Article', 'Thesis', 'Report')",
                },
                "from_date": {
                    "type": "string",
                    "description": "Start date filter in YYYY-MM-DD format",
                },
                "until_date": {
                    "type": "string",
                    "description": "End date filter in YYYY-MM-DD format",
                },
                "size": {
                    "type": "integer",
                    "description": "Number of results to return (max 100, default 10)",
                    "default": 10,
                },
                "sort": {
                    "type": "string",
                    "description": "Sort order: 'mostrecent', 'bestmatch', or 'mostcited'",
                    "enum": ["mostrecent", "bestmatch", "mostcited"],
                    "default": "mostrecent",
                },
            },
            "required": ["query"],
        },
    },
    "get_cds_document_details": {
        "function": get_cds_document_details,
        "description": "Get detailed information about a specific CDS document including full abstract, authors, and metadata",
        "parameters": {
            "type": "object",
            "properties": {
                "mcp_id": {
                    "type": "string",
                    "description": "MCP ID of the document (format: 'cds:123456')",
                },
            },
            "required": ["mcp_id"],
        },
    },
    "get_cds_document_files": {
        "function": get_cds_document_files,
        "description": "Get file information and download URLs for a specific CDS document",
        "parameters": {
            "type": "object",
            "properties": {
                "mcp_id": {
                    "type": "string",
                    "description": "MCP ID of the document (format: 'cds:123456')",
                },
            },
            "required": ["mcp_id"],
        },
    },
    "get_cds_experiments": {
        "function": get_cds_experiments,
        "description": "Get a list of common CERN experiments that can be used for filtering searches",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    "get_cds_document_types": {
        "function": get_cds_document_types,
        "description": "Get a list of common CDS document types that can be used for filtering searches",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
}
