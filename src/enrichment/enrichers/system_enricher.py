"""System enricher — enriches System entities with context-aware technology profiles.

The System entity is the richest in the knowledge graph (~119 attributes).
This enricher reads the entity's graph neighborhood (Networks, DataAssets,
Vendors, Vulnerabilities, Integrations) to inform enrichment decisions.

Tiers:
  2 (Managed): tech_stack, authentication_mechanism, encryption_profile, support_status
  3 (Defined): api_surface, availability_sla, compliance_certifications, security_posture
  4 (Measured): cost_optimization, performance_metrics, incident_history, change_velocity
  5 (Optimized): replacement_roadmap, technical_debt_score, business_impact_if_unavailable
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

# Realistic tech stacks mapped to system types
TECH_STACK_TEMPLATES = {
    "Enterprise Application": [
        {"layer": "Operating System", "technology": "RHEL", "version": "8.x", "vendor": "Red Hat"},
        {"layer": "Runtime", "technology": "Java", "version": "17", "vendor": "Eclipse Adoptium"},
        {"layer": "Framework", "technology": "Spring Boot", "version": "3.x", "vendor": "VMware"},
    ],
    "Microservice": [
        {
            "layer": "Container Runtime",
            "technology": "Docker",
            "version": "24.x",
            "vendor": "Docker Inc",
        },
        {"layer": "Orchestration", "technology": "Kubernetes", "version": "1.28", "vendor": "CNCF"},
        {"layer": "Language", "technology": "Node.js", "version": "20.x", "vendor": "OpenJS"},
    ],
    "Data Platform": [
        {
            "layer": "Cluster Manager",
            "technology": "Apache Spark",
            "version": "3.5.x",
            "vendor": "Apache",
        },
        {
            "layer": "Message Queue",
            "technology": "Apache Kafka",
            "version": "3.x",
            "vendor": "Apache",
        },
        {
            "layer": "Database",
            "technology": "PostgreSQL",
            "version": "15.x",
            "vendor": "PostgreSQL",
        },
    ],
    "Data Warehouse": [
        {"layer": "Database", "technology": "Snowflake", "version": "Cloud", "vendor": "Snowflake"},
        {"layer": "ETL", "technology": "dbt", "version": "1.7.x", "vendor": "dbt Labs"},
        {"layer": "BI Tool", "technology": "Tableau", "version": "2024.1", "vendor": "Salesforce"},
    ],
    "API Gateway": [
        {
            "layer": "Operating System",
            "technology": "Ubuntu",
            "version": "22.04 LTS",
            "vendor": "Canonical",
        },
        {"layer": "Gateway", "technology": "Kong", "version": "3.x", "vendor": "Kong Inc"},
        {"layer": "Monitoring", "technology": "Prometheus", "version": "2.x", "vendor": "CNCF"},
    ],
    "Security Tool": [
        {"layer": "Operating System", "technology": "RHEL", "version": "8.x", "vendor": "Red Hat"},
        {"layer": "Engine", "technology": "Custom C++", "version": "varies", "vendor": "Internal"},
        {"layer": "Database", "technology": "MongoDB", "version": "6.x", "vendor": "MongoDB"},
    ],
}

AUTHENTICATION_TEMPLATES = [
    {"mechanism": "SAML 2.0", "protocol": "SAML", "mfa_supported": True, "mfa_enforced": False},
    {
        "mechanism": "OAuth 2.0",
        "protocol": "OpenID Connect",
        "mfa_supported": True,
        "mfa_enforced": True,
    },
    {"mechanism": "LDAP", "protocol": "LDAP3", "mfa_supported": False, "mfa_enforced": False},
    {
        "mechanism": "Kerberos",
        "protocol": "Kerberos5",
        "mfa_supported": True,
        "mfa_enforced": False,
    },
    {"mechanism": "mTLS", "protocol": "TLS 1.3", "mfa_supported": True, "mfa_enforced": True},
]

ENCRYPTION_TEMPLATES = [
    {"data_at_rest": "AES-256", "data_in_transit": "TLS 1.3", "key_management": "AWS KMS"},
    {"data_at_rest": "TDE", "data_in_transit": "TLS 1.2", "key_management": "Oracle KMS"},
    {"data_at_rest": "AES-256-GCM", "data_in_transit": "TLS 1.3", "key_management": "Vault"},
]

COMPLIANCE_TEMPLATES = [
    "SOC 2 Type II",
    "ISO 27001",
    "PCI DSS 3.2.1",
    "HIPAA",
    "GDPR",
    "FedRAMP",
]


@EnricherRegistry.register
class SystemEnricher(AbstractEnricher):
    """Enricher for System entities.

    Context-aware enrichment that reads graph neighbors to populate
    technical attributes, security posture, operational metrics, and
    strategic importance fields.
    """

    ENRICHES: ClassVar[EntityType] = EntityType.SYSTEM

    def enrich(
        self,
        entity: BaseEntity,
        context: EntityContext,
        osint: OSINTResults | None = None,
        tier: EnrichmentTier = EnrichmentTier.BASIC,
        profile: EnrichmentProfile = EnrichmentProfile.STANDARD,
        enrichment_context: EnrichmentContext | None = None,
    ) -> EnrichmentResult:
        """Enrich a System entity based on graph context.

        Args:
            entity: The System entity to enrich.
            context: EntityContext with System's neighbors by relationship type.
            osint: Optional external research results.
            tier: Enrichment tier (BASIC, STANDARD, DEEP).
            profile: Enrichment profile (MINIMAL, STANDARD, COMPREHENSIVE).
            enrichment_context: Shared enrichment context.

        Returns:
            EnrichmentResult with field updates, provenance, relationships, gaps.
        """
        result = EnrichmentResult(
            entity_id=entity.id,
            entity_type=EntityType.SYSTEM,
        )

        # Determine which tiers to populate based on profile
        tiers_to_populate = self._get_tiers_for_profile(profile)

        # Build cross-entity profile from graph context
        cross_profile = self._build_system_profile(entity, context)

        # Tier 2: Managed — core operational fields
        if 2 in tiers_to_populate:
            updates_t2, actions_t2 = self._populate_tier_2(entity, context, cross_profile)
            result.field_updates.update(updates_t2)
            result.actions.extend(actions_t2)

        # Tier 3: Defined — cross-entity coherence
        if 3 in tiers_to_populate:
            updates_t3, actions_t3 = self._populate_tier_3(entity, context, cross_profile)
            result.field_updates.update(updates_t3)
            result.actions.extend(actions_t3)

        # Tier 4: Measured — quantitative metrics
        if 4 in tiers_to_populate:
            updates_t4, actions_t4 = self._populate_tier_4(entity, context, cross_profile)
            result.field_updates.update(updates_t4)
            result.actions.extend(actions_t4)

        # Tier 5: Optimized — full fidelity & predictive
        if 5 in tiers_to_populate:
            updates_t5, actions_t5 = self._populate_tier_5(entity, context, cross_profile)
            result.field_updates.update(updates_t5)
            result.actions.extend(actions_t5)

        # Identify data gaps
        result.known_gaps = self._identify_gaps(entity, cross_profile)

        # Update provenance
        result.provenance_update = self._build_provenance(
            result.actions,
            tier,
            profile,
        )

        return result

    def _get_tiers_for_profile(self, profile: EnrichmentProfile) -> set[int]:
        """Determine which tiers to populate based on profile."""
        if profile == EnrichmentProfile.MINIMAL:
            return {2}
        elif profile == EnrichmentProfile.STANDARD:
            return {2, 3, 4}
        else:  # COMPREHENSIVE
            return {2, 3, 4, 5}

    def _build_system_profile(self, entity: BaseEntity, context: EntityContext) -> dict:
        """Build holistic profile from graph neighborhood."""
        profile = {
            "system_id": entity.id,
            "system_name": getattr(entity, "name", ""),
            "system_type": getattr(entity, "system_type", ""),
            "networks_count": len(context.get_neighbors(RelationshipType.RUNS_ON)),
            "data_assets_count": len(context.get_neighbors(RelationshipType.STORES)),
            "vendors_count": len(context.get_neighbors(RelationshipType.SUPPLIED_BY)),
            "vulnerabilities_count": len(context.get_neighbors(RelationshipType.AFFECTS)),
            "integrations_count": len(context.get_neighbors(RelationshipType.CONNECTS_TO)),
            "critical_data_stored": self._has_critical_data(entity, context),
        }
        return profile

    def _has_critical_data(self, entity: BaseEntity, context: EntityContext) -> bool:
        """Check if system stores critical data assets."""
        data_assets = context.get_neighbors(RelationshipType.STORES)
        for asset in data_assets:
            classification = getattr(asset, "classification", "").lower()
            if "confidential" in classification or "restricted" in classification:
                return True
        return False

    def _populate_tier_2(
        self, entity: BaseEntity, context: EntityContext, cross_profile: dict
    ) -> tuple[dict, list]:
        """Populate Tier 2 (Managed) fields: core operational."""
        updates = {}
        actions = []

        system_type = getattr(entity, "system_type", "").strip() or "Enterprise Application"

        # Tech stack from templates
        tech_stack = TECH_STACK_TEMPLATES.get(
            system_type, TECH_STACK_TEMPLATES["Enterprise Application"]
        )
        updates["tech_stack"] = tech_stack
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.SYSTEM,
                fields_enriched=["tech_stack"],
                source="Template Registry",
                methodology="Coordinated template dicts (system_type match)",
                confidence=ConfidenceLevel.HIGH,
            )
        )

        # Authentication mechanism from context
        is_critical = cross_profile.get("critical_data_stored", False)
        auth_template = AUTHENTICATION_TEMPLATES[-1 if is_critical else 0]
        updates["authentication_mechanisms"] = [auth_template]  # type: ignore[list-item]
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.SYSTEM,
                fields_enriched=["authentication_mechanisms"],
                source="Context-aware selection",
                methodology=f"Graph analysis (critical_data={is_critical})",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Encryption profile
        encryption = ENCRYPTION_TEMPLATES[0]
        updates["encryption_profile"] = encryption
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.SYSTEM,
                fields_enriched=["encryption_profile"],
                source="Security standards",
                methodology="Default modern encryption stack",
                confidence=ConfidenceLevel.HIGH,
            )
        )

        # Support status from vendor relationships
        vendors = context.get_neighbors(RelationshipType.SUPPLIED_BY)
        support_status = "Vendor Supported" if vendors else "Internal Support"
        updates["support_status"] = support_status
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.SYSTEM,
                fields_enriched=["support_status"],
                source="Vendor relationship analysis",
                methodology=f"Graph traversal (vendors={len(vendors)})",
                confidence=ConfidenceLevel.HIGH,
            )
        )

        return updates, actions

    def _populate_tier_3(
        self, entity: BaseEntity, context: EntityContext, cross_profile: dict
    ) -> tuple[dict, list]:
        """Populate Tier 3 (Defined) fields: cross-entity coherence."""
        updates = {}
        actions = []

        # API surface from integration connections
        integrations = context.get_neighbors(RelationshipType.CONNECTS_TO)
        api_surface = {
            "api_count": len(integrations),
            "api_types": ["REST", "SOAP"] if len(integrations) > 0 else [],
            "api_documentation_status": "Documented" if len(integrations) < 10 else "Partial",
            "api_versioning_strategy": "Semantic Versioning",
            "api_gateway": "Kong" if len(integrations) > 5 else "None",
        }
        updates["api_surface"] = api_surface
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.SYSTEM,
                fields_enriched=["api_surface"],
                source="Integration topology analysis",
                methodology=f"Graph traversal (integrations={len(integrations)})",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Availability SLA
        is_critical = cross_profile.get("critical_data_stored", False)
        uptime_target = 99.99 if is_critical else 99.5
        availability_sla = {
            "target_uptime_pct": uptime_target,
            "measurement_window": "Monthly",
            "actual_uptime_pct": uptime_target - 0.1,
            "actual_measurement_period": "Last 12 months",
            "sla_source": "Operational agreement",
            "sla_breach_count_12m": 0 if uptime_target > 99.9 else 1,
        }
        updates["availability_sla"] = availability_sla
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.SYSTEM,
                fields_enriched=["availability_sla"],
                source="Context-aware SLA determination",
                methodology=f"Criticality assessment (critical={is_critical})",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Compliance certifications
        has_sensitive_data = cross_profile.get("critical_data_stored", False)
        certifications = [COMPLIANCE_TEMPLATES[0]]  # SOC 2 always
        if has_sensitive_data:
            certifications.append(COMPLIANCE_TEMPLATES[1])  # ISO 27001
        updates["compliance_certifications"] = [
            {
                "certification": cert,
                "scope": "Full system",
                "status": "Certified",
                "last_audit_date": datetime.now(UTC).isoformat(),
                "next_audit_date": None,
            }
            for cert in certifications
        ]
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.SYSTEM,
                fields_enriched=["compliance_certifications"],
                source="Data criticality assessment",
                methodology=f"Based on stored data sensitivity (sensitive={has_sensitive_data})",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Security posture from vulnerability count
        vulnerabilities = context.get_neighbors(RelationshipType.AFFECTS)
        vuln_count = len(vulnerabilities)
        if vuln_count == 0:
            posture = "Strong"
        elif vuln_count < 5:
            posture = "Acceptable"
        else:
            posture = "At Risk"
        updates["security_posture"] = posture
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.SYSTEM,
                fields_enriched=["security_posture"],
                source="Vulnerability analysis",
                methodology=f"Count-based assessment (vulns={vuln_count})",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        return updates, actions

    def _populate_tier_4(
        self, entity: BaseEntity, context: EntityContext, cross_profile: dict
    ) -> tuple[dict, list]:
        """Populate Tier 4 (Measured) fields: quantitative metrics."""
        updates = {}
        actions = []

        # Cost optimization opportunities
        integration_count = cross_profile.get("integrations_count", 0)
        opportunities = []
        if integration_count > 5:
            opportunities.append(
                {
                    "opportunity_description": "Consolidate redundant integrations",
                    "estimated_annual_savings": 50000.0,
                    "currency": "USD",
                    "effort_level": "High",
                    "status": "Identified",
                }
            )
        if cross_profile.get("system_type", "").lower() == "legacy":
            opportunities.append(
                {
                    "opportunity_description": "Migrate to cloud platform",
                    "estimated_annual_savings": 100000.0,
                    "currency": "USD",
                    "effort_level": "Very High",
                    "status": "Identified",
                }
            )
        updates["cost_optimization"] = opportunities
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.SYSTEM,
                fields_enriched=["cost_optimization"],
                source="Economic optimization analysis",
                methodology="Integration density + system type heuristics",
                confidence=ConfidenceLevel.LOW,
            )
        )

        # Performance metrics
        updates["performance_metrics"] = {
            "response_time_p95_ms": 250,
            "throughput_target": "10000 req/sec",
            "uptime_actual_pct": 99.87,
        }
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.SYSTEM,
                fields_enriched=["performance_metrics"],
                source="Monitoring baseline",
                methodology="Template-based reasonable defaults",
                confidence=ConfidenceLevel.LOW,
            )
        )

        # Incident history
        vuln_count = cross_profile.get("vulnerabilities_count", 0)
        updates["incident_history"] = {
            "p1_count_12m": max(0, vuln_count // 3),
            "p2_count_12m": max(0, vuln_count // 2),
            "mttr_hours": 4.5,
            "last_major_incident_date": datetime.now(UTC).isoformat(),
            "last_major_incident_description": "Security patch deployment"
            if vuln_count > 0
            else "None",
        }
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.SYSTEM,
                fields_enriched=["incident_history"],
                source="Vulnerability correlation",
                methodology="Derived from vulnerability_count in context",
                confidence=ConfidenceLevel.LOW,
            )
        )

        return updates, actions

    def _populate_tier_5(
        self, entity: BaseEntity, context: EntityContext, cross_profile: dict
    ) -> tuple[dict, list]:
        """Populate Tier 5 (Optimized) fields: full fidelity & predictive."""
        updates = {}
        actions = []

        # Replacement roadmap
        updates["replacement_roadmap"] = {
            "has_replacement_planned": False,
            "replacement_system_id": "",
            "replacement_system_name": "",
            "migration_timeline": "",
            "migration_status": "Not planned",
            "migration_complexity": "Unknown",
        }
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.SYSTEM,
                fields_enriched=["replacement_roadmap"],
                source="Strategic assessment",
                methodology="Baseline assumption (not planned)",
                confidence=ConfidenceLevel.LOW,
            )
        )

        # Technical debt score
        vuln_count = cross_profile.get("vulnerabilities_count", 0)
        integration_count = cross_profile.get("integrations_count", 0)
        debt_score = min(100, 20 + (vuln_count * 5) + (integration_count * 2))
        updates["technical_debt_score"] = debt_score
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.SYSTEM,
                fields_enriched=["technical_debt_score"],
                source="Quantitative debt assessment",
                methodology="Weighted formula: base(20) + vulns(5x) + integrations(2x)",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Business impact if unavailable
        is_critical = cross_profile.get("critical_data_stored", False)
        impact_per_hour = 500000.0 if is_critical else 50000.0
        affected_users = 5000 if is_critical else 500
        updates["business_impact_if_unavailable"] = {
            "impact_description": "Critical revenue and operations impact"
            if is_critical
            else "Operational disruption",
            "estimated_financial_impact_per_hour": impact_per_hour,
            "currency": "USD",
            "affected_capabilities": ["Payment Processing"] if is_critical else ["Reporting"],
            "affected_users": affected_users,
            "affected_customers": 100 if is_critical else 10,
        }
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.SYSTEM,
                fields_enriched=["business_impact_if_unavailable"],
                source="Criticality assessment",
                methodology="Based on data sensitivity and integration density",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        return updates, actions

    def _identify_gaps(self, entity: BaseEntity, cross_profile: dict) -> list[DataGap]:
        """Identify known data gaps."""
        gaps = []

        # Assess what's missing
        if not getattr(entity, "incident_history", None):
            gaps.append(
                DataGap(
                    field_name="incident_history",
                    description="No incident data available",
                    severity="Low",
                    remediation_suggestion="Connect to incident tracking system",
                )
            )

        if cross_profile.get("vulnerabilities_count", 0) == 0:
            gaps.append(
                DataGap(
                    field_name="vulnerability_profile",
                    description="No vulnerability scans linked",
                    severity="High",
                    remediation_suggestion="Run vulnerability assessment and link results",
                )
            )

        if not getattr(entity, "owner_person_id", None):
            gaps.append(
                DataGap(
                    field_name="owner_person_id",
                    description="System owner not assigned",
                    severity="Medium",
                    remediation_suggestion="Assign system owner via RESPONSIBLE_FOR relationship",
                )
            )

        return gaps

    def _build_provenance(
        self, actions: list[EnrichmentAction], tier: EnrichmentTier, profile: EnrichmentProfile
    ) -> ProvenanceAndConfidence:
        """Build provenance record."""
        confidence_map = {
            EnrichmentTier.BASIC: "Medium",
            EnrichmentTier.STANDARD: "High",
            EnrichmentTier.DEEP: "Verified",
        }

        primary_source = "Enrichment Agency - System Enricher"
        if actions:
            primary_source += f" ({len(actions)} fields enriched)"

        return ProvenanceAndConfidence(
            primary_data_source=primary_source,
            last_assessed_date=datetime.now(UTC).isoformat(),
            assessed_by="SystemEnricher v1.0",
            assessment_methodology="Context-aware graph analysis + template coordination",
            confidence_level=confidence_map.get(tier, "Medium"),
        )
