"""Tests for atomic file write functionality."""

import json
import os
from pathlib import Path

import pytest

from domain.base import BaseRelationship, RelationshipType
from domain.entities.department import Department
from domain.entities.person import Person
from engine.networkx_engine import NetworkXGraphEngine
from export.base import atomic_write_text
from export.graphml_export import GraphMLExporter
from export.json_export import JSONExporter


def _build_engine() -> NetworkXGraphEngine:
    engine = NetworkXGraphEngine()
    person = Person(
        id="p1",
        first_name="Alice",
        last_name="Smith",
        name="Alice Smith",
        email="a@b.com",
    )
    dept = Department(id="d1", name="Engineering")
    engine.add_entity(person)
    engine.add_entity(dept)
    engine.add_relationship(
        BaseRelationship(
            relationship_type=RelationshipType.WORKS_IN,
            source_id="p1",
            target_id="d1",
        )
    )
    return engine


class TestAtomicWriteText:
    """Tests for the atomic_write_text utility function."""

    def test_writes_content_to_file(self, tmp_path: Path):
        path = tmp_path / "test.txt"
        atomic_write_text(path, "hello world")
        assert path.read_text() == "hello world"

    def test_creates_parent_directories(self, tmp_path: Path):
        path = tmp_path / "a" / "b" / "c" / "test.txt"
        atomic_write_text(path, "nested")
        assert path.read_text() == "nested"

    def test_overwrites_existing_file(self, tmp_path: Path):
        path = tmp_path / "test.txt"
        path.write_text("old content")
        atomic_write_text(path, "new content")
        assert path.read_text() == "new content"

    def test_no_temp_files_remain_on_success(self, tmp_path: Path):
        path = tmp_path / "test.json"
        atomic_write_text(path, '{"key": "value"}')
        remaining = list(tmp_path.glob(".*"))
        assert remaining == [], f"Temp files left behind: {remaining}"

    def test_preserves_original_on_write_failure(self, tmp_path: Path):
        # Make directory read-only to force mkstemp failure
        no_write_dir = tmp_path / "readonly"
        no_write_dir.mkdir()
        target = no_write_dir / "test.txt"
        target.write_text("original")
        os.chmod(str(no_write_dir), 0o444)

        try:
            with pytest.raises(PermissionError):
                atomic_write_text(target, "should fail")
        finally:
            os.chmod(str(no_write_dir), 0o700)

        # Original file should still be intact (check after restoring perms)
        assert target.read_text() == "original"

    def test_cleans_up_temp_on_failure(self, tmp_path: Path):
        # Create a scenario where the write can fail
        no_write_dir = tmp_path / "readonly"
        no_write_dir.mkdir()
        target = no_write_dir / "test.txt"
        os.chmod(str(no_write_dir), 0o444)

        try:
            with pytest.raises(PermissionError):
                atomic_write_text(target, "fail")
            # No temp files should remain
            temps = list(no_write_dir.glob(".*"))
            assert temps == [], f"Temp files not cleaned: {temps}"
        finally:
            os.chmod(str(no_write_dir), 0o700)

    def test_handles_unicode_content(self, tmp_path: Path):
        path = tmp_path / "unicode.txt"
        content = "Hello \u4e16\u754c \U0001f30d \u00e9\u00e8\u00ea"
        atomic_write_text(path, content)
        assert path.read_text(encoding="utf-8") == content


class TestJSONExporterAtomic:
    """Verify JSONExporter uses atomic writes."""

    def test_export_produces_valid_json(self, tmp_path: Path):
        engine = _build_engine()
        path = tmp_path / "graph.json"
        JSONExporter().export(engine, path)
        data = json.loads(path.read_text())
        assert len(data["entities"]) == 2
        assert len(data["relationships"]) == 1

    def test_no_temp_files_after_export(self, tmp_path: Path):
        engine = _build_engine()
        path = tmp_path / "graph.json"
        JSONExporter().export(engine, path)
        temps = list(tmp_path.glob(".*"))
        assert temps == [], f"Temp files left behind: {temps}"

    def test_overwrite_is_atomic(self, tmp_path: Path):
        """Write twice — second write should fully replace first."""
        engine = _build_engine()
        path = tmp_path / "graph.json"

        JSONExporter().export(engine, path)
        first = json.loads(path.read_text())

        # Add another entity and re-export
        dept2 = Department(id="d2", name="Sales")
        engine.add_entity(dept2)
        JSONExporter().export(engine, path)
        second = json.loads(path.read_text())

        assert len(second["entities"]) == len(first["entities"]) + 1


class TestGraphMLExporterAtomic:
    """Verify GraphMLExporter uses atomic writes."""

    def test_export_produces_valid_graphml(self, tmp_path: Path):
        engine = _build_engine()
        path = tmp_path / "graph.graphml"
        GraphMLExporter().export(engine, path)
        content = path.read_text()
        assert "graphml" in content

    def test_no_temp_files_after_export(self, tmp_path: Path):
        engine = _build_engine()
        path = tmp_path / "graph.graphml"
        GraphMLExporter().export(engine, path)
        temps = list(tmp_path.glob(".*"))
        assert temps == [], f"Temp files left behind: {temps}"
