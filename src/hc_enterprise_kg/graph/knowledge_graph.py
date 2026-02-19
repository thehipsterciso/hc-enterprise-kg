"""High-level KnowledgeGraph facade — the main entry point for the library."""

from __future__ import annotations

from typing import Any

from hc_enterprise_kg.domain.base import (
    BaseEntity,
    BaseRelationship,
    EntityType,
    RelationshipType,
)
from hc_enterprise_kg.domain.registry import EntityRegistry
from hc_enterprise_kg.domain.temporal import GraphEvent, MutationType
from hc_enterprise_kg.engine.abstract import AbstractGraphEngine
from hc_enterprise_kg.engine.factory import GraphEngineFactory
from hc_enterprise_kg.engine.query import QueryBuilder
from hc_enterprise_kg.graph.events import EventBus


class KnowledgeGraph:
    """High-level facade for the Enterprise Knowledge Graph.

    This is the main entry point for all graph operations. It coordinates
    the engine, domain model, event tracking, and query capabilities.

    Usage:
        kg = KnowledgeGraph()
        kg.add_entity(person)
        kg.add_relationship(rel)
        results = kg.query().entities(EntityType.PERSON).where(is_active=True).execute()
    """

    def __init__(
        self,
        backend: str = "networkx",
        track_events: bool = True,
        **engine_kwargs: Any,
    ) -> None:
        EntityRegistry.auto_discover()
        GraphEngineFactory.auto_discover()
        self._engine = GraphEngineFactory.create(backend, **engine_kwargs)
        self._event_bus = EventBus() if track_events else None
        self._event_log: list[GraphEvent] = []

    # --- Entity operations ---

    def add_entity(self, entity: BaseEntity) -> str:
        entity_id = self._engine.add_entity(entity)
        self._record_event(MutationType.CREATE, entity=entity)
        return entity_id

    def get_entity(self, entity_id: str) -> BaseEntity | None:
        return self._engine.get_entity(entity_id)

    def update_entity(self, entity_id: str, **updates: Any) -> BaseEntity:
        before = self._engine.get_entity(entity_id)
        result = self._engine.update_entity(entity_id, updates)
        self._record_event(
            MutationType.UPDATE,
            entity=result,
            before=before.model_dump() if before else None,
        )
        return result

    def remove_entity(self, entity_id: str) -> bool:
        entity = self._engine.get_entity(entity_id)
        success = self._engine.remove_entity(entity_id)
        if success and entity:
            self._record_event(MutationType.DELETE, entity=entity)
        return success

    def list_entities(
        self,
        entity_type: EntityType | None = None,
        filters: dict[str, Any] | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[BaseEntity]:
        return self._engine.list_entities(entity_type, filters, limit, offset)

    # --- Relationship operations ---

    def add_relationship(self, relationship: BaseRelationship) -> str:
        rel_id = self._engine.add_relationship(relationship)
        self._record_event(MutationType.LINK, relationship=relationship)
        return rel_id

    def get_relationship(self, relationship_id: str) -> BaseRelationship | None:
        return self._engine.get_relationship(relationship_id)

    def remove_relationship(self, relationship_id: str) -> bool:
        rel = self._engine.get_relationship(relationship_id)
        success = self._engine.remove_relationship(relationship_id)
        if success and rel:
            self._record_event(MutationType.UNLINK, relationship=rel)
        return success

    def get_relationships(
        self,
        entity_id: str,
        direction: str = "both",
        relationship_type: RelationshipType | None = None,
    ) -> list[BaseRelationship]:
        return self._engine.get_relationships(entity_id, direction, relationship_type)

    # --- Bulk operations ---

    def add_entities_bulk(self, entities: list[BaseEntity]) -> list[str]:
        ids = self._engine.add_entities_bulk(entities)
        for entity in entities:
            self._record_event(MutationType.CREATE, entity=entity)
        return ids

    def add_relationships_bulk(self, relationships: list[BaseRelationship]) -> list[str]:
        ids = self._engine.add_relationships_bulk(relationships)
        for rel in relationships:
            self._record_event(MutationType.LINK, relationship=rel)
        return ids

    # --- Traversal ---

    def neighbors(
        self,
        entity_id: str,
        direction: str = "both",
        relationship_type: RelationshipType | None = None,
        entity_type: EntityType | None = None,
    ) -> list[BaseEntity]:
        return self._engine.neighbors(entity_id, direction, relationship_type, entity_type)

    def shortest_path(self, source_id: str, target_id: str) -> list[str] | None:
        return self._engine.shortest_path(source_id, target_id)

    # --- Query ---

    def query(self) -> QueryBuilder:
        return QueryBuilder(self._engine)

    # --- Event bus ---

    def subscribe(
        self,
        handler: Any,
        mutation_type: MutationType | None = None,
    ) -> None:
        if self._event_bus:
            self._event_bus.subscribe(handler, mutation_type)

    # --- Statistics ---

    @property
    def statistics(self) -> dict[str, Any]:
        return self._engine.get_statistics()

    @property
    def event_log(self) -> list[GraphEvent]:
        return list(self._event_log)

    @property
    def engine(self) -> AbstractGraphEngine:
        return self._engine

    # --- Internal ---

    def _record_event(
        self,
        mutation_type: MutationType,
        entity: BaseEntity | None = None,
        relationship: BaseRelationship | None = None,
        before: dict | None = None,
    ) -> None:
        event = GraphEvent(
            mutation_type=mutation_type,
            entity_type=entity.entity_type.value if entity else None,
            entity_id=entity.id if entity else None,
            relationship_id=relationship.id if relationship else None,
            before_snapshot=before,
            after_snapshot=(
                entity.model_dump() if entity else relationship.model_dump() if relationship else None
            ),
        )
        self._event_log.append(event)
        if self._event_bus:
            self._event_bus.emit(event)
