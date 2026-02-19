"""Tests for the GraphRAGRetriever pipeline."""

from __future__ import annotations

from domain.base import BaseRelationship, RelationshipType
from domain.entities.department import Department
from domain.entities.person import Person
from graph.knowledge_graph import KnowledgeGraph
from rag.retriever import GraphRAGRetriever


def _build_rich_kg() -> KnowledgeGraph:
    """Build a KG with multiple interconnected entities for retrieval tests."""
    kg = KnowledgeGraph(backend="networkx", track_events=False)

    people = [
        Person(
            id="p1", first_name="Alice", last_name="Smith",
            name="Alice Smith", email="alice@acme.com", title="Engineer",
        ),
        Person(
            id="p2", first_name="Bob", last_name="Johnson",
            name="Bob Johnson", email="bob@acme.com", title="Manager",
        ),
        Person(
            id="p3", first_name="Carol", last_name="Williams",
            name="Carol Williams", email="carol@acme.com", title="Analyst",
        ),
    ]
    dept = Department(
        id="d1", name="Engineering", description="Eng dept", code="ENG", headcount=10,
    )

    kg.add_entities_bulk(people)
    kg.add_entity(dept)

    kg.add_relationship(BaseRelationship(
        relationship_type=RelationshipType.WORKS_IN, source_id="p1", target_id="d1",
    ))
    kg.add_relationship(BaseRelationship(
        relationship_type=RelationshipType.WORKS_IN, source_id="p2", target_id="d1",
    ))
    kg.add_relationship(BaseRelationship(
        relationship_type=RelationshipType.MANAGES, source_id="p2", target_id="p1",
    ))

    return kg


class TestRetrieve:
    """Tests for GraphRAGRetriever.retrieve."""

    def test_retrieve_finds_relevant_entities(self):
        """Retrieve should find entities matching keywords in the question."""
        kg = _build_rich_kg()
        retriever = GraphRAGRetriever()
        result = retriever.retrieve("Tell me about Alice Smith", kg)

        entity_names = [e.name for e in result.entities]
        assert "Alice Smith" in entity_names
        assert result.stats["entities_returned"] >= 1

    def test_retrieve_expands_neighbors(self):
        """Retrieve should include neighbor entities of matched entities."""
        kg = _build_rich_kg()
        retriever = GraphRAGRetriever()
        result = retriever.retrieve("Alice Smith", kg)

        entity_names = [e.name for e in result.entities]
        # Alice's neighbors: Engineering (works_in) and Bob (manages)
        assert "Alice Smith" in entity_names
        # At least one neighbor should be included
        assert len(result.entities) > 1

    def test_retrieve_returns_context_string(self):
        """Retrieve should return a non-empty formatted context string."""
        kg = _build_rich_kg()
        retriever = GraphRAGRetriever()
        result = retriever.retrieve("Who works in Engineering?", kg)

        assert result.context
        assert "Knowledge Graph Context" in result.context
        assert len(result.context) > 50

    def test_retrieve_respects_top_k(self):
        """Retrieve should not return more entities than top_k."""
        kg = _build_rich_kg()
        retriever = GraphRAGRetriever()
        result = retriever.retrieve("Tell me about everyone", kg, top_k=2)

        assert len(result.entities) <= 2
        assert result.stats["entities_returned"] <= 2

    def test_retrieve_handles_no_matches(self):
        """Retrieve should return empty results for a completely unrelated question."""
        kg = _build_rich_kg()
        retriever = GraphRAGRetriever()
        result = retriever.retrieve("zzzzxxxxxqqqq yyyyywwwww", kg)

        assert len(result.entities) == 0
        assert len(result.relationships) == 0
        assert result.context  # Should still produce a context string (the "no results" message)
