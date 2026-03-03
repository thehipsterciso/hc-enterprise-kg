"""Graph Context Engine — retrieves full neighborhood context for entity enrichment.

The GraphContextEngine is a critical bridge between the KnowledgeGraph and enrichers.
No enricher operates in a silo; every enrichment decision considers the entity's neighbors,
relationships, and broader organizational context.

This module provides efficient graph traversal and context aggregation for enrichment
operations, including entity neighborhood retrieval, cross-entity profiling, and
relationship-aware querying.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from domain.base import BaseEntity, BaseRelationship, EntityType, RelationshipType
from enrichment.base import CrossEntityProfile, EntityContext

if TYPE_CHECKING:
    from graph.knowledge_graph import KnowledgeGraph

logger = logging.getLogger(__name__)


@dataclass
class HolisticEntityProfile:
    """Extended holistic profile for a single entity with typed neighbors."""

    entity: BaseEntity
    department: BaseEntity | None = None
    org_unit: BaseEntity | None = None
    roles: list[BaseEntity] = field(default_factory=list)
    systems: list[BaseEntity] = field(default_factory=list)
    risks: list[BaseEntity] = field(default_factory=list)
    controls: list[BaseEntity] = field(default_factory=list)
    locations: list[BaseEntity] = field(default_factory=list)
    sites: list[BaseEntity] = field(default_factory=list)
    jurisdictions: list[BaseEntity] = field(default_factory=list)
    vendors: list[BaseEntity] = field(default_factory=list)
    contracts: list[BaseEntity] = field(default_factory=list)
    initiatives: list[BaseEntity] = field(default_factory=list)
    policies: list[BaseEntity] = field(default_factory=list)
    data_assets: list[BaseEntity] = field(default_factory=list)
    threat_actors: list[BaseEntity] = field(default_factory=list)
    vulnerabilities: list[BaseEntity] = field(default_factory=list)
    incidents: list[BaseEntity] = field(default_factory=list)
    regulations: list[BaseEntity] = field(default_factory=list)
    business_capabilities: list[BaseEntity] = field(default_factory=list)
    data_domains: list[BaseEntity] = field(default_factory=list)
    data_flows: list[BaseEntity] = field(default_factory=list)
    networks: list[BaseEntity] = field(default_factory=list)
    integrations: list[BaseEntity] = field(default_factory=list)
    geographies: list[BaseEntity] = field(default_factory=list)
    product_portfolios: list[BaseEntity] = field(default_factory=list)
    products: list[BaseEntity] = field(default_factory=list)
    market_segments: list[BaseEntity] = field(default_factory=list)
    customers: list[BaseEntity] = field(default_factory=list)
    people: list[BaseEntity] = field(default_factory=list)
    threats: list[BaseEntity] = field(default_factory=list)

    def neighbor_count(self) -> int:
        """Return total count of all neighbors across all typed lists."""
        return sum(
            len(neighbors)
            for neighbors in [
                [self.department] if self.department else [],
                [self.org_unit] if self.org_unit else [],
                self.roles,
                self.systems,
                self.risks,
                self.controls,
                self.locations,
                self.sites,
                self.jurisdictions,
                self.vendors,
                self.contracts,
                self.initiatives,
                self.policies,
                self.data_assets,
                self.threat_actors,
                self.vulnerabilities,
                self.incidents,
                self.regulations,
                self.business_capabilities,
                self.data_domains,
                self.data_flows,
                self.networks,
                self.integrations,
                self.geographies,
                self.product_portfolios,
                self.products,
                self.market_segments,
                self.customers,
                self.people,
                self.threats,
            ]
        )

    def get_neighbors_by_type(self, entity_type: EntityType) -> list[BaseEntity]:
        """Retrieve neighbors of a specific entity type.

        Args:
            entity_type: The type of neighbors to retrieve.

        Returns:
            List of neighbors of the specified type, or empty list if none found.
        """
        type_map = {
            EntityType.DEPARTMENT: [self.department] if self.department else [],
            EntityType.ORGANIZATIONAL_UNIT: (
                [self.org_unit] if self.org_unit else []
            ),
            EntityType.ROLE: self.roles,
            EntityType.SYSTEM: self.systems,
            EntityType.RISK: self.risks,
            EntityType.CONTROL: self.controls,
            EntityType.LOCATION: self.locations,
            EntityType.SITE: self.sites,
            EntityType.JURISDICTION: self.jurisdictions,
            EntityType.VENDOR: self.vendors,
            EntityType.CONTRACT: self.contracts,
            EntityType.INITIATIVE: self.initiatives,
            EntityType.POLICY: self.policies,
            EntityType.DATA_ASSET: self.data_assets,
            EntityType.THREAT_ACTOR: self.threat_actors,
            EntityType.VULNERABILITY: self.vulnerabilities,
            EntityType.INCIDENT: self.incidents,
            EntityType.REGULATION: self.regulations,
            EntityType.BUSINESS_CAPABILITY: self.business_capabilities,
            EntityType.DATA_DOMAIN: self.data_domains,
            EntityType.DATA_FLOW: self.data_flows,
            EntityType.NETWORK: self.networks,
            EntityType.INTEGRATION: self.integrations,
            EntityType.GEOGRAPHY: self.geographies,
            EntityType.PRODUCT_PORTFOLIO: self.product_portfolios,
            EntityType.PRODUCT: self.products,
            EntityType.MARKET_SEGMENT: self.market_segments,
            EntityType.CUSTOMER: self.customers,
            EntityType.PERSON: self.people,
            EntityType.THREAT: self.threats,
        }
        return type_map.get(entity_type, [])


class GraphContextEngine:
    """Retrieves full neighborhood context for any entity being enriched.

    This engine bridges the KnowledgeGraph and enrichers, providing efficient
    access to entity neighborhoods, relationship metadata, and cross-entity profiles.
    All context retrieval goes through this engine to ensure consistency and enable
    caching/optimization strategies.

    Attributes:
        kg: The KnowledgeGraph instance to query from.
    """

    def __init__(self, kg: KnowledgeGraph) -> None:
        """Initialize the GraphContextEngine.

        Args:
            kg: KnowledgeGraph instance to use for traversal and entity lookup.
        """
        self.kg = kg

    def get_entity_context(self, entity_id: str) -> EntityContext:
        """Retrieve the full graph context for an entity.

        Returns the entity itself, all its direct neighbors grouped by relationship
        type, and relationship metadata for each edge. This context is the primary
        input to all enrichers.

        Args:
            entity_id: ID of the entity to get context for.

        Returns:
            EntityContext containing the entity, neighbors grouped by relationship
            type, and relationship metadata.

        Raises:
            ValueError: If entity_id does not exist in the knowledge graph.
        """
        entity = self.kg.get_entity(entity_id)
        if entity is None:
            raise ValueError(f"Entity {entity_id} not found in knowledge graph")

        # Get all relationships for this entity (both incoming and outgoing)
        relationships = self.kg.get_relationships(entity_id, direction="both")

        # Build neighbors_by_type mapping
        neighbors_by_type: dict[RelationshipType, list[BaseEntity]] = {}

        for rel in relationships:
            # Determine target entity: if source is our entity, target is the neighbor
            target_id = (
                rel.target_id if rel.source_id == entity_id else rel.source_id
            )
            target_entity = self.kg.get_entity(target_id)

            if target_entity is None:
                logger.warning(
                    f"Relationship {rel.id} references non-existent entity {target_id}"
                )
                continue

            rel_type = RelationshipType(rel.relationship_type)
            if rel_type not in neighbors_by_type:
                neighbors_by_type[rel_type] = []

            # Avoid duplicates (in case of multi-edges)
            if target_entity not in neighbors_by_type[rel_type]:
                neighbors_by_type[rel_type].append(target_entity)

        return EntityContext(
            entity=entity, neighbors_by_type=neighbors_by_type, relationships=relationships
        )

    def get_cross_entity_profile(self, entity_id: str) -> HolisticEntityProfile:
        """Build a holistic profile by traversing the entity's neighborhood.

        Creates a typed, multi-entity profile from graph traversal, enabling
        enrichers to understand the full organizational context. For example,
        for a Person, retrieves their department, role, assigned systems, risks,
        controls, locations, jurisdictions, initiatives, and more.

        Args:
            entity_id: ID of the entity to build a profile for.

        Returns:
            HolisticEntityProfile containing the entity and all typed neighbors.

        Raises:
            ValueError: If entity_id does not exist in the knowledge graph.
        """
        entity = self.kg.get_entity(entity_id)
        if entity is None:
            raise ValueError(f"Entity {entity_id} not found in knowledge graph")

        profile = HolisticEntityProfile(entity=entity)

        # Retrieve neighbors for all entity types
        # For efficiency, retrieve by type rather than iterating all neighbors
        for target_type in EntityType:
            neighbors = self.kg.neighbors(
                entity_id, direction="both", entity_type=target_type
            )

            if not neighbors:
                continue

            # Assign neighbors to the appropriate profile field
            if target_type == EntityType.DEPARTMENT:
                profile.department = neighbors[0] if neighbors else None
            elif target_type == EntityType.ORGANIZATIONAL_UNIT:
                profile.org_unit = neighbors[0] if neighbors else None
            elif target_type == EntityType.ROLE:
                profile.roles = neighbors
            elif target_type == EntityType.SYSTEM:
                profile.systems = neighbors
            elif target_type == EntityType.RISK:
                profile.risks = neighbors
            elif target_type == EntityType.CONTROL:
                profile.controls = neighbors
            elif target_type == EntityType.LOCATION:
                profile.locations = neighbors
            elif target_type == EntityType.SITE:
                profile.sites = neighbors
            elif target_type == EntityType.JURISDICTION:
                profile.jurisdictions = neighbors
            elif target_type == EntityType.VENDOR:
                profile.vendors = neighbors
            elif target_type == EntityType.CONTRACT:
                profile.contracts = neighbors
            elif target_type == EntityType.INITIATIVE:
                profile.initiatives = neighbors
            elif target_type == EntityType.POLICY:
                profile.policies = neighbors
            elif target_type == EntityType.DATA_ASSET:
                profile.data_assets = neighbors
            elif target_type == EntityType.THREAT_ACTOR:
                profile.threat_actors = neighbors
            elif target_type == EntityType.VULNERABILITY:
                profile.vulnerabilities = neighbors
            elif target_type == EntityType.INCIDENT:
                profile.incidents = neighbors
            elif target_type == EntityType.REGULATION:
                profile.regulations = neighbors
            elif target_type == EntityType.BUSINESS_CAPABILITY:
                profile.business_capabilities = neighbors
            elif target_type == EntityType.DATA_DOMAIN:
                profile.data_domains = neighbors
            elif target_type == EntityType.DATA_FLOW:
                profile.data_flows = neighbors
            elif target_type == EntityType.NETWORK:
                profile.networks = neighbors
            elif target_type == EntityType.INTEGRATION:
                profile.integrations = neighbors
            elif target_type == EntityType.GEOGRAPHY:
                profile.geographies = neighbors
            elif target_type == EntityType.PRODUCT_PORTFOLIO:
                profile.product_portfolios = neighbors
            elif target_type == EntityType.PRODUCT:
                profile.products = neighbors
            elif target_type == EntityType.MARKET_SEGMENT:
                profile.market_segments = neighbors
            elif target_type == EntityType.CUSTOMER:
                profile.customers = neighbors
            elif target_type == EntityType.PERSON:
                profile.people = neighbors
            elif target_type == EntityType.THREAT:
                profile.threats = neighbors

        return profile

    def get_neighbors_by_type(
        self, entity_id: str, entity_type: EntityType
    ) -> list[BaseEntity]:
        """Retrieve all neighbors of a specific entity type.

        Convenience method for querying neighbors filtered by a single entity type.

        Args:
            entity_id: ID of the entity whose neighbors to retrieve.
            entity_type: Filter neighbors to this entity type.

        Returns:
            List of neighbors matching the specified entity type.
        """
        return self.kg.neighbors(
            entity_id, direction="both", entity_type=entity_type
        )

    def get_relationship_context(
        self, entity_id: str
    ) -> dict[RelationshipType, list[tuple[BaseRelationship, BaseEntity]]]:
        """Retrieve all relationships with both edge and target entity metadata.

        Returns a map of relationship types to lists of (relationship, target_entity)
        tuples. This provides enrichers with both the edge metadata and the full
        target entity context.

        Args:
            entity_id: ID of the entity whose relationships to retrieve.

        Returns:
            Dict mapping RelationshipType to list of (edge, target_entity) tuples.

        Raises:
            ValueError: If entity_id does not exist in the knowledge graph.
        """
        entity = self.kg.get_entity(entity_id)
        if entity is None:
            raise ValueError(f"Entity {entity_id} not found in knowledge graph")

        relationships = self.kg.get_relationships(entity_id, direction="both")
        context: dict[RelationshipType, list[tuple[BaseRelationship, BaseEntity]]] = {}

        for rel in relationships:
            # Determine target entity ID
            target_id = (
                rel.target_id if rel.source_id == entity_id else rel.source_id
            )
            target_entity = self.kg.get_entity(target_id)

            if target_entity is None:
                logger.warning(
                    f"Relationship {rel.id} references non-existent entity {target_id}"
                )
                continue

            rel_type = RelationshipType(rel.relationship_type)
            if rel_type not in context:
                context[rel_type] = []

            context[rel_type].append((rel, target_entity))

        return context

    def get_incoming_relationships(
        self, entity_id: str
    ) -> list[tuple[BaseRelationship, BaseEntity]]:
        """Retrieve all incoming relationships with source entity metadata.

        Args:
            entity_id: ID of the entity to retrieve incoming relationships for.

        Returns:
            List of (relationship, source_entity) tuples for all incoming edges.

        Raises:
            ValueError: If entity_id does not exist in the knowledge graph.
        """
        entity = self.kg.get_entity(entity_id)
        if entity is None:
            raise ValueError(f"Entity {entity_id} not found in knowledge graph")

        relationships = self.kg.get_relationships(entity_id, direction="in")
        result: list[tuple[BaseRelationship, BaseEntity]] = []

        for rel in relationships:
            source_entity = self.kg.get_entity(rel.source_id)
            if source_entity is None:
                logger.warning(
                    f"Relationship {rel.id} references non-existent source {rel.source_id}"
                )
                continue
            result.append((rel, source_entity))

        return result

    def get_outgoing_relationships(
        self, entity_id: str
    ) -> list[tuple[BaseRelationship, BaseEntity]]:
        """Retrieve all outgoing relationships with target entity metadata.

        Args:
            entity_id: ID of the entity to retrieve outgoing relationships for.

        Returns:
            List of (relationship, target_entity) tuples for all outgoing edges.

        Raises:
            ValueError: If entity_id does not exist in the knowledge graph.
        """
        entity = self.kg.get_entity(entity_id)
        if entity is None:
            raise ValueError(f"Entity {entity_id} not found in knowledge graph")

        relationships = self.kg.get_relationships(entity_id, direction="out")
        result: list[tuple[BaseRelationship, BaseEntity]] = []

        for rel in relationships:
            target_entity = self.kg.get_entity(rel.target_id)
            if target_entity is None:
                logger.warning(
                    f"Relationship {rel.id} references non-existent target {rel.target_id}"
                )
                continue
            result.append((rel, target_entity))

        return result

    def build_cross_entity_profile_base(self, entity_id: str) -> CrossEntityProfile:
        """Build a basic CrossEntityProfile for analysis and decision-making.

        Creates a lightweight profile suitable for statistical analysis and pattern
        detection, aggregating neighbor types, relationship patterns, and risk signals.

        Args:
            entity_id: ID of the entity to profile.

        Returns:
            CrossEntityProfile with neighbor counts, relationship patterns, and signals.

        Raises:
            ValueError: If entity_id does not exist in the knowledge graph.
        """
        entity = self.kg.get_entity(entity_id)
        if entity is None:
            raise ValueError(f"Entity {entity_id} not found in knowledge graph")

        # Count neighbors by type
        neighbors_by_type: dict[EntityType, int] = {}
        for target_type in EntityType:
            neighbors = self.kg.neighbors(
                entity_id, direction="both", entity_type=target_type
            )
            if neighbors:
                neighbors_by_type[target_type.value] = len(neighbors)

        # Count relationships by type
        relationships = self.kg.get_relationships(entity_id, direction="both")
        relationship_patterns: dict[str, int] = {}
        for rel in relationships:
            rel_type = rel.relationship_type
            relationship_patterns[rel_type] = relationship_patterns.get(rel_type, 0) + 1

        # Identify risk signals based on entity type and neighbors
        risk_signals: list[str] = []
        if neighbors_by_type.get("risk", 0) > 0:
            risk_signals.append("associated_with_risks")
        if neighbors_by_type.get("vulnerability", 0) > 0:
            risk_signals.append("has_vulnerabilities")
        if neighbors_by_type.get("incident", 0) > 0:
            risk_signals.append("involved_in_incidents")
        if neighbors_by_type.get("threat_actor", 0) > 0:
            risk_signals.append("targeted_by_threat_actors")

        # Infer properties based on neighbors
        inferred_properties: dict[str, bool] = {}
        inferred_properties["has_controls"] = neighbors_by_type.get("control", 0) > 0
        inferred_properties["regulated"] = neighbors_by_type.get("regulation", 0) > 0
        inferred_properties["multi_site"] = neighbors_by_type.get("site", 0) > 1
        inferred_properties["has_vendors"] = neighbors_by_type.get("vendor", 0) > 0
        inferred_properties["has_initiatives"] = (
            neighbors_by_type.get("initiative", 0) > 0
        )

        return CrossEntityProfile(
            entity_id=entity_id,
            entity_type=EntityType(entity.entity_type),
            neighbors_by_type={
                EntityType(k): v for k, v in neighbors_by_type.items()
            },
            relationship_patterns=relationship_patterns,
            inferred_properties=inferred_properties,
            risk_signals=risk_signals,
        )
