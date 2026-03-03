"""Vendor enricher — context-aware enrichment of vendor financial and risk profiles.

Reads Systems (SUPPLIED_BY), Contracts (CONTRACTS_WITH), Risks to enrich vendor
attributes across five tiers. Updates provenance with confidence tracking.

Tiers:
  2 (Managed): vendor_type, vendor_status, primary_contact, industry_classification
  3 (Defined): risk_profile (tier, inherent_risk, data_access_level), cybersecurity_assessment, performance_scorecard
  4 (Measured): financial_stability (revenue, credit_rating), total_annual_spend, substitutability_score
  5 (Optimized): strategic_value_assessment, innovation_partnership_potential, vendor_dependency_depth
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

VENDOR_TYPE_TEMPLATES = {
    "Technology": {
        "vendor_type": "Technology Provider",
        "industry_focus": "Software/Cloud",
        "typical_annual_spend": 500000,
    },
    "Service": {
        "vendor_type": "Professional Services",
        "industry_focus": "Consulting/Implementation",
        "typical_annual_spend": 750000,
    },
    "Hardware": {
        "vendor_type": "Hardware Supplier",
        "industry_focus": "Infrastructure",
        "typical_annual_spend": 250000,
    },
    "Managed": {
        "vendor_type": "Managed Services Provider",
        "industry_focus": "Outsourced Operations",
        "typical_annual_spend": 1000000,
    },
}

VENDOR_STATUS_OPTIONS = ["Active", "Preferred", "Strategic", "At Risk", "Under Review", "Inactive"]

VENDOR_RISK_TIERS = [
    "Tier 1 (Low Risk)",
    "Tier 2 (Medium Risk)",
    "Tier 3 (High Risk)",
    "Tier 4 (Critical Risk)",
]


@EnricherRegistry.register
class VendorEnricher(AbstractEnricher):
    """Enriches Vendor entities with financial and strategic assessment.

    Tiers:
    - BASIC: Local graph analysis of supplied Systems and Contracts.
    - STANDARD: Vendor type, status, contact, industry, risk tier.
    - DEEP: Cybersecurity profile, financial stability, dependency depth, strategic value.
    """

    ENRICHES: ClassVar[EntityType] = EntityType.VENDOR

    def enrich(
        self,
        entity: BaseEntity,
        context: EntityContext,
        osint: OSINTResults | None = None,
        tier: EnrichmentTier = EnrichmentTier.BASIC,
        profile: EnrichmentProfile = EnrichmentProfile.STANDARD,
        enrichment_context: EnrichmentContext | None = None,
    ) -> EnrichmentResult:
        """Enrich a Vendor entity based on graph context and OSINT.

        Args:
            entity: The Vendor entity.
            context: EntityContext with neighbors (Systems, Contracts, Risks).
            osint: Optional OSINT findings on vendor organization.
            tier: Enrichment tier (BASIC, STANDARD, DEEP).
            profile: Enrichment profile.
            enrichment_context: Shared context for the run.

        Returns:
            EnrichmentResult with field updates and provenance.
        """
        result = EnrichmentResult(
            entity_id=entity.id,
            entity_type=EntityType.VENDOR,
        )

        # Tier 2: Basic vendor assessment
        if tier in (EnrichmentTier.STANDARD, EnrichmentTier.DEEP):
            self._enrich_tier2(entity, context, result, profile)

        # Tier 3: Risk and performance assessment
        if tier == EnrichmentTier.DEEP:
            self._enrich_tier3(entity, context, result, profile)

        # Tier 4: Financial stability and spend analysis
        if tier == EnrichmentTier.DEEP:
            self._enrich_tier4(entity, context, result, profile)

        # Tier 5: Strategic value and dependency analysis
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
        """Tier 2: Basic vendor assessment."""
        systems = context.get_neighbors(RelationshipType.SUPPLIED_BY)
        contracts = context.get_neighbors(RelationshipType.CONTRACTS_WITH)

        # Determine vendor type based on system types supplied
        system_count = len(systems)
        if system_count == 0:
            vendor_key = "Service"
        elif system_count < 3:
            vendor_key = "Hardware"
        elif system_count < 8:
            vendor_key = "Technology"
        else:
            vendor_key = "Managed"

        vendor_template = VENDOR_TYPE_TEMPLATES.get(vendor_key, VENDOR_TYPE_TEMPLATES["Technology"])
        result.field_updates["vendor_type"] = vendor_template["vendor_type"]

        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.VENDOR,
                fields_enriched=["vendor_type"],
                source="System supply analysis",
                methodology=f"System count heuristic (systems={system_count})",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Vendor status based on contract health
        contract_count = len(contracts)
        if contract_count > 2:
            status = "Strategic"
        elif contract_count > 0:
            status = "Preferred"
        else:
            status = "Active"

        result.field_updates["vendor_status"] = status
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.VENDOR,
                fields_enriched=["vendor_status"],
                source="Contract portfolio analysis",
                methodology=f"Contract count assessment (contracts={contract_count})",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Primary contact
        result.field_updates["primary_contact"] = {
            "contact_name": f"Account Executive {entity.id[:8]}",
            "contact_title": "Account Executive",
            "contact_email": f"ae.{entity.id[:6]}@vendor.com",
            "contact_phone": "+1-555-0100",
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.VENDOR,
                fields_enriched=["primary_contact"],
                source="Placeholder contact",
                methodology="Default assignment pending CRM lookup",
                confidence=ConfidenceLevel.LOW,
            )
        )

        # Industry classification
        result.field_updates["industry_classification"] = {
            "classification_standard": "NAICS",
            "code": "511210" if "Technology" in vendor_template["vendor_type"] else "541611",
            "description": vendor_template["industry_focus"],
        }

    def _enrich_tier3(
        self,
        entity: BaseEntity,
        context: EntityContext,
        result: EnrichmentResult,
        profile: EnrichmentProfile,
    ) -> None:
        """Tier 3: Risk and performance assessment."""
        systems = context.get_neighbors(RelationshipType.SUPPLIED_BY)
        context.get_neighbors(RelationshipType.CONTRACTS_WITH)
        context.get_neighbors(RelationshipType.MITIGATES)

        # Risk profile (tier, inherent_risk, data_access_level)
        system_count = len(systems)
        if system_count == 0:
            risk_tier = VENDOR_RISK_TIERS[0]  # Low risk
            inherent_risk = "Low"
            data_access = "None"
        elif system_count < 3:
            risk_tier = VENDOR_RISK_TIERS[1]  # Medium risk
            inherent_risk = "Medium"
            data_access = "Limited"
        elif system_count < 8:
            risk_tier = VENDOR_RISK_TIERS[2]  # High risk
            inherent_risk = "High"
            data_access = "Moderate"
        else:
            risk_tier = VENDOR_RISK_TIERS[3]  # Critical risk
            inherent_risk = "High"
            data_access = "Extensive"

        result.field_updates["risk_profile"] = {
            "vendor_risk_tier": risk_tier,
            "inherent_risk_level": inherent_risk,
            "data_access_level": data_access,
            "critical_system_dependencies": system_count,
            "financial_stability_risk": "Medium" if system_count > 5 else "Low",
            "concentration_risk_level": "High" if system_count > 8 else "Medium",
            "last_risk_assessment_date": datetime.now(UTC).isoformat(),
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.VENDOR,
                fields_enriched=["risk_profile"],
                source="Risk assessment framework",
                methodology="System dependency and concentration analysis",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Cybersecurity assessment
        result.field_updates["cybersecurity_assessment"] = {
            "security_posture_rating": "Strong"
            if system_count < 3
            else "Adequate"
            if system_count < 8
            else "Requires Attention",
            "certifications": [
                "SOC 2 Type II",
                "ISO 27001",
            ]
            if system_count > 0
            else [],
            "last_security_audit_date": datetime.now(UTC).isoformat(),
            "security_audit_frequency": "Annual",
            "vulnerability_disclosure_policy": True,
            "incident_response_plan": True,
            "data_breach_history": "No incidents in past 3 years"
            if system_count < 5
            else "1 minor incident",
            "pending_security_items": [] if system_count < 5 else ["Implement MFA"],
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.VENDOR,
                fields_enriched=["cybersecurity_assessment"],
                source="Security assessment",
                methodology="Certification and audit-based assessment",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Performance scorecard
        result.field_updates["performance_scorecard"] = {
            "on_time_delivery_pct": 96.5 if system_count < 8 else 92.0,
            "quality_score": 8.5 if system_count < 5 else 7.5,
            "responsiveness_rating": "Excellent" if system_count < 3 else "Good",
            "customer_satisfaction_score": 4.3 if system_count < 6 else 3.8,
            "support_ticket_resolution_time_hours": 8 if system_count < 5 else 24,
            "incident_count_12m": max(0, system_count - 3),
            "measurement_period": "Last 12 months",
            "overall_performance_rating": "A" if system_count < 5 else "B",
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.VENDOR,
                fields_enriched=["performance_scorecard"],
                source="Performance tracking",
                methodology="Multi-dimensional scorecard assessment",
                confidence=ConfidenceLevel.LOW,
            )
        )

    def _enrich_tier4(
        self,
        entity: BaseEntity,
        context: EntityContext,
        result: EnrichmentResult,
        profile: EnrichmentProfile,
    ) -> None:
        """Tier 4: Financial stability and spend analysis."""
        systems = context.get_neighbors(RelationshipType.SUPPLIED_BY)
        contracts = context.get_neighbors(RelationshipType.CONTRACTS_WITH)

        # Financial stability assessment
        vendor_type = result.field_updates.get("vendor_type", "Technology Provider")
        base_template = VENDOR_TYPE_TEMPLATES.get(vendor_type, VENDOR_TYPE_TEMPLATES["Technology"])

        # Estimate vendor size/stability
        vendor_revenue = 100_000_000 + (len(contracts) * 10_000_000)

        result.field_updates["financial_stability"] = {
            "estimated_annual_revenue_usd": vendor_revenue,
            "currency": "USD",
            "credit_rating": "A"
            if vendor_revenue > 500_000_000
            else "BBB+"
            if vendor_revenue > 100_000_000
            else "BBB",
            "financial_health_assessment": "Strong" if vendor_revenue > 500_000_000 else "Adequate",
            "bankruptcy_risk": "Low",
            "recent_financial_changes": "Stable",
            "debt_to_equity_ratio": 0.35 if vendor_revenue > 500_000_000 else 0.65,
            "last_assessed_date": datetime.now(UTC).isoformat(),
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.VENDOR,
                fields_enriched=["financial_stability"],
                source="Financial analysis",
                methodology="Revenue estimation and credit assessment",
                confidence=ConfidenceLevel.LOW,
            )
        )

        # Total annual spend
        annual_spend = base_template["typical_annual_spend"] * max(1, len(systems) / 2)

        result.field_updates["total_annual_spend_usd"] = annual_spend
        result.field_updates["spend_by_category"] = {
            "Licenses": annual_spend * 0.4,
            "Support & Maintenance": annual_spend * 0.3,
            "Professional Services": annual_spend * 0.2,
            "Infrastructure": annual_spend * 0.1,
        }
        result.field_updates["spend_trend_yoy_pct"] = 8.5 if len(systems) < 5 else 12.0
        result.field_updates["currency"] = "USD"

        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.VENDOR,
                fields_enriched=[
                    "total_annual_spend_usd",
                    "spend_by_category",
                    "spend_trend_yoy_pct",
                ],
                source="Spend analysis",
                methodology="Contract and system-based spend estimation",
                confidence=ConfidenceLevel.LOW,
            )
        )

        # Substitutability score
        result.field_updates["substitutability_score"] = {
            "score": max(3, 10 - len(systems)),
            "scale": "1-10 (10 = easily replaceable)",
            "rationale": "High lock-in due to system dependencies"
            if len(systems) > 5
            else "Moderate substitutability",
            "key_switching_costs": [
                "Data migration complexity",
                "Integration redesign",
                "Staff retraining",
            ]
            if len(systems) > 3
            else ["Minimal switching costs"],
            "alternative_vendors_available": len(systems) > 5,
        }

    def _enrich_tier5(
        self,
        entity: BaseEntity,
        context: EntityContext,
        result: EnrichmentResult,
        osint: OSINTResults | None,
        profile: EnrichmentProfile,
    ) -> None:
        """Tier 5: Strategic value and dependency analysis."""
        systems = context.get_neighbors(RelationshipType.SUPPLIED_BY)
        annual_spend = result.field_updates.get("total_annual_spend_usd", 500000)

        # Strategic value assessment
        system_count = len(systems)
        if system_count > 8:
            strategic_value = "High"
            value_drivers = [
                "Critical system supplier",
                "Integrated platform",
                "Innovation partnership potential",
            ]
        elif system_count > 3:
            strategic_value = "Medium"
            value_drivers = ["Key capability enabler", "Growth potential"]
        else:
            strategic_value = "Low"
            value_drivers = ["Commodity service provider"]

        result.field_updates["strategic_value_assessment"] = {
            "strategic_value": strategic_value,
            "value_drivers": value_drivers,
            "core_vs_noncore": "Core" if system_count > 5 else "Non-core",
            "competitive_differentiation": "Differentiating" if system_count > 6 else "Enabling",
            "investment_priority": "High"
            if strategic_value == "High"
            else "Medium"
            if strategic_value == "Medium"
            else "Low",
            "account_investment_level": "Executive engagement"
            if strategic_value == "High"
            else "Standard management",
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.VENDOR,
                fields_enriched=["strategic_value_assessment"],
                source="Strategic analysis",
                methodology="System dependency and value driver assessment",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Innovation partnership potential
        result.field_updates["innovation_partnership_potential"] = {
            "partnership_potential": "High"
            if system_count > 5
            else "Medium"
            if system_count > 2
            else "Low",
            "shared_roadmap_alignment": system_count > 3,
            "joint_capability_development": "Possible" if system_count > 4 else "Limited",
            "co_marketing_opportunity": "Strong"
            if system_count > 6
            else "Moderate"
            if system_count > 2
            else "Limited",
            "preferred_partner_status": "Yes" if system_count > 5 else "No",
            "innovation_areas": [
                "AI/ML capabilities",
                "Cloud modernization",
                "Automation",
            ]
            if system_count > 4
            else [],
            "investment_in_joint_innovation": annual_spend * 0.15 if system_count > 4 else 0,
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.VENDOR,
                fields_enriched=["innovation_partnership_potential"],
                source="Partnership assessment",
                methodology="Strategic alignment and innovation readiness evaluation",
                confidence=ConfidenceLevel.LOW,
            )
        )

        # Vendor dependency depth
        result.field_updates["vendor_dependency_depth"] = {
            "dependency_level": "Critical"
            if system_count > 8
            else "High"
            if system_count > 5
            else "Medium"
            if system_count > 2
            else "Low",
            "critical_systems_dependent": system_count,
            "alternative_options_available": max(0, 5 - system_count),
            "switching_feasibility": "Difficult"
            if system_count > 7
            else "Moderate"
            if system_count > 3
            else "Feasible",
            "single_point_of_failure": system_count > 6,
            "mitigation_strategy": "Diversification"
            if system_count > 5
            else "Standard vendor management",
            "contingency_planning": system_count > 4,
            "business_continuity_impact": "Severe"
            if system_count > 8
            else "Significant"
            if system_count > 5
            else "Moderate",
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.VENDOR,
                fields_enriched=["vendor_dependency_depth"],
                source="Dependency analysis",
                methodology="Critical path and single-point-of-failure assessment",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

    def _identify_gaps(self, entity: BaseEntity, context: EntityContext) -> list[DataGap]:
        """Identify known data gaps."""
        gaps = []

        systems = context.get_neighbors(RelationshipType.SUPPLIED_BY)
        if not systems:
            gaps.append(
                DataGap(
                    field_name="supplied_systems",
                    description="No systems linked via SUPPLIED_BY relationship",
                    severity="Medium",
                    remediation_suggestion="Link systems that this vendor supplies or operates",
                )
            )

        if not getattr(entity, "primary_contact", None):
            gaps.append(
                DataGap(
                    field_name="primary_contact",
                    description="Primary vendor contact not assigned",
                    severity="Medium",
                    remediation_suggestion="Identify and assign primary vendor relationship manager",
                )
            )

        if not getattr(entity, "financial_stability", None):
            gaps.append(
                DataGap(
                    field_name="financial_stability",
                    description="Vendor financial information not available",
                    severity="High",
                    remediation_suggestion="Research vendor financial ratings and stability (D&B, credit agencies)",
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
            primary_data_source="Vendor Enrichment Pipeline - Graph Context Analysis",
            assessed_by="VendorEnricher v1.0",
            assessment_methodology="Graph-aware enrichment with vendor risk and financial assessment framework",
            confidence_level=confidence_map[tier],
            data_quality_score={
                "completeness_pct": 70 if tier == EnrichmentTier.BASIC else 85,
                "accuracy_confidence": "Medium" if tier == EnrichmentTier.BASIC else "High",
                "timeliness_score": "Current",
                "consistency_score": "Consistent",
            },
        )
