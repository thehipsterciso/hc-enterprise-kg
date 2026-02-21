"""CLI command: hckg install — register the KG server with LLM clients."""

from __future__ import annotations

import json
import os
import platform
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import click

# Minimum Python version required by hc-enterprise-kg
_MIN_PYTHON = (3, 11)

# ---------------------------------------------------------------------------
# Config I/O helpers (centralised JSON handling)
# ---------------------------------------------------------------------------


def _read_config(path: Path) -> dict:
    """Read and parse the Claude Desktop config file.

    Returns an empty dict if the file does not exist.
    Raises SystemExit with a clear message on malformed JSON or permission
    errors.
    """
    if not path.exists():
        return {}
    try:
        text = path.read_text(encoding="utf-8")
    except PermissionError as exc:
        click.echo(f"  Error: permission denied reading {path}", err=True)
        raise SystemExit(1) from exc
    if not text.strip():
        return {}
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        click.echo(f"  Error: config file contains malformed JSON: {exc}", err=True)
        click.echo(f"  File: {path}", err=True)
        click.echo("  Fix the file manually or delete it and re-run.", err=True)
        raise SystemExit(1) from exc
    if not isinstance(data, dict):
        click.echo("  Error: config file root is not a JSON object.", err=True)
        raise SystemExit(1)
    return data


