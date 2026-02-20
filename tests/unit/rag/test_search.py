"""Tests for the GraphSearch fuzzy search module."""

from __future__ import annotations

from domain.base import EntityType
from rag.search import GraphSearch


class TestSearchByName:
    """Tests for GraphSearch.search_by_name."""

    def test_search_by_name_finds_exact_match(self, populated_kg):
        """An exact name should return a high-confidence match."""
        results = GraphSearch.search_by_name(populated_kg, "Alice Smith")
        assert len(results) >= 1
        names = [entity.name for entity, _score in results]
        assert "Alice Smith" in names
        # Exact match should have a high score
        for entity, score in results:
            if entity.name == "Alice Smith":
                assert score >= 90.0

    def test_search_by_name_finds_fuzzy_match(self, populated_kg):
        """A misspelled name should still find a close match via fuzzy matching."""
        results = GraphSearch.search_by_name(populated_kg, "Alce Smth")
        assert len(results) >= 1
        names = [entity.name for entity, _score in results]
        assert "Alice Smith" in names

    def test_search_by_name_returns_empty_for_no_match(self, populated_kg):
        """A completely unrelated query should return no results (below threshold)."""
        results = GraphSearch.search_by_name(populated_kg, "zzzzxxxxxqqqq")
        # All results should be filtered out due to low scores
        assert len(results) == 0


class TestSearchByType:
    """Tests for GraphSearch.search_by_type."""

    def test_search_by_type_filters_correctly(self, populated_kg):
        """Searching by type should return only entities of that type."""
        results = GraphSearch.search_by_type(populated_kg, EntityType.PERSON)
        assert len(results) >= 1
        for entity in results:
            assert entity.entity_type == EntityType.PERSON

        # Department type should return departments
        dept_results = GraphSearch.search_by_type(populated_kg, EntityType.DEPARTMENT)
        assert len(dept_results) >= 1
        for entity in dept_results:
            assert entity.entity_type == EntityType.DEPARTMENT


class TestSearchByAttribute:
    """Tests for GraphSearch.search_by_attribute."""

    def test_search_by_attribute_finds_match(self, populated_kg):
        """Searching by an attribute value should find matching entities."""
        results = GraphSearch.search_by_attribute(populated_kg, "email", "alice.smith@acme.com")
        assert len(results) == 1
        assert results[0].name == "Alice Smith"

    def test_search_by_attribute_case_insensitive(self, populated_kg):
        """Attribute search should be case-insensitive."""
        results = GraphSearch.search_by_attribute(populated_kg, "email", "ALICE.SMITH@ACME.COM")
        assert len(results) == 1
        assert results[0].name == "Alice Smith"
