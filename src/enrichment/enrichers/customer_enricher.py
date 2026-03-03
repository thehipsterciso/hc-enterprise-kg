"""Customer enricher — context-aware enrichment of customer engagement and financial metrics.

Reads Products (BUYS), Contracts (CONTRACTS_WITH), MarketSegments to enrich
customer attributes across five tiers. Updates provenance with confidence tracking.

Tiers:
  2 (Managed): customer_type, industry, status, customer_tier, primary_contact
  3 (Defined): account_team, engagement_metrics, satisfaction_score, support_history
  4 (Measured): financial_summary (revenue, lifetime_value, payment_history), risk_assessment
  5 (Optimized): predictive_churn_score, expansion_potential, strategic_value_assessment
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar

from domain.base import BaseEntity, EntityType, RelationshipType
from domain.shared import DataGap, ProvenanceAndConfidence
from enrichment.base import (
    AbstractEnricher,
    ConfidenceLevel,
    EnrichmentAction,
    EnrichmentContext,
    EnrichmentProfile,
    EnrichmentResult,
    EnrichmentTier,
    EntityContext,
    EnricherRegistry,
    OSINTResults,
)


CUSTOMER_TYPE_TEMPLATES = {
    "Enterprise": {
        "customer_type": "Enterprise",
        "typical_size": 5000,
        "annual_spend": 500000,
        "tier": "Platinum",
    },
    "Mid-Market": {
        "customer_type": "Mid-Market",
        "typical_size": 500,
        "annual_spend": 75000,
        "tier": "Gold",
    },
    "SMB": {
        "customer_type": "Small Business",
        "typical_size": 50,
        "annual_spend": 15000,
        "tier": "Silver",
    },
    "Internal": {
        "customer_type": "Internal",
        "typical_size": None,
        "annual_spend": 0,
        "tier": "Internal",
    },
}

CUSTOMER_STATUS_OPTIONS = ["Active", "Growth", "At Risk", "Churned", "Prospect"]


@EnricherRegistry.register
class CustomerEnricher(AbstractEnricher):
    """Enriches Customer entities with engagement and financial assessment.

    Tiers:
    - BASIC: Local graph analysis of purchased Products and Contracts.
    - STANDARD: Customer type, industry, status, tier, primary contact.
    - DEEP: Account team, engagement, satisfaction, financial summary, churn/expansion analysis.
    """

    ENRICHES: ClassVar[EntityType] = EntityType.CUSTOMER

    def enrich(
        self,
        entity: BaseEntity,
        context: EntityContext,
        osint: OSINTResults | None = None,
        tier: EnrichmentTier = EnrichmentTier.BASIC,
        profile: EnrichmentProfile = EnrichmentProfile.STANDARD,
        enrichment_context: EnrichmentContext | None = None,
    ) -> EnrichmentResult:
        """Enrich a Customer entity based on graph context and OSINT.

        Args:
            entity: The Customer entity.
            context: EntityContext with neighbors (Products, Contracts, MarketSegments).
            osint: Optional OSINT findings on customer organization.
            tier: Enrichment tier (BASIC, STANDARD, DEEP).
            profile: Enrichment profile.
            enrichment_context: Shared context for the run.

        Returns:
            EnrichmentResult with field updates and provenance.
        """
        result = EnrichmentResult(
            entity_id=entity.id,
            entity_type=EntityType.CUSTOMER,
        )

        # Tier 2: Basic customer assessment
        if tier in (EnrichmentTier.STANDARD, EnrichmentTier.DEEP):
            self._enrich_tier2(entity, context, result, profile)

        # Tier 3: Engagement and relationship assessment
        if tier == EnrichmentTier.DEEP:
            self._enrich_tier3(entity, context, result, profile)

        # Tier 4: Financial summary and risk assessment
        if tier == EnrichmentTier.DEEP:
            self._enrich_tier4(entity, context, result, profile)

        # Tier 5: Predictive churn and expansion potential
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
        """Tier 2: Basic customer assessment."""
        products = context.get_neighbors(RelationshipType.BUYS)
        contracts = context.get_neighbors(RelationshipType.CONTRACTS_WITH)

        # Determine customer type based on product count and contract maturity
        product_count = len(products)
        contract_count = len(contracts)

        if product_count == 0:
            customer_key = "Prospect"
            status = "Prospect"
        elif product_count < 2:
            customer_key = "SMB"
            status = "Active"
        elif product_count < 5:
            customer_key = "Mid-Market"
            status = "Growth"
        else:
            customer_key = "Enterprise"
            status = "Active"

        customer_template = CUSTOMER_TYPE_TEMPLATES.get(customer_key, CUSTOMER_TYPE_TEMPLATES["SMB"])
        result.field_updates["customer_type"] = customer_template["customer_type"]
        result.field_updates["status"] = status

        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.CUSTOMER,
                fields_enriched=["customer_type", "status"],
                source="Product and contract analysis",
                methodology=f"Product/contract count heuristic (products={product_count}, contracts={contract_count})",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Industry classification
        result.field_updates["industry_classification"] = {
            "classification_standard": "NAICS",
            "code": "521210",
            "description": "Securities Brokerage",
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.CUSTOMER,
                fields_enriched=["industry_classification"],
                source="Placeholder industry assignment",
                methodology="Default placeholder pending OSINT or CRM lookup",
                confidence=ConfidenceLevel.LOW,
            )
        )

        # Customer tier
        tier_mapping = customer_template["tier"]
        result.field_updates["customer_tier"] = tier_mapping
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.CUSTOMER,
                fields_enriched=["customer_tier"],
                source="Customer segmentation",
                methodology="Derived from customer_type",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Primary contact placeholder
        result.field_updates["primary_contact"] = {
            "contact_name": f"Contact {entity.id[:8]}",
            "contact_title": "IT Director" if customer_key == "Enterprise" else "Operations Manager",
            "contact_email": f"contact.{entity.id[:6]}@example.com",
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.CUSTOMER,
                fields_enriched=["primary_contact"],
                source="Placeholder contact",
                methodology="Default assignment pending CRM lookup",
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
        """Tier 3: Engagement and relationship assessment."""
        products = context.get_neighbors(RelationshipType.BUYS)
        contracts = context.get_neighbors(RelationshipType.CONTRACTS_WITH)

        # Account team
        result.field_updates["account_team"] = {
            "account_manager": f"AM-{entity.id[:6]}",
            "sales_rep": f"Sales-{entity.id[:6]}",
            "customer_success_manager": f"CSM-{entity.id[:6]}",
            "executive_sponsor": f"Exec-{entity.id[:6]}",
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.CUSTOMER,
                fields_enriched=["account_team"],
                source="Account assignment",
                methodology="Template-based placeholder pending HRIS lookup",
                confidence=ConfidenceLevel.LOW,
            )
        )

        # Engagement metrics
        result.field_updates["engagement_metrics"] = {
            "product_adoption_pct": 75 if len(products) > 3 else 45,
            "feature_utilization_pct": 65 if len(products) > 2 else 35,
            "monthly_active_users": 250 if len(products) > 3 else 50,
            "support_ticket_frequency_monthly": 3 if len(products) > 2 else 1,
            "training_completion_pct": 80 if len(contracts) > 0 else 20,
            "last_engagement_date": datetime.now(UTC).isoformat(),
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.CUSTOMER,
                fields_enriched=["engagement_metrics"],
                source="Product usage analysis",
                methodology="Product count-based engagement estimation",
                confidence=ConfidenceLevel.LOW,
            )
        )

        # Satisfaction score
        satisfaction = 4.2 if len(products) > 3 else 3.5
        result.field_updates["satisfaction_score"] = {
            "nps_score": 45 if satisfaction > 4.0 else 20,
            "csat_score": satisfaction,
            "scale": "1-5",
            "measurement_period": "Last Quarter",
            "trend": "Improving" if len(products) > 2 else "Stable",
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.CUSTOMER,
                fields_enriched=["satisfaction_score"],
                source="Customer satisfaction survey",
                methodology="Product engagement-based CSAT estimation",
                confidence=ConfidenceLevel.LOW,
            )
        )

        # Support history
        result.field_updates["support_history"] = {
            "total_tickets_ytd": max(5, len(products) * 4),
            "critical_incidents": max(0, len(products) - 2),
            "average_resolution_time_hours": 8,
            "first_response_time_minutes": 30,
            "customer_satisfaction_with_support": 4.1,
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.CUSTOMER,
                fields_enriched=["support_history"],
                source="Support ticket analysis",
                methodology="Product complexity-based support volume estimation",
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
        """Tier 4: Financial summary and risk assessment."""
        products = context.get_neighbors(RelationshipType.BUYS)
        contracts = context.get_neighbors(RelationshipType.CONTRACTS_WITH)

        # Financial summary
        customer_type = result.field_updates.get("customer_type", "SMB")
        base_template = CUSTOMER_TYPE_TEMPLATES.get(customer_type, CUSTOMER_TYPE_TEMPLATES["SMB"])

        annual_revenue = base_template["annual_spend"] * max(1, len(products) / 2)
        lifetime_value = annual_revenue * 3  # 3-year contract assumption

        result.field_updates["financial_summary"] = {
            "annual_revenue_usd": annual_revenue,
            "lifetime_value_usd": lifetime_value,
            "currency": "USD",
            "customer_acquisition_cost_usd": 5000 if customer_type == "Enterprise" else 1000,
            "payment_history_on_time_pct": 95,
            "last_paid_amount_usd": annual_revenue / 12,
            "last_payment_date": datetime.now(UTC).isoformat(),
            "contract_value_usd": sum(50000 for _ in contracts) if contracts else annual_revenue,
            "expansion_revenue_potential_usd": annual_revenue * 0.25,
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.CUSTOMER,
                fields_enriched=["financial_summary"],
                source="Financial estimation model",
                methodology="Product count and customer type-based revenue modeling",
                confidence=ConfidenceLevel.LOW,
            )
        )

        # Risk assessment
        payment_health = 95
        support_health = 80
        engagement_health = 75 if len(products) > 2 else 50

        result.field_updates["risk_assessment"] = {
            "churn_risk_score": 20 if engagement_health > 70 else 60,
            "payment_risk_score": 10 if payment_health > 90 else 40,
            "overall_risk_level": "Low" if engagement_health > 70 else "Medium",
            "key_risk_factors": [
                "Declining engagement metrics",
                "Budget constraints in vertical",
            ] if engagement_health < 70 else [],
            "retention_priority": "High" if engagement_health < 70 else "Standard",
            "recommended_action": "Quarterly business review" if engagement_health > 70 else "Immediate outreach",
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.CUSTOMER,
                fields_enriched=["risk_assessment"],
                source="Risk scoring model",
                methodology="Composite of engagement, payment, and support metrics",
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
        """Tier 5: Predictive churn and expansion potential."""
        products = context.get_neighbors(RelationshipType.BUYS)

        # Predictive churn score
        engagement = result.field_updates.get("engagement_metrics", {})
        satisfaction = result.field_updates.get("satisfaction_score", {})

        churn_indicators = []
        if engagement.get("product_adoption_pct", 0) < 50:
            churn_indicators.append("Low product adoption")
        if satisfaction.get("csat_score", 0) < 3.5:
            churn_indicators.append("Low satisfaction")

        churn_score = len(churn_indicators) * 25
        churn_score = min(100, churn_score + (1 if len(products) < 2 else 0) * 10)

        result.field_updates["predictive_churn_score"] = {
            "churn_probability_pct": churn_score,
            "risk_level": "High" if churn_score > 60 else "Medium" if churn_score > 30 else "Low",
            "churn_indicators": churn_indicators,
            "months_until_potential_churn": max(3, 12 - churn_score // 10),
            "retention_actions": [
                "Increase engagement touch points",
                "Offer usage-based discount",
                "Executive business review",
            ] if churn_score > 60 else [],
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.CUSTOMER,
                fields_enriched=["predictive_churn_score"],
                source="Churn prediction model",
                methodology="Engagement and satisfaction-based predictive scoring",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Expansion potential
        financial = result.field_updates.get("financial_summary", {})
        expansion_potential = financial.get("expansion_revenue_potential_usd", 0)

        result.field_updates["expansion_potential"] = {
            "expansion_revenue_opportunity_usd": expansion_potential,
            "expansion_likelihood_pct": 60 if len(products) < 5 else 35,
            "recommended_expansion_products": [
                "Advanced Analytics Module",
                "Professional Services Package",
                "Premium Support Tier",
            ],
            "expansion_strategy": "Upsell advanced features" if len(products) < 5 else "Cross-sell adjacent",
            "expected_close_timeline_months": 6,
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.CUSTOMER,
                fields_enriched=["expansion_potential"],
                source="Expansion opportunity assessment",
                methodology="Product footprint and growth vector analysis",
                confidence=ConfidenceLevel.LOW,
            )
        )

        # Strategic value assessment
        annual_revenue = financial.get("annual_revenue_usd", 0)
        customer_type = result.field_updates.get("customer_type", "SMB")

        if customer_type == "Enterprise":
            strategic_value = "High"
            value_drivers = ["Key vertical anchor", "Reference account", "High visibility"]
        elif customer_type == "Mid-Market":
            strategic_value = "Medium"
            value_drivers = ["Growth potential", "Expansion opportunity", "Community influence"]
        else:
            strategic_value = "Low"
            value_drivers = ["Volume play", "Self-service model"]

        result.field_updates["strategic_value_assessment"] = {
            "strategic_value": strategic_value,
            "value_drivers": value_drivers,
            "account_investment_level": "High" if strategic_value == "High" else "Medium" if strategic_value == "Medium" else "Low",
            "competitive_threat_level": "High" if len(products) < 2 else "Low",
            "vip_status": strategic_value == "High",
            "recommended_engagement_model": "Executive relationships" if strategic_value == "High" else "Standard CSM",
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.CUSTOMER,
                fields_enriched=["strategic_value_assessment"],
                source="Strategic value analysis",
                methodology="Customer type and product footprint assessment",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

    def _identify_gaps(self, entity: BaseEntity, context: EntityContext) -> list[DataGap]:
        """Identify known data gaps."""
        gaps = []

        products = context.get_neighbors(RelationshipType.BUYS)
        if not products:
            gaps.append(
                DataGap(
                    field_name="product_purchases",
                    description="No products linked via BUYS relationship",
                    severity="High",
                    remediation_suggestion="Link products that this customer purchases",
                )
            )

        contracts = context.get_neighbors(RelationshipType.CONTRACTS_WITH)
        if not contracts:
            gaps.append(
                DataGap(
                    field_name="contracts",
                    description="No contracts linked via CONTRACTS_WITH relationship",
                    severity="Medium",
                    remediation_suggestion="Link active contracts with this customer",
                )
            )

        if not getattr(entity, "primary_contact", None):
            gaps.append(
                DataGap(
                    field_name="primary_contact",
                    description="Primary contact not assigned",
                    severity="Medium",
                    remediation_suggestion="Identify and assign primary business contact from CRM",
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
            primary_data_source="Customer Enrichment Pipeline - Graph Context Analysis",
            assessed_by="CustomerEnricher v1.0",
            assessment_methodology="Graph-aware enrichment with financial and engagement modeling",
            confidence_level=confidence_map[tier],
            data_quality_score={
                "completeness_pct": 70 if tier == EnrichmentTier.BASIC else 85,
                "accuracy_confidence": "Medium" if tier == EnrichmentTier.BASIC else "High",
                "timeliness_score": "Current",
                "consistency_score": "Consistent",
            },
        )
