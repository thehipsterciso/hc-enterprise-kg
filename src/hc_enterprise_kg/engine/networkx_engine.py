"""NetworkX-backed graph engine implementation."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import networkx as nx

from hc_enterprise_kg.domain.base import (
    BaseEntity,
    BaseRelationship,
    EntityType,
    RelationshipType,
)
from hc_enterprise_kg.domain.registry import EntityRegistry
from hc_enterprise_kg.engine.abstract import AbstractGraphEngine


class NetworkXGraphEngine(AbstractGraphEngine):
    """In-memory graph engine backed by NetworkX MultiDiGraph.

    Entities are stored as nodes with their Pydantic model dict as attributes.
    Relationships are stored as edges keyed by relationship ID.
    """

    def __init__(self) -> None:
        self._graph = nx.MultiDiGraph()
        self._relationship_index: dict[str, tuple[str, str, str]] = {}

    # --- Entity CRUD ---

    def add_entity(self, entity: BaseEntity) -> str:
        data = entity.model_dump(mode="python")
        # Store entity_type as string for serialization
        data["entity_type"] = entity.entity_type.value
        self._graph.add_node(entity.id, **data)
        return entity.id

    def get_entity(self, entity_id: str) -> BaseEntity | None:
        if entity_id not in self._graph:
            return None
        data = dict(self._graph.nodes[entity_id])
        return self._deserialize_entity(data)

    def update_entity(self, entity_id: str, updates: dict[str, Any]) -> BaseEntity:
        if entity_id not in self._graph:
            raise KeyError(f"Entity not found: {entity_id}")
        node_data = self._graph.nodes[entity_id]
        node_data.update(updates)
        node_data["updated_at"] = datetime.utcnow()
        node_data["version"] = node_data.get("version", 1) + 1
        return self._deserialize_entity(dict(node_data))

    def remove_entity(self, entity_id: str) -> bool:
        if entity_id not in self._graph:
            return False
        # Remove all relationships involving this entity from the index
        edges_to_remove = []
        for rel_id, (src, tgt, key) in list(self._relationship_index.items()):
            if src == entity_id or tgt == entity_id:
                edges_to_remove.append(rel_id)
        for rel_id in edges_to_remove:
            del self._relationship_index[rel_id]
        self._graph.remove_node(entity_id)
        return True

    def list_entities(
        self,
        entity_type: EntityType | None = None,
        filters: dict[str, Any] | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[BaseEntity]:
        results: list[BaseEntity] = []
        for node_id, data in self._graph.nodes(data=True):
            if entity_type and data.get("entity_type") != entity_type.value:
                continue
            if filters:
                if not all(data.get(k) == v for k, v in filters.items()):
                    continue
            entity = self._deserialize_entity(dict(data))
            if entity:
                results.append(entity)

        results = results[offset:]
        if limit is not None:
            results = results[:limit]
        return results

    def entity_count(self, entity_type: EntityType | None = None) -> int:
        if entity_type is None:
            return self._graph.number_of_nodes()
        return sum(
            1
            for _, data in self._graph.nodes(data=True)
            if data.get("entity_type") == entity_type.value
        )

    # --- Relationship CRUD ---

    def add_relationship(self, relationship: BaseRelationship) -> str:
        if relationship.source_id not in self._graph:
            raise KeyError(f"Source entity not found: {relationship.source_id}")
        if relationship.target_id not in self._graph:
            raise KeyError(f"Target entity not found: {relationship.target_id}")

        data = relationship.model_dump(mode="python")
        data["relationship_type"] = relationship.relationship_type.value
        key = self._graph.add_edge(
            relationship.source_id,
            relationship.target_id,
            key=relationship.id,
            **data,
        )
        self._relationship_index[relationship.id] = (
            relationship.source_id,
            relationship.target_id,
            key,
        )
        return relationship.id

    def get_relationship(self, relationship_id: str) -> BaseRelationship | None:
        if relationship_id not in self._relationship_index:
            return None
        src, tgt, key = self._relationship_index[relationship_id]
        data = dict(self._graph.edges[src, tgt, key])
        return self._deserialize_relationship(data)

    def remove_relationship(self, relationship_id: str) -> bool:
        if relationship_id not in self._relationship_index:
            return False
        src, tgt, key = self._relationship_index[relationship_id]
        self._graph.remove_edge(src, tgt, key=key)
        del self._relationship_index[relationship_id]
        return True

    def get_relationships(
        self,
        entity_id: str,
        direction: str = "both",
        relationship_type: RelationshipType | None = None,
    ) -> list[BaseRelationship]:
        results: list[BaseRelationship] = []
        rel_type_val = relationship_type.value if relationship_type else None

        if direction in ("out", "both"):
            for _, tgt, data in self._graph.out_edges(entity_id, data=True):
                if rel_type_val and data.get("relationship_type") != rel_type_val:
                    continue
                rel = self._deserialize_relationship(dict(data))
                if rel:
                    results.append(rel)

        if direction in ("in", "both"):
            for src, _, data in self._graph.in_edges(entity_id, data=True):
                if rel_type_val and data.get("relationship_type") != rel_type_val:
                    continue
                rel = self._deserialize_relationship(dict(data))
                if rel:
                    results.append(rel)

        return results

    def relationship_count(self, relationship_type: RelationshipType | None = None) -> int:
        if relationship_type is None:
            return self._graph.number_of_edges()
        rel_type_val = relationship_type.value
        return sum(
            1
            for _, _, data in self._graph.edges(data=True)
            if data.get("relationship_type") == rel_type_val
        )

    # --- Traversal ---

    def neighbors(
        self,
        entity_id: str,
        direction: str = "both",
        relationship_type: RelationshipType | None = None,
        entity_type: EntityType | None = None,
    ) -> list[BaseEntity]:
        neighbor_ids: set[str] = set()
        rel_type_val = relationship_type.value if relationship_type else None

        if direction in ("out", "both"):
            for _, tgt, data in self._graph.out_edges(entity_id, data=True):
                if rel_type_val and data.get("relationship_type") != rel_type_val:
                    continue
                neighbor_ids.add(tgt)

        if direction in ("in", "both"):
            for src, _, data in self._graph.in_edges(entity_id, data=True):
                if rel_type_val and data.get("relationship_type") != rel_type_val:
                    continue
                neighbor_ids.add(src)

        results: list[BaseEntity] = []
        for nid in neighbor_ids:
            entity = self.get_entity(nid)
            if entity is None:
                continue
            if entity_type and entity.entity_type != entity_type:
                continue
            results.append(entity)
        return results

    def shortest_path(self, source_id: str, target_id: str) -> list[str] | None:
        try:
            return nx.shortest_path(self._graph, source_id, target_id)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def subgraph(self, entity_ids: list[str]) -> NetworkXGraphEngine:
        sub = NetworkXGraphEngine()
        sub_nx = self._graph.subgraph(entity_ids).copy()
        sub._graph = sub_nx
        # Rebuild relationship index for the subgraph
        for src, tgt, key, data in sub_nx.edges(keys=True, data=True):
            rel_id = data.get("id", key)
            sub._relationship_index[rel_id] = (src, tgt, key)
        return sub

    # --- Bulk Operations ---

    def add_entities_bulk(self, entities: list[BaseEntity]) -> list[str]:
        ids: list[str] = []
        for entity in entities:
            ids.append(self.add_entity(entity))
        return ids

    def add_relationships_bulk(self, relationships: list[BaseRelationship]) -> list[str]:
        ids: list[str] = []
        for rel in relationships:
            ids.append(self.add_relationship(rel))
        return ids

    # --- Introspection ---

    def get_statistics(self) -> dict[str, Any]:
        g = self._graph
        type_counts: dict[str, int] = {}
        for _, data in g.nodes(data=True):
            t = data.get("entity_type", "unknown")
            type_counts[t] = type_counts.get(t, 0) + 1

        rel_type_counts: dict[str, int] = {}
        for _, _, data in g.edges(data=True):
            t = data.get("relationship_type", "unknown")
            rel_type_counts[t] = rel_type_counts.get(t, 0) + 1

        return {
            "total_entities": g.number_of_nodes(),
            "total_relationships": g.number_of_edges(),
            "entity_type_counts": type_counts,
            "relationship_type_counts": rel_type_counts,
            "density": nx.density(g),
            "is_weakly_connected": (
                nx.is_weakly_connected(g) if g.number_of_nodes() > 0 else True
            ),
        }

    def clear(self) -> None:
        self._graph.clear()
        self._relationship_index.clear()

    def get_native_graph(self) -> nx.MultiDiGraph:
        return self._graph

    # --- Internal helpers ---

    def _deserialize_entity(self, data: dict[str, Any]) -> BaseEntity | None:
        try:
            entity_type = EntityType(data["entity_type"])
            entity_class = EntityRegistry.get(entity_type)
            return entity_class.model_validate(data)
        except (KeyError, ValueError):
            return None

    def _deserialize_relationship(self, data: dict[str, Any]) -> BaseRelationship | None:
        try:
            data["relationship_type"] = RelationshipType(data["relationship_type"])
            return BaseRelationship.model_validate(data)
        except (KeyError, ValueError):
            return None
