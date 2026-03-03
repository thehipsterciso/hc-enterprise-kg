"""HealthcareEnrichmentProfile — healthcare focus on data classification, regulations, privacy."""

from __future__ import annotations

from domain.base import EntityType
from enrichment.profiles.base import EnrichmentProfile


class HealthcareEnrichmentProfile(EnrichmentProfile):
    """Enrichment profile for healthcare organizations.

    Prioritizes:
    - Data classification and PHI/PII inventory
    - Data domain governance and residency requirements
    - HIPAA and privacy regulations
    - Consent and privacy control effectiveness
    - Clinical roles and patient safety

    Focus areas:
    - hipaa_compliance: HIPAA rule alignment
    - fda_regulations: FDA guidance adherence
    - phi_classification: Protected Health Information inventory
    - hitrust_framework: HITRUST CSF alignment
    - data_residency: geographic data residency requirements
    - consent_management: patient consent tracking

    Enrichment priority:
    DataAsset → DataDomain → Regulation → Control → Policy → Person (clinical roles)
    """

    name: str = "HealthcareEnrichmentProfile"

    def should_populate_field(self, entity_type: EntityType, field: str, tier: int) -> bool:
        """Healthcare profile populates data classification and privacy fields.

        At tier 2+: Data asset classification, data domain ownership, policy assignment
        At tier 3+: PHI mappings, consent tracking, assessment history
        At tier 4+: Data inventory completeness, compliance gaps, breach history
        At tier 5+: Privacy impact assessments, predictive compliance indicators
        """
        healthcare_fields_by_tier = {
            EntityType.DATA_ASSET: {
                2: ["name", "owner_id", "classification", "contains_phi"],
                3: ["residency_requirement", "consent_requirements", "retention_period"],
                4: ["data_discovery_date", "inventory_completeness", "breach_history"],
                5: ["privacy_impact_assessment", "de_identification_feasibility"],
            },
            EntityType.DATA_DOMAIN: {
                2: ["domain_name", "owner_id", "steward_id"],
                3: ["related_regulations", "consent_model"],
                4: ["data_asset_count", "quality_metrics"],
                5: ["strategic_importance", "modernization_status"],
            },
            EntityType.REGULATION: {
                2: ["regulation_name", "jurisdiction", "status"],
                3: ["key_requirements", "audit_frequency"],
                4: ["compliance_status", "audit_findings"],
                5: ["enforcement_trend", "upcoming_changes"],
            },
            EntityType.CONTROL: {
                2: ["control_type", "status", "owner_id"],
                3: ["related_regulations", "related_data_assets"],
                4: ["control_maturity_level", "test_results"],
                5: ["effectiveness_trends", "optimization_recommendations"],
            },
            EntityType.POLICY: {
                2: ["policy_name", "policy_type", "status"],
                3: ["related_regulations", "covered_data_domains"],
                4: ["training_count", "violation_count"],
                5: ["policy_effectiveness_score", "update_recommendations"],
            },
            EntityType.PERSON: {
                2: ["title", "role", "clinical_role"],
                3: ["hipaa_training_status", "clinical_credentials"],
                4: ["patient_contact_count", "privacy_violations"],
                5: ["patient_safety_incidents", "key_person_risk"],
            },
        }

        if entity_type not in healthcare_fields_by_tier:
            return True  # Default: populate other entity types

        tier_dict = healthcare_fields_by_tier[entity_type]
        for check_tier in range(2, tier + 1):
            if check_tier in tier_dict and field in tier_dict[check_tier]:
                return True
        return False

    def get_focus_areas(self) -> list[str]:
        """Healthcare profile focus areas."""
        return [
            "hipaa_compliance",
            "fda_regulations",
            "phi_classification",
            "hitrust_framework",
            "data_residency",
            "consent_management",
            "patient_safety",
            "clinical_documentation",
        ]

    def get_enrichment_priority(self) -> list[EntityType]:
        """Healthcare profile enrichment priority: data assets and domains first."""
        return [
            EntityType.DATA_ASSET,
            EntityType.DATA_DOMAIN,
            EntityType.REGULATION,
            EntityType.CONTROL,
            EntityType.POLICY,
            EntityType.PERSON,
            EntityType.VENDOR,
            EntityType.SYSTEM,
            EntityType.RISK,
            EntityType.CONTRACT,
            EntityType.INCIDENT,
            EntityType.ROLE,
            EntityType.DEPARTMENT,
            EntityType.DATA_FLOW,
            EntityType.LOCATION,
            EntityType.NETWORK,
        ]

    def get_osint_sources(self) -> list[str]:
        """Healthcare profile OSINT sources."""
        return [
            "hipaa_breach_notification_list",
            "fda_database",
            "medical_device_recalls",
            "healthcare_cybersecurity_feeds",
            "clinical_trial_registries",
            "healthcare_workforce_registries",
            "state_medical_board_data",
        ]
