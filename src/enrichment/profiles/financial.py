"""FinancialEnrichmentProfile — financial services focus on risk, compliance, controls."""

from __future__ import annotations

from domain.base import EntityType
from enrichment.profiles.base import EnrichmentProfile


class FinancialEnrichmentProfile(EnrichmentProfile):
    """Enrichment profile for financial services organizations.

    Prioritizes:
    - Risk quantification and FAIR models
    - Regulatory compliance and control effectiveness
    - Control mappings to regulations and frameworks
    - Vendor risk and contract management
    - Compliance roles and audit functions

    Focus areas:
    - sox_controls: SOX 404 control alignment
    - basel_capital: Basel III capital requirements
    - sec_compliance: SEC rule alignment
    - fair_quantification: FAIR risk quantification
    - control_risk_linkage: ensuring controls map to risks

    Enrichment priority:
    Risk → Control → Regulation → Vendor → Contract → Person (compliance roles)
    """

    name: str = "FinancialEnrichmentProfile"

    def should_populate_field(self, entity_type: EntityType, field: str, tier: int) -> bool:
        """Financial profile populates risk, control, and compliance fields.

        At tier 2+: Risk likelihood/impact, control type, regulation name
        At tier 3+: Control mappings, test results, exceptions
        At tier 4+: Risk quantification, control KPIs, audit findings
        At tier 5+: Scenario analysis, capital models, forward-looking indicators
        """
        financial_fields_by_tier = {
            EntityType.RISK: {
                2: ["risk_type", "likelihood", "impact", "risk_level"],
                3: ["affected_systems", "related_controls", "owner_id"],
                4: ["quantified_loss_estimate", "fair_model_parameters"],
                5: ["scenario_analysis_results", "residual_risk_after_controls"],
            },
            EntityType.CONTROL: {
                2: ["control_type", "status", "owner_id", "framework_mapping"],
                3: ["related_risks", "test_frequency", "test_results"],
                4: ["control_maturity_level", "kpis", "deviations_count"],
                5: ["predictive_effectiveness", "optimization_opportunities"],
            },
            EntityType.REGULATION: {
                2: ["regulation_name", "jurisdiction", "status"],
                3: ["requirements_count", "related_controls", "related_risks"],
                4: ["compliance_status", "audit_findings_count"],
                5: ["enforcement_trend", "upcoming_changes"],
            },
            EntityType.VENDOR: {
                2: ["vendor_name", "vendor_type", "status", "risk_rating"],
                3: ["contract_count", "critical_services", "audit_status"],
                4: ["risk_score", "incident_history", "compliance_certifications"],
                5: ["financial_stability_score", "replacement_feasibility"],
            },
            EntityType.CONTRACT: {
                2: ["contract_type", "vendor_id", "status", "start_date", "end_date"],
                3: ["service_level_agreements", "remediation_items"],
                4: ["cost_tracking", "usage_metrics", "performance_ratings"],
                5: ["renewal_readiness", "renegotiation_recommendations"],
            },
            EntityType.PERSON: {
                2: ["title", "clearance_level", "compliance_certifications"],
                3: ["regulatory_roles", "audit_responsibilities"],
                4: ["training_completion_rate", "compliance_violations"],
                5: ["key_person_risk", "succession_readiness"],
            },
        }

        if entity_type not in financial_fields_by_tier:
            return True  # Default: populate other entity types

        tier_dict = financial_fields_by_tier[entity_type]
        for check_tier in range(2, tier + 1):
            if check_tier in tier_dict and field in tier_dict[check_tier]:
                return True
        return False

    def get_focus_areas(self) -> list[str]:
        """Financial profile focus areas."""
        return [
            "sox_controls",
            "basel_capital",
            "sec_compliance",
            "fair_quantification",
            "control_risk_linkage",
            "vendor_risk_management",
            "audit_readiness",
        ]

    def get_enrichment_priority(self) -> list[EntityType]:
        """Financial profile enrichment priority: risk first, controls second."""
        return [
            EntityType.RISK,
            EntityType.CONTROL,
            EntityType.REGULATION,
            EntityType.VENDOR,
            EntityType.CONTRACT,
            EntityType.PERSON,
            EntityType.POLICY,
            EntityType.INCIDENT,
            EntityType.SYSTEM,
            EntityType.DATA_ASSET,
            EntityType.ROLE,
            EntityType.DEPARTMENT,
            EntityType.VULNERABILITY,
            EntityType.THREAT_ACTOR,
            EntityType.NETWORK,
            EntityType.LOCATION,
        ]

    def get_osint_sources(self) -> list[str]:
        """Financial profile OSINT sources."""
        return [
            "sec_edgar",
            "fdic_databases",
            "bank_regulatory_filings",
            "sanctions_lists",
            "credit_bureau_data",
            "financial_news_feeds",
            "regulatory_action_tracking",
        ]