def _write_config(path: Path, data: dict) -> None:
    """Atomically write *data* as JSON to *path*.

    Uses write-to-temp-then-rename so Claude Desktop never reads a
    partially-written file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, indent=2) + "\n"
    try:
        fd, tmp = tempfile.mkstemp(
            dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp"
        )
        try:
            os.write(fd, payload.encode("utf-8"))
        finally:
            os.close(fd)
        os.replace(tmp, str(path))  # atomic on POSIX
    except PermissionError as exc:
        click.echo(f"  Error: permission denied writing {path}", err=True)
        raise SystemExit(1) from exc
    except OSError as exc:
        click.echo(f"  Error writing config: {exc}", err=True)
        raise SystemExit(1) from exc


# ---------------------------------------------------------------------------
# Detection helpers
# ---------------------------------------------------------------------------


def _detect_claude_config_path() -> Path | None:
    """Auto-detect the Claude Desktop config file path."""
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
        appdata = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
        return Path(appdata) / "Claude" / "claude_desktop_config.json"
    if system == "Linux":
        config_home = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
        return Path(config_home) / "Claude" / "claude_desktop_config.json"
    return None


def _detect_python_path() -> str:
    """Get the path to the current Python interpreter."""
    exe = sys.executable
    if not exe:
        raise click.ClickException(
            "Cannot determine Python interpreter path (sys.executable is empty)."
        )
    return exe


def _is_source_checkout() -> bool:
    """Return True if we are running from a source checkout (not pip-installed)."""
    # If __file__ is inside a site-packages directory, it's a pip install
    here = Path(__file__).resolve()
    return "site-packages" not in str(here)


def _detect_project_root() -> Path | None:
    """Find the hc-enterprise-kg project root, or None if pip-installed.

    Walks up from this file looking for a pyproject.toml that belongs to
    hc-enterprise-kg.  Returns None when running from a pip install (no
    source tree available).
    """
    if not _is_source_checkout():
        return None

    current = Path(__file__).resolve().parent
    for _ in range(10):
        candidate = current / "pyproject.toml"
        if candidate.exists():
            try:
                text = candidate.read_text(encoding="utf-8")
                if "hc-enterprise-kg" in text:
                    return current
            except OSError:
                pass
        current = current.parent
    return None


# ---------------------------------------------------------------------------
# Pre-flight validation checks
# ---------------------------------------------------------------------------


def _check_python_version(python_path: str) -> tuple[bool, str]:
    """Verify the interpreter exists and meets the minimum version."""
    try:
        result = subprocess.run(  # noqa: S603
            [python_path, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError:
        return False, f"interpreter not found: {python_path}"
    except subprocess.TimeoutExpired:
        return False, f"timed out checking: {python_path}"

    version_str = (result.stdout.strip() or result.stderr.strip())
    match = re.search(r"(\d+)\.(\d+)", version_str)
    if not match:
        return False, f"could not parse version from: {version_str}"
    major, minor = int(match.group(1)), int(match.group(2))
    if (major, minor) < _MIN_PYTHON:
        return False, (
            f"{version_str} — requires Python >={_MIN_PYTHON[0]}.{_MIN_PYTHON[1]}\n"
            f"  Fix: install Python {_MIN_PYTHON[0]}.{_MIN_PYTHON[1]}+"
            " and re-create your virtualenv"
        )
    return True, version_str


def _check_mcp_importable(python_path: str) -> tuple[bool, str]:
    """Check whether the MCP SDK is importable from the given interpreter."""
    try:
        result = subprocess.run(  # noqa: S603
            [python_path, "-c", "from mcp.server.fastmcp import FastMCP; print('ok')"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except FileNotFoundError:
        return False, f"interpreter not found: {python_path}"
    except subprocess.TimeoutExpired:
        return False, "import check timed out (>15s)"

    if result.returncode == 0 and "ok" in result.stdout:
        return True, "mcp SDK is importable"

    stderr = result.stderr.strip()
    if "No module named 'mcp'" in stderr:
        return False, (
            "the 'mcp' package is not installed in this Python environment.\n"
            "  Fix: poetry install --extras mcp\n"
            "   or: pip install 'hc-enterprise-kg[mcp]'"
        )
    return False, f"import failed:\n  {stderr.splitlines()[0] if stderr else 'unknown error'}"


def _check_server_importable(python_path: str) -> tuple[bool, str]:
    """Check whether the mcp_server module is importable."""
    try:
        result = subprocess.run(  # noqa: S603
            [python_path, "-c", "import mcp_server.state; print('ok')"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except FileNotFoundError:
        return False, f"interpreter not found: {python_path}"
    except subprocess.TimeoutExpired:
        return False, "import check timed out (>15s)"

    if result.returncode == 0 and "ok" in result.stdout:
        return True, "mcp_server module is importable"

    stderr = result.stderr.strip()
    if "No module named 'mcp_server'" in stderr:
        return False, (
            "the hc-enterprise-kg package is not installed in this Python environment.\n"
            "  Fix: poetry install --extras mcp\n"
            "   or: pip install 'hc-enterprise-kg[mcp]'"
        )
    if "No module named 'mcp'" in stderr:
        return False, (
            "the 'mcp' package is not installed (required by mcp_server).\n"
            "  Fix: poetry install --extras mcp\n"
            "   or: pip install 'hc-enterprise-kg[mcp]'"
        )
    first_line = stderr.splitlines()[0] if stderr else "unknown error"
    return False, f"import failed:\n  {first_line}"


def _run_preflight(python_path: str) -> list[tuple[str, bool, str]]:
    """Run all pre-flight checks.

    Returns list of (check_name, passed, detail).  Short-circuits if the
    Python interpreter is not reachable.
    """
    checks: list[tuple[str, bool, str]] = []

    # 1. Python version — gates everything else
    ok, detail = _check_python_version(python_path)
    checks.append(("Python version", ok, detail))
    if not ok:
        checks.append(("MCP SDK", False, "skipped — Python interpreter not reachable"))
        checks.append(("Server module", False, "skipped — Python interpreter not reachable"))
        return checks

    # 2. MCP SDK
    ok, detail = _check_mcp_importable(python_path)
    checks.append(("MCP SDK", ok, detail))

    # 3. Server module
    ok, detail = _check_server_importable(python_path)
    checks.append(("Server module", ok, detail))

    return checks


def _print_checks(checks: list[tuple[str, bool, str]]) -> int:
    """Print check results and return the number of failures."""
    failures = 0
    for name, passed, detail in checks:
        icon = "PASS" if passed else "FAIL"
        click.echo(f"  [{icon}] {name}: {detail.split(chr(10))[0]}")
        if not passed:
            failures += 1
            for line in detail.split("\n")[1:]:
                click.echo(f"         {line}")
    return failures


# ---------------------------------------------------------------------------
# Config entry builder
# ---------------------------------------------------------------------------


def _build_server_entry(
    python_path: str,
    project_root: Path | None,
    graph_path: str | None,
) -> dict:
    """Build the mcpServers entry dict.

    When the package is properly installed (pip or poetry), ``cwd`` is
    omitted — modules resolve from site-packages.  When running from a
    source checkout where modules are NOT installed, ``cwd`` points to
    ``src/`` so Python can find them via ``-m``.
    """
    entry: dict = {
        "command": python_path,
        "args": ["-m", "mcp_server.server"],
    }
    # Only set cwd when running from source AND the module is NOT installed.
    # In practice, `poetry install` installs the package, so cwd is rarely
    # needed.  But if someone clones without installing, this is the
    # fallback.
    if project_root is not None:
        src_dir = project_root / "src"
        if src_dir.is_dir():
            entry["cwd"] = str(src_dir)

    if graph_path:
        abs_graph = Path(graph_path).resolve()
        entry["env"] = {"HCKG_DEFAULT_GRAPH": str(abs_graph)}

    return entry


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------


@click.group("install")
def install_group() -> None:
    """Register hc-enterprise-kg with LLM clients (Claude Desktop, etc.)."""


@install_group.command("claude")
@click.option(
    "--config", "config_path", type=click.Path(), default=None,
    help="Path to claude_desktop_config.json. Auto-detected if omitted.",
)
@click.option(
    "--graph", "graph_path", type=click.Path(), default=None,
    help="Default graph file to auto-load on startup.",
)
@click.option(
    "--skip-checks", is_flag=True, default=False,
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
      hckg install claude --skip-checks
    """
    # --- Resolve config path ---
    if config_path:
        conf_file = Path(config_path).expanduser()
    else:
        conf_file = _detect_claude_config_path()
        if conf_file is None:
            click.echo("  Error: could not detect Claude Desktop config path.", err=True)
            click.echo("  Specify manually: --config <path>", err=True)
            raise SystemExit(1)

    python_path = _detect_python_path()
    project_root = _detect_project_root()

    click.echo()
    click.echo("  Environment")
    click.echo(f"    Python:  {python_path}")
    click.echo(f"    Config:  {conf_file}")
    if project_root:
        click.echo(f"    Source:  {project_root}")
    else:
        click.echo("    Source:  (installed package — no source checkout detected)")

    # --- Validate --graph path ---
    if graph_path:
        abs_graph = Path(graph_path).resolve()
        if not abs_graph.exists():
            click.echo()
            click.echo(f"  Warning: graph file not found: {abs_graph}")
            click.echo("  The server will start without a pre-loaded graph.")
        click.echo(f"    Graph:   {abs_graph}")

    # --- Pre-flight checks ---
    if not skip_checks:
        click.echo()
        click.echo("  Pre-flight checks")
        checks = _run_preflight(python_path)
        failures = _print_checks(checks)
        if failures > 0:
            click.echo()
            click.echo(
                f"  {failures} check(s) failed. Resolve the issues above "
                "or use --skip-checks to bypass."
            )
            raise SystemExit(1)

    # --- Write config ---
    click.echo()
    server_entry = _build_server_entry(python_path, project_root, graph_path)
    existing = _read_config(conf_file)

    if "mcpServers" not in existing or not isinstance(existing.get("mcpServers"), dict):
        existing["mcpServers"] = {}

    if "hc-enterprise-kg" in existing["mcpServers"]:
        click.echo("  Updating existing registration...")
    else:
        click.echo("  Registering new MCP server...")

    existing["mcpServers"]["hc-enterprise-kg"] = server_entry
    _write_config(conf_file, existing)

    click.echo(f"  Written to {conf_file}")
    click.echo()
    click.echo("  Next steps:")
    click.echo("    1. Restart Claude Desktop")
    click.echo('    2. Ask Claude: "Load the graph and show me statistics"')


