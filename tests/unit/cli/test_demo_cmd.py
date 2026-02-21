"""Tests for the hckg demo CLI command."""

from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from cli.main import cli


class TestDemoHelp:
    def test_help_shows_options(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["demo", "--help"])
        assert result.exit_code == 0
        assert "--profile" in result.output
        assert "--employees" in result.output
        assert "--clean" in result.output
        assert "--format" in result.output


class TestDemoClean:
    def test_clean_removes_files(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "graph.json").write_text("{}")
        (tmp_path / "graph.graphml").write_text("")
        (tmp_path / "test_viz.html").write_text("")

        runner = CliRunner()
        result = runner.invoke(cli, ["demo", "--clean", "--employees", "10"])
        assert result.exit_code == 0
        assert "Cleaned" in result.output

    def test_clean_warns_on_locked_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        target = tmp_path / "graph.json"
        target.write_text("{}")

        with patch("pathlib.Path.unlink", side_effect=OSError("locked")):
            runner = CliRunner()
            result = runner.invoke(cli, ["demo", "--clean", "--employees", "10"])
            # Should still succeed — clean failure is a warning, not fatal
            assert result.exit_code == 0
            assert "could not remove" in result.output or "Nothing to clean" in result.output

    def test_clean_nothing_to_clean(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()
        result = runner.invoke(cli, ["demo", "--employees", "10"])
        assert result.exit_code == 0


class TestDemoOutput:
    def test_output_creates_parent_dirs(self, tmp_path):
        nested = tmp_path / "a" / "b" / "c" / "graph.json"
        runner = CliRunner()
        result = runner.invoke(cli, ["demo", "--employees", "10", "--output", str(nested)])
        assert result.exit_code == 0
        assert nested.exists()

    def test_output_permission_error(self, tmp_path):
        """Export failure shows clean error."""
        output = tmp_path / "graph.json"
        runner = CliRunner()
        with patch(
            "export.json_export.JSONExporter.export",
            side_effect=PermissionError("denied"),
        ):
            result = runner.invoke(cli, ["demo", "--employees", "10", "--output", str(output)])
            assert result.exit_code != 0


class TestDemoGeneration:
    def test_default_run(self, tmp_path):
        output = tmp_path / "graph.json"
        runner = CliRunner()
        result = runner.invoke(cli, ["demo", "--employees", "10", "--output", str(output)])
        assert result.exit_code == 0
        assert output.exists()
        assert "Total entities:" in result.output

    def test_profiles(self, tmp_path):
        for profile in ("tech", "healthcare", "financial"):
            output = tmp_path / f"{profile}.json"
            runner = CliRunner()
            result = runner.invoke(
                cli,
                ["demo", "--profile", profile, "--employees", "10", "--output", str(output)],
            )
            assert result.exit_code == 0, f"{profile} failed: {result.output}"
            assert output.exists()

    def test_graphml_format(self, tmp_path):
        output = tmp_path / "graph.graphml"
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["demo", "--employees", "10", "--format", "graphml", "--output", str(output)],
        )
        assert result.exit_code == 0
        assert output.exists()
