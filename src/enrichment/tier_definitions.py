"""Central tier definition schema mapping all 30 entity types to enrichment tiers.

This module defines which fields get populated at each enrichment tier (2-5)
for every entity type. Tier 1 represents what generators already produce
(identity and basic core fields).

Tier levels represent maturity progression:
- Tier 1: Identity only (~10-15% field population)
- Tier 2: Core operational fields (~30-40% field population)
- Tier 3: Cross-entity coherence (~50-65% field population)
- Tier 4: Quantitative metrics (~70-85% field population)
- Tier 5: Full fidelity & predictive indicators (~90%+ field population)
"""

from __future__ import annotations

# Tier metadata
TIER_NAMES = {
    1: "Initial",
    2: "Managed",
    3: "Defined",
    4: "Measured",
    5: "Optimized",
}

TIER_DESCRIPTIONS = {
    1: "Identity only. What generators produce today. (~10-15% field population)",
    2: "Core operational fields. Ownership, classifications, basic financials. (~30-40%)",
    3: "Cross-entity coherence. Framework mappings, assessment histories. (~50-65%)",
    4: "Quantitative metrics. KPIs, financial models, scorecards. (~70-85%)",
    5: "Full fidelity. Scenario analysis, predictive indicators. (~90%+)",
}


# ============================================================================
# TIER DEFINITIONS BY ENTITY TYPE
# ============================================================================
# Each entity type maps to a dict of tier -> list of field names.
# Field names correspond to actual Pydantic model attributes.
# ============================================================================

