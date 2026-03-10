"""Tests for persistent JSONL audit logger."""

from __future__ import annotations

import json
from pathlib import Path

from domain.temporal import GraphEvent, MutationType
from graph.audit import AuditLogger, derive_audit_path


class TestDeriveAuditPath:
    """Tests for derive_audit_path()."""

    def test_json_extension(self):
        assert derive_audit_path(Path("/tmp/graph.json")) == Path("/tmp/graph.audit.jsonl")

    def test_no_extension(self):
        assert derive_audit_path(Path("/tmp/graph")) == Path("/tmp/graph.audit.jsonl")

    def test_nested_path(self):
        result = derive_audit_path(Path("/home/user/data/kg.json"))
        assert result == Path("/home/user/data/kg.audit.jsonl")


class TestAuditLogger:
    """Tests for AuditLogger event persistence."""

    def _make_event(self, **kwargs) -> GraphEvent:
        defaults = {
            "mutation_type": MutationType.CREATE,
            "entity_type": "person",
            "entity_id": "test-123",
            "source": "test",
        }
        defaults.update(kwargs)
        return GraphEvent(**defaults)

    def test_creates_file_on_first_event(self, tmp_path: Path):
        audit_path = tmp_path / "graph.audit.jsonl"
        audit = AuditLogger(audit_path)
        audit(self._make_event())
        assert audit_path.exists()

    def test_writes_valid_jsonl(self, tmp_path: Path):
        audit_path = tmp_path / "graph.audit.jsonl"
        audit = AuditLogger(audit_path)
        audit(self._make_event())

        lines = audit_path.read_text().strip().split("\n")
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["mutation_type"] == "create"
        assert data["entity_type"] == "person"
        assert data["entity_id"] == "test-123"

    def test_appends_multiple_events(self, tmp_path: Path):
        audit_path = tmp_path / "graph.audit.jsonl"
        audit = AuditLogger(audit_path)
        audit(self._make_event(entity_id="a"))
        audit(self._make_event(entity_id="b"))
        audit(self._make_event(entity_id="c"))

        lines = audit_path.read_text().strip().split("\n")
        assert len(lines) == 3
        ids = [json.loads(line)["entity_id"] for line in lines]
        assert ids == ["a", "b", "c"]

    def test_read_events_returns_dicts(self, tmp_path: Path):
        audit_path = tmp_path / "graph.audit.jsonl"
        audit = AuditLogger(audit_path)
        audit(self._make_event(entity_id="x"))
        audit(self._make_event(entity_id="y"))

        events = audit.read_events()
        assert len(events) == 2
        assert events[0]["entity_id"] == "x"
        assert events[1]["entity_id"] == "y"

    def test_read_events_empty_file(self, tmp_path: Path):
        audit_path = tmp_path / "graph.audit.jsonl"
        audit = AuditLogger(audit_path)
        assert audit.read_events() == []

    def test_event_count(self, tmp_path: Path):
        audit_path = tmp_path / "graph.audit.jsonl"
        audit = AuditLogger(audit_path)
        assert audit.event_count() == 0

        audit(self._make_event())
        assert audit.event_count() == 1

        audit(self._make_event())
        audit(self._make_event())
        assert audit.event_count() == 3

    def test_captures_all_mutation_types(self, tmp_path: Path):
        audit_path = tmp_path / "graph.audit.jsonl"
        audit = AuditLogger(audit_path)

        for mt in MutationType:
            audit(self._make_event(mutation_type=mt))

        events = audit.read_events()
        assert len(events) == len(MutationType)
        types = {e["mutation_type"] for e in events}
        assert types == {mt.value for mt in MutationType}

    def test_captures_before_after_snapshots(self, tmp_path: Path):
        audit_path = tmp_path / "graph.audit.jsonl"
        audit = AuditLogger(audit_path)
        event = self._make_event(
            mutation_type=MutationType.UPDATE,
            before_snapshot={"name": "old"},
            after_snapshot={"name": "new"},
        )
        audit(event)

        events = audit.read_events()
        assert events[0]["before_snapshot"] == {"name": "old"}
        assert events[0]["after_snapshot"] == {"name": "new"}

    def test_path_property(self, tmp_path: Path):
        audit_path = tmp_path / "graph.audit.jsonl"
        audit = AuditLogger(audit_path)
        assert audit.path == audit_path


class TestAuditLoggerWithKnowledgeGraph:
    """Integration: AuditLogger subscribed to KnowledgeGraph EventBus."""

    def test_kg_subscribe_records_events(self, tmp_path: Path):
        from domain.entities.department import Department
        from graph.knowledge_graph import KnowledgeGraph

        audit_path = tmp_path / "graph.audit.jsonl"
        audit = AuditLogger(audit_path)

        kg = KnowledgeGraph()
        kg.subscribe(audit)

        dept = Department(name="Engineering")
        kg.add_entity(dept)

        events = audit.read_events()
        assert len(events) == 1
        assert events[0]["mutation_type"] == "create"
        assert events[0]["entity_id"] == dept.id
