#!/usr/bin/env python3
"""Integration test script to validate CDS API connectivity and tool functionality."""

import json
import sys
from typing import Dict, Any

from cds_mcp.cds_client import CDSClient, CDSClientError
from cds_mcp.tools import (
    search_cds_documents,
    get_cds_document_details,
    get_cds_document_files,
    get_cds_experiments,
    get_cds_document_types,
)


def test_cds_api_connectivity():
    """Test basic CDS API connectivity."""
    print("🔍 Testing CDS API connectivity...")
    
    try:
        client = CDSClient()
        # Try a simple search to test connectivity
        response = client.search("ATLAS", size=1)
        print(f"✅ CDS API is accessible. Found {response.total} total records.")
        return True
    except Exception as e:
        print(f"❌ CDS API connectivity failed: {e}")
        return False


def test_search_functionality():
    """Test search functionality with various queries."""
    print("\n🔍 Testing search functionality...")
    
    test_cases = [
        {
            "name": "Basic search",
            "params": {"query": "ATLAS", "size": 3}
        },
        {
            "name": "Experiment filter",
            "params": {"query": "Higgs", "experiment": "ATLAS", "size": 2}
        },
        {
            "name": "Document type filter", 
            "params": {"query": "physics", "doc_type": "Article", "size": 2}
        },
        {
            "name": "Date range filter",
            "params": {"query": "LHC", "from_date": "2023-01-01", "size": 2}
        }
    ]
    
    results = {}
    for test_case in test_cases:
        try:
            print(f"  Testing: {test_case['name']}")
            result = search_cds_documents(**test_case["params"])
            
            if "error" in result:
                print(f"    ❌ Error: {result['error']}")
                results[test_case["name"]] = False
            else:
                print(f"    ✅ Found {result['returned_count']} of {result['total_results']} documents")
                results[test_case["name"]] = True
                
                # Store first result for later testing
                if result["documents"] and "first_document" not in results:
                    results["first_document"] = result["documents"][0]
                    
        except Exception as e:
            print(f"    ❌ Exception: {e}")
            results[test_case["name"]] = False
    
    return results


def test_document_details(mcp_id: str):
    """Test document details retrieval."""
    print(f"\n🔍 Testing document details for {mcp_id}...")
    
    try:
        result = get_cds_document_details(mcp_id)
        
        if "error" in result:
            print(f"❌ Error getting document details: {result['error']}")
            return False
        else:
            print(f"✅ Retrieved details for: {result.get('title', 'Unknown title')}")
            print(f"   Authors: {len(result.get('authors_detailed', []))} authors")
            print(f"   Files: {len(result.get('files', []))} files")
            return True
            
    except Exception as e:
        print(f"❌ Exception getting document details: {e}")
        return False


def test_document_files(mcp_id: str):
    """Test document files retrieval."""
    print(f"\n🔍 Testing document files for {mcp_id}...")
    
    try:
        result = get_cds_document_files(mcp_id)
        
        if "error" in result:
            print(f"❌ Error getting document files: {result['error']}")
            return False
        else:
            print(f"✅ Found {result['file_count']} files")
            for file_info in result.get("files", [])[:3]:  # Show first 3 files
                print(f"   - {file_info['name']} ({file_info.get('size_mb', 'Unknown')} MB)")
            return True
            
    except Exception as e:
        print(f"❌ Exception getting document files: {e}")
        return False


def test_helper_tools():
    """Test helper tools (experiments and document types)."""
    print("\n🔍 Testing helper tools...")
    
    try:
        # Test experiments
        experiments = get_cds_experiments()
        exp_count = sum(len(exp_list) for exp_list in experiments["experiments"].values())
        print(f"✅ Retrieved {exp_count} experiments")
        
        # Test document types
        doc_types = get_cds_document_types()
        type_count = sum(len(type_list) for type_list in doc_types["document_types"].values())
        print(f"✅ Retrieved {type_count} document types")
        
        return True
        
    except Exception as e:
        print(f"❌ Exception in helper tools: {e}")
        return False


def test_api_response_structure():
    """Test and analyze actual API response structure."""
    print("\n🔍 Analyzing CDS API response structure...")
    
    try:
        client = CDSClient()
        
        # Get a sample search response
        import requests
        response = requests.get("https://cds.cern.ch/api/records", params={"q": "ATLAS", "size": 1})
        response.raise_for_status()
        data = response.json()
        
        print("✅ Raw API response structure:")
        print(f"   Top-level keys: {list(data.keys())}")
        
        if "hits" in data and data["hits"].get("hits"):
            sample_record = data["hits"]["hits"][0]
            print(f"   Record keys: {list(sample_record.keys())}")
            
            if "metadata" in sample_record:
                metadata = sample_record["metadata"]
                print(f"   Metadata keys: {list(metadata.keys())}")
                
                # Check specific fields we're expecting
                expected_fields = ["title", "authors", "creation_date", "experiment", "document_type"]
                for field in expected_fields:
                    if field in metadata:
                        field_type = type(metadata[field]).__name__
                        print(f"   ✅ {field}: {field_type}")
                    else:
                        print(f"   ❌ {field}: missing")
        
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing API response: {e}")
        return False


def main():
    """Run all integration tests."""
    print("🚀 Starting CDS MCP Server Integration Tests\n")
    
    # Test 1: API Connectivity
    if not test_cds_api_connectivity():
        print("\n❌ Cannot proceed without API connectivity")
        sys.exit(1)
    
    # Test 2: API Response Structure
    test_api_response_structure()
    
    # Test 3: Search Functionality
    search_results = test_search_functionality()
    
    # Test 4: Document Details (if we have a document from search)
    first_doc = search_results.get("first_document")
    if first_doc and first_doc.get("mcp_id"):
        test_document_details(first_doc["mcp_id"])
        test_document_files(first_doc["mcp_id"])
    else:
        print("\n⚠️  No document found from search to test details/files")
    
    # Test 5: Helper Tools
    test_helper_tools()
    
    # Summary
    print("\n📊 Test Summary:")
    successful_tests = sum(1 for result in search_results.values() if result is True)
    total_search_tests = len([k for k in search_results.keys() if k != "first_document"])
    
    print(f"   Search tests: {successful_tests}/{total_search_tests} passed")
    
    if successful_tests == total_search_tests and first_doc:
        print("✅ All tests completed successfully!")
        return 0
    else:
        print("❌ Some tests failed - review output above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
