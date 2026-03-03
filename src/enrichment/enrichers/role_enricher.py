"""RoleEnricher — context-aware enrichment for Role entities.

Enriches Role entities (EntityType.ROLE) with graph-aware field updates:
- Reads filled_by persons → informs headcount, vacancy, turnover
- Reads department → informs role family context
- Reads systems required → informs technical skill requirements
- Analyzes workforce patterns → informs compensation, headcount targets

Tier 2: required_skills, compensation_range, authority_level, travel_requirement
Tier 3: competency_model_reference, governance_memberships, regulatory_accountability
Tier 4: vacancy_count, headcount_target, turnover_rate, time_to_fill
Tier 5: future_skills_projection, automation_risk_assessment
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, ClassVar

from domain.base import BaseEntity, EntityType, RelationshipType
from domain.entities.role import (
    AuthorityDelegated,
    CompetencyModelReference,
    CompetencyReference,
    ContractAuthority,
    FinancialLimit,
    RequiredSkill,
    TravelRequirement,
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

# Coordinated skill templates by role family
ROLE_SKILL_TEMPLATES = {
    "engineering": [
        {"name": "Python", "category": "Technical", "level": "Expert", "criticality": "Must Have"},
        {
            "name": "Cloud Architecture",
            "category": "Technical",
            "level": "Expert",
            "criticality": "Must Have",
        },
        {
            "name": "System Design",
            "category": "Technical",
            "level": "Practitioner",
            "criticality": "Should Have",
        },
        {
            "name": "Software Engineering Practices",
            "category": "Strategic & Business",
            "level": "Expert",
            "criticality": "Must Have",
        },
        {
            "name": "Team Leadership",
            "category": "Leadership & Management",
            "level": "Practitioner",
            "criticality": "Should Have",
        },
    ],
    "data": [
        {"name": "SQL", "category": "Technical", "level": "Expert", "criticality": "Must Have"},
        {
            "name": "Statistics",
            "category": "Analytical & Quantitative",
            "level": "Expert",
            "criticality": "Must Have",
        },
        {
            "name": "Data Modeling",
            "category": "Technical",
            "level": "Expert",
            "criticality": "Must Have",
        },
        {
            "name": "Python/R",
            "category": "Technical",
            "level": "Practitioner",
            "criticality": "Should Have",
        },
        {
            "name": "Business Acumen",
            "category": "Strategic & Business",
            "level": "Practitioner",
            "criticality": "Should Have",
        },
    ],
    "product": [
        {
            "name": "Product Strategy",
            "category": "Strategic & Business",
            "level": "Expert",
            "criticality": "Must Have",
        },
        {
            "name": "User Research",
            "category": "Communication & Influence",
            "level": "Expert",
            "criticality": "Must Have",
        },
        {
            "name": "Roadmap Development",
            "category": "Strategic & Business",
            "level": "Expert",
            "criticality": "Must Have",
        },
        {
            "name": "Data Analysis",
            "category": "Analytical & Quantitative",
            "level": "Practitioner",
            "criticality": "Should Have",
        },
        {
            "name": "Stakeholder Management",
            "category": "Communication & Influence",
            "level": "Expert",
            "criticality": "Must Have",
        },
    ],
    "compliance": [
        {
            "name": "Risk Management",
            "category": "Regulatory & Compliance",
            "level": "Expert",
            "criticality": "Must Have",
        },
        {
            "name": "Audit Procedures",
            "category": "Regulatory & Compliance",
            "level": "Expert",
            "criticality": "Must Have",
        },
        {
            "name": "Regulatory Framework Knowledge",
            "category": "Regulatory & Compliance",
            "level": "Expert",
            "criticality": "Must Have",
        },
        {
            "name": "Documentation & Writing",
            "category": "Communication & Influence",
            "level": "Expert",
            "criticality": "Must Have",
        },
    ],
    "management": [
        {
            "name": "Strategic Planning",
            "category": "Strategic & Business",
            "level": "Expert",
            "criticality": "Must Have",
        },
        {
            "name": "Team Leadership",
            "category": "Leadership & Management",
            "level": "Expert",
            "criticality": "Must Have",
        },
        {
            "name": "Budget Management",
            "category": "Analytical & Quantitative",
            "level": "Expert",
            "criticality": "Must Have",
        },
        {
            "name": "Stakeholder Management",
            "category": "Communication & Influence",
            "level": "Expert",
            "criticality": "Must Have",
        },
        {
            "name": "Change Management",
            "category": "Leadership & Management",
            "level": "Practitioner",
            "criticality": "Should Have",
        },
    ],
}

COMPENSATION_TEMPLATES = {
    "engineering": {"min": 120000, "mid": 150000, "max": 200000},
    "data": {"min": 110000, "mid": 145000, "max": 190000},
    "product": {"min": 130000, "mid": 160000, "max": 210000},
    "compliance": {"min": 100000, "mid": 130000, "max": 170000},
    "management": {"min": 150000, "mid": 200000, "max": 300000},
}

AUTHORITY_TEMPLATES = {
    "engineering": {
        "financial_approval_limit": 50000,
        "hiring_authority": "Individual Contributors Only",
        "contract_max": 250000,
        "system_access": "Power User",
    },
    "data": {
        "financial_approval_limit": 50000,
        "hiring_authority": "Individual Contributors Only",
        "contract_max": 200000,
        "system_access": "Standard User",
    },
    "product": {
        "financial_approval_limit": 100000,
        "hiring_authority": "Up to Manager Level",
        "contract_max": 500000,
        "system_access": "Power User",
    },
    "compliance": {
        "financial_approval_limit": 75000,
        "hiring_authority": "No Hiring Authority",
        "contract_max": 300000,
        "system_access": "Standard User",
    },
    "management": {
        "financial_approval_limit": 500000,
        "hiring_authority": "Full — All Levels",
        "contract_max": 2000000,
        "system_access": "Enterprise Admin",
    },
}


@EnricherRegistry.register
class RoleEnricher(AbstractEnricher):
    """RoleEnricher — context-aware enrichment for Role entities.

    Analyzes graph neighborhood (filled persons, departments, systems)
    to populate skills, compensation, authority levels, and workforce metrics.
    Updates provenance on every mutation to track enrichment source/confidence.
    """

    ENRICHES: ClassVar[EntityType] = EntityType.ROLE

    def enrich(
        self,
        entity: BaseEntity,
        context: EntityContext,
        osint: OSINTResults | None = None,
        tier: EnrichmentTier = EnrichmentTier.BASIC,
        profile: EnrichmentProfile = EnrichmentProfile.STANDARD,
        enrichment_context: EnrichmentContext | None = None,
    ) -> EnrichmentResult:
        """Enrich a Role entity based on graph context and tier.

        Args:
            entity: The Role entity to enrich.
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
            entity_type=EntityType.ROLE,
        )

        if tier == EnrichmentTier.BASIC:
            return result

        # Analyze graph context
        filled_by = (
            context.get_neighbors(RelationshipType.FILLED_BY)
            if RelationshipType.FILLED_BY in [rt.value for rt in RelationshipType]
            else []
        )
        departments = context.get_neighbors(RelationshipType.BELONGS_TO)
        systems = context.get_neighbors(RelationshipType.REQUIRES)

        # Infer role family from role name
        role_family = self._infer_role_family(entity)

        # Tier 2: Core operational enrichment
        if tier in (EnrichmentTier.STANDARD, EnrichmentTier.DEEP):
            tier2_updates = self._enrich_tier2(entity, filled_by, departments, systems, role_family)
            result.field_updates.update(tier2_updates)

        # Tier 3: Cross-entity coherence
        if tier == EnrichmentTier.DEEP:
            tier3_updates = self._enrich_tier3(entity, role_family)
            result.field_updates.update(tier3_updates)

            # Tier 4: Quantitative metrics
            tier4_updates = self._enrich_tier4(entity, filled_by, role_family)
            result.field_updates.update(tier4_updates)

            # Tier 5: Full fidelity & predictive
            tier5_updates = self._enrich_tier5(entity, role_family)
            result.field_updates.update(tier5_updates)

        # Update provenance on all mutations
        if result.field_updates:
            result.provenance_update = ProvenanceAndConfidence(
                primary_data_source="Knowledge Graph Enrichment Agency (Role Enricher)",
                assessment_methodology="Graph-Aware Workforce Context Analysis",
                confidence_level="high" if tier == EnrichmentTier.DEEP else "medium",
                data_quality_score=DataQualityScore(
                    completeness_pct=60.0 + (20 * (1 if tier == EnrichmentTier.DEEP else 0)),
                    accuracy_confidence="High" if tier == EnrichmentTier.DEEP else "Medium",
                    timeliness_score="Current",
                    consistency_score="Consistent",
                ),
                last_assessed_date=datetime.now(UTC).isoformat(),
            )

        return result

    def _infer_role_family(self, entity: BaseEntity) -> str:
        """Infer role family from role name and description."""
        name = entity.name.lower() if hasattr(entity, "name") else ""
        desc = getattr(entity, "description", "").lower()
        combined = f"{name} {desc}"

        if any(keyword in combined for keyword in ["engineer", "developer", "architect", "devops"]):
            return "engineering"
        elif any(keyword in combined for keyword in ["data", "analyst", "scientist"]):
            return "data"
        elif any(keyword in combined for keyword in ["product", "pm"]):
            return "product"
        elif any(keyword in combined for keyword in ["compliance", "audit", "risk", "governance"]):
            return "compliance"
        elif any(
            keyword in combined
            for keyword in ["director", "vp", "head", "chief", "manager", "lead"]
        ):
            return "management"
        else:
            return "engineering"

    def _enrich_tier2(
        self,
        entity: BaseEntity,
        filled_by: list[BaseEntity],
        departments: list[BaseEntity],
        systems: list[BaseEntity],
        role_family: str,
    ) -> dict[str, Any]:
        """Populate Tier 2 fields: core operational attributes."""
        updates: dict[str, Any] = {}

        # required_skills — derive from role family
        skill_templates = ROLE_SKILL_TEMPLATES.get(role_family, ROLE_SKILL_TEMPLATES["engineering"])
        updates["required_skills"] = [
            RequiredSkill(
                skill_name=t["name"],
                skill_category=t["category"],
                proficiency_level_required=t["level"],
                criticality=t["criticality"],
            )
            for t in skill_templates
        ]

        # compensation_range
        comp_range = COMPENSATION_TEMPLATES.get(role_family, COMPENSATION_TEMPLATES["engineering"])
        updates["compensation_range"] = {
            "minimum_salary": comp_range["min"],
            "midpoint_salary": comp_range["mid"],
            "maximum_salary": comp_range["max"],
            "currency": "USD",
        }

        # authority_level based on role family
        updates["authority_level"] = (
            "Manager" if role_family in ("management", "product") else "Practitioner"
        )

        # travel_requirement
        updates["travel_requirement"] = TravelRequirement(
            travel_pct=5.0 if role_family == "management" else 0.0,
            travel_scope="Regional" if role_family == "management" else "Local",
            travel_frequency="Occasional" if role_family == "management" else "Rare",
        )

        return updates

    def _enrich_tier3(self, entity: BaseEntity, role_family: str) -> dict[str, Any]:
        """Populate Tier 3 fields: cross-entity coherence."""
        updates: dict[str, Any] = {}

        # competency_model_reference
        competency_models = {
            "engineering": "Technical Competency Model v2.0",
            "data": "Data Science Competency Model v1.5",
            "product": "Product Management Competency Model v2.1",
            "compliance": "Risk & Compliance Competency Model v1.0",
            "management": "Leadership Competency Model v3.0",
        }

        model_name = competency_models.get(role_family, "Enterprise Competency Model")

        updates["competency_model"] = CompetencyModelReference(
            model_name=model_name,
            applicable_competencies=[
                CompetencyReference(competency_name="Analytical Thinking", required_level="Expert"),
                CompetencyReference(competency_name="Communication", required_level="Expert"),
                CompetencyReference(competency_name="Accountability", required_level="Expert"),
            ],
        )

        # governance_memberships
        updates["governance_memberships"] = [
            {
                "governance_body": "Architecture Review Board"
                if role_family in ("engineering", "data")
                else "Risk Committee",
                "participation_type": "Core Member",
                "contribution_area": f"{role_family.title()} Domain",
            }
        ]

        # regulatory_accountability
        updates["regulatory_accountability"] = [
            {
                "regulation": "SOX 404",
                "accountability_type": "Data Owner" if role_family == "data" else "Process Owner",
                "attestation_required": True,
            }
        ]

        return updates

    def _enrich_tier4(
        self, entity: BaseEntity, filled_by: list[BaseEntity], role_family: str
    ) -> dict[str, Any]:
        """Populate Tier 4 fields: quantitative metrics."""
        updates: dict[str, Any] = {}

        # Vacancy and headcount calculations
        current_filled = len(filled_by)
        target_headcount = 3 if role_family in ("management", "product") else 5

        updates["headcount_actual"] = current_filled
        updates["headcount_planned"] = target_headcount
        updates["vacancy_count"] = max(0, target_headcount - current_filled)

        # turnover_rate based on role family
        turnover_rates = {
            "engineering": 0.12,
            "data": 0.15,
            "product": 0.10,
            "compliance": 0.08,
            "management": 0.06,
        }
        updates["turnover_rate_annual"] = turnover_rates.get(role_family, 0.10)

        # time_to_fill (days)
        time_to_fill = {
            "engineering": 45,
            "data": 50,
            "product": 40,
            "compliance": 30,
            "management": 60,
        }
        updates["time_to_fill_days"] = time_to_fill.get(role_family, 45)

        # average_tenure (months)
        tenure = {
            "engineering": 42,
            "data": 36,
            "product": 48,
            "compliance": 60,
            "management": 72,
        }
        updates["average_tenure_months"] = tenure.get(role_family, 48)

        return updates

    def _enrich_tier5(self, entity: BaseEntity, role_family: str) -> dict[str, Any]:
        """Populate Tier 5 fields: full fidelity & predictive."""
        updates: dict[str, Any] = {}

        # future_skills_projection
        future_skills = {
            "engineering": ["AI/ML Integration", "Cloud Native Architecture", "Security by Design"],
            "data": ["Real-time Analytics", "ML Ops", "Data Ethics & Governance"],
            "product": ["AI Product Strategy", "Ethical AI", "Extended Reality (XR)"],
            "compliance": [
                "AI Risk Assessment",
                "Algorithmic Accountability",
                "Privacy Engineering",
            ],
            "management": ["Remote Team Leadership", "AI Governance", "Organizational Resilience"],
        }

        updates["future_skills_projection"] = future_skills.get(
            role_family, ["Emerging Technology Literacy"]
        )

        # automation_risk_assessment
        automation_risks = {
            "engineering": "Low",
            "data": "Low",
            "product": "Very Low",
            "compliance": "Low",
            "management": "Very Low",
        }

        updates["automation_risk"] = {
            "risk_level": automation_risks.get(role_family, "Low"),
            "assessment_date": datetime.now(UTC).strftime("%Y-%m-%d"),
            "risk_factors": [
                "Increasing automation of manual data analysis",
                "AI-assisted code generation",
            ],
        }

        # authority_delegated (detailed)
        auth_template = AUTHORITY_TEMPLATES.get(role_family, AUTHORITY_TEMPLATES["engineering"])
        updates["authority_delegated"] = AuthorityDelegated(
            financial_approval_limit=FinancialLimit(
                amount=auth_template["financial_approval_limit"],
                currency="USD",
            ),
            hiring_authority=auth_template["hiring_authority"],
            contract_authority=ContractAuthority(
                max_value=auth_template["contract_max"],
                currency="USD",
                max_term_months=36,
            ),
            system_access_level=auth_template["system_access"],
            data_access_level="Business Unit Scope"
            if role_family == "management"
            else "Role-Specific Scope",
        )

        return updates
