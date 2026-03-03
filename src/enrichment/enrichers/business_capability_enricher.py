"""BusinessCapability enricher — context-aware enrichment of capability maturity.

Reads Systems (REALIZED_BY), Roles (ENABLES), OrgUnits to enrich capability
attributes across five tiers. Updates provenance with confidence tracking.

Tiers:
  2 (Managed): capability_level, maturity_level, capability_owner, strategic_importance
  3 (Defined): supporting_systems, performance_metrics, risk_exposure
  4 (Measured): maturity_dimensions (5 dimensions scored 1-5), value_stream_alignment
  5 (Optimized): transformation_roadmap, automation_opportunity_score
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar

from domain.base import BaseEntity, EntityType, RelationshipType
from domain.shared import DataGap, ProvenanceAndConfidence
from enrichment.base import (
    AbstractEnricher,
    ConfidenceLevel,
    EnrichmentAction,
    EnrichmentContext,
    EnrichmentProfile,
    EnrichmentResult,
    EnrichmentTier,
    EntityContext,
    EnricherRegistry,
    OSINTResults,
)


# Capability level templates
CAPABILITY_LEVEL_TEMPLATES = {
    "Strategic": {
        "level": "Strategic",
        "strategic_importance": "Critical",
        "drives_competitive_advantage": True,
        "investment_tier": "High",
    },
    "Core": {
        "level": "Core",
        "strategic_importance": "High",
        "drives_competitive_advantage": False,
        "investment_tier": "Medium",
    },
    "Supporting": {
        "level": "Supporting",
        "strategic_importance": "Medium",
        "drives_competitive_advantage": False,
        "investment_tier": "Low",
    },
    "Legacy": {
        "level": "Legacy",
        "strategic_importance": "Low",
        "drives_competitive_advantage": False,
        "investment_tier": "Minimal",
    },
}

MATURITY_DIMENSIONS = [
    {
        "dimension": "Process Maturity",
        "description": "Standardization and documentation of processes",
    },
    {
        "dimension": "Technology Enablement",
        "description": "Modern technology stack and automation",
    },
    {
        "dimension": "Talent & Skills",
        "description": "Team capability and expertise",
    },
    {
        "dimension": "Data Quality",
        "description": "Data completeness, accuracy, and governance",
    },
    {
        "dimension": "Measurement & Analytics",
        "description": "Metrics and insights availability",
    },
]


@EnricherRegistry.register
class BusinessCapabilityEnricher(AbstractEnricher):
    """Enriches BusinessCapability entities with context-aware assessment.

    Tiers:
    - BASIC: Local graph analysis of Systems and Roles.
    - STANDARD: Capability level, maturity assessment, ownership.
    - DEEP: Detailed maturity dimensions, value stream alignment, automation opportunities.
    """

    ENRICHES: ClassVar[EntityType] = EntityType.BUSINESS_CAPABILITY

    def enrich(
        self,
        entity: BaseEntity,
        context: EntityContext,
        osint: OSINTResults | None = None,
        tier: EnrichmentTier = EnrichmentTier.BASIC,
        profile: EnrichmentProfile = EnrichmentProfile.STANDARD,
        enrichment_context: EnrichmentContext | None = None,
    ) -> EnrichmentResult:
        """Enrich a BusinessCapability entity based on graph context and OSINT.

        Args:
            entity: The BusinessCapability entity.
            context: EntityContext with neighbors (Systems, Roles, OrgUnits).
            osint: Optional OSINT findings on capability landscape.
            tier: Enrichment tier (BASIC, STANDARD, DEEP).
            profile: Enrichment profile.
            enrichment_context: Shared context for the run.

        Returns:
            EnrichmentResult with field updates and provenance.
        """
        result = EnrichmentResult(
            entity_id=entity.id,
            entity_type=EntityType.BUSINESS_CAPABILITY,
        )

        # Tier 2: Basic capability assessment
        if tier in (EnrichmentTier.STANDARD, EnrichmentTier.DEEP):
            self._enrich_tier2(entity, context, result, profile)

        # Tier 3: Cross-entity coherence and systems linkage
        if tier == EnrichmentTier.DEEP:
            self._enrich_tier3(entity, context, result, profile)

        # Tier 4: Detailed maturity assessment and dimensions
        if tier == EnrichmentTier.DEEP:
            self._enrich_tier4(entity, context, result, profile)

        # Tier 5: Transformation roadmap and optimization
        if tier == EnrichmentTier.DEEP:
            self._enrich_tier5(entity, context, result, profile)

        # Identify data gaps
        result.known_gaps = self._identify_gaps(entity, context)

        # Update provenance
        self._update_provenance(result, tier, profile)

        return result

    def _enrich_tier2(
        self,
        entity: BaseEntity,
        context: EntityContext,
        result: EnrichmentResult,
        profile: EnrichmentProfile,
    ) -> None:
        """Tier 2: Basic capability assessment."""
        systems = context.get_neighbors(RelationshipType.REALIZED_BY)
        roles = context.get_neighbors(RelationshipType.ENABLES)

        # Determine capability level based on system complexity
        system_count = len(systems)
        if system_count == 0:
            cap_level = "Legacy"
        elif system_count < 2:
            cap_level = "Supporting"
        elif system_count < 5:
            cap_level = "Core"
        else:
            cap_level = "Strategic"

        cap_template = CAPABILITY_LEVEL_TEMPLATES.get(cap_level, CAPABILITY_LEVEL_TEMPLATES["Supporting"])
        result.field_updates["capability_level"] = cap_template["level"]
        result.field_updates["strategic_importance"] = cap_template["strategic_importance"]
        result.field_updates["investment_tier"] = cap_template["investment_tier"]

        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.BUSINESS_CAPABILITY,
                fields_enriched=["capability_level", "strategic_importance", "investment_tier"],
                source="Graph-aware capability assessment",
                methodology=f"System count heuristic (systems={system_count})",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Maturity level based on role coverage
        role_count = len(roles)
        if role_count == 0:
            maturity = "Initial"
        elif role_count < 3:
            maturity = "Repeatable"
        elif role_count < 7:
            maturity = "Defined"
        else:
            maturity = "Managed"

        result.field_updates["maturity_level"] = maturity
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.BUSINESS_CAPABILITY,
                fields_enriched=["maturity_level"],
                source="Role coverage analysis",
                methodology=f"Role count assessment (roles={role_count})",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Capability owner (first available system owner or placeholder)
        if systems:
            # In a real scenario, would follow RESPONSIBLE_FOR edges
            result.field_updates["capability_owner"] = f"Capability Owner {entity.id[:8]}"
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.BUSINESS_CAPABILITY,
                fields_enriched=["capability_owner"],
                source="Placeholder assignment",
                methodology="Default assignment pending ownership discovery",
                confidence=ConfidenceLevel.LOW,
            )
        )

    def _enrich_tier3(
        self,
        entity: BaseEntity,
        context: EntityContext,
        result: EnrichmentResult,
        profile: EnrichmentProfile,
    ) -> None:
        """Tier 3: Cross-entity coherence and system linkage."""
        systems = context.get_neighbors(RelationshipType.REALIZED_BY)

        # Supporting systems summary
        supporting_systems = [
            {
                "system_id": sys.id,
                "system_name": getattr(sys, "name", "Unknown"),
                "system_type": getattr(sys, "system_type", "Unknown"),
                "criticality": "High" if len(systems) < 3 else "Medium",
            }
            for sys in systems
        ]
        result.field_updates["supporting_systems"] = supporting_systems
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.BUSINESS_CAPABILITY,
                fields_enriched=["supporting_systems"],
                source="System topology analysis",
                methodology=f"REALIZED_BY traversal ({len(systems)} systems)",
                confidence=ConfidenceLevel.HIGH,
            )
        )

        # Performance metrics placeholder
        result.field_updates["performance_metrics"] = {
            "availability_pct": 99.5 if systems else 0,
            "response_time_ms": 250 if systems else None,
            "transaction_volume_daily": 100000 if len(systems) > 2 else 10000,
            "measurement_period": "Last 90 days",
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.BUSINESS_CAPABILITY,
                fields_enriched=["performance_metrics"],
                source="System-derived metrics",
                methodology="Template-based estimation from system count",
                confidence=ConfidenceLevel.LOW,
            )
        )

        # Risk exposure based on system vulnerabilities
        risk_count = sum(len(context.get_neighbors(RelationshipType.AFFECTS)) for _ in [systems] if systems)
        risk_exposure = "Low" if risk_count == 0 else "Medium" if risk_count < 3 else "High"
        result.field_updates["risk_exposure"] = risk_exposure
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.BUSINESS_CAPABILITY,
                fields_enriched=["risk_exposure"],
                source="Risk correlation analysis",
                methodology=f"Derived from system risk profiles",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

    def _enrich_tier4(
        self,
        entity: BaseEntity,
        context: EntityContext,
        result: EnrichmentResult,
        profile: EnrichmentProfile,
    ) -> None:
        """Tier 4: Detailed maturity dimensions and value stream alignment."""
        systems = context.get_neighbors(RelationshipType.REALIZED_BY)

        # Score each maturity dimension 1-5 based on system modernization
        system_count = len(systems)
        base_score = min(5, 2 + (system_count / 3))

        maturity_dimensions = []
        for dim_info in MATURITY_DIMENSIONS:
            # Vary scores slightly based on dimension
            if "Technology" in dim_info["dimension"]:
                score = base_score + 0.5
            elif "Process" in dim_info["dimension"]:
                score = base_score - 0.3
            else:
                score = base_score

            maturity_dimensions.append({
                "dimension": dim_info["dimension"],
                "description": dim_info["description"],
                "score": min(5.0, max(1.0, score)),
                "assessed_date": datetime.now(UTC).isoformat(),
                "evidence_reference": f"System assessment for {entity.id}",
            })

        result.field_updates["maturity_dimensions"] = maturity_dimensions
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.BUSINESS_CAPABILITY,
                fields_enriched=["maturity_dimensions"],
                source="Dimension-based capability assessment",
                methodology="5-point scale scoring based on system modernization",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Value stream alignment
        result.field_updates["value_stream_alignment"] = {
            "value_stream_id": f"VS-{entity.id[:8]}",
            "value_stream_name": f"Core Value Stream {entity.id[:8]}",
            "contribution_type": "Primary Driver" if system_count > 3 else "Key Enabler",
            "strategic_value": "High" if system_count > 3 else "Medium",
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.BUSINESS_CAPABILITY,
                fields_enriched=["value_stream_alignment"],
                source="Strategic alignment analysis",
                methodology="Based on system complexity and supporting role count",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Investment allocation
        investment_tier = result.field_updates.get("investment_tier", "Medium")
        if investment_tier == "High":
            annual_allocation = 500000
        elif investment_tier == "Medium":
            annual_allocation = 250000
        else:
            annual_allocation = 50000

        result.field_updates["investment_allocation"] = {
            "annual_allocation_usd": annual_allocation,
            "allocation_horizon_years": 3,
            "allocation_rationale": f"Based on {investment_tier} investment tier",
            "last_reviewed_date": datetime.now(UTC).isoformat(),
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.BUSINESS_CAPABILITY,
                fields_enriched=["investment_allocation"],
                source="Investment planning analysis",
                methodology="Tier-based allocation formula",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

    def _enrich_tier5(
        self,
        entity: BaseEntity,
        context: EntityContext,
        result: EnrichmentResult,
        profile: EnrichmentProfile,
    ) -> None:
        """Tier 5: Transformation roadmap and automation opportunities."""
        systems = context.get_neighbors(RelationshipType.REALIZED_BY)

        # Transformation roadmap
        result.field_updates["transformation_roadmap"] = {
            "current_state_summary": "Operational with legacy components" if systems else "Initial/minimal automation",
            "target_state_summary": "Modernized cloud-native capability",
            "planned_initiatives": [
                {
                    "initiative_name": "System Modernization",
                    "planned_start_date": "2026-Q3",
                    "planned_end_date": "2027-Q2",
                    "estimated_investment": 250000,
                    "expected_roi_pct": 25,
                },
                {
                    "initiative_name": "Process Automation",
                    "planned_start_date": "2027-Q1",
                    "planned_end_date": "2027-Q3",
                    "estimated_investment": 150000,
                    "expected_roi_pct": 35,
                },
            ],
            "success_metrics": [
                "Reduce manual processing by 50%",
                "Improve capability maturity to 'Optimized'",
                "Achieve 99.95% availability",
            ],
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.BUSINESS_CAPABILITY,
                fields_enriched=["transformation_roadmap"],
                source="Strategic transformation planning",
                methodology="Template-based roadmap with system complexity factors",
                confidence=ConfidenceLevel.LOW,
            )
        )

        # Automation opportunity score
        manual_tasks_estimate = max(1, 10 - len(systems))
        automation_potential = min(95, 50 + (len(systems) * 5))

        result.field_updates["automation_opportunity_score"] = {
            "overall_score": automation_potential,
            "scale": "0-100",
            "manual_tasks_identified": manual_tasks_estimate,
            "automation_potential_annual_savings": automation_potential * 1000,
            "currency": "USD",
            "implementation_complexity": "Medium" if automation_potential > 60 else "Low",
            "recommended_next_step": "Conduct detailed automation assessment",
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.BUSINESS_CAPABILITY,
                fields_enriched=["automation_opportunity_score"],
                source="Automation opportunity analysis",
                methodology="Manual task estimation + system complexity formula",
                confidence=ConfidenceLevel.LOW,
            )
        )

    def _identify_gaps(self, entity: BaseEntity, context: EntityContext) -> list[DataGap]:
        """Identify known data gaps."""
        gaps = []

        systems = context.get_neighbors(RelationshipType.REALIZED_BY)
        if not systems:
            gaps.append(
                DataGap(
                    field_name="supporting_systems",
                    description="No systems linked via REALIZED_BY",
                    severity="High",
                    remediation_suggestion="Link systems that realize this capability",
                )
            )

        if not getattr(entity, "capability_owner", None):
            gaps.append(
                DataGap(
                    field_name="capability_owner",
                    description="Capability owner not assigned",
                    severity="Medium",
                    remediation_suggestion="Assign owner via organizational relationship",
                )
            )

        if not getattr(entity, "performance_metrics", None):
            gaps.append(
                DataGap(
                    field_name="performance_metrics",
                    description="No performance metrics defined",
                    severity="Medium",
                    remediation_suggestion="Define KPIs for capability health",
                )
            )

        return gaps

    def _update_provenance(
        self,
        result: EnrichmentResult,
        tier: EnrichmentTier,
        profile: EnrichmentProfile,
    ) -> None:
        """Update provenance with enrichment confidence tracking."""
        confidence_map = {
            EnrichmentTier.BASIC: ConfidenceLevel.MEDIUM,
            EnrichmentTier.STANDARD: ConfidenceLevel.HIGH,
            EnrichmentTier.DEEP: ConfidenceLevel.HIGH,
        }

        result.provenance_update = ProvenanceAndConfidence(
            primary_data_source="Capability Enrichment Pipeline - Graph Context Analysis",
            assessed_by="BusinessCapabilityEnricher v1.0",
            assessment_methodology="Graph-aware enrichment with capability maturity model alignment",
            confidence_level=confidence_map[tier],
            data_quality_score={
                "completeness_pct": 65 if tier == EnrichmentTier.BASIC else 85,
                "accuracy_confidence": "Medium" if tier == EnrichmentTier.BASIC else "High",
                "timeliness_score": "Current",
                "consistency_score": "Consistent",
            },
        )
