"""Integration tests for import template files.

Validates that all template files in examples/import-templates/ are
syntactically correct and import successfully via the CLI.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from cli.main import cli
from domain.base import EntityType

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "examples" / "import-templates"
ALL_ENTITY_TYPES = [et.value for et in EntityType]


class TestOrganizationJson:
    """Tests for the comprehensive organization.json multi-type template."""

    def test_valid_json(self) -> None:
        data = json.loads((TEMPLATES_DIR / "organization.json").read_text())
        assert "entities" in data
        assert "relationships" in data

    def test_contains_all_30_entity_types(self) -> None:
        data = json.loads((TEMPLATES_DIR / "organization.json").read_text())
        types_found = {e["entity_type"] for e in data["entities"]}
        all_types = {et.value for et in EntityType}
        missing = all_types - types_found
        assert not missing, f"Missing entity types: {missing}"

    def test_all_entities_have_required_fields(self) -> None:
        data = json.loads((TEMPLATES_DIR / "organization.json").read_text())
        for entity in data["entities"]:
            assert "id" in entity, f"Missing id: {entity.get('name')}"
            assert "entity_type" in entity, f"Missing entity_type: {entity.get('name')}"
            assert "name" in entity, f"Missing name: {entity.get('id')}"

    def test_all_relationships_reference_valid_entities(self) -> None:
        data = json.loads((TEMPLATES_DIR / "organization.json").read_text())
        entity_ids = {e["id"] for e in data["entities"]}
        for rel in data["relationships"]:
            assert rel["source_id"] in entity_ids, (
                f"Unknown source: {rel['source_id']}"
            )
            assert rel["target_id"] in entity_ids, (
                f"Unknown target: {rel['target_id']}"
            )

    def test_dry_run_strict(self) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["import", str(TEMPLATES_DIR / "organization.json"), "--dry-run", "--strict"],
        )
        assert result.exit_code == 0, f"Failed: {result.output}"

    def test_import_produces_output(self, tmp_path: Path) -> None:
        output = tmp_path / "graph.json"
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["import", str(TEMPLATES_DIR / "organization.json"), "-o", str(output)],
        )
        assert result.exit_code == 0, f"Failed: {result.output}"
        data = json.loads(output.read_text())
        assert len(data["entities"]) >= 30

    def test_round_trip(self, tmp_path: Path) -> None:
        out1 = tmp_path / "first.json"
        out2 = tmp_path / "second.json"
        runner = CliRunner()
        r1 = runner.invoke(
            cli,
            ["import", str(TEMPLATES_DIR / "organization.json"), "-o", str(out1)],
        )
        assert r1.exit_code == 0
        r2 = runner.invoke(cli, ["import", str(out1), "-o", str(out2)])
        assert r2.exit_code == 0
        assert len(json.loads(out1.read_text())["entities"]) == len(
            json.loads(out2.read_text())["entities"]
        )


class TestPerTypeJsonTemplates:
    """Each entity type has a single-type JSON template that imports cleanly."""

    def test_all_30_json_templates_exist(self) -> None:
        for et in ALL_ENTITY_TYPES:
            path = TEMPLATES_DIR / f"{et}.json"
            assert path.exists(), f"Missing JSON template: {et}.json"

    @pytest.mark.parametrize("entity_type", ALL_ENTITY_TYPES)
    def test_json_template_dry_run_strict(self, entity_type: str) -> None:
        path = TEMPLATES_DIR / f"{entity_type}.json"
        runner = CliRunner()
        result = runner.invoke(
            cli, ["import", str(path), "--dry-run", "--strict"]
        )
        assert result.exit_code == 0, (
            f"{entity_type}.json failed: {result.output}"
        )

    @pytest.mark.parametrize("entity_type", ALL_ENTITY_TYPES)
    def test_json_template_has_entities(self, entity_type: str) -> None:
        data = json.loads((TEMPLATES_DIR / f"{entity_type}.json").read_text())
        assert "entities" in data
        assert len(data["entities"]) >= 3, (
            f"{entity_type}.json has < 3 entities"
        )
        for e in data["entities"]:
            assert e["entity_type"] == entity_type


class TestPerTypeCsvTemplates:
    """Each entity type has a CSV template that imports cleanly."""

    def test_all_30_csv_templates_exist(self) -> None:
        for et in ALL_ENTITY_TYPES:
            path = TEMPLATES_DIR / f"{et}.csv"
            assert path.exists(), f"Missing CSV template: {et}.csv"

    @pytest.mark.parametrize("entity_type", ALL_ENTITY_TYPES)
    def test_csv_has_header_and_data(self, entity_type: str) -> None:
        lines = (TEMPLATES_DIR / f"{entity_type}.csv").read_text().strip().splitlines()
        assert len(lines) >= 6, f"{entity_type}.csv has < 5 data rows"

    @pytest.mark.parametrize("entity_type", ALL_ENTITY_TYPES)
    def test_csv_template_import(self, entity_type: str, tmp_path: Path) -> None:
        output = tmp_path / "graph.json"
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "import",
                str(TEMPLATES_DIR / f"{entity_type}.csv"),
                "-t", entity_type,
                "-o", str(output),
            ],
        )
        assert result.exit_code == 0, (
            f"{entity_type}.csv import failed: {result.output}"
        )
        data = json.loads(output.read_text())
        assert len(data["entities"]) == 5
