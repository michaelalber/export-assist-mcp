"""Export Control MCP Server - Export regulation and sanctions list access."""

import logging

from fastmcp import FastMCP

from export_control_mcp.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

mcp = FastMCP(
    "export-control-mcp",
    instructions="""
    Export Control MCP Server for National Laboratory Export Control groups.

    This server provides tools for:
    - Searching EAR (Export Administration Regulations)
    - Searching ITAR (International Traffic in Arms Regulations)
    - Looking up ECCN (Export Control Classification Numbers)
    - Searching sanctions lists (Entity List, SDN, Denied Persons)
    - Getting country sanctions and country group information

    All queries are logged for audit purposes. No data leaves the network
    unless explicitly configured for external API access.

    For classification suggestions, always note that official classification
    requires formal commodity jurisdiction or classification requests.
    """,
)

# Import tools to register them with FastMCP via @mcp.tool() decorators
# These imports must happen after mcp is defined
from export_control_mcp.tools import (  # noqa: E402
    classification,  # noqa: F401
    regulations,  # noqa: F401
    sanctions,  # noqa: F401
)


def main() -> None:
    """Run the MCP server with configured transport."""
    transport = settings.mcp_transport

    if transport == "streamable-http":
        mcp.run(
            transport="streamable-http",
            host=settings.mcp_host,
            port=settings.mcp_port,
        )
    elif transport == "sse":
        mcp.run(
            transport="sse",
            host=settings.mcp_host,
            port=settings.mcp_port,
        )
    else:
        # Default: stdio for Claude Desktop integration
        mcp.run()


if __name__ == "__main__":
    main()
