"""Customer entity — a customer account in the enterprise knowledge graph.

Represents enterprise, mid-market, SMB, government, nonprofit, academic,
consumer, or internal customer accounts with full relationship, financial,
risk, and product consumption profiles.

Attribute groups
----------------
1. Identity & Classification (~14 attrs)
2. Relationship & Engagement (~10 attrs)
3. Financial Profile (~10 attrs)
4. Risk & Compliance (~8 attrs)
5. Products & Services Consumed (~6 attrs)
6. Dependencies & Relationships (~11 attrs)
7. Temporal & Provenance
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, Field

from domain.base import BaseEntity, EntityType
from domain.shared import (
    AuditFinding,
    ProvenanceAndConfidence,
    RegulatoryApplicability,
    TemporalAndVersioning,
)

# ===========================================================================
# Group 1: Identity & Classification — sub-models
# ===========================================================================


class CustomerFormerName(BaseModel):
    """Historical customer name with effective period."""

    former_name: str = ""
    from_date: str = ""
    to_date: str = ""
    change_reason: str = ""


class CustomerIndustryClassification(BaseModel):
    """Industry classification for B2B customers."""

    classification_standard: str = ""
    code: str = ""
    description: str = ""


class CustomerLocation(BaseModel):
    """Customer location reference."""

    location_id: str = ""
    location_name: str = ""
    business_conducted: bool | None = None


class CustomerSize(BaseModel):
    """Customer size metrics (B2B)."""

    annual_revenue: float | None = None
    employee_count: int | None = None
    currency: str = "USD"
    as_of_date: str = ""


# ===========================================================================
# Group 2: Relationship & Engagement — sub-models
# ===========================================================================


class PrimaryContact(BaseModel):
    """Lightweight primary contact (full contacts in CRM)."""

    contact_name: str = ""
    contact_title: str = ""
    contact_email: str = ""


class AccountTeam(BaseModel):
    """Account team role assignments."""

    account_manager: str = ""
    sales_rep: str = ""
    customer_success_manager: str = ""
    executive_sponsor: str = ""


class CommunicationPreferences(BaseModel):
    """Customer communication preferences."""

    preferred_channel: str = ""
    language: str = ""
    timezone: str = ""


class SatisfactionCurrent(BaseModel):
    """Current customer satisfaction measurement."""

    score: float | None = None
    methodology: str = ""
    measurement_date: str = ""
    trend: str = ""


class HealthScore(BaseModel):
    """Customer health score."""

    score: float | None = None
    scale: str = ""
    methodology: str = ""
    risk_factors: list[str] = Field(default_factory=list)
    last_calculated: str = ""


# ===========================================================================
# Group 3: Financial Profile — sub-models
# ===========================================================================


class CustomerRevenueCurrent(BaseModel):
    """Current revenue from this customer."""

    annual_revenue: float | None = None
    currency: str = "USD"
    fiscal_year: str = ""
    yoy_growth_pct: float | None = None


class RevenueLifetime(BaseModel):
    """Lifetime revenue from this customer."""

    total_revenue: float | None = None
    currency: str = "USD"
    since_date: str = ""


class RevenueByProduct(BaseModel):
    """Revenue breakdown by product."""

    product_id: str = ""
    product_name: str = ""
    revenue: float | None = None
    currency: str = "USD"


class RevenueConcentrationRisk(BaseModel):
    """Revenue concentration risk assessment."""

    pct_of_enterprise_revenue: float | None = None
    concentration_tier: str = ""


class ContractValue(BaseModel):
    """Contract value summary."""

    total_contract_value: float | None = None
    annual_contract_value: float | None = None
    currency: str = "USD"
    contract_end_date: str = ""


class PaymentTerms(BaseModel):
    """Payment terms and DSO."""

    standard_terms: str = ""
    actual_terms: str = ""
    days_sales_outstanding: float | None = None


class CreditProfile(BaseModel):
    """Customer credit profile."""

    credit_rating: str = ""
    credit_limit: float | None = None
    currency: str = "USD"
    credit_risk_level: str = ""


class Profitability(BaseModel):
    """Customer profitability metrics."""

    gross_margin_pct: float | None = None
    cost_to_serve: float | None = None
    cost_to_serve_currency: str = "USD"
    profit_contribution: float | None = None
    profit_contribution_currency: str = "USD"


class WalletShare(BaseModel):
    """Share of customer's total spend in category."""

    estimated_total_spend_in_category: float | None = None
    our_share_pct: float | None = None
    currency: str = "USD"


