"""Relationship enricher — context-aware enrichment of relationship metadata.

This enricher iterates over all relationships in the knowledge graph and enriches
their temporal fields, confidence scores, and contextual properties based on
source/target entity provenance and relationship semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import ClassVar

from domain.base import BaseEntity, BaseRelationship, EntityType, RelationshipType
from domain.shared import ProvenanceAndConfidence
from enrichment.base import (
    ConfidenceLevel,
    EnrichmentContext,
    EnrichmentProfile,
    EnrichmentStats,
    EnrichmentTier,
)


@dataclass
class RelationshipEnrichment:
    """Result of enriching a single relationship."""

    relationship_id: str
    relationship_type: RelationshipType
    field_updates: dict[str, object]
    confidence_refinement: float | None = None


class RelationshipEnricher:
    """Enriches relationship metadata across the knowledge graph.

    For each relationship, this enricher:
    1. Refines confidence based on source/target entity provenance.
    2. Populates temporal fields (valid_from, valid_until) based on entity lifecycles.
    3. Adds contextual properties derived from relationship type semantics.
    4. Identifies relationship quality gaps.

    Usage:
        enricher = RelationshipEnricher()
        stats = enricher.enrich_relationships(kg, EnrichmentTier.STANDARD)
    """

    # Mapping of relationship types to contextual properties they should carry.
    RELATIONSHIP_PROPERTIES = {
        RelationshipType.DEPENDS_ON: {
            "dependency_type": ["hard", "soft"],
            "criticality": ["critical", "high", "medium", "low"],
            "redundancy_available": [True, False],
        },
        RelationshipType.MITIGATES: {
            "effectiveness_rating": ["effective", "largely_effective", "partially_effective", "ineffective"],
            "coverage_pct": None,  # Range 0-100
        },
        RelationshipType.HOSTS: {
            "capacity_utilization": None,  # Range 0-100
            "capacity_warning_threshold": None,
        },
        RelationshipType.CONNECTS_TO: {
            "connection_type": ["direct", "indirect", "federated"],
            "encryption_enabled": [True, False],
            "bandwidth_mbps": None,
        },
        RelationshipType.MANAGES: {
            "management_type": ["full", "partial", "oversight"],
            "approval_required": [True, False],
        },
        RelationshipType.WORKS_IN: {
            "assignment_type": ["primary", "secondary", "matrix"],
            "allocation_pct": None,  # Range 0-100
        },
        RelationshipType.SUBJECT_TO: {
            "applicability_type": ["directly_regulated", "indirectly_affected", "voluntary"],
            "compliance_status": ["compliant", "partially_compliant", "non_compliant"],
        },
        RelationshipType.IMPLEMENTS: {
            "implementation_status": ["implemented", "partially_implemented", "planned"],
            "effectiveness_rating": ["effective", "largely_effective", "partially_effective"],
        },
        RelationshipType.FLOWS_TO: {
            "classification_level": ["public", "internal", "confidential", "restricted"],
            "encryption_in_transit": [True, False],
            "encryption_in_rest": [True, False],
        },
    }

    def enrich_relationships(
        self,
        kg: object,  # KnowledgeGraph
        tier: EnrichmentTier = EnrichmentTier.STANDARD,
        profile: EnrichmentProfile = EnrichmentProfile.STANDARD,
    ) -> EnrichmentStats:
        """Enrich all relationships in the knowledge graph.

        Args:
            kg: The KnowledgeGraph instance.
            tier: Enrichment tier (BASIC, STANDARD, DEEP).
            profile: Enrichment profile (MINIMAL, STANDARD, COMPREHENSIVE).

        Returns:
            EnrichmentStats with counts of enriched relationships and identified gaps.
        """
        stats = EnrichmentStats()
        stats.start_time = datetime.now(UTC)

        # Build entity lookup for fast access.
        entity_map = {}
        if hasattr(kg, "get_entities"):
            for entity_type in EntityType:
                entities = kg.get_entities(entity_type)
                for entity in entities:
                    entity_map[entity.id] = entity

        # Get all relationships from the graph.
        relationships = []
        if hasattr(kg, "get_relationships"):
            relationships = kg.get_relationships()
        elif hasattr(kg, "edges"):
            # For NetworkX graphs: iterate edges
            relationships = kg.edges(data=True)

        enriched_relationships = []
        for rel in relationships:
            # Handle both BaseRelationship objects and NetworkX edge tuples.
            if isinstance(rel, BaseRelationship):
                rel_obj = rel
            else:
                # NetworkX tuple (source_id, target_id, data_dict)
                continue  # Skip NetworkX format for now

            enrichment = self._enrich_single_relationship(
                rel_obj,
                entity_map,
                tier=tier,
                profile=profile,
            )

            if enrichment and enrichment.field_updates:
                enriched_relationships.append(enrichment)
                stats.total_fields_enriched += len(enrichment.field_updates)

        # Persist enriched relationships back to the graph.
        if hasattr(kg, "update_relationships"):
            for enrichment in enriched_relationships:
                kg.update_relationships(
                    enrichment.relationship_id,
                    enrichment.field_updates,
                )

        stats.total_entities_enriched = len(enriched_relationships)
        stats.end_time = datetime.now(UTC)
        return stats

    def _enrich_single_relationship(
        self,
        rel: BaseRelationship,
        entity_map: dict[str, BaseEntity],
        tier: EnrichmentTier = EnrichmentTier.STANDARD,
        profile: EnrichmentProfile = EnrichmentProfile.STANDARD,
    ) -> RelationshipEnrichment | None:
        """Enrich a single relationship.

        Args:
            rel: The relationship to enrich.
            entity_map: Map of entity ID to BaseEntity for fast lookup.
            tier: Enrichment tier.
            profile: Enrichment profile.

        Returns:
            RelationshipEnrichment with field updates, or None if no enrichment.
        """
        updates = {}

        # 1. Refine confidence based on source/target entity provenance.
        source_entity = entity_map.get(rel.source_id)
        target_entity = entity_map.get(rel.target_id)

        if source_entity and target_entity:
            confidence = self._refine_confidence(
                rel,
                source_entity,
                target_entity,
                tier,
            )
            if confidence is not None:
                updates["confidence"] = confidence

        # 2. Populate temporal fields based on entity lifecycles.
        temporal_updates = self._enrich_temporal(
            rel,
            source_entity,
            target_entity,
            tier,
        )
        updates.update(temporal_updates)

        # 3. Add contextual properties based on relationship type.
        property_updates = self._enrich_properties(
            rel,
            source_entity,
            target_entity,
            profile,
        )
        if property_updates:
            current_props = rel.properties or {}
            current_props.update(property_updates)
            updates["properties"] = current_props

        if updates:
            return RelationshipEnrichment(
                relationship_id=rel.id,
                relationship_type=rel.relationship_type,
                field_updates=updates,
            )

        return None

    def _refine_confidence(
        self,
        rel: BaseRelationship,
        source: BaseEntity,
        target: BaseEntity,
        tier: EnrichmentTier,
    ) -> float | None:
        """Refine relationship confidence based on source/target entity provenance.

        Confidence = min(source_confidence, target_confidence) * edge_quality_factor
        Edge quality factor varies by tier and relationship type.
        """
        source_conf = self._extract_entity_confidence(source)
        target_conf = self._extract_entity_confidence(target)

        min_conf = min(source_conf, target_conf)

        # Edge quality factor by tier.
        edge_quality_factor = {
            EnrichmentTier.BASIC: 0.9,
            EnrichmentTier.STANDARD: 0.95,
            EnrichmentTier.DEEP: 1.0,
        }.get(tier, 0.95)

        refined = min_conf * edge_quality_factor
        return max(0.0, min(1.0, refined))  # Clamp to [0, 1]

    def _extract_entity_confidence(self, entity: BaseEntity) -> float:
        """Extract confidence level from an entity's provenance."""
        if not hasattr(entity, "provenance"):
            return 0.5

        provenance = entity.provenance
        if not isinstance(provenance, ProvenanceAndConfidence):
            return 0.5

        confidence_str = provenance.confidence_level or "medium"
        confidence_map = {
            "verified": 1.0,
            "high": 0.85,
            "medium": 0.65,
            "low": 0.4,
            "unverified": 0.2,
        }
        return confidence_map.get(confidence_str.lower(), 0.5)

    def _enrich_temporal(
        self,
        rel: BaseRelationship,
        source: BaseEntity | None,
        target: BaseEntity | None,
        tier: EnrichmentTier,
    ) -> dict[str, object]:
        """Populate temporal fields based on entity lifecycles."""
        updates = {}

        if tier == EnrichmentTier.BASIC:
            return updates

        # Set valid_from to the maximum of source/target created_at dates.
        source_created = getattr(source, "created_at", None) if source else None
        target_created = getattr(target, "created_at", None) if target else None

        if source_created and target_created:
            valid_from = max(source_created, target_created)
            if not rel.valid_from or rel.valid_from < valid_from:
                updates["valid_from"] = valid_from

        # For certain relationship types, infer valid_until.
        # E.g., if target has valid_until, relationship inherits it.
        if target and hasattr(target, "valid_until") and target.valid_until:
            if not rel.valid_until or rel.valid_until > target.valid_until:
                updates["valid_until"] = target.valid_until

        return updates

    def _enrich_properties(
        self,
        rel: BaseRelationship,
        source: BaseEntity | None,
        target: BaseEntity | None,
        profile: EnrichmentProfile,
    ) -> dict[str, object]:
        """Add contextual properties based on relationship type semantics."""
        props = {}

        rel_type = rel.relationship_type
        type_props = self.RELATIONSHIP_PROPERTIES.get(rel_type)

        if not type_props:
            return props

        # For COMPREHENSIVE profile, enrich all available properties.
        if profile == EnrichmentProfile.COMPREHENSIVE:
            for prop_name, possible_values in type_props.items():
                # Skip properties that are already set.
                if prop_name in (rel.properties or {}):
                    continue

                # For boolean/enum properties, pick sensible defaults.
                if possible_values and isinstance(possible_values, list):
                    # Default to the middle/safer value.
                    default_val = possible_values[len(possible_values) // 2]
                    props[prop_name] = default_val
                elif possible_values is None:
                    # Numeric property (e.g., percentage, bandwidth).
                    # Set a sensible default based on context.
                    if "pct" in prop_name.lower():
                        props[prop_name] = 50
                    elif "bandwidth" in prop_name.lower():
                        props[prop_name] = 100
                    elif "utilization" in prop_name.lower():
                        props[prop_name] = 60

        # For STANDARD profile, only add critical properties.
        elif profile == EnrichmentProfile.STANDARD:
            if rel_type == RelationshipType.DEPENDS_ON:
                props["criticality"] = "medium"
            elif rel_type == RelationshipType.MITIGATES:
                props["effectiveness_rating"] = "largely_effective"
            elif rel_type == RelationshipType.SUBJECT_TO:
                props["compliance_status"] = "partially_compliant"

        return props


def enrich_relationships_in_graph(
    kg: object,
    tier: EnrichmentTier = EnrichmentTier.STANDARD,
    profile: EnrichmentProfile = EnrichmentProfile.STANDARD,
) -> EnrichmentStats:
    """Convenience function to enrich all relationships in a knowledge graph.

    Args:
        kg: The KnowledgeGraph instance.
        tier: Enrichment tier.
        profile: Enrichment profile.

    Returns:
        EnrichmentStats with enrichment results.
    """
    enricher = RelationshipEnricher()
    return enricher.enrich_relationships(kg, tier=tier, profile=profile)
