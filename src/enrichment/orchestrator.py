"""EnrichmentOrchestrator: coordinates the full enrichment agency pipeline.

The EnrichmentOrchestrator follows the same design pattern as SyntheticOrchestrator,
but for enrichment instead of generation. It:

1. Loads or works with a KnowledgeGraph
2. Creates an EnrichmentContext with GraphContextEngine and ProvenanceReconciler
3. For each tier (2-5), enriches all entities in generation order
4. Applies enrichment results and tracks provenance
5. Runs relationship and coherence enrichers post-entity enrichment
6. Assesses quality and returns aggregate stats
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import TYPE_CHECKING

# UTC timezone (Python 3.11+) or fallback for compatibility
try:
    from datetime import UTC
except ImportError:
    UTC = UTC

from domain.base import EntityType
from enrichment.base import (
    AdversarialValidator,
    EnricherRegistry,
    EnrichmentResult,
    EnrichmentStats,
    EnrichmentTier,
)
from enrichment.coherence_rules import CoherenceSeverity, validate_all_rules
from enrichment.graph_context import GraphContextEngine
from enrichment.provenance_reconciler import ProvenanceReconciler
from synthetic.orchestrator import GENERATION_ORDER

if TYPE_CHECKING:
    from graph.knowledge_graph import KnowledgeGraph

logger = logging.getLogger(__name__)

# Mapping of tier levels to EnrichmentTier enums
TIER_LEVEL_MAP = {
    1: EnrichmentTier.BASIC,
    2: EnrichmentTier.BASIC,
    3: EnrichmentTier.STANDARD,
    4: EnrichmentTier.DEEP,
    5: EnrichmentTier.DEEP,
}

# Default tier fields per entity type for completeness assessment
# Maps EntityType -> list of expected fields at full enrichment
TIER_FIELDS: dict[EntityType, list[str]] = {
    EntityType.PERSON: [
        "name",
        "email",
        "phone",
        "employee_id",
        "department_id",
        "role_id",
        "manager_id",
        "title",
        "description",
    ],
    EntityType.DEPARTMENT: [
        "name",
        "description",
        "parent_id",
        "budget",
        "head_count",
        "location",
    ],
    EntityType.ROLE: [
        "name",
        "description",
        "level",
        "responsibilities",
        "required_skills",
    ],
    EntityType.SYSTEM: [
        "name",
        "description",
        "status",
        "owner_id",
        "criticality",
        "classification",
        "encryption_enabled",
    ],
    EntityType.NETWORK: [
        "name",
        "description",
        "network_range",
        "location_id",
        "status",
    ],
    EntityType.DATA_ASSET: [
        "name",
        "description",
        "owner_id",
        "classification",
        "encryption_status",
        "residency_requirement",
    ],
    EntityType.POLICY: [
        "name",
        "description",
        "policy_type",
        "effective_date",
        "status",
        "owner_id",
    ],
    EntityType.VENDOR: [
        "name",
        "description",
        "vendor_type",
        "status",
        "location",
        "contact_email",
    ],
    EntityType.LOCATION: [
        "name",
        "description",
        "latitude",
        "longitude",
        "address",
        "country",
    ],
    EntityType.VULNERABILITY: [
        "name",
        "description",
        "severity",
        "cvss_score",
        "affected_system_id",
        "remediation",
    ],
    EntityType.THREAT_ACTOR: [
        "name",
        "description",
        "threat_level",
        "known_targets",
        "motivation",
    ],
    EntityType.INCIDENT: [
        "name",
        "description",
        "severity",
        "start_date",
        "end_date",
        "status",
        "root_cause",
    ],
    EntityType.REGULATION: [
        "name",
        "description",
        "jurisdiction_id",
        "effective_date",
        "status",
    ],
    EntityType.CONTROL: [
        "name",
        "description",
        "control_type",
        "status",
        "owner_id",
        "implementation_status",
    ],
    EntityType.RISK: [
        "name",
        "description",
        "risk_level",
        "probability",
        "impact",
        "owner_id",
        "mitigation_strategy",
    ],
    EntityType.THREAT: [
        "name",
        "description",
        "threat_type",
        "threat_level",
        "affected_assets",
    ],
    EntityType.INTEGRATION: [
        "name",
        "description",
        "source_system_id",
        "target_system_id",
        "integration_type",
        "status",
    ],
    EntityType.DATA_DOMAIN: [
        "name",
        "description",
        "owner_id",
        "data_assets",
        "criticality",
    ],
    EntityType.DATA_FLOW: [
        "name",
        "description",
        "source_id",
        "target_id",
        "data_type",
        "frequency",
    ],
    EntityType.ORGANIZATIONAL_UNIT: [
        "name",
        "description",
        "parent_id",
        "head_count",
        "location_id",
    ],
    EntityType.BUSINESS_CAPABILITY: [
        "name",
        "description",
        "owner_id",
        "maturity_level",
        "business_outcomes",
    ],
    EntityType.SITE: [
        "name",
        "description",
        "location_id",
        "site_type",
        "capacity",
        "security_level",
    ],
    EntityType.GEOGRAPHY: [
        "name",
        "description",
        "region",
        "parent_id",
        "regulatory_requirements",
    ],
    EntityType.JURISDICTION: [
        "name",
        "description",
        "geography_id",
        "legal_framework",
        "data_protection_level",
    ],
    EntityType.PRODUCT_PORTFOLIO: [
        "name",
        "description",
        "owner_id",
        "product_count",
        "market_value",
    ],
    EntityType.PRODUCT: [
        "name",
        "description",
        "product_portfolio_id",
        "status",
        "launch_date",
        "target_market_id",
    ],
    EntityType.MARKET_SEGMENT: [
        "name",
        "description",
        "geography_id",
        "customer_count",
        "market_size",
    ],
    EntityType.CUSTOMER: [
        "name",
        "description",
        "customer_type",
        "location_id",
        "relationship_status",
        "contact_email",
    ],
    EntityType.CONTRACT: [
        "name",
        "description",
        "vendor_id",
        "customer_id",
        "start_date",
        "end_date",
        "value",
        "status",
    ],
    EntityType.INITIATIVE: [
        "name",
        "description",
        "owner_id",
        "status",
        "start_date",
        "end_date",
        "budget",
        "objectives",
    ],
}

# Tier names for logging
TIER_NAMES = {
    1: "Tier 1 (Baseline)",
    2: "Tier 2 (Basic)",
    3: "Tier 3 (Standard)",
    4: "Tier 4 (Deep)",
    5: "Tier 5 (Comprehensive)",
}


class EnrichmentOrchestrator:
    """Coordinates the full enrichment agency pipeline.

    The orchestrator:
    1. Loads the KnowledgeGraph
    2. Creates an EnrichmentContext with GraphContextEngine and ProvenanceReconciler
    3. For each entity type in GENERATION_ORDER, retrieves all entities and enriches them
    4. Applies enrichment results, records provenance, and persists updates
    5. Runs relationship and coherence enrichers post-entity enrichment
    6. Performs quality assessment
    7. Returns aggregate EnrichmentStats

    Usage:
        kg = KnowledgeGraph()
        # ... load graph ...
        orchestrator = EnrichmentOrchestrator(kg, profile="tech", seed=42)
        stats = orchestrator.enrich_to_tier(3)
        print(f"Enriched {stats.total_entities_enriched} entities")

    Attributes:
        knowledge_graph: The KnowledgeGraph instance to enrich.
        profile: Profile name (e.g., "tech", "financial", "healthcare").
        seed: Random seed for reproducible enrichment.
        osint_enabled: Whether to enable OSINT research (default False).
    """

    def __init__(
        self,
        knowledge_graph: KnowledgeGraph,
        profile: str = "tech",
        seed: int | None = None,
        osint_enabled: bool = False,
        pipeline: str = "legacy",
    ) -> None:
        """Initialize the EnrichmentOrchestrator.

        Args:
            knowledge_graph: KnowledgeGraph instance to enrich.
            profile: Profile name for enrichment strategy.
            seed: Random seed for reproducibility.
            osint_enabled: Enable OSINT research if available.
            pipeline: Pipeline backend — "legacy" or "karma" (see ADR-014).
        """
        self._kg = knowledge_graph
        self._profile_name = profile
        self._seed = seed
        self._osint_enabled = osint_enabled
        self._pipeline = pipeline
        self._graph_context = GraphContextEngine(knowledge_graph)
        self._provenance_reconciler = ProvenanceReconciler(knowledge_graph)
        self._adversarial_validator = AdversarialValidator()
        self._osint_agent = None  # Optional, would be loaded if osint_enabled=True

    def enrich_to_tier(self, tier_level: int) -> EnrichmentStats:
        """Enrich all entities to the specified tier level.

        Delegates to the KARMA pipeline if pipeline="karma", otherwise
        uses the legacy orchestrator loop.

        Args:
            tier_level: Target tier level (1-5).

        Returns:
            EnrichmentStats with aggregate enrichment results.

        Raises:
            ValueError: If tier_level is not 1-5.
        """
        if not 1 <= tier_level <= 5:
            raise ValueError(f"Tier level must be 1-5, got {tier_level}")

        # KARMA pipeline delegation (ADR-014)
        if self._pipeline == "karma":
            from enrichment.karma.controller import ControllerAgent

            controller = ControllerAgent(
                knowledge_graph=self._kg,
                graph_context_engine=self._graph_context,
                provenance_reconciler=self._provenance_reconciler,
                osint_agent=self._osint_agent,
            )
            return controller.run_pipeline(tier_level)

        overall_stats = EnrichmentStats()
        datetime.now(UTC)

        logger.info(f"Starting enrichment to {TIER_NAMES.get(tier_level, f'Tier {tier_level}')}")

        # Enrich progressively from tier 2 up to target tier
        for current_tier in range(2, tier_level + 1):
            tier_stats = self._enrich_tier(current_tier)
            overall_stats.total_entities_enriched += tier_stats.total_entities_enriched
            overall_stats.total_fields_enriched += tier_stats.total_fields_enriched
            overall_stats.total_relationships_suggested += tier_stats.total_relationships_suggested
            overall_stats.total_gaps_identified += tier_stats.total_gaps_identified
            overall_stats.total_fields_attempted += tier_stats.total_fields_attempted
            overall_stats.total_validation_failures += tier_stats.total_validation_failures
            overall_stats.validation_failures.extend(tier_stats.validation_failures)
            overall_stats.actions.extend(tier_stats.actions)

        overall_stats.end_time = datetime.now(UTC)
        rejection_rate = overall_stats.rejection_rate()
        logger.info(
            f"Enrichment complete. Enriched {overall_stats.total_entities_enriched} "
            f"entities, {overall_stats.total_fields_enriched} fields in "
            f"{overall_stats.duration_seconds():.2f}s. "
            f"Adversarial rejections: {overall_stats.total_validation_failures} "
            f"({rejection_rate:.1%} of {overall_stats.total_fields_attempted} attempted)"
        )

        return overall_stats

    def enrich_all_tiers(self) -> dict[int, EnrichmentStats]:
        """Progressively enrich from Tier 2 through Tier 5.

        Returns:
            Dictionary mapping tier level (2-5) to EnrichmentStats for that tier.
        """
        results: dict[int, EnrichmentStats] = {}

        logger.info("Starting full enrichment pipeline (Tiers 2-5)")

        for tier_level in range(2, 6):
            logger.info(f"Enriching to {TIER_NAMES.get(tier_level, f'Tier {tier_level}')}")
            stats = self._enrich_tier(tier_level)
            results[tier_level] = stats

        logger.info("Full enrichment pipeline complete")
        return results

    def _enrich_tier(self, tier_level: int) -> EnrichmentStats:
        """Enrich all entities to a specific tier level.

        Args:
            tier_level: Tier level to enrich to.

        Returns:
            EnrichmentStats for this tier's enrichment.
        """
        tier_stats = EnrichmentStats()
        tier_enum = TIER_LEVEL_MAP.get(tier_level, EnrichmentTier.BASIC)
        profile_enum = self._profile_name  # Set at construction time via CLI or API

        # Get expected tier fields
        self._get_tier_fields(tier_level)

        logger.info(
            f"Enriching entities to {TIER_NAMES.get(tier_level, f'Tier {tier_level}')} "
            f"({tier_enum.value})"
        )

        # Phase 1: Enrich entities in generation order
        for entity_type, _ in GENERATION_ORDER:
            if not EnricherRegistry.is_registered(entity_type):
                continue

            entities = self._kg.list_entities(entity_type)
            if not entities:
                continue

            logger.debug(f"Enriching {len(entities)} {entity_type.value} entities")

            enricher_class = EnricherRegistry.get(entity_type)
            enricher = enricher_class()
            entity_type_start = time.time()

            for entity in entities:
                try:
                    # Get entity context from graph
                    context = self._graph_context.get_entity_context(entity.id)

                    # Optional: run OSINT research
                    osint = None
                    if self._osint_enabled and self._osint_agent:
                        osint = self._osint_agent.research(entity)

                    # Run enricher
                    result = enricher.enrich(
                        entity,
                        context,
                        osint=osint,
                        tier=tier_enum,
                        profile=profile_enum,
                    )

                    # --- ADVERSARIAL VALIDATION GATE ---
                    # Every enrichment result passes through the validator
                    # BEFORE being applied. Rejected fields never reach the graph.
                    if result.has_updates():
                        fields_attempted = len(result.field_updates)
                        tier_stats.total_fields_attempted += fields_attempted

                        validated_result, failures = self._adversarial_validator.validate(
                            entity, result
                        )

                        # Track rejections
                        if failures:
                            tier_stats.total_validation_failures += len(failures)
                            tier_stats.validation_failures.extend(failures)

                        # Apply ONLY validated result
                        if validated_result.has_updates():
                            self._apply_enrichment_result(entity.id, validated_result)
                            tier_stats.total_entities_enriched += 1
                            tier_stats.total_fields_enriched += len(validated_result.field_updates)
                            tier_stats.total_relationships_suggested += len(
                                validated_result.relationship_suggestions
                            )
                            tier_stats.total_gaps_identified += len(validated_result.known_gaps)
                            tier_stats.actions.extend(validated_result.actions)

                except Exception as e:
                    logger.error(
                        f"Error enriching {entity_type.value} {entity.id}: {e}",
                        exc_info=True,
                    )
                    continue

            entity_type_duration = time.time() - entity_type_start
            logger.debug(
                f"Enriched {entity_type.value} in {entity_type_duration:.2f}s "
                f"({len(entities)} entities)"
            )

        # Phase 2: Relationship enricher (if registered)
        if EnricherRegistry.is_registered("relationship"):
            logger.debug("Running relationship enricher")
            try:
                rel_enricher_class = EnricherRegistry.get("relationship")
                rel_enricher_class()
                # Relationship enricher operates on the full graph, not per-entity
                rels = self._kg.list_relationships(limit=500)
                for rel in rels:
                    try:
                        source = self._kg.get_entity(rel.source_id)
                        target = self._kg.get_entity(rel.target_id)
                        if source and target:
                            # Recalculate relationship confidence based on entity confidences
                            new_confidence = (
                                self._provenance_reconciler.recalculate_relationship_confidence(
                                    source, target
                                )
                            )
                            # Only update if confidence has changed
                            if abs(new_confidence - (rel.confidence or 0.75)) > 0.05:
                                self._kg.engine.update_relationship(
                                    rel.id, confidence=new_confidence
                                )
                    except Exception as e:
                        logger.debug(f"Relationship confidence update skipped for {rel.id}: {e}")
            except (KeyError, Exception) as e:
                logger.error(f"Error running relationship enricher: {e}", exc_info=True)

        # Phase 3: Cross-entity coherence validation
        # This uses the REAL coherence_rules.py — not a stub.
        logger.debug("Running cross-entity coherence validation")
        try:
            violations = validate_all_rules(self._kg)
            if violations:
                error_count = sum(1 for v in violations if v.severity == CoherenceSeverity.ERROR)
                warn_count = sum(1 for v in violations if v.severity == CoherenceSeverity.WARNING)
                logger.info(
                    f"Coherence validation: {len(violations)} violations "
                    f"({error_count} errors, {warn_count} warnings)"
                )
                for violation in violations[:10]:  # Log first 10
                    logger.debug(
                        f"  [{violation.severity.value}] {violation.rule_id}: "
                        f"{violation.description}"
                    )
        except Exception as e:
            logger.error(f"Error running coherence validation: {e}", exc_info=True)

        tier_stats.end_time = datetime.now(UTC)
        return tier_stats

    def _apply_enrichment_result(self, entity_id: str, result: EnrichmentResult) -> None:
        """Apply field updates and provenance to an entity.

        Args:
            entity_id: ID of the entity to update.
            result: EnrichmentResult containing updates.
        """
        # Get the entity to update provenance field name
        entity = self._kg.get_entity(entity_id)
        if not entity:
            logger.warning(f"Entity {entity_id} not found in knowledge graph")
            return

        # Apply field updates
        if result.field_updates:
            try:
                self._kg.update_entity(entity_id, **result.field_updates)
            except Exception as e:
                logger.error(
                    f"Error updating entity {entity_id} with fields {result.field_updates}: {e}"
                )

        # Record and apply provenance
        if result.actions:
            for action in result.actions:
                provenance = self._provenance_reconciler.record_enrichment(
                    entity_id,
                    result.entity_type,
                    action.fields_enriched,
                    action.source,
                    action.methodology,
                    action.confidence,
                )

                # Update provenance field on entity
                provenance_field = self._provenance_reconciler.get_provenance_field_name(
                    result.entity_type
                )
                try:
                    self._kg.update_entity(entity_id, **{provenance_field: provenance})
                except Exception as e:
                    logger.error(f"Error updating provenance for {entity_id}: {e}", exc_info=True)

    def _get_tier_fields(self, tier_level: int) -> dict[EntityType, list[str]]:
        """Get expected fields for a tier level.

        Args:
            tier_level: Tier level (1-5).

        Returns:
            Dictionary mapping EntityType to list of expected field names.
        """
        # Could vary fields by tier, for now returns consistent set
        # Tiers 1-2 might have subset, tiers 3-5 have full set
        if tier_level <= 1:
            return {}
        elif tier_level <= 2:
            # Tier 2: basic fields only
            return {k: v[:4] if len(v) > 4 else v for k, v in TIER_FIELDS.items()}
        else:
            # Tier 3+: full field set
            return TIER_FIELDS

    @property
    def knowledge_graph(self) -> KnowledgeGraph:
        """Return the knowledge graph instance."""
        return self._kg

    @property
    def context_engine(self) -> GraphContextEngine:
        """Return the graph context engine."""
        return self._graph_context

    @property
    def provenance_reconciler(self) -> ProvenanceReconciler:
        """Return the provenance reconciler."""
        return self._provenance_reconciler

    @property
    def adversarial_validator(self) -> AdversarialValidator:
        """Return the adversarial validator."""
        return self._adversarial_validator
