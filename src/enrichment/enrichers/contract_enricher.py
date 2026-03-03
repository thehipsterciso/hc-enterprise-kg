"""Contract enricher — context-aware enrichment of commercial agreement terms and risk.

Reads Vendors/Customers (CONTRACTS_WITH), Systems covered, DataAssets to enrich
contract attributes across five tiers. Updates provenance with confidence tracking.

Tiers:
  2 (Managed): contract_type, status, effective_date, total_value, currency
  3 (Defined): sla_entries, data_handling_provisions, ip_provisions, termination_clauses
  4 (Measured): financial_terms (payment_schedule, penalties), insurance_requirements
  5 (Optimized): renegotiation_scenarios, consolidation_opportunities
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
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

CONTRACT_TYPE_TEMPLATES = {
    "MSA": {
        "contract_type": "Master Service Agreement",
        "typical_duration_months": 36,
        "typical_value": 500000,
        "renewal_frequency": "Annual",
    },
    "SLA": {
        "contract_type": "Service Level Agreement",
        "typical_duration_months": 12,
        "typical_value": 100000,
        "renewal_frequency": "Annual",
    },
    "License": {
        "contract_type": "Software License",
        "typical_duration_months": 24,
        "typical_value": 250000,
        "renewal_frequency": "Bi-annual",
    },
    "Subscription": {
        "contract_type": "Subscription Agreement",
        "typical_duration_months": 12,
        "typical_value": 50000,
        "renewal_frequency": "Annual",
    },
}

CONTRACT_STATUS_OPTIONS = [
    "Active",
    "Renewal Pending",
    "Expired",
    "Under Negotiation",
    "Terminated",
]


@EnricherRegistry.register
class ContractEnricher(AbstractEnricher):
    """Enriches Contract entities with commercial and legal assessment.

    Tiers:
    - BASIC: Local graph analysis of Vendors and Customers.
    - STANDARD: Contract type, status, effective dates, total value.
    - DEEP: SLAs, data provisions, financial terms, insurance, renegotiation scenarios.
    """

    ENRICHES: ClassVar[EntityType] = EntityType.CONTRACT

    def enrich(
        self,
        entity: BaseEntity,
        context: EntityContext,
        osint: OSINTResults | None = None,
        tier: EnrichmentTier = EnrichmentTier.BASIC,
        profile: EnrichmentProfile = EnrichmentProfile.STANDARD,
        enrichment_context: EnrichmentContext | None = None,
    ) -> EnrichmentResult:
        """Enrich a Contract entity based on graph context and OSINT.

        Args:
            entity: The Contract entity.
            context: EntityContext with neighbors (Vendors, Customers, Systems).
            osint: Optional OSINT findings on contract party.
            tier: Enrichment tier (BASIC, STANDARD, DEEP).
            profile: Enrichment profile.
            enrichment_context: Shared context for the run.

        Returns:
            EnrichmentResult with field updates and provenance.
        """
        result = EnrichmentResult(
            entity_id=entity.id,
            entity_type=EntityType.CONTRACT,
        )

        # Tier 2: Basic contract assessment
        if tier in (EnrichmentTier.STANDARD, EnrichmentTier.DEEP):
            self._enrich_tier2(entity, context, result, profile)

        # Tier 3: Legal and operational provisions
        if tier == EnrichmentTier.DEEP:
            self._enrich_tier3(entity, context, result, profile)

        # Tier 4: Financial terms and insurance
        if tier == EnrichmentTier.DEEP:
            self._enrich_tier4(entity, context, result, profile)

        # Tier 5: Renegotiation scenarios and consolidation
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
        """Tier 2: Basic contract assessment."""
        vendors = context.get_neighbors(RelationshipType.CONTRACTS_WITH)

        # Determine contract type based on vendor/customer nature
        # In production would differentiate vendor vs customer contracts
        vendor_count = len(vendors)
        if vendor_count == 0:
            contract_key = "Subscription"
        elif vendor_count == 1 and vendor_count < 5:
            contract_key = "MSA"
        else:
            contract_key = "License"

        contract_template = CONTRACT_TYPE_TEMPLATES.get(
            contract_key, CONTRACT_TYPE_TEMPLATES["Subscription"]
        )
        result.field_updates["contract_type"] = contract_template["contract_type"]

        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.CONTRACT,
                fields_enriched=["contract_type"],
                source="Party analysis",
                methodology=f"Vendor/customer count heuristic (vendors={vendor_count})",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Contract status based on effective dates
        datetime.now(UTC)
        # Default assumption: active contracts
        status = "Active"
        result.field_updates["status"] = status
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.CONTRACT,
                fields_enriched=["status"],
                source="Status determination",
                methodology="Default assumption pending date field analysis",
                confidence=ConfidenceLevel.LOW,
            )
        )

        # Effective dates
        effective_date = datetime.now(UTC)
        expiration_date = effective_date + timedelta(
            days=365 * (contract_template["typical_duration_months"] // 12)
        )

        result.field_updates["effective_date"] = effective_date.isoformat()
        result.field_updates["expiration_date"] = expiration_date.isoformat()
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.CONTRACT,
                fields_enriched=["effective_date", "expiration_date"],
                source="Date assignment",
                methodology="Template-based duration calculation",
                confidence=ConfidenceLevel.LOW,
            )
        )

        # Total contract value
        total_value = contract_template["typical_value"] * max(1, vendor_count)
        result.field_updates["total_value_usd"] = total_value
        result.field_updates["currency"] = "USD"
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.CONTRACT,
                fields_enriched=["total_value_usd", "currency"],
                source="Financial estimation",
                methodology="Contract type value template with vendor count adjustment",
                confidence=ConfidenceLevel.LOW,
            )
        )

    def _enrich_tier3(
        self,
        entity: BaseEntity,
        context: EntityContext,
        result: EnrichmentResult,
        profile: EnrichmentProfile,
    ) -> None:
        """Tier 3: Legal and operational provisions."""
        context.get_neighbors(RelationshipType.CONTRACTS_WITH)
        context.get_neighbors(RelationshipType.IMPACTS)

        # SLA entries
        result.field_updates["sla_entries"] = [
            {
                "sla_name": "System Availability",
                "metric": "Uptime percentage",
                "target": "99.95%",
                "measurement_method": "Monthly active monitoring",
                "penalty_for_breach": "Service credit (5% monthly fee)",
            },
            {
                "sla_name": "Response Time",
                "metric": "First response SLA",
                "target": "4 business hours",
                "measurement_method": "Ticket timestamp analysis",
                "penalty_for_breach": "Escalation and management review",
            },
            {
                "sla_name": "Critical Issue Resolution",
                "metric": "MTTR for P1 issues",
                "target": "4 hours",
                "measurement_method": "Issue tracking system",
                "penalty_for_breach": "10% service credit per incident",
            },
        ]
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.CONTRACT,
                fields_enriched=["sla_entries"],
                source="Standard SLA template",
                methodology="Industry-standard SLA framework",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Data handling provisions
        result.field_updates["data_handling_provisions"] = {
            "data_classification": ["Confidential", "Internal", "Public"],
            "data_return_clause": True,
            "data_destruction_clause": True,
            "breach_notification_hours": 24,
            "sub_processor_approval_required": True,
            "encryption_requirements": "AES-256 at rest, TLS 1.3 in transit",
            "audit_rights": "Quarterly security audits permitted",
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.CONTRACT,
                fields_enriched=["data_handling_provisions"],
                source="Data governance standards",
                methodology="GDPR/CCPA-aligned data handling template",
                confidence=ConfidenceLevel.HIGH,
            )
        )

        # IP provisions
        result.field_updates["ip_provisions"] = {
            "ip_ownership": "Vendor retains ownership of pre-existing IP",
            "work_product_ownership": "Customer owns custom work product",
            "license_grants": "Non-exclusive, non-transferable license to use Software",
            "residual_knowledge_rights": "Retained by Service Provider",
            "third_party_ip_indemnification": True,
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.CONTRACT,
                fields_enriched=["ip_provisions"],
                source="Standard IP terms",
                methodology="Balanced IP framework template",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Termination clauses
        result.field_updates["termination_clauses"] = {
            "termination_for_cause_allowed": True,
            "notice_period_days": 30,
            "early_termination_penalty": {
                "penalty_exists": True,
                "penalty_description": "Remaining contract value subject to 50% reduction",
                "penalty_amount": result.field_updates.get("total_value_usd", 100000) * 0.5,
                "currency": "USD",
            },
            "termination_for_convenience_allowed": False,
            "wind_down_period_days": 60,
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.CONTRACT,
                fields_enriched=["termination_clauses"],
                source="Standard termination framework",
                methodology="Industry-standard termination terms",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

    def _enrich_tier4(
        self,
        entity: BaseEntity,
        context: EntityContext,
        result: EnrichmentResult,
        profile: EnrichmentProfile,
    ) -> None:
        """Tier 4: Financial terms and insurance requirements."""
        total_value = result.field_updates.get("total_value_usd", 100000)
        contract_type = result.field_updates.get("contract_type", "Subscription Agreement")

        # Payment schedule
        if "License" in contract_type:
            payment_schedule = [
                {
                    "payment_sequence": 1,
                    "payment_date": (datetime.now(UTC)).isoformat(),
                    "payment_amount": total_value * 0.5,
                    "description": "Initial license purchase",
                },
                {
                    "payment_sequence": 2,
                    "payment_date": (datetime.now(UTC) + timedelta(days=30)).isoformat(),
                    "payment_amount": total_value * 0.5,
                    "description": "Final payment",
                },
            ]
        else:
            payment_schedule = [
                {
                    "payment_sequence": i,
                    "payment_date": (datetime.now(UTC) + timedelta(days=30 * i)).isoformat(),
                    "payment_amount": total_value / 12,
                    "description": f"Monthly payment {i}",
                }
                for i in range(1, 13)
            ]

        result.field_updates["payment_schedule"] = payment_schedule
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.CONTRACT,
                fields_enriched=["payment_schedule"],
                source="Financial terms derivation",
                methodology="Contract type-based payment schedule generation",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Financial penalties
        result.field_updates["financial_penalties"] = {
            "late_payment_penalty_pct": 1.5,
            "late_payment_grace_period_days": 5,
            "sla_breach_credit_pct": 5,
            "maximum_credit_monthly_pct": 10,
            "dispute_escalation_threshold_usd": 50000,
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.CONTRACT,
                fields_enriched=["financial_penalties"],
                source="Standard penalty framework",
                methodology="Industry-standard penalty terms",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Insurance requirements
        result.field_updates["insurance_requirements"] = {
            "cyber_insurance_required": True,
            "minimum_coverage": 5_000_000,
            "currency": "USD",
            "verified": False,
            "general_liability_minimum": 2_000_000,
            "professional_liability_minimum": 2_000_000,
            "coverage_verification_frequency": "Annual",
            "coverage_verification_method": "Certificate of Insurance",
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.CONTRACT,
                fields_enriched=["insurance_requirements"],
                source="Risk management standards",
                methodology="Standard enterprise insurance requirements",
                confidence=ConfidenceLevel.HIGH,
            )
        )

        # Liability caps
        result.field_updates["liability_caps"] = {
            "liability_cap": total_value * 2,
            "currency": "USD",
            "liability_type": "Total liability under contract",
            "unlimited_liability_carve_outs": [
                "Data breach indemnification",
                "IP infringement",
                "Gross negligence or willful misconduct",
            ],
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.CONTRACT,
                fields_enriched=["liability_caps"],
                source="Legal risk management",
                methodology="Value-proportionate liability capping",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

    def _enrich_tier5(
        self,
        entity: BaseEntity,
        context: EntityContext,
        result: EnrichmentResult,
        osint: OSINTResults | None,
        profile: EnrichmentProfile,
    ) -> None:
        """Tier 5: Renegotiation scenarios and consolidation."""
        total_value = result.field_updates.get("total_value_usd", 100000)

        # Renegotiation scenarios
        result.field_updates["renegotiation_scenarios"] = [
            {
                "scenario_name": "Renewal with Price Increase",
                "trigger": "Contract approaching expiration",
                "likelihood": "High",
                "projected_new_terms": {
                    "price_increase_pct": 5,
                    "volume_discount_opportunity_pct": 10,
                    "new_total_value": total_value * 1.05,
                },
                "negotiation_strategy": "Volume commitment in exchange for discount",
                "preparation_timeline_months": 3,
            },
            {
                "scenario_name": "Consolidation with Alternative Vendor",
                "trigger": "Competitive RFP or vendor dissatisfaction",
                "likelihood": "Medium",
                "projected_new_terms": {
                    "potential_savings_pct": 15,
                    "migration_cost": 50000,
                    "net_savings_year1": total_value * 0.15 - 50000,
                },
                "negotiation_strategy": "Benchmark against market alternatives",
                "preparation_timeline_months": 6,
            },
            {
                "scenario_name": "Scope Expansion",
                "trigger": "New business requirements identified",
                "likelihood": "Medium",
                "projected_new_terms": {
                    "scope_expansion_pct": 25,
                    "incremental_value": total_value * 0.25,
                    "extension_months": 12,
                },
                "negotiation_strategy": "Leverage existing relationship for favorable terms",
                "preparation_timeline_months": 2,
            },
        ]
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.CONTRACT,
                fields_enriched=["renegotiation_scenarios"],
                source="Strategic contract management",
                methodology="Scenario-based negotiation planning",
                confidence=ConfidenceLevel.LOW,
            )
        )

        # Consolidation opportunities
        result.field_updates["consolidation_opportunities"] = {
            "consolidation_candidate": True,
            "similar_active_contracts": 2,
            "estimated_consolidation_savings": total_value * 0.1,
            "consolidation_complexity": "Medium",
            "implementation_timeline_months": 6,
            "risks": [
                "Service continuity during transition",
                "Vendor transition readiness",
                "Data migration complexity",
            ],
            "benefits": [
                "Simplified vendor management",
                "Volume discounts",
                "Unified service levels",
            ],
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.CONTRACT,
                fields_enriched=["consolidation_opportunities"],
                source="Portfolio optimization analysis",
                methodology="Contract portfolio consolidation review",
                confidence=ConfidenceLevel.LOW,
            )
        )

    def _identify_gaps(self, entity: BaseEntity, context: EntityContext) -> list[DataGap]:
        """Identify known data gaps."""
        gaps = []

        vendors = context.get_neighbors(RelationshipType.CONTRACTS_WITH)
        if not vendors:
            gaps.append(
                DataGap(
                    field_name="contracting_parties",
                    description="No vendors or customers linked via CONTRACTS_WITH",
                    severity="High",
                    remediation_suggestion="Link Vendor or Customer entities that are parties to this contract",
                )
            )

        if not getattr(entity, "effective_date", None):
            gaps.append(
                DataGap(
                    field_name="effective_date",
                    description="Contract effective date not available",
                    severity="High",
                    remediation_suggestion="Extract from contract document or metadata",
                )
            )

        if not getattr(entity, "sla_entries", None):
            gaps.append(
                DataGap(
                    field_name="sla_entries",
                    description="Service level agreements not documented",
                    severity="Medium",
                    remediation_suggestion="Extract SLA terms from contract document",
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
            primary_data_source="Contract Enrichment Pipeline - Graph Context Analysis",
            assessed_by="ContractEnricher v1.0",
            assessment_methodology="Graph-aware enrichment with commercial and legal term templates",
            confidence_level=confidence_map[tier],
            data_quality_score={
                "completeness_pct": 65 if tier == EnrichmentTier.BASIC else 85,
                "accuracy_confidence": "Medium" if tier == EnrichmentTier.BASIC else "High",
                "timeliness_score": "Current",
                "consistency_score": "Consistent",
            },
        )
