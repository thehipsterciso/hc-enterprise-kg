"""Fuzzy entity search for the knowledge graph using rapidfuzz."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rapidfuzz import fuzz, process

if TYPE_CHECKING:
    from domain.base import BaseEntity, EntityType
    from graph.knowledge_graph import KnowledgeGraph


class GraphSearch:
    """Provides fuzzy and filtered search across knowledge graph entities."""

    @staticmethod
    def search_by_name(
        kg: KnowledgeGraph,
        query: str,
        top_k: int = 10,
    ) -> list[tuple[BaseEntity, float]]:
        """Fuzzy match entity names, returning entities with match scores.

        Args:
            kg: The knowledge graph to search.
            query: The search string to match against entity names.
            top_k: Maximum number of results to return.

        Returns:
            List of (entity, score) tuples sorted by descending score.
        """
        all_entities = kg.list_entities()
        if not all_entities:
            return []

        # Build a mapping from name to entities (multiple entities can share a name)
        name_to_entities: dict[str, list[BaseEntity]] = {}
        for entity in all_entities:
            name_to_entities.setdefault(entity.name, []).append(entity)

        names = list(name_to_entities.keys())
        matches = process.extract(
            query,
            names,
            scorer=fuzz.WRatio,
            limit=top_k,
        )

        results: list[tuple[BaseEntity, float]] = []
        for name, score, _idx in matches:
            if score < 50.0:
                continue
            for entity in name_to_entities[name]:
                results.append((entity, score))

        # Sort by score descending, then trim to top_k
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    @staticmethod
    def search_by_type(
        kg: KnowledgeGraph,
        entity_type: EntityType,
        limit: int = 50,
    ) -> list[BaseEntity]:
        """Get entities of a specific type.

        Args:
            kg: The knowledge graph to search.
            entity_type: The type of entities to retrieve.
            limit: Maximum number of results to return.

        Returns:
            List of entities matching the specified type.
        """
        return kg.list_entities(entity_type=entity_type, limit=limit)

    @staticmethod
    def search_by_attribute(
        kg: KnowledgeGraph,
        key: str,
        value: str,
        entity_type: EntityType | None = None,
    ) -> list[BaseEntity]:
        """Find entities where an attribute contains a value (case-insensitive).

        Args:
            kg: The knowledge graph to search.
            key: The attribute name to search.
            value: The value to look for (case-insensitive substring match).
            entity_type: Optional type filter.

        Returns:
            List of entities whose attribute contains the value.
        """
        all_entities = kg.list_entities(entity_type=entity_type)
        results: list[BaseEntity] = []
        value_lower = value.lower()

        for entity in all_entities:
            entity_data = entity.model_dump()
            attr_value = entity_data.get(key)
            if attr_value is not None and value_lower in str(attr_value).lower():
                results.append(entity)

        return results
