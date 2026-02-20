"""BusinessCapability entity — functional building block of the enterprise.

Full enterprise ontology entity (~90 attributes across 9 groups): identity &
classification, maturity & state, performance & measurement, strategic
importance, ownership & accountability, risk & compliance, dependencies &
relationships, temporal, and provenance. Part of L06: Business Capabilities
layer. Derived from L0 schema.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, Field

from domain.base import BaseEntity, EntityType
from domain.shared import (
    AuditFinding,
    CyberExposure,
    ProvenanceAndConfidence,
    RegulatoryApplicability,
    SinglePointOfFailure,
    StrategicAlignment,
    TemporalAndVersioning,
)

# ---------------------------------------------------------------------------
# Sub-models — Group 1: Identity & Classification
# ---------------------------------------------------------------------------


class CapabilityLocalName(BaseModel):
    """Multi-lingual name for a capability."""

    language_code: str = ""  # ISO 639-1
    name: str = ""
    locale: str = ""  # ISO 3166-1 alpha-2


class ValueStreamAlignment(BaseModel):
    """Alignment to a value stream."""

    value_stream_id: str = ""
    value_stream_name: str = ""
    contribution_type: str = ""
    # Enum: Primary Driver, Key Enabler, Supporting, Indirect


class BusinessModelRelevance(BaseModel):
    """Relevance to a business model segment."""

    business_model_segment: str = ""
    relevance_type: str = ""
    # Enum: Critical to Model, Supports Model, Tangential, Not Applicable


class CapabilityTaxonomyLineage(BaseModel):
    """Framework crosswalk mapping for a capability."""

    framework: str = ""
    # Enum: APQC PCF, TOGAF, BIAN, eTOM, ArchiMate, DCAM, DMBOK, SCF, Custom
    framework_element_id: str = ""
    mapping_confidence: str = ""
    # Enum: Exact Match, Strong Analog, Partial Overlap, No Match


# ---------------------------------------------------------------------------
# Sub-models — Group 2: Maturity & State
# ---------------------------------------------------------------------------


class MaturityDimension(BaseModel):
    """Individual maturity dimension assessment."""

    dimension: str = ""
    # Enum: Process Maturity, Technology Enablement, Talent & Skills,
    # Data Quality, Automation Level, Governance Integration,
    # Measurement & Analytics
    score: float | None = None  # 1.0–5.0
    evidence_reference: str = ""
    assessed_date: str | None = None


class MaturityByRegion(BaseModel):
    """Regional maturity breakdown."""

    region_id: str = ""
    region_name: str = ""
    maturity_composite_score: float | None = None  # 1.0–5.0
    maturity_dimensions: list[MaturityDimension] = Field(default_factory=list)
    assessed_date: str | None = None


class MaturityByBusinessUnit(BaseModel):
    """Business unit maturity breakdown."""

    business_unit_id: str = ""
    business_unit_name: str = ""
    maturity_composite_score: float | None = None  # 1.0–5.0
    maturity_dimensions: list[MaturityDimension] = Field(default_factory=list)
    assessed_date: str | None = None


class MaturityTarget(BaseModel):
    """Target maturity state."""

    target_composite_score: float | None = None  # 1.0–5.0
    target_dimensions: list[MaturityDimension] = Field(default_factory=list)
    target_date: str | None = None
    target_rationale: str = ""


# ---------------------------------------------------------------------------
# Sub-models — Group 3: Performance & Measurement
# ---------------------------------------------------------------------------


class KPIDefinition(BaseModel):
    """Key Performance Indicator definition."""

    kpi_id: str = ""
    kpi_name: str = ""
    kpi_description: str = ""
    measurement_frequency: str = ""
    # Enum: Real-Time, Daily, Weekly, Monthly, Quarterly, Annually
    unit_of_measure: str = ""
    target_value: float | None = None
    threshold_critical: float | None = None
    threshold_warning: float | None = None
    data_source_reference: str = ""


class KPICurrentValue(BaseModel):
    """Current value for a KPI."""

    kpi_id: str = ""
    current_value: float | None = None
    measurement_date: str | None = None
    trend_direction: str = ""  # Improving, Stable, Declining


class CostBreakdownItem(BaseModel):
    """Cost breakdown category."""

    category: str = ""
    # Enum: Personnel, Technology, Outsourcing, Facilities,
    # Training, Licensing, Other
    amount: float | None = None


class CostToOperate(BaseModel):
    """Operational cost for a capability."""

    annual_cost: float | None = None
    currency: str = "USD"  # ISO 4217
    cost_type: str = ""  # Fully Loaded, Direct Only, Estimated
    cost_breakdown: list[CostBreakdownItem] = Field(default_factory=list)


class RevenueAttribution(BaseModel):
    """Revenue attribution for a capability."""

    attribution_type: str = ""
    # Enum: Direct Revenue Generating, Revenue Enabling,
    # Cost Avoidance, No Revenue Linkage
    estimated_revenue_impact: float | None = None
    confidence_level: str = ""
    # Enum: High — Data Supported, Medium — Model Derived, Low — Estimated


class CapacityUtilization(BaseModel):
    """Capacity utilization metrics."""

    current_utilization_pct: float | None = None  # 0–100
    peak_utilization_pct: float | None = None  # 0–100
    measurement_basis: str = ""


# ---------------------------------------------------------------------------
# Sub-models — Group 4: Strategic Importance
# ---------------------------------------------------------------------------


class BusinessImpactIfDegraded(BaseModel):
    """Impact assessment if capability is degraded or lost."""

    impact_description: str = ""
    estimated_financial_impact_per_day: float | None = None
    affected_value_streams: list[str] = Field(default_factory=list)
    affected_customer_segments: list[str] = Field(default_factory=list)
    recovery_time_expectation: str = ""


# ---------------------------------------------------------------------------
# Sub-models — Group 5: Ownership & Accountability
# ---------------------------------------------------------------------------


class RACIMatrix(BaseModel):
    """RACI accountability matrix."""

    responsible: list[str] = Field(default_factory=list)  # Role refs
    accountable: list[str] = Field(default_factory=list)  # Role refs
    consulted: list[str] = Field(default_factory=list)  # Role refs
    informed: list[str] = Field(default_factory=list)  # Role refs


class FundingAmount(BaseModel):
    """Budget allocation for a capability."""

    annual_budget: float | None = None
    currency: str = "USD"  # ISO 4217
    fiscal_year: str = ""  # YYYY


class HeadcountAllocation(BaseModel):
    """Headcount allocation for a capability."""

    fte_count: float | None = None
    contractor_count: float | None = None
    vendor_fte_count: float | None = None
    total: float | None = None


# ---------------------------------------------------------------------------
# Sub-models — Group 6: Risk & Compliance
# ---------------------------------------------------------------------------


class RiskFactor(BaseModel):
    """Risk factor for a capability."""

    risk_id: str = ""
    risk_description: str = ""
    risk_category: str = ""
    # Enum: Operational, Strategic, Financial, Regulatory, Technology,
    # Talent, Reputational, Cyber, Third Party, Geopolitical,
    # Environmental, Supply Chain
    likelihood: str = ""
    # Enum: Almost Certain, Likely, Possible, Unlikely, Rare
    impact: str = ""
    # Enum: Catastrophic, Major, Moderate, Minor, Insignificant
    velocity: str = ""
    # Enum: Sudden, Rapid, Gradual, Slow


class ControlReference(BaseModel):
    """Reference to a control covering a capability."""

    control_id: str = ""
    control_framework: str = ""
    # Enum: SCF, NIST CSF, NIST 800-53, ISO 27001, CIS Controls,
    # COBIT, SOX, Custom
    control_description: str = ""
    control_effectiveness: str = ""
    # Enum: Effective, Partially Effective, Ineffective, Not Tested
    last_tested_date: str | None = None


# ---------------------------------------------------------------------------
# Sub-models — Group 7: Dependencies & Relationships
# ---------------------------------------------------------------------------


class CapabilityDependency(BaseModel):
    """Dependency on another capability."""

    capability_id: str = ""
    dependency_type: str = ""  # Requires, Enhances, Optional
    dependency_strength: str = ""  # Hard, Soft, Informational


class CapabilityInterface(BaseModel):
    """Interface with another capability."""

    capability_id: str = ""
    interface_type: str = ""
    # Enum: Synchronous, Asynchronous, Batch, Manual, Event-Driven
    data_exchange_description: str = ""


class SystemSupport(BaseModel):
    """System supporting a capability."""

    system_id: str = ""
    support_type: str = ""
    # Enum: Primary Platform, Supporting Tool, Integration Layer, Infrastructure


class DataSupport(BaseModel):
    """Data asset supporting a capability."""

    data_asset_id: str = ""
    data_relationship_type: str = ""
    # Enum: Primary Data Source, Data Consumer, Data Producer, Data Processor


class VendorDependency(BaseModel):
    """Vendor dependency for a capability."""

    vendor_id: str = ""
    dependency_criticality: str = ""
    # Enum: Critical — No Alternative, Critical — Alternatives Exist,
    # Important, Convenience


# ---------------------------------------------------------------------------
# Main entity
# ---------------------------------------------------------------------------


class BusinessCapability(BaseEntity):
    """Represents a business capability in the enterprise.

    Full enterprise ontology entity (~90 attributes across 9 groups).
    Models the functional decomposition of the enterprise: what the
    organization does (not how). Used for strategic planning, gap analysis,
    and investment prioritization.
    """

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.BUSINESS_CAPABILITY
    entity_type: Literal[EntityType.BUSINESS_CAPABILITY] = EntityType.BUSINESS_CAPABILITY

    # --- Group 1: Identity & Classification ---
    capability_id: str = ""  # BC-{L1}.{L2}.{L3}
    capability_description_extended: str = ""
    tier: str = ""  # Strategic, Business, Component
    tier_justification: str = ""
    capability_type: str = ""
    # Enum: Core Differentiating, Core Non-Differentiating, Supporting,
    # Management, Enabling Infrastructure
    functional_domain: str = ""
    # Enum: Strategy & Governance, Product & Service Development,
    # Supply Chain & Operations, Customer Engagement & Experience,
    # Human Capital Management, Finance & Accounting, Technology & Digital,
    # Risk & Compliance, Data & Analytics, Corporate Services,
    # Sales & Marketing, Research & Innovation
    functional_domain_secondary: list[str] = Field(default_factory=list)
    capability_name_local: list[CapabilityLocalName] = Field(default_factory=list)
    value_stream_alignment: list[ValueStreamAlignment] = Field(default_factory=list)
    business_model_relevance: list[BusinessModelRelevance] = Field(default_factory=list)
    taxonomy_lineage: list[CapabilityTaxonomyLineage] = Field(default_factory=list)
    origin: str = ""
    # Enum: Organic, Acquired, Merged, Outsourced, Joint Venture, Inherited
    acquisition_source: str = ""

    # --- Group 2: Maturity & State ---
    maturity_model_reference: str = ""  # CMM, DCAM, DMBOK Maturity Model, Custom
    maturity_composite_score: float | None = None  # 1.0–5.0
    maturity_dimensions: list[MaturityDimension] = Field(default_factory=list)
    maturity_by_region: list[MaturityByRegion] = Field(default_factory=list)
    maturity_by_business_unit: list[MaturityByBusinessUnit] = Field(default_factory=list)
    maturity_target: MaturityTarget | None = None
    maturity_trajectory: str = ""  # Improving, Stable, Declining, Unknown
    lifecycle_state: str = ""
    # Enum: Planned, Pilot, Active, Scaling, Mature, Declining,
    # Deprecated, Retired
    lifecycle_state_rationale: str = ""
    lifecycle_transition_date: str | None = None
    lifecycle_next_state: str = ""
    lifecycle_next_state_target_date: str | None = None

    # --- Group 3: Performance & Measurement ---
    performance_status: str = ""
    # Enum: Exceeding, Meeting, Below, Critical, Not Measured
    kpi_definitions: list[KPIDefinition] = Field(default_factory=list)
    kpi_current_values: list[KPICurrentValue] = Field(default_factory=list)
    cost_to_operate: CostToOperate | None = None
    cost_benchmark: StrategicAlignment | None = None  # Reuses shared CostBenchmark
    revenue_attribution: RevenueAttribution | None = None
    capacity_utilization: CapacityUtilization | None = None

    # --- Group 4: Strategic Importance ---
    strategic_alignment: list[StrategicAlignment] = Field(default_factory=list)
    business_criticality: str = ""
    # Enum: Mission Critical, Business Critical, Business Operational, Administrative
    criticality_justification: str = ""
    business_impact_if_degraded: BusinessImpactIfDegraded | None = None
    differentiation_level: str = ""
    # Enum: Commodity, Competitive Parity, Differentiating, Distinctive
    differentiation_evidence: str = ""
    sourcing_suitability: str = ""
    # Enum: Must Own, Prefer Own, Outsource Candidate,
    # Outsource Recommended, Currently Outsourced
    strategic_risk_if_lost: str = ""

    # --- Group 5: Ownership & Accountability ---
    executive_sponsor: str = ""  # Role reference
    capability_owner: str = ""  # Role reference
    governance_body: str = ""
    governance_cadence: str = ""
    # Enum: Monthly, Quarterly, Bi-Annual, Annual, Ad Hoc, None
    raci_matrix: RACIMatrix | None = None
    shared_service_model: str = ""
    # Enum: Dedicated, Shared Service, Center of Excellence,
    # Federated, Hybrid, Not Applicable
    funding_model: str = ""
    # Enum: Centrally Funded, BU Funded, Chargeback,
    # Shared Cost Pool, Unfunded
    funding_amount: FundingAmount | None = None
    headcount_allocation: HeadcountAllocation | None = None

    # --- Group 6: Risk & Compliance ---
    risk_exposure_inherent: str = ""  # Critical, High, Medium, Low
    risk_exposure_residual: str = ""  # Critical, High, Medium, Low
    risk_factors: list[RiskFactor] = Field(default_factory=list)
    control_coverage: str = ""
    # Enum: Comprehensive, Substantial, Partial, Minimal, None, Unknown
    control_references: list[ControlReference] = Field(default_factory=list)
    regulatory_applicability: list[RegulatoryApplicability] = Field(default_factory=list)
    audit_findings: list[AuditFinding] = Field(default_factory=list)
    resilience_tier: str = ""  # Platinum, Gold, Silver, Bronze
    rto: float | None = None  # hours
    rpo: float | None = None  # hours
    single_points_of_failure: list[SinglePointOfFailure] = Field(default_factory=list)
    cyber_exposure: CyberExposure | None = None

    # --- Group 7: Dependencies & Relationships ---
    parent_capability: str = ""  # Self-reference to parent
    child_capabilities: list[str] = Field(default_factory=list)
    depends_on_capabilities: list[CapabilityDependency] = Field(default_factory=list)
    enables_capabilities: list[str] = Field(default_factory=list)
    interfaces_with: list[CapabilityInterface] = Field(default_factory=list)
    supported_by_systems: list[SystemSupport] = Field(default_factory=list)
    supported_by_data: list[DataSupport] = Field(default_factory=list)
    delivered_through_products: list[str] = Field(default_factory=list)
    owned_by_organization: list[str] = Field(default_factory=list)
    staffed_by: list[str] = Field(default_factory=list)  # Role/Person IDs
    located_at: list[str] = Field(default_factory=list)  # Location IDs
    governed_by: list[str] = Field(default_factory=list)  # Regulation/Control IDs
    realized_by_initiatives: list[str] = Field(default_factory=list)
    depends_on_vendors: list[VendorDependency] = Field(default_factory=list)
    serves_customers: list[str] = Field(default_factory=list)

    # --- Group 8: Temporal & Versioning (shared) ---
    temporal: TemporalAndVersioning = Field(default_factory=TemporalAndVersioning)

    # --- Group 9: Provenance & Confidence (shared) ---
    provenance: ProvenanceAndConfidence = Field(default_factory=ProvenanceAndConfidence)
