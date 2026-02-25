"""Tests for pre-ingest validation."""

from __future__ import annotations

from domain.base import EntityType
from ingest.validator import ValidationResult, validate_csv_import, validate_json_import


class TestValidationResult:
    def test_is_valid_no_errors(self) -> None:
        vr = ValidationResult()
        assert vr.is_valid is True

    def test_is_valid_with_errors(self) -> None:
        vr = ValidationResult(errors=["some error"])
        assert vr.is_valid is False

    def test_warnings_dont_invalidate(self) -> None:
        vr = ValidationResult(warnings=["some warning"])
        assert vr.is_valid is True


class TestValidateJsonImport:
    def test_valid_data(self) -> None:
        data = {
            "entities": [
                {
                    "entity_type": "department",
                    "name": "Engineering",
                    "code": "ENG",
                }
            ],
            "relationships": [],
        }
        vr = validate_json_import(data)
        assert vr.is_valid
        assert vr.entity_count == 1
        assert vr.entity_type_counts == {"department": 1}
        assert not vr.errors
        assert not vr.warnings

    def test_valid_data_with_relationships(self) -> None:
        data = {
            "entities": [
                {
                    "entity_type": "person",
                    "id": "p1",
                    "name": "Alice",
                    "first_name": "Alice",
                    "last_name": "Smith",
                    "email": "a@b.com",
                },
                {"entity_type": "department", "id": "d1", "name": "Eng"},
            ],
            "relationships": [
                {"relationship_type": "works_in", "source_id": "p1", "target_id": "d1"},
            ],
        }
        vr = validate_json_import(data)
        assert vr.is_valid
        assert vr.entity_count == 2
        assert vr.relationship_count == 1
        assert vr.relationship_type_counts == {"works_in": 1}

    def test_missing_entities_key(self) -> None:
        data = {"relationships": []}
        vr = validate_json_import(data)
        assert not vr.is_valid
        assert "Missing 'entities' key" in vr.errors[0]

    def test_entities_not_a_list(self) -> None:
        data = {"entities": "not a list"}
        vr = validate_json_import(data)
        assert not vr.is_valid
        assert "'entities' must be a list" in vr.errors[0]

    def test_relationships_not_a_list(self) -> None:
        data = {"entities": [], "relationships": "bad"}
        vr = validate_json_import(data)
        assert not vr.is_valid
        assert "'relationships' must be a list" in vr.errors[0]

    def test_empty_entities_list(self) -> None:
        data = {"entities": []}
        vr = validate_json_import(data)
        assert vr.is_valid
        assert vr.entity_count == 0

    def test_entity_not_a_dict(self) -> None:
        data = {"entities": ["not a dict"]}
        vr = validate_json_import(data)
        assert not vr.is_valid
        assert "must be a dict" in vr.errors[0]

    def test_missing_entity_type(self) -> None:
        data = {"entities": [{"name": "Test"}]}
        vr = validate_json_import(data)
        assert not vr.is_valid
        assert "missing 'entity_type'" in vr.errors[0]

    def test_invalid_entity_type(self) -> None:
        data = {"entities": [{"entity_type": "bogus", "name": "Test"}]}
        vr = validate_json_import(data)
        assert not vr.is_valid
        assert "invalid entity_type 'bogus'" in vr.errors[0]

    def test_missing_name(self) -> None:
        data = {"entities": [{"entity_type": "department"}]}
        vr = validate_json_import(data)
        assert not vr.is_valid
        assert "missing or empty 'name'" in vr.errors[0]

    def test_empty_name(self) -> None:
        data = {"entities": [{"entity_type": "department", "name": "  "}]}
        vr = validate_json_import(data)
        assert not vr.is_valid
        assert "missing or empty 'name'" in vr.errors[0]

    def test_person_missing_required_fields(self) -> None:
        data = {"entities": [{"entity_type": "person", "name": "Alice"}]}
        vr = validate_json_import(data)
        assert not vr.is_valid
        assert any("first_name" in e for e in vr.errors)
        assert any("last_name" in e for e in vr.errors)
        assert any("email" in e for e in vr.errors)

    def test_person_with_all_required(self) -> None:
        data = {
            "entities": [
                {
                    "entity_type": "person",
                    "name": "Alice Smith",
                    "first_name": "Alice",
                    "last_name": "Smith",
                    "email": "alice@acme.com",
                }
            ]
        }
        vr = validate_json_import(data)
        assert vr.is_valid
        assert not vr.errors

    def test_unknown_fields_detected(self) -> None:
        data = {
            "entities": [
                {
                    "entity_type": "department",
                    "name": "Engineering",
                    "bogus_field": "value",
                    "another_typo": 42,
                }
            ]
        }
        vr = validate_json_import(data)
        assert vr.is_valid  # warnings, not errors
        assert len(vr.warnings) == 1
        assert "unknown field" in vr.warnings[0].lower()
        assert "bogus_field" in vr.warnings[0]

    def test_invalid_relationship_type(self) -> None:
        data = {
            "entities": [{"entity_type": "department", "name": "Eng"}],
            "relationships": [
                {"relationship_type": "fake_rel", "source_id": "a", "target_id": "b"}
            ],
        }
        vr = validate_json_import(data)
        assert not vr.is_valid
        assert "invalid relationship_type 'fake_rel'" in vr.errors[0]

    def test_relationship_missing_source_id(self) -> None:
        data = {
            "entities": [],
            "relationships": [{"relationship_type": "works_in", "target_id": "d1"}],
        }
        vr = validate_json_import(data)
        assert not vr.is_valid
        assert any("missing 'source_id'" in e for e in vr.errors)

    def test_relationship_missing_target_id(self) -> None:
        data = {
            "entities": [],
            "relationships": [{"relationship_type": "works_in", "source_id": "p1"}],
        }
        vr = validate_json_import(data)
        assert not vr.is_valid
        assert any("missing 'target_id'" in e for e in vr.errors)

    def test_relationship_missing_type(self) -> None:
        data = {
            "entities": [],
            "relationships": [{"source_id": "p1", "target_id": "d1"}],
        }
        vr = validate_json_import(data)
        assert not vr.is_valid
        assert "missing 'relationship_type'" in vr.errors[0]

    def test_dangling_reference_warning(self) -> None:
        data = {
            "entities": [{"entity_type": "department", "id": "d1", "name": "Eng"}],
            "relationships": [
                {
                    "relationship_type": "works_in",
                    "source_id": "missing-person",
                    "target_id": "d1",
                }
            ],
        }
        vr = validate_json_import(data)
        assert vr.is_valid  # dangling refs are warnings
        assert any("missing-person" in w for w in vr.warnings)

    def test_mixed_errors_and_warnings(self) -> None:
        data = {
            "entities": [
                {"entity_type": "department", "id": "d1", "name": "Eng", "typo_field": 1},
                {"entity_type": "bogus", "name": "Bad"},
            ],
            "relationships": [
                {
                    "relationship_type": "works_in",
                    "source_id": "missing",
                    "target_id": "d1",
                }
            ],
        }
        vr = validate_json_import(data)
        assert not vr.is_valid  # has errors from bogus type
        assert len(vr.errors) >= 1
        assert len(vr.warnings) >= 1

    def test_multiple_entity_types_counted(self) -> None:
        data = {
            "entities": [
                {"entity_type": "department", "name": "A"},
                {"entity_type": "department", "name": "B"},
                {"entity_type": "system", "name": "C"},
            ]
        }
        vr = validate_json_import(data)
        assert vr.is_valid
        assert vr.entity_type_counts == {"department": 2, "system": 1}
        assert vr.entity_count == 3

    def test_relationship_not_a_dict(self) -> None:
        data = {
            "entities": [],
            "relationships": ["not a dict"],
        }
        vr = validate_json_import(data)
        assert not vr.is_valid
        assert "must be a dict" in vr.errors[0]

    def test_statistics_key_ignored(self) -> None:
        """Exported JSON includes 'statistics' — validator should ignore it."""
        data = {
            "entities": [{"entity_type": "department", "name": "Eng"}],
            "relationships": [],
            "statistics": {"entity_count": 1},
        }
        vr = validate_json_import(data)
        assert vr.is_valid


