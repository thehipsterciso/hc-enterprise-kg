"""CLI command: hckg mcp install — configure Claude Desktop MCP integration."""

from __future__ import annotations

import json
import platform
import sys
from pathlib import Path

import click


def _detect_config_path() -> Path | None:
    """Auto-detect the Claude Desktop config file path based on the OS."""
    system = platform.system()
    if system == "Darwin":
        return (
            Path.home() / "Library" / "Application Support"
            / "Claude" / "claude_desktop_config.json"
        )
    if system == "Windows":
        appdata = Path.home() / "AppData" / "Roaming" / "Claude"
        return appdata / "claude_desktop_config.json"
    if system == "Linux":
        # XDG convention
        config_home = Path(
            __import__("os").environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
        )
        return config_home / "claude" / "claude_desktop_config.json"
    return None


def _detect_python_path() -> str:
    """Get the path to the current Python interpreter (inside the Poetry venv)."""
    return sys.executable


def _detect_project_root() -> Path:
    """Walk up from this file to find the project root (where pyproject.toml is)."""
    current = Path(__file__).resolve().parent
    for _ in range(10):
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    # Fallback: use the cwd
    return Path.cwd()


@click.group("mcp")
def mcp_group() -> None:
    """MCP (Model Context Protocol) integration for Claude Desktop."""


@mcp_group.command("install")
@click.option(
    "--config",
    "config_path",
    type=click.Path(),
    default=None,
    help="Path to claude_desktop_config.json. Auto-detected if omitted.",
)
@click.option(
    "--graph",
    "graph_path",
    type=click.Path(),
    default=None,
    help="Default graph file to load. If omitted, Claude will need to call load_graph.",
)
def mcp_install(config_path: str | None, graph_path: str | None) -> None:
    """Register hc-enterprise-kg as an MCP server in Claude Desktop.

    Auto-detects the config file location and Python path based on your
    current environment. Works on macOS, Windows, and Linux.

    \b
    Examples:
      hckg mcp install
      hckg mcp install --graph graph.json
      hckg mcp install --config ~/custom/claude_desktop_config.json
    """
    # Detect config path
    if config_path:
        conf_file = Path(config_path).expanduser()
    else:
        conf_file = _detect_config_path()
        if conf_file is None:
            click.echo("Error: Could not detect Claude Desktop config location.", err=True)
            click.echo("Specify it manually with --config <path>", err=True)
            raise SystemExit(1)

    # Detect Python and project paths
    python_path = _detect_python_path()
    project_root = _detect_project_root()

    click.echo(f"  Config:  {conf_file}")
    click.echo(f"  Python:  {python_path}")
    click.echo(f"  Project: {project_root}")

    # Build the MCP server entry
    server_entry: dict = {
        "command": python_path,
        "args": ["-m", "mcp_server.server"],
        "cwd": str(project_root / "src"),
    }

    if graph_path:
        abs_graph = Path(graph_path).resolve()
        server_entry["env"] = {"HCKG_DEFAULT_GRAPH": str(abs_graph)}
        click.echo(f"  Graph:   {abs_graph}")

    # Read existing config or create new one
    existing = json.loads(conf_file.read_text()) if conf_file.exists() else {}

    # Ensure mcpServers key exists
    if "mcpServers" not in existing:
        existing["mcpServers"] = {}

    # Check if already installed
    if "hc-enterprise-kg" in existing["mcpServers"]:
        click.echo("\n  hc-enterprise-kg is already registered in Claude Desktop.")
        click.echo("  Updating configuration...")

    existing["mcpServers"]["hc-enterprise-kg"] = server_entry

    # Write config
    conf_file.parent.mkdir(parents=True, exist_ok=True)
    conf_file.write_text(json.dumps(existing, indent=2) + "\n")

    click.echo(f"\n  ✓ MCP server registered in {conf_file}")
    click.echo("\n  Next steps:")
    click.echo("    1. Restart Claude Desktop")
    click.echo("    2. Look for the 🔌 icon in the input field")
    click.echo('    3. Ask Claude: "Load the graph and show me statistics"')


@mcp_group.command("status")
def mcp_status() -> None:
    """Check if hc-enterprise-kg is registered in Claude Desktop."""
    conf_file = _detect_config_path()
    if conf_file is None or not conf_file.exists():
        click.echo("Claude Desktop config not found.")
        click.echo("Run: hckg mcp install")
        return

    config = json.loads(conf_file.read_text())
    servers = config.get("mcpServers", {})

    if "hc-enterprise-kg" in servers:
        entry = servers["hc-enterprise-kg"]
        click.echo("  ✓ hc-enterprise-kg is registered")
        click.echo(f"    Command: {entry.get('command', '?')}")
        click.echo(f"    Args:    {entry.get('args', [])}")
        if "cwd" in entry:
            click.echo(f"    CWD:     {entry['cwd']}")
        if "env" in entry and "HCKG_DEFAULT_GRAPH" in entry["env"]:
            click.echo(f"    Graph:   {entry['env']['HCKG_DEFAULT_GRAPH']}")
    else:
        click.echo("  ✗ hc-enterprise-kg is NOT registered")
        click.echo("  Run: hckg mcp install")


@mcp_group.command("uninstall")
def mcp_uninstall() -> None:
    """Remove hc-enterprise-kg from Claude Desktop config."""
    conf_file = _detect_config_path()
    if conf_file is None or not conf_file.exists():
        click.echo("Claude Desktop config not found. Nothing to remove.")
        return

    config = json.loads(conf_file.read_text())
    servers = config.get("mcpServers", {})

    if "hc-enterprise-kg" not in servers:
        click.echo("hc-enterprise-kg is not registered. Nothing to remove.")
        return

    del servers["hc-enterprise-kg"]
    conf_file.write_text(json.dumps(config, indent=2) + "\n")
    click.echo("  ✓ hc-enterprise-kg removed from Claude Desktop config.")
    click.echo("  Restart Claude Desktop to apply changes.")