# ---------------------------------------------------------------------------
# doctor
# ---------------------------------------------------------------------------


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

    # --- Config file ---
    if conf_file is None:
        click.echo("  Could not determine config file location for this OS.")
        raise SystemExit(1)
    if not conf_file.exists():
        click.echo(f"  Config file not found: {conf_file}")
        click.echo("  Run: hckg install claude")
        raise SystemExit(1)

    config = _read_config(conf_file)
    servers = config.get("mcpServers")
    if not isinstance(servers, dict):
        click.echo("  Config file has no valid 'mcpServers' object.")
        click.echo("  Run: hckg install claude")
        raise SystemExit(1)

    if "hc-enterprise-kg" not in servers:
        click.echo("  hc-enterprise-kg is not registered.")
        click.echo("  Run: hckg install claude")
        raise SystemExit(1)

    entry = servers["hc-enterprise-kg"]
    if not isinstance(entry, dict):
        click.echo("  hc-enterprise-kg entry is not a valid JSON object.")
        click.echo("  Run: hckg install claude")
        raise SystemExit(1)

    python_path = entry.get("command", "")
    args = entry.get("args", [])
    cwd = entry.get("cwd", "")

    click.echo("  Registered config:")
    click.echo(f"    command: {python_path}")
    click.echo(f"    args:    {args}")
    if cwd:
        click.echo(f"    cwd:     {cwd}")
    if "env" in entry and isinstance(entry["env"], dict):
        for k, v in entry["env"].items():
            click.echo(f"    env:     {k}={v}")
    click.echo()

    # --- Run all checks ---
    checks: list[tuple[str, bool, str]] = []

    # 1. command field present and non-empty
    if not python_path:
        checks.append(("Command", False, "no 'command' field in registration"))
    elif not Path(python_path).exists():
        checks.append((
            "Command",
            False,
            f"interpreter not found: {python_path}\n"
            "  The virtualenv may have been deleted. Re-run: hckg install claude",
        ))
    else:
        checks.append(("Command", True, python_path))

    # 2. args format
    expected_args = ["-m", "mcp_server.server"]
    if args == expected_args:
        checks.append(("Args", True, str(args)))
    else:
        checks.append((
            "Args",
            False,
            f"unexpected args: {args}\n"
            f"  Expected: {expected_args}\n"
            "  Re-run: hckg install claude",
        ))

    # 3. cwd (if present) exists
    if cwd:
        if Path(cwd).is_dir():
            checks.append(("Working dir", True, cwd))
        else:
            checks.append((
                "Working dir",
                False,
                f"directory not found: {cwd}\n"
                "  The project may have been moved. Re-run: hckg install claude",
            ))

    # 4. Graph file (if configured)
    env = entry.get("env", {})
    if isinstance(env, dict) and "HCKG_DEFAULT_GRAPH" in env:
        graph = env["HCKG_DEFAULT_GRAPH"]
        if Path(graph).exists():
            checks.append(("Graph file", True, graph))
        else:
            checks.append((
                "Graph file",
                False,
                f"not found: {graph}\n"
                "  Re-generate: hckg demo --clean",
            ))

    # 5-7. Python version, MCP SDK, server module (only if command exists)
    if python_path and Path(python_path).exists():
        runtime_checks = _run_preflight(python_path)
        checks.extend(runtime_checks)

    click.echo("  Validation")
    failures = _print_checks(checks)
    click.echo()

    if failures == 0:
        click.echo("  All checks passed. The MCP server should connect successfully.")
        click.echo("  If issues persist, restart Claude Desktop.")
    else:
        click.echo(f"  {failures} issue(s) found. Resolve them and re-run: hckg install claude")
        raise SystemExit(1)


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------