class ExpansionPotential(BaseModel):
    """Upsell / cross-sell expansion potential."""

    estimated_expansion_revenue: float | None = None
    currency: str = "USD"
    confidence: str = ""
    expansion_products: list[str] = Field(default_factory=list)


# ===========================================================================
# Group 4: Risk & Compliance — sub-models
# ===========================================================================


class CustomerRiskProfile(BaseModel):
    """Multi-dimensional customer risk assessment."""

    overall_risk: str = ""
    financial_risk: str = ""
    operational_risk: str = ""
    reputational_risk: str = ""
    regulatory_risk: str = ""


class CustomerSanctionsScreening(BaseModel):
    """Sanctions / watchlist screening results."""

    screened: bool | None = None
    screening_date: str = ""
    screening_tool: str = ""
    result: str = ""
    screening_lists: list[str] = Field(default_factory=list)


class KycStatus(BaseModel):
    """Know Your Customer status."""

    completed: bool | None = None
    completion_date: str = ""
    next_review_date: str = ""
    kyc_level: str = ""


class ExportControlStatus(BaseModel):
    """Export control classification for the customer."""

    classification: str = ""
    restricted_products: list[str] = Field(default_factory=list)
    license_required: bool | None = None
    end_use_statement_on_file: bool | None = None


class DataPrivacyObligations(BaseModel):
    """Data privacy obligations for the customer relationship."""

    jurisdictions: list[str] = Field(default_factory=list)
    special_requirements: str = ""
    data_processing_agreement_in_place: bool | None = None
    dpa_reference: str = ""
    data_classification_of_shared_data: str = ""


class CustomerComplianceCertification(BaseModel):
    """Compliance certification held by the customer."""

    certification: str = ""
    issuing_body: str = ""
    status: str = ""
    relevance: str = ""


# ===========================================================================
# Group 5: Products & Services Consumed — sub-models
# ===========================================================================


class ActiveProduct(BaseModel):
    """Currently active product subscription/purchase."""

    product_id: str = ""
    product_name: str = ""
    subscription_status: str = ""
    start_date: str = ""
    renewal_date: str = ""


class HistoricalProduct(BaseModel):
    """Previously consumed product."""

    product_id: str = ""
    product_name: str = ""
    start_date: str = ""
    end_date: str = ""
    end_reason: str = ""


class ServiceAgreement(BaseModel):
    """Service agreement with the customer."""

    agreement_id: str = ""
    agreement_type: str = ""
    sla_tier: str = ""
    start_date: str = ""
    end_date: str = ""


class Customization(BaseModel):
    """Product customization for this customer."""

    customization_description: str = ""
    complexity: str = ""
    annual_cost: float | None = None
    currency: str = "USD"


class IntegrationPoint(BaseModel):
    """System integration point with the customer."""

    integration_description: str = ""
    integration_type: str = ""
    our_system_id: str = ""
    customer_system: str = ""


class DeploymentModel(BaseModel):
    """Deployment model for tech products."""

    model_type: str = ""
    environment_count: int | None = None


# ===========================================================================
# Group 6: Dependencies & Relationships — sub-models
# ===========================================================================


class BelongsToSegment(BaseModel):
    """Segment membership reference."""

    segment_id: str = ""
    segment_name: str = ""
    primary_segment: bool | None = None


class BuysProduct(BaseModel):
    """Product purchase relationship."""

    product_id: str = ""
    annual_revenue: float | None = None
    currency: str = "USD"
    contract_status: str = ""


