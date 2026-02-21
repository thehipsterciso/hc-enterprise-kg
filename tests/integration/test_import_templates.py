"""Integration tests for import template files.

Validates that all template files in examples/import-templates/ are
syntactically correct and import successfully via the CLI.
"""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from cli.main import cli
from domain.base import EntityType

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "examples" / "import-templates"


class TestJsonTemplate:
    """Tests for the organization.json template."""

    def test_valid_json(self) -> None:
        path = TEMPLATES_DIR / "organization.json"
        data = json.loads(path.read_text())
        assert "entities" in data
        assert "relationships" in data

    def test_contains_all_30_entity_types(self) -> None:
        path = TEMPLATES_DIR / "organization.json"
        data = json.loads(path.read_text())
        types_found = {e["entity_type"] for e in data["entities"]}
        all_types = {et.value for et in EntityType}
        missing = all_types - types_found
        assert not missing, f"Missing entity types in template: {missing}"

    def test_all_entities_have_required_fields(self) -> None:
        path = TEMPLATES_DIR / "organization.json"
        data = json.loads(path.read_text())
        for entity in data["entities"]:
            assert "id" in entity, f"Entity missing id: {entity}"
            assert "entity_type" in entity, f"Entity missing entity_type: {entity}"
            assert "name" in entity, f"Entity missing name: {entity}"

    def test_all_relationships_reference_valid_entities(self) -> None:
        path = TEMPLATES_DIR / "organization.json"
        data = json.loads(path.read_text())
        entity_ids = {e["id"] for e in data["entities"]}
        for rel in data["relationships"]:
            assert rel["source_id"] in entity_ids, (
                f"Relationship references unknown source: {rel['source_id']}"
            )
            assert rel["target_id"] in entity_ids, (
                f"Relationship references unknown target: {rel['target_id']}"
            )

    def test_dry_run_succeeds(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli, ["import", str(TEMPLATES_DIR / "organization.json"), "--dry-run"]
        )
        assert result.exit_code == 0, f"Dry run failed: {result.output}"

    def test_import_succeeds(self, tmp_path: Path) -> None:
        output = tmp_path / "graph.json"
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["import", str(TEMPLATES_DIR / "organization.json"), "-o", str(output)],
        )
        assert result.exit_code == 0, f"Import failed: {result.output}"
        assert output.exists()
        data = json.loads(output.read_text())
        assert len(data["entities"]) >= 30

    def test_round_trip(self, tmp_path: Path) -> None:
        """Import → export → re-import produces consistent entity count."""
        output1 = tmp_path / "first.json"
        output2 = tmp_path / "second.json"
        runner = CliRunner()

        # First import
        result1 = runner.invoke(
            cli,
            ["import", str(TEMPLATES_DIR / "organization.json"), "-o", str(output1)],
        )
        assert result1.exit_code == 0

        # Re-import the exported file
        result2 = runner.invoke(
            cli, ["import", str(output1), "-o", str(output2)]
        )
        assert result2.exit_code == 0

        data1 = json.loads(output1.read_text())
        data2 = json.loads(output2.read_text())
        assert len(data1["entities"]) == len(data2["entities"])


CSV_TEMPLATES = [
    "people.csv",
    "departments.csv",
    "systems.csv",
    "vendors.csv",
    "vulnerabilities.csv",
    "risks.csv",
    "controls.csv",
    "incidents.csv",
]


class TestCsvTemplates:
    """Tests for CSV template files."""

    def test_all_csv_templates_exist(self) -> None:
        for filename in CSV_TEMPLATES:
            path = TEMPLATES_DIR / filename
            assert path.exists(), f"Missing CSV template: {filename}"

    def test_all_csv_templates_have_headers_and_data(self) -> None:
        for filename in CSV_TEMPLATES:
            path = TEMPLATES_DIR / filename
            lines = path.read_text().strip().splitlines()
            assert len(lines) >= 2, f"{filename} needs at least header + 1 data row"

    def test_people_csv_import(self, tmp_path: Path) -> None:
        output = tmp_path / "graph.json"
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "import",
                str(TEMPLATES_DIR / "people.csv"),
                "-t", "person",
                "-o", str(output),
            ],
        )
        assert result.exit_code == 0, f"Import failed: {result.output}"
        data = json.loads(output.read_text())
        assert len(data["entities"]) == 5

    def test_departments_csv_import(self, tmp_path: Path) -> None:
        output = tmp_path / "graph.json"
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "import",
                str(TEMPLATES_DIR / "departments.csv"),
                "-t", "department",
                "-o", str(output),
            ],
        )
        assert result.exit_code == 0, f"Import failed: {result.output}"
        data = json.loads(output.read_text())
        assert len(data["entities"]) == 5

    def test_systems_csv_import(self, tmp_path: Path) -> None:
        output = tmp_path / "graph.json"
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "import",
                str(TEMPLATES_DIR / "systems.csv"),
                "-t", "system",
                "-o", str(output),
            ],
        )
        assert result.exit_code == 0, f"Import failed: {result.output}"
        data = json.loads(output.read_text())
        assert len(data["entities"]) == 5

    def test_vendors_csv_import(self, tmp_path: Path) -> None:
        output = tmp_path / "graph.json"
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "import",
                str(TEMPLATES_DIR / "vendors.csv"),
                "-t", "vendor",
                "-o", str(output),
            ],
        )
        assert result.exit_code == 0, f"Import failed: {result.output}"
        data = json.loads(output.read_text())
        assert len(data["entities"]) == 5

    def test_vulnerabilities_csv_import(self, tmp_path: Path) -> None:
        output = tmp_path / "graph.json"
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "import",
                str(TEMPLATES_DIR / "vulnerabilities.csv"),
                "-t", "vulnerability",
                "-o", str(output),
            ],
        )
        assert result.exit_code == 0, f"Import failed: {result.output}"
        data = json.loads(output.read_text())
        assert len(data["entities"]) == 5

    def test_risks_csv_import(self, tmp_path: Path) -> None:
        output = tmp_path / "graph.json"
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "import",
                str(TEMPLATES_DIR / "risks.csv"),
                "-t", "risk",
                "-o", str(output),
            ],
        )
        assert result.exit_code == 0, f"Import failed: {result.output}"
        data = json.loads(output.read_text())
        assert len(data["entities"]) == 5

    def test_controls_csv_import(self, tmp_path: Path) -> None:
        output = tmp_path / "graph.json"
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "import",
                str(TEMPLATES_DIR / "controls.csv"),
                "-t", "control",
                "-o", str(output),
            ],
        )
        assert result.exit_code == 0, f"Import failed: {result.output}"
        data = json.loads(output.read_text())
        assert len(data["entities"]) == 5

    def test_incidents_csv_import(self, tmp_path: Path) -> None:
        output = tmp_path / "graph.json"
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "import",
                str(TEMPLATES_DIR / "incidents.csv"),
                "-t", "incident",
                "-o", str(output),
            ],
        )
        assert result.exit_code == 0, f"Import failed: {result.output}"
        data = json.loads(output.read_text())
        assert len(data["entities"]) == 5
