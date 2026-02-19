"""Fluent query builder for graph queries."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from hc_enterprise_kg.domain.base import BaseEntity, EntityType, RelationshipType
from hc_enterprise_kg.engine.abstract import AbstractGraphEngine


@dataclass
class QuerySpec:
    """Declarative query specification built by QueryBuilder."""

    entity_type: EntityType | None = None
    filters: dict[str, Any] = field(default_factory=dict)
    relationship_traversals: list[dict[str, Any]] = field(default_factory=list)
    limit: int | None = None
    offset: int = 0


class QueryBuilder:
    """Fluent API for constructing graph queries.

    Usage:
        results = (
            QueryBuilder(engine)
            .entities(EntityType.PERSON)
            .where(is_active=True)
            .connected_to(dept_id, via=RelationshipType.WORKS_IN)
            .limit(50)
            .execute()
        )
    """

    def __init__(self, engine: AbstractGraphEngine) -> None:
        self._engine = engine
        self._spec = QuerySpec()

    def entities(self, entity_type: EntityType) -> QueryBuilder:
        self._spec.entity_type = entity_type
        return self

    def where(self, **filters: Any) -> QueryBuilder:
        self._spec.filters.update(filters)
        return self

    def connected_to(
        self,
        entity_id: str,
        via: RelationshipType | None = None,
        direction: str = "both",
    ) -> QueryBuilder:
        self._spec.relationship_traversals.append(
            {
                "entity_id": entity_id,
                "relationship_type": via,
                "direction": direction,
            }
        )
        return self

    def limit(self, n: int) -> QueryBuilder:
        self._spec.limit = n
        return self

    def offset(self, n: int) -> QueryBuilder:
        self._spec.offset = n
        return self

    def execute(self) -> list[BaseEntity]:
        """Execute the query and return matching entities."""
        results = self._engine.list_entities(
            entity_type=self._spec.entity_type,
            filters=self._spec.filters if self._spec.filters else None,
            limit=None,  # Apply limit after traversal filters
            offset=0,
        )

        # Apply traversal filters
        for traversal in self._spec.relationship_traversals:
            neighbor_ids = {
                e.id
                for e in self._engine.neighbors(
                    traversal["entity_id"],
                    direction=traversal["direction"],
                    relationship_type=traversal.get("relationship_type"),
                )
            }
            results = [e for e in results if e.id in neighbor_ids]

        # Apply offset and limit
        results = results[self._spec.offset :]
        if self._spec.limit is not None:
            results = results[: self._spec.limit]

        return results

    def count(self) -> int:
        """Execute the query and return the count of matching entities."""
        return len(self.execute())
