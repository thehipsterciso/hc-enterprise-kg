"""Tests for CSVIngestor — transforms and relationship mappings."""

from __future__ import annotations

import csv
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from domain.base import EntityType, RelationshipType
from ingest.csv_ingestor import CSVIngestor
from ingest.mapping import EntityMapping, FieldMapping, RelationshipMapping, SchemaMapping


@pytest.fixture
def csv_path(tmp_path: Path) -> Path:
    """Create a simple CSV with department data."""
    p = tmp_path / "departments.csv"
    with open(p, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["dept_name", "description"])
        writer.writeheader()
        writer.writerow({"dept_name": "Engineering", "description": "  Builds software  "})
        writer.writerow({"dept_name": "Marketing", "description": "  Promotes products  "})
    return p


@pytest.fixture
def mapping() -> SchemaMapping:
    return SchemaMapping(
        entity_mappings=[
            EntityMapping(
                source_type="csv",
                target_entity_type=EntityType.DEPARTMENT,
                name_field="dept_name",
                field_mappings=[
                    FieldMapping(
                        source_field="description",
                        target_attribute="description",
                    ),
                ],
            )
        ],
    )


class TestCSVTransforms:
    """Tests for FieldMapping.transform support."""

    def test_no_transform_passes_through(self):
        assert CSVIngestor._apply_transform("Hello", None) == "Hello"

    def test_lowercase_transform(self):
        assert CSVIngestor._apply_transform("HELLO", "lowercase") == "hello"

    def test_uppercase_transform(self):
        assert CSVIngestor._apply_transform("hello", "uppercase") == "HELLO"

    def test_strip_transform(self):
        assert CSVIngestor._apply_transform("  hello  ", "strip") == "hello"

    def test_int_transform(self):
        assert CSVIngestor._apply_transform("42", "int") == 42

    def test_float_transform(self):
        assert CSVIngestor._apply_transform("3.14", "float") == pytest.approx(3.14)

    def test_bool_transform_true(self):
        assert CSVIngestor._apply_transform("true", "bool") is True
        assert CSVIngestor._apply_transform("1", "bool") is True
        assert CSVIngestor._apply_transform("yes", "bool") is True

    def test_bool_transform_false(self):
        assert CSVIngestor._apply_transform("false", "bool") is False
        assert CSVIngestor._apply_transform("no", "bool") is False

    def test_unknown_transform_passes_through(self):
        assert CSVIngestor._apply_transform("hello", "nonexistent") == "hello"

    def test_transform_applied_during_ingest(self, tmp_path: Path):
        """Verify transforms are applied when ingesting CSV with mapping."""
        p = tmp_path / "test.csv"
        with open(p, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["name", "desc"])
            writer.writeheader()
            writer.writerow({"name": "Engineering", "desc": "  BUILDS SOFTWARE  "})

        mapping = SchemaMapping(
            entity_mappings=[
                EntityMapping(
                    source_type="csv",
                    target_entity_type=EntityType.DEPARTMENT,
                    name_field="name",
                    field_mappings=[
                        FieldMapping(
                            source_field="desc",
                            target_attribute="description",
                            transform="strip",
                        ),
                    ],
                )
            ],
        )

        ingestor = CSVIngestor()
        result = ingestor.ingest(p, mapping=mapping)
        assert len(result.entities) == 1
        assert result.entities[0].description == "BUILDS SOFTWARE"


class TestCSVBasicIngest:
    """Tests for basic CSV ingestion."""

    def test_ingest_with_mapping(self, csv_path: Path, mapping: SchemaMapping):
        ingestor = CSVIngestor()
        result = ingestor.ingest(csv_path, mapping=mapping)
        assert len(result.entities) == 2
        assert result.entities[0].name == "Engineering"
        assert not result.errors

    def test_ingest_with_entity_type(self, csv_path: Path):
        ingestor = CSVIngestor()
        result = ingestor.ingest(csv_path, entity_type=EntityType.DEPARTMENT)
        assert len(result.entities) == 2
        assert not result.errors

    def test_ingest_file_not_found(self):
        ingestor = CSVIngestor()
        result = ingestor.ingest("/tmp/nonexistent_test.csv")
        assert len(result.errors) == 1
        assert "not found" in result.errors[0].lower()

    def test_ingest_no_mapping_or_type(self, csv_path: Path):
        ingestor = CSVIngestor()
        result = ingestor.ingest(csv_path)
        assert len(result.errors) == 1

    def test_can_handle(self):
        ingestor = CSVIngestor()
        assert ingestor.can_handle("test.csv")
        assert not ingestor.can_handle("test.json")


class TestCSVRelationshipMappings:
    """Tests for relationship_mappings support."""

    def test_relationship_mappings_create_relationships(self, tmp_path: Path):
        """Relationship mappings should create relationships between ingested entities."""
        p = tmp_path / "people.csv"
        with open(p, "w", newline="") as f:
            writer = csv.DictWriter(
                f, fieldnames=["name", "first_name", "last_name", "email", "department"]
            )
            writer.writeheader()
            writer.writerow(
                {
                    "name": "Engineering",
                    "first_name": "",
                    "last_name": "",
                    "email": "",
                    "department": "",
                }
            )

        # Create a mapping with both entity and relationship mappings
        # For simplicity, create two departments where one references the other
        p2 = tmp_path / "depts.csv"
        with open(p2, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["name", "parent_dept"])
            writer.writeheader()
            writer.writerow({"name": "Engineering", "parent_dept": "Technology"})
            writer.writerow({"name": "Technology", "parent_dept": ""})

        mapping = SchemaMapping(
            entity_mappings=[
                EntityMapping(
                    source_type="csv",
                    target_entity_type=EntityType.DEPARTMENT,
                    name_field="name",
                    field_mappings=[
                        FieldMapping(
                            source_field="parent_dept",
                            target_attribute="parent_dept",
                        ),
                    ],
                )
            ],
            relationship_mappings=[
                RelationshipMapping(
                    source_field="name",
                    target_field="parent_dept",
                    relationship_type=RelationshipType.MANAGES,
                )
            ],
        )

        ingestor = CSVIngestor()
        result = ingestor.ingest(p2, mapping=mapping)
        assert len(result.entities) == 2
        # Engineering → Technology relationship should be created
        assert len(result.relationships) >= 1
        rel = result.relationships[0]
        assert rel.relationship_type == RelationshipType.MANAGES