class DataSharedWith(BaseModel):
    """Data sharing relationship with the customer."""

    data_asset_id: str = ""
    sharing_direction: str = ""
    data_classification: str = ""


# ===========================================================================
# Customer entity
# ===========================================================================


class Customer(BaseEntity):
    """A customer account in the enterprise knowledge graph.

    Represents the full customer profile including identity, relationship,
    financials, risk/compliance, product consumption, and cross-layer
    dependencies.
    """

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.CUSTOMER
    entity_type: Literal[EntityType.CUSTOMER] = EntityType.CUSTOMER

    # --- Group 1: Identity & Classification ---
    customer_id: str = ""
    customer_name_common: str = ""
    customer_name_former: list[CustomerFormerName] = Field(default_factory=list)
    customer_type: str = ""
    customer_subtype: str = ""
    industry_classification: CustomerIndustryClassification | None = None
    parent_customer: str = ""
    subsidiaries: list[str] = Field(default_factory=list)
    headquarters_location: str = ""
    customer_locations: list[CustomerLocation] = Field(default_factory=list)
    customer_size: CustomerSize | None = None
    origin: str = ""
    functional_domain_primary: str = ""

    # --- Group 2: Relationship & Engagement ---
    relationship_status: str = ""
    relationship_start_date: str = ""
    relationship_tenure_years: float | None = None
    account_tier: str = ""
    engagement_model: str = ""
    primary_contact: PrimaryContact | None = None
    account_team: AccountTeam | None = None
    communication_preferences: CommunicationPreferences | None = None
    satisfaction_current: SatisfactionCurrent | None = None
    health_score: HealthScore | None = None

    # --- Group 3: Financial Profile ---
    revenue_current: CustomerRevenueCurrent | None = None
    revenue_lifetime: RevenueLifetime | None = None
    revenue_by_product: list[RevenueByProduct] = Field(default_factory=list)
    revenue_concentration_risk: RevenueConcentrationRisk | None = None
    contract_value: ContractValue | None = None
    payment_terms: PaymentTerms | None = None
    credit_profile: CreditProfile | None = None
    profitability: Profitability | None = None
    wallet_share: WalletShare | None = None
    expansion_potential: ExpansionPotential | None = None

    # --- Group 4: Risk & Compliance ---
    customer_risk_profile: CustomerRiskProfile | None = None
    sanctions_screening: CustomerSanctionsScreening | None = None
    kyc_status: KycStatus | None = None
    export_control_status: ExportControlStatus | None = None
    data_privacy_obligations: DataPrivacyObligations | None = None
    regulatory_applicability: list[RegulatoryApplicability] = Field(default_factory=list)
    customer_compliance_certifications: list[CustomerComplianceCertification] = Field(
        default_factory=list
    )
    audit_findings: list[AuditFinding] = Field(default_factory=list)

    # --- Group 5: Products & Services Consumed ---
    products_active: list[ActiveProduct] = Field(default_factory=list)
    products_historical: list[HistoricalProduct] = Field(default_factory=list)
    service_agreements: list[ServiceAgreement] = Field(default_factory=list)
    customizations: list[Customization] = Field(default_factory=list)
    integration_points: list[IntegrationPoint] = Field(default_factory=list)
    deployment_model: DeploymentModel | None = None

    # --- Group 6: Dependencies & Relationships ---
    belongs_to_segment: list[BelongsToSegment] = Field(default_factory=list)
    buys_products: list[BuysProduct] = Field(default_factory=list)
    managed_by_org_unit: str = ""
    account_roles: list[str] = Field(default_factory=list)
    located_in: list[str] = Field(default_factory=list)
    uses_systems: list[str] = Field(default_factory=list)
    data_shared_with: list[DataSharedWith] = Field(default_factory=list)
    managed_through_vendors: list[str] = Field(default_factory=list)

    # --- Group 7: Temporal & Provenance ---
    temporal_and_versioning: TemporalAndVersioning = Field(default_factory=TemporalAndVersioning)
    provenance_and_confidence: ProvenanceAndConfidence = Field(
        default_factory=ProvenanceAndConfidence
    )
