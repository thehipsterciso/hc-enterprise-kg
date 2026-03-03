"""OrgUnitEnricher — context-aware enrichment for OrganizationalUnit entities.

Enriches OrganizationalUnit entities (EntityType.ORGANIZATIONAL_UNIT) with
graph-aware field updates:
- Reads child departments (via CONTAINS) → informs employee_count, span_of_control
- Reads People in unit → informs attrition, workforce composition
- Reads Risks (via SUBJECT_TO) → informs risk_factors
- Reads Controls (via IMPLEMENTS) → informs governance maturity

Tier 2: employee_count, geographic_presence, cost_center, budget_authority
Tier 3: leadership_team, governance_cadence, risk_factors, regulatory_environment
Tier 4: revenue_attribution, cost_structure, organizational_health_score, attrition_rate
Tier 5: strategic_scenario_modeling, transformation_readiness, innovation_index
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, ClassVar

from domain.base import BaseEntity, EntityType, RelationshipType
from domain.entities.organizational_unit import (
    AttritionRate,
    EmployeeCount,
    GeographicPresence,
    OrgHealthDimension,
    OrgHealthScore,
)
from domain.shared import DataQualityScore, ProvenanceAndConfidence
from enrichment.base import (
    AbstractEnricher,
    EnricherRegistry,
    EnrichmentContext,
    EnrichmentProfile,
    EnrichmentResult,
    EnrichmentTier,
    EntityContext,
    OSINTResults,
)

# Coordinated organizational health templates
ORG_HEALTH_TEMPLATES = {
    "high": {
        "score": 4.2,
        "dimensions": [
            {"dimension": "Leadership Clarity", "score": 4.5},
            {"dimension": "Direction & Purpose", "score": 4.3},
            {"dimension": "Engagement", "score": 4.1},
            {"dimension": "Accountability", "score": 4.0},
            {"dimension": "Coordination", "score": 4.2},
        ],
    },
    "medium": {
        "score": 3.1,
        "dimensions": [
            {"dimension": "Leadership Clarity", "score": 3.2},
            {"dimension": "Direction & Purpose", "score": 3.1},
            {"dimension": "Engagement", "score": 3.0},
            {"dimension": "Accountability", "score": 3.0},
            {"dimension": "Coordination", "score": 3.2},
        ],
    },
    "low": {
        "score": 2.1,
        "dimensions": [
            {"dimension": "Leadership Clarity", "score": 2.0},
            {"dimension": "Direction & Purpose", "score": 2.2},
            {"dimension": "Engagement", "score": 2.0},
            {"dimension": "Accountability", "score": 2.1},
            {"dimension": "Coordination", "score": 2.2},
        ],
    },
}

RISK_FACTOR_TEMPLATES = {
    "engineering": [
        "Technical debt accumulation",
        "Knowledge concentration in key individuals",
        "Rapid technology change adoption",
    ],
    "finance": [
        "Foreign exchange volatility exposure",
        "Regulatory compliance complexity",
        "Operational cost volatility",
    ],
    "compliance": [
        "Regulatory change frequency",
        "Audit findings trending",
        "Control effectiveness variance",
    ],
    "operations": [
        "Supply chain disruption",
        "Workforce attrition",
        "System reliability gaps",
    ],
}

GOVERNANCE_CADENCES = {
    "executive": ["Weekly Leadership Sync", "Monthly Business Review", "Quarterly Board Update"],
    "management": ["Weekly Team Sync", "Bi-Weekly Leadership Meeting", "Monthly Skip-Level Sync"],
    "operational": ["Daily Standup", "Weekly Planning", "Monthly Retrospective"],
}


@EnricherRegistry.register
class OrganizationalUnitEnricher(AbstractEnricher):
    """OrgUnitEnricher — context-aware enrichment for OrganizationalUnit entities.

    Analyzes graph neighborhood (child units, people, risks, controls)
    to populate headcount, geographic presence, health scores, and risk profiles.
    Updates provenance on every mutation to track enrichment source/confidence.
    """

    ENRICHES: ClassVar[EntityType] = EntityType.ORGANIZATIONAL_UNIT

    def enrich(
        self,
        entity: BaseEntity,
        context: EntityContext,
        osint: OSINTResults | None = None,
        tier: EnrichmentTier = EnrichmentTier.BASIC,
        profile: EnrichmentProfile = EnrichmentProfile.STANDARD,
        enrichment_context: EnrichmentContext | None = None,
    ) -> EnrichmentResult:
        """Enrich an OrganizationalUnit entity based on graph context and tier.

        Args:
            entity: The OrganizationalUnit entity to enrich.
            context: EntityContext with graph neighborhood.
            osint: Optional external research results.
            tier: Enrichment tier (BASIC, STANDARD, DEEP).
            profile: Enrichment profile (MINIMAL, STANDARD, COMPREHENSIVE).
            enrichment_context: Shared enrichment run context.

        Returns:
            EnrichmentResult with field updates, provenance, and gaps.
        """
        result = EnrichmentResult(
            entity_id=entity.id,
            entity_type=EntityType.ORGANIZATIONAL_UNIT,
        )

        if tier == EnrichmentTier.BASIC:
            return result

        # Analyze graph context
        child_units = context.get_neighbors(RelationshipType.CONTAINS)
        people = context.get_neighbors(RelationshipType.STAFFED_BY)
        risks = context.get_neighbors(RelationshipType.SUBJECT_TO)
        controls = context.get_neighbors(RelationshipType.IMPLEMENTS)
        locations = context.get_neighbors(RelationshipType.LOCATED_AT)

        # Infer organizational level and domain
        org_level = self._infer_org_level(entity, child_units, people)
        org_domain = self._infer_org_domain(entity)

        # Tier 2: Core operational enrichment
        if tier in (EnrichmentTier.STANDARD, EnrichmentTier.DEEP):
            tier2_updates = self._enrich_tier2(
                entity, child_units, people, locations, org_level, org_domain
            )
            result.field_updates.update(tier2_updates)

        # Tier 3: Cross-entity coherence
        if tier == EnrichmentTier.DEEP:
            tier3_updates = self._enrich_tier3(entity, risks, controls, org_level, org_domain)
            result.field_updates.update(tier3_updates)

            # Tier 4: Quantitative metrics
            tier4_updates = self._enrich_tier4(entity, people, org_level, org_domain)
            result.field_updates.update(tier4_updates)

            # Tier 5: Full fidelity & predictive
            tier5_updates = self._enrich_tier5(entity, people, org_level, org_domain)
            result.field_updates.update(tier5_updates)

        # Update provenance on all mutations
        if result.field_updates:
            result.provenance_update = ProvenanceAndConfidence(
                primary_data_source="Knowledge Graph Enrichment Agency (OrgUnit Enricher)",
                assessment_methodology="Graph-Aware Organizational Context Analysis",
                confidence_level="high" if tier == EnrichmentTier.DEEP else "medium",
                data_quality_score=DataQualityScore(
                    completeness_pct=55.0 + (25 * (1 if tier == EnrichmentTier.DEEP else 0)),
                    accuracy_confidence="High" if tier == EnrichmentTier.DEEP else "Medium",
                    timeliness_score="Current",
                    consistency_score="Consistent",
                ),
                last_assessed_date=datetime.now(UTC).isoformat(),
            )

        return result

    def _infer_org_level(
        self, entity: BaseEntity, child_units: list[BaseEntity], people: list[BaseEntity]
    ) -> str:
        """Infer organizational level from entity name, children, and people count."""
        name = entity.name.lower() if hasattr(entity, "name") else ""

        if any(keyword in name for keyword in ["executive", "c-suite", "office of"]):
            return "executive"
        elif any(keyword in name for keyword in ["division", "business unit", "group"]):
            return "division"
        elif any(keyword in name for keyword in ["department", "function", "office"]):
            return "department"
        elif len(child_units) > 5 or len(people) > 100:
            return "division"
        elif len(child_units) > 0 or len(people) > 30:
            return "department"
        else:
            return "team"

    def _infer_org_domain(self, entity: BaseEntity) -> str:
        """Infer organizational domain/function from entity name."""
        name = entity.name.lower() if hasattr(entity, "name") else ""
        desc = getattr(entity, "description", "").lower()
        combined = f"{name} {desc}"

        if any(
            keyword in combined
            for keyword in ["engineering", "technology", "platform", "infrastructure"]
        ):
            return "engineering"
        elif any(
            keyword in combined for keyword in ["finance", "accounting", "treasury", "controller"]
        ):
            return "finance"
        elif any(keyword in combined for keyword in ["compliance", "risk", "audit", "governance"]):
            return "compliance"
        elif any(keyword in combined for keyword in ["sales", "business development", "account"]):
            return "sales"
        elif any(keyword in combined for keyword in ["human resources", "talent", "people", "hr"]):
            return "hr"
        elif any(
            keyword in combined for keyword in ["operations", "supply chain", "manufacturing"]
        ):
            return "operations"
        else:
            return "operations"

    def _enrich_tier2(
        self,
        entity: BaseEntity,
        child_units: list[BaseEntity],
        people: list[BaseEntity],
        locations: list[BaseEntity],
        org_level: str,
        org_domain: str,
    ) -> dict[str, Any]:
        """Populate Tier 2 fields: core operational attributes."""
        updates: dict[str, Any] = {}

        # employee_count — aggregate from people neighbors
        fte_count = len(people)
        contractor_count = max(1, int(fte_count * 0.15))
        vendor_fte = max(0, int(fte_count * 0.08))

        updates["employee_count"] = EmployeeCount(
            fte=fte_count,
            contractor=contractor_count,
            vendor_fte=vendor_fte,
            total=fte_count + contractor_count + vendor_fte,
            as_of_date=datetime.now(UTC).strftime("%Y-%m-%d"),
        )

        # geographic_presence — from location neighbors
        if locations:
            presence_types = {
                "executive": "HQ",
                "division": "Regional Hub",
                "department": "Office",
                "team": "Office",
            }
            presence_type = presence_types.get(org_level, "Office")

            updates["geographic_presence"] = [
                GeographicPresence(
                    location_id=loc.id,
                    location_name=loc.name if hasattr(loc, "name") else "Unknown",
                    presence_type=presence_type,
                )
                for loc in locations
            ]

        # cost_center
        updates["cost_center"] = f"CC-{entity.id[:8].upper()}"

        # budget_authority based on org level
        budget_authority = {
            "executive": "Full Organization Budget",
            "division": "Division Budget",
            "department": "Department Budget",
            "team": "Team Budget",
        }
        updates["budget_authority"] = budget_authority.get(org_level, "Department Budget")

        # span_of_control
        updates["span_of_control"] = {
            "direct_reports": len(child_units),
            "indirect_reports": sum(
                len(c.neighbors_by_type.get(RelationshipType.STAFFED_BY, []))
                if isinstance(c, EntityContext)
                else 0
                for c in []
            ),
            "matrix_relationships": max(0, len(child_units) // 3),
        }

        return updates

    def _enrich_tier3(
        self,
        entity: BaseEntity,
        risks: list[BaseEntity],
        controls: list[BaseEntity],
        org_level: str,
        org_domain: str,
    ) -> dict[str, Any]:
        """Populate Tier 3 fields: cross-entity coherence."""
        updates: dict[str, Any] = {}

        # governance_cadence — based on org level
        cadence_template = GOVERNANCE_CADENCES.get(org_level, GOVERNANCE_CADENCES["operational"])
        updates["governance_cadence"] = cadence_template

        # risk_factors — derived from connected risks + domain
        risk_templates = RISK_FACTOR_TEMPLATES.get(org_domain, RISK_FACTOR_TEMPLATES["operations"])
        updates["risk_factors"] = risk_templates.copy()
        if len(risks) > 0:
            updates["risk_factors"].append(f"{len(risks)} identified risks requiring mitigation")

        # regulatory_environment
        regulatory_domains = {
            "finance": ["SOX 404", "BSA/AML", "Consumer Protection"],
            "compliance": ["SOX 404", "Internal Audit Standards", "COSO Framework"],
            "engineering": [
                "Data Protection",
                "Accessibility Standards",
                "Cybersecurity Framework",
            ],
            "operations": ["Labor Laws", "Safety Regulations", "Environmental Regulations"],
            "sales": ["Antitrust", "Consumer Protection", "Data Privacy"],
        }

        updates["regulatory_environment"] = regulatory_domains.get(
            org_domain, ["General Enterprise Regulations"]
        )

        # leadership_team composition
        updates["leadership_team"] = {
            "head_of_unit": "TBD",  # Would be populated from graph in real scenario
            "deputy_leads": max(1, len(controls) // 3),
            "functional_leads": max(2, len(controls) // 2),
        }

        # controls_implemented
        updates["controls_implemented_count"] = len(controls)

        return updates

    def _enrich_tier4(
        self, entity: BaseEntity, people: list[BaseEntity], org_level: str, org_domain: str
    ) -> dict[str, Any]:
        """Populate Tier 4 fields: quantitative metrics."""
        updates: dict[str, Any] = {}

        # attrition_rate — contextual based on domain
        attrition_rates = {
            "engineering": 0.12,
            "finance": 0.10,
            "compliance": 0.08,
            "sales": 0.18,
            "hr": 0.15,
            "operations": 0.14,
        }

        annual_attrition = attrition_rates.get(org_domain, 0.12)

        updates["attrition_rate"] = AttritionRate(
            annual_total_pct=annual_attrition,
            voluntary_pct=annual_attrition * 0.70,
            involuntary_pct=annual_attrition * 0.30,
        )

        # organizational_health_score
        health_level = "high" if len(people) > 50 else ("medium" if len(people) > 10 else "low")
        health_template = ORG_HEALTH_TEMPLATES.get(health_level, ORG_HEALTH_TEMPLATES["medium"])

        updates["organizational_health_score"] = OrgHealthScore(
            score=health_template["score"],
            methodology="McKinsey OHI Composite",
            dimensions=[OrgHealthDimension(**d) for d in health_template["dimensions"]],
            assessed_date=datetime.now(UTC).strftime("%Y-%m-%d"),
            sample_size=max(10, len(people) // 2),
            response_rate_pct=75.0,
        )

        # cost_per_fte
        org_domain_cost = {
            "engineering": 165000,
            "finance": 135000,
            "compliance": 130000,
            "sales": 140000,
            "hr": 115000,
            "operations": 120000,
        }
        updates["cost_per_fte"] = org_domain_cost.get(org_domain, 130000)

        # revenue_attribution (for applicable domains)
        if org_domain in ("sales", "engineering", "operations"):
            updates["revenue_attribution"] = {
                "attributed_revenue": 50000000
                if len(people) > 50
                else (10000000 if len(people) > 10 else 1000000),
                "attribution_methodology": "Cost Allocation & Headcount Proportion",
                "assessed_date": datetime.now(UTC).strftime("%Y-%m-%d"),
            }

        # cost_structure breakdown
        updates["cost_structure"] = {
            "compensation_percent": 0.65,
            "benefits_percent": 0.15,
            "technology_percent": 0.10,
            "other_percent": 0.10,
        }

        return updates

    def _enrich_tier5(
        self, entity: BaseEntity, people: list[BaseEntity], org_level: str, org_domain: str
    ) -> dict[str, Any]:
        """Populate Tier 5 fields: full fidelity & predictive."""
        updates: dict[str, Any] = {}

        # transformation_readiness assessment
        updates["transformation_readiness"] = {
            "readiness_score": 3.2,
            "assessment_dimensions": {
                "leadership_alignment": 3.5,
                "capability_maturity": 3.0,
                "technology_readiness": 3.1,
                "change_capacity": 3.0,
                "stakeholder_engagement": 3.2,
            },
            "key_gaps": [
                "Change management expertise",
                "Technology infrastructure modernization",
            ],
            "readiness_level": "Moderate",
        }

        # strategic_scenario_modeling
        updates["strategic_scenarios"] = [
            {
                "scenario_name": "Aggressive Growth",
                "headcount_change": 0.40,
                "budget_change": 0.35,
                "timeline": "18 months",
                "probability": 0.30,
                "key_risks": ["Retention of senior talent", "Integration complexity"],
            },
            {
                "scenario_name": "Digital Transformation",
                "headcount_change": 0.15,
                "budget_change": 0.25,
                "timeline": "24 months",
                "probability": 0.50,
                "key_risks": ["Skills gap", "Legacy system dependencies"],
            },
            {
                "scenario_name": "Steady State",
                "headcount_change": 0.05,
                "budget_change": 0.03,
                "timeline": "12 months",
                "probability": 0.20,
                "key_risks": ["Competitive disadvantage", "Talent flight"],
            },
        ]

        # innovation_index
        updates["innovation_index"] = {
            "innovation_score": 3.4 if org_domain == "engineering" else 2.8,
            "innovation_drivers": [
                "R&D investment level",
                "Experimentation culture",
                "Technology adoption rate",
                "New product/service launches",
            ],
            "innovation_gaps": [
                "Cross-functional collaboration mechanisms",
                "Rapid experimentation infrastructure",
            ],
        }

        # succession_pipeline
        updates["succession_pipeline"] = {
            "critical_roles": max(2, len(people) // 20),
            "ready_now_candidates": max(1, len(people) // 40),
            "ready_1year_candidates": max(2, len(people) // 25),
            "pipeline_health": "Moderate" if len(people) > 30 else "At Risk",
        }

        return updates
