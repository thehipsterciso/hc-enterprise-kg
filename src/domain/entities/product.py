"""Product entity — a distinct offering the enterprise brings to market.

Covers physical products, digital products, software, professional services,
managed services, subscriptions, platforms, IP licenses, solution bundles,
and hybrid offerings.

Attribute groups
----------------
1. Identity & Classification (~16 attrs)
2. Lifecycle & Maturity (~8 attrs)
3. Market & Revenue (~12 attrs)
4. Quality & Customer Experience (~8 attrs)
5. Regulatory & Compliance (~8 attrs)
6. Delivery & Operations (~6 attrs)
7. Dependencies & Relationships (~12 attrs)
8. Temporal & Provenance
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, Field

from domain.base import BaseEntity, EntityType
from domain.shared import (
    ProvenanceAndConfidence,
    RegulatoryApplicability,
    StrategicAlignment,
    TemporalAndVersioning,
)

# ===========================================================================
# Group 1: Identity & Classification — sub-models
# ===========================================================================


class ProductLocalName(BaseModel):
    """Localized product name for a specific market."""

    language_code: str = ""
    name: str = ""
    locale: str = ""


class ProductFormerName(BaseModel):
    """Historical product name with effective period."""

    former_name: str = ""
    from_date: str = ""
    to_date: str = ""
    change_reason: str = ""


class ProductCategory(BaseModel):
    """Product taxonomy classification (UNSPSC, GPC, or enterprise)."""

    taxonomy: str = ""
    category_code: str = ""
    category_name: str = ""


class ProductAcquisitionSource(BaseModel):
    """Origin details for products acquired via M&A."""

    source_entity_name: str = ""
    acquisition_date: str = ""
    deal_reference: str = ""


class ProductTaxonomyLineage(BaseModel):
    """Industry taxonomy mapping for the product."""

    framework: str = ""
    framework_element_id: str = ""
    mapping_confidence: str = ""


# ===========================================================================
# Group 2: Lifecycle & Maturity — sub-models
# ===========================================================================


class VersionCurrent(BaseModel):
    """Current product version."""

    version: str = ""
    release_date: str = ""


class VersionEntry(BaseModel):
    """Historical version record."""

    version: str = ""
    release_date: str = ""
    end_of_support_date: str = ""


class Generation(BaseModel):
    """Product generation tracking (physical products)."""

    current_generation: int | None = None
    generation_name: str = ""
    generation_launch_date: str = ""


class JurisdictionApproval(BaseModel):
    """Per-jurisdiction regulatory approval status."""

    jurisdiction_id: str = ""
    jurisdiction_name: str = ""
    approval_status: str = ""


class RegulatoryApprovalStatus(BaseModel):
    """Overall regulatory approval status for the product."""

    approved: bool | None = None
    approval_body: str = ""
    approval_date: str = ""
    approval_conditions: str = ""
    jurisdictions_approved: list[JurisdictionApproval] = Field(default_factory=list)


# ===========================================================================
# Group 3: Market & Revenue — sub-models
# ===========================================================================


class RevenueCurrent(BaseModel):
    """Current revenue metrics for the product."""

    annual_revenue: float | None = None
    currency: str = "USD"
    fiscal_year: str = ""
    revenue_type: str = ""
    recurring_revenue_pct: float | None = None


class RevenueByGeo(BaseModel):
    """Revenue breakdown by geography."""

    geography_id: str = ""
    geography_name: str = ""
    revenue: float | None = None
    currency: str = "USD"


class RevenueBySegment(BaseModel):
    """Revenue breakdown by customer segment."""

    customer_segment: str = ""
    revenue: float | None = None
    currency: str = "USD"


class PricingRange(BaseModel):
    """Product pricing range."""

    minimum: float | None = None
    maximum: float | None = None
    currency: str = "USD"
    unit: str = ""


class MarginProfile(BaseModel):
    """Product margin and profitability metrics."""

    gross_margin_pct: float | None = None
    contribution_margin_pct: float | None = None
    target_margin_pct: float | None = None
    margin_trend: str = ""


class CostToDeliver(BaseModel):
    """Cost to deliver the product."""

    annual_cost: float | None = None
    currency: str = "USD"
    cost_type: str = ""


class CustomerCount(BaseModel):
    """Customer count metrics."""

    active_customers: int | None = None
    total_customers_lifetime: int | None = None
    customer_count_trend: str = ""


class ProductMarketPosition(BaseModel):
    """Product-level market position (richer than shared MarketPosition)."""

    competitive_rank: int | None = None
    market_share_pct: float | None = None
    tam: float | None = None
    sam: float | None = None
    som: float | None = None
    currency: str = "USD"


class CompetitorEntry(BaseModel):
    """Competitive landscape entry."""

    competitor_name: str = ""
    competitor_product: str = ""
    relative_position: str = ""
    competitive_advantage: str = ""
    competitive_vulnerability: str = ""


class DifferentiationFactor(BaseModel):
    """Product differentiation factor."""

    factor: str = ""
    strength: str = ""
    defensibility: str = ""


# ===========================================================================
# Group 4: Quality & Customer Experience — sub-models
# ===========================================================================


class CustomerSatisfaction(BaseModel):
    """Customer satisfaction measurement."""

    score: float | None = None
    methodology: str = ""
    sample_size: int | None = None
    measurement_date: str = ""
    benchmark_comparison: str = ""


class QualityMetrics(BaseModel):
    """Product quality metrics (ISO 9001 provenance)."""

    defect_rate: float | None = None
    return_rate_pct: float | None = None
    warranty_claim_rate_pct: float | None = None
    measurement_period: str = ""
    quality_trend: str = ""


class ServiceLevelTargets(BaseModel):
    """Service-level targets for service/subscription products."""

    availability_target_pct: float | None = None
    response_time_target: str = ""
    resolution_time_target: str = ""


class ServiceLevelPerformance(BaseModel):
    """Actual service-level performance."""

    availability_actual_pct: float | None = None
    response_time_actual: str = ""
    resolution_time_actual: str = ""
    sla_breaches_12m: int | None = None


class CustomerComplaints(BaseModel):
    """Customer complaint metrics."""

    count_12m: int | None = None
    trend: str = ""
    top_categories: list[str] = Field(default_factory=list)


class ProductReviews(BaseModel):
    """Product review / rating metrics."""

    average_rating: float | None = None
    rating_scale: str = ""
    review_count: int | None = None
    rating_trend: str = ""


class ChurnRate(BaseModel):
    """Churn metrics for subscription/recurring products."""

    annual_churn_pct: float | None = None
    monthly_churn_pct: float | None = None
    logo_churn_pct: float | None = None
    revenue_churn_pct: float | None = None
    trend: str = ""


class CustomerLifetimeValue(BaseModel):
    """Customer lifetime value metrics."""

    average_clv: float | None = None
    currency: str = "USD"
    methodology: str = ""
    payback_period_months: int | None = None


# ===========================================================================
# Group 5: Regulatory & Compliance — sub-models
# ===========================================================================


class RegulatoryClassification(BaseModel):
    """Regulatory classification for the product."""

    classification: str = ""
    classification_body: str = ""
    jurisdiction: str = ""
    classification_date: str = ""


class CertificationEntry(BaseModel):
    """Required certification for the product."""

    certification: str = ""
    issuing_body: str = ""
    status: str = ""
    jurisdiction: str = ""
    expiration_date: str = ""


class ExportControlClassification(BaseModel):
    """Export control classification (EAR, ITAR, Wassenaar, etc.)."""

    classification_number: str = ""
    control_regime: str = ""
    jurisdiction: str = ""
    restrictions_summary: str = ""
    license_exceptions: str = ""


class CarbonFootprint(BaseModel):
    """Product carbon footprint measurement."""

    value: float | None = None
    unit: str = ""
    scope: str = ""


class EnvironmentalCompliance(BaseModel):
    """Environmental compliance status (RoHS, REACH, WEEE, etc.)."""

    rohs_compliant: bool | None = None
    reach_compliant: bool | None = None
    weee_applicable: bool | None = None
    conflict_minerals_status: str = ""
    carbon_footprint: CarbonFootprint | None = None


class SafetyCertification(BaseModel):
    """Safety certification for the product."""

    certification: str = ""
    standard: str = ""
    status: str = ""
    jurisdiction: str = ""


class RecallEntry(BaseModel):
    """Product recall history entry."""

    recall_date: str = ""
    recall_scope: str = ""
    reason: str = ""
    units_affected: int | None = None
    resolution: str = ""
    regulatory_body: str = ""


class LiabilityExposure(BaseModel):
    """Product liability exposure profile."""

    product_liability_insurance: bool | None = None
    coverage_limit: float | None = None
    currency: str = "USD"
    claims_history_12m: int | None = None


# ===========================================================================
# Group 6: Delivery & Operations — sub-models
# ===========================================================================


class DeliveryChannel(BaseModel):
    """Product delivery / distribution channel."""

    channel_type: str = ""
    channel_name: str = ""
    revenue_pct: float | None = None


class ManufacturingLocation(BaseModel):
    """Manufacturing location for physical products."""

    site_id: str = ""
    site_name: str = ""
    production_type: str = ""


class FulfillmentModel(BaseModel):
    """Product fulfillment model."""

    model_type: str = ""
    average_lead_time: str = ""
    on_time_delivery_pct: float | None = None


class ScalabilityConstraint(BaseModel):
    """Constraint limiting product scalability."""

    constraint_type: str = ""
    constraint_description: str = ""
    impact: str = ""
    mitigation_plan: str = ""


# ===========================================================================
# Group 7: Dependencies & Relationships — sub-models
# ===========================================================================


class PortfolioMembership(BaseModel):
    """Portfolio membership reference."""

    portfolio_id: str = ""
    relationship_type: str = ""


class CapabilityLink(BaseModel):
    """Link to an enabling business capability."""

    capability_id: str = ""
    enablement_type: str = ""


class ProductRoles(BaseModel):
    """Key role assignments for the product."""

    product_manager: str = ""
    engineering_lead: str = ""
    marketing_lead: str = ""
    quality_lead: str = ""


class SystemLink(BaseModel):
    """Link to an enabling system."""

    system_id: str = ""
    enablement_type: str = ""


class DataLink(BaseModel):
    """Link to a data asset used by the product."""

    data_asset_id: str = ""
    usage_type: str = ""


class CustomerLink(BaseModel):
    """Link to a customer segment served by the product."""

    customer_segment_id: str = ""
    revenue_contribution: float | None = None
    currency: str = "USD"


class VendorLink(BaseModel):
    """Link to a vendor dependency."""

    vendor_id: str = ""
    dependency_type: str = ""
    dependency_criticality: str = ""


class RelatedProduct(BaseModel):
    """Cross-reference to a related product."""

    product_id: str = ""
    relationship_type: str = ""


# ===========================================================================
# Product entity
# ===========================================================================


class Product(BaseEntity):
    """A distinct offering the enterprise brings to market.

    Covers physical products, digital products, software, professional
    services, managed services, subscriptions, platforms, IP licenses,
    solution bundles, and hybrid offerings.
    """

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.PRODUCT
    entity_type: Literal[EntityType.PRODUCT] = EntityType.PRODUCT

    # --- Group 1: Identity & Classification ---
    product_id: str = ""
    product_name_internal: str = ""
    product_name_local: list[ProductLocalName] = Field(default_factory=list)
    product_name_former: list[ProductFormerName] = Field(default_factory=list)
    product_description_internal: str = ""
    offering_type: str = ""
    offering_subtype: str = ""
    product_category: ProductCategory | None = None
    sku_count: int | None = None
    functional_domain_primary: str = ""
    functional_domain_secondary: list[str] = Field(default_factory=list)
    origin: str = ""
    acquisition_source: ProductAcquisitionSource | None = None
    taxonomy_lineage: list[ProductTaxonomyLineage] = Field(default_factory=list)

    # --- Group 2: Lifecycle & Maturity ---
    lifecycle_stage: str = ""
    lifecycle_stage_rationale: str = ""
    launch_date: str = ""
    planned_retirement_date: str = ""
    version_current: VersionCurrent | None = None
    version_history: list[VersionEntry] = Field(default_factory=list)
    generation: Generation | None = None
    regulatory_approval_status: RegulatoryApprovalStatus | None = None

    # --- Group 3: Market & Revenue ---
    revenue_current: RevenueCurrent | None = None
    revenue_trend: str = ""
    revenue_by_geography: list[RevenueByGeo] = Field(default_factory=list)
    revenue_by_segment: list[RevenueBySegment] = Field(default_factory=list)
    pricing_model: str = ""
    pricing_range: PricingRange | None = None
    margin_profile: MarginProfile | None = None
    cost_to_deliver: CostToDeliver | None = None
    customer_count: CustomerCount | None = None
    market_position: ProductMarketPosition | None = None
    competitive_landscape: list[CompetitorEntry] = Field(default_factory=list)
    differentiation_factors: list[DifferentiationFactor] = Field(default_factory=list)

    # --- Group 4: Quality & Customer Experience ---
    customer_satisfaction: CustomerSatisfaction | None = None
    quality_metrics: QualityMetrics | None = None
    service_level_targets: ServiceLevelTargets | None = None
    service_level_performance: ServiceLevelPerformance | None = None
    customer_complaints: CustomerComplaints | None = None
    product_reviews: ProductReviews | None = None
    churn_rate: ChurnRate | None = None
    customer_lifetime_value: CustomerLifetimeValue | None = None

    # --- Group 5: Regulatory & Compliance ---
    regulatory_classification: RegulatoryClassification | None = None
    regulatory_applicability: list[RegulatoryApplicability] = Field(
        default_factory=list
    )
    certifications_required: list[CertificationEntry] = Field(default_factory=list)
    export_control_classification: ExportControlClassification | None = None
    environmental_compliance: EnvironmentalCompliance | None = None
    safety_certifications: list[SafetyCertification] = Field(default_factory=list)
    recall_history: list[RecallEntry] = Field(default_factory=list)
    liability_exposure: LiabilityExposure | None = None

    # --- Group 6: Delivery & Operations ---
    delivery_model: str = ""
    delivery_channels: list[DeliveryChannel] = Field(default_factory=list)
    supply_chain_complexity: str = ""
    manufacturing_locations: list[ManufacturingLocation] = Field(default_factory=list)
    fulfillment_model: FulfillmentModel | None = None
    scalability_constraints: list[ScalabilityConstraint] = Field(default_factory=list)

    # --- Group 7: Dependencies & Relationships ---
    belongs_to_portfolio: list[PortfolioMembership] = Field(default_factory=list)
    enabled_by_capabilities: list[CapabilityLink] = Field(default_factory=list)
    managed_by_org_unit: str = ""
    product_roles: ProductRoles | None = None
    delivered_from_locations: list[str] = Field(default_factory=list)
    enabled_by_systems: list[SystemLink] = Field(default_factory=list)
    uses_data: list[DataLink] = Field(default_factory=list)
    serves_customers: list[CustomerLink] = Field(default_factory=list)
    depends_on_vendors: list[VendorLink] = Field(default_factory=list)
    strategic_alignment: StrategicAlignment | None = None
    related_products: list[RelatedProduct] = Field(default_factory=list)

    # --- Group 8: Temporal & Provenance ---
    temporal_and_versioning: TemporalAndVersioning = Field(
        default_factory=TemporalAndVersioning
    )
    provenance_and_confidence: ProvenanceAndConfidence = Field(
        default_factory=ProvenanceAndConfidence
    )
