"""CLI command: hckg serve — start the REST API server."""

from __future__ import annotations

import click


@click.command("serve")
@click.argument("source", type=click.Path(exists=True))
@click.option("--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1).")
@click.option("--port", default=8420, type=int, help="Port to listen on (default: 8420).")
@click.option(
    "--reload", "use_reload", is_flag=True, default=False,
    help="Enable auto-reload for development.",
)
def serve_cmd(source: str, host: str, port: int, use_reload: bool) -> None:
    """Start the REST API server with a loaded knowledge graph.

    Exposes the full knowledge graph as a REST API that any LLM client,
    agent framework, or HTTP consumer can query.

    \b
    Endpoints include:
      GET  /statistics            — Graph stats
      GET  /entities              — List entities
      GET  /entities/<id>         — Entity details
      GET  /search?q=alice        — Fuzzy search
      POST /ask                   — GraphRAG question answering
      GET  /openai/tools          — OpenAI function-calling definitions
      POST /openai/call           — Execute tools (for agents)

    \b
    Examples:
      hckg serve graph.json
      hckg serve graph.json --port 9000 --host 0.0.0.0
    """
    try:
        from serve.app import create_app
    except ImportError:
        click.echo(
            "Error: REST API server requires Flask. Install it with:\n"
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
        f"  Works with: Claude Desktop (MCP), ChatGPT, OpenAI API,\n"
        f"              LangChain, curl, or any HTTP client.\n"
        f"\n"
        f"  Press Ctrl+C to stop.\n"
    )

    app.run(host=host, port=port, debug=use_reload)
