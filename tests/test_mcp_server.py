#!/usr/bin/env python3
"""Test script to validate MCP server functionality end-to-end."""

import pytest


@pytest.mark.asyncio
async def test_mcp_server_tools():
    """Test MCP server tool listing and execution."""
    print("🔍 Testing MCP server tool functionality...")

    # Test the tools directly since MCP server testing is complex
    from cds_mcp.tools import MCP_TOOLS

    # Test 1: Verify tools are registered
    print("  Testing tool registration...")
    try:
        expected_tools = [
            "search_cds_documents",
            "get_cds_document_details",
            "get_cds_document_files",
            "get_cds_experiments",
            "get_cds_document_types",
        ]
        for tool_name in expected_tools:
            if tool_name not in MCP_TOOLS:
                print(f"    ❌ Missing tool: {tool_name}")
                assert False, f"Missing tool: {tool_name}"
        print(f"    ✅ All {len(expected_tools)} expected tools are registered")
    except Exception as e:
        print(f"    ❌ Error checking tool registration: {e}")
        assert False, f"Error checking tool registration: {e}"

    # Test 2: Call search tool directly
    print("  Testing search tool execution...")
    try:
        from cds_mcp.tools import search_cds_documents

        result = search_cds_documents(query="ATLAS", size=2)

        if "error" in result:
            print(f"    ❌ Search tool error: {result['error']}")
            # Don't fail for network issues in CI environment
            network_errors = [
                "Extra data",
                "403",
                "Forbidden",
                "SSL",
                "ConnectionPool",
                "Max retries",
                "EOF",
            ]
            if not any(error in result["error"] for error in network_errors):
                assert False, f"Search tool error: {result['error']}"
            else:
                print("    ⚠️  Skipping due to network issues in CI environment")
        else:
            print(f"    ✅ Search returned {result.get('returned_count', 0)} documents")
            assert "returned_count" in result
    except Exception as e:
        print(f"    ❌ Error calling search tool: {e}")
        # Don't fail for network issues in CI environment
        network_errors = [
            "Extra data",
            "403",
            "Forbidden",
            "SSL",
            "ConnectionPool",
            "Max retries",
            "EOF",
        ]
        if not any(error in str(e) for error in network_errors):
            assert False, f"Error calling search tool: {e}"
        else:
            print("    ⚠️  Skipping due to network issues in CI environment")

    # Test 3: Call document details tool directly
    print("  Testing document details tool execution...")
    try:
        from cds_mcp.tools import get_cds_document_details

        result = get_cds_document_details(mcp_id="cds:2957917")

        if "error" in result:
            print(f"    ❌ Document details error: {result['error']}")
            # Don't fail for network issues in CI environment
            network_errors = [
                "403",
                "Forbidden",
                "SSL",
                "ConnectionPool",
                "Max retries",
                "EOF",
            ]
            if not any(error in result["error"] for error in network_errors):
                assert False, f"Document details error: {result['error']}"
            else:
                print("    ⚠️  Skipping due to network issues in CI environment")
        else:
            print(
                f"    ✅ Retrieved details for: {result.get('title', 'Unknown')[:50]}..."
            )
            assert "title" in result
    except Exception as e:
        print(f"    ❌ Error calling document details tool: {e}")
        # Don't fail for network issues in CI environment
        network_errors = [
            "403",
            "Forbidden",
            "SSL",
            "ConnectionPool",
            "Max retries",
            "EOF",
        ]
        if not any(error in str(e) for error in network_errors):
            assert False, f"Error calling document details tool: {e}"
        else:
            print("    ⚠️  Skipping due to network issues in CI environment")

    # Test 4: Call helper tools directly
    print("  Testing helper tools execution...")
    try:
        from cds_mcp.tools import get_cds_experiments

        result = get_cds_experiments()

        if "error" in result:
            print(f"    ❌ Experiments tool error: {result['error']}")
            assert False, f"Experiments tool error: {result['error']}"
        else:
            exp_count = sum(
                len(exp_list) for exp_list in result["experiments"].values()
            )
            print(f"    ✅ Retrieved {exp_count} experiments")
            assert exp_count > 0
    except Exception as e:
        print(f"    ❌ Error calling experiments tool: {e}")
        assert False, f"Error calling experiments tool: {e}"

    assert len(MCP_TOOLS) > 0


def test_tool_parameter_validation():
    """Test tool parameter validation."""
    print("\n🔍 Testing tool parameter validation...")

    from cds_mcp.tools import get_cds_document_details, search_cds_documents

    # Test 1: Missing required parameter
    try:
        result = search_cds_documents()  # Missing query parameter
        print("    ❌ Should have failed with missing query parameter")
        assert False, "Should have failed with missing query parameter"
    except TypeError:
        print("    ✅ Correctly rejected missing required parameter")

    # Test 2: Invalid MCP ID format
    try:
        result = get_cds_document_details("invalid-id")
        if "error" in result and "Invalid MCP ID format" in result["error"]:
            print("    ✅ Correctly rejected invalid MCP ID format")
        else:
            print("    ❌ Should have rejected invalid MCP ID format")
            assert False, "Should have rejected invalid MCP ID format"
    except Exception as e:
        print(f"    ❌ Unexpected error: {e}")
        assert False, f"Unexpected error: {e}"
