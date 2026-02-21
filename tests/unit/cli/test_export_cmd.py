"""Tests for the hckg export CLI command."""

from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from cli.main import cli


def _make_graph_file(tmp_path):
    """Create a small valid graph file and return its path."""
    from export.json_export import JSONExporter
    from graph.knowledge_graph import KnowledgeGraph
    from synthetic.orchestrator import SyntheticOrchestrator
    from synthetic.profiles.tech_company import mid_size_tech_company

    kg = KnowledgeGraph()
    profile = mid_size_tech_company(10)
    SyntheticOrchestrator(kg, profile, seed=42).generate()
    path = tmp_path / "source.json"
    JSONExporter().export(kg.engine, path)
    return path


class TestExportHelp:
    def test_help_shows_options(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["export", "--help"])
        assert result.exit_code == 0
        assert "--source" in result.output
        assert "--output" in result.output
        assert "--format" in result.output


class TestExportErrors:
    def test_malformed_source(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("not json {{{")
        output = tmp_path / "out.json"
        runner = CliRunner()
        result = runner.invoke(cli, ["export", "--source", str(bad), "--output", str(output)])
        assert result.exit_code != 0

    def test_permission_error_on_write(self, tmp_path):
        source = _make_graph_file(tmp_path)
        output = tmp_path / "out.json"
        with patch(
            "export.json_export.JSONExporter.export",
            side_effect=PermissionError("denied"),
        ):
            runner = CliRunner()
            result = runner.invoke(
                cli, ["export", "--source", str(source), "--output", str(output)]
            )
            assert result.exit_code != 0


class TestExportValid:
    def test_json_round_trip(self, tmp_path):
        source = _make_graph_file(tmp_path)
        output = tmp_path / "exported.json"
        runner = CliRunner()
        result = runner.invoke(cli, ["export", "--source", str(source), "--output", str(output)])
        assert result.exit_code == 0
        assert output.exists()
        assert "Exported to" in result.output

    def test_output_creates_parent_dirs(self, tmp_path):
        source = _make_graph_file(tmp_path)
        output = tmp_path / "a" / "b" / "out.json"
        runner = CliRunner()
        result = runner.invoke(cli, ["export", "--source", str(source), "--output", str(output)])
        assert result.exit_code == 0
        assert output.exists()
