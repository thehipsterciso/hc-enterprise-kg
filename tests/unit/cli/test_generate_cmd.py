"""Tests for the hckg generate CLI command."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import patch

if TYPE_CHECKING:
    from pathlib import Path

from click.testing import CliRunner

from cli.main import cli


class TestGenerateHelp:
    def test_help_shows_options(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["generate", "org", "--help"])
        assert result.exit_code == 0
        assert "--profile" in result.output
        assert "--employees" in result.output
        assert "--output" in result.output


class TestGenerateOutput:
    def test_output_creates_parent_dirs(self, tmp_path):
        nested = tmp_path / "a" / "b" / "graph.json"
        runner = CliRunner()
        result = runner.invoke(
            cli, ["generate", "org", "--employees", "10", "--output", str(nested)]
        )
        assert result.exit_code == 0
        assert nested.exists()

    def test_output_permission_error(self, tmp_path):
        output = tmp_path / "graph.json"
        runner = CliRunner()
        with patch(
            "export.json_export.JSONExporter.export",
            side_effect=PermissionError("denied"),
        ):
            result = runner.invoke(
                cli, ["generate", "org", "--employees", "10", "--output", str(output)]
            )
            assert result.exit_code != 0


class TestGenerateRuns:
    def test_default_generation(self, tmp_path):
        output = tmp_path / "graph.json"
        runner = CliRunner()
        result = runner.invoke(
            cli, ["generate", "org", "--employees", "10", "--output", str(output)]
        )
        assert result.exit_code == 0
        assert output.exists()
        assert "Generation complete" in result.output

    def test_all_profiles(self, tmp_path):
        for profile in ("tech", "healthcare", "financial"):
            output = tmp_path / f"{profile}.json"
            runner = CliRunner()
            result = runner.invoke(
                cli,
                [
                    "generate",
                    "org",
                    "--profile",
                    profile,
                    "--employees",
                    "10",
                    "--output",
                    str(output),
                ],
            )
            assert result.exit_code == 0, f"{profile} failed: {result.output}"


class TestGenerateClaudeSync:
    def test_syncs_claude_config_when_registered(self, tmp_path: Path):
        """Generate updates Claude Desktop config with new graph path."""
        config_path = tmp_path / "claude_config.json"
        config_path.write_text(
            json.dumps(
                {
                    "mcpServers": {
                        "hc-enterprise-kg": {
                            "command": "python",
                            "args": ["-m", "mcp_server.server"],
                            "env": {"HCKG_DEFAULT_GRAPH": "/old/graph.json"},
                        }
                    }
                }
            )
        )
        output = tmp_path / "graph.json"
        with patch("cli.install_cmd._detect_claude_config_path", return_value=config_path):
            result = CliRunner().invoke(
                cli, ["generate", "org", "--employees", "10", "--output", str(output)]
            )
        assert result.exit_code == 0, result.output
        assert "Claude Desktop config updated" in result.output
        config = json.loads(config_path.read_text())
        assert config["mcpServers"]["hc-enterprise-kg"]["env"]["HCKG_DEFAULT_GRAPH"] == str(
            output.resolve()
        )

    def test_no_sync_when_not_registered(self, tmp_path: Path):
        """Generate does not crash or print sync message when not registered."""
        config_path = tmp_path / "claude_config.json"
        config_path.write_text(json.dumps({"mcpServers": {}}))
        output = tmp_path / "graph.json"
        with patch("cli.install_cmd._detect_claude_config_path", return_value=config_path):
            result = CliRunner().invoke(
                cli, ["generate", "org", "--employees", "10", "--output", str(output)]
            )
        assert result.exit_code == 0, result.output
        assert "Claude Desktop config updated" not in result.output
