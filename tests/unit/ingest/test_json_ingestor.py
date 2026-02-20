"""Tests for JSONIngestor — including ingest_string()."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from ingest.json_ingestor import JSONIngestor

if TYPE_CHECKING:
    from pathlib import Path


class TestJSONIngestorFile:
    """Tests for file-based JSON ingestion."""

    def test_ingest_file(self, tmp_path: Path):
        data = {
            "entities": [
                {"entity_type": "department", "name": "Engineering"},
                {"entity_type": "department", "name": "Marketing"},
            ],
            "relationships": [],
        }
        p = tmp_path / "test.json"
        p.write_text(json.dumps(data))

        ingestor = JSONIngestor()
        result = ingestor.ingest(p)
        assert len(result.entities) == 2
        assert not result.errors

    def test_ingest_file_not_found(self):
        ingestor = JSONIngestor()
        result = ingestor.ingest("/tmp/nonexistent_test_hckg.json")
        assert len(result.errors) == 1
        assert "not found" in result.errors[0].lower()

    def test_ingest_invalid_json_file(self, tmp_path: Path):
        p = tmp_path / "bad.json"
        p.write_text("not json {{{")

        ingestor = JSONIngestor()
        result = ingestor.ingest(p)
        assert len(result.errors) == 1
        assert "invalid json" in result.errors[0].lower()

    def test_can_handle(self):
        ingestor = JSONIngestor()
        assert ingestor.can_handle("test.json")
        assert not ingestor.can_handle("test.csv")


class TestJSONIngestString:
    """Tests for ingest_string() method."""

    def test_ingest_string_basic(self):
        data = {
            "entities": [
                {"entity_type": "department", "name": "Engineering"},
            ],
            "relationships": [],
        }
        ingestor = JSONIngestor()
        result = ingestor.ingest_string(json.dumps(data))
        assert len(result.entities) == 1
        assert result.entities[0].name == "Engineering"
        assert not result.errors

    def test_ingest_string_with_relationships(self):
        data = {
            "entities": [
                {"entity_type": "department", "id": "d1", "name": "Eng"},
                {"entity_type": "person", "id": "p1", "name": "Alice",
                 "first_name": "Alice", "last_name": "Smith", "email": "a@b.com"},
            ],
            "relationships": [
                {
                    "relationship_type": "works_in",
                    "source_id": "p1",
                    "target_id": "d1",
                },
            ],
        }
        ingestor = JSONIngestor()
        result = ingestor.ingest_string(json.dumps(data))
        assert len(result.entities) == 2
        assert len(result.relationships) == 1
        assert not result.errors

    def test_ingest_string_invalid_json(self):
        ingestor = JSONIngestor()
        result = ingestor.ingest_string("not json {{{")
        assert len(result.errors) == 1
        assert "invalid json" in result.errors[0].lower()

    def test_ingest_string_empty(self):
        ingestor = JSONIngestor()
        result = ingestor.ingest_string('{"entities": [], "relationships": []}')
        assert len(result.entities) == 0
        assert not result.errors

    def test_ingest_string_matches_file_ingest(self, tmp_path: Path):
        """ingest_string() should produce same result as ingest() for same data."""
        data = {
            "entities": [
                {"entity_type": "department", "id": "d1", "name": "Eng"},
                {"entity_type": "department", "id": "d2", "name": "Mkt"},
            ],
            "relationships": [],
        }
        json_str = json.dumps(data)

        p = tmp_path / "test.json"
        p.write_text(json_str)

        ingestor = JSONIngestor()
        file_result = ingestor.ingest(p)
        str_result = ingestor.ingest_string(json_str)

        assert len(file_result.entities) == len(str_result.entities)
        assert len(file_result.errors) == len(str_result.errors)
