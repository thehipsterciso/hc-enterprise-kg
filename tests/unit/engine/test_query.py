"""Tests for QueryBuilder."""

from hc_enterprise_kg.domain.base import BaseRelationship, EntityType, RelationshipType
from hc_enterprise_kg.domain.entities.department import Department
from hc_enterprise_kg.domain.entities.person import Person
from hc_enterprise_kg.engine.networkx_engine import NetworkXGraphEngine
from hc_enterprise_kg.engine.query import QueryBuilder


class TestQueryBuilder:
    def test_query_by_type(self, engine):
        engine.add_entity(Person(id="p1", first_name="A", last_name="B", name="A B", email="a@b.com"))
        engine.add_entity(Department(id="d1", name="Eng"))

        results = QueryBuilder(engine).entities(EntityType.PERSON).execute()
        assert len(results) == 1
        assert results[0].id == "p1"

    def test_query_with_filter(self, engine):
        engine.add_entity(Person(id="p1", first_name="A", last_name="B", name="A B", email="a@b.com", is_active=True))
        engine.add_entity(Person(id="p2", first_name="C", last_name="D", name="C D", email="c@d.com", is_active=False))

        results = QueryBuilder(engine).entities(EntityType.PERSON).where(is_active=True).execute()
        assert len(results) == 1

    def test_query_with_limit(self, engine):
        for i in range(10):
            engine.add_entity(Person(id=f"p{i}", first_name=f"F{i}", last_name=f"L{i}", name=f"F{i}", email=f"{i}@t.com"))

        results = QueryBuilder(engine).entities(EntityType.PERSON).limit(3).execute()
        assert len(results) == 3

    def test_query_connected_to(self, engine):
        engine.add_entity(Person(id="p1", first_name="A", last_name="B", name="A B", email="a@b.com"))
        engine.add_entity(Person(id="p2", first_name="C", last_name="D", name="C D", email="c@d.com"))
        engine.add_entity(Department(id="d1", name="Eng"))
        engine.add_relationship(BaseRelationship(relationship_type=RelationshipType.WORKS_IN, source_id="p1", target_id="d1"))

        results = (
            QueryBuilder(engine)
            .entities(EntityType.PERSON)
            .connected_to("d1", via=RelationshipType.WORKS_IN, direction="in")
            .execute()
        )
        assert len(results) == 1
        assert results[0].id == "p1"

    def test_query_count(self, engine):
        engine.add_entity(Person(id="p1", first_name="A", last_name="B", name="A B", email="a@b.com"))
        engine.add_entity(Person(id="p2", first_name="C", last_name="D", name="C D", email="c@d.com"))

        count = QueryBuilder(engine).entities(EntityType.PERSON).count()
        assert count == 2
