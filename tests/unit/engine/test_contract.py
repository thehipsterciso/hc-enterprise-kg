"""Engine contract tests — reusable for any backend implementation."""

import pytest

from hc_enterprise_kg.domain.base import BaseRelationship, EntityType, RelationshipType
from hc_enterprise_kg.domain.entities.department import Department
from hc_enterprise_kg.domain.entities.person import Person
from hc_enterprise_kg.domain.entities.system import System
from hc_enterprise_kg.engine.abstract import AbstractGraphEngine
from hc_enterprise_kg.engine.networkx_engine import NetworkXGraphEngine


class GraphEngineContractTests:
    """Contract tests that any AbstractGraphEngine implementation must pass."""

    @pytest.fixture
    def engine(self) -> AbstractGraphEngine:
        raise NotImplementedError

    def test_add_and_get_entity(self, engine):
        person = Person(id="p1", first_name="A", last_name="B", name="A B", email="a@b.com")
        eid = engine.add_entity(person)
        assert eid == "p1"

        retrieved = engine.get_entity("p1")
        assert retrieved is not None
        assert retrieved.name == "A B"

    def test_get_nonexistent_entity(self, engine):
        assert engine.get_entity("nonexistent") is None

    def test_update_entity(self, engine):
        person = Person(id="p1", first_name="A", last_name="B", name="A B", email="a@b.com")
        engine.add_entity(person)

        updated = engine.update_entity("p1", {"title": "Senior Engineer"})
        assert updated is not None

    def test_remove_entity(self, engine):
        person = Person(id="p1", first_name="A", last_name="B", name="A B", email="a@b.com")
        engine.add_entity(person)

        assert engine.remove_entity("p1") is True
        assert engine.get_entity("p1") is None

    def test_remove_nonexistent(self, engine):
        assert engine.remove_entity("nonexistent") is False

    def test_list_entities(self, engine):
        engine.add_entity(Person(id="p1", first_name="A", last_name="B", name="A B", email="a@b.com"))
        engine.add_entity(Department(id="d1", name="Eng"))

        all_entities = engine.list_entities()
        assert len(all_entities) == 2

        people = engine.list_entities(entity_type=EntityType.PERSON)
        assert len(people) == 1

    def test_entity_count(self, engine):
        assert engine.entity_count() == 0
        engine.add_entity(Person(id="p1", first_name="A", last_name="B", name="A B", email="a@b.com"))
        assert engine.entity_count() == 1
        assert engine.entity_count(EntityType.PERSON) == 1
        assert engine.entity_count(EntityType.SYSTEM) == 0

    def test_add_relationship(self, engine):
        engine.add_entity(Person(id="p1", first_name="A", last_name="B", name="A B", email="a@b.com"))
        engine.add_entity(Department(id="d1", name="Eng"))

        rel = BaseRelationship(
            id="r1",
            relationship_type=RelationshipType.WORKS_IN,
            source_id="p1",
            target_id="d1",
        )
        rid = engine.add_relationship(rel)
        assert rid == "r1"

    def test_add_relationship_missing_source(self, engine):
        engine.add_entity(Department(id="d1", name="Eng"))
        rel = BaseRelationship(
            relationship_type=RelationshipType.WORKS_IN, source_id="nonexistent", target_id="d1"
        )
        with pytest.raises(KeyError):
            engine.add_relationship(rel)

    def test_get_relationship(self, engine):
        engine.add_entity(Person(id="p1", first_name="A", last_name="B", name="A B", email="a@b.com"))
        engine.add_entity(Department(id="d1", name="Eng"))
        engine.add_relationship(
            BaseRelationship(id="r1", relationship_type=RelationshipType.WORKS_IN, source_id="p1", target_id="d1")
        )

        rel = engine.get_relationship("r1")
        assert rel is not None
        assert rel.source_id == "p1"

    def test_remove_relationship(self, engine):
        engine.add_entity(Person(id="p1", first_name="A", last_name="B", name="A B", email="a@b.com"))
        engine.add_entity(Department(id="d1", name="Eng"))
        engine.add_relationship(
            BaseRelationship(id="r1", relationship_type=RelationshipType.WORKS_IN, source_id="p1", target_id="d1")
        )

        assert engine.remove_relationship("r1") is True
        assert engine.get_relationship("r1") is None

    def test_neighbors(self, engine):
        engine.add_entity(Person(id="p1", first_name="A", last_name="B", name="A B", email="a@b.com"))
        engine.add_entity(Department(id="d1", name="Eng"))
        engine.add_relationship(
            BaseRelationship(relationship_type=RelationshipType.WORKS_IN, source_id="p1", target_id="d1")
        )

        neighbors = engine.neighbors("p1", direction="out")
        assert len(neighbors) == 1
        assert neighbors[0].id == "d1"

    def test_shortest_path(self, engine):
        engine.add_entity(Person(id="p1", first_name="A", last_name="B", name="A B", email="a@b.com"))
        engine.add_entity(Department(id="d1", name="Eng"))
        engine.add_entity(System(id="s1", name="Web App"))
        engine.add_relationship(
            BaseRelationship(relationship_type=RelationshipType.WORKS_IN, source_id="p1", target_id="d1")
        )
        engine.add_relationship(
            BaseRelationship(relationship_type=RelationshipType.RESPONSIBLE_FOR, source_id="d1", target_id="s1")
        )

        path = engine.shortest_path("p1", "s1")
        assert path == ["p1", "d1", "s1"]

    def test_shortest_path_no_path(self, engine):
        engine.add_entity(Person(id="p1", first_name="A", last_name="B", name="A B", email="a@b.com"))
        engine.add_entity(System(id="s1", name="Web App"))
        assert engine.shortest_path("p1", "s1") is None

    def test_bulk_add(self, engine):
        people = [
            Person(id=f"p{i}", first_name=f"F{i}", last_name=f"L{i}", name=f"F{i} L{i}", email=f"p{i}@test.com")
            for i in range(10)
        ]
        ids = engine.add_entities_bulk(people)
        assert len(ids) == 10
        assert engine.entity_count() == 10

    def test_statistics(self, engine):
        engine.add_entity(Person(id="p1", first_name="A", last_name="B", name="A B", email="a@b.com"))
        stats = engine.get_statistics()
        assert stats["total_entities"] == 1
        assert stats["total_relationships"] == 0

    def test_clear(self, engine):
        engine.add_entity(Person(id="p1", first_name="A", last_name="B", name="A B", email="a@b.com"))
        engine.clear()
        assert engine.entity_count() == 0

    def test_remove_entity_removes_relationships(self, engine):
        engine.add_entity(Person(id="p1", first_name="A", last_name="B", name="A B", email="a@b.com"))
        engine.add_entity(Department(id="d1", name="Eng"))
        engine.add_relationship(
            BaseRelationship(id="r1", relationship_type=RelationshipType.WORKS_IN, source_id="p1", target_id="d1")
        )
        engine.remove_entity("p1")
        assert engine.relationship_count() == 0


class TestNetworkXEngine(GraphEngineContractTests):
    """Runs the full engine contract test suite against NetworkX backend."""

    @pytest.fixture
    def engine(self) -> AbstractGraphEngine:
        return NetworkXGraphEngine()
