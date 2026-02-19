"""Tests for the hckg serve CLI command."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

flask = pytest.importorskip("flask", reason="flask not installed")

from cli.main import cli  # noqa: E402


class TestServeCLI:
    def test_serve_nonexistent_file(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["serve", "/tmp/nonexistent_graph_xyz.json"])
        assert result.exit_code != 0

    def test_serve_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["serve", "--help"])
        assert result.exit_code == 0
        assert "--port" in result.output
        assert "--host" in result.output
        assert "--stdio" in result.output

    def test_serve_help_shows_both_modes(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["serve", "--help"])
        assert result.exit_code == 0
        assert "REST" in result.output
        assert "stdio" in result.output
