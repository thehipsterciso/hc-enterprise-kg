"""CLI command: hckg install — register the KG server with LLM clients."""

from __future__ import annotations

import json
import platform
import sys
from pathlib import Path

import click


def _detect_claude_config_path() -> Path | None:
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
        config_home = Path(
            __import__("os").environ.get(
                "XDG_CONFIG_HOME", str(Path.home() / ".config")
            )
        )
        return config_home / "claude" / "claude_desktop_config.json"
    return None


def _detect_python_path() -> str:
    """Get the path to the current Python interpreter."""
    return sys.executable


def _detect_project_root() -> Path:
    """Walk up from this file to find the project root."""
    current = Path(__file__).resolve().parent
    for _ in range(10):
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    return Path.cwd()


@click.group("install")
def install_group() -> None:
    """Register hc-enterprise-kg with LLM clients (Claude Desktop, etc.)."""


@install_group.command("claude")
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
    help="Default graph file to auto-load on startup.",
)
def install_claude(config_path: str | None, graph_path: str | None) -> None:
    """Register hc-enterprise-kg with Claude Desktop.

    Auto-detects the config file location and Python path based on your
    current environment. Works on macOS, Windows, and Linux.

    \b
    Examples:
      hckg install claude
      hckg install claude --graph graph.json
      hckg install claude --config ~/custom/claude_desktop_config.json
    """
    if config_path:
        conf_file = Path(config_path).expanduser()
    else:
        conf_file = _detect_claude_config_path()
        if conf_file is None:
            click.echo(
                "Error: Could not detect Claude Desktop config.",
                err=True,
            )
            click.echo("Specify manually: --config <path>", err=True)
            raise SystemExit(1)

    python_path = _detect_python_path()
    project_root = _detect_project_root()

    click.echo(f"  Config:  {conf_file}")
    click.echo(f"  Python:  {python_path}")
    click.echo(f"  Project: {project_root}")

    server_entry: dict = {
        "command": python_path,
        "args": ["-m", "mcp_server.server"],
        "cwd": str(project_root / "src"),
    }

    if graph_path:
        abs_graph = Path(graph_path).resolve()
        server_entry["env"] = {"HCKG_DEFAULT_GRAPH": str(abs_graph)}
        click.echo(f"  Graph:   {abs_graph}")

    existing = (
        json.loads(conf_file.read_text()) if conf_file.exists() else {}
    )

    if "mcpServers" not in existing:
        existing["mcpServers"] = {}

    if "hc-enterprise-kg" in existing["mcpServers"]:
        click.echo("\n  Already registered. Updating configuration...")

    existing["mcpServers"]["hc-enterprise-kg"] = server_entry

    conf_file.parent.mkdir(parents=True, exist_ok=True)
    conf_file.write_text(json.dumps(existing, indent=2) + "\n")

    click.echo(f"\n  Registered in {conf_file}")
    click.echo("\n  Next steps:")
    click.echo("    1. Restart Claude Desktop")
    click.echo("    2. Ask Claude: \"Load the graph and show me statistics\"")


@install_group.command("status")
def install_status() -> None:
    """Check which LLM clients have hc-enterprise-kg registered."""
    conf_file = _detect_claude_config_path()

    click.echo("  Claude Desktop:")
    if conf_file is None or not conf_file.exists():
        click.echo("    Not found (config file missing)")
    else:
        config = json.loads(conf_file.read_text())
        servers = config.get("mcpServers", {})
        if "hc-enterprise-kg" in servers:
            entry = servers["hc-enterprise-kg"]
            click.echo("    Registered")
            click.echo(f"    Command: {entry.get('command', '?')}")
            if "cwd" in entry:
                click.echo(f"    CWD:     {entry['cwd']}")
            if "env" in entry and "HCKG_DEFAULT_GRAPH" in entry["env"]:
                click.echo(
                    f"    Graph:   {entry['env']['HCKG_DEFAULT_GRAPH']}"
                )
        else:
            click.echo("    Not registered")
            click.echo("    Run: hckg install claude")


@install_group.command("remove")
@click.argument("client", type=click.Choice(["claude"]))
def install_remove(client: str) -> None:
    """Remove hc-enterprise-kg from an LLM client.

    \b
    Examples:
      hckg install remove claude
    """
    if client == "claude":
        _remove_claude()


def _remove_claude() -> None:
    """Remove from Claude Desktop config."""
    conf_file = _detect_claude_config_path()
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
    click.echo("  Removed from Claude Desktop.")
    click.echo("  Restart Claude Desktop to apply changes.")
