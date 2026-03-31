"""MCP server for CDS (CERN Document Server) integration."""

import asyncio
import json
import logging
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolResult,
    TextContent,
    Tool,
)

from .tools import MCP_TOOLS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr)
    ],  # Log to stderr to avoid interfering with stdio
)
logger = logging.getLogger(__name__)


class CDSMCPServer:
    """MCP server for CDS operations."""

    def __init__(self) -> None:
        """Initialize the CDS MCP server."""
        self.server = Server("cds-mcp")
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Set up MCP request handlers."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available CDS tools."""
            tools = []
            for tool_name, tool_config in MCP_TOOLS.items():
                tool = Tool(
                    name=tool_name,
                    description=str(tool_config["description"]),
                    inputSchema=tool_config["parameters"],  # type: ignore[arg-type]
                )
                tools.append(tool)

            logger.info(f"Listed {len(tools)} available tools")
            return tools

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
            """Handle tool calls."""
            logger.info(f"Tool called: {name} with arguments: {arguments}")

            if name not in MCP_TOOLS:
                error_msg = f"Unknown tool: {name}"
                logger.error(error_msg)
                return CallToolResult(
                    content=[TextContent(type="text", text=error_msg)],
                    isError=True,
                )

            try:
                # Get the tool function and call it
                tool_function = MCP_TOOLS[name]["function"]
                result = tool_function(**arguments)  # type: ignore[operator]

                # Format the result as JSON for the MCP client
                result_text = json.dumps(result, indent=2, default=str)

                logger.info(f"Tool {name} completed successfully")
                return CallToolResult(
                    content=[TextContent(type="text", text=result_text)],
                    isError=False,
                )

            except Exception as e:
                error_msg = f"Error calling tool {name}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return CallToolResult(
                    content=[TextContent(type="text", text=error_msg)],
                    isError=True,
                )

    async def run(self) -> None:
        """Run the MCP server with stdio transport."""
        logger.info("Starting CDS MCP server with stdio transport")

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )


def main() -> None:
    """Main entry point for the CLI."""
    asyncio.run(run_async())


async def run_async() -> None:
    """Main async entry point for the CDS MCP server."""
    try:
        server = CDSMCPServer()
        await server.run()
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
