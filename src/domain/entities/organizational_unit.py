"""OrganizationalUnit entity — structural building block of the enterprise.

Replaces the v0.1 Department stub with a full enterprise ontology entity
(~100 attributes across 9 groups). Supports multi-hierarchy structures,
P&L accountability, strategic classification, and governance cadence.
Part of L04: Organization layer. Derived from L1 schema.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, Field

from domain.base import BaseEntity, EntityType
from domain.shared import (
    AuditFinding,
    ProvenanceAndConfidence,
    StrategicAlignment,
    TemporalAndVersioning,
)

# ---------------------------------------------------------------------------
# Sub-models — Group 1: Identity & Classification
# ---------------------------------------------------------------------------


class LocalName(BaseModel):
    """Multi-lingual name for an organizational unit."""

    language_code: str = ""  # ISO 639-1
    name: str = ""
    locale: str = ""


class FormerUnitName(BaseModel):
    """Historical name of an organizational unit."""

    former_name: str = ""
    from_date: str | None = None
    to_date: str | None = None
    change_reason: str = ""


class HierarchyMembership(BaseModel):
    """Parent reference in a specific hierarchy.

    Core structural concept: a unit can have different parents in
    Legal, Operational, Financial, and Geographic hierarchies.
    """

    hierarchy_type: str = ""  # Legal, Operational, Financial, Geographic
    parent_unit_id: str = ""  # Reference to OrganizationalUnit
    position_in_hierarchy: int | None = None
    is_root: bool = False
    effective_date: str | None = None


class MatrixRelationship(BaseModel):
    """Dotted-line or influence relationship between units."""

    related_unit_id: str = ""  # Reference to OrganizationalUnit
    relationship_direction: str = ""  # Influences, Influenced By, Peer
    influence_strength: str = ""  # Strong, Moderate, Advisory
    relationship_description: str = ""
    effective_date: str | None = None


class AcquisitionSourceOU(BaseModel):
    """Acquisition source details for acquired/merged units."""

    source_entity_name: str = ""
    acquisition_date: str | None = None
    deal_reference: str = ""
    integration_status: str = ""  # Complete, In Progress, Planned, Stalled


class TaxonomyLineageOU(BaseModel):
    """Framework crosswalk mapping for an organizational unit."""

    framework: str = ""  # TOGAF, ArchiMate, COBIT, APQC, Custom
    framework_element_id: str = ""
    mapping_confidence: str = ""  # Exact Match, Close Approximation, Partial, Loose


# ---------------------------------------------------------------------------
# Sub-models — Group 2: Operational Profile
# ---------------------------------------------------------------------------


class EmployeeCount(BaseModel):
    """Headcount breakdown for an organizational unit."""

    fte: int | None = None
    contractor: int | None = None
    vendor_fte: int | None = None
    total: int | None = None
    as_of_date: str | None = None


class EmployeeCountByLocation(BaseModel):
    """Per-location headcount breakdown."""

    location_id: str = ""  # Reference to L3 Site
    location_name: str = ""
    fte: int | None = None
    contractor: int | None = None
    vendor_fte: int | None = None


class GeographicPresence(BaseModel):
    """Physical or virtual presence at a location."""

    location_id: str = ""  # Reference to L3 Site
    location_name: str = ""
    presence_type: str = ""  # HQ, Regional Hub, Office, Manufacturing, DC, R&D, etc.


class OperatingHours(BaseModel):
    """Operating hours configuration."""

    timezone_primary: str = ""  # IANA timezone
    timezones_all: list[str] = Field(default_factory=list)
    operating_model: str = ""  # Business Hours, Extended, Follow-the-Sun, 24x7, Shift


class OrgHealthDimension(BaseModel):
    """Individual dimension of organizational health assessment."""

    dimension: str = ""
    score: float | None = None  # 1.0-5.0


class OrgHealthScore(BaseModel):
    """Organizational health assessment (McKinsey OHI / Gallup Q12 / etc.)."""

    score: float | None = None  # 1.0-5.0
    methodology: str = ""  # McKinsey OHI, Gallup Q12, Custom, Composite, Estimated
    dimensions: list[OrgHealthDimension] = Field(default_factory=list)
    assessed_date: str | None = None
    sample_size: int | None = None
    response_rate_pct: float | None = None


class AttritionRate(BaseModel):
    """Employee attrition metrics."""

    annual_total_pct: float | None = None
    voluntary_pct: float | None = None
    involuntary_pct: float | None = None
    regrettable_pct: float | None = None
    as_of_date: str | None = None
    benchmark_comparison: str = ""


class SpanOfControl(BaseModel):
    """Management span-of-control metrics."""

    average_direct_reports: float | None = None
    min_direct_reports: int | None = None
    max_direct_reports: int | None = None


# ---------------------------------------------------------------------------
# Sub-models — Group 3: Financial Profile
# ---------------------------------------------------------------------------


class RevenueAttribution(BaseModel):
    """Revenue attribution for P&L-owning units."""

    annual_revenue: float | None = None
    currency: str = "USD"
    fiscal_year: str = ""
    revenue_type: str = ""  # Direct, Allocated, Intercompany, None


class CostStructure(BaseModel):
    """Cost structure summary."""

    annual_opex: float | None = None
    annual_capex: float | None = None
    total_annual_cost: float | None = None
    currency: str = "USD"
    fiscal_year: str = ""


class CostBreakdownItemOU(BaseModel):
    """Cost category breakdown for an organizational unit."""

    category: str = ""  # Personnel, Contractor, Tech Software, Facilities, etc.
    amount: float | None = None
    percentage_of_total: float | None = None


class BudgetAuthority(BaseModel):
    """Delegated budget and authority limits."""

    approval_limit: float | None = None
    currency: str = "USD"
    delegation_level: str = ""
    hiring_authority: bool = False
    contract_authority: bool = False


class IntercompanyRelationship(BaseModel):
    """Internal economic relationship between units."""

    counterparty_unit_id: str = ""  # Reference to OrganizationalUnit
    relationship_type: str = ""  # Service Provider/Consumer, Transfer Pricing, etc.
    annual_volume: float | None = None
    currency: str = "USD"
    agreement_reference: str = ""


class TaxJurisdiction(BaseModel):
    """Tax jurisdiction for legal entities."""

    jurisdiction_name: str = ""
    tax_id: str = ""
    tax_status: str = ""  # Active, Exempt, Dormant, Under Audit


class StatutoryReportingObligation(BaseModel):
    """Statutory reporting obligation for legal entities."""

    obligation: str = ""
    jurisdiction: str = ""
    frequency: str = ""
    governing_body: str = ""
    compliance_status: str = ""  # Compliant, Non-Compliant, Pending


# ---------------------------------------------------------------------------
# Sub-models — Group 4: Strategic Importance
# ---------------------------------------------------------------------------


class MarketPositionOU(BaseModel):
    """Market position for externally-facing business units."""

    position_description: str = ""
    competitive_rank: int | None = None
    market_share_pct: float | None = None
    market_size_tam: float | None = None
    market_size_sam: float | None = None
    currency: str = "USD"
    as_of_date: str | None = None


# ---------------------------------------------------------------------------
# Sub-models — Group 5: Ownership & Governance
# ---------------------------------------------------------------------------


class LeadershipTeamMember(BaseModel):
    """Direct report on the leadership team."""

    role_id: str = ""  # Reference to L2 Role
    title: str = ""
    functional_responsibility: str = ""


class GoverningBoard(BaseModel):
    """Board governance for legal entities."""

    board_name: str = ""
    board_type: str = ""  # Board of Directors, Advisory Board, Supervisory Board
    member_count: int | None = None
    independent_member_count: int | None = None
    meeting_frequency: str = ""
    charter_reference: str = ""


class ParentReportingRelationship(BaseModel):
    """Upward reporting relationship to parent unit."""

    reports_to_unit_id: str = ""  # Reference to OrganizationalUnit
    reports_to_leader: str = ""  # Reference to L2 Role
    reporting_cadence: str = ""
    reporting_format: str = ""


class DelegationOfAuthority(BaseModel):
    """Delegation of authority limits."""

    financial_limit: float | None = None
    hiring_authority: bool = False
    contract_authority: bool = False
    policy_authority: bool = False
    technology_authority: bool = False


class CharterDocument(BaseModel):
    """Unit charter or mandate document."""

    document_reference: str = ""
    document_date: str | None = None
    last_reviewed_date: str | None = None
    approval_authority: str = ""


# ---------------------------------------------------------------------------
# Sub-models — Group 6: Risk & Compliance
# ---------------------------------------------------------------------------


class RiskFactor(BaseModel):
    """Risk factor for an organizational unit."""

    risk_id: str = ""  # Reference to L01 Risk
    risk_description: str = ""
    risk_category: str = ""  # Operational, Strategic, Financial, Regulatory, etc.
    likelihood: str = ""  # Almost Certain, Likely, Possible, Unlikely, Rare
    impact: str = ""  # Critical, High, Medium, Low
    velocity: str = ""  # Immediate, Days, Weeks, Months, Years


class RegulatoryEnvironment(BaseModel):
    """Regulatory obligation for an organizational unit."""

    regulation: str = ""
    jurisdiction: str = ""
    compliance_status: str = ""  # Compliant, Partially, Non-Compliant, Not Assessed
    regulatory_body: str = ""
    last_examination_date: str | None = None
    next_examination_date: str | None = None
    material_findings: int | None = None


class ControlEnvironmentDimension(BaseModel):
    """Individual control environment maturity dimension."""

    dimension: str = ""  # Control Design, Implementation, Monitoring, etc.
    score: float | None = None  # 1.0-5.0


class ControlEnvironmentMaturity(BaseModel):
    """Control environment maturity assessment."""

    overall_score: float | None = None  # 1.0-5.0
    dimensions: list[ControlEnvironmentDimension] = Field(default_factory=list)
    assessed_date: str | None = None
    assessed_by: str = ""


class LitigationExposure(BaseModel):
    """Litigation exposure for legal entities."""

    active_matters_count: int | None = None
    severity_assessment: str = ""  # Critical, High, Medium, Low
    materiality_flag: bool = False
    total_exposure_estimate: float | None = None
    currency: str = "USD"


class KeyPersonDependency(BaseModel):
    """Key person risk and succession status."""

    person_reference: str = ""  # Reference to L2 Person/Role
    role: str = ""
    criticality: str = ""  # Critical, High, Medium
    succession_plan_exists: bool = False
    successor_identified: bool = False
    successor_readiness: str = ""  # Ready Now, Ready in 1 Year, Ready in 2+ Years


# ---------------------------------------------------------------------------
# Sub-models — Conditional (type-specific extensions)
# ---------------------------------------------------------------------------


class LegalEntityDetails(BaseModel):
    """Extra fields when unit_type = Legal Entity."""

    jurisdiction: str = ""
    registration_id: str = ""
    entity_type_legal: str = ""  # Holding Company, Operating Subsidiary, Branch, etc.
    incorporation_date: str | None = None
    registered_address: str = ""
    registered_capital: float | None = None
    ultimate_parent_entity: str = ""
    ownership_percentage: float | None = None
    minority_interests: list[str] = Field(default_factory=list)
    statutory_directors: list[str] = Field(default_factory=list)


class SharedServiceCatalogEntry(BaseModel):
    """Service offered by a Shared Service Center."""

    service_name: str = ""
    description: str = ""
    service_level: str = ""
    sla_reference: str = ""


class SharedServiceClient(BaseModel):
    """Client unit consuming shared services."""

    unit_id: str = ""  # Reference to OrganizationalUnit
    annual_charge: float | None = None
    satisfaction_score: float | None = None


class SharedServiceDetails(BaseModel):
    """Extra fields when unit_type = Shared Service Center."""

    service_catalog: list[SharedServiceCatalogEntry] = Field(default_factory=list)
    chargeback_model: str = ""  # Full Chargeback, Partial Allocation, Flat Fee, None
    client_units: list[SharedServiceClient] = Field(default_factory=list)


class CoEStandard(BaseModel):
    """Standard published by a Center of Excellence."""

    standard_name: str = ""
    description: str = ""
    adoption_rate_pct: float | None = None


class CoEAdoptionMetrics(BaseModel):
    """Adoption metrics for a Center of Excellence."""

    enterprise_adoption_pct: float | None = None
    units_engaged: int | None = None
    units_total: int | None = None


class CenterOfExcellenceDetails(BaseModel):
    """Extra fields when unit_type = Center of Excellence."""

    expertise_domains: list[str] = Field(default_factory=list)
    standards_published: list[CoEStandard] = Field(default_factory=list)
    adoption_metrics: CoEAdoptionMetrics = Field(default_factory=CoEAdoptionMetrics)


class JVPartnerEntity(BaseModel):
    """Partner in a Joint Venture."""

    partner_name: str = ""
    ownership_pct: float | None = None
    governance_rights: str = ""


class JVOwnershipSplit(BaseModel):
    """Ownership split in a Joint Venture."""

    enterprise_pct: float | None = None
    partner_pct: float | None = None


class JointVentureDetails(BaseModel):
    """Extra fields when unit_type = Joint Venture Unit."""

    partner_entities: list[JVPartnerEntity] = Field(default_factory=list)
    ownership_split: JVOwnershipSplit = Field(default_factory=JVOwnershipSplit)
    governance_agreement_reference: str = ""
    jv_term_years: float | None = None
    renewal_provisions: str = ""
    exit_triggers: list[str] = Field(default_factory=list)
    buyout_mechanisms: str = ""


class IMOSunsetCriterion(BaseModel):
    """Sunset criterion for an Integration Management Office."""

    criterion: str = ""
    status: str = ""  # Met, In Progress, Not Started


class IntegrationManagementOfficeDetails(BaseModel):
    """Extra fields when unit_type = Integration Management Office."""

    integration_target: str = ""  # What's being integrated
    start_date: str | None = None
    target_end_date: str | None = None
    sunset_criteria: list[IMOSunsetCriterion] = Field(default_factory=list)
    transition_plan_reference: str = ""


# ---------------------------------------------------------------------------
# OrganizationalUnit entity
# ---------------------------------------------------------------------------


class OrganizationalUnit(BaseEntity):
    """A structural building block of the enterprise.

    Supports multi-hierarchy structures (Legal, Operational, Financial,
    Geographic), P&L accountability, strategic classification, governance
    cadence, and type-specific extensions for Legal Entities, SSCs, CoEs,
    Joint Ventures, and Integration Management Offices.
    """

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.ORGANIZATIONAL_UNIT
    entity_type: Literal[EntityType.ORGANIZATIONAL_UNIT] = EntityType.ORGANIZATIONAL_UNIT

    # === Group 1: Identity & Classification ===
    unit_id: str = ""  # Format: OU-XXXXX
    unit_type: str = ""  # Legal Entity, Business Unit, Division, Department, Team, etc.
    unit_subtype: str = ""  # Type-specific sub-classification
    unit_description_extended: str = ""
    unit_name_local: list[LocalName] = Field(default_factory=list)
    unit_name_former: list[FormerUnitName] = Field(default_factory=list)
    functional_domain_primary: str = ""  # Strategy & Governance, Finance, Technology, etc.
    functional_domain_secondary: list[str] = Field(default_factory=list)
    operating_model: str = ""  # Product-Centric, Function-Centric, Matrix, Hybrid, etc.
    hierarchy_memberships: list[HierarchyMembership] = Field(default_factory=list)
    matrix_relationships: list[MatrixRelationship] = Field(default_factory=list)
    origin: str = ""  # Organic, Acquired, Merged, Joint Venture, Spun Off, etc.
    acquisition_source: AcquisitionSourceOU = Field(default_factory=AcquisitionSourceOU)
    formation_date: str | None = None
    taxonomy_lineage: list[TaxonomyLineageOU] = Field(default_factory=list)

    # === Group 2: Operational Profile ===
    operational_status: str = ""  # Active, Forming, Restructuring, Integrating, etc.
    operational_status_rationale: str = ""
    operational_status_effective_date: str | None = None
    employee_count: EmployeeCount = Field(default_factory=EmployeeCount)
    employee_count_by_location: list[EmployeeCountByLocation] = Field(default_factory=list)
    geographic_scope: str = ""  # Global, Multi-Regional, Regional, Country, Local
    geographic_presence: list[GeographicPresence] = Field(default_factory=list)
    operating_hours: OperatingHours = Field(default_factory=OperatingHours)
    language_primary: str = ""  # ISO 639-1
    languages_supported: list[str] = Field(default_factory=list)
    culture_integration_status: str = ""  # Native, Integrated, Integrating, Distinct
    organizational_health_score: OrgHealthScore = Field(default_factory=OrgHealthScore)
    attrition_rate: AttritionRate = Field(default_factory=AttritionRate)
    span_of_control: SpanOfControl = Field(default_factory=SpanOfControl)
    management_layers: int | None = None

    # === Group 3: Financial Profile ===
    pl_accountability: bool = False
    revenue_attribution: RevenueAttribution = Field(default_factory=RevenueAttribution)
    cost_structure: CostStructure = Field(default_factory=CostStructure)
    cost_breakdown: list[CostBreakdownItemOU] = Field(default_factory=list)
    budget_authority: BudgetAuthority = Field(default_factory=BudgetAuthority)
    intercompany_relationships: list[IntercompanyRelationship] = Field(default_factory=list)
    cost_center_id: str = ""
    profit_center_id: str = ""
    financial_consolidation_entity: str = ""
    tax_jurisdictions: list[TaxJurisdiction] = Field(default_factory=list)
    statutory_reporting_obligations: list[StatutoryReportingObligation] = Field(
        default_factory=list
    )
    audit_scope: str = ""  # In Scope — External, In Scope — Internal Only, Out of Scope

    # === Group 4: Strategic Importance ===
    strategic_role: str = ""  # Growth Engine, Cash Generator, Turnaround, etc.
    strategic_role_rationale: str = ""
    strategic_alignment: list[StrategicAlignment] = Field(default_factory=list)
    business_criticality: str = ""  # Mission Critical, Business Critical, etc.
    criticality_justification: str = ""
    market_position: MarketPositionOU = Field(default_factory=MarketPositionOU)
    transformation_stage: str = ""  # Pre/Early/Mid/Late Transformation, Optimizing, Stable
    divestiture_candidacy: str = ""  # Not Considered, Under Evaluation, Planned, etc.

    # === Group 5: Ownership & Governance ===
    unit_leader: str = ""  # Reference to L2 Role
    unit_leader_title: str = ""
    leadership_team: list[LeadershipTeamMember] = Field(default_factory=list)
    governing_board: GoverningBoard = Field(default_factory=GoverningBoard)
    governance_cadence: str = ""  # Monthly, Quarterly, Bi-Annual, Annual, Ad Hoc, None
    parent_reporting_relationship: ParentReportingRelationship = Field(
        default_factory=ParentReportingRelationship
    )
    delegation_of_authority: DelegationOfAuthority = Field(default_factory=DelegationOfAuthority)
    compliance_officer: str = ""  # Reference to L2 Role
    data_protection_officer: str = ""  # Reference to L2 Role
    charter_document: CharterDocument = Field(default_factory=CharterDocument)

    # === Group 6: Risk & Compliance ===
    risk_exposure_inherent: str = ""  # Critical, High, Medium, Low
    risk_exposure_residual: str = ""  # Critical, High, Medium, Low
    risk_factors: list[RiskFactor] = Field(default_factory=list)
    regulatory_environment: list[RegulatoryEnvironment] = Field(default_factory=list)
    control_environment_maturity: ControlEnvironmentMaturity = Field(
        default_factory=ControlEnvironmentMaturity
    )
    audit_findings: list[AuditFinding] = Field(default_factory=list)
    litigation_exposure: LitigationExposure = Field(default_factory=LitigationExposure)
    sanctions_screening_status: str = ""  # Cleared, Flagged, Under Review, Not Screened
    business_continuity_tier: str = ""  # Platinum, Gold, Silver, Bronze
    key_person_dependencies: list[KeyPersonDependency] = Field(default_factory=list)

    # === Type-specific extensions (optional sub-models) ===
    legal_entity_details: LegalEntityDetails = Field(default_factory=LegalEntityDetails)
    shared_service_details: SharedServiceDetails = Field(default_factory=SharedServiceDetails)
    center_of_excellence_details: CenterOfExcellenceDetails = Field(
        default_factory=CenterOfExcellenceDetails
    )
    joint_venture_details: JointVentureDetails = Field(default_factory=JointVentureDetails)
    integration_management_office_details: IntegrationManagementOfficeDetails = Field(
        default_factory=IntegrationManagementOfficeDetails
    )

    # === Temporal & Provenance ===
    temporal: TemporalAndVersioning = Field(default_factory=TemporalAndVersioning)
    provenance: ProvenanceAndConfidence = Field(default_factory=ProvenanceAndConfidence)
