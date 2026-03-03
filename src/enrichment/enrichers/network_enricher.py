"""Network enricher — enriches Network entities with security and operational profiles.

Network is a lightweight entity (~8 core fields). This enricher reads graph neighbors
(Systems on the network, connected networks) to populate security zones, segmentation,
criticality, and monitoring status.

Tiers:
  2 (Managed): security_zone, bandwidth_capacity
  3 (Defined): monitoring_status, segmentation_policy
  4 (Measured): traffic_metrics
  5 (Optimized): optimization_recommendations
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

SECURITY_ZONE_CLASSIFIERS = {
    "dmz": {"traffic_risk": "High", "typical_systems": ["Web Servers", "API Gateways"]},
    "internal": {
        "traffic_risk": "Medium",
        "typical_systems": ["Application Servers", "Business Apps"],
    },
    "restricted": {"traffic_risk": "Low", "typical_systems": ["Database Servers", "Auth Services"]},
    "guest": {"traffic_risk": "Very High", "typical_systems": ["VPN", "Public WiFi"]},
    "external": {"traffic_risk": "Critical", "typical_systems": ["Internet-facing", "Third-party"]},
}

MONITORING_STATUS_TEMPLATES = {
    "restricted": "Fully Monitored with Advanced Threat Detection",
    "internal": "Fully Monitored",
    "dmz": "Continuously Monitored with IDS/IPS",
    "guest": "Monitored with Logging",
    "external": "Not Monitored (External)",
}

BANDWIDTH_TEMPLATES = {
    "restricted": "1000 Mbps (Critical tier)",
    "internal": "500 Mbps (Standard tier)",
    "dmz": "1000 Mbps (High traffic)",
    "guest": "100 Mbps (Best effort)",
    "external": "Varies",
}


@EnricherRegistry.register
class NetworkEnricher(AbstractEnricher):
    """Enricher for Network entities.

    Context-aware enrichment that reads Systems on the network and other
    networks to populate security zone, segmentation, criticality, and
    monitoring status.
    """

    ENRICHES: ClassVar[EntityType] = EntityType.NETWORK

    def enrich(
        self,
        entity: BaseEntity,
        context: EntityContext,
        osint: OSINTResults | None = None,
        tier: EnrichmentTier = EnrichmentTier.BASIC,
        profile: EnrichmentProfile = EnrichmentProfile.STANDARD,
        enrichment_context: EnrichmentContext | None = None,
    ) -> EnrichmentResult:
        """Enrich a Network entity based on graph context.

        Args:
            entity: The Network entity to enrich.
            context: EntityContext with Network's neighbors by relationship type.
            osint: Optional external research results.
            tier: Enrichment tier (BASIC, STANDARD, DEEP).
            profile: Enrichment profile (MINIMAL, STANDARD, COMPREHENSIVE).
            enrichment_context: Shared enrichment context.

        Returns:
            EnrichmentResult with field updates, provenance, relationships, gaps.
        """
        result = EnrichmentResult(
            entity_id=entity.id,
            entity_type=EntityType.NETWORK,
        )

        # Determine which tiers to populate based on profile
        tiers_to_populate = self._get_tiers_for_profile(profile)

        # Build network profile from graph context
        network_profile = self._build_network_profile(entity, context)

        # Tier 2: Managed — core operational fields
        if 2 in tiers_to_populate:
            updates_t2, actions_t2 = self._populate_tier_2(entity, context, network_profile)
            result.field_updates.update(updates_t2)
            result.actions.extend(actions_t2)

        # Tier 3: Defined — cross-entity coherence
        if 3 in tiers_to_populate:
            updates_t3, actions_t3 = self._populate_tier_3(entity, context, network_profile)
            result.field_updates.update(updates_t3)
            result.actions.extend(actions_t3)

        # Tier 4: Measured — quantitative metrics
        if 4 in tiers_to_populate:
            updates_t4, actions_t4 = self._populate_tier_4(entity, context, network_profile)
            result.field_updates.update(updates_t4)
            result.actions.extend(actions_t4)

        # Tier 5: Optimized — optimization recommendations
        if 5 in tiers_to_populate:
            updates_t5, actions_t5 = self._populate_tier_5(entity, context, network_profile)
            result.field_updates.update(updates_t5)
            result.actions.extend(actions_t5)

        # Identify data gaps
        result.known_gaps = self._identify_gaps(entity, network_profile)

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

    def _build_network_profile(self, entity: BaseEntity, context: EntityContext) -> dict:
        """Build holistic profile from graph neighborhood."""
        # Get the network's zone
        zone = getattr(entity, "zone", "internal").lower()

        # Count systems on this network
        systems_on_network = context.get_neighbors(RelationshipType.RUNS_ON)

        # Determine criticality
        has_critical_systems = any(self._system_is_critical(sys) for sys in systems_on_network)

        profile = {
            "network_id": entity.id,
            "network_name": getattr(entity, "name", ""),
            "zone": zone,
            "systems_on_network": len(systems_on_network),
            "has_critical_systems": has_critical_systems,
            "connected_networks": len(context.get_neighbors(RelationshipType.CONNECTS_TO)),
            "cidr": getattr(entity, "cidr", ""),
        }
        return profile

    def _system_is_critical(self, system: BaseEntity) -> bool:
        """Heuristic: determine if a system is critical."""
        system_type = getattr(system, "system_type", "").lower()
        name = getattr(system, "name", "").lower()

        critical_keywords = [
            "payment",
            "auth",
            "identity",
            "core",
            "main",
            "critical",
            "database",
            "data warehouse",
        ]
        return any(keyword in system_type or keyword in name for keyword in critical_keywords)

    def _populate_tier_2(
        self, entity: BaseEntity, context: EntityContext, network_profile: dict
    ) -> tuple[dict, list]:
        """Populate Tier 2 (Managed) fields: core operational."""
        updates = {}
        actions = []

        # Security zone determination
        zone = network_profile.get("zone", "internal")
        # Infer zone from system types if not explicitly set
        if zone == "internal" and network_profile.get("has_critical_systems"):
            zone = "restricted"
        elif zone == "internal" and network_profile.get("systems_on_network", 0) > 20:
            zone = "internal"  # Large internal network

        updates["security_zone"] = zone
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.NETWORK,
                fields_enriched=["security_zone"],
                source="Zone classification engine",
                methodology=f"Inferred from system criticality (critical={network_profile.get('has_critical_systems')})",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Bandwidth capacity from zone
        bandwidth = BANDWIDTH_TEMPLATES.get(zone, "500 Mbps")
        updates["bandwidth_capacity"] = bandwidth
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.NETWORK,
                fields_enriched=["bandwidth_capacity"],
                source="Zone-based bandwidth policy",
                methodology=f"Lookup from BANDWIDTH_TEMPLATES[{zone}]",
                confidence=ConfidenceLevel.HIGH,
            )
        )

        return updates, actions

    def _populate_tier_3(
        self, entity: BaseEntity, context: EntityContext, network_profile: dict
    ) -> tuple[dict, list]:
        """Populate Tier 3 (Defined) fields: cross-entity coherence."""
        updates = {}
        actions = []

        zone = network_profile.get("zone", "internal")

        # Monitoring status from zone
        monitoring = MONITORING_STATUS_TEMPLATES.get(zone, "Partially Monitored")
        updates["monitoring_status"] = monitoring
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.NETWORK,
                fields_enriched=["monitoring_status"],
                source="Security zone policies",
                methodology=f"Policy-driven assignment for zone '{zone}'",
                confidence=ConfidenceLevel.HIGH,
            )
        )

        # Segmentation policy
        has_critical = network_profile.get("has_critical_systems", False)
        system_count = network_profile.get("systems_on_network", 0)

        if has_critical:
            segmentation = "Micro-segmentation with network ACLs"
        elif system_count > 50:
            segmentation = "VLAN-based segmentation"
        else:
            segmentation = "Basic segmentation"

        updates["segmentation_policy"] = segmentation
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.NETWORK,
                fields_enriched=["segmentation_policy"],
                source="Segmentation requirement analysis",
                methodology=f"Determined by criticality={has_critical} and density={system_count}",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        return updates, actions

    def _populate_tier_4(
        self, entity: BaseEntity, context: EntityContext, network_profile: dict
    ) -> tuple[dict, list]:
        """Populate Tier 4 (Measured) fields: quantitative metrics."""
        updates = {}
        actions = []

        zone = network_profile.get("zone", "internal")
        system_count = network_profile.get("systems_on_network", 0)

        # Traffic metrics (inferred)
        traffic_utilization = min(95, 30 + (system_count * 2))
        updates["traffic_metrics"] = {
            "average_utilization_pct": traffic_utilization,
            "peak_utilization_pct": min(99, traffic_utilization + 20),
            "packet_loss_pct": 0.01 if zone == "internal" else 0.05,
            "latency_ms": 1 if zone in ["restricted", "internal"] else 10,
        }
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.NETWORK,
                fields_enriched=["traffic_metrics"],
                source="Network load modeling",
                methodology=f"Derived from system count={system_count} and zone='{zone}'",
                confidence=ConfidenceLevel.LOW,
            )
        )

        return updates, actions

    def _populate_tier_5(
        self, entity: BaseEntity, context: EntityContext, network_profile: dict
    ) -> tuple[dict, list]:
        """Populate Tier 5 (Optimized) fields: optimization recommendations."""
        updates = {}
        actions = []

        zone = network_profile.get("zone", "internal")
        system_count = network_profile.get("systems_on_network", 0)
        connected_networks = network_profile.get("connected_networks", 0)

        recommendations = []

        # Generate zone-specific recommendations
        if zone == "internal" and system_count > 50:
            recommendations.append(
                {
                    "recommendation": "Implement VLAN sub-segmentation",
                    "benefit": "Improved traffic isolation and performance",
                    "effort": "Medium",
                    "estimated_savings": 0,
                }
            )

        if zone == "dmz" and connected_networks > 3:
            recommendations.append(
                {
                    "recommendation": "Deploy jump-host architecture",
                    "benefit": "Enhanced security posture",
                    "effort": "High",
                    "estimated_savings": 0,
                }
            )

        if zone == "restricted":
            recommendations.append(
                {
                    "recommendation": "Enable encrypted traffic monitoring",
                    "benefit": "Better visibility without decryption",
                    "effort": "Low",
                    "estimated_savings": 0,
                }
            )

        # Bandwidth optimization
        if zone != "external":
            recommendations.append(
                {
                    "recommendation": "Monitor QoS and implement traffic shaping",
                    "benefit": "Prevent bandwidth congestion",
                    "effort": "Low",
                    "estimated_savings": 50000,
                }
            )

        updates["optimization_recommendations"] = recommendations
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.NETWORK,
                fields_enriched=["optimization_recommendations"],
                source="Network optimization engine",
                methodology="Zone + density-based heuristics",
                confidence=ConfidenceLevel.LOW,
            )
        )

        return updates, actions

    def _identify_gaps(self, entity: BaseEntity, network_profile: dict) -> list[DataGap]:
        """Identify known data gaps."""
        gaps = []

        # Check for missing key attributes
        if not getattr(entity, "gateway", None):
            gaps.append(
                DataGap(
                    field_name="gateway",
                    description="Network gateway IP not specified",
                    severity="Medium",
                    remediation_suggestion="Define default gateway for network",
                )
            )

        if not getattr(entity, "dns_servers", None) or len(getattr(entity, "dns_servers", [])) == 0:
            gaps.append(
                DataGap(
                    field_name="dns_servers",
                    description="No DNS servers configured",
                    severity="High",
                    remediation_suggestion="Configure primary and secondary DNS servers",
                )
            )

        if network_profile.get("systems_on_network", 0) == 0:
            gaps.append(
                DataGap(
                    field_name="systems_on_network",
                    description="No systems linked to this network",
                    severity="Medium",
                    remediation_suggestion="Link systems via RUNS_ON relationships",
                )
            )

        if not getattr(entity, "location_id", None):
            gaps.append(
                DataGap(
                    field_name="location_id",
                    description="Network location/site not specified",
                    severity="Low",
                    remediation_suggestion="Link to Location entity via LOCATED_AT relationship",
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

        primary_source = "Enrichment Agency - Network Enricher"
        if actions:
            primary_source += f" ({len(actions)} fields enriched)"

        return ProvenanceAndConfidence(
            primary_data_source=primary_source,
            last_assessed_date=datetime.now(UTC).isoformat(),
            assessed_by="NetworkEnricher v1.0",
            assessment_methodology="Zone-aware security profiling + neighbor topology analysis",
            confidence_level=confidence_map.get(tier, "Medium"),
        )
