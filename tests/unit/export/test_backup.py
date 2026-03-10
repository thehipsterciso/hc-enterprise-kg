"""Tests for backup-on-write rotation."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from domain.base import BaseRelationship, RelationshipType
from domain.entities.department import Department
from domain.entities.person import Person
from engine.networkx_engine import NetworkXGraphEngine
from export.json_export import JSONExporter, _rotate_backups

if TYPE_CHECKING:
    from pathlib import Path


def _build_engine(extra_dept: str | None = None) -> NetworkXGraphEngine:
    engine = NetworkXGraphEngine()
    person = Person(
        id="p1", first_name="Alice", last_name="Smith", name="Alice Smith", email="a@b.com"
    )
    dept = Department(id="d1", name="Engineering")
    engine.add_entity(person)
    engine.add_entity(dept)
    if extra_dept:
        engine.add_entity(Department(id=extra_dept, name=extra_dept))
    engine.add_relationship(
        BaseRelationship(
            relationship_type=RelationshipType.WORKS_IN, source_id="p1", target_id="d1"
        )
    )
    return engine


class TestRotateBackups:
    """Tests for the _rotate_backups utility."""

    def test_no_backup_when_file_missing(self, tmp_path: Path):
        target = tmp_path / "graph.json"
        _rotate_backups(target)
        assert not (tmp_path / "graph.json.1").exists()

    def test_first_overwrite_creates_backup_1(self, tmp_path: Path):
        target = tmp_path / "graph.json"
        target.write_text("v1")
        _rotate_backups(target)
        assert (tmp_path / "graph.json.1").exists()
        assert (tmp_path / "graph.json.1").read_text() == "v1"

    def test_second_overwrite_shifts_backups(self, tmp_path: Path):
        target = tmp_path / "graph.json"
        target.write_text("v1")
        _rotate_backups(target)
        target.write_text("v2")
        _rotate_backups(target)
        assert (tmp_path / "graph.json.1").read_text() == "v2"
        assert (tmp_path / "graph.json.2").read_text() == "v1"

    def test_rotation_caps_at_max_backups(self, tmp_path: Path):
        target = tmp_path / "graph.json"
        for i in range(5):
            target.write_text(f"v{i}")
            _rotate_backups(target, max_backups=3)
        assert (tmp_path / "graph.json.1").exists()
        assert (tmp_path / "graph.json.2").exists()
        assert (tmp_path / "graph.json.3").exists()
        assert not (tmp_path / "graph.json.4").exists()

    def test_max_backups_zero_disables(self, tmp_path: Path):
        target = tmp_path / "graph.json"
        target.write_text("v1")
        _rotate_backups(target, max_backups=0)
        assert not (tmp_path / "graph.json.1").exists()


class TestJSONExporterBackup:
    """Integration: JSONExporter creates backups during export."""

    def test_export_creates_backup(self, tmp_path: Path):
        engine = _build_engine()
        path = tmp_path / "graph.json"
        exporter = JSONExporter()

        # First export — no backup (no prior file)
        exporter.export(engine, path)
        assert not (tmp_path / "graph.json.1").exists()

        # Second export — backup of first version
        engine2 = _build_engine(extra_dept="d2")
        exporter.export(engine2, path)
        assert (tmp_path / "graph.json.1").exists()
        backup_data = json.loads((tmp_path / "graph.json.1").read_text())
        assert len(backup_data["entities"]) == 2  # original had 2

        current_data = json.loads(path.read_text())
        assert len(current_data["entities"]) == 3  # new has 3

    def test_export_max_backups_zero_skips(self, tmp_path: Path):
        engine = _build_engine()
        path = tmp_path / "graph.json"
        exporter = JSONExporter()
        exporter.export(engine, path)
        exporter.export(engine, path, max_backups=0)
        assert not (tmp_path / "graph.json.1").exists()
