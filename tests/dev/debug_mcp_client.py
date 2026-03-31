#!/usr/bin/env python3
"""Simple MCP client to test the CDS MCP server functionality."""

import asyncio
import json
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_mcp_server():
    """Test the CDS MCP server functionality."""
    print(" Testing CDS MCP Server")
    print("=" * 30)

    # Connect to the MCP server
    server_params = StdioServerParameters(command="uv", args=["run", "cds-mcp"], env={})

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()

            # Test 1: List available tools
            print("1️ Testing tool listing...")
            tools = await session.list_tools()
            print(f"✅ Found {len(tools.tools)} tools:")
            for tool in tools.tools:
                print(f"   - {tool.name}: {tool.description}")

            # Test 2: Search for CDS documents
            print("\n2️⃣ Testing CDS search...")
            search_result = await session.call_tool(
                "search_cds_documents", {"query": "ATLAS", "size": 2}
            )

            if search_result.isError:
                print(f"❌ Search failed: {search_result.content}")
            else:
                result_data = json.loads(search_result.content[0].text)
                print(f"✅ Search successful: {result_data['returned_count']} results")
                if result_data["documents"]:
                    first_doc = result_data["documents"][0]
                    print(f"   First result: {first_doc['title'][:50]}...")

            # Test 3: Get document details
            if not search_result.isError:
                result_data = json.loads(search_result.content[0].text)
                if result_data["documents"]:
                    doc_id = result_data["documents"][0]["mcp_id"]
                    print(f"\n3️⃣ Testing document details for {doc_id}...")

                    details_result = await session.call_tool(
                        "get_cds_document_details", {"mcp_id": doc_id}
                    )

                    if details_result.isError:
                        print(f"❌ Details failed: {details_result.content}")
                    else:
                        details_data = json.loads(details_result.content[0].text)
                        print(
                            f"✅ Details retrieved for: {details_data.get('title', 'N/A')[:50]}..."
                        )

            # Test 4: List experiments
            print("\n4️⃣ Testing experiments list...")
            experiments_result = await session.call_tool("get_cds_experiments", {})

            if experiments_result.isError:
                print(f"❌ Experiments failed: {experiments_result.content}")
            else:
                exp_data = json.loads(experiments_result.content[0].text)
                lhc_experiments = exp_data["experiments"]["LHC Experiments"]
                print(f"✅ Found {len(lhc_experiments)} LHC experiments:")
                for exp in lhc_experiments:
                    print(f"   - {exp['name']}: {exp['description']}")

            print("\n MCP server test completed successfully!")


if __name__ == "__main__":
    try:
        asyncio.run(test_mcp_server())
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
