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
        assert "REST API" in result.output or "server" in result.output
        assert "--port" in result.output
        assert "--host" in result.output
