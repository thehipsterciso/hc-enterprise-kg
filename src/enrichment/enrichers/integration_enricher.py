"""Integration enricher — enriches Integration entities with protocol and reliability profiles.

Integration is a first-class node (~45 fields) representing connections between systems.
This enricher reads source/target systems and DataFlows to populate protocol details,
error handling profiles, SLAs, and technical debt indicators.

Tiers:
  2 (Managed): source_systems, target_systems, protocol, frequency, data_format
  3 (Defined): error_handling, security_profile, middleware_platform, sla
  4 (Measured): annual_cost, monitoring_status, latency_metrics
  5 (Optimized): technical_debt_indicators, modernization_candidates
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar

from enrichment.base import (
    AbstractEnricher,
    EnrichmentAction,
    EnrichmentContext,
    EnrichmentResult,
    EntityContext,
    EnricherRegistry,
    EnrichmentTier,
    EnrichmentProfile,
    ConfidenceLevel,
    OSINTResults,
)
from domain.base import BaseEntity, EntityType, RelationshipType
from domain.shared import ProvenanceAndConfidence, DataGap


PROTOCOL_TEMPLATES = {
    "REST": {
        "protocol_name": "REST over HTTPS",
        "endpoint_format": "JSON",
        "version": "HTTP/1.1",
        "timeout_ms": 30000,
    },
    "SOAP": {
        "protocol_name": "SOAP over HTTPS",
        "endpoint_format": "XML",
        "version": "SOAP 1.2",
        "timeout_ms": 60000,
    },
    "gRPC": {
        "protocol_name": "gRPC over HTTP/2",
        "endpoint_format": "Protocol Buffers",
        "version": "gRPC 1.x",
        "timeout_ms": 10000,
    },
    "File Transfer": {
        "protocol_name": "SFTP/HTTPS",
        "endpoint_format": "Binary/CSV",
        "version": "SFTP",
        "timeout_ms": None,
    },
    "Message Queue": {
        "protocol_name": "AMQP/Kafka",
        "endpoint_format": "JSON",
        "version": "AMQP 0.9.1",
        "timeout_ms": None,
    },
    "Database Link": {
        "protocol_name": "Native database protocol",
        "endpoint_format": "SQL",
        "version": "Depends on DB",
        "timeout_ms": 5000,
    },
}

FREQUENCY_TEMPLATES = {
    "Real-Time": {"interval_seconds": 0, "description": "Sub-second latency required"},
    "Near Real-Time": {"interval_seconds": 60, "description": "Within 60 seconds"},
    "Hourly": {"interval_seconds": 3600, "description": "Once per hour"},
    "Daily": {"interval_seconds": 86400, "description": "Once per day"},
    "On-Demand": {"interval_seconds": None, "description": "Event-driven"},
}

ERROR_HANDLING_TEMPLATES = [
    {
        "retry_mechanism": "Exponential Backoff",
        "dead_letter_queue": True,
        "alerting": True,
        "manual_intervention_required": False,
        "error_rate_pct": 0.1,
    },
    {
        "retry_mechanism": "Fixed Interval (30s)",
        "dead_letter_queue": True,
        "alerting": True,
        "manual_intervention_required": False,
        "error_rate_pct": 0.5,
    },
    {
        "retry_mechanism": "None",
        "dead_letter_queue": False,
        "alerting": True,
        "manual_intervention_required": True,
        "error_rate_pct": 1.0,
    },
]

SECURITY_PROFILE_TEMPLATES = [
    {
        "authentication": "OAuth 2.0",
        "encryption_in_transit": True,
        "encryption_protocol": "TLS 1.3",
        "data_masking": True,
        "api_key_rotation": True,
        "ip_whitelisting": True,
        "rate_limiting": True,
    },
    {
        "authentication": "mTLS",
        "encryption_in_transit": True,
        "encryption_protocol": "TLS 1.3",
        "data_masking": False,
        "api_key_rotation": True,
        "ip_whitelisting": True,
        "rate_limiting": True,
    },
    {
        "authentication": "API Key",
        "encryption_in_transit": True,
        "encryption_protocol": "TLS 1.2",
        "data_masking": False,
        "api_key_rotation": False,
        "ip_whitelisting": False,
        "rate_limiting": False,
    },
]


@EnricherRegistry.register
class IntegrationEnricher(AbstractEnricher):
    """Enricher for Integration entities.

    Context-aware enrichment that reads source/target systems and data flows
    to populate protocol details, error handling, SLAs, costs, and technical
    debt indicators.
    """

    ENRICHES: ClassVar[EntityType] = EntityType.INTEGRATION

    def enrich(
        self,
        entity: BaseEntity,
        context: EntityContext,
        osint: OSINTResults | None = None,
        tier: EnrichmentTier = EnrichmentTier.BASIC,
        profile: EnrichmentProfile = EnrichmentProfile.STANDARD,
        enrichment_context: EnrichmentContext | None = None,
    ) -> EnrichmentResult:
        """Enrich an Integration entity based on graph context.

        Args:
            entity: The Integration entity to enrich.
            context: EntityContext with Integration's neighbors by relationship type.
            osint: Optional external research results.
            tier: Enrichment tier (BASIC, STANDARD, DEEP).
            profile: Enrichment profile (MINIMAL, STANDARD, COMPREHENSIVE).
            enrichment_context: Shared enrichment context.

        Returns:
            EnrichmentResult with field updates, provenance, relationships, gaps.
        """
        result = EnrichmentResult(
            entity_id=entity.id,
            entity_type=EntityType.INTEGRATION,
        )

        # Determine which tiers to populate based on profile
        tiers_to_populate = self._get_tiers_for_profile(profile)

        # Build integration profile from graph context
        integration_profile = self._build_integration_profile(entity, context)

        # Tier 2: Managed — core operational fields
        if 2 in tiers_to_populate:
            updates_t2, actions_t2 = self._populate_tier_2(entity, context, integration_profile)
            result.field_updates.update(updates_t2)
            result.actions.extend(actions_t2)

        # Tier 3: Defined — cross-entity coherence
        if 3 in tiers_to_populate:
            updates_t3, actions_t3 = self._populate_tier_3(entity, context, integration_profile)
            result.field_updates.update(updates_t3)
            result.actions.extend(actions_t3)

        # Tier 4: Measured — quantitative metrics
        if 4 in tiers_to_populate:
            updates_t4, actions_t4 = self._populate_tier_4(entity, context, integration_profile)
            result.field_updates.update(updates_t4)
            result.actions.extend(actions_t4)

        # Tier 5: Optimized — modernization & technical debt
        if 5 in tiers_to_populate:
            updates_t5, actions_t5 = self._populate_tier_5(entity, context, integration_profile)
            result.field_updates.update(updates_t5)
            result.actions.extend(actions_t5)

        # Identify data gaps
        result.known_gaps = self._identify_gaps(entity, integration_profile)

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
            return {2, 3}
        else:  # COMPREHENSIVE
            return {2, 3, 4, 5}

    def _build_integration_profile(self, entity: BaseEntity, context: EntityContext) -> dict:
        """Build holistic profile from graph neighborhood."""
        # Get connected systems (source and target)
        connected_systems = context.get_neighbors(RelationshipType.CONNECTS_TO)

        # Get integration type
        integration_type = getattr(entity, "integration_type", "API").strip() or "API"

        # Get data flows
        data_flows = context.get_neighbors(RelationshipType.FLOWS_TO)

        # Determine if integration is critical
        is_critical = len(data_flows) > 0 and any(
            self._flow_is_critical(flow) for flow in data_flows
        )

        profile = {
            "integration_id": entity.id,
            "integration_name": getattr(entity, "name", ""),
            "integration_type": integration_type,
            "connected_system_count": len(connected_systems),
            "data_flow_count": len(data_flows),
            "is_critical": is_critical,
            "frequency": getattr(entity, "frequency", "Hourly").strip() or "Hourly",
        }
        return profile

    def _flow_is_critical(self, data_flow: BaseEntity) -> bool:
        """Heuristic: determine if a data flow is critical."""
        classification = getattr(data_flow, "data_classification", "").lower()
        description = getattr(data_flow, "description", "").lower()

        critical_keywords = ["payment", "restricted", "confidential", "regulated", "sensitive"]
        return any(keyword in classification or keyword in description for keyword in critical_keywords)

    def _populate_tier_2(self, entity: BaseEntity, context: EntityContext, integration_profile: dict) -> tuple[dict, list]:
        """Populate Tier 2 (Managed) fields: core operational."""
        updates = {}
        actions = []

        integration_type = integration_profile.get("integration_type", "API")

        # Source and target systems (reference enrichment)
        source_systems = getattr(entity, "source_systems", [])
        target_systems = getattr(entity, "target_systems", [])

        if not source_systems or not target_systems:
            # Infer from context if not already populated
            connected = context.get_neighbors(RelationshipType.CONNECTS_TO)
            if len(connected) >= 2:
                if not source_systems:
                    updates["source_systems"] = [
                        {"system_id": connected[0].id, "system_name": getattr(connected[0], "name", "")}
                    ]
                if not target_systems:
                    updates["target_systems"] = [
                        {"system_id": connected[-1].id, "system_name": getattr(connected[-1], "name", "")}
                    ]
                actions.append(
                    EnrichmentAction(
                        entity_id=entity.id,
                        entity_type=EntityType.INTEGRATION,
                        fields_enriched=["source_systems", "target_systems"],
                        source="Graph topology inference",
                        methodology="Extracted from CONNECTS_TO neighbors",
                        confidence=ConfidenceLevel.MEDIUM,
                    )
                )

        # Protocol from integration type
        protocol_template = PROTOCOL_TEMPLATES.get(integration_type, PROTOCOL_TEMPLATES["REST"])
        updates["protocol"] = protocol_template
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.INTEGRATION,
                fields_enriched=["protocol"],
                source="Protocol registry",
                methodology=f"Template lookup for integration_type='{integration_type}'",
                confidence=ConfidenceLevel.HIGH,
            )
        )

        # Frequency
        frequency = integration_profile.get("frequency", "Hourly")
        freq_details = FREQUENCY_TEMPLATES.get(frequency, FREQUENCY_TEMPLATES["Hourly"])
        updates["frequency"] = frequency
        updates["frequency_description"] = freq_details.get("description", "")
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.INTEGRATION,
                fields_enriched=["frequency"],
                source="Integration configuration",
                methodology=f"Read from entity or inferred as '{frequency}'",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Data format from protocol
        data_format = protocol_template.get("endpoint_format", "JSON")
        updates["data_format"] = data_format
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.INTEGRATION,
                fields_enriched=["data_format"],
                source="Protocol specification",
                methodology=f"Derived from protocol: {data_format}",
                confidence=ConfidenceLevel.HIGH,
            )
        )

        return updates, actions

    def _populate_tier_3(self, entity: BaseEntity, context: EntityContext, integration_profile: dict) -> tuple[dict, list]:
        """Populate Tier 3 (Defined) fields: cross-entity coherence."""
        updates = {}
        actions = []

        is_critical = integration_profile.get("is_critical", False)
        integration_type = integration_profile.get("integration_type", "API")

        # Error handling
        if is_critical:
            error_template = ERROR_HANDLING_TEMPLATES[0]  # Robust exponential backoff
        elif integration_type == "File Transfer":
            error_template = ERROR_HANDLING_TEMPLATES[1]  # Fixed interval
        else:
            error_template = ERROR_HANDLING_TEMPLATES[2]  # Minimal

        updates["error_handling"] = error_template
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.INTEGRATION,
                fields_enriched=["error_handling"],
                source="Criticality-aware error policy",
                methodology=f"Selected based on criticality={is_critical} and type='{integration_type}'",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Security profile
        if is_critical:
            security_template = SECURITY_PROFILE_TEMPLATES[0]  # mTLS + strongest
        elif integration_type == "API":
            security_template = SECURITY_PROFILE_TEMPLATES[0]  # OAuth 2.0
        else:
            security_template = SECURITY_PROFILE_TEMPLATES[2]  # Basic API Key

        updates["security_profile"] = security_template
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.INTEGRATION,
                fields_enriched=["security_profile"],
                source="Security baseline policy",
                methodology=f"Risk-based selection: critical={is_critical}, type='{integration_type}'",
                confidence=ConfidenceLevel.HIGH,
            )
        )

        # Middleware platform
        middleware_template = "API Gateway" if integration_type == "API" else "Message Broker"
        if integration_type == "Message Queue":
            middleware_template = "Apache Kafka"
        elif integration_type == "File Transfer":
            middleware_template = "SFTP Server"

        updates["middleware_platform"] = {
            "platform_name": middleware_template,
            "platform_system_id": "",
            "managed_by": "IT Operations",
        }
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.INTEGRATION,
                fields_enriched=["middleware_platform"],
                source="Integration pattern mapping",
                methodology=f"Inferred from integration_type='{integration_type}'",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # SLA
        target_uptime = 99.95 if is_critical else 99.0
        sla = {
            "target_uptime_pct": target_uptime,
            "actual_uptime_pct": target_uptime - 0.05,
            "measurement_period": "Monthly",
        }
        updates["availability_sla"] = sla
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.INTEGRATION,
                fields_enriched=["availability_sla"],
                source="SLA baseline",
                methodology=f"Assigned based on criticality: {target_uptime}%",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        return updates, actions

    def _populate_tier_4(self, entity: BaseEntity, context: EntityContext, integration_profile: dict) -> tuple[dict, list]:
        """Populate Tier 4 (Measured) fields: quantitative metrics."""
        updates = {}
        actions = []

        is_critical = integration_profile.get("is_critical", False)
        integration_type = integration_profile.get("integration_type", "API")

        # Annual cost
        base_cost = 50000.0 if is_critical else 10000.0
        if integration_type == "Message Queue":
            base_cost *= 1.5
        elif integration_type == "File Transfer":
            base_cost *= 0.8

        annual_cost = {
            "amount": base_cost,
            "currency": "USD",
            "cost_components": ["License", "Hosting", "Support", "Data transfer"],
        }
        updates["annual_cost"] = annual_cost
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.INTEGRATION,
                fields_enriched=["annual_cost"],
                source="Cost modeling",
                methodology=f"Base cost adjusted for criticality={is_critical} and type='{integration_type}'",
                confidence=ConfidenceLevel.LOW,
            )
        )

        # Monitoring status
        monitoring = "Fully Monitored" if is_critical else "Partially Monitored"
        updates["monitoring_status"] = monitoring
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.INTEGRATION,
                fields_enriched=["monitoring_status"],
                source="Criticality-driven monitoring",
                methodology=f"Determined by criticality={is_critical}",
                confidence=ConfidenceLevel.HIGH,
            )
        )

        # Latency metrics
        if integration_type == "gRPC":
            latency_p95 = 50
        elif integration_type == "REST":
            latency_p95 = 200
        elif integration_type == "Message Queue":
            latency_p95 = 100
        else:
            latency_p95 = 500

        updates["latency_metrics"] = {
            "max_acceptable_ms": latency_p95 * 2,
            "actual_p95_ms": latency_p95,
            "meets_requirement": True,
        }
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.INTEGRATION,
                fields_enriched=["latency_metrics"],
                source="Protocol-based baseline",
                methodology=f"Derived from protocol type='{integration_type}'",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        return updates, actions

    def _populate_tier_5(self, entity: BaseEntity, context: EntityContext, integration_profile: dict) -> tuple[dict, list]:
        """Populate Tier 5 (Optimized) fields: modernization & technical debt."""
        updates = {}
        actions = []

        integration_type = integration_profile.get("integration_type", "API")
        is_critical = integration_profile.get("is_critical", False)

        # Technical debt indicators
        debt_indicators = []

        if integration_type == "File Transfer":
            debt_indicators.append({
                "indicator_type": "Legacy File Transfer",
                "severity": "Medium",
                "description": "File transfer integrations are being replaced with API-based solutions",
            })

        if integration_type == "SOAP":
            debt_indicators.append({
                "indicator_type": "SOAP Web Services",
                "severity": "High",
                "description": "SOAP is deprecated; migrate to REST or gRPC",
            })

        if not is_critical:
            debt_indicators.append({
                "indicator_type": "Monitoring Gap",
                "severity": "Low",
                "description": "Consider upgrading to full monitoring",
            })

        updates["technical_debt_indicators"] = debt_indicators
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.INTEGRATION,
                fields_enriched=["technical_debt_indicators"],
                source="Technical debt assessment",
                methodology=f"Based on integration_type='{integration_type}'",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Modernization candidates
        modernization = []

        if integration_type == "File Transfer":
            modernization.append({
                "candidate": "RESTful API wrapper",
                "rationale": "Event-driven, lower latency",
                "effort": "High",
                "savings": 30000,
            })

        if integration_type == "SOAP":
            modernization.append({
                "candidate": "REST with API gateway",
                "rationale": "Easier to manage, better ecosystem",
                "effort": "Medium",
                "savings": 50000,
            })

        if is_critical and not debt_indicators:
            modernization.append({
                "candidate": "Implement service mesh (Istio)",
                "rationale": "Enhanced reliability and observability",
                "effort": "High",
                "savings": 0,
            })

        updates["modernization_candidates"] = modernization
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.INTEGRATION,
                fields_enriched=["modernization_candidates"],
                source="Modernization roadmap",
                methodology="Architecture best practices + debt assessment",
                confidence=ConfidenceLevel.LOW,
            )
        )

        return updates, actions

    def _identify_gaps(self, entity: BaseEntity, integration_profile: dict) -> list[DataGap]:
        """Identify known data gaps."""
        gaps = []

        # Check for missing key attributes
        if not getattr(entity, "source_systems", None) or len(getattr(entity, "source_systems", [])) == 0:
            gaps.append(
                DataGap(
                    field_name="source_systems",
                    description="No source systems defined",
                    severity="High",
                    remediation_suggestion="Link source systems via SystemRef",
                )
            )

        if not getattr(entity, "target_systems", None) or len(getattr(entity, "target_systems", [])) == 0:
            gaps.append(
                DataGap(
                    field_name="target_systems",
                    description="No target systems defined",
                    severity="High",
                    remediation_suggestion="Link target systems via SystemRef",
                )
            )

        if not getattr(entity, "owner", None):
            gaps.append(
                DataGap(
                    field_name="owner",
                    description="No integration owner assigned",
                    severity="Medium",
                    remediation_suggestion="Assign owner via RESPONSIBLE_FOR relationship",
                )
            )

        if integration_profile.get("data_flow_count", 0) == 0:
            gaps.append(
                DataGap(
                    field_name="data_exchanged",
                    description="No data flows linked to this integration",
                    severity="Low",
                    remediation_suggestion="Link DataAssets via FLOWS_TO relationships",
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

        primary_source = "Enrichment Agency - Integration Enricher"
        if actions:
            primary_source += f" ({len(actions)} fields enriched)"

        return ProvenanceAndConfidence(
            primary_data_source=primary_source,
            last_assessed_date=datetime.now(UTC).isoformat(),
            assessed_by="IntegrationEnricher v1.0",
            assessment_methodology="Type-aware protocol assignment + criticality-driven SLA selection",
            confidence_level=confidence_map.get(tier, "Medium"),
        )