TIER_FIELDS: dict[str, dict[int, list[str]]] = {
    # ========================================================================
    # PEOPLE & ORGANIZATIONAL
    # ========================================================================
    "person": {
        1: [
            # Tier 1: Identity (what generators produce)
            "id",
            "name",
            "first_name",
            "last_name",
            "email",
            "employee_id",
            "is_active",
            "entity_type",
        ],
        2: [
            # Tier 2: Core operational fields
            "person_id",
            "person_name",
            "employment_status",
            "employment_type",
            "title",
            "location_primary",
            "organizational_unit_primary",
            "skills_inventory",
            "certifications_held",
            "education",
            "phone",
            "clearance_level",
        ],
        3: [
            # Tier 3: Cross-entity coherence
            "current_roles",
            "reporting_to",
            "dotted_line_to",
            "experience_profile",
            "training_completed",
            "background_check_status",
            "conflict_of_interest_declarations",
            "access_privileges",
            "tags",
        ],
        4: [
            # Tier 4: Quantitative & assessment metrics
            "performance_rating_current",
            "performance_rating_history",
            "performance_trajectory",
            "potential_assessment",
            "skills_gap_assessment",
            "retention_actions",
            "flight_risk",
            "regulatory_fitness",
        ],
        5: [
            # Tier 5: Full fidelity & predictive
            "development_plan",
            "career_aspirations",
            "succession_candidate_for",
            "mentors",
            "mentored_by",
            "insider_status",
            "mandatory_training_compliance",
            "acquisition_origin",
        ],
    },
    "role": {
        1: [
            # Tier 1: Identity
            "id",
            "name",
            "entity_type",
            "description",
        ],
        2: [
            # Tier 2: Core operational
            "role_family",
            "role_level",
            "required_skills",
            "required_certifications",
            "compensation_range",
            "authority_level",
            "reporting_line_reporting",
        ],
        3: [
            # Tier 3: Cross-entity coherence
            "taxonomy_lineage",
            "governance_memberships",
            "required_experience",
            "regulatory_accountability",
            "competency_model",
            "local_names",
        ],
        4: [
            # Tier 4: Quantitative metrics
            "vacancy_count",
            "headcount_planned",
            "headcount_actual",
            "average_tenure_months",
            "turnover_rate_annual",
            "time_to_fill_days",
        ],
        5: [
            # Tier 5: Predictive & scenario
            "future_skills_projection",
            "succession_readiness",
            "role_obsolescence_risk",
            "market_salary_benchmark",
            "former_names",
        ],
    },
    "department": {
        1: [
            "id",
            "name",
            "entity_type",
            "description",
        ],
        2: [
            "department_code",
            "department_type",
            "cost_center",
            "budget",
            "status",
        ],
        3: [
            "parent_department",
            "organizational_unit_id",
            "governance_structure",
            "key_metrics",
        ],
        4: [
            "headcount",
            "annual_spend",
            "revenue_attribution",
        ],
        5: [
            "strategic_roadmap",
            "organizational_health",
            "scenario_modeling",
        ],
    },
    "organizational_unit": {
        1: [
            "id",
            "name",
            "entity_type",
            "description",
        ],
        2: [
            "unit_type",
            "unit_code",
            "employee_count",
            "geographic_presence",
            "budget",
            "status",
        ],
        3: [
            "parent_unit",
            "leadership_team",
            "governance_cadence",
            "risk_factors",
            "organizational_structure",
        ],
        4: [
            "revenue_attribution",
            "cost_structure",
            "organizational_health_score",
            "key_performance_indicators",
        ],
        5: [
            "strategic_scenario_modeling",
            "future_staffing_projection",
            "capability_roadmap",
        ],
    },
    # ========================================================================
    # TECHNOLOGY
    # ========================================================================
    "system": {
        1: [
            "id",
            "name",
            "entity_type",
            "description",
        ],
        2: [
            "system_type",
            "technology_category",
            "status",
            "tech_stack",
            "authentication_mechanisms",
            "encryption_profile",
            "support_status",
        ],
        3: [
            "api_surface",
            "availability_design",
            "scalability_profile",
            "compliance_certifications",
            "security_posture",
            "data_classification",
            "version_info",
        ],
        4: [
            "cost_optimization",
            "performance_metrics",
            "incident_history",
            "availability_sla",
            "backup_status",
            "audit_findings",
        ],
        5: [
            "replacement_roadmap",
            "technical_debt_indicators",
            "business_impact_analysis",
            "future_capability_needs",
            "acquisition_source",
        ],
    },
    "network": {
        1: [
            "id",
            "name",
            "entity_type",
            "description",
        ],
        2: [
            "network_type",
            "security_zone",
            "bandwidth",
            "status",
        ],
        3: [
            "monitoring_status",
            "security_classification",
        ],
        4: [],
        5: [],
    },
    "integration": {
        1: [
            "id",
            "name",
            "entity_type",
            "description",
        ],
        2: [
            "integration_type",
            "source_systems",
            "target_systems",
            "protocol",
            "status",
        ],
        3: [
            "error_handling",
            "security_profile",
            "sla_entry",
            "data_mapping",
        ],
        4: [
            "cost_tracking",
            "monitoring_status",
            "performance_metrics",
            "reliability_score",
        ],
        5: [
            "technical_debt_indicators",
            "future_integration_roadmap",
            "automation_potential",
        ],
    },
    # ========================================================================
    # DATA ASSETS & DOMAINS
    # ========================================================================
    "data_asset": {
        1: [
            "id",
            "name",
            "entity_type",
            "description",
        ],
        2: [
            "asset_type",
            "classification",
            "storage_technology",
            "retention_period",
            "owner_person_id",
            "status",
        ],
        3: [
            "quality_dimensions",
            "lineage_sources",
            "catalog_status",
            "regulatory_applicability",
            "privacy_classification",
        ],
        4: [
            "cost_tracking",
            "privacy_impact_assessment",
            "data_quality_score",
            "access_controls",
        ],
        5: [
            "ai_training_usage",
            "monetization_potential",
            "predictive_quality_trends",
            "strategic_value_assessment",
        ],
    },
    "data_domain": {
        1: [
            "id",
            "name",
            "entity_type",
            "description",
        ],
        2: [
            "domain_owner",
            "sensitivity_flags",
            "domain_type",
            "status",
        ],
        3: [
            "governing_policies",
            "quality_targets",
            "data_steward_team",
        ],
        4: [
            "maturity_dimensions",
            "key_performance_indicators",
            "compliance_status",
        ],
        5: [
            "monetization_potential",
            "strategic_alignment",
            "future_capability_roadmap",
        ],
    },
    "data_flow": {
        1: [
            "id",
            "name",
            "entity_type",
            "description",
        ],
        2: [
            "flow_type",
            "source_system_id",
            "target_system_id",
            "frequency",
            "encryption_status",
        ],
        3: [
            "transformation_logic",
            "quality_gates",
            "data_classification",
        ],
        4: [
            "sla_entry",
            "cost_tracking",
            "performance_metrics",
            "reliability_metrics",
        ],
        5: [
            "lineage_position",
            "future_architecture_roadmap",
            "optimization_opportunities",
        ],
    },
    # ========================================================================
    # RISK & COMPLIANCE
    # ========================================================================
    "risk": {
        1: [
            "id",
            "name",
            "entity_type",
            "description",
        ],
        2: [
            "risk_category",
            "inherent_likelihood",
            "inherent_impact",
            "risk_owner",
            "status",
        ],
        3: [
            "treatment_plan",
            "control_effectiveness",
            "risk_interconnections",
            "regulatory_applicability",
        ],
        4: [
            "key_risk_indicators",
            "financial_impact_estimate",
            "loss_scenarios",
            "residual_likelihood",
            "residual_impact",
        ],
        5: [
            "predictive_indicators",
            "risk_scenarios",
            "strategic_risk_alignment",
            "external_risk_factors",
        ],
    },
    "threat": {
        1: [
            "id",
            "name",
            "entity_type",
            "description",
        ],
        2: [
            "threat_category",
            "threat_likelihood",
            "threat_severity",
            "status",
        ],
        3: [
            "taxonomy_references",
            "mitigated_by_controls",
            "affected_asset_types",
        ],
        4: [
            "historical_frequency",
            "geographic_applicability",
            "industry_relevance",
        ],
        5: [
            "seasonal_pattern",
            "predictive_model",
            "emerging_trend_assessment",
        ],
    },
    "vulnerability": {
        1: [
            "id",
            "name",
            "entity_type",
            "description",
        ],
        2: [
            "severity",
            "cve_id",
            "status",
        ],
        3: [
            "cvss_vector",
            "exploit_availability",
            "affected_systems",
        ],
        4: [
            "affected_systems_count",
            "remediation_cost_estimate",
            "remediation_complexity",
        ],
        5: [
            "remediation_timeline",
            "exposure_risk_score",
            "business_impact_assessment",
        ],
    },
    "threat_actor": {
        1: [
            "id",
            "name",
            "entity_type",
            "description",
        ],
        2: [
            "actor_type",
            "motivation",
            "actor_category",
            "status",
        ],
        3: [
            "tactics_techniques_procedures",
            "target_industries",
            "known_campaigns",
        ],
        4: [
            "sophistication_score",
            "capability_level",
            "historical_activity_count",
        ],
        5: [
            "predictive_targeting",
            "emerging_capability_assessment",
            "strategic_threat_alignment",
        ],
    },
    "incident": {
        1: [
            "id",
            "name",
            "entity_type",
            "description",
        ],
        2: [
            "incident_severity",
            "incident_status",
            "detected_at",
            "incident_type",
        ],
        3: [
            "root_cause",
            "affected_systems",
            "lessons_learned",
            "contributing_factors",
        ],
        4: [
            "financial_impact",
            "response_timeline",
            "detection_to_resolution_hours",
            "containment_effectiveness",
        ],
        5: [
            "predictive_indicators",
            "preventability_assessment",
            "trend_analysis",
        ],
    },
    "control": {
        1: [
            "id",
            "name",
            "entity_type",
            "description",
        ],
        2: [
            "control_type",
            "implementation_status",
            "control_owner",
            "status",
        ],
        3: [
            "framework_mappings",
            "effectiveness_rating",
            "testing_approach",
            "regulatory_drivers",
        ],
        4: [
            "key_performance_indicator",
            "automation_status",
            "annual_cost",
            "control_maturity_level",
        ],
        5: [
            "optimization_opportunities",
            "risk_reduction_percentage",
            "strategic_alignment",
        ],
    },
    "policy": {
        1: [
            "id",
            "name",
            "entity_type",
            "description",
        ],
        2: [
            "policy_type",
            "policy_status",
            "policy_owner",
            "version",
        ],
        3: [
            "regulatory_drivers",
            "policy_requirements",
            "applies_to_entities",
            "approval_chain",
        ],
        4: [
            "compliance_measurement",
            "exceptions_tracking",
            "audit_schedule",
            "key_performance_indicators",
        ],
        5: [
            "communication_plan",
            "training_effectiveness",
            "strategic_alignment",
        ],
    },
    "regulation": {
        1: [
            "id",
            "name",
            "entity_type",
            "description",
        ],
        2: [
            "issuing_body",
            "jurisdiction",
            "regulation_status",
            "applicability",
        ],
        3: [
            "key_requirements",
            "compliance_status",
            "affected_systems",
            "regulatory_framework",
        ],
        4: [
            "compliance_gaps",
            "remediation_status",
            "monitoring_approach",
            "audit_frequency",
        ],
        5: [
            "regulatory_change_pipeline",
            "future_impact_assessment",
            "strategic_compliance_roadmap",
        ],
    },
    # ========================================================================
    # GEOGRAPHY & LOCATIONS
    # ========================================================================
    "location": {
        1: [
            "id",
            "name",
            "entity_type",
            "description",
        ],
        2: [
            "address",
            "coordinates",
            "location_type",
            "timezone",
        ],
        3: [
            "security_zone",
        ],
        4: [],
        5: [],
    },
    "site": {
        1: [
            "id",
            "name",
            "entity_type",
            "description",
        ],
        2: [
            "site_type",
            "address",
            "physical_security_level",
            "site_status",
        ],
        3: [
            "site_capacity",
            "environmental_certifications",
            "facility_type",
        ],
        4: [
            "annual_operating_cost",
            "facility_condition_index",
            "utilization_rate",
            "space_metrics",
        ],
        5: [
            "strategic_assessment",
            "future_capacity_planning",
            "consolidation_analysis",
        ],
    },
    "geography": {
        1: [
            "id",
            "name",
            "entity_type",
            "description",
        ],
        2: [
            "region_type",
            "countries",
            "status",
        ],
        3: [
            "market_characteristics",
            "regulatory_frameworks",
        ],
        4: [
            "strategic_importance",
            "revenue_attribution",
            "headcount",
        ],
        5: [
            "growth_potential",
            "future_expansion_roadmap",
        ],
    },
    "jurisdiction": {
        1: [
            "id",
            "name",
            "entity_type",
            "description",
        ],
        2: [
            "jurisdiction_type",
            "governing_body",
            "countries",
        ],
        3: [
            "regulatory_frameworks",
            "data_residency_requirements",
            "privacy_laws",
        ],
        4: [
            "labor_law_requirements",
            "tax_requirements",
            "compliance_complexity_score",
        ],
        5: [
            "regulatory_change_pipeline",
            "business_impact_assessment",
        ],
    },
    # ========================================================================
    # BUSINESS & PRODUCTS
    # ========================================================================
    "business_capability": {
        1: [
            "id",
            "name",
            "entity_type",
            "description",
        ],
        2: [
            "capability_level",
            "maturity_level",
            "capability_owner",
            "status",
        ],
        3: [
            "supporting_systems",
            "performance_metrics",
            "enabling_processes",
        ],
        4: [
            "maturity_dimensions",
            "value_stream_alignment",
            "key_performance_indicators",
            "investment_level",
        ],
        5: [
            "strategic_scenario_modeling",
            "future_capability_roadmap",
            "competitive_advantage_assessment",
        ],
    },
    "product_portfolio": {
        1: [
            "id",
            "name",
            "entity_type",
            "description",
        ],
        2: [
            "portfolio_type",
            "portfolio_status",
        ],
        3: [
            "market_position",
            "products_count",
        ],
        4: [
            "annual_revenue",
            "profitability_metrics",
        ],
        5: [
            "strategic_alignment",
        ],
    },
    "product": {
        1: [
            "id",
            "name",
            "entity_type",
            "description",
        ],
        2: [
            "product_type",
            "lifecycle_stage",
            "product_category",
            "status",
        ],
        3: [
            "market_position",
            "regulatory_applicability",
            "supporting_systems",
        ],
        4: [
            "annual_revenue",
            "profitability_metrics",
            "quality_metrics",
            "customer_satisfaction_score",
        ],
        5: [
            "innovation_pipeline",
            "market_growth_potential",
            "strategic_roadmap",
        ],
    },
    "market_segment": {
        1: [
            "id",
            "name",
            "entity_type",
            "description",
        ],
        2: [
            "segment_type",
            "target_profile",
            "status",
        ],
        3: [
            "competitive_landscape",
            "market_characteristics",
        ],
        4: [
            "market_size_estimate",
            "growth_rate_annual",
            "market_share",
        ],
        5: [
            "predictive_trends",
            "future_opportunity_assessment",
        ],
    },
    "customer": {
        1: [
            "id",
            "name",
            "entity_type",
            "description",
        ],
        2: [
            "customer_type",
            "industry",
            "customer_status",
            "primary_contact_person_id",
        ],
        3: [
            "account_team",
            "engagement_metrics",
            "customer_segment",
        ],
        4: [
            "annual_contract_value",
            "lifetime_value_estimate",
            "profitability_score",
            "risk_assessment",
        ],
        5: [
            "predictive_churn_risk",
            "expansion_opportunity",
            "strategic_account_classification",
        ],
    },
    "contract": {
        1: [
            "id",
            "name",
            "entity_type",
            "description",
        ],
        2: [
            "contract_type",
            "contract_status",
            "contract_value",
        ],
        3: [
            "sla_entries",
            "data_handling_provisions",
            "counterparty_id",
        ],
        4: [
            "financial_terms",
            "insurance_requirements",
            "termination_provisions",
        ],
        5: [
            "renegotiation_scenarios",
            "risk_assessment",
        ],
    },
    "initiative": {
        1: [
            "id",
            "name",
            "entity_type",
            "description",
        ],
        2: [
            "initiative_type",
            "initiative_status",
            "priority",
            "initiative_owner",
        ],
        3: [
            "strategic_objectives",
            "milestones",
            "resource_requirements",
            "supporting_systems",
        ],
        4: [
            "financial_model",
            "risk_profile",
            "success_criteria",
            "key_performance_indicators",
        ],
        5: [
            "value_realization",
            "scenario_analysis",
            "business_impact_assessment",
        ],
    },
    # ========================================================================
    # VENDORS & PARTNERS
    # ========================================================================
    "vendor": {
        1: [
            "id",
            "name",
            "entity_type",
            "description",
        ],
        2: [
            "vendor_type",
            "vendor_status",
            "primary_contact_person_id",
            "headquarters_location",
        ],
        3: [
            "risk_profile",
            "cybersecurity_assessment",
            "performance_scorecard",
            "contract_terms",
        ],
        4: [
            "financial_stability",
            "total_annual_spend",
            "vendor_concentration_risk",
            "substitutability_score",
        ],
        5: [
            "strategic_value_assessment",
            "innovation_partnership_potential",
            "future_roadmap_alignment",
        ],
    },
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_tier_fields(entity_type: str, tier: int) -> list[str]:
    """Get all field names to enrich for a specific entity type at a given tier.

    Args:
        entity_type: The EntityType to query
        tier: The enrichment tier (1-5)

    Returns:
        List of field names defined for that tier, or empty list if not defined.

    Raises:
        KeyError: If entity_type is not in TIER_FIELDS
    """
    if entity_type not in TIER_FIELDS:
        raise KeyError(f"Entity type {entity_type} not found in tier definitions")

    return TIER_FIELDS[entity_type].get(tier, [])


def get_cumulative_fields(entity_type: str, max_tier: int) -> list[str]:
    """Get all field names to enrich cumulatively up to and including max_tier.

    This returns the union of all fields from tier 1 through max_tier,
    removing duplicates while preserving order.

    Args:
        entity_type: The EntityType to query
        max_tier: The maximum enrichment tier (1-5)

    Returns:
        List of all field names from tier 1 to max_tier
    """
    fields = []
    for tier in range(1, max_tier + 1):
        tier_fields = get_tier_fields(entity_type, tier)
        for field in tier_fields:
            if field not in fields:
                fields.append(field)
    return fields


def get_tier_description(tier: int) -> str:
    """Get human-readable description of a tier.

    Args:
        tier: The enrichment tier (1-5)

    Returns:
        Description string
    """
    return TIER_DESCRIPTIONS.get(tier, "Unknown tier")


def get_tier_name(tier: int) -> str:
    """Get the name of a tier.

    Args:
        tier: The enrichment tier (1-5)

    Returns:
        Tier name
    """
    return TIER_NAMES.get(tier, "Unknown")


def list_all_entity_types() -> list[str]:
    """List all entity types defined in tier definitions.

    Returns:
        List of EntityType values in definition order
    """
    return list(TIER_FIELDS.keys())


def get_entity_field_count(entity_type: str, tier: int) -> int:
    """Get the number of fields defined for an entity at a tier.

    Args:
        entity_type: The EntityType to query
        tier: The enrichment tier (1-5)

    Returns:
        Number of fields at that tier
    """
    return len(get_tier_fields(entity_type, tier))
