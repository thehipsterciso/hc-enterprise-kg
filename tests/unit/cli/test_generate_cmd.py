"""Tests for the hckg generate CLI command."""

from __future__ import annotations

from unittest.mock import patch

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
