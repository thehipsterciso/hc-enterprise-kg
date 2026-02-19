"""Integration tests for the KnowledgeGraph lifecycle."""

from hc_enterprise_kg.domain.base import BaseRelationship, EntityType, RelationshipType
from hc_enterprise_kg.domain.entities.department import Department
from hc_enterprise_kg.domain.entities.person import Person
from hc_enterprise_kg.domain.entities.system import System
from hc_enterprise_kg.domain.temporal import MutationType
from hc_enterprise_kg.graph.knowledge_graph import KnowledgeGraph


class TestKnowledgeGraphLifecycle:
    def test_add_query_remove_entity(self, kg: KnowledgeGraph):
        person = Person(
            id="p1", first_name="Alice", last_name="Smith",
            name="Alice Smith", email="a@b.com",
        )
        kg.add_entity(person)
        assert kg.get_entity("p1") is not None
        assert kg.get_entity("p1").name == "Alice Smith"

        # Query
        results = kg.query().entities(EntityType.PERSON).execute()
        assert len(results) == 1

        # Remove
        kg.remove_entity("p1")
        assert kg.get_entity("p1") is None

    def test_add_and_traverse_relationships(self, kg: KnowledgeGraph):
        person = Person(id="p1", first_name="A", last_name="B", name="A B", email="a@b.com")
        dept = Department(id="d1", name="Engineering")
        system = System(id="s1", name="WebApp", system_type="app")

        kg.add_entity(person)
        kg.add_entity(dept)
        kg.add_entity(system)

        kg.add_relationship(BaseRelationship(
            relationship_type=RelationshipType.WORKS_IN,
            source_id="p1", target_id="d1",
        ))
        kg.add_relationship(BaseRelationship(
            relationship_type=RelationshipType.RESPONSIBLE_FOR,
            source_id="d1", target_id="s1",
        ))

        # Neighbors
        neighbors = kg.neighbors("d1")
        neighbor_ids = {n.id for n in neighbors}
        assert "p1" in neighbor_ids
        assert "s1" in neighbor_ids

        # Shortest path
        path = kg.shortest_path("p1", "s1")
        assert path is not None
        assert "p1" in path
        assert "s1" in path

    def test_event_tracking(self, kg: KnowledgeGraph):
        person = Person(id="p1", first_name="A", last_name="B", name="A B", email="a@b.com")
        kg.add_entity(person)
        kg.update_entity("p1", title="Manager")
        kg.remove_entity("p1")

        log = kg.event_log
        types = [e.mutation_type for e in log]
        assert MutationType.CREATE in types
        assert MutationType.UPDATE in types
        assert MutationType.DELETE in types

    def test_event_subscription(self, kg: KnowledgeGraph):
        events_received = []

        def handler(event):
            events_received.append(event)

        kg.subscribe(handler, MutationType.CREATE)
        person = Person(id="p1", first_name="A", last_name="B", name="A B", email="a@b.com")
        kg.add_entity(person)

        assert len(events_received) == 1
        assert events_received[0].mutation_type == MutationType.CREATE

    def test_bulk_operations(self, kg: KnowledgeGraph):
        people = [
            Person(id=f"p{i}", first_name=f"P{i}", last_name="T", name=f"P{i} T", email=f"p{i}@t.com")
            for i in range(10)
        ]
        kg.add_entities_bulk(people)
        assert kg.statistics["entity_count"] == 10

        rels = [
            BaseRelationship(
                relationship_type=RelationshipType.REPORTS_TO,
                source_id=f"p{i}", target_id="p0",
            )
            for i in range(1, 10)
        ]
        kg.add_relationships_bulk(rels)
        assert kg.statistics["relationship_count"] == 9

    def test_statistics(self, populated_kg: KnowledgeGraph):
        stats = populated_kg.statistics
        assert stats["entity_count"] == 3
        assert stats["relationship_count"] == 2
        assert "entity_types" in stats

    def test_query_with_filters(self, kg: KnowledgeGraph):
        kg.add_entity(Person(
            id="p1", first_name="Alice", last_name="Smith",
            name="Alice Smith", email="a@b.com", is_active=True,
        ))
        kg.add_entity(Person(
            id="p2", first_name="Bob", last_name="Jones",
            name="Bob Jones", email="b@c.com", is_active=False,
        ))

        active = kg.query().entities(EntityType.PERSON).where(is_active=True).execute()
        assert len(active) == 1
        assert active[0].id == "p1"

    def test_list_entities_with_limit_offset(self, kg: KnowledgeGraph):
        for i in range(5):
            kg.add_entity(Person(
                id=f"p{i}", first_name=f"P{i}", last_name="T",
                name=f"P{i} T", email=f"p{i}@t.com",
            ))
        page = kg.list_entities(limit=2, offset=0)
        assert len(page) == 2

        page2 = kg.list_entities(limit=2, offset=2)
        assert len(page2) == 2

    def test_relationship_direction_filtering(self, populated_kg: KnowledgeGraph):
        out_rels = populated_kg.get_relationships("person-1", direction="out")
        assert len(out_rels) >= 1

        in_rels = populated_kg.get_relationships("dept-1", direction="in")
        assert len(in_rels) >= 1
