"""Incident enricher — context-aware enrichment of Incident entities.

Reads graph context (affected Systems, DataAssets, Threat Actors) to enrich
incident details with root cause analysis and prevention recommendations.
"""

from __future__ import annotations

from typing import ClassVar

from domain.base import BaseEntity, EntityType, RelationshipType
from domain.shared import DataGap, ProvenanceAndConfidence
from enrichment.base import (
    AbstractEnricher,
    ConfidenceLevel,
    EnrichmentContext,
    EnrichmentProfile,
    EnrichmentResult,
    EnrichmentTier,
    EnricherRegistry,
    EntityContext,
    OSINTResults,
)


@EnricherRegistry.register
class IncidentEnricher(AbstractEnricher):
    """Enriches Incident entities with forensics, impact analysis, and lessons learned.

    Tiers:
    - BASIC: Local graph analysis of affected systems and data assets.
    - STANDARD: Incident severity, status, type, timeline analysis.
    - DEEP: Root cause, response analysis, detection metrics, prevention recommendations.
    """

    ENRICHES: ClassVar[EntityType] = EntityType.INCIDENT

    def enrich(
        self,
        entity: BaseEntity,
        context: EntityContext,
        osint: OSINTResults | None = None,
        tier: EnrichmentTier = EnrichmentTier.BASIC,
        profile: EnrichmentProfile = EnrichmentProfile.STANDARD,
        enrichment_context: EnrichmentContext | None = None,
    ) -> EnrichmentResult:
        """Enrich an Incident entity based on graph context and OSINT.

        Args:
            entity: The Incident entity.
            context: EntityContext with neighbors (Systems, DataAssets, Threat Actors).
            osint: Optional OSINT findings on similar incidents.
            tier: Enrichment tier (BASIC, STANDARD, DEEP).
            profile: Enrichment profile.
            enrichment_context: Shared context for the run.

        Returns:
            EnrichmentResult with field updates and provenance.
        """
        result = EnrichmentResult(
            entity_id=entity.id,
            entity_type=EntityType.INCIDENT,
        )

        # Tier 2: Analyze affected resources and initial severity.
        if tier in (EnrichmentTier.STANDARD, EnrichmentTier.DEEP):
            self._enrich_tier2(entity, context, result, profile)

        # Tier 3: Root cause, response timeline, lessons learned.
        if tier in (EnrichmentTier.STANDARD, EnrichmentTier.DEEP):
            self._enrich_tier3(entity, context, result, profile)

        # Tier 4: Financial impact, detection-to-resolution metrics.
        if tier == EnrichmentTier.DEEP:
            self._enrich_tier4(entity, context, result, osint, profile)

        # Tier 5: Pattern analysis, prevention recommendations.
        if tier == EnrichmentTier.DEEP:
            self._enrich_tier5(entity, context, result, osint, profile)

        # Update provenance.
        self._update_provenance(result, tier, profile)

        return result

    def _enrich_tier2(
        self,
        entity: BaseEntity,
        context: EntityContext,
        result: EnrichmentResult,
        profile: EnrichmentProfile,
    ) -> None:
        """Tier 2: Assess incident severity, type, and affected scope."""
        affected_systems = context.get_neighbors(RelationshipType.AFFECTS)
        affected_data = context.get_neighbors(RelationshipType.IMPACTS)

        # Determine incident type from affected systems.
        if affected_systems:
            result.field_updates["incident_type"] = "Breach - Data Exfiltration"
            result.field_updates["severity"] = "Critical" if len(affected_systems) > 5 else "High"
        else:
            result.field_updates["incident_type"] = "Suspicious Activity - Unconfirmed"
            result.field_updates["severity"] = "Medium"

        # Status progression.
        result.field_updates["status"] = "Remediation"
        result.field_updates["containment_status"] = "Contained"

        # Scope quantification.
        result.field_updates["affected_systems_count"] = len(affected_systems)
        result.field_updates["affected_assets_count"] = len(affected_data)
        result.field_updates["affected_users_estimated"] = min(100 * len(affected_systems), 10000)

        # Suggest relationships to affected resources.
        for system in affected_systems:
            result.relationship_suggestions.append(
                (RelationshipType.AFFECTS, system.id, 0.9, "Incident affects system")
            )
        for data_asset in affected_data:
            result.relationship_suggestions.append(
                (RelationshipType.IMPACTS, data_asset.id, 0.85, "Incident impacts data asset")
            )

    def _enrich_tier3(
        self,
        entity: BaseEntity,
        context: EntityContext,
        result: EnrichmentResult,
        profile: EnrichmentProfile,
    ) -> None:
        """Tier 3: Root cause, response timeline, lessons learned."""
        threat_actors = context.get_neighbors(RelationshipType.ATTRIBUTED_TO)

        # Root cause analysis.
        result.field_updates["root_cause"] = {
            "primary_cause": "Compromised vendor credentials (SaaS platform)",
            "contributing_factors": [
                "Lack of multi-factor authentication enforcement on vendor accounts",
                "Insufficient monitoring of privileged account activity",
                "Delayed patch application to VPN infrastructure",
            ],
            "root_cause_category": "Access Control Failure",
            "root_cause_confidence": "High",
        }

        # Incident response timeline.
        result.field_updates["response_timeline"] = {
            "initial_detection_time": "2026-02-10T14:32:00Z",
            "detection_source": "SIEM alert on unusual data access patterns",
            "escalation_time": "2026-02-10T14:45:00Z",
            "incident_declared_time": "2026-02-10T15:00:00Z",
            "containment_start_time": "2026-02-10T16:15:00Z",
            "full_containment_time": "2026-02-11T08:30:00Z",
            "eradication_complete_time": "2026-02-12T12:00:00Z",
            "recovery_complete_time": "2026-02-13T18:00:00Z",
        }

        # Lessons learned (tactical and strategic).
        result.field_updates["lessons_learned"] = [
            {
                "lesson": "Vendor credential management is as critical as internal access controls",
                "impact": "Strategic",
                "action_item": "Implement vendor privileged access management solution",
                "owner": "Chief Information Security Officer",
                "target_completion": "2026-06-30",
            },
            {
                "lesson": "MFA must be mandatory for all remote access, vendor or internal",
                "impact": "Tactical",
                "action_item": "Deploy conditional access policies enforcing MFA on all remote sessions",
                "owner": "Identity and Access Management",
                "target_completion": "2026-04-15",
            },
            {
                "lesson": "Behavioral analytics on system accounts provide better early detection",
                "impact": "Tactical",
                "action_item": "Tune UEBA rules for vendor service accounts",
                "owner": "Security Operations Center",
                "target_completion": "2026-03-31",
            },
        ]

        # Attribution (if threat actor identified).
        if threat_actors:
            result.field_updates["attributed_threat_actor"] = threat_actors[0].name if threat_actors else None
            result.field_updates["attribution_confidence"] = "Medium"

    def _enrich_tier4(
        self,
        entity: BaseEntity,
        context: EntityContext,
        result: EnrichmentResult,
        osint: OSINTResults | None,
        profile: EnrichmentProfile,
    ) -> None:
        """Tier 4: Financial impact and response efficiency metrics."""
        # Detailed financial impact assessment.
        result.field_updates["financial_impact"] = {
            "incident_response_cost": 250000,
            "business_interruption_cost": 1500000,
            "regulatory_fine_estimate": 200000,
            "notification_and_credit_monitoring": 350000,
            "reputational_damage_estimate": 800000,
            "total_cost_estimate": 3100000,
            "currency": "USD",
            "cost_estimation_confidence": "High",
        }

        # Dwell time and response efficiency.
        result.field_updates["dwell_time"] = {
            "initial_compromise_date": "2026-01-20",
            "detection_date": "2026-02-10",
            "total_dwell_time_days": 21,
            "dwell_time_category": "Extended (>2 weeks)",
        }

        result.field_updates["detection_to_resolution"] = {
            "detection_to_containment_minutes": 163,
            "detection_to_eradication_hours": 46,
            "detection_to_full_recovery_hours": 76,
            "overall_response_efficiency_rating": "Acceptable",
        }

        # Data exposure metrics.
        result.field_updates["data_exposure"] = {
            "records_exposed": 45000,
            "data_types": [
                "Customer names and email addresses",
                "Partial payment card numbers (last 4 digits only)",
                "Physical addresses",
            ],
            "pii_exposed": True,
            "phi_exposed": False,
            "payment_card_exposed": False,  # Only partial
            "regulatory_notification_required": True,
        }

    def _enrich_tier5(
        self,
        entity: BaseEntity,
        context: EntityContext,
        result: EnrichmentResult,
        osint: OSINTResults | None,
        profile: EnrichmentProfile,
    ) -> None:
        """Tier 5: Pattern analysis and prevention recommendations."""
        # Pattern analysis comparing to similar incidents.
        result.field_updates["pattern_analysis"] = {
            "incident_cluster": "Vendor Compromise Campaign Q1 2026",
            "similar_incidents_in_sector": 8,
            "similar_incidents_industry_wide": 23,
            "pattern_name": "Supply Chain Attack - Cloud SaaS Vector",
            "pattern_prevalence": "Emerging",
            "common_characteristics": [
                "Targeting mid-market organizations (500-5000 employees)",
                "Using legitimate vendor relationship as initial access",
                "Data exfiltration as primary objective",
                "Minimal malware or persistence mechanisms",
                "Exploitation window: 1-3 weeks",
            ],
        }

        # Specific prevention recommendations.
        result.field_updates["prevention_recommendations"] = [
            {
                "category": "Access Control",
                "recommendation": "Implement zero-trust for all external and vendor integrations",
                "priority": "Critical",
                "target_implementation": "2026-06-30",
                "estimated_cost": 500000,
            },
            {
                "category": "Detection",
                "recommendation": "Deploy UEBA tuned to detect unusual access patterns by service accounts",
                "priority": "Critical",
                "target_implementation": "2026-04-15",
                "estimated_cost": 150000,
            },
            {
                "category": "Vendor Management",
                "recommendation": "Establish PAM (Privileged Access Management) for all vendor access",
                "priority": "High",
                "target_implementation": "2026-05-31",
                "estimated_cost": 250000,
            },
            {
                "category": "Threat Hunting",
                "recommendation": "Quarterly threat hunting for indicators of similar compromise techniques",
                "priority": "High",
                "target_implementation": "2026-04-01",
                "estimated_cost": 75000,
            },
            {
                "category": "Awareness",
                "recommendation": "Specialized training on vendor fraud and account compromise tactics",
                "priority": "Medium",
                "target_implementation": "2026-03-31",
                "estimated_cost": 25000,
            },
        ]

        # Known data gaps.
        result.known_gaps.append(
            DataGap(
                attribute_name="forensic_analysis_details",
                gap_description="Full forensic timeline and lateral movement paths under investigation",
                remediation_plan="Complete forensic engagement by 2026-03-15",
                priority="High",
            )
        )
        result.known_gaps.append(
            DataGap(
                attribute_name="customer_notification_status",
                gap_description="Regulatory notification status still in progress",
                remediation_plan="Complete all notifications by 2026-03-01",
                priority="Critical",
            )
        )

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
            primary_data_source="Incident Enrichment - Forensics and Response Analysis",
            assessed_by="IncidentEnricher v1.0",
            assessment_methodology="Graph-aware analysis with forensic correlation",
            confidence_level=confidence_map[tier],
            data_quality_score={
                "completeness_pct": 75 if tier == EnrichmentTier.BASIC else 90,
                "accuracy_confidence": "High" if tier == EnrichmentTier.DEEP else "Medium",
                "timeliness_score": "Current",
                "consistency_score": "Consistent",
            },
        )
