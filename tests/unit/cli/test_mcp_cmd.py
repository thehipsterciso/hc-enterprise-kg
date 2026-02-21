"""Tests for the hckg install claude/status/remove/doctor CLI commands."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from cli import install_cmd
from cli.main import cli

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _setup_project_tree(tmpdir: str) -> Path:
    """Create a minimal project tree with mcp_server/server.py."""
    root = Path(tmpdir) / "project"
    (root / "src" / "mcp_server").mkdir(parents=True)
    (root / "src" / "mcp_server" / "server.py").write_text("# server\n")
    (root / "pyproject.toml").write_text("[project]\nname = 'test'\n")
    return root


class TestInstallClaude:
    def test_install_creates_config(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "claude_desktop_config.json"
            result = runner.invoke(cli, ["install", "claude", "--config", str(config_path)])
            assert result.exit_code == 0, result.output
            assert config_path.exists()

            config = json.loads(config_path.read_text())
            assert "mcpServers" in config
            assert "hc-enterprise-kg" in config["mcpServers"]

            server = config["mcpServers"]["hc-enterprise-kg"]
            assert "command" in server
            assert server["args"] == ["-m", "mcp_server.server"]

    def test_install_preserves_existing_config(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "claude_desktop_config.json"
            existing = {
                "mcpServers": {
                    "other-server": {"command": "node", "args": ["server.js"]},
                }
            }
            config_path.write_text(json.dumps(existing))

            result = runner.invoke(cli, ["install", "claude", "--config", str(config_path)])
            assert result.exit_code == 0, result.output

            config = json.loads(config_path.read_text())
            assert "other-server" in config["mcpServers"]
            assert "hc-enterprise-kg" in config["mcpServers"]

    def test_install_with_graph_option(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "claude_desktop_config.json"
            graph_path = Path(tmpdir) / "graph.json"
            graph_path.write_text("{}")

            result = runner.invoke(
                cli,
                [
                    "install",
                    "claude",
                    "--config",
                    str(config_path),
                    "--graph",
                    str(graph_path),
                ],
            )
            assert result.exit_code == 0, result.output

            config = json.loads(config_path.read_text())
            server = config["mcpServers"]["hc-enterprise-kg"]
            assert "env" in server
            assert "HCKG_DEFAULT_GRAPH" in server["env"]

    def test_install_update_existing(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "claude_desktop_config.json"

            runner.invoke(cli, ["install", "claude", "--config", str(config_path)])
            result = runner.invoke(cli, ["install", "claude", "--config", str(config_path)])
            assert result.exit_code == 0, result.output
            assert "Updating" in result.output or "Registered" in result.output

    def test_install_skip_checks(self):
        """--skip-checks bypasses pre-flight validation."""
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "claude_desktop_config.json"
            result = runner.invoke(
                cli,
                ["install", "claude", "--config", str(config_path), "--skip-checks"],
            )
            assert result.exit_code == 0, result.output
            assert "Pre-flight" not in result.output
            assert config_path.exists()


class TestPreflightChecks:
    """Tests for the pre-flight validation functions."""

    def test_check_mcp_importable_with_current_python(self):
        """Current test env has mcp installed, so this should pass."""
        ok, detail = install_cmd._check_mcp_importable(sys.executable)
        assert ok is True
        assert "importable" in detail

    def test_check_mcp_importable_bad_interpreter(self):
        """Non-existent interpreter should fail gracefully."""
        ok, detail = install_cmd._check_mcp_importable("/nonexistent/python")
        assert ok is False
        assert "not found" in detail

    def test_check_mcp_importable_missing_module(self):
        """Python without mcp should report the fix command."""
        # Use a subprocess that will fail the import
        ok, detail = install_cmd._check_mcp_importable(sys.executable)
        # We can't easily test "missing mcp" with the current interpreter,
        # so we mock subprocess.run to simulate it
        import subprocess

        fake_result = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="",
            stderr="ModuleNotFoundError: No module named 'mcp'",
        )
        with patch("cli.install_cmd.subprocess.run", return_value=fake_result):
            ok, detail = install_cmd._check_mcp_importable(sys.executable)
            assert ok is False
            assert "poetry install --extras mcp" in detail

    def test_check_server_module_exists(self):
        """Server module check passes when file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = _setup_project_tree(tmpdir)
            ok, detail = install_cmd._check_server_module(root)
            assert ok is True
            assert "found" in detail

    def test_check_server_module_missing(self):
        """Server module check fails when file is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "empty"
            root.mkdir()
            ok, detail = install_cmd._check_server_module(root)
            assert ok is False
            assert "not found" in detail

    def test_check_python_version(self):
        """Python version check returns version string."""
        ok, detail = install_cmd._check_python_version(sys.executable)
        assert ok is True
        assert "Python" in detail

    def test_check_python_version_bad_interpreter(self):
        """Non-existent interpreter reports failure."""
        ok, detail = install_cmd._check_python_version("/nonexistent/python")
        assert ok is False

    def test_run_preflight_all_pass(self):
        """Full pre-flight with valid environment."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = _setup_project_tree(tmpdir)
            checks = install_cmd._run_preflight(sys.executable, root)
            assert len(checks) == 3
            assert all(passed for _, passed, _ in checks)

    def test_run_preflight_missing_server(self):
        """Pre-flight detects missing server module."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "empty"
            root.mkdir()
            checks = install_cmd._run_preflight(sys.executable, root)
            # Server module check should fail
            server_check = [c for c in checks if c[0] == "Server module"][0]
            assert server_check[1] is False

    def test_install_fails_on_preflight_failure(self):
        """Install exits with error when pre-flight fails."""
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "claude_desktop_config.json"

            # Mock _check_mcp_importable to simulate missing mcp
            import subprocess as sp

            fake = sp.CompletedProcess(
                args=[], returncode=1, stdout="",
                stderr="ModuleNotFoundError: No module named 'mcp'",
            )
            with patch("cli.install_cmd.subprocess.run", return_value=fake):
                result = runner.invoke(
                    cli, ["install", "claude", "--config", str(config_path)]
                )
                assert result.exit_code != 0
                assert "FAIL" in result.output
                assert "poetry install --extras mcp" in result.output
                # Config should NOT be written
                assert not config_path.exists()

    def test_print_checks_counts_failures(self):
        """_print_checks returns correct failure count."""
        checks = [
            ("Check A", True, "all good"),
            ("Check B", False, "broken\n  Fix: do something"),
            ("Check C", True, "fine"),
        ]
        failures = install_cmd._print_checks(checks)
        assert failures == 1


class TestInstallDoctor:
    def test_doctor_all_pass(self):
        """Doctor passes when registration is valid."""
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = _setup_project_tree(tmpdir)
            config_path = Path(tmpdir) / "claude_desktop_config.json"
            config = {
                "mcpServers": {
                    "hc-enterprise-kg": {
                        "command": sys.executable,
                        "args": ["-m", "mcp_server.server"],
                        "cwd": str(root / "src"),
                    }
                }
            }
            config_path.write_text(json.dumps(config))

            original = install_cmd._detect_claude_config_path
            try:
                install_cmd._detect_claude_config_path = lambda: config_path
                result = runner.invoke(cli, ["install", "doctor"])
                assert result.exit_code == 0, result.output
                assert "All checks passed" in result.output
            finally:
                install_cmd._detect_claude_config_path = original

    def test_doctor_missing_python(self):
        """Doctor catches a non-existent Python interpreter."""
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = _setup_project_tree(tmpdir)
            config_path = Path(tmpdir) / "claude_desktop_config.json"
            config = {
                "mcpServers": {
                    "hc-enterprise-kg": {
                        "command": "/nonexistent/python",
                        "args": ["-m", "mcp_server.server"],
                        "cwd": str(root / "src"),
                    }
                }
            }
            config_path.write_text(json.dumps(config))

            original = install_cmd._detect_claude_config_path
            try:
                install_cmd._detect_claude_config_path = lambda: config_path
                result = runner.invoke(cli, ["install", "doctor"])
                assert result.exit_code != 0
                assert "FAIL" in result.output
                assert "not found" in result.output
            finally:
                install_cmd._detect_claude_config_path = original

    def test_doctor_missing_cwd(self):
        """Doctor catches a non-existent CWD."""
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "claude_desktop_config.json"
            config = {
                "mcpServers": {
                    "hc-enterprise-kg": {
                        "command": sys.executable,
                        "args": ["-m", "mcp_server.server"],
                        "cwd": "/nonexistent/path/src",
                    }
                }
            }
            config_path.write_text(json.dumps(config))

            original = install_cmd._detect_claude_config_path
            try:
                install_cmd._detect_claude_config_path = lambda: config_path
                result = runner.invoke(cli, ["install", "doctor"])
                assert result.exit_code != 0
                assert "FAIL" in result.output
            finally:
                install_cmd._detect_claude_config_path = original

    def test_doctor_not_registered(self):
        """Doctor reports when not registered."""
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "claude_desktop_config.json"
            config_path.write_text(json.dumps({"mcpServers": {}}))

            original = install_cmd._detect_claude_config_path
            try:
                install_cmd._detect_claude_config_path = lambda: config_path
                result = runner.invoke(cli, ["install", "doctor"])
                assert result.exit_code != 0
                assert "not registered" in result.output
            finally:
                install_cmd._detect_claude_config_path = original


class TestInstallStatus:
    def test_status_when_registered(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "claude_desktop_config.json"
            runner.invoke(cli, ["install", "claude", "--config", str(config_path)])

            original = install_cmd._detect_claude_config_path

            try:
                install_cmd._detect_claude_config_path = lambda: config_path
                result = runner.invoke(cli, ["install", "status"])
                assert result.exit_code == 0, result.output
                assert "Registered" in result.output
            finally:
                install_cmd._detect_claude_config_path = original

    def test_status_when_not_registered(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "claude_desktop_config.json"
            config_path.write_text(json.dumps({"mcpServers": {}}))

            original = install_cmd._detect_claude_config_path

            try:
                install_cmd._detect_claude_config_path = lambda: config_path
                result = runner.invoke(cli, ["install", "status"])
                assert result.exit_code == 0
                assert "Not registered" in result.output
            finally:
                install_cmd._detect_claude_config_path = original


class TestInstallRemove:
    def test_remove_claude(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "claude_desktop_config.json"
            runner.invoke(cli, ["install", "claude", "--config", str(config_path)])

            original = install_cmd._detect_claude_config_path

            try:
                install_cmd._detect_claude_config_path = lambda: config_path
                result = runner.invoke(cli, ["install", "remove", "claude"])
                assert result.exit_code == 0, result.output
                assert "Removed" in result.output

                config = json.loads(config_path.read_text())
                assert "hc-enterprise-kg" not in config.get("mcpServers", {})
            finally:
                install_cmd._detect_claude_config_path = original

    def test_remove_when_not_registered(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "claude_desktop_config.json"
            config_path.write_text(json.dumps({"mcpServers": {}}))

            original = install_cmd._detect_claude_config_path

            try:
                install_cmd._detect_claude_config_path = lambda: config_path
                result = runner.invoke(cli, ["install", "remove", "claude"])
                assert result.exit_code == 0
                assert "not registered" in result.output or "Nothing" in result.output
            finally:
                install_cmd._detect_claude_config_path = original
