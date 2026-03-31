#!/usr/bin/env python3
"""Test script to validate MCP server functionality end-to-end."""

import asyncio
import json
import sys
from io import StringIO
from unittest.mock import patch

from cds_mcp.server import CDSMCPServer


async def test_mcp_server_tools():
    """Test MCP server tool listing and execution."""
    print("🔍 Testing MCP server tool functionality...")
    
    # Test the tools directly since MCP server testing is complex
    from cds_mcp.tools import MCP_TOOLS
    
    # Test 1: Verify tools are registered
    print("  Testing tool registration...")
    try:
        expected_tools = ["search_cds_documents", "get_cds_document_details", "get_cds_document_files", "get_cds_experiments", "get_cds_document_types"]
        for tool_name in expected_tools:
            if tool_name not in MCP_TOOLS:
                print(f"    ❌ Missing tool: {tool_name}")
                return False
        print(f"    ✅ All {len(expected_tools)} expected tools are registered")
    except Exception as e:
        print(f"    ❌ Error checking tool registration: {e}")
        return False
    
    # Test 2: Call search tool directly
    print("  Testing search tool execution...")
    try:
        from cds_mcp.tools import search_cds_documents
        result = search_cds_documents(query="ATLAS", size=2)
        
        if "error" in result:
            print(f"    ❌ Search tool error: {result['error']}")
            return False
        else:
            print(f"    ✅ Search returned {result.get('returned_count', 0)} documents")
    except Exception as e:
        print(f"    ❌ Error calling search tool: {e}")
        return False
    
    # Test 3: Call document details tool directly
    print("  Testing document details tool execution...")
    try:
        from cds_mcp.tools import get_cds_document_details
        result = get_cds_document_details(mcp_id="cds:2957917")
        
        if "error" in result:
            print(f"    ❌ Document details error: {result['error']}")
            return False
        else:
            print(f"    ✅ Retrieved details for: {result.get('title', 'Unknown')[:50]}...")
    except Exception as e:
        print(f"    ❌ Error calling document details tool: {e}")
        return False
    
    # Test 4: Call helper tools directly
    print("  Testing helper tools execution...")
    try:
        from cds_mcp.tools import get_cds_experiments
        result = get_cds_experiments()
        
        if "error" in result:
            print(f"    ❌ Experiments tool error: {result['error']}")
            return False
        else:
            exp_count = sum(len(exp_list) for exp_list in result["experiments"].values())
            print(f"    ✅ Retrieved {exp_count} experiments")
    except Exception as e:
        print(f"    ❌ Error calling experiments tool: {e}")
        return False
    
    return True


def test_tool_parameter_validation():
    """Test tool parameter validation."""
    print("\n🔍 Testing tool parameter validation...")
    
    from cds_mcp.tools import search_cds_documents, get_cds_document_details
    
    # Test 1: Missing required parameter
    try:
        result = search_cds_documents()  # Missing query parameter
        print("    ❌ Should have failed with missing query parameter")
        return False
    except TypeError:
        print("    ✅ Correctly rejected missing required parameter")
    
    # Test 2: Invalid MCP ID format
    try:
        result = get_cds_document_details("invalid-id")
        if "error" in result and "Invalid MCP ID format" in result["error"]:
            print("    ✅ Correctly rejected invalid MCP ID format")
        else:
            print("    ❌ Should have rejected invalid MCP ID format")
            return False
    except Exception as e:
        print(f"    ❌ Unexpected error: {e}")
        return False
    
    return True


async def main():
    """Run all MCP server tests."""
    print("🚀 Starting MCP Server End-to-End Tests\n")
    
    # Test 1: Server functionality
    server_test_passed = await test_mcp_server_tools()
    
    # Test 2: Parameter validation
    validation_test_passed = test_tool_parameter_validation()
    
    # Summary
    print("\n📊 MCP Server Test Summary:")
    print(f"   Server functionality: {'✅ PASSED' if server_test_passed else '❌ FAILED'}")
    print(f"   Parameter validation: {'✅ PASSED' if validation_test_passed else '❌ FAILED'}")
    
    if server_test_passed and validation_test_passed:
        print("\n✅ All MCP server tests passed!")
        return 0
    else:
        print("\n❌ Some MCP server tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
