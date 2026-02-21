"""Tests for the hckg auto CLI command."""

from __future__ import annotations

from click.testing import CliRunner

from cli.main import cli


class TestAutoHelp:
    def test_build_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["auto", "build", "--help"])
        assert result.exit_code == 0
        assert "--demo" in result.output
        assert "--output" in result.output

    def test_extract_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["auto", "extract", "--help"])
        assert result.exit_code == 0
        assert "TEXT" in result.output


class TestAutoBuild:
    def test_missing_source_and_no_demo(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["auto", "build"])
        assert result.exit_code != 0
        assert "SOURCE" in result.output or "source" in result.output.lower()

    def test_demo_mode_runs(self, tmp_path):
        output = tmp_path / "result.json"
        runner = CliRunner()
        result = runner.invoke(cli, ["auto", "build", "--demo", "--output", str(output)])
        assert result.exit_code == 0
        assert "Pipeline results" in result.output
        assert output.exists()

    def test_demo_cleans_temp_file(self, tmp_path):
        """Demo mode should not leave temp files behind."""
        import glob
        import tempfile

        before = set(glob.glob(f"{tempfile.gettempdir()}/hckg_demo_*"))
        output = tmp_path / "result.json"
        runner = CliRunner()
        runner.invoke(cli, ["auto", "build", "--demo", "--output", str(output)])
        after = set(glob.glob(f"{tempfile.gettempdir()}/hckg_demo_*"))
        # No new temp files should remain
        new_files = after - before
        assert len(new_files) == 0, f"Temp files leaked: {new_files}"

    def test_output_creates_parent_dirs(self, tmp_path):
        output = tmp_path / "a" / "b" / "result.json"
        runner = CliRunner()
        result = runner.invoke(cli, ["auto", "build", "--demo", "--output", str(output)])
        assert result.exit_code == 0
        assert output.exists()


class TestAutoExtract:
    def test_extract_finds_entities(self):
        runner = CliRunner()
        result = runner.invoke(
            cli, ["auto", "extract", "John Smith works in Engineering department"]
        )
        assert result.exit_code == 0
        assert "Found" in result.output
