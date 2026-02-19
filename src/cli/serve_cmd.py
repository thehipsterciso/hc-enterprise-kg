"""CLI command: hckg serve — start the knowledge graph server."""

from __future__ import annotations

import click


@click.command("serve")
@click.argument("source", type=click.Path(exists=True))
@click.option("--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1).")
@click.option("--port", default=8420, type=int, help="Port to listen on (default: 8420).")
@click.option(
    "--stdio", "use_stdio", is_flag=True, default=False,
    help="Run as MCP server over stdio (for Claude Desktop).",
)
@click.option(
    "--reload", "use_reload", is_flag=True, default=False,
    help="Enable auto-reload for development.",
)
def serve_cmd(
    source: str, host: str, port: int, use_stdio: bool, use_reload: bool,
) -> None:
    """Start the knowledge graph server.

    By default, starts a REST API on http://localhost:8420 that works
    with any LLM client, agent framework, or HTTP consumer.

    Use --stdio to run as an MCP server over stdio (used by Claude
    Desktop to pipe requests directly).

    \b
    REST mode (default):
      hckg serve graph.json
      hckg serve graph.json --port 9000 --host 0.0.0.0

    \b
    MCP stdio mode (for Claude Desktop):
      hckg serve graph.json --stdio
    """
    if use_stdio:
        _run_stdio(source)
    else:
        _run_rest(source, host, port, use_reload)


def _run_stdio(source: str) -> None:
    """Start the MCP server over stdio transport."""
    try:
        from mcp_server.server import load_graph, mcp
    except ImportError:
        click.echo(
            "Error: MCP server requires the mcp package. Install with:\n"
            "  poetry install --extras mcp",
            err=True,
        )
        raise SystemExit(1) from None

    # Pre-load the graph so Claude doesn't have to call load_graph
    result = load_graph(source)
    if "error" in result:
        click.echo(f"Error loading graph: {result['error']}", err=True)
        raise SystemExit(1)

    mcp.run(transport="stdio")


def _run_rest(source: str, host: str, port: int, use_reload: bool) -> None:
    """Start the REST API server."""
    try:
        from serve.app import create_app
    except ImportError:
        click.echo(
            "Error: REST API server requires Flask. Install with:\n"
            "  poetry install --extras api\n"
            "  # or: pip install flask",
            err=True,
        )
        raise SystemExit(1) from None

    click.echo(f"Loading graph from {source}...")
    app = create_app(graph_path=source)

    click.echo(
        f"\n"
        f"  hc-enterprise-kg REST API\n"
        f"  ─────────────────────────────────\n"
        f"  Listening:    http://{host}:{port}\n"
        f"  API index:    http://{host}:{port}/\n"
        f"  Health:       http://{host}:{port}/health\n"
        f"  OpenAI tools: http://{host}:{port}/openai/tools\n"
        f"  GraphRAG:     POST http://{host}:{port}/ask\n"
        f"\n"
        f"  Works with: Claude Desktop, ChatGPT, OpenAI API,\n"
        f"              LangChain, curl, or any HTTP client.\n"
        f"\n"
        f"  Press Ctrl+C to stop.\n"
    )

    app.run(host=host, port=port, debug=use_reload)