@install_group.command("status")
def install_status() -> None:
    """Check which LLM clients have hc-enterprise-kg registered."""
    conf_file = _detect_claude_config_path()

    click.echo("  Claude Desktop:")
    if conf_file is None or not conf_file.exists():
        click.echo("    Not found (config file missing)")
        return

    config = _read_config(conf_file)
    servers = config.get("mcpServers", {})
    if not isinstance(servers, dict) or "hc-enterprise-kg" not in servers:
        click.echo("    Not registered")
        click.echo("    Run: hckg install claude")
        return

    entry = servers["hc-enterprise-kg"]
    click.echo("    Registered")
    click.echo(f"    Command: {entry.get('command', '?')}")
    if entry.get("cwd"):
        click.echo(f"    CWD:     {entry['cwd']}")
    if isinstance(entry.get("env"), dict) and "HCKG_DEFAULT_GRAPH" in entry["env"]:
        click.echo(f"    Graph:   {entry['env']['HCKG_DEFAULT_GRAPH']}")


# ---------------------------------------------------------------------------
# remove
# ---------------------------------------------------------------------------


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
        click.echo("  Claude Desktop config not found. Nothing to remove.")
        return

    config = _read_config(conf_file)
    servers = config.get("mcpServers", {})

    if not isinstance(servers, dict) or "hc-enterprise-kg" not in servers:
        click.echo("  hc-enterprise-kg is not registered. Nothing to remove.")
        return

    del servers["hc-enterprise-kg"]
    _write_config(conf_file, config)
    click.echo("  Removed from Claude Desktop.")
    click.echo("  Restart Claude Desktop to apply changes.")
