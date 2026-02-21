"""CLI command: hckg install — register the KG server with LLM clients."""

from __future__ import annotations

import json
import platform
import subprocess
import sys
from pathlib import Path

import click

# ---------------------------------------------------------------------------
# Detection helpers
# ---------------------------------------------------------------------------


def _detect_claude_config_path() -> Path | None:
    """Auto-detect the Claude Desktop config file path based on the OS."""
    system = platform.system()
    if system == "Darwin":
        return (
            Path.home()
            / "Library"
            / "Application Support"
            / "Claude"
            / "claude_desktop_config.json"
        )
    if system == "Windows":
        appdata = Path.home() / "AppData" / "Roaming" / "Claude"
        return appdata / "claude_desktop_config.json"
    if system == "Linux":
        config_home = Path(
            __import__("os").environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
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


# ---------------------------------------------------------------------------
# Pre-flight validation
# ---------------------------------------------------------------------------


def _check_mcp_importable(python_path: str) -> tuple[bool, str]:
    """Check whether the MCP SDK is importable from the given interpreter.

    Returns (ok, detail) where *detail* is a human-readable diagnostic.
    """
    try:
        result = subprocess.run(  # noqa: S603
            [
                python_path,
                "-c",
                "from mcp.server.fastmcp import FastMCP; print('ok')",
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0 and "ok" in result.stdout:
            return True, "mcp SDK is importable"
        # Parse the error for a helpful message
        stderr = result.stderr.strip()
        if "No module named 'mcp'" in stderr:
            return False, (
                "The 'mcp' package is not installed in this Python environment.\n"
                "  Fix: poetry install --extras mcp"
            )
        return False, f"Import check failed:\n  {stderr}"
    except FileNotFoundError:
        return False, f"Python interpreter not found: {python_path}"
    except subprocess.TimeoutExpired:
        return False, "Import check timed out (>15s)"


def _check_server_module(project_root: Path) -> tuple[bool, str]:
    """Check that mcp_server/server.py exists under src/."""
    server_file = project_root / "src" / "mcp_server" / "server.py"
    if server_file.exists():
        return True, f"Server module found: {server_file}"
    return False, (
        f"Server module not found: {server_file}\n"
        "  Ensure you are running from the hc-enterprise-kg project directory."
    )


def _check_python_version(python_path: str) -> tuple[bool, str]:
    """Report the Python version for the detected interpreter."""
    try:
        result = subprocess.run(  # noqa: S603
            [python_path, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        version = result.stdout.strip() or result.stderr.strip()
        return True, version
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, f"Could not determine version for: {python_path}"


def _run_preflight(python_path: str, project_root: Path) -> list[tuple[str, bool, str]]:
    """Run all pre-flight checks. Returns list of (check_name, passed, detail)."""
    checks: list[tuple[str, bool, str]] = []

    # 1. Python version (informational — always "passes" if reachable)
    ok, detail = _check_python_version(python_path)
    checks.append(("Python version", ok, detail))

    # 2. Server module exists
    ok, detail = _check_server_module(project_root)
    checks.append(("Server module", ok, detail))

    # 3. MCP SDK importable (the critical one)
    ok, detail = _check_mcp_importable(python_path)
    checks.append(("MCP SDK", ok, detail))

    return checks


def _print_checks(checks: list[tuple[str, bool, str]]) -> int:
    """Print check results. Returns count of failures."""
    failures = 0
    for name, passed, detail in checks:
        icon = "PASS" if passed else "FAIL"
        click.echo(f"  [{icon}] {name}: {detail.split(chr(10))[0]}")
        if not passed:
            failures += 1
            # Print additional lines indented
            lines = detail.split("\n")
            for line in lines[1:]:
                click.echo(f"         {line}")
    return failures


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------


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
@click.option(
    "--skip-checks",
    is_flag=True,
    default=False,
    help="Skip pre-flight validation checks.",
)
def install_claude(
    config_path: str | None, graph_path: str | None, skip_checks: bool
) -> None:
    """Register hc-enterprise-kg with Claude Desktop.

    Runs pre-flight validation to ensure the MCP server will start
    correctly. Use --skip-checks to bypass validation.

    \b
    Examples:
      hckg install claude
      hckg install claude --graph graph.json
      hckg install claude --config ~/custom/claude_desktop_config.json
      hckg install claude --skip-checks
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

    click.echo()
    click.echo("  Environment")
    click.echo(f"    Config:  {conf_file}")
    click.echo(f"    Python:  {python_path}")
    click.echo(f"    Project: {project_root}")

    # --- Pre-flight checks ---
    if not skip_checks:
        click.echo()
        click.echo("  Pre-flight checks")
        checks = _run_preflight(python_path, project_root)
        failures = _print_checks(checks)

        if failures > 0:
            click.echo()
            click.echo(
                f"  {failures} check(s) failed. Resolve the issues above "
                "or use --skip-checks to bypass."
            )
            raise SystemExit(1)

        click.echo()

    # --- Write config ---
    server_entry: dict = {
        "command": python_path,
        "args": ["-m", "mcp_server.server"],
        "cwd": str(project_root / "src"),
    }

    if graph_path:
        abs_graph = Path(graph_path).resolve()
        server_entry["env"] = {"HCKG_DEFAULT_GRAPH": str(abs_graph)}
        click.echo(f"  Graph:   {abs_graph}")

    existing = json.loads(conf_file.read_text()) if conf_file.exists() else {}

    if "mcpServers" not in existing:
        existing["mcpServers"] = {}

    if "hc-enterprise-kg" in existing["mcpServers"]:
        click.echo("  Already registered. Updating configuration...")

    existing["mcpServers"]["hc-enterprise-kg"] = server_entry

    conf_file.parent.mkdir(parents=True, exist_ok=True)
    conf_file.write_text(json.dumps(existing, indent=2) + "\n")

    click.echo(f"\n  Registered in {conf_file}")
    click.echo("\n  Next steps:")
    click.echo("    1. Restart Claude Desktop")
    click.echo('    2. Ask Claude: "Load the graph and show me statistics"')


@install_group.command("doctor")
def install_doctor() -> None:
    """Diagnose an existing Claude Desktop registration.

    Validates the currently registered configuration without modifying
    anything. Use this to troubleshoot connection issues.

    \b
    Examples:
      hckg install doctor
    """
    conf_file = _detect_claude_config_path()

    click.echo()
    click.echo("  Claude Desktop Doctor")
    click.echo()

    if conf_file is None or not conf_file.exists():
        click.echo("  Config file not found.")
        click.echo("  Run: hckg install claude")
        raise SystemExit(1)

    config = json.loads(conf_file.read_text())
    servers = config.get("mcpServers", {})

    if "hc-enterprise-kg" not in servers:
        click.echo("  hc-enterprise-kg is not registered.")
        click.echo("  Run: hckg install claude")
        raise SystemExit(1)

    entry = servers["hc-enterprise-kg"]
    python_path = entry.get("command", "")
    cwd = entry.get("cwd", "")

    click.echo("  Registered config:")
    click.echo(f"    Command: {python_path}")
    click.echo(f"    Args:    {entry.get('args', [])}")
    click.echo(f"    CWD:     {cwd}")
    if "env" in entry:
        for k, v in entry["env"].items():
            click.echo(f"    Env:     {k}={v}")
    click.echo()

    # Derive project_root from cwd (cwd = project_root/src)
    cwd_path = Path(cwd)
    project_root = cwd_path.parent if cwd_path.name == "src" else cwd_path

    click.echo("  Validation")
    checks = _run_preflight(python_path, project_root)

    # Extra check: does the registered Python still exist?
    python_exists = Path(python_path).exists()
    if not python_exists:
        checks.insert(
            0,
            (
                "Python exists",
                False,
                f"Interpreter not found at: {python_path}\n"
                "  The virtualenv may have been deleted. Re-run: hckg install claude",
            ),
        )

    # Extra check: does the CWD exist?
    if not cwd_path.exists():
        checks.insert(
            0,
            (
                "Working directory",
                False,
                f"CWD does not exist: {cwd}\n"
                "  The project may have been moved. Re-run: hckg install claude",
            ),
        )

    failures = _print_checks(checks)

    click.echo()
    if failures == 0:
        click.echo("  All checks passed. The MCP server should connect successfully.")
        click.echo("  If issues persist, restart Claude Desktop.")
    else:
        click.echo(f"  {failures} issue(s) found. Resolve them and re-run: hckg install claude")
        raise SystemExit(1)


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
                click.echo(f"    Graph:   {entry['env']['HCKG_DEFAULT_GRAPH']}")
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
