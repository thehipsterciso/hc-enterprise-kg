"""ProductPortfolio enricher — context-aware enrichment of portfolio strategy and performance.

Reads Products (CONTAINS), MarketSegments (SERVES) to enrich portfolio
attributes across five tiers. Updates provenance with confidence tracking.

Tiers:
  2 (Managed): portfolio_type, status, portfolio_owner
  3 (Defined): market_position, competitive_positioning
  4 (Measured): financial_summary (revenue, margin, growth_rate)
  5 (Optimized): strategic_assessment, rationalization_candidates
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


PORTFOLIO_TYPE_TEMPLATES = {
    "Enterprise": {
        "portfolio_type": "Enterprise Portfolio",
        "scope": "Organization-wide",
        "governance_level": "Executive",
        "typical_product_count": 50,
    },
    "Business Unit": {
        "portfolio_type": "Business Unit Portfolio",
        "scope": "Single business unit",
        "governance_level": "VP/Director",
        "typical_product_count": 15,
    },
    "Product Line": {
        "portfolio_type": "Product Line",
        "scope": "Related product family",
        "governance_level": "Product Manager",
        "typical_product_count": 5,
    },
}

PORTFOLIO_STATUS_OPTIONS = ["Active", "Growth", "Mature", "Decline", "Under Review", "Divesting"]

MARKET_POSITION_TEMPLATES = [
    "Market Leader",
    "Strong Challenger",
    "Established Player",
    "Emerging Entrant",
    "Niche Player",
]


@EnricherRegistry.register
class ProductPortfolioEnricher(AbstractEnricher):
    """Enriches ProductPortfolio entities with strategic assessment.

    Tiers:
    - BASIC: Local graph analysis of contained Products.
    - STANDARD: Portfolio type, status, ownership.
    - DEEP: Market position, financial summary, rationalization analysis.
    """

    ENRICHES: ClassVar[EntityType] = EntityType.PRODUCT_PORTFOLIO

    def enrich(
        self,
        entity: BaseEntity,
        context: EntityContext,
        osint: OSINTResults | None = None,
        tier: EnrichmentTier = EnrichmentTier.BASIC,
        profile: EnrichmentProfile = EnrichmentProfile.STANDARD,
        enrichment_context: EnrichmentContext | None = None,
    ) -> EnrichmentResult:
        """Enrich a ProductPortfolio entity based on graph context and OSINT.

        Args:
            entity: The ProductPortfolio entity.
            context: EntityContext with neighbors (Products, MarketSegments).
            osint: Optional OSINT findings on portfolio market position.
            tier: Enrichment tier (BASIC, STANDARD, DEEP).
            profile: Enrichment profile.
            enrichment_context: Shared context for the run.

        Returns:
            EnrichmentResult with field updates and provenance.
        """
        result = EnrichmentResult(
            entity_id=entity.id,
            entity_type=EntityType.PRODUCT_PORTFOLIO,
        )

        # Tier 2: Basic portfolio assessment
        if tier in (EnrichmentTier.STANDARD, EnrichmentTier.DEEP):
            self._enrich_tier2(entity, context, result, profile)

        # Tier 3: Market position and competitive analysis
        if tier == EnrichmentTier.DEEP:
            self._enrich_tier3(entity, context, result, profile)

        # Tier 4: Financial summary and metrics
        if tier == EnrichmentTier.DEEP:
            self._enrich_tier4(entity, context, result, profile)

        # Tier 5: Strategic assessment and rationalization
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
        """Tier 2: Basic portfolio assessment."""
        products = context.get_neighbors(RelationshipType.CONTAINS)
        market_segments = context.get_neighbors(RelationshipType.SERVES)

        # Determine portfolio type based on product count
        product_count = len(products)
        if product_count == 0:
            portfolio_key = "Product Line"
        elif product_count < 10:
            portfolio_key = "Product Line"
        elif product_count < 30:
            portfolio_key = "Business Unit"
        else:
            portfolio_key = "Enterprise"

        portfolio_template = PORTFOLIO_TYPE_TEMPLATES.get(portfolio_key, PORTFOLIO_TYPE_TEMPLATES["Product Line"])
        result.field_updates["portfolio_type"] = portfolio_template["portfolio_type"]

        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.PRODUCT_PORTFOLIO,
                fields_enriched=["portfolio_type"],
                source="Product composition analysis",
                methodology=f"Portfolio size heuristic (products={product_count})",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Portfolio status based on product lifecycle mix
        if product_count == 0:
            status = "Under Review"
        elif product_count < 3:
            status = "Growth"
        else:
            status = "Active"

        result.field_updates["status"] = status
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.PRODUCT_PORTFOLIO,
                fields_enriched=["status"],
                source="Portfolio composition analysis",
                methodology=f"Product count lifecycle assessment",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Portfolio owner assignment
        result.field_updates["portfolio_owner"] = f"Portfolio Owner {entity.id[:8]}"
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.PRODUCT_PORTFOLIO,
                fields_enriched=["portfolio_owner"],
                source="Placeholder assignment",
                methodology="Default assignment pending ownership discovery",
                confidence=ConfidenceLevel.LOW,
            )
        )

        # Segment coverage
        if market_segments:
            result.field_updates["segment_coverage"] = [
                {
                    "segment_id": seg.id,
                    "segment_name": getattr(seg, "name", "Unknown"),
                    "served": True,
                }
                for seg in market_segments
            ]

    def _enrich_tier3(
        self,
        entity: BaseEntity,
        context: EntityContext,
        result: EnrichmentResult,
        profile: EnrichmentProfile,
    ) -> None:
        """Tier 3: Market position and competitive analysis."""
        products = context.get_neighbors(RelationshipType.CONTAINS)
        market_segments = context.get_neighbors(RelationshipType.SERVES)

        # Market position (select based on segment count and product diversity)
        if len(market_segments) == 0:
            market_position = "Niche Player"
        elif len(market_segments) < 3:
            market_position = "Established Player"
        else:
            market_position = "Market Leader"

        result.field_updates["market_position"] = market_position
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.PRODUCT_PORTFOLIO,
                fields_enriched=["market_position"],
                source="Market segment coverage analysis",
                methodology=f"Segment diversity heuristic (segments={len(market_segments)})",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Competitive positioning
        result.field_updates["competitive_positioning"] = {
            "market_position": market_position,
            "primary_competitors": [
                "Competitor A",
                "Competitor B",
                "Competitor C",
            ],
            "competitive_advantages": [
                "Integrated solution offering",
                "Established customer relationships",
                f"{len(products)} product offerings",
            ],
            "competitive_vulnerabilities": [
                "Legacy technology in some products",
                "Limited geographic presence",
            ],
            "market_share_estimate_pct": 8.5 if market_position == "Market Leader" else 3.2,
            "market_share_as_of_date": datetime.now(UTC).isoformat(),
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.PRODUCT_PORTFOLIO,
                fields_enriched=["competitive_positioning"],
                source="Competitive analysis",
                methodology="Template-based positioning based on market presence",
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
        """Tier 4: Financial summary and metrics."""
        products = context.get_neighbors(RelationshipType.CONTAINS)

        # Estimate financial metrics from product count
        base_revenue = 10_000_000  # $10M baseline
        revenue_per_product = 500_000
        total_revenue = base_revenue + (len(products) * revenue_per_product)

        # Margin assumptions by portfolio type
        portfolio_type = result.field_updates.get("portfolio_type", "Product Line")
        if "Enterprise" in portfolio_type:
            gross_margin = 65
            contribution_margin = 45
        elif "Business Unit" in portfolio_type:
            gross_margin = 60
            contribution_margin = 40
        else:
            gross_margin = 55
            contribution_margin = 35

        result.field_updates["financial_summary"] = {
            "annual_revenue_usd": total_revenue,
            "annual_cost_usd": total_revenue * (100 - contribution_margin) / 100,
            "gross_margin_pct": gross_margin,
            "contribution_margin_pct": contribution_margin,
            "currency": "USD",
            "fiscal_year": "2025",
            "yoy_growth_pct": 8.5 if len(products) > 5 else 3.2,
            "revenue_pct_of_enterprise": 12.0,
            "as_of_date": datetime.now(UTC).isoformat(),
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.PRODUCT_PORTFOLIO,
                fields_enriched=["financial_summary"],
                source="Financial estimation model",
                methodology="Product-count-based revenue model with margin templates",
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
        """Tier 5: Strategic assessment and rationalization."""
        products = context.get_neighbors(RelationshipType.CONTAINS)

        # Strategic assessment
        result.field_updates["strategic_assessment"] = {
            "portfolio_alignment_to_strategy": "High" if len(products) > 5 else "Medium",
            "strategic_priorities": [
                "Grow cloud-native offerings",
                "Consolidate legacy product lines",
                "Expand into adjacent markets",
            ],
            "capability_gaps": [
                "AI/ML product capabilities",
                "Low-code/no-code platforms",
                "Sustainability features",
            ],
            "required_investments_usd": 2_500_000,
            "expected_portfolio_roi_pct": 22,
            "strategic_review_date": datetime.now(UTC).isoformat(),
        }
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.PRODUCT_PORTFOLIO,
                fields_enriched=["strategic_assessment"],
                source="Strategic portfolio review",
                methodology="Template-based assessment with product count factors",
                confidence=ConfidenceLevel.LOW,
            )
        )

        # Rationalization candidates
        rationalization_list = []
        if len(products) > 10:
            # Candidate for consolidation
            rationalization_list.append({
                "product_id": f"candidate-{entity.id[:8]}-1",
                "product_name": "Legacy Product A",
                "rationale": "Low growth, declining market share",
                "recommended_action": "Consolidate into newer offering",
                "annual_cost_usd": 250000,
                "strategic_fit": "Low",
            })

        result.field_updates["rationalization_candidates"] = rationalization_list
        result.actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.PRODUCT_PORTFOLIO,
                fields_enriched=["rationalization_candidates"],
                source="Portfolio optimization analysis",
                methodology="Heuristic-based candidate identification",
                confidence=ConfidenceLevel.LOW,
            )
        )

    def _identify_gaps(self, entity: BaseEntity, context: EntityContext) -> list[DataGap]:
        """Identify known data gaps."""
        gaps = []

        products = context.get_neighbors(RelationshipType.CONTAINS)
        if not products:
            gaps.append(
                DataGap(
                    field_name="contained_products",
                    description="No products linked via CONTAINS relationship",
                    severity="High",
                    remediation_suggestion="Link products that belong to this portfolio",
                )
            )

        market_segments = context.get_neighbors(RelationshipType.SERVES)
        if not market_segments:
            gaps.append(
                DataGap(
                    field_name="served_segments",
                    description="No market segments linked via SERVES relationship",
                    severity="Medium",
                    remediation_suggestion="Link market segments served by this portfolio",
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
            primary_data_source="Product Portfolio Enrichment Pipeline - Graph Context Analysis",
            assessed_by="ProductPortfolioEnricher v1.0",
            assessment_methodology="Graph-aware enrichment with portfolio strategy alignment",
            confidence_level=confidence_map[tier],
            data_quality_score={
                "completeness_pct": 60 if tier == EnrichmentTier.BASIC else 80,
                "accuracy_confidence": "Low" if tier == EnrichmentTier.BASIC else "Medium",
                "timeliness_score": "Current",
                "consistency_score": "Consistent",
            },
        )
