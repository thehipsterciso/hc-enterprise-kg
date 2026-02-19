"""Tests for temporal event types."""

from hc_enterprise_kg.domain.temporal import GraphEvent, MutationType


class TestGraphEvent:
    def test_event_creation(self):
        event = GraphEvent(
            mutation_type=MutationType.CREATE,
            entity_type="person",
            entity_id="p-1",
        )
        assert event.mutation_type == MutationType.CREATE
        assert event.entity_type == "person"
        assert event.timestamp is not None
        assert event.id is not None

    def test_all_mutation_types(self):
        for mt in MutationType:
            event = GraphEvent(mutation_type=mt)
            assert event.mutation_type == mt
