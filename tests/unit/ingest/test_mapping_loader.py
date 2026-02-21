"""Tests for declarative column mapping loader."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from domain.base import EntityType
from ingest.mapping_loader import (
    ColumnMapping,
    load_column_mapping,
    to_schema_mapping,
)

if TYPE_CHECKING:
    from pathlib import Path


def _write_mapping(tmp_path: Path, data: dict) -> Path:
    """Write a mapping dict to a temp JSON file."""
    path = tmp_path / "test.mapping.json"
    path.write_text(json.dumps(data))
    return path


VALID_MAPPING = {
    "name": "Test Mapping",
    "description": "Maps test columns",
    "entity_type": "person",
    "name_field": "Full_Name",
    "columns": {
        "First": "first_name",
        "Last": "last_name",
        "Mail": "email",
        "Job": "title",
    },
}


class TestLoadColumnMapping:
    def test_valid_mapping(self, tmp_path: Path) -> None:
        path = _write_mapping(tmp_path, VALID_MAPPING)
        result = load_column_mapping(path)
        assert result.is_valid
        assert result.mapping is not None
        assert result.mapping.name == "Test Mapping"
        assert result.mapping.entity_type == EntityType.PERSON
        assert result.mapping.name_field == "Full_Name"
        assert result.mapping.columns["First"] == "first_name"
        assert len(result.mapping.columns) == 4

    def test_file_not_found(self, tmp_path: Path) -> None:
        result = load_column_mapping(tmp_path / "nonexistent.json")
        assert not result.is_valid
        assert "not found" in result.errors[0]

    def test_invalid_json(self, tmp_path: Path) -> None:
        path = tmp_path / "bad.json"
        path.write_text("not json {{{")
        result = load_column_mapping(path)
        assert not result.is_valid
        assert "Invalid JSON" in result.errors[0]

    def test_not_a_dict(self, tmp_path: Path) -> None:
        path = tmp_path / "array.json"
        path.write_text("[1, 2, 3]")
        result = load_column_mapping(path)
        assert not result.is_valid
        assert "JSON object" in result.errors[0]

    def test_missing_entity_type(self, tmp_path: Path) -> None:
        data = {**VALID_MAPPING}
        del data["entity_type"]
        path = _write_mapping(tmp_path, data)
        result = load_column_mapping(path)
        assert not result.is_valid
        assert "entity_type" in result.errors[0]

    def test_invalid_entity_type(self, tmp_path: Path) -> None:
        data = {**VALID_MAPPING, "entity_type": "bogus"}
        path = _write_mapping(tmp_path, data)
        result = load_column_mapping(path)
        assert not result.is_valid
        assert "bogus" in result.errors[0]

    def test_missing_name_field(self, tmp_path: Path) -> None:
        data = {**VALID_MAPPING}
        del data["name_field"]
        path = _write_mapping(tmp_path, data)
        result = load_column_mapping(path)
        assert not result.is_valid
        assert "name_field" in result.errors[0]

    def test_columns_not_a_dict(self, tmp_path: Path) -> None:
        data = {**VALID_MAPPING, "columns": ["not", "a", "dict"]}
        path = _write_mapping(tmp_path, data)
        result = load_column_mapping(path)
        assert not result.is_valid
        assert "dict" in result.errors[0]

    def test_empty_columns_ok(self, tmp_path: Path) -> None:
        data = {**VALID_MAPPING, "columns": {}}
        path = _write_mapping(tmp_path, data)
        result = load_column_mapping(path)
        assert result.is_valid
        assert result.mapping is not None
        assert len(result.mapping.columns) == 0

    def test_default_name_from_filename(self, tmp_path: Path) -> None:
        data = {**VALID_MAPPING}
        del data["name"]
        path = _write_mapping(tmp_path, data)
        result = load_column_mapping(path)
        assert result.is_valid
        assert result.mapping is not None
        assert result.mapping.name == "test.mapping"


class TestColumnValidation:
    def test_unknown_target_field_warns(self, tmp_path: Path) -> None:
        data = {
            **VALID_MAPPING,
            "columns": {"Source_Col": "totally_bogus_field"},
        }
        path = _write_mapping(tmp_path, data)
        result = load_column_mapping(path)
        assert result.is_valid  # warnings, not errors
        assert len(result.warnings) == 1
        assert "totally_bogus_field" in result.warnings[0]

    def test_non_string_target_value_errors(self, tmp_path: Path) -> None:
        data = {
            **VALID_MAPPING,
            "columns": {"Source_Col": 42},
        }
        path = _write_mapping(tmp_path, data)
        result = load_column_mapping(path)
        assert not result.is_valid
        assert "string" in result.errors[0].lower()


class TestToSchemaMapping:
    def test_converts_to_schema_mapping(self) -> None:
        cm = ColumnMapping(
            name="Test",
            description="",
            entity_type=EntityType.PERSON,
            name_field="Full_Name",
            columns={"First": "first_name", "Last": "last_name"},
        )
        sm = to_schema_mapping(cm)
        assert len(sm.entity_mappings) == 1
        em = sm.entity_mappings[0]
        assert em.target_entity_type == EntityType.PERSON
        assert em.name_field == "Full_Name"
        assert len(em.field_mappings) == 2
        assert em.field_mappings[0].source_field == "First"
        assert em.field_mappings[0].target_attribute == "first_name"

    def test_empty_columns(self) -> None:
        cm = ColumnMapping(
            name="Test",
            description="",
            entity_type=EntityType.DEPARTMENT,
            name_field="Name",
            columns={},
        )
        sm = to_schema_mapping(cm)
        assert len(sm.entity_mappings) == 1
        assert len(sm.entity_mappings[0].field_mappings) == 0

    def test_no_relationship_mappings(self) -> None:
        cm = ColumnMapping(
            name="Test",
            description="",
            entity_type=EntityType.SYSTEM,
            name_field="CI_Name",
            columns={"IP": "ip_address"},
        )
        sm = to_schema_mapping(cm)
        assert len(sm.relationship_mappings) == 0


class TestMappingWithCsvIngestor:
    def test_end_to_end_csv_with_mapping(self, tmp_path: Path) -> None:
        """Full round-trip: mapping file + CSV -> entities."""
        from ingest.csv_ingestor import CSVIngestor

        # Create a CSV with non-canonical column names
        csv_path = tmp_path / "hr_export.csv"
        csv_path.write_text(
            "Full_Name,First,Last,Mail\n"
            "Alice Smith,Alice,Smith,alice@acme.com\n"
            "Bob Jones,Bob,Jones,bob@acme.com\n"
        )

        # Create mapping
        mapping_data = {
            "entity_type": "person",
            "name_field": "Full_Name",
            "columns": {
                "First": "first_name",
                "Last": "last_name",
                "Mail": "email",
            },
        }
        mapping_path = _write_mapping(tmp_path, mapping_data)

        # Load mapping and convert
        load_result = load_column_mapping(mapping_path)
        assert load_result.is_valid
        sm = to_schema_mapping(load_result.mapping)  # type: ignore[arg-type]

        # Ingest with mapping
        ingestor = CSVIngestor()
        result = ingestor.ingest(csv_path, mapping=sm)
        assert result.entity_count == 2
        assert not result.errors

        # Verify entity fields were mapped correctly
        alice = result.entities[0]
        assert alice.name == "Alice Smith"
        assert alice.first_name == "Alice"  # type: ignore[attr-defined]
        assert alice.last_name == "Smith"  # type: ignore[attr-defined]
        assert alice.email == "alice@acme.com"  # type: ignore[attr-defined]
