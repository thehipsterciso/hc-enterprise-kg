"""Role entity — job role definition within the enterprise.

Extends the v0.1 Role (~5 fields) to ~65 attributes across 7 groups:
identity & classification, requirements & competencies, governance &
accountability, capacity & allocation, edge interface ports, temporal,
and provenance. Part of L05: People & Roles layer. Derived from L2 schema.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, Field

from domain.base import BaseEntity, EntityType
from domain.shared import ProvenanceAndConfidence, TemporalAndVersioning

# ---------------------------------------------------------------------------
# Sub-models — Group 1: Identity & Classification
# ---------------------------------------------------------------------------


class RoleLocalName(BaseModel):
    """Multi-lingual name for a role."""

    language_code: str = ""  # ISO 639-1
    name: str = ""
    locale: str = ""  # ISO 3166-1 alpha-2


class RoleFormerName(BaseModel):
    """Historical name of a role."""

    former_name: str = ""
    from_date: str | None = None
    to_date: str | None = None
    change_reason: str = ""


class RoleFamily(BaseModel):
    """Job family classification."""

    family_name: str = ""
    subfamily: str = ""


class RoleLevel(BaseModel):
    """Grade/band level classification."""

    level_code: str = ""
    level_name: str = ""
    level_band: str = ""
    # Enum: Executive Band, Senior Leadership Band, Management Band,
    # Professional Band — Senior/Mid/Entry, Administrative Band


class RoleTaxonomyLineage(BaseModel):
    """Framework crosswalk mapping for a role."""

    framework: str = ""
    # Enum: NICE Workforce Framework, SFIA v8, APQC, TOGAF / ArchiMate,
    # COBIT, DCAM, DMBOK2, Custom
    framework_element_id: str = ""
    mapping_confidence: str = ""  # Exact Match, Strong Analog, Partial Overlap, No Match


# ---------------------------------------------------------------------------
# Sub-models — Group 2: Requirements & Competencies
# ---------------------------------------------------------------------------


class RequiredSkill(BaseModel):
    """Skill requirement for a role."""

    skill_id: str = ""
    skill_name: str = ""
    skill_category: str = ""
    # Enum: Technical, Domain / Subject Matter, Leadership & Management,
    # Regulatory & Compliance, Analytical & Quantitative,
    # Communication & Influence, Strategic & Business, Operational
    proficiency_level_required: str = ""  # Awareness, Practitioner, Expert, Master
    criticality: str = ""  # Must Have, Should Have, Nice to Have


class RequiredCertification(BaseModel):
    """Certification requirement for a role."""

    certification_name: str = ""
    issuing_body: str = ""
    requirement_level: str = ""  # Mandatory, Strongly Preferred, Preferred
    jurisdiction_specific: bool = False
    applicable_jurisdictions: list[str] = Field(default_factory=list)


class RequiredExperience(BaseModel):
    """Experience requirement for a role."""

    minimum_years_total: int | None = None
    minimum_years_in_domain: int | None = None
    minimum_years_in_role_level: int | None = None
    preferred_industry_experience: list[str] = Field(default_factory=list)
    international_experience_required: bool = False


class RequiredEducation(BaseModel):
    """Education requirement for a role."""

    minimum_level: str = ""
    # Enum: None, High School / Equivalent, Associate, Bachelor, Master,
    # Doctorate, Professional Degree (JD, MD, etc.)
    preferred_fields: list[str] = Field(default_factory=list)
    equivalency_accepted: bool = True


class RequiredClearance(BaseModel):
    """Security clearance requirement."""

    clearance_type: str = ""
    jurisdiction: str = ""
    mandatory: bool = False


class CompetencyReference(BaseModel):
    """Single competency within a competency model."""

    competency_name: str = ""
    required_level: str = ""


class CompetencyModelReference(BaseModel):
    """Reference to enterprise competency model."""

    model_name: str = ""
    applicable_competencies: list[CompetencyReference] = Field(default_factory=list)


class LanguageRequirement(BaseModel):
    """Language proficiency requirement for a role."""

    language: str = ""  # ISO 639-1
    proficiency_level: str = ""
    # Enum: Basic, Conversational, Professional Working,
    # Full Professional, Native / Bilingual
    requirement_level: str = ""  # Mandatory, Preferred


class TravelRequirement(BaseModel):
    """Travel expectations for a role."""

    travel_pct: float | None = None  # 0-100
    travel_scope: str = ""  # Local, Regional, National, International
    travel_frequency: str = ""


class PhysicalRequirements(BaseModel):
    """Physical/environmental requirements for a role."""

    has_physical_requirements: bool = False
    requirement_description: str = ""
    work_environment: str = ""
    # Enum: Office Only, Office + Manufacturing Floor, Office + Data Center,
    # Field-Based, Warehouse / Distribution, Laboratory, Mixed


class FinancialLimit(BaseModel):
    """Monetary limit with currency."""

    amount: float | None = None
    currency: str = "USD"  # ISO 4217


class ContractAuthority(BaseModel):
    """Contract signing authority."""

    max_value: float | None = None
    max_term_months: int | None = None
    currency: str = "USD"  # ISO 4217


class AuthorityDelegated(BaseModel):
    """Delegated authorities for a role."""

    financial_approval_limit: FinancialLimit = Field(default_factory=FinancialLimit)
    hiring_authority: str = ""
    # Enum: Full — All Levels, Up to Director Level, Up to Manager Level,
    # Individual Contributors Only, No Hiring Authority
    contract_authority: ContractAuthority = Field(default_factory=ContractAuthority)
    system_access_level: str = ""
    # Enum: Enterprise Admin, Business Unit Admin, Power User,
    # Standard User, Read Only, No System Access
    data_access_level: str = ""
    # Enum: Unrestricted, Business Unit Scope, Department Scope,
    # Role-Specific Scope, No Direct Data Access


# ---------------------------------------------------------------------------
# Sub-models — Group 3: Governance & Accountability
# ---------------------------------------------------------------------------


class DottedLineRelationship(BaseModel):
    """Matrix/dotted-line reporting relationship."""

    role_id: str = ""
    relationship_type: str = ""
    # Enum: Functional Reporting, Technical Oversight, Governance Oversight,
    # Project Reporting, Advisory
    influence_strength: str = ""  # Strong, Moderate, Advisory


class DirectReportsTarget(BaseModel):
    """Span of control target for a role."""

    target_count: int | None = None
    actual_count: int | None = None
    includes_roles: list[str] = Field(default_factory=list)


class GovernanceMembership(BaseModel):
    """Governance body membership."""

    governance_body_name: str = ""
    membership_type: str = ""
    # Enum: Chair, Voting Member, Non-Voting Member, Secretary,
    # Subject Matter Advisor, Standing Invitee
    cadence: str = ""


class DecisionRight(BaseModel):
    """Decision-making authority."""

    decision_type: str = ""
    authority_level: str = ""  # Decide, Approve, Recommend, Input, Inform
    scope: str = ""


class RegulatoryAccountability(BaseModel):
    """Regulatory accountability for a role."""

    regulation: str = ""
    accountability_description: str = ""
    personal_liability_flag: bool = False
    jurisdiction: str = ""


class RoleMandateDocument(BaseModel):
    """Role mandate/charter document reference."""

    document_reference: str = ""
    document_date: str | None = None
    last_reviewed_date: str | None = None
    approval_authority: str = ""


# ---------------------------------------------------------------------------
# Sub-models — Group 4: Capacity & Allocation
# ---------------------------------------------------------------------------


class VacancyDuration(BaseModel):
    """Vacancy tracking for a role."""

    average_days_vacant: float | None = None
    longest_vacancy_days: float | None = None
    active_recruitment: bool = False
    recruitment_stage: str = ""
    # Enum: Not Started, Job Posted, Screening, Interviewing,
    # Offer Extended, Offer Accepted, On Hold, Frozen


class HeadcountByLocation(BaseModel):
    """Headcount breakdown by location."""

    location_id: str = ""
    location_name: str = ""
    authorized: int | None = None
    filled: int | None = None
    vacant: int | None = None


class CompensationRange(BaseModel):
    """Compensation range for a role (restricted sensitivity)."""

    minimum: float | None = None
    midpoint: float | None = None
    maximum: float | None = None
    currency: str = "USD"  # ISO 4217
    compensation_type: str = ""
    # Enum: Base Salary, Total Cash Compensation,
    # Total Compensation (incl. equity)
    benchmark_source: str = ""
    benchmark_percentile_target: float | None = None  # 1-100


# ---------------------------------------------------------------------------
# Sub-models — Group 5: Edge Interface Ports
# ---------------------------------------------------------------------------


class CapabilityContribution(BaseModel):
    """Role contribution to a business capability."""

    capability_id: str = ""
    contribution_type: str = ""  # Accountable, Responsible, Contributing, Advisory


class UnitAssignment(BaseModel):
    """Role assignment to an organizational unit."""

    unit_id: str = ""
    assignment_type: str = ""  # Primary, Secondary, Matrix, Shared Service


class SystemAccessRequirement(BaseModel):
    """System access requirement for a role."""

    system_id: str = ""
    access_level: str = ""  # Admin, Power User, Standard, Read Only


class DataAccessRequirement(BaseModel):
    """Data asset access requirement for a role."""

    data_asset_id: str = ""
    access_type: str = ""  # Create, Read, Update, Delete, Approve


# ---------------------------------------------------------------------------
# Main entity
# ---------------------------------------------------------------------------


class Role(BaseEntity):
    """Represents a role within the enterprise.

    Extended from v0.1 (~5 fields) to full enterprise ontology (~65 attrs).
    Defines the structural position, requirements, governance accountability,
    and capacity allocation for a job role.
    """

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.ROLE
    entity_type: Literal[EntityType.ROLE] = EntityType.ROLE

    # --- v0.1 fields (preserved for backward compatibility) ---
    department_id: str | None = None
    access_level: str = "standard"
    is_privileged: bool = False
    permissions: list[str] = Field(default_factory=list)
    max_headcount: int | None = None

    # --- Group 1: Identity & Classification ---
    role_id: str = ""  # RL-XXXXX
    role_description_extended: str = ""
    role_type: str = ""
    # Enum: Executive, Senior Leadership, Management,
    # Professional / Individual Contributor, Technical Specialist,
    # Administrative, Governance / Oversight, Temporary / Project-Based
    role_subtype: str = ""
    functional_domain_primary: str = ""
    # Enum: Strategy & Governance, Product & Service Development,
    # Supply Chain & Operations, Customer Engagement & Experience,
    # Human Capital Management, Finance & Accounting, Technology & Digital,
    # Risk & Compliance, Data & Analytics, Corporate Services,
    # Sales & Marketing, Research & Innovation, Enterprise-Wide
    functional_domain_secondary: list[str] = Field(default_factory=list)
    role_family: RoleFamily = Field(default_factory=RoleFamily)
    role_level: RoleLevel = Field(default_factory=RoleLevel)
    origin: str = ""
    # Enum: Organic, Acquired, Merged, Restructured,
    # Regulatory Mandate, Project-Created
    role_name_local: list[RoleLocalName] = Field(default_factory=list)
    role_name_former: list[RoleFormerName] = Field(default_factory=list)
    taxonomy_lineage: list[RoleTaxonomyLineage] = Field(default_factory=list)
    regulatory_designation: str = ""
    # Enum: Statutory Required, Regulatory Required, Best Practice, Discretionary

    # --- Group 2: Requirements & Competencies ---
    required_skills: list[RequiredSkill] = Field(default_factory=list)
    required_certifications: list[RequiredCertification] = Field(default_factory=list)
    required_experience: RequiredExperience = Field(default_factory=RequiredExperience)
    required_education: RequiredEducation = Field(default_factory=RequiredEducation)
    required_clearances: list[RequiredClearance] = Field(default_factory=list)
    competency_model_reference: CompetencyModelReference = Field(
        default_factory=CompetencyModelReference
    )
    language_requirements: list[LanguageRequirement] = Field(default_factory=list)
    travel_requirement: TravelRequirement = Field(default_factory=TravelRequirement)
    physical_requirements: PhysicalRequirements = Field(
        default_factory=PhysicalRequirements
    )
    authority_delegated: AuthorityDelegated = Field(default_factory=AuthorityDelegated)

    # --- Group 3: Governance & Accountability ---
    reports_to_role: str = ""  # Reference to parent Role
    dotted_line_to: list[DottedLineRelationship] = Field(default_factory=list)
    direct_reports_target: DirectReportsTarget = Field(
        default_factory=DirectReportsTarget
    )
    governance_memberships: list[GovernanceMembership] = Field(default_factory=list)
    decision_rights: list[DecisionRight] = Field(default_factory=list)
    regulatory_accountability: list[RegulatoryAccountability] = Field(
        default_factory=list
    )
    succession_criticality: str = ""
    # Enum: Critical — Must Have Successor, Important — Should Have Plan,
    # Standard — Normal Replacement, Temporary — No Succession Needed
    role_mandate_document: RoleMandateDocument = Field(
        default_factory=RoleMandateDocument
    )

    # --- Group 4: Capacity & Allocation ---
    headcount_authorized: int | None = None
    headcount_filled: int | None = None
    headcount_vacant: int | None = None
    vacancy_duration: VacancyDuration | None = None
    headcount_by_location: list[HeadcountByLocation] = Field(default_factory=list)
    allocation_model: str = ""
    # Enum: Dedicated to Single Unit, Shared Across Units,
    # Rotational, Fractional, Pooled
    location_flexibility: str = ""
    # Enum: On-Site Required, Hybrid — Primarily On-Site,
    # Hybrid — Primarily Remote, Fully Remote,
    # Location Flexible — Any Enterprise Site
    employment_type_target: str = ""
    # Enum: Full-Time Employee, Part-Time Employee, Contract — Fixed Term,
    # Contract — Indefinite, Vendor-Provided, Intern / Trainee,
    # Interim / Acting
    compensation_range: CompensationRange | None = None

    # --- Group 5: Edge Interface Ports ---
    fills_capability: list[CapabilityContribution] = Field(default_factory=list)
    belongs_to_unit: list[UnitAssignment] = Field(default_factory=list)
    filled_by_persons: list[str] = Field(default_factory=list)  # Person IDs
    requires_systems_access: list[SystemAccessRequirement] = Field(default_factory=list)
    requires_data_access: list[DataAccessRequirement] = Field(default_factory=list)
    governed_by: list[str] = Field(default_factory=list)  # Regulation/Control IDs
    supports_initiatives: list[str] = Field(default_factory=list)  # Initiative IDs

    # --- Group 6: Temporal & Versioning (shared) ---
    temporal: TemporalAndVersioning = Field(default_factory=TemporalAndVersioning)

    # --- Group 7: Provenance & Confidence (shared) ---
    provenance: ProvenanceAndConfidence = Field(default_factory=ProvenanceAndConfidence)
