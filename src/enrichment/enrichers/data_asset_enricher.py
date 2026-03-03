"""Data Asset enricher — enriches DataAsset entities with context-aware data architecture profiles.

The DataAsset entity (~85 attributes) is enriched by analyzing its graph neighborhood:
- Systems (via STORES) → storage_technology, hosting_environment
- DataDomains (via BELONGS_TO/CLASSIFIED_AS) → classification, sensitivity
- DataFlows (via FLOWS_TO/ORIGINATES_FROM) → lineage, consumers
- Policies (via GOVERNS) → retention, privacy requirements

Tiers:
  2 (Managed): data_classification, storage_technology, retention_policy, data_owner, sensitivity_level
  3 (Defined): quality_dimensions (completeness, accuracy, timeliness), lineage, catalog_status, consent
  4 (Measured): storage_cost, processing_cost, privacy_impact_assessment, breach_notification
  5 (Optimized): ai_training_usage, monetization_potential, golden_record_status, fitness_for_purpose
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar

from domain.base import BaseEntity, EntityType, RelationshipType
from domain.shared import DataGap, ProvenanceAndConfidence
from enrichment.base import (
    AbstractEnricher,
    ConfidenceLevel,
    EnricherRegistry,
    EnrichmentAction,
    EnrichmentContext,
    EnrichmentProfile,
    EnrichmentResult,
    EnrichmentTier,
    EntityContext,
    OSINTResults,
)

# Classification levels and associated handling requirements
CLASSIFICATION_LEVELS = [
    {"level": "Public", "encryption_required": False, "access_control": "Minimal"},
    {"level": "Internal", "encryption_required": True, "access_control": "Moderate"},
    {"level": "Confidential", "encryption_required": True, "access_control": "Strict"},
    {"level": "Restricted", "encryption_required": True, "access_control": "Very Strict"},
]

# Storage technology profiles
STORAGE_TECHNOLOGIES = [
    {
        "name": "PostgreSQL",
        "type": "Relational DBMS",
        "hosting": "On-Premise",
        "encryption_capable": True,
        "backup_capable": True,
    },
    {
        "name": "Snowflake",
        "type": "Cloud Data Warehouse",
        "hosting": "Cloud-Native",
        "encryption_capable": True,
        "backup_capable": True,
    },
    {
        "name": "Amazon S3",
        "type": "Object Storage",
        "hosting": "Cloud-Native",
        "encryption_capable": True,
        "backup_capable": True,
    },
    {
        "name": "MongoDB",
        "type": "NoSQL Document Store",
        "hosting": "On-Premise/Cloud",
        "encryption_capable": True,
        "backup_capable": True,
    },
    {
        "name": "Apache Kafka",
        "type": "Event Streaming",
        "hosting": "On-Premise/Cloud",
        "encryption_capable": True,
        "backup_capable": False,
    },
]

# Data quality dimension templates
QUALITY_DIMENSION_TEMPLATES = {
    "completeness": {"target": 98.5, "scoring_method": "Row count vs expected"},
    "accuracy": {"target": 99.0, "scoring_method": "Validation rule pass rate"},
    "timeliness": {"target": 99.5, "scoring_method": "Freshness vs SLA"},
}

# Retention policy templates
RETENTION_POLICIES = {
    "transactional": {"minimum": "7 days", "maximum": "7 years", "basis": "Legal requirement"},
    "analytical": {"minimum": "30 days", "maximum": "5 years", "basis": "Business requirement"},
    "archival": {"minimum": "1 year", "maximum": "10 years", "basis": "Compliance/Legal hold"},
    "ephemeral": {"minimum": "1 day", "maximum": "30 days", "basis": "Operational"},
}


@EnricherRegistry.register
class DataAssetEnricher(AbstractEnricher):
    """Enricher for DataAsset entities.

    Context-aware enrichment that reads graph neighbors (Systems, DataDomains,
    DataFlows, Policies) to populate data architecture, quality, lineage,
    and strategic value fields.
    """

    ENRICHES: ClassVar[EntityType] = EntityType.DATA_ASSET

    def enrich(
        self,
        entity: BaseEntity,
        context: EntityContext,
        osint: OSINTResults | None = None,
        tier: EnrichmentTier = EnrichmentTier.BASIC,
        profile: EnrichmentProfile = EnrichmentProfile.STANDARD,
        enrichment_context: EnrichmentContext | None = None,
    ) -> EnrichmentResult:
        """Enrich a DataAsset entity based on graph context.

        Args:
            entity: The DataAsset entity to enrich.
            context: EntityContext with DataAsset's neighbors by relationship type.
            osint: Optional external research results.
            tier: Enrichment tier (BASIC, STANDARD, DEEP).
            profile: Enrichment profile (MINIMAL, STANDARD, COMPREHENSIVE).
            enrichment_context: Shared enrichment context.

        Returns:
            EnrichmentResult with field updates, provenance, relationships, gaps.
        """
        result = EnrichmentResult(
            entity_id=entity.id,
            entity_type=EntityType.DATA_ASSET,
        )

        # Determine which tiers to populate based on profile
        tiers_to_populate = self._get_tiers_for_profile(profile)

        # Build cross-entity profile from graph context
        cross_profile = self._build_asset_profile(entity, context)

        # Tier 2: Managed — core operational fields
        if 2 in tiers_to_populate:
            updates_t2, actions_t2 = self._populate_tier_2(entity, context, cross_profile)
            result.field_updates.update(updates_t2)
            result.actions.extend(actions_t2)

        # Tier 3: Defined — cross-entity coherence
        if 3 in tiers_to_populate:
            updates_t3, actions_t3 = self._populate_tier_3(entity, context, cross_profile)
            result.field_updates.update(updates_t3)
            result.actions.extend(actions_t3)

        # Tier 4: Measured — quantitative metrics
        if 4 in tiers_to_populate:
            updates_t4, actions_t4 = self._populate_tier_4(entity, context, cross_profile)
            result.field_updates.update(updates_t4)
            result.actions.extend(actions_t4)

        # Tier 5: Optimized — full fidelity & predictive
        if 5 in tiers_to_populate:
            updates_t5, actions_t5 = self._populate_tier_5(entity, context, cross_profile)
            result.field_updates.update(updates_t5)
            result.actions.extend(actions_t5)

        # Identify data gaps
        result.known_gaps = self._identify_gaps(entity, cross_profile)

        # Update provenance
        result.provenance_update = self._build_provenance(
            result.actions,
            tier,
            profile,
        )

        return result

    def _get_tiers_for_profile(self, profile: EnrichmentProfile) -> set[int]:
        """Determine which tiers to populate based on profile."""
        if profile == EnrichmentProfile.MINIMAL:
            return {2}
        elif profile == EnrichmentProfile.STANDARD:
            return {2, 3, 4}
        else:  # COMPREHENSIVE
            return {2, 3, 4, 5}

    def _build_asset_profile(self, entity: BaseEntity, context: EntityContext) -> dict:
        """Build holistic profile from graph neighborhood."""
        systems = context.get_neighbors(RelationshipType.STORES)
        domains = context.get_neighbors(RelationshipType.CLASSIFIED_AS)
        inbound_flows = context.get_neighbors(RelationshipType.ORIGINATES_FROM)
        outbound_flows = context.get_neighbors(RelationshipType.FLOWS_TO)
        policies = context.get_neighbors(RelationshipType.GOVERNS)

        # Infer criticality from domain count and outbound flows
        is_critical = len(domains) > 0 and len(outbound_flows) > 2

        profile = {
            "asset_id": entity.id,
            "asset_name": getattr(entity, "name", ""),
            "asset_type": getattr(entity, "asset_type", ""),
            "systems_count": len(systems),
            "domains_count": len(domains),
            "inbound_flows_count": len(inbound_flows),
            "outbound_flows_count": len(outbound_flows),
            "policies_count": len(policies),
            "is_critical": is_critical,
            "is_shared": len(outbound_flows) > 1,
        }
        return profile

    def _populate_tier_2(
        self, entity: BaseEntity, context: EntityContext, cross_profile: dict
    ) -> tuple[dict, list]:
        """Populate Tier 2 (Managed) fields: core operational."""
        updates = {}
        actions = []

        # Data classification from domain neighbors or default to Internal
        domains = context.get_neighbors(RelationshipType.CLASSIFIED_AS)
        classification = "Internal"  # default
        if domains:
            domain_classification = getattr(domains[0], "data_classification", "Internal")
            if domain_classification:
                classification = domain_classification

        updates["classification"] = classification
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.DATA_ASSET,
                fields_enriched=["classification"],
                source="Domain context analysis",
                methodology=f"Inherited from {len(domains)} related DataDomains"
                if domains
                else "Default policy",
                confidence=ConfidenceLevel.HIGH if domains else ConfidenceLevel.MEDIUM,
            )
        )

        # Storage technology from Systems
        systems = context.get_neighbors(RelationshipType.STORES)
        storage_tech = STORAGE_TECHNOLOGIES[0]  # default PostgreSQL
        if systems:
            system_type = getattr(systems[0], "system_type", "").lower()
            # Match based on system type
            if "warehouse" in system_type:
                storage_tech = STORAGE_TECHNOLOGIES[1]  # Snowflake
            elif "kafka" in system_type:
                storage_tech = STORAGE_TECHNOLOGIES[4]  # Kafka
            elif "cloud" in system_type:
                storage_tech = STORAGE_TECHNOLOGIES[2]  # S3

        updates["storage_technology"] = storage_tech
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.DATA_ASSET,
                fields_enriched=["storage_technology"],
                source="System topology analysis",
                methodology=f"Selected from {len(systems)} storing systems",
                confidence=ConfidenceLevel.HIGH if systems else ConfidenceLevel.MEDIUM,
            )
        )

        # Retention policy
        asset_type = getattr(entity, "asset_type", "").lower()
        retention_key = "transactional"
        if "analytical" in asset_type:
            retention_key = "analytical"
        elif "archive" in asset_type:
            retention_key = "archival"

        retention_policy = RETENTION_POLICIES.get(
            retention_key, RETENTION_POLICIES["transactional"]
        )
        updates["retention_policy"] = retention_policy
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.DATA_ASSET,
                fields_enriched=["retention_policy"],
                source="Template Registry",
                methodology="Coordinated template dicts (asset_type match)",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Data owner from domain owner
        domains = context.get_neighbors(RelationshipType.CLASSIFIED_AS)
        data_owner = getattr(domains[0], "domain_owner", "") if domains else ""
        if data_owner:
            updates["data_owner"] = data_owner
            actions.append(
                EnrichmentAction(
                    entity_id=entity.id,
                    entity_type=EntityType.DATA_ASSET,
                    fields_enriched=["data_owner"],
                    source="Domain ownership inheritance",
                    methodology="Inherited from domain_owner via CLASSIFIED_AS",
                    confidence=ConfidenceLevel.HIGH,
                )
            )

        # Sensitivity level from classification
        sensitivity_map = {
            "Public": "Low",
            "Internal": "Medium",
            "Confidential": "High",
            "Restricted": "Critical",
        }
        sensitivity = sensitivity_map.get(classification, "Medium")
        updates["sensitivity_level"] = sensitivity
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.DATA_ASSET,
                fields_enriched=["sensitivity_level"],
                source="Classification mapping",
                methodology="Derived from data_classification field",
                confidence=ConfidenceLevel.HIGH,
            )
        )

        return updates, actions

    def _populate_tier_3(
        self, entity: BaseEntity, context: EntityContext, cross_profile: dict
    ) -> tuple[dict, list]:
        """Populate Tier 3 (Defined) fields: cross-entity coherence."""
        updates = {}
        actions = []

        # Quality dimensions (completeness, accuracy, timeliness)
        quality_dims = {}
        for dimension_name, template in QUALITY_DIMENSION_TEMPLATES.items():
            quality_dims[dimension_name] = {
                "target": template["target"],
                "current": template["target"] - 1.5,  # Slightly below target
                "scoring_method": template["scoring_method"],
            }

        updates["quality_dimensions"] = quality_dims
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.DATA_ASSET,
                fields_enriched=["quality_dimensions"],
                source="Quality baseline templates",
                methodology="Coordinated quality metric templates",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Lineage upstream (source flows)
        inbound_flows = context.get_neighbors(RelationshipType.ORIGINATES_FROM)
        lineage_upstream = [
            {"flow_id": flow.id, "flow_name": getattr(flow, "name", "")}
            for flow in inbound_flows[:5]
        ]
        updates["lineage_upstream"] = lineage_upstream
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.DATA_ASSET,
                fields_enriched=["lineage_upstream"],
                source="DataFlow topology analysis",
                methodology=f"Identified {len(inbound_flows)} upstream flows via ORIGINATES_FROM",
                confidence=ConfidenceLevel.HIGH,
            )
        )

        # Lineage downstream (consumer flows)
        outbound_flows = context.get_neighbors(RelationshipType.FLOWS_TO)
        lineage_downstream = [
            {"flow_id": flow.id, "flow_name": getattr(flow, "name", "")}
            for flow in outbound_flows[:5]
        ]
        updates["lineage_downstream"] = lineage_downstream
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.DATA_ASSET,
                fields_enriched=["lineage_downstream"],
                source="DataFlow topology analysis",
                methodology=f"Identified {len(outbound_flows)} downstream flows via FLOWS_TO",
                confidence=ConfidenceLevel.HIGH,
            )
        )

        # Catalog status
        catalog_status = (
            "Cataloged - Complete" if cross_profile.get("domains_count", 0) > 0 else "Uncataloged"
        )
        updates["catalog_status"] = catalog_status
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.DATA_ASSET,
                fields_enriched=["catalog_status"],
                source="Domain membership analysis",
                methodology=f"Based on {cross_profile.get('domains_count', 0)} domain memberships",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Consent management requirements
        domains = context.get_neighbors(RelationshipType.CLASSIFIED_AS)
        has_pii = False
        if domains:
            sensitivity_flags = getattr(domains[0], "sensitivity_flags", None)
            if sensitivity_flags:
                has_pii = getattr(sensitivity_flags, "pii_flag", False)

        consent_management = {
            "requires_consent": has_pii,
            "consent_mechanism": "Opt-in" if has_pii else "Not required",
            "consent_tracking": "Enabled" if has_pii else "Disabled",
        }
        updates["consent_management"] = consent_management
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.DATA_ASSET,
                fields_enriched=["consent_management"],
                source="Domain sensitivity analysis",
                methodology=f"Inferred from PII flags in {len(domains)} related domains",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        return updates, actions

    def _populate_tier_4(
        self, entity: BaseEntity, context: EntityContext, cross_profile: dict
    ) -> tuple[dict, list]:
        """Populate Tier 4 (Measured) fields: quantitative metrics."""
        updates = {}
        actions = []

        # Storage cost estimation
        systems = context.get_neighbors(RelationshipType.STORES)
        storage_count = len(systems)
        storage_cost = 5000.0 * storage_count + 2000.0  # $5k per system + base
        updates["storage_cost"] = {
            "amount": storage_cost,
            "currency": "USD",
            "annual": True,
            "cost_drivers": f"{storage_count} storage systems",
        }
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.DATA_ASSET,
                fields_enriched=["storage_cost"],
                source="Cost estimation model",
                methodology=f"Derived from {storage_count} storage systems at $5k/yr base",
                confidence=ConfidenceLevel.LOW,
            )
        )

        # Processing cost estimation
        outbound_flows = context.get_neighbors(RelationshipType.FLOWS_TO)
        processing_cost = 2000.0 * len(outbound_flows) + 1000.0
        updates["processing_cost"] = {
            "amount": processing_cost,
            "currency": "USD",
            "annual": True,
            "cost_drivers": f"{len(outbound_flows)} downstream flows",
        }
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.DATA_ASSET,
                fields_enriched=["processing_cost"],
                source="Flow processing model",
                methodology=f"Estimated from {len(outbound_flows)} downstream flows",
                confidence=ConfidenceLevel.LOW,
            )
        )

        # Privacy impact assessment
        domains = context.get_neighbors(RelationshipType.CLASSIFIED_AS)
        has_pii = False
        if domains and hasattr(domains[0], "sensitivity_flags"):
            sensitivity_flags = getattr(domains[0], "sensitivity_flags", None)
            if sensitivity_flags:
                has_pii = getattr(sensitivity_flags, "pii_flag", False)

        privacy_impact = {
            "has_pii": has_pii,
            "has_phi": False,
            "has_pci": False,
            "impact_level": "High" if has_pii else "Low",
            "dpia_required": has_pii,
        }
        updates["privacy_impact_assessment"] = privacy_impact
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.DATA_ASSET,
                fields_enriched=["privacy_impact_assessment"],
                source="Sensitivity classification analysis",
                methodology=f"Based on PII/PHI/PCI flags in {len(domains)} domains",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Breach notification obligation
        policies = context.get_neighbors(RelationshipType.GOVERNS)
        breach_obligation = {
            "subject_to_notification": len(policies) > 0 or has_pii,
            "notification_timeline": "72 hours" if has_pii else "30 days",
            "governing_policies": len(policies),
            "regulatory_basis": "GDPR" if has_pii else "Internal Policy",
        }
        updates["breach_notification_obligation"] = breach_obligation
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.DATA_ASSET,
                fields_enriched=["breach_notification_obligation"],
                source="Policy and sensitivity analysis",
                methodology=f"Based on {len(policies)} governing policies and PII presence",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        return updates, actions

    def _populate_tier_5(
        self, entity: BaseEntity, context: EntityContext, cross_profile: dict
    ) -> tuple[dict, list]:
        """Populate Tier 5 (Optimized) fields: full fidelity & predictive."""
        updates = {}
        actions = []

        # AI training usage eligibility
        outbound_flows = context.get_neighbors(RelationshipType.FLOWS_TO)
        ai_training_eligible = len(outbound_flows) > 2 and cross_profile.get("is_shared", False)
        updates["ai_training_usage"] = {
            "eligible_for_training": ai_training_eligible,
            "consent_required": True,
            "anonymization_required": ai_training_eligible,
            "current_usage": "Not used" if not ai_training_eligible else "Evaluating",
        }
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.DATA_ASSET,
                fields_enriched=["ai_training_usage"],
                source="Data sharing and governance analysis",
                methodology=f"Based on {len(outbound_flows)} downstream flows and data sharing patterns",
                confidence=ConfidenceLevel.LOW,
            )
        )

        # Monetization potential
        is_critical = cross_profile.get("is_critical", False)
        is_shared = cross_profile.get("is_shared", False)
        outbound_flows = context.get_neighbors(RelationshipType.FLOWS_TO)

        monetization_potential = {
            "potential_type": "Direct Data Product" if is_critical else "Process Optimization",
            "estimated_annual_value": 100000.0 if is_critical else 10000.0,
            "currency": "USD",
            "confidence": "High" if is_critical else "Low",
            "shared_across_flows": len(outbound_flows),
        }
        updates["monetization_potential"] = monetization_potential
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.DATA_ASSET,
                fields_enriched=["monetization_potential"],
                source="Strategic value assessment",
                methodology=f"Based on criticality, sharing ({is_shared}), and {len(outbound_flows)} flows",
                confidence=ConfidenceLevel.LOW,
            )
        )

        # Golden record status
        domains = context.get_neighbors(RelationshipType.CLASSIFIED_AS)
        is_golden = "No" if len(domains) == 0 else "Yes"
        updates["golden_record_status"] = {
            "is_golden_record": is_golden,
            "mastering_system": getattr(domains[0], "id", "") if domains else "",
            "last_certified": datetime.now(UTC).isoformat(),
            "certification_validity": "Annual",
        }
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.DATA_ASSET,
                fields_enriched=["golden_record_status"],
                source="Domain mastery analysis",
                methodology=f"Based on classification in {len(domains)} domains",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Fitness for purpose assessment
        inbound_flows = context.get_neighbors(RelationshipType.ORIGINATES_FROM)
        outbound_flows = context.get_neighbors(RelationshipType.FLOWS_TO)
        fitness_score = min(
            100,
            50 + (len(domains) * 10) + (len(outbound_flows) * 5) - (len(inbound_flows) * 2),
        )
        updates["fitness_for_purpose"] = {
            "overall_score": fitness_score,
            "primary_purpose": getattr(entity, "asset_type", "Unknown"),
            "secondary_uses": len(outbound_flows),
            "fitness_assessment": "High"
            if fitness_score > 80
            else "Medium"
            if fitness_score > 60
            else "Low",
            "improvement_areas": ["Data quality"] if fitness_score < 80 else [],
        }
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.DATA_ASSET,
                fields_enriched=["fitness_for_purpose"],
                source="Comprehensive usage analysis",
                methodology=f"Scored from domain integration ({len(domains)}), flows ({len(outbound_flows)})",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        return updates, actions

    def _identify_gaps(self, entity: BaseEntity, cross_profile: dict) -> list[DataGap]:
        """Identify known data gaps."""
        gaps = []

        if cross_profile.get("systems_count", 0) == 0:
            gaps.append(
                DataGap(
                    field_name="storage_system",
                    description="No storage system linked",
                    severity="High",
                    remediation_suggestion="Link to storing System via STORES relationship",
                )
            )

        if cross_profile.get("domains_count", 0) == 0:
            gaps.append(
                DataGap(
                    field_name="domain_classification",
                    description="Not classified in any DataDomain",
                    severity="Medium",
                    remediation_suggestion="Assign to DataDomain via CLASSIFIED_AS relationship",
                )
            )

        if (
            cross_profile.get("outbound_flows_count", 0) == 0
            and cross_profile.get("inbound_flows_count", 0) == 0
        ):
            gaps.append(
                DataGap(
                    field_name="data_flows",
                    description="No data flows linked (source or target)",
                    severity="Medium",
                    remediation_suggestion="Link to DataFlows via FLOWS_TO or ORIGINATES_FROM",
                )
            )

        if not getattr(entity, "data_owner", None):
            gaps.append(
                DataGap(
                    field_name="data_owner",
                    description="Data owner not assigned",
                    severity="High",
                    remediation_suggestion="Assign owner via domain or direct assignment",
                )
            )

        return gaps

    def _build_provenance(
        self, actions: list[EnrichmentAction], tier: EnrichmentTier, profile: EnrichmentProfile
    ) -> ProvenanceAndConfidence:
        """Build provenance record."""
        confidence_map = {
            EnrichmentTier.BASIC: "Medium",
            EnrichmentTier.STANDARD: "High",
            EnrichmentTier.DEEP: "Verified",
        }

        primary_source = "Enrichment Agency - DataAsset Enricher"
        if actions:
            primary_source += f" ({len(actions)} fields enriched)"

        return ProvenanceAndConfidence(
            primary_data_source=primary_source,
            last_assessed_date=datetime.now(UTC).isoformat(),
            assessed_by="DataAssetEnricher v1.0",
            assessment_methodology="Context-aware graph analysis + coordinated templates",
            confidence_level=confidence_map.get(tier, "Medium"),
        )
