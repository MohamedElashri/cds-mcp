"""CDS API client for interacting with CERN Document Server."""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import urlencode

import requests
from pydantic import ValidationError

from .schema import CDSRecord, CDSFile, CDSAuthor, CDSSearchResponse

logger = logging.getLogger(__name__)


class CDSClientError(Exception):
    """Base exception for CDS client errors."""
    pass


class CDSClient:
    """Client for interacting with the CDS (Invenio) REST API."""
    
    def __init__(self, base_url: str = "https://cds.cern.ch", session_cookie: Optional[str] = None):
        """Initialize the CDS client.
        
        Args:
            base_url: Base URL for the CDS instance (default: https://cds.cern.ch)
            session_cookie: Optional INVENIOSESSION cookie for authenticated access
                          (WORKAROUND: This is a temporary solution for accessing restricted content.
                           A proper authentication mechanism is being developed.)
        """
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "cds-mcp/0.1.0",
            "Accept": "application/json",
        })
        
        # Add session cookie if provided (workaround for authentication)
        if session_cookie:
            self.session.cookies.set("INVENIOSESSION", session_cookie, domain="cds.cern.ch")
    
    def search(
        self,
        query: str,
        experiment: Optional[str] = None,
        doc_type: Optional[str] = None,
        from_date: Optional[str] = None,
        until_date: Optional[str] = None,
        size: int = 10,
        page: int = 1,
        sort: str = "mostrecent",
    ) -> CDSSearchResponse:
        """Search CDS records.
        
        Args:
            query: Search query string
            experiment: Filter by experiment (e.g., "ATLAS", "CMS", "LHCb", "ALICE")
            doc_type: Filter by document type (e.g., "Article", "Thesis", "Report")
            from_date: Start date filter (YYYY-MM-DD format)
            until_date: End date filter (YYYY-MM-DD format)
            size: Number of results per page (max 100)
            page: Page number (1-based)
            sort: Sort order ("mostrecent", "bestmatch", "mostcited")
            
        Returns:
            CDSSearchResponse containing search results
            
        Raises:
            CDSClientError: If the API request fails
        """
        # Build search query with filters
        search_query = query
        if experiment:
            search_query += f" AND experiment:{experiment}"
        if doc_type:
            search_query += f" AND collection:{doc_type}"
        if from_date:
            search_query += f" AND year:{from_date[:4]}-"
            if until_date:
                search_query += until_date[:4]
        
        params = {
            "p": search_query,
            "of": "recjson",
            "rg": min(size, 100),  # CDS API limit
            "jrec": ((page - 1) * size) + 1,  # Starting record number
        }
        
        # Map sort options to CDS format
        sort_map = {
            "mostrecent": "d",  # date descending
            "bestmatch": "r",   # relevance
            "mostcited": "c",   # citation count
        }
        if sort in sort_map:
            params["sf"] = sort_map[sort]
        
        try:
            response = self.session.get(f"{self.base_url}/search", params=params)
            response.raise_for_status()
            data = response.json()
            
            # CDS returns a list of records directly
            records = []
            if isinstance(data, list):
                for record_data in data:
                    try:
                        record = self._parse_record(record_data)
                        records.append(record)
                    except ValidationError as e:
                        logger.warning(f"Failed to parse record {record_data.get('recid', 'unknown')}: {e}")
                        continue
            
            # For total count, we need to make a separate request
            total_count = len(records)  # Simplified for now
            
            return CDSSearchResponse(
                total=total_count,
                records=records,
                facets=None,  # CDS doesn't provide facets in this format
            )
            
        except requests.RequestException as e:
            raise CDSClientError(f"Failed to search CDS: {e}") from e
    
    def get_record(self, cds_id: str) -> CDSRecord:
        """Get a specific CDS record by ID.
        
        Args:
            cds_id: CDS record ID
            
        Returns:
            CDSRecord object
            
        Raises:
            CDSClientError: If the record is not found or API request fails
        """
        try:
            params = {
                "p": f"recid:{cds_id}",
                "of": "recjson",
                "rg": 1,
            }
            response = self.session.get(f"{self.base_url}/search", params=params)
            response.raise_for_status()
            data = response.json()
            
            if isinstance(data, list) and len(data) > 0:
                return self._parse_record(data[0])
            else:
                raise CDSClientError(f"Record {cds_id} not found")
            
        except requests.RequestException as e:
            if hasattr(e, 'response') and e.response.status_code == 404:
                raise CDSClientError(f"Record {cds_id} not found") from e
            raise CDSClientError(f"Failed to get record {cds_id}: {e}") from e
    
    def get_record_files(self, cds_id: str) -> List[CDSFile]:
        """Get files for a specific CDS record.
        
        Args:
            cds_id: CDS record ID
            
        Returns:
            List of CDSFile objects
            
        Raises:
            CDSClientError: If the record is not found or API request fails
        """
        try:
            # Get the full record first, which includes file information
            record = self.get_record(cds_id)
            return record.files
            
        except CDSClientError:
            raise
        except Exception as e:
            raise CDSClientError(f"Failed to get files for record {cds_id}: {e}") from e
    
    def _parse_record(self, data: Dict[str, Any]) -> CDSRecord:
        """Parse a CDS record from API response data.
        
        Args:
            data: Raw record data from CDS API
            
        Returns:
            CDSRecord object
        """
        # Parse authors
        authors = []
        for author_data in data.get("authors", []):
            # Handle affiliation which can be a string or list
            affiliation = author_data.get("affiliation")
            if isinstance(affiliation, list):
                affiliation = ", ".join(affiliation) if affiliation else None
            
            author = CDSAuthor(
                name=author_data.get("full_name", ""),
                affiliation=affiliation,
                orcid=None,  # Not typically in CDS format
            )
            authors.append(author)
        
        # Parse files
        files = []
        for file_data in data.get("files", []):
            file_obj = CDSFile(
                name=file_data.get("full_name", file_data.get("name", "")),
                size=file_data.get("size"),
                checksum=None,  # Not in the format we saw
                mime_type=file_data.get("magic", [""])[1] if isinstance(file_data.get("magic"), list) and len(file_data.get("magic", [])) > 1 else None,
            )
            files.append(file_obj)
        
        # Parse dates
        created = self._parse_date(data.get("creation_date"))
        updated = self._parse_date(data.get("version_id", data.get("creation_date")))
        
        # Extract experiment and document type
        experiment = None
        doc_type = "unknown"
        
        # Extract experiment from accelerator_experiment field
        if "accelerator_experiment" in data:
            exp_data = data["accelerator_experiment"]
            if isinstance(exp_data, list) and exp_data:
                experiment = exp_data[0].get("experiment")
        
        # Extract document type from collection field
        if "collection" in data:
            collections = data["collection"]
            if isinstance(collections, list) and collections:
                # Look for primary collection
                for coll in collections:
                    if isinstance(coll, dict) and coll.get("primary"):
                        doc_type = coll["primary"]
                        break
        
        # Extract keywords and subjects
        keywords = []
        subjects = []
        
        # Subject field handling
        if "subject" in data:
            subject_data = data["subject"]
            if isinstance(subject_data, dict):
                subjects.append(subject_data.get("term", ""))
            elif isinstance(subject_data, list):
                for subj in subject_data:
                    if isinstance(subj, dict):
                        subjects.append(subj.get("term", ""))
                    else:
                        subjects.append(str(subj))
        
        # Extract abstract
        abstract = None
        if "abstract" in data:
            abstract_data = data["abstract"]
            if isinstance(abstract_data, dict):
                abstract = abstract_data.get("summary", "")
            elif isinstance(abstract_data, str):
                abstract = abstract_data
        
        # Extract title
        title = ""
        if "title" in data:
            title_data = data["title"]
            if isinstance(title_data, dict):
                title = title_data.get("title", "")
            elif isinstance(title_data, str):
                title = title_data
        
        return CDSRecord(
            cds_id=str(data.get("recid", "")),
            title=title,
            authors=authors,
            abstract=abstract,
            experiment=experiment,
            doc_type=doc_type,
            created=created,
            updated=updated,
            public=True,  # Assume public if we can access it
            files=files,
            keywords=keywords,
            subjects=subjects,
            doi=data.get("doi"),
            arxiv_id=None,  # Would need to parse from system_control_number if present
        )
    
    def _parse_date(self, date_str: Optional[str]) -> datetime:
        """Parse a date string from CDS API.
        
        Args:
            date_str: Date string from API
            
        Returns:
            datetime object
        """
        if not date_str:
            return datetime.now()
        
        # Try different date formats used by CDS
        formats = [
            "%Y-%m-%dT%H:%M:%S.%fZ",  # ISO format with microseconds
            "%Y-%m-%dT%H:%M:%SZ",     # ISO format
            "%Y-%m-%d",               # Date only
            "%Y",                     # Year only
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # Fallback: try to parse just the year
        try:
            year = int(date_str[:4])
            return datetime(year, 1, 1)
        except (ValueError, IndexError):
            return datetime.now()
