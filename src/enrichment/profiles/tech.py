"""TechEnrichmentProfile — tech company focus on systems, integrations, architecture."""

from __future__ import annotations

from domain.base import EntityType
from enrichment.profiles.base import EnrichmentProfile


class TechEnrichmentProfile(EnrichmentProfile):
    """Enrichment profile for technology companies.

    Prioritizes:
    - System architecture and tech stack coherence
    - Integration mappings and API surfaces
    - Data flows and technical dependencies
    - Technical roles and engineering organization
    - Cyber risk and vulnerability management

    Focus areas:
    - technology_radar: track tech stack evolution
    - api_standards: API gateway, REST/GraphQL patterns
    - cloud_benchmarks: cloud maturity, multi-cloud alignment
    - cvee_feeds: CVE and vulnerability intelligence

    Enrichment priority:
    System → Integration → DataFlow → Person (tech roles) → Risk (cyber)
    """

    name: str = "TechEnrichmentProfile"

    def should_populate_field(self, entity_type: EntityType, field: str, tier: int) -> bool:
        """Tech profile populates tech-stack and architecture fields.

        At tier 2+: System status, integration_type, criticality
        At tier 3+: Data flow mappings, API specifications
        At tier 4+: Performance metrics, architectural decisions
        At tier 5+: Tech stack evolution, replacement roadmaps
        """
        tech_fields_by_tier = {
            EntityType.SYSTEM: {
                2: ["status", "criticality", "owner_id", "tech_stack"],
                3: ["dependencies", "deployment_model", "api_surface"],
                4: ["performance_sla", "scalability_score", "tech_debt_items"],
                5: ["architecture_decisions", "modernization_roadmap"],
            },
            EntityType.INTEGRATION: {
                2: ["integration_type", "source_id", "target_id", "status"],
                3: ["protocol", "data_format", "frequency", "sla"],
                4: ["latency_metrics", "throughput_metrics", "error_rate"],
                5: ["cost_model", "modernization_path"],
            },
            EntityType.DATA_FLOW: {
                2: ["source_id", "target_id", "data_classification"],
                3: ["frequency", "volume_estimate", "transformation_rules"],
                4: ["actual_volume_monthly", "latency_percentile"],
                5: ["cost_per_gb", "compliance_flags"],
            },
            EntityType.PERSON: {
                2: ["title", "skills_inventory", "certifications_held"],
                3: ["technical_skills", "architecture_experience"],
                4: ["technical_authority_areas", "peer_review_load"],
                5: ["mentoring_load", "knowledge_transfer_priority"],
            },
            EntityType.RISK: {
                2: ["risk_type", "likelihood", "impact"],
                3: ["affected_systems", "affected_data_assets"],
                4: ["quantified_loss_estimate", "occurrence_history"],
                5: ["scenario_analysis", "residual_after_controls"],
            },
        }

        if entity_type not in tech_fields_by_tier:
            return True  # Default: populate other entity types

        tier_dict = tech_fields_by_tier[entity_type]
        for check_tier in range(2, tier + 1):
            if check_tier in tier_dict and field in tier_dict[check_tier]:
                return True
        return False

    def get_focus_areas(self) -> list[str]:
        """Tech profile focus areas."""
        return [
            "technology_radar",
            "api_standards",
            "cloud_benchmarks",
            "cve_feeds",
            "tech_debt_tracking",
            "architecture_governance",
        ]

    def get_enrichment_priority(self) -> list[EntityType]:
        """Tech profile enrichment priority: systems first, then integrations, then data flows."""
        return [
            EntityType.SYSTEM,
            EntityType.INTEGRATION,
            EntityType.DATA_FLOW,
            EntityType.PERSON,
            EntityType.RISK,
            EntityType.VULNERABILITY,
            EntityType.NETWORK,
            EntityType.ROLE,
            EntityType.DEPARTMENT,
            EntityType.POLICY,
            EntityType.DATA_ASSET,
            EntityType.VENDOR,
            EntityType.CONTROL,
            EntityType.INCIDENT,
            EntityType.THREAT_ACTOR,
            EntityType.LOCATION,
        ]

    def get_osint_sources(self) -> list[str]:
        """Tech profile OSINT sources."""
        return [
            "shodan",
            "censys",
            "cve_feeds",
            "github_public_repos",
            "dns_records",
            "ssl_certificate_transparency",
            "cloud_storage_discovery",
        ]
