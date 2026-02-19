"""Tests for the hckg install claude/status/remove CLI commands."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from click.testing import CliRunner

from cli.main import cli


class TestInstallClaude:
    def test_install_creates_config(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "claude_desktop_config.json"
            result = runner.invoke(
                cli, ["install", "claude", "--config", str(config_path)]
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
            existing = {
                "mcpServers": {
                    "other-server": {"command": "node", "args": ["server.js"]},
                }
            }
            config_path.write_text(json.dumps(existing))

            result = runner.invoke(
                cli, ["install", "claude", "--config", str(config_path)]
            )
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
                    "install", "claude",
                    "--config", str(config_path),
                    "--graph", str(graph_path),
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

            runner.invoke(
                cli, ["install", "claude", "--config", str(config_path)]
            )
            result = runner.invoke(
                cli, ["install", "claude", "--config", str(config_path)]
            )
            assert result.exit_code == 0, result.output
            assert "Updating" in result.output or "Registered" in result.output


class TestInstallStatus:
    def test_status_when_registered(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "claude_desktop_config.json"
            runner.invoke(
                cli, ["install", "claude", "--config", str(config_path)]
            )

            from cli import install_cmd
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

            from cli import install_cmd
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
            runner.invoke(
                cli, ["install", "claude", "--config", str(config_path)]
            )

            from cli import install_cmd
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

            from cli import install_cmd
            original = install_cmd._detect_claude_config_path

            try:
                install_cmd._detect_claude_config_path = lambda: config_path
                result = runner.invoke(cli, ["install", "remove", "claude"])
                assert result.exit_code == 0
                assert "not registered" in result.output or "Nothing" in result.output
            finally:
                install_cmd._detect_claude_config_path = original
