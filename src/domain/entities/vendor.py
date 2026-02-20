"""Vendor entity — third-party supplier, service provider, or partner.

Extended in L10 from the original v0.1 entity with full enterprise
attributes covering identity, relationship, financials, performance,
risk/compliance, supply chain, and partnership profiles.

Attribute groups
----------------
1. Identity & Classification (~16 attrs)
2. Relationship & Engagement (~8 attrs)
3. Financial Profile (~8 attrs)
4. Performance & Quality (~8 attrs)
5. Risk & Compliance (~10 attrs)
6. Supply Chain & Dependency (~6 attrs)
7. Partnership Attributes (~5 attrs, conditional)
8. Dependencies & Relationships (~11 attrs)
9. Temporal & Provenance
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, Field

from domain.base import BaseEntity, EntityType
from domain.shared import (
    AuditFinding,
    CostBenchmark,
    ProvenanceAndConfidence,
    RegulatoryApplicability,
    TemporalAndVersioning,
)

# ===========================================================================
# Group 1: Identity & Classification — sub-models
# ===========================================================================


class VendorFormerName(BaseModel):
    """Historical vendor name with effective period."""

    former_name: str = ""
    from_date: str = ""
    to_date: str = ""
    change_reason: str = ""


class VendorIndustryClassification(BaseModel):
    """Industry classification for the vendor."""

    classification_standard: str = ""
    code: str = ""
    description: str = ""


class VendorLocation(BaseModel):
    """Vendor location with role designation."""

    location_id: str = ""
    location_name: str = ""
    location_role: str = ""


class VendorSize(BaseModel):
    """Vendor size metrics."""

    annual_revenue: float | None = None
    employee_count: int | None = None
    currency: str = "USD"
    as_of_date: str = ""


class DiversityClassification(BaseModel):
    """Vendor diversity certification status."""

    certified: bool | None = None
    certification_types: list[str] = Field(default_factory=list)
    certifying_bodies: list[str] = Field(default_factory=list)


# ===========================================================================
# Group 2: Relationship & Engagement — sub-models
# ===========================================================================


class GovernanceCadence(BaseModel):
    """Vendor governance review cadence."""

    review_frequency: str = ""
    last_review_date: str = ""
    next_review_date: str = ""
    review_format: str = ""


# ===========================================================================
# Group 3: Financial Profile — sub-models
# ===========================================================================


class TotalAnnualSpend(BaseModel):
    """Total annual spend with this vendor."""

    amount: float | None = None
    currency: str = "USD"
    fiscal_year: str = ""
    yoy_change_pct: float | None = None


class SpendByCategory(BaseModel):
    """Spend breakdown by category."""

    category: str = ""
    amount: float | None = None
    currency: str = "USD"


class SpendByBU(BaseModel):
    """Spend breakdown by business unit."""

    org_unit_id: str = ""
    org_unit_name: str = ""
    amount: float | None = None
    currency: str = "USD"


class SpendConcentrationRisk(BaseModel):
    """Spend concentration risk assessment."""

    pct_of_category_spend: float | None = None
    pct_of_total_procurement_spend: float | None = None
    concentration_tier: str = ""


class VendorPaymentTerms(BaseModel):
    """Payment terms with the vendor."""

    standard_terms: str = ""
    actual_terms: str = ""
    average_days_to_pay: float | None = None


class CostTrend(BaseModel):
    """Cost trend over time."""

    three_yr_cagr_pct: float | None = None
    trend_driver: str = ""


class SavingsRealized(BaseModel):
    """Savings realized from vendor relationship."""

    amount: float | None = None
    currency: str = "USD"
    period: str = ""
    methodology: str = ""


# ===========================================================================
# Group 4: Performance & Quality — sub-models
# ===========================================================================


class PerformanceScorecard(BaseModel):
    """Overall vendor performance scorecard."""

    overall_score: float | None = None
    scale: str = ""
    methodology: str = ""
    last_assessed: str = ""


class PerformanceDimension(BaseModel):
    """Individual performance dimension score."""

    dimension: str = ""
    score: float | None = None
    weight: float | None = None


class SLACompliance(BaseModel):
    """SLA compliance metrics."""

    sla_count: int | None = None
    slas_met: int | None = None
    sla_compliance_pct: float | None = None
    sla_breaches_12m: int | None = None


class VendorQualityMetrics(BaseModel):
    """Quality metrics for manufacturing/component vendors."""

    defect_rate: float | None = None
    rejection_rate_pct: float | None = None
    corrective_action_count_12m: int | None = None
    quality_trend: str = ""


class DeliveryPerformance(BaseModel):
    """Delivery performance for physical goods suppliers."""

    on_time_delivery_pct: float | None = None
    lead_time_average: str = ""
    lead_time_trend: str = ""


class IncidentHistory(BaseModel):
    """Incident history for technology/service vendors."""

    p1_count_12m: int | None = None
    p2_count_12m: int | None = None
    mttr_hours: float | None = None
    last_major_incident: str = ""


class EscalationEvent(BaseModel):
    """Escalation event record."""

    escalation_date: str = ""
    reason: str = ""
    resolution: str = ""
    days_to_resolve: int | None = None


class InnovationContribution(BaseModel):
    """Vendor innovation contribution assessment."""

    contributes_innovation: bool | None = None
    examples: list[str] = Field(default_factory=list)
    joint_patents: int | None = None
    co_development_active: bool | None = None


# ===========================================================================
# Group 5: Risk & Compliance — sub-models
# ===========================================================================


class VendorRiskProfile(BaseModel):
    """Multi-dimensional vendor risk assessment."""

    overall_risk: str = ""
    financial_risk: str = ""
    operational_risk: str = ""
    cybersecurity_risk: str = ""
    geopolitical_risk: str = ""
    concentration_risk: str = ""


class FinancialStability(BaseModel):
    """Vendor financial stability assessment."""

    credit_rating: str = ""
    credit_agency: str = ""
    financial_health_indicator: str = ""
    bankruptcy_risk: str = ""
    last_assessed: str = ""


class CybersecurityAssessment(BaseModel):
    """Vendor cybersecurity assessment results."""

    assessed: bool | None = None
    assessment_date: str = ""
    assessment_methodology: str = ""
    risk_rating: str = ""
    findings_summary: str = ""
    open_findings_count: int | None = None
    next_assessment_date: str = ""


class BusinessContinuity(BaseModel):
    """Vendor business continuity assessment."""

    bcp_exists: bool | None = None
    bcp_tested: bool | None = None
    bcp_test_date: str = ""
    rto: str = ""
    rpo: str = ""
    geographic_redundancy: bool | None = None
    disaster_recovery_plan: bool | None = None


class VendorComplianceCertification(BaseModel):
    """Compliance certification held by the vendor."""

    certification: str = ""
    issuing_body: str = ""
    status: str = ""
    expiration_date: str = ""
    scope: str = ""


class VendorSanctionsScreening(BaseModel):
    """Sanctions / watchlist screening results."""

    screened: bool | None = None
    screening_date: str = ""
    screening_tool: str = ""
    result: str = ""
    screening_lists: list[str] = Field(default_factory=list)


class DataProcessing(BaseModel):
    """Vendor data processing details (GDPR Article 28)."""

    processes_our_data: bool | None = None
    data_classification_handled: list[str] = Field(default_factory=list)
    data_processing_agreement: bool | None = None
    dpa_reference: str = ""
    sub_processors_disclosed: bool | None = None
    sub_processor_count: int | None = None
    data_residency_confirmed: bool | None = None


class VendorInsuranceCoverage(BaseModel):
    """Vendor insurance coverage verification."""

    cyber_insurance: bool | None = None
    cyber_insurance_limit: float | None = None
    general_liability: bool | None = None
    professional_liability: bool | None = None
    coverage_verified_date: str = ""
    currency: str = "USD"


# ===========================================================================
# Group 6: Supply Chain & Dependency — sub-models
# ===========================================================================


class Substitutability(BaseModel):
    """Vendor substitutability assessment."""

    alternative_vendor_count: int | None = None
    switching_cost: float | None = None
    switching_cost_currency: str = "USD"
    switching_time: str = ""
    switching_complexity: str = ""


class GeographicConcentration(BaseModel):
    """Geographic concentration risk."""

    primary_delivery_location: str = ""
    backup_locations: list[str] = Field(default_factory=list)
    single_geography_risk: bool | None = None
    risk_description: str = ""


class VendorDependency(BaseModel):
    """Dependency on a specific vendor product/service."""

    product_or_service: str = ""
    dependency_strength: str = ""
    impact_if_unavailable: str = ""


class VendorDependencies(BaseModel):
    """Tier 2 vendor visibility."""

    key_sub_vendors: list[str] = Field(default_factory=list)
    known_concentration_risks: str = ""
    visibility_level: str = ""


class ForceMajeureExposure(BaseModel):
    """Force majeure risk exposure."""

    natural_disaster_risk: str = ""
    geopolitical_risk: str = ""
    pandemic_risk: str = ""
    mitigation_plan: str = ""


# ===========================================================================
# Group 7: Partnership Attributes — sub-models
# ===========================================================================


class JointGovernance(BaseModel):
    """Joint governance structure for strategic partnerships."""

    governance_body: str = ""
    meeting_frequency: str = ""
    escalation_path: str = ""


class SharedIP(BaseModel):
    """Shared intellectual property details."""

    ip_exists: bool | None = None
    ip_ownership_model: str = ""
    ip_reference: str = ""


class CoInvestment(BaseModel):
    """Co-investment details."""

    joint_investment_exists: bool | None = None
    investment_amount: float | None = None
    currency: str = "USD"
    investment_purpose: str = ""


class Exclusivity(BaseModel):
    """Exclusivity arrangement details."""

    exclusivity_exists: bool | None = None
    exclusivity_scope: str = ""
    exclusivity_term: str = ""


# ===========================================================================
# Group 8: Dependencies & Relationships — sub-models
# ===========================================================================


class SuppliesProduct(BaseModel):
    """Product supply relationship."""

    product_id: str = ""
    supply_type: str = ""


class ProvidesSystem(BaseModel):
    """System provision relationship."""

    system_id: str = ""
    relationship_type: str = ""


class ProvidesData(BaseModel):
    """Data provision relationship."""

    data_asset_id: str = ""
    provision_type: str = ""


# ===========================================================================
# Vendor entity
# ===========================================================================


class Vendor(BaseEntity):
    """A third-party vendor, supplier, or strategic partner.

    Extended in L10 with full enterprise attributes covering identity,
    relationship, financials, performance, risk/compliance, supply chain,
    and partnership profiles. v0.1 fields preserved for backward compat.
    """

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.VENDOR
    entity_type: Literal[EntityType.VENDOR] = EntityType.VENDOR

    # --- v0.1 fields (preserved for backward compatibility) ---
    vendor_type: str = ""
    contract_value: float | None = None
    risk_tier: str = "medium"
    has_data_access: bool = False
    data_classification_access: list[str] = Field(default_factory=list)
    compliance_certifications: list[str] = Field(default_factory=list)
    contract_expiry: str | None = None
    primary_contact: str = ""
    sla_uptime: float | None = None

    # --- Group 1: Identity & Classification ---
    vendor_id: str = ""
    vendor_name_common: str = ""
    vendor_name_former: list[VendorFormerName] = Field(default_factory=list)
    vendor_category: str = ""
    vendor_subcategory: str = ""
    industry_classification: VendorIndustryClassification | None = None
    headquarters_location: str = ""
    vendor_locations: list[VendorLocation] = Field(default_factory=list)
    vendor_size: VendorSize | None = None
    ownership_structure: str = ""
    origin: str = ""
    diversity_classification: DiversityClassification | None = None
    parent_company: str = ""
    subsidiaries: list[str] = Field(default_factory=list)

    # --- Group 2: Relationship & Engagement ---
    relationship_status: str = ""
    relationship_start_date: str = ""
    relationship_tenure_years: float | None = None
    strategic_importance: str = ""
    engagement_model: str = ""
    vendor_manager: str = ""
    executive_sponsor: str = ""
    governance_cadence: GovernanceCadence | None = None

    # --- Group 3: Financial Profile ---
    total_annual_spend: TotalAnnualSpend | None = None
    spend_by_category: list[SpendByCategory] = Field(default_factory=list)
    spend_by_business_unit: list[SpendByBU] = Field(default_factory=list)
    spend_concentration_risk: SpendConcentrationRisk | None = None
    payment_terms: VendorPaymentTerms | None = None
    cost_trend: CostTrend | None = None
    cost_benchmark: CostBenchmark | None = None
    savings_realized: SavingsRealized | None = None

    # --- Group 4: Performance & Quality ---
    performance_scorecard: PerformanceScorecard | None = None
    performance_dimensions: list[PerformanceDimension] = Field(default_factory=list)
    sla_compliance: SLACompliance | None = None
    quality_metrics: VendorQualityMetrics | None = None
    delivery_performance: DeliveryPerformance | None = None
    incident_history: IncidentHistory | None = None
    escalation_history: list[EscalationEvent] = Field(default_factory=list)
    innovation_contribution: InnovationContribution | None = None

    # --- Group 5: Risk & Compliance ---
    vendor_risk_profile: VendorRiskProfile | None = None
    financial_stability: FinancialStability | None = None
    cybersecurity_assessment: CybersecurityAssessment | None = None
    business_continuity: BusinessContinuity | None = None
    vendor_compliance_certifications: list[VendorComplianceCertification] = Field(
        default_factory=list
    )
    regulatory_applicability: list[RegulatoryApplicability] = Field(
        default_factory=list
    )
    sanctions_screening: VendorSanctionsScreening | None = None
    data_processing: DataProcessing | None = None
    insurance_coverage: VendorInsuranceCoverage | None = None
    audit_findings: list[AuditFinding] = Field(default_factory=list)

    # --- Group 6: Supply Chain & Dependency ---
    supply_chain_role: str = ""
    substitutability: Substitutability | None = None
    geographic_concentration: GeographicConcentration | None = None
    dependency_on_vendor: list[VendorDependency] = Field(default_factory=list)
    vendor_dependencies: VendorDependencies | None = None
    force_majeure_exposure: ForceMajeureExposure | None = None

    # --- Group 7: Partnership Attributes (conditional) ---
    partnership_structure: str = ""
    joint_governance: JointGovernance | None = None
    shared_ip: SharedIP | None = None
    co_investment: CoInvestment | None = None
    exclusivity: Exclusivity | None = None

    # --- Group 8: Dependencies & Relationships ---
    holds_contracts: list[str] = Field(default_factory=list)
    supplies_products: list[SuppliesProduct] = Field(default_factory=list)
    managed_by_org_unit: str = ""
    vendor_management_roles: list[str] = Field(default_factory=list)
    operates_from_locations: list[str] = Field(default_factory=list)
    provides_systems: list[ProvidesSystem] = Field(default_factory=list)
    provides_data: list[ProvidesData] = Field(default_factory=list)
    serves_customers_through: list[str] = Field(default_factory=list)

    # --- Group 9: Temporal & Provenance ---
    temporal_and_versioning: TemporalAndVersioning = Field(
        default_factory=TemporalAndVersioning
    )
    provenance_and_confidence: ProvenanceAndConfidence = Field(
        default_factory=ProvenanceAndConfidence
    )
