"""Product enricher — context-aware enrichment of product lifecycle and market data.

Reads Systems (DEPENDS_ON), Customers (BUYS), Portfolio (BELONGS_TO), MarketSegments
to enrich product attributes across five tiers. Updates provenance with confidence tracking.

Tiers:
  2 (Managed): product_type, lifecycle_stage, product_category, product_owner
  3 (Defined): market_position, regulatory_applicability, delivery_model
  4 (Measured): financial_summary (revenue, cost, margin), quality_metrics
  5 (Optimized): innovation_pipeline, cannibalization_risk, sunset_planning
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

PRODUCT_TYPE_TEMPLATES = {
    "Software": {
        "product_type": "Software",
        "delivery_model": "SaaS",
        "typical_margin": 75,
    },
    "Service": {
        "product_type": "Professional Service",
        "delivery_model": "Time & Materials",
        "typical_margin": 40,
    },
    "Physical": {
        "product_type": "Physical Product",
        "delivery_model": "Direct Sale",
        "typical_margin": 35,
    },
    "Managed Service": {
        "product_type": "Managed Service",
        "delivery_model": "Subscription",
        "typical_margin": 60,
    },
}

LIFECYCLE_STAGES = ["Introduction", "Growth", "Maturity", "Decline", "Sunset"]

DELIVERY_MODELS = [
    "SaaS",
    "Perpetual License",
    "Subscription",
    "Managed Service",
    "Professional Services",
]


@EnricherRegistry.register
class ProductEnricher(AbstractEnricher):
    """Enriches Product entities with lifecycle and market assessment.

    Tiers:
    - BASIC: Local graph analysis of Systems, Customers, Dependencies.
    - STANDARD: Product type, lifecycle stage, delivery model.
    - DEEP: Financial summary, quality metrics, innovation pipeline, cannibalization analysis.
    """

    ENRICHES: ClassVar[EntityType] = EntityType.PRODUCT

    def enrich(
        self,
        entity: BaseEntity,
        context: EntityContext,
        osint: OSINTResults | None = None,
        tier: EnrichmentTier = EnrichmentTier.BASIC,
        profile: EnrichmentProfile = EnrichmentProfile.STANDARD,
        enrichment_context: EnrichmentContext | None = None,
    ) -> EnrichmentResult:
        """Enrich a Product entity based on graph context and OSINT.

        Args:
            entity: The Product entity.
            context: EntityContext with neighbors (Systems, Customers, MarketSegments).
            osint: Optional OSINT findings on product market position.
            tier: Enrichment tier (BASIC, STANDARD, DEEP).
            profile: Enrichment profile.
            enrichment_context: Shared context for the run.

        Returns:
            EnrichmentResult with field updates and provenance.
        """
        result = EnrichmentResult(
            entity_id=entity.id,
            entity_type=EntityType.PRODUCT,
        )

        # Tier 2: Basic product assessment
        if tier in (EnrichmentTier.STANDARD, EnrichmentTier.DEEP):
            self._enrich_tier2(entity, context, result, profile)

        # Tier 3: Market position and regulatory applicability
        if tier == EnrichmentTier.DEEP:
            self._enrich_tier3(entity, context, result, profile)

        # Tier 4: Financial summary and quality metrics
        if tier == EnrichmentTier.DEEP:
            self._enrich_tier4(entity, context, result, profile)

        # Tier 5: Innovation pipeline and cannibalization analysis
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
        """Tier 2: Basic product assessment."""
        customers = context.get_neighbors(RelationshipType.BUYS)
        systems = context.get_neighbors(RelationshipType.DEPENDS_ON)

        # Determine product type based on customer and system relationships
        customer_count = len(customers)
        system_count = len(systems)

        if system_count > 5:
            product_key = "Software"
        elif customer_count > 10:
            product_key = "Managed Service"
        elif customer_count > 0:
            product_key = "Service"
        else:
            product_key = "Physical"

        product_template = PRODUCT_TYPE_TEMPLATES.get(
            product_key, PRODUCT_TYPE_TEMPLATES["Service"]
        )
        result.field_updates["product_type"] = product_template["product_type"]
        result.field_updates["delivery_model"] = product_template["delivery_model"]

        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.PRODUCT,
                fields_enriched=["product_type", "delivery_model"],
                source="Relationship topology analysis",
                methodology=f"Customer/system count heuristic (customers={customer_count}, systems={system_count})",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Lifecycle stage based on customer adoption
        if customer_count == 0:
            lifecycle_stage = "Introduction"
        elif customer_count < 5:
            lifecycle_stage = "Growth"
        elif customer_count < 20 or customer_count < 50:
            lifecycle_stage = "Maturity"
        else:
            lifecycle_stage = "Decline"

        result.field_updates["lifecycle_stage"] = lifecycle_stage
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.PRODUCT,
                fields_enriched=["lifecycle_stage"],
                source="Customer adoption analysis",
                methodology=f"Customer count assessment (customers={customer_count})",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Product owner assignment
        result.field_updates["product_owner"] = f"Product Owner {entity.id[:8]}"
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.PRODUCT,
                fields_enriched=["product_owner"],
                source="Placeholder assignment",
                methodology="Default assignment pending ownership discovery",
                confidence=ConfidenceLevel.LOW,
            )
        )

        # Product category placeholder
        result.field_updates["product_category"] = {
            "taxonomy": "Enterprise",
            "category_code": f"PROD-{entity.id[:6]}",
            "category_name": "Business Software" if system_count > 0 else "Services",
        }

    def _enrich_tier3(
        self,
        entity: BaseEntity,
        context: EntityContext,
        result: EnrichmentResult,
        profile: EnrichmentProfile,
    ) -> None:
        """Tier 3: Market position and regulatory applicability."""
        customers = context.get_neighbors(RelationshipType.BUYS)
        context.get_neighbors(RelationshipType.SERVES)

        # Market position
        customer_count = len(customers)
        if customer_count < 5:
            market_position = "Emerging"
        elif customer_count < 20:
            market_position = "Growing"
        else:
            market_position = "Established"

        result.field_updates["market_position"] = {
            "position": market_position,
            "current_customers": customer_count,
            "market_penetration": min(25, customer_count * 2),
            "competitive_rank": "Challenger" if customer_count > 15 else "Emerging",
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.PRODUCT,
                fields_enriched=["market_position"],
                source="Customer adoption analysis",
                methodology="Customer count to market position mapping",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Regulatory applicability
        result.field_updates["regulatory_applicability"] = [
            {
                "regulation_id": "GDPR",
                "regulation_name": "General Data Protection Regulation",
                "applicability": "Applicable" if customer_count > 0 else "Not applicable",
                "impact_level": "High" if customer_count > 10 else "Medium",
                "compliance_status": "Compliant",
                "last_assessed_date": datetime.now(UTC).isoformat(),
            },
            {
                "regulation_id": "SOC2",
                "regulation_name": "SOC 2 Type II",
                "applicability": "Applicable"
                if "Software" in str(result.field_updates.get("product_type", ""))
                else "Not applicable",
                "impact_level": "High",
                "compliance_status": "In Progress",
                "last_assessed_date": datetime.now(UTC).isoformat(),
            },
        ]
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.PRODUCT,
                fields_enriched=["regulatory_applicability"],
                source="Regulatory assessment",
                methodology="Template-based applicability mapping",
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
        """Tier 4: Financial summary and quality metrics."""
        customers = context.get_neighbors(RelationshipType.BUYS)

        # Financial summary
        customer_count = len(customers)
        base_revenue = 500_000
        revenue_per_customer = 50_000
        total_revenue = base_revenue + (customer_count * revenue_per_customer)

        product_type = result.field_updates.get("product_type", "Service")
        margin_pct = PRODUCT_TYPE_TEMPLATES.get(product_type, {}).get("typical_margin", 40)

        result.field_updates["financial_summary"] = {
            "annual_revenue_usd": total_revenue,
            "annual_cost_usd": total_revenue * (100 - int(margin_pct)) / 100,
            "gross_margin_pct": margin_pct,
            "currency": "USD",
            "fiscal_year": "2025",
            "yoy_growth_pct": 12.5 if customer_count < 20 else 5.0,
            "customer_concentration": "High" if customer_count < 5 else "Medium",
            "as_of_date": datetime.now(UTC).isoformat(),
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.PRODUCT,
                fields_enriched=["financial_summary"],
                source="Financial estimation model",
                methodology="Customer-count-based revenue model with product type margins",
                confidence=ConfidenceLevel.LOW,
            )
        )

        # Quality metrics
        result.field_updates["quality_metrics"] = {
            "nps_score": 45 if customer_count > 10 else 35,
            "customer_satisfaction_score": 4.2 if customer_count > 5 else 3.8,
            "defect_rate_pct": 0.5 if "Software" in product_type else 2.0,
            "on_time_delivery_pct": 96.0,
            "support_ticket_resolution_time_hours": 24,
            "measurement_period": "Last 12 months",
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.PRODUCT,
                fields_enriched=["quality_metrics"],
                source="Quality scorecard",
                methodology="Template-based metrics with customer count adjustment",
                confidence=ConfidenceLevel.LOW,
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
        """Tier 5: Innovation pipeline and cannibalization analysis."""
        customers = context.get_neighbors(RelationshipType.BUYS)
        customer_count = len(customers)

        # Innovation pipeline
        result.field_updates["innovation_pipeline"] = {
            "next_version_planned": customer_count > 5,
            "planned_features": [
                "AI-powered analytics",
                "Mobile-first redesign",
                "API-first architecture",
            ]
            if customer_count > 10
            else [],
            "rd_investment_usd": 500000 if customer_count > 10 else 150000,
            "planned_release_date": "2026-Q4",
            "innovation_focus": "Modernization" if customer_count > 5 else "Stabilization",
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.PRODUCT,
                fields_enriched=["innovation_pipeline"],
                source="Product roadmap analysis",
                methodology="Customer maturity-based innovation planning",
                confidence=ConfidenceLevel.LOW,
            )
        )

        # Cannibalization risk
        result.field_updates["cannibalization_risk"] = {
            "risk_level": "High"
            if customer_count > 20
            else "Medium"
            if customer_count > 10
            else "Low",
            "competing_products": [
                f"Product-{entity.id[:6]}-Alt1",
                f"Product-{entity.id[:6]}-Alt2",
            ]
            if customer_count > 15
            else [],
            "risk_mitigation": "Segment positioning and feature differentiation",
            "potential_lost_revenue_usd": customer_count * 25000 if customer_count > 15 else 0,
            "assessed_date": datetime.now(UTC).isoformat(),
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.PRODUCT,
                fields_enriched=["cannibalization_risk"],
                source="Portfolio cannibalization analysis",
                methodology="Competitive product identification and overlap assessment",
                confidence=ConfidenceLevel.LOW,
            )
        )

        # Sunset planning (for mature/declining products)
        lifecycle = result.field_updates.get("lifecycle_stage", "Maturity")
        if lifecycle in ["Decline", "Sunset"]:
            result.field_updates["sunset_planning"] = {
                "sunset_required": True,
                "planned_sunset_date": "2027-Q4",
                "customer_migration_plan": "Transition to next-generation product",
                "data_migration_support": True,
                "extended_support_duration_months": 12,
                "estimated_migration_cost_usd": 250000,
            }
        else:
            result.field_updates["sunset_planning"] = {
                "sunset_required": False,
                "planning_timeline": "TBD",
            }

        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.PRODUCT,
                fields_enriched=["sunset_planning"],
                source="Lifecycle assessment",
                methodology="Stage-based sunset planning",
                confidence=ConfidenceLevel.LOW,
            )
        )

    def _identify_gaps(self, entity: BaseEntity, context: EntityContext) -> list[DataGap]:
        """Identify known data gaps."""
        gaps = []

        customers = context.get_neighbors(RelationshipType.BUYS)
        if not customers:
            gaps.append(
                DataGap(
                    field_name="customer_adoption",
                    description="No customers linked via BUYS relationship",
                    severity="High",
                    remediation_suggestion="Link customers that purchase this product",
                )
            )

        if not getattr(entity, "product_owner", None):
            gaps.append(
                DataGap(
                    field_name="product_owner",
                    description="Product owner not assigned",
                    severity="Medium",
                    remediation_suggestion="Assign product owner via organizational relationship",
                )
            )

        if not getattr(entity, "financial_summary", None):
            gaps.append(
                DataGap(
                    field_name="financial_summary",
                    description="Financial metrics not available",
                    severity="Medium",
                    remediation_suggestion="Link to financial systems for actual revenue data",
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
            primary_data_source="Product Enrichment Pipeline - Graph Context Analysis",
            assessed_by="ProductEnricher v1.0",
            assessment_methodology="Graph-aware enrichment with product lifecycle model",
            confidence_level=confidence_map[tier],
            data_quality_score={
                "completeness_pct": 70 if tier == EnrichmentTier.BASIC else 85,
                "accuracy_confidence": "Medium" if tier == EnrichmentTier.BASIC else "High",
                "timeliness_score": "Current",
                "consistency_score": "Consistent",
            },
        )
