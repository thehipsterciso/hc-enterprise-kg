"""MCP server for Claude Desktop integration with the Enterprise Knowledge Graph.

Entry point module — creates the FastMCP instance, registers tools,
and runs the stdio transport.

Usage:
    python -m mcp_server.server
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_server.state import auto_load_default_graph
from mcp_server.tools import register_tools

mcp = FastMCP("hc-enterprise-kg")
register_tools(mcp)


def main() -> None:
    """Run the MCP server over stdio transport."""
    auto_load_default_graph()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
