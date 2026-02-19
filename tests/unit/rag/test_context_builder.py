"""Tests for the ContextBuilder module."""

from __future__ import annotations

from rag.context_builder import ContextBuilder


class TestBuildContext:
    """Tests for ContextBuilder.build_context."""

    def test_build_context_includes_entity_details(self, populated_kg):
        """Context should include entity names, types, and key attributes."""
        entities = populated_kg.list_entities()
        relationships = []
        context = ContextBuilder.build_context(entities, relationships, populated_kg)

        # Should contain the header
        assert "Knowledge Graph Context" in context
        assert f"Entities: {len(entities)}" in context

        # Should contain entity names
        assert "Alice Smith" in context
        assert "Engineering" in context
        assert "Web Application" in context

        # Should contain entity types
        assert "PERSON" in context
        assert "DEPARTMENT" in context
        assert "SYSTEM" in context

    def test_build_context_includes_relationships(self, populated_kg):
        """Context should include relationship descriptions in natural language."""
        entities = populated_kg.list_entities()
        # Get all relationships in the KG
        relationships = []
        for entity in entities:
            rels = populated_kg.get_relationships(entity.id, direction="out")
            relationships.extend(rels)

        context = ContextBuilder.build_context(entities, relationships, populated_kg)

        # Should contain relationship descriptions
        assert "works in" in context
        assert "Alice Smith" in context
        assert "Engineering" in context

    def test_build_context_respects_token_budget(self, populated_kg):
        """Context should be truncated if it exceeds the token budget."""
        entities = populated_kg.list_entities()
        relationships = []
        for entity in entities:
            rels = populated_kg.get_relationships(entity.id, direction="out")
            relationships.extend(rels)

        # Use a very small token budget
        context = ContextBuilder.build_context(
            entities, relationships, populated_kg, max_tokens=50
        )

        # 50 tokens ~ 200 chars. Context should be within budget.
        assert len(context) <= 200 + 3  # +3 for potential "..."

    def test_build_context_empty_input(self, populated_kg):
        """Empty entities and relationships should produce a fallback message."""
        context = ContextBuilder.build_context([], [], populated_kg)
        assert "No relevant context found" in context
