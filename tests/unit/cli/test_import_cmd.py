"""Tests for the hckg import CLI command."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

from click.testing import CliRunner

from cli.main import cli

if TYPE_CHECKING:
    import pytest

SAMPLE_ENTITIES_JSON = Path(__file__).parent.parent.parent / "fixtures" / "sample_entities.json"
SAMPLE_ORG_CSV = Path(__file__).parent.parent.parent / "fixtures" / "sample_org.csv"


def _minimal_json(tmp_path: Path) -> Path:
    """Create a minimal valid JSON import file."""
    data = {
        "entities": [
            {"entity_type": "department", "name": "Engineering", "code": "ENG"},
            {"entity_type": "department", "name": "Marketing", "code": "MKT"},
        ],
        "relationships": [],
    }
    path = tmp_path / "minimal.json"
    path.write_text(json.dumps(data))
    return path


def _minimal_csv(tmp_path: Path) -> Path:
    """Create a minimal valid CSV for system import."""
    path = tmp_path / "systems.csv"
    path.write_text(
        "name,system_type,hostname,ip_address\n"
        "Web Server,application,web-01,10.0.1.1\n"
        "DB Server,database,db-01,10.0.1.2\n"
    )
    return path


def _make_graph_file(tmp_path: Path) -> Path:
    """Create a small graph JSON file for merge tests."""
    from export.json_export import JSONExporter
    from graph.knowledge_graph import KnowledgeGraph
    from synthetic.orchestrator import SyntheticOrchestrator
    from synthetic.profiles.tech_company import mid_size_tech_company

    kg = KnowledgeGraph()
    profile = mid_size_tech_company(10)
    SyntheticOrchestrator(kg, profile, seed=42).generate()
    path = tmp_path / "existing.json"
    JSONExporter().export(kg.engine, path)
    return path


class TestImportHelp:
    def test_help_shows_options(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["import", "--help"])
        assert result.exit_code == 0
        assert "--output" in result.output
        assert "--entity-type" in result.output
        assert "--merge" in result.output
        assert "--dry-run" in result.output
        assert "--strict" in result.output
        assert "SOURCE" in result.output


class TestImportJsonValid:
    def test_import_minimal_json(self, tmp_path: Path) -> None:
        src = _minimal_json(tmp_path)
        out = tmp_path / "result.json"
        runner = CliRunner()
        result = runner.invoke(cli, ["import", str(src), "-o", str(out)])
        assert result.exit_code == 0
        assert out.exists()
        assert "2 entities validated" in result.output

    def test_import_sample_entities_json(self, tmp_path: Path) -> None:
        out = tmp_path / "result.json"
        runner = CliRunner()
        result = runner.invoke(cli, ["import", str(SAMPLE_ENTITIES_JSON), "-o", str(out)])
        assert result.exit_code == 0
        assert out.exists()
        assert "Import Summary" in result.output

    def test_output_contains_summary(self, tmp_path: Path) -> None:
        src = _minimal_json(tmp_path)
        out = tmp_path / "result.json"
        runner = CliRunner()
        result = runner.invoke(cli, ["import", str(src), "-o", str(out)])
        assert result.exit_code == 0
        assert "department" in result.output
        assert "Output:" in result.output


class TestImportJsonErrors:
    def test_malformed_json(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.json"
        bad.write_text("not json {{{")
        runner = CliRunner()
        result = runner.invoke(cli, ["import", str(bad)])
        assert result.exit_code != 0
        combined = result.output + str(result.exception or "")
        assert "invalid json" in combined.lower()

    def test_missing_entities_key(self, tmp_path: Path) -> None:
        src = tmp_path / "no_entities.json"
        src.write_text('{"relationships": []}')
        runner = CliRunner()
        result = runner.invoke(cli, ["import", str(src)])
        assert result.exit_code != 0

    def test_empty_json_file(self, tmp_path: Path) -> None:
        src = tmp_path / "empty.json"
        src.write_text("{}")
        runner = CliRunner()
        result = runner.invoke(cli, ["import", str(src)])
        assert result.exit_code != 0

    def test_invalid_entity_type(self, tmp_path: Path) -> None:
        src = tmp_path / "bad_type.json"
        src.write_text(json.dumps({
            "entities": [{"entity_type": "bogus", "name": "Test"}]
        }))
        runner = CliRunner()
        result = runner.invoke(cli, ["import", str(src)])
        assert result.exit_code != 0
        assert "bogus" in result.output


class TestImportCsvValid:
    def test_import_csv_with_auto_detection(self, tmp_path: Path) -> None:
        out = tmp_path / "result.json"
        runner = CliRunner()
        result = runner.invoke(cli, ["import", str(SAMPLE_ORG_CSV), "-o", str(out)])
        assert result.exit_code == 0
        assert out.exists()
        assert "Auto-detected" in result.output

    def test_import_csv_with_entity_type(self, tmp_path: Path) -> None:
        src = _minimal_csv(tmp_path)
        out = tmp_path / "result.json"
        runner = CliRunner()
        result = runner.invoke(
            cli, ["import", str(src), "-t", "system", "-o", str(out)]
        )
        assert result.exit_code == 0
        assert out.exists()


class TestImportCsvErrors:
    def test_invalid_entity_type(self, tmp_path: Path) -> None:
        src = _minimal_csv(tmp_path)
        runner = CliRunner()
        result = runner.invoke(cli, ["import", str(src), "-t", "bogus_type"])
        assert result.exit_code != 0
        assert "bogus_type" in result.output

    def test_no_detection_unrecognizable_csv(self, tmp_path: Path) -> None:
        src = tmp_path / "weird.csv"
        src.write_text("col_a,col_b,col_c\n1,2,3\n")
        runner = CliRunner()
        result = runner.invoke(cli, ["import", str(src)])
        assert result.exit_code != 0
        assert "could not auto-detect" in result.output.lower()

    def test_empty_csv(self, tmp_path: Path) -> None:
        src = tmp_path / "empty.csv"
        src.write_text("")
        runner = CliRunner()
        result = runner.invoke(cli, ["import", str(src)])
        assert result.exit_code != 0


class TestImportDryRun:
    def test_dry_run_validates_only(self, tmp_path: Path) -> None:
        src = _minimal_json(tmp_path)
        out = tmp_path / "should_not_exist.json"
        runner = CliRunner()
        result = runner.invoke(
            cli, ["import", str(src), "-o", str(out), "--dry-run"]
        )
        assert result.exit_code == 0
        assert not out.exists()
        assert "Dry run complete" in result.output

    def test_dry_run_csv(self, tmp_path: Path) -> None:
        out = tmp_path / "nope.json"
        runner = CliRunner()
        result = runner.invoke(
            cli, ["import", str(SAMPLE_ORG_CSV), "-o", str(out), "--dry-run"]
        )
        assert result.exit_code == 0
        assert not out.exists()


class TestImportStrict:
    def test_strict_fails_on_warnings(self, tmp_path: Path) -> None:
        src = tmp_path / "with_typo.json"
        src.write_text(json.dumps({
            "entities": [
                {
                    "entity_type": "department",
                    "name": "Eng",
                    "typo_field": "oops",
                }
            ]
        }))
        runner = CliRunner()
        result = runner.invoke(cli, ["import", str(src), "--strict"])
        assert result.exit_code != 0
        assert "strict" in result.output.lower()

    def test_no_warnings_passes_strict(self, tmp_path: Path) -> None:
        src = _minimal_json(tmp_path)
        out = tmp_path / "result.json"
        runner = CliRunner()
        result = runner.invoke(
            cli, ["import", str(src), "-o", str(out), "--strict"]
        )
        assert result.exit_code == 0
        assert out.exists()


class TestImportMerge:
    def test_merge_into_existing(self, tmp_path: Path) -> None:
        existing = _make_graph_file(tmp_path)
        new_data = _minimal_json(tmp_path)
        out = tmp_path / "merged.json"
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["import", str(new_data), "-m", str(existing), "-o", str(out)],
        )
        assert result.exit_code == 0
        assert out.exists()
        assert "Merging" in result.output

        # Verify merged graph has more entities than the new data alone
        with open(out) as f:
            merged = json.load(f)
        assert len(merged["entities"]) > 2  # more than the 2 departments we added


class TestImportOutput:
    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        src = _minimal_json(tmp_path)
        nested = tmp_path / "a" / "b" / "result.json"
        runner = CliRunner()
        result = runner.invoke(cli, ["import", str(src), "-o", str(nested)])
        assert result.exit_code == 0
        assert nested.exists()

    def test_permission_error(self, tmp_path: Path) -> None:
        src = _minimal_json(tmp_path)
        with patch(
            "export.json_export.JSONExporter.export",
            side_effect=PermissionError("denied"),
        ):
            runner = CliRunner()
            result = runner.invoke(
                cli, ["import", str(src), "-o", str(tmp_path / "out.json")]
            )
            assert result.exit_code != 0
            assert "permission denied" in result.output.lower()


class TestImportClaudeSync:
    def test_sync_called_on_success(self, tmp_path: Path) -> None:
        src = _minimal_json(tmp_path)
        out = tmp_path / "result.json"
        with patch("cli.install_cmd.sync_claude_graph_path", return_value=True) as mock_sync:
            runner = CliRunner()
            result = runner.invoke(cli, ["import", str(src), "-o", str(out)])
            assert result.exit_code == 0
            mock_sync.assert_called_once()


class TestImportMapping:
    def _make_mapping(self, tmp_path: Path) -> Path:
        mapping = {
            "entity_type": "person",
            "name_field": "Full_Name",
            "columns": {
                "First": "first_name",
                "Last": "last_name",
                "Mail": "email",
            },
        }
        path = tmp_path / "test.mapping.json"
        path.write_text(json.dumps(mapping))
        return path

    def _make_mapped_csv(self, tmp_path: Path) -> Path:
        path = tmp_path / "hr_export.csv"
        path.write_text(
            "Full_Name,First,Last,Mail\n"
            "Alice Smith,Alice,Smith,alice@acme.com\n"
            "Bob Jones,Bob,Jones,bob@acme.com\n"
        )
        return path

    def test_mapping_with_csv(self, tmp_path: Path) -> None:
        csv_path = self._make_mapped_csv(tmp_path)
        mapping_path = self._make_mapping(tmp_path)
        out = tmp_path / "result.json"
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["import", str(csv_path), "--mapping", str(mapping_path), "-o", str(out)],
        )
        assert result.exit_code == 0
        assert out.exists()
        assert "Using mapping" in result.output

        with open(out) as f:
            data = json.load(f)
        assert len(data["entities"]) == 2

    def test_mapping_mutual_exclusion_with_entity_type(self, tmp_path: Path) -> None:
        csv_path = self._make_mapped_csv(tmp_path)
        mapping_path = self._make_mapping(tmp_path)
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["import", str(csv_path), "--mapping", str(mapping_path), "-t", "person"],
        )
        assert result.exit_code != 0
        assert "mutually exclusive" in result.output.lower()

    def test_mapping_not_supported_for_json(self, tmp_path: Path) -> None:
        src = _minimal_json(tmp_path)
        mapping_path = self._make_mapping(tmp_path)
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["import", str(src), "--mapping", str(mapping_path)],
        )
        assert result.exit_code != 0
        assert "csv" in result.output.lower()

    def test_mapping_invalid_format(self, tmp_path: Path) -> None:
        csv_path = self._make_mapped_csv(tmp_path)
        bad_mapping = tmp_path / "bad.mapping.json"
        bad_mapping.write_text('{"entity_type": "bogus"}')
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["import", str(csv_path), "--mapping", str(bad_mapping)],
        )
        assert result.exit_code != 0

    def test_help_shows_mapping_option(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["import", "--help"])
        assert "--mapping" in result.output


class TestImportEdgeCases:
    def test_unsupported_format(self, tmp_path: Path) -> None:
        src = tmp_path / "data.xml"
        src.write_text("<root/>")
        runner = CliRunner()
        result = runner.invoke(cli, ["import", str(src)])
        assert result.exit_code != 0
        assert "unsupported file format" in result.output.lower()

    def test_file_not_found(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["import", "/nonexistent/file.json"])
        assert result.exit_code != 0

    def test_default_output_path(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Default output is graph.json in current directory."""
        monkeypatch.chdir(tmp_path)
        src = _minimal_json(tmp_path)
        runner = CliRunner()
        result = runner.invoke(cli, ["import", str(src)])
        assert result.exit_code == 0
        assert (tmp_path / "graph.json").exists()

    def test_json_root_not_object(self, tmp_path: Path) -> None:
        src = tmp_path / "array.json"
        src.write_text("[1, 2, 3]")
        runner = CliRunner()
        result = runner.invoke(cli, ["import", str(src)])
        assert result.exit_code != 0
        assert "object" in result.output.lower()
