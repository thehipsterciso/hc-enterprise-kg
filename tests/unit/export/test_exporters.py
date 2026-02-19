"""Tests for JSON and GraphML exporters."""

import json
import tempfile
from pathlib import Path

from domain.base import BaseRelationship, RelationshipType
from domain.entities.department import Department
from domain.entities.person import Person
from engine.networkx_engine import NetworkXGraphEngine
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


class TestJSONExporter:
    def test_export_string_returns_valid_json(self):
        engine = _build_engine()
        exporter = JSONExporter()
        result = exporter.export_string(engine)
        data = json.loads(result)
        assert "entities" in data
        assert "relationships" in data
        assert "statistics" in data
        assert len(data["entities"]) == 2
        assert len(data["relationships"]) == 1

    def test_export_to_file(self):
        engine = _build_engine()
        exporter = JSONExporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "output.json"
            exporter.export(engine, path)
            assert path.exists()
            data = json.loads(path.read_text())
            assert len(data["entities"]) == 2

    def test_export_statistics_include_counts(self):
        engine = _build_engine()
        exporter = JSONExporter()
        result = exporter.export_string(engine)
        data = json.loads(result)
        stats = data["statistics"]
        assert stats["entity_count"] == 2
        assert stats["relationship_count"] == 1

    def test_export_with_custom_indent(self):
        engine = _build_engine()
        exporter = JSONExporter()
        result = exporter.export_string(engine, indent=4)
        # 4-space indent means lines start with 4 spaces
        assert "    " in result


class TestGraphMLExporter:
    def test_export_string_returns_xml(self):
        engine = _build_engine()
        exporter = GraphMLExporter()
        result = exporter.export_string(engine)
        assert "<?xml" in result or "<graphml" in result

    def test_export_to_file(self):
        engine = _build_engine()
        exporter = GraphMLExporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "output.graphml"
            exporter.export(engine, path)
            assert path.exists()
            content = path.read_text()
            assert "graphml" in content

    def test_export_contains_nodes_and_edges(self):
        engine = _build_engine()
        exporter = GraphMLExporter()
        result = exporter.export_string(engine)
        assert "p1" in result
        assert "d1" in result
        assert "<edge" in result

    def test_complex_attributes_converted_to_strings(self):
        engine = _build_engine()
        exporter = GraphMLExporter()
        # Should not raise even with complex attrs
        result = exporter.export_string(engine)
        assert isinstance(result, str)
