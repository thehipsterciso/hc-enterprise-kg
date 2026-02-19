"""Tests for the hckg mcp install/status/uninstall CLI commands."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from click.testing import CliRunner

from cli.main import cli


class TestMcpInstall:
    def test_install_creates_config(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "claude_desktop_config.json"
            result = runner.invoke(
                cli, ["mcp", "install", "--config", str(config_path)]
            )
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
            # Write existing config with another server
            existing = {
                "mcpServers": {
                    "other-server": {"command": "node", "args": ["server.js"]},
                }
            }
            config_path.write_text(json.dumps(existing))

            result = runner.invoke(
                cli, ["mcp", "install", "--config", str(config_path)]
            )
            assert result.exit_code == 0, result.output

            config = json.loads(config_path.read_text())
            # Both servers should be present
            assert "other-server" in config["mcpServers"]
            assert "hc-enterprise-kg" in config["mcpServers"]

    def test_install_with_graph_option(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "claude_desktop_config.json"
            graph_path = Path(tmpdir) / "graph.json"
            graph_path.write_text("{}")  # Dummy file

            result = runner.invoke(
                cli,
                ["mcp", "install", "--config", str(config_path), "--graph", str(graph_path)],
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

            # Install once
            runner.invoke(cli, ["mcp", "install", "--config", str(config_path)])

            # Install again — should update, not error
            result = runner.invoke(
                cli, ["mcp", "install", "--config", str(config_path)]
            )
            assert result.exit_code == 0, result.output
            assert "Updating" in result.output or "registered" in result.output


class TestMcpStatus:
    def test_status_when_registered(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "claude_desktop_config.json"
            # Install first
            runner.invoke(cli, ["mcp", "install", "--config", str(config_path)])

            # Patch _detect_config_path to return our temp config
            from cli import mcp_cmd
            original = mcp_cmd._detect_config_path

            try:
                mcp_cmd._detect_config_path = lambda: config_path
                result = runner.invoke(cli, ["mcp", "status"])
                assert result.exit_code == 0, result.output
                assert "✓" in result.output or "registered" in result.output
            finally:
                mcp_cmd._detect_config_path = original

    def test_status_when_not_registered(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "claude_desktop_config.json"
            config_path.write_text(json.dumps({"mcpServers": {}}))

            from cli import mcp_cmd
            original = mcp_cmd._detect_config_path

            try:
                mcp_cmd._detect_config_path = lambda: config_path
                result = runner.invoke(cli, ["mcp", "status"])
                assert result.exit_code == 0
                assert "NOT" in result.output or "not" in result.output
            finally:
                mcp_cmd._detect_config_path = original


class TestMcpUninstall:
    def test_uninstall_removes_entry(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "claude_desktop_config.json"
            # Install first
            runner.invoke(cli, ["mcp", "install", "--config", str(config_path)])

            # Patch _detect_config_path
            from cli import mcp_cmd
            original = mcp_cmd._detect_config_path

            try:
                mcp_cmd._detect_config_path = lambda: config_path
                result = runner.invoke(cli, ["mcp", "uninstall"])
                assert result.exit_code == 0, result.output
                assert "removed" in result.output

                config = json.loads(config_path.read_text())
                assert "hc-enterprise-kg" not in config.get("mcpServers", {})
            finally:
                mcp_cmd._detect_config_path = original

    def test_uninstall_when_not_registered(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "claude_desktop_config.json"
            config_path.write_text(json.dumps({"mcpServers": {}}))

            from cli import mcp_cmd
            original = mcp_cmd._detect_config_path

            try:
                mcp_cmd._detect_config_path = lambda: config_path
                result = runner.invoke(cli, ["mcp", "uninstall"])
                assert result.exit_code == 0
                assert "not registered" in result.output or "Nothing" in result.output
            finally:
                mcp_cmd._detect_config_path = original
