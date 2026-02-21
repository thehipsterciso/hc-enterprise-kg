"""Tests for the hckg benchmark CLI command."""

from __future__ import annotations

from click.testing import CliRunner

from cli.main import cli


class TestBenchmarkHelp:
    def test_help_shows_options(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["benchmark", "--help"])
        assert result.exit_code == 0
        assert "--profiles" in result.output
        assert "--scales" in result.output
        assert "--full" in result.output


class TestBenchmarkValidation:
    def test_invalid_scale_string(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["benchmark", "--scales", "abc"])
        assert result.exit_code != 0
        assert "Invalid scale" in result.output or "comma-separated integers" in result.output

    def test_mixed_valid_invalid_scales(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["benchmark", "--scales", "100,abc,500"])
        assert result.exit_code != 0

    def test_invalid_profile(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["benchmark", "--profiles", "invalid"])
        assert result.exit_code != 0
        assert "Unknown profile" in result.output


class TestBenchmarkRuns:
    def test_default_run(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["benchmark", "--scales", "10"])
        assert result.exit_code == 0
        assert "Completed" in result.output

    def test_output_creates_parent_dirs(self, tmp_path):
        output = tmp_path / "a" / "b" / "report.md"
        runner = CliRunner()
        result = runner.invoke(cli, ["benchmark", "--scales", "10", "--output", str(output)])
        assert result.exit_code == 0
        assert output.exists()
