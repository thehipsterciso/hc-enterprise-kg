"""Abstract graph engine interface defining the backend contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from domain.base import (
        BaseEntity,
        BaseRelationship,
        EntityType,
        RelationshipType,
    )


class AbstractGraphEngine(ABC):
    """Abstract interface for graph storage backends.

    All graph operations go through this interface. Concrete implementations
    (NetworkX, Neo4j, etc.) implement these methods. Business logic in the
    graph/ layer ONLY depends on this interface, never on a concrete backend.
    """

    # --- Entity CRUD ---

    @abstractmethod
    def add_entity(self, entity: BaseEntity) -> str:
        """Add an entity to the graph. Returns the entity ID."""
        ...

    @abstractmethod
    def get_entity(self, entity_id: str) -> BaseEntity | None:
        """Retrieve an entity by its ID. Returns None if not found."""
        ...

    @abstractmethod
    def update_entity(self, entity_id: str, updates: dict[str, Any]) -> BaseEntity:
        """Update attributes on an existing entity. Returns updated entity."""
        ...

    @abstractmethod
    def remove_entity(self, entity_id: str) -> bool:
        """Remove an entity and all its relationships. Returns True if found."""
        ...

    @abstractmethod
    def list_entities(
        self,
        entity_type: EntityType | None = None,
        filters: dict[str, Any] | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[BaseEntity]:
        """List entities, optionally filtered by type and attribute filters."""
        ...

    @abstractmethod
    def entity_count(self, entity_type: EntityType | None = None) -> int:
        """Count entities, optionally filtered by type."""
        ...

    # --- Relationship CRUD ---

    @abstractmethod
    def add_relationship(self, relationship: BaseRelationship) -> str:
        """Add a relationship between two entities. Returns relationship ID."""
        ...

    @abstractmethod
    def get_relationship(self, relationship_id: str) -> BaseRelationship | None:
        """Retrieve a relationship by its ID."""
        ...

    @abstractmethod
    def remove_relationship(self, relationship_id: str) -> bool:
        """Remove a relationship. Returns True if found."""
        ...

    @abstractmethod
    def get_relationships(
        self,
        entity_id: str,
        direction: str = "both",
        relationship_type: RelationshipType | None = None,
    ) -> list[BaseRelationship]:
        """Get all relationships for an entity, with optional filters."""
        ...

    @abstractmethod
    def relationship_count(self, relationship_type: RelationshipType | None = None) -> int:
        """Count relationships, optionally filtered by type."""
        ...

    # --- Traversal ---

    @abstractmethod
    def neighbors(
        self,
        entity_id: str,
        direction: str = "both",
        relationship_type: RelationshipType | None = None,
        entity_type: EntityType | None = None,
    ) -> list[BaseEntity]:
        """Get neighboring entities, optionally filtered."""
        ...

    @abstractmethod
    def shortest_path(self, source_id: str, target_id: str) -> list[str] | None:
        """Find shortest path between two entities. Returns list of entity IDs."""
        ...

    @abstractmethod
    def subgraph(self, entity_ids: list[str]) -> AbstractGraphEngine:
        """Extract a subgraph containing only the specified entities."""
        ...

    def blast_radius(self, entity_id: str, max_depth: int = 3) -> dict[int, list[BaseEntity]]:
        """Compute entities reachable within N hops via BFS.

        Returns a dict mapping hop depth to lists of entities at that depth.
        Override in subclasses for more efficient implementations.
        """
        visited: set[str] = set()
        queue: deque[tuple[str, int]] = deque([(entity_id, 0)])
        by_depth: dict[int, list[BaseEntity]] = {}

        while queue:
            current_id, depth = queue.popleft()
            if current_id in visited or depth > max_depth:
                continue
            visited.add(current_id)

            if current_id != entity_id:
                entity = self.get_entity(current_id)
                if entity:
                    by_depth.setdefault(depth, []).append(entity)

            if depth < max_depth:
                for neighbor in self.neighbors(current_id):
                    if neighbor.id not in visited:
                        queue.append((neighbor.id, depth + 1))

        return by_depth

    # --- Bulk Operations ---

    @abstractmethod
    def add_entities_bulk(self, entities: list[BaseEntity]) -> list[str]:
        """Add multiple entities efficiently. Returns list of IDs."""
        ...

    @abstractmethod
    def add_relationships_bulk(self, relationships: list[BaseRelationship]) -> list[str]:
        """Add multiple relationships efficiently. Returns list of IDs."""
        ...

    # --- Introspection ---

    @abstractmethod
    def get_statistics(self) -> dict[str, Any]:
        """Return summary statistics about the graph."""
        ...

    @abstractmethod
    def clear(self) -> None:
        """Remove all entities and relationships."""
        ...

    @abstractmethod
    def get_native_graph(self) -> Any:
        """Return the underlying native graph object (e.g., nx.MultiDiGraph)."""
        ...
