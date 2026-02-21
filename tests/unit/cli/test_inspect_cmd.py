"""Tests for the hckg inspect CLI command."""

from __future__ import annotations

from click.testing import CliRunner

from cli.main import cli


class TestInspectHelp:
    def test_help_shows_options(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["inspect", "--help"])
        assert result.exit_code == 0
        assert "SOURCE" in result.output


class TestInspectErrors:
    def test_malformed_json(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("not json at all {{{")
        runner = CliRunner()
        result = runner.invoke(cli, ["inspect", str(bad)])
        assert result.exit_code != 0
        assert "could not load" in result.output or "Invalid JSON" in result.output

    def test_empty_file(self, tmp_path):
        empty = tmp_path / "empty.json"
        empty.write_text("")
        runner = CliRunner()
        result = runner.invoke(cli, ["inspect", str(empty)])
        assert result.exit_code != 0

    def test_nonexistent_file(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["inspect", "/tmp/nonexistent_xyz_abc.json"])
        assert result.exit_code != 0


class TestInspectValid:
    def test_valid_graph(self, tmp_path):
        from export.json_export import JSONExporter
        from graph.knowledge_graph import KnowledgeGraph
        from synthetic.orchestrator import SyntheticOrchestrator
        from synthetic.profiles.tech_company import mid_size_tech_company

        kg = KnowledgeGraph()
        profile = mid_size_tech_company(10)
        SyntheticOrchestrator(kg, profile, seed=42).generate()
        path = tmp_path / "graph.json"
        JSONExporter().export(kg.engine, path)

        runner = CliRunner()
        result = runner.invoke(cli, ["inspect", str(path)])
        assert result.exit_code == 0
        assert "Knowledge Graph Summary" in result.output
        assert "Total entities:" in result.output

    def test_empty_graph(self, tmp_path):
        path = tmp_path / "empty_graph.json"
        path.write_text('{"entities": [], "relationships": []}')
        runner = CliRunner()
        result = runner.invoke(cli, ["inspect", str(path)])
        assert result.exit_code == 0
        assert "Total entities:      0" in result.output
