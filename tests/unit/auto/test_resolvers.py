"""Tests for entity resolvers."""

from auto.resolvers.dedup_resolver import DedupResolver
from domain.entities.person import Person


class TestDedupResolver:
    def test_no_duplicates(self):
        entities = [
            Person(
                id="p1", first_name="Alice", last_name="Smith", name="Alice Smith", email="a@b.com"
            ),
            Person(id="p2", first_name="Bob", last_name="Jones", name="Bob Jones", email="b@c.com"),
        ]
        resolver = DedupResolver()
        result = resolver.resolve(entities)
        assert len(result.entities) == 2
        assert len(result.merged_entity_ids) == 0

    def test_exact_name_duplicate(self):
        entities = [
            Person(
                id="p1", first_name="Alice", last_name="Smith", name="Alice Smith", email="a@b.com"
            ),
            Person(id="p2", first_name="Alice", last_name="Smith", name="Alice Smith", email=""),
        ]
        resolver = DedupResolver(name_threshold=90.0)
        result = resolver.resolve(entities)
        assert len(result.entities) == 1
        assert len(result.merged_entity_ids) == 1

    def test_merge_fills_empty_fields(self):
        entities = [
            Person(
                id="p1",
                first_name="Alice",
                last_name="Smith",
                name="Alice Smith",
                email="alice@test.com",
                title="",
            ),
            Person(
                id="p2",
                first_name="Alice",
                last_name="Smith",
                name="Alice Smith",
                email="",
                title="Engineer",
            ),
        ]
        resolver = DedupResolver(name_threshold=90.0)
        result = resolver.resolve(entities)
        merged = result.entities[0]
        assert merged.email == "alice@test.com"  # From winner
        assert merged.title == "Engineer"  # Filled from loser

    def test_different_types_not_merged(self):
        from domain.entities.department import Department

        entities = [
            Person(
                id="p1",
                first_name="Engineering",
                last_name="",
                name="Engineering",
                email="eng@test.com",
            ),
            Department(id="d1", name="Engineering"),
        ]
        resolver = DedupResolver(name_threshold=90.0)
        result = resolver.resolve(entities)
        assert len(result.entities) == 2
