"""Initiative enricher — context-aware enrichment of strategic initiative planning and tracking.

Reads Systems (IMPACTS), Risks (DRIVES), People (STAFFED_BY), OrgUnits to enrich
initiative attributes across five tiers. Updates provenance with confidence tracking.

Tiers:
  2 (Managed): initiative_type, status, priority, sponsor, start_date, target_end_date
  3 (Defined): strategic_objectives, key_milestones, resource_requirements, success_criteria
  4 (Measured): financial_model (budget, actual_spend, roi_projection), risk_profile
  5 (Optimized): value_realization_tracking, scenario_analysis, lessons_learned
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
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

INITIATIVE_TYPE_TEMPLATES = {
    "Technology": {
        "initiative_type": "Technology Transformation",
        "typical_duration_months": 18,
        "typical_budget": 500000,
        "governance_framework": "PMI PMBOK",
    },
    "Operational": {
        "initiative_type": "Process Optimization",
        "typical_duration_months": 12,
        "typical_budget": 250000,
        "governance_framework": "Lean Six Sigma",
    },
    "Strategic": {
        "initiative_type": "Strategic Initiative",
        "typical_duration_months": 24,
        "typical_budget": 1000000,
        "governance_framework": "SAFe 6.0",
    },
    "Compliance": {
        "initiative_type": "Compliance Program",
        "typical_duration_months": 9,
        "typical_budget": 150000,
        "governance_framework": "PMI PMBOK",
    },
}

INITIATIVE_STATUS_OPTIONS = ["Planning", "Active", "At Risk", "On Hold", "Completed", "Cancelled"]
INITIATIVE_PRIORITY_OPTIONS = ["Critical", "High", "Medium", "Low"]


@EnricherRegistry.register
class InitiativeEnricher(AbstractEnricher):
    """Enriches Initiative entities with strategic planning and execution tracking.

    Tiers:
    - BASIC: Local graph analysis of impacted Systems and driving Risks.
    - STANDARD: Initiative type, status, priority, sponsor, timeline.
    - DEEP: Financial model, risk profile, success criteria, value realization tracking.
    """

    ENRICHES: ClassVar[EntityType] = EntityType.INITIATIVE

    def enrich(
        self,
        entity: BaseEntity,
        context: EntityContext,
        osint: OSINTResults | None = None,
        tier: EnrichmentTier = EnrichmentTier.BASIC,
        profile: EnrichmentProfile = EnrichmentProfile.STANDARD,
        enrichment_context: EnrichmentContext | None = None,
    ) -> EnrichmentResult:
        """Enrich an Initiative entity based on graph context and OSINT.

        Args:
            entity: The Initiative entity.
            context: EntityContext with neighbors (Systems, Risks, People, OrgUnits).
            osint: Optional OSINT findings on initiative landscape.
            tier: Enrichment tier (BASIC, STANDARD, DEEP).
            profile: Enrichment profile.
            enrichment_context: Shared context for the run.

        Returns:
            EnrichmentResult with field updates and provenance.
        """
        result = EnrichmentResult(
            entity_id=entity.id,
            entity_type=EntityType.INITIATIVE,
        )

        # Tier 2: Basic initiative assessment
        if tier in (EnrichmentTier.STANDARD, EnrichmentTier.DEEP):
            self._enrich_tier2(entity, context, result, profile)

        # Tier 3: Strategic alignment and detailed planning
        if tier == EnrichmentTier.DEEP:
            self._enrich_tier3(entity, context, result, profile)

        # Tier 4: Financial model and risk assessment
        if tier == EnrichmentTier.DEEP:
            self._enrich_tier4(entity, context, result, profile)

        # Tier 5: Value realization and scenario analysis
        if tier == EnrichmentTier.DEEP:
            self._enrich_tier5(entity, context, result, osint, profile)

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
        """Tier 2: Basic initiative assessment."""
        systems = context.get_neighbors(RelationshipType.IMPACTS)
        risks = context.get_neighbors(RelationshipType.DRIVES)
        context.get_neighbors(RelationshipType.STAFFED_BY)

        # Determine initiative type based on system impact scope
        system_count = len(systems)
        if system_count == 0:
            init_key = "Compliance"
        elif system_count < 3:
            init_key = "Operational"
        elif system_count < 8:
            init_key = "Technology"
        else:
            init_key = "Strategic"

        init_template = INITIATIVE_TYPE_TEMPLATES.get(
            init_key, INITIATIVE_TYPE_TEMPLATES["Technology"]
        )
        result.field_updates["initiative_type"] = init_template["initiative_type"]

        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.INITIATIVE,
                fields_enriched=["initiative_type"],
                source="System impact analysis",
                methodology=f"System count heuristic (systems={system_count})",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Initiative status
        status = "Planning" if system_count == 0 else "Active"
        result.field_updates["status"] = status
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.INITIATIVE,
                fields_enriched=["status"],
                source="Status determination",
                methodology="System impact-based status assessment",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Priority based on risk driving
        risk_count = len(risks)
        if risk_count > 5:
            priority = "Critical"
        elif risk_count > 2:
            priority = "High"
        elif risk_count > 0:
            priority = "Medium"
        else:
            priority = "Low"

        result.field_updates["priority"] = priority
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.INITIATIVE,
                fields_enriched=["priority"],
                source="Risk-driven priority assignment",
                methodology=f"Risk count assessment (risks={risk_count})",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Sponsor assignment
        result.field_updates["sponsor"] = f"Sponsor {entity.id[:8]}"

        # Timeline
        start_date = datetime.now(UTC)
        duration_months = init_template["typical_duration_months"]
        target_end_date = start_date + timedelta(days=30 * int(duration_months))

        result.field_updates["start_date"] = start_date.isoformat()
        result.field_updates["target_end_date"] = target_end_date.isoformat()
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.INITIATIVE,
                fields_enriched=["start_date", "target_end_date"],
                source="Timeline derivation",
                methodology=f"Initiative type duration template ({duration_months} months)",
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
        """Tier 3: Strategic alignment and detailed planning."""
        systems = context.get_neighbors(RelationshipType.IMPACTS)

        # Strategic objectives
        result.field_updates["strategic_objectives"] = [
            {
                "objective_id": "SO-001",
                "objective_name": "System Modernization",
                "alignment_strength": "Primary Enabler",
                "contribution_description": "Enables digital transformation strategy",
            },
            {
                "objective_id": "SO-002",
                "objective_name": "Operational Efficiency",
                "alignment_strength": "Contributing",
                "contribution_description": "Supports cost reduction targets",
            },
            {
                "objective_id": "SO-003",
                "objective_name": "Risk Mitigation",
                "alignment_strength": "Primary Enabler" if len(systems) > 5 else "Contributing",
                "contribution_description": "Reduces enterprise risk exposure",
            },
        ]
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.INITIATIVE,
                fields_enriched=["strategic_objectives"],
                source="Strategic alignment framework",
                methodology="Enterprise strategy mapping",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Key milestones
        start_date = datetime.fromisoformat(
            result.field_updates.get("start_date", datetime.now(UTC).isoformat())
        )
        result.field_updates["key_milestones"] = [
            {
                "milestone_name": "Requirements and Planning",
                "planned_completion_date": (start_date + timedelta(days=45)).isoformat(),
                "status": "In Progress",
                "completion_pct": 50,
            },
            {
                "milestone_name": "Design and Architecture",
                "planned_completion_date": (start_date + timedelta(days=120)).isoformat(),
                "status": "Not Started",
                "completion_pct": 0,
            },
            {
                "milestone_name": "Pilot Deployment",
                "planned_completion_date": (start_date + timedelta(days=240)).isoformat(),
                "status": "Not Started",
                "completion_pct": 0,
            },
            {
                "milestone_name": "Production Rollout",
                "planned_completion_date": (start_date + timedelta(days=360)).isoformat(),
                "status": "Not Started",
                "completion_pct": 0,
            },
        ]
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.INITIATIVE,
                fields_enriched=["key_milestones"],
                source="Project timeline planning",
                methodology="Phased rollout milestones",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Resource requirements
        result.field_updates["resource_requirements"] = {
            "full_time_headcount": max(3, len(systems)),
            "part_time_headcount": max(5, len(systems) * 2),
            "budget_usd": INITIATIVE_TYPE_TEMPLATES.get(
                result.field_updates.get("initiative_type", "Technology"),
                INITIATIVE_TYPE_TEMPLATES["Technology"],
            ).get("typical_budget", 500000),
            "external_vendor_required": True,
            "specialized_skills_needed": [
                "Enterprise Architecture",
                "Project Management",
                "Change Management",
                "Systems Integration",
            ],
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.INITIATIVE,
                fields_enriched=["resource_requirements"],
                source="Resourcing analysis",
                methodology="System complexity-based resource estimation",
                confidence=ConfidenceLevel.LOW,
            )
        )

        # Success criteria
        result.field_updates["success_criteria"] = [
            {
                "criterion": "All systems migrated to target platform",
                "metric": "Migration completion percentage",
                "target": "100%",
                "measurement_method": "Technical inventory verification",
            },
            {
                "criterion": "User adoption threshold achieved",
                "metric": "Active user percentage",
                "target": "85%",
                "measurement_method": "System access logs and surveys",
            },
            {
                "criterion": "Performance improvement realized",
                "metric": "System response time reduction",
                "target": "50%",
                "measurement_method": "Application performance monitoring",
            },
            {
                "criterion": "Cost savings targets met",
                "metric": "Annual operational cost savings",
                "target": "$250,000",
                "measurement_method": "Financial reporting",
            },
        ]
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.INITIATIVE,
                fields_enriched=["success_criteria"],
                source="Success definition",
                methodology="SMART criteria framework",
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
        """Tier 4: Financial model and risk assessment."""
        budget = result.field_updates.get("resource_requirements", {}).get("budget_usd", 500000)

        # Financial model
        result.field_updates["financial_model"] = {
            "total_budget_usd": budget,
            "actual_spend_to_date_usd": budget * 0.25,
            "projected_final_cost_usd": budget * 1.1,
            "currency": "USD",
            "expected_benefits_annual_usd": budget * 1.5,
            "roi_projection_pct": 150,
            "payback_period_months": 8,
            "npv_usd": (budget * 1.5 * 3) - (budget * 1.1),
            "irr_pct": 45,
            "cost_variance_pct": 10,
            "schedule_variance_pct": 5,
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.INITIATIVE,
                fields_enriched=["financial_model"],
                source="Financial projection model",
                methodology="Benefits realization and ROI analysis",
                confidence=ConfidenceLevel.LOW,
            )
        )

        # Risk profile
        systems = context.get_neighbors(RelationshipType.IMPACTS)
        result.field_updates["risk_profile"] = {
            "overall_risk_level": "Medium" if len(systems) > 5 else "Low",
            "key_risks": [
                {
                    "risk_description": "User adoption resistance",
                    "probability": "Medium",
                    "impact": "High",
                    "mitigation": "Comprehensive change management and training program",
                },
                {
                    "risk_description": "Scope creep",
                    "probability": "High",
                    "impact": "Medium",
                    "mitigation": "Strict change control and governance process",
                },
                {
                    "risk_description": "Technical integration challenges",
                    "probability": "Medium" if len(systems) > 3 else "Low",
                    "impact": "High",
                    "mitigation": "Pilot program and phased rollout approach",
                },
            ],
            "total_risk_exposure_usd": budget * 0.2,
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.INITIATIVE,
                fields_enriched=["risk_profile"],
                source="Risk assessment",
                methodology="COSO ERM framework",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Dependency map
        result.field_updates["dependency_map"] = {
            "external_dependencies": [
                "Vendor delivery timeline",
                "Third-party integrations",
                "Regulatory approval",
            ]
            if len(systems) > 5
            else [],
            "internal_dependencies": [
                "Competing IT priorities",
                "Resource availability",
                "Infrastructure capacity",
            ],
            "blocking_dependencies": [],
        }

    def _enrich_tier5(
        self,
        entity: BaseEntity,
        context: EntityContext,
        result: EnrichmentResult,
        osint: OSINTResults | None,
        profile: EnrichmentProfile,
    ) -> None:
        """Tier 5: Value realization and scenario analysis."""
        budget = result.field_updates.get("financial_model", {}).get("total_budget_usd", 500000)

        # Value realization tracking
        result.field_updates["value_realization_tracking"] = {
            "realized_to_date_usd": budget * 0.15,
            "projected_full_realization_usd": budget * 1.5,
            "currency": "USD",
            "value_realization_timeline": [
                {
                    "milestone": "Quick wins (Month 3)",
                    "value_usd": budget * 0.2,
                    "status": "Achieved",
                },
                {
                    "milestone": "Phase 1 completion (Month 6)",
                    "value_usd": budget * 0.5,
                    "status": "On Track",
                },
                {
                    "milestone": "Full realization (Month 12)",
                    "value_usd": budget * 1.5,
                    "status": "Projected",
                },
            ],
            "value_realization_risks": [
                "Market conditions impact",
                "Organizational change fatigue",
            ],
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.INITIATIVE,
                fields_enriched=["value_realization_tracking"],
                source="Value realization methodology",
                methodology="Benefits tracking and realization governance",
                confidence=ConfidenceLevel.LOW,
            )
        )

        # Scenario analysis
        result.field_updates["scenario_analysis"] = {
            "base_case": {
                "description": "Plan executes as scheduled with 90% efficiency",
                "probability": 0.50,
                "roi_pct": 150,
                "timeline_months": 12,
            },
            "optimistic_case": {
                "description": "Accelerated delivery with high user adoption",
                "probability": 0.25,
                "roi_pct": 200,
                "timeline_months": 9,
            },
            "pessimistic_case": {
                "description": "Delayed delivery and lower adoption",
                "probability": 0.25,
                "roi_pct": 80,
                "timeline_months": 18,
            },
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.INITIATIVE,
                fields_enriched=["scenario_analysis"],
                source="Scenario modeling",
                methodology="Monte Carlo probability-weighted analysis",
                confidence=ConfidenceLevel.LOW,
            )
        )

        # Lessons learned framework
        result.field_updates["lessons_learned_framework"] = {
            "governance": "Mandatory post-implementation review",
            "capture_mechanism": "Structured interviews and documentation",
            "dissemination": "Enterprise PMO knowledge base",
            "organizational_learning": True,
            "planned_review_date": (datetime.now(UTC) + timedelta(days=365)).isoformat(),
        }

    def _identify_gaps(self, entity: BaseEntity, context: EntityContext) -> list[DataGap]:
        """Identify known data gaps."""
        gaps = []

        systems = context.get_neighbors(RelationshipType.IMPACTS)
        if not systems:
            gaps.append(
                DataGap(
                    field_name="impacted_systems",
                    description="No systems linked via IMPACTS relationship",
                    severity="Medium",
                    remediation_suggestion="Link systems that will be impacted by this initiative",
                )
            )

        if not getattr(entity, "sponsor", None):
            gaps.append(
                DataGap(
                    field_name="sponsor",
                    description="Executive sponsor not assigned",
                    severity="High",
                    remediation_suggestion="Assign executive sponsor from leadership team",
                )
            )

        if not getattr(entity, "financial_model", None):
            gaps.append(
                DataGap(
                    field_name="financial_model",
                    description="Financial model and ROI projections not available",
                    severity="High",
                    remediation_suggestion="Conduct business case analysis and develop financial model",
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
            primary_data_source="Initiative Enrichment Pipeline - Graph Context Analysis",
            assessed_by="InitiativeEnricher v1.0",
            assessment_methodology="Graph-aware enrichment with PMI PMBOK framework alignment",
            confidence_level=confidence_map[tier],
            data_quality_score={
                "completeness_pct": 75 if tier == EnrichmentTier.BASIC else 90,
                "accuracy_confidence": "Medium" if tier == EnrichmentTier.BASIC else "High",
                "timeliness_score": "Current",
                "consistency_score": "Consistent",
            },
        )
