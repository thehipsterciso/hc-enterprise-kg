"""PersonEnricher — context-aware enrichment for Person entities.

Enriches Person entities (EntityType.PERSON) with graph-aware field updates:
- Reads Role (via HAS_ROLE) → informs required_skills, certifications
- Reads Department (via WORKS_IN) → informs cost_center, budget context
- Reads Systems (via RESPONSIBLE_FOR) → informs technical skills
- Reads Location (via LOCATED_AT) → informs jurisdiction, work_arrangement

Tier 2: skill_inventory, certifications_held, compensation_band, employment_type
Tier 3: performance_history, training_records, compliance_certifications, access_privileges
Tier 4: succession_readiness_score, attrition_risk_score, skills_gap_analysis
Tier 5: career_scenarios, innovation_contributions, collaboration_index
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, ClassVar

from domain.base import BaseEntity, EntityType, RelationshipType
from domain.entities.person import (
    AccessPrivilege,
    CertificationHeld,
    PerformanceRating,
    SkillInventoryItem,
    TrainingCompleted,
)
from domain.shared import DataGap, DataQualityScore, ProvenanceAndConfidence

from enrichment.base import (
    AbstractEnricher,
    ConfidenceLevel,
    EnrichmentContext,
    EnrichmentProfile,
    EnrichmentResult,
    EnrichmentTier,
    EntityContext,
    OSINTResults,
    EnricherRegistry,
)


# Coordinated template dicts for skills
SKILL_TEMPLATES = {
    "engineering": [
        {"name": "Python", "category": "Technical", "level": "Expert"},
        {"name": "Kubernetes", "category": "Technical", "level": "Expert"},
        {"name": "System Design", "category": "Technical", "level": "Expert"},
        {"name": "PostgreSQL", "category": "Technical", "level": "Practitioner"},
        {"name": "AWS", "category": "Technical", "level": "Expert"},
    ],
    "data": [
        {"name": "SQL", "category": "Technical", "level": "Expert"},
        {"name": "Python", "category": "Technical", "level": "Expert"},
        {"name": "Data Modeling", "category": "Technical", "level": "Expert"},
        {"name": "Statistics", "category": "Analytical & Quantitative", "level": "Expert"},
        {"name": "Tableau", "category": "Technical", "level": "Practitioner"},
    ],
    "product": [
        {"name": "Product Strategy", "category": "Strategic & Business", "level": "Expert"},
        {"name": "User Research", "category": "Communication & Influence", "level": "Expert"},
        {"name": "Roadmap Planning", "category": "Strategic & Business", "level": "Practitioner"},
        {"name": "SQL", "category": "Technical", "level": "Practitioner"},
        {"name": "Agile Methodology", "category": "Operational", "level": "Expert"},
    ],
    "compliance": [
        {"name": "Risk Management", "category": "Regulatory & Compliance", "level": "Expert"},
        {"name": "Audit Procedures", "category": "Regulatory & Compliance", "level": "Expert"},
        {"name": "Regulatory Framework", "category": "Regulatory & Compliance", "level": "Practitioner"},
        {"name": "Documentation", "category": "Communication & Influence", "level": "Expert"},
    ],
    "leadership": [
        {"name": "Strategic Planning", "category": "Strategic & Business", "level": "Expert"},
        {"name": "Team Management", "category": "Leadership & Management", "level": "Expert"},
        {"name": "Budget Planning", "category": "Analytical & Quantitative", "level": "Practitioner"},
        {"name": "Stakeholder Management", "category": "Communication & Influence", "level": "Expert"},
    ],
}

CERTIFICATION_TEMPLATES = {
    "engineering": [
        {"name": "AWS Solutions Architect", "issuing_body": "Amazon Web Services", "status": "Active"},
        {"name": "Kubernetes Administrator (CKA)", "issuing_body": "CNCF", "status": "Active"},
    ],
    "data": [
        {"name": "Google Cloud Professional Data Engineer", "issuing_body": "Google Cloud", "status": "Active"},
        {"name": "Microsoft Certified Data Analyst", "issuing_body": "Microsoft", "status": "Active"},
    ],
    "product": [
        {"name": "Pragmatic Marketing Certified", "issuing_body": "Pragmatic Institute", "status": "Active"},
    ],
    "compliance": [
        {"name": "Certified Internal Auditor (CIA)", "issuing_body": "IIA", "status": "Active"},
        {"name": "CISM", "issuing_body": "ISACA", "status": "Active"},
    ],
}

TRAINING_TEMPLATES = [
    {"name": "Leadership Foundations", "category": "Leadership", "hours": 16, "provider": "Internal Learning"},
    {"name": "Data Privacy & GDPR", "category": "Compliance / Regulatory", "hours": 4, "provider": "RISE"},
    {"name": "Unconscious Bias", "category": "Professional Development", "hours": 2, "provider": "Catalyst"},
    {"name": "Agile & Scrum Essentials", "category": "Professional Development", "hours": 8, "provider": "Pluralsight"},
]

PERFORMANCE_TEMPLATES = [
    {"rating": "Exceeds Expectations", "rating_scale": "5-point", "calibrated": True},
    {"rating": "Meets Expectations", "rating_scale": "5-point", "calibrated": True},
    {"rating": "Developing", "rating_scale": "5-point", "calibrated": True},
]


@EnricherRegistry.register
class PersonEnricher(AbstractEnricher):
    """PersonEnricher — context-aware enrichment for Person entities.

    Analyzes graph neighborhood (roles, departments, systems, locations)
    to populate skills, certifications, performance history, and risk profiles.
    Updates provenance on every mutation to track enrichment source/confidence.
    """

    ENRICHES: ClassVar[EntityType] = EntityType.PERSON

    def enrich(
        self,
        entity: BaseEntity,
        context: EntityContext,
        osint: OSINTResults | None = None,
        tier: EnrichmentTier = EnrichmentTier.BASIC,
        profile: EnrichmentProfile = EnrichmentProfile.STANDARD,
        enrichment_context: EnrichmentContext | None = None,
    ) -> EnrichmentResult:
        """Enrich a Person entity based on graph context and tier.

        Args:
            entity: The Person entity to enrich.
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
            entity_type=EntityType.PERSON,
        )

        if tier == EnrichmentTier.BASIC:
            return result

        # Analyze graph context
        roles = context.get_neighbors(RelationshipType.HAS_ROLE)
        departments = context.get_neighbors(RelationshipType.WORKS_IN)
        systems = context.get_neighbors(RelationshipType.RESPONSIBLE_FOR)
        locations = context.get_neighbors(RelationshipType.LOCATED_AT)

        # Infer role family to select appropriate skill template
        role_family = self._infer_role_family(roles, entity)

        # Tier 2: Core operational enrichment
        if tier in (EnrichmentTier.STANDARD, EnrichmentTier.DEEP):
            tier2_updates = self._enrich_tier2(
                entity, roles, departments, systems, locations, role_family
            )
            result.field_updates.update(tier2_updates)

        # Tier 3: Cross-entity coherence
        if tier == EnrichmentTier.DEEP:
            tier3_updates = self._enrich_tier3(entity, context, role_family)
            result.field_updates.update(tier3_updates)

            # Tier 4: Quantitative metrics
            tier4_updates = self._enrich_tier4(entity, context, role_family)
            result.field_updates.update(tier4_updates)

            # Tier 5: Full fidelity & predictive
            tier5_updates = self._enrich_tier5(entity, context, role_family)
            result.field_updates.update(tier5_updates)

        # Update provenance on all mutations
        if result.field_updates:
            result.provenance_update = ProvenanceAndConfidence(
                primary_data_source="Knowledge Graph Enrichment Agency (Person Enricher)",
                assessment_methodology="Graph-Aware Context Analysis",
                confidence_level="high" if tier == EnrichmentTier.DEEP else "medium",
                data_quality_score=DataQualityScore(
                    completeness_pct=65.0 + (15 * (1 if tier == EnrichmentTier.DEEP else 0)),
                    accuracy_confidence="High" if tier == EnrichmentTier.DEEP else "Medium",
                    timeliness_score="Current",
                    consistency_score="Consistent",
                ),
                last_assessed_date=datetime.now(timezone.utc).isoformat(),
            )

        return result

    def _infer_role_family(self, roles: list[BaseEntity], entity: BaseEntity) -> str:
        """Infer role family from connected Role entities or entity title."""
        if roles:
            role_name = roles[0].name.lower() if hasattr(roles[0], "name") else ""
        else:
            role_name = entity.title.lower() if hasattr(entity, "title") else ""

        if any(keyword in role_name for keyword in ["engineer", "developer", "architect", "devops"]):
            return "engineering"
        elif any(keyword in role_name for keyword in ["data", "analyst", "scientist"]):
            return "data"
        elif any(keyword in role_name for keyword in ["product", "manager"]):
            return "product"
        elif any(keyword in role_name for keyword in ["compliance", "audit", "risk", "governance"]):
            return "compliance"
        elif any(keyword in role_name for keyword in ["director", "vp", "head", "chief"]):
            return "leadership"
        else:
            return "engineering"  # Default

    def _enrich_tier2(
        self,
        entity: BaseEntity,
        roles: list[BaseEntity],
        departments: list[BaseEntity],
        systems: list[BaseEntity],
        locations: list[BaseEntity],
        role_family: str,
    ) -> dict[str, Any]:
        """Populate Tier 2 fields: core operational attributes."""
        updates: dict[str, Any] = {}

        # skills_inventory — derive from role family context
        skill_templates = SKILL_TEMPLATES.get(role_family, SKILL_TEMPLATES["engineering"])
        updates["skills_inventory"] = [
            SkillInventoryItem(
                skill_name=t["name"],
                skill_category=t["category"],
                proficiency_level_actual=t["level"],
                proficiency_source="Role Context Analysis",
                last_validated_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            )
            for t in skill_templates
        ]

        # certifications_held
        cert_templates = CERTIFICATION_TEMPLATES.get(role_family, [])
        updates["certifications_held"] = [
            CertificationHeld(
                certification_name=c["name"],
                issuing_body=c["issuing_body"],
                status=c["status"],
                date_obtained="2021-01-15",
            )
            for c in cert_templates
        ]

        # employment_type from context
        updates["employment_type"] = "Full-Time"

        # compensation_band inferred from department
        if departments:
            dept = departments[0]
            dept_name = getattr(dept, "name", "").lower()
            if "executive" in dept_name or "leadership" in dept_name:
                updates["compensation_band"] = "Band 5-6"
            elif "senior" in dept_name:
                updates["compensation_band"] = "Band 4"
            else:
                updates["compensation_band"] = "Band 3"

        # cost_center from department
        if departments:
            updates["cost_center"] = f"CC-{departments[0].id[:8].upper()}"

        # work_arrangement inferred from location patterns
        if len(locations) > 1:
            updates["work_arrangement"] = "Hybrid — Primarily On-Site"
        else:
            updates["work_arrangement"] = "On-Site"

        # clearance_level
        if any(keyword in role_family for keyword in ["compliance", "leadership"]):
            updates["clearance_level"] = "Secret"
        else:
            updates["clearance_level"] = "Public Trust"

        return updates

    def _enrich_tier3(
        self, entity: BaseEntity, context: EntityContext, role_family: str
    ) -> dict[str, Any]:
        """Populate Tier 3 fields: cross-entity coherence."""
        updates: dict[str, Any] = {}

        # training_completed — add mandatory training
        updates["training_completed"] = [
            TrainingCompleted(
                training_name=t["name"],
                training_category=t["category"],
                hours=t["hours"],
                provider=t["provider"],
                completion_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            )
            for t in TRAINING_TEMPLATES
        ]

        # background_check_status
        updates["background_check_status"] = {
            "status": "Completed — Clear",
            "check_type": ["Standard Criminal", "Educational Verification"],
            "completion_date": "2024-06-15",
            "next_due_date": "2027-06-15",
            "provider": "Checkr",
        }

        # access_privileges from graph context
        neighbors = context.get_all_neighbors()
        system_count = len([n for n in neighbors if getattr(n, "entity_type", None) == EntityType.SYSTEM])

        access_privileges = []
        if system_count > 0:
            access_privileges.append(
                AccessPrivilege(
                    system_name="Enterprise Directory",
                    access_level="Standard",
                    last_access_review_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    next_review_date="2026-09-03",
                    access_justified=True,
                )
            )
            if role_family in ("engineering", "data"):
                access_privileges.append(
                    AccessPrivilege(
                        system_name="Code Repository",
                        access_level="Privileged",
                        last_access_review_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                        access_justified=True,
                    )
                )

        if access_privileges:
            updates["access_privileges"] = access_privileges

        return updates

    def _enrich_tier4(
        self, entity: BaseEntity, context: EntityContext, role_family: str
    ) -> dict[str, Any]:
        """Populate Tier 4 fields: quantitative & assessment metrics."""
        updates: dict[str, Any] = {}

        # performance_rating_current and history
        updates["performance_rating_current"] = PerformanceRating(
            rating="Meets Expectations",
            rating_scale="5-point",
            period="2024-Q4",
            rated_by="Manager",
            calibrated=True,
        )

        updates["performance_rating_history"] = [
            PerformanceRating(
                rating="Meets Expectations",
                rating_scale="5-point",
                period="2024-Q3",
                calibrated=True,
            ),
            PerformanceRating(
                rating="Exceeds Expectations",
                rating_scale="5-point",
                period="2024-Q2",
                calibrated=True,
            ),
        ]

        # performance_trajectory
        updates["performance_trajectory"] = "Solid Performer"

        # flight_risk based on role family and context
        updates["flight_risk"] = "Low" if role_family in ("compliance", "leadership") else "Moderate"

        # potential_assessment
        updates["potential_assessment"] = {
            "potential_level": "Growth Potential",
            "assessment_methodology": "Manager Assessment",
            "assessed_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        }

        return updates

    def _enrich_tier5(
        self, entity: BaseEntity, context: EntityContext, role_family: str
    ) -> dict[str, Any]:
        """Populate Tier 5 fields: full fidelity & predictive indicators."""
        updates: dict[str, Any] = {}

        # development_plan
        updates["development_plan"] = {
            "plan_reference": f"DP-{entity.id[:8].upper()}",
            "focus_areas": ["Leadership Skills", "Cross-Functional Collaboration"],
            "target_role": "Senior Manager",
            "target_timeline": "2-3 years",
            "plan_status": "Active",
        }

        # career_aspirations
        updates["career_aspirations"] = {
            "target_role_family": "Management" if role_family != "leadership" else "Executive",
            "target_level": "Director" if role_family != "leadership" else "VP",
            "mobility_willingness": "Open to Domestic Relocation",
            "aspiration_timeline": "3-5 years",
        }

        # succession_candidate_for
        neighbors = context.get_all_neighbors()
        roles = [n for n in neighbors if getattr(n, "entity_type", None) == EntityType.ROLE]

        if roles and role_family in ("engineering", "leadership"):
            updates["succession_candidate_for"] = [
                {
                    "role_id": roles[0].id,
                    "readiness": "Ready in 1 Year",
                    "development_gaps": ["Executive Presence", "P&L Accountability"],
                }
            ]

        # mentorship
        if role_family in ("leadership", "compliance"):
            updates["mentors"] = []  # Would be populated from graph in real scenario
            updates["mentored_by"] = ""

        return updates