class TestValidateCsvImport:
    def test_valid_person_headers(self) -> None:
        headers = ["name", "first_name", "last_name", "email", "title"]
        vr = validate_csv_import(headers, EntityType.PERSON)
        assert vr.is_valid
        assert not vr.errors

    def test_valid_system_headers(self) -> None:
        headers = ["name", "system_type", "hostname", "ip_address", "os"]
        vr = validate_csv_import(headers, EntityType.SYSTEM)
        assert vr.is_valid

    def test_empty_headers(self) -> None:
        vr = validate_csv_import([], EntityType.DEPARTMENT)
        assert not vr.is_valid
        assert "no column headers" in vr.errors[0]

    def test_unknown_columns_detected(self) -> None:
        headers = ["name", "code", "bogus_column", "typo_field"]
        vr = validate_csv_import(headers, EntityType.DEPARTMENT)
        assert vr.is_valid  # warnings, not errors
        assert len(vr.warnings) == 1
        assert "bogus_column" in vr.warnings[0]
        assert "typo_field" in vr.warnings[0]

    def test_person_missing_required_columns(self) -> None:
        headers = ["name", "title"]
        vr = validate_csv_import(headers, EntityType.PERSON)
        assert not vr.is_valid
        assert any("first_name" in e for e in vr.errors)
        assert any("last_name" in e for e in vr.errors)
        assert any("email" in e for e in vr.errors)

    def test_non_person_no_required_columns(self) -> None:
        """Non-person entities only require 'name' (from BaseEntity, always present)."""
        headers = ["name", "description"]
        vr = validate_csv_import(headers, EntityType.DEPARTMENT)
        assert vr.is_valid
