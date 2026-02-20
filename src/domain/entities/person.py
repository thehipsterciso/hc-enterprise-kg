"""Person entity — individual within the enterprise.

Extends the v0.1 Person (~10 fields) to ~64 attributes across 8 groups:
identity, current assignment, skills & competencies, performance &
development, risk & compliance, edge interface ports, temporal, and
provenance. Part of L05: People & Roles layer. Derived from L2 schema.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, Field

from domain.base import BaseEntity, EntityType
from domain.shared import ProvenanceAndConfidence, TemporalAndVersioning

# ---------------------------------------------------------------------------
# Sub-models — Group 1: Identity
# ---------------------------------------------------------------------------


class PersonName(BaseModel):
    """Structured name object for a person."""

    display_name: str = ""
    given_name: str = ""
    family_name: str = ""
    preferred_name: str = ""


class AcquisitionOrigin(BaseModel):
    """Pre-acquisition employment details for acquired employees."""

    acquisition_name: str = ""
    acquisition_date: str | None = None
    pre_acquisition_tenure_years: float | None = None
    pre_acquisition_role: str = ""


# ---------------------------------------------------------------------------
# Sub-models — Group 2: Current Assignment
# ---------------------------------------------------------------------------


class CurrentRoleAssignment(BaseModel):
    """Active role assignment for a person."""

    role_id: str = ""
    assignment_type: str = ""
    # Enum: Primary, Secondary, Acting, Interim, Project-Based
    allocation_pct: float | None = None  # 0-100
    start_date: str | None = None
    expected_end_date: str | None = None


class ReportingRelationship(BaseModel):
    """Solid-line reporting relationship."""

    manager_person_id: str = ""
    manager_role_id: str = ""
    reporting_type: str = ""  # Solid Line, Interim Reporting


class PersonDottedLine(BaseModel):
    """Matrix/dotted-line relationship for a person."""

    person_id: str = ""
    role_id: str = ""
    relationship_type: str = ""
    # Enum: Functional, Technical, Governance, Project, Advisory


# ---------------------------------------------------------------------------
# Sub-models — Group 3: Skills & Competencies
# ---------------------------------------------------------------------------


class SkillInventoryItem(BaseModel):
    """Skill assessment for a person."""

    skill_id: str = ""
    skill_name: str = ""
    skill_category: str = ""
    # Enum: Technical, Domain / Subject Matter, Leadership & Management,
    # Regulatory & Compliance, Analytical & Quantitative,
    # Communication & Influence, Strategic & Business, Operational
    proficiency_level_actual: str = ""  # Awareness, Practitioner, Expert, Master
    proficiency_source: str = ""
    # Enum: Self-Assessed, Manager Assessed, Certification Verified,
    # Peer Reviewed, Assessment Tool, Demonstrated
    last_validated_date: str | None = None


class CertificationHeld(BaseModel):
    """Certification held by a person."""

    certification_name: str = ""
    issuing_body: str = ""
    date_obtained: str | None = None
    expiration_date: str | None = None
    status: str = ""  # Active, Expired, In Renewal, Revoked, Suspended
    credential_id: str = ""


class Education(BaseModel):
    """Educational attainment."""

    institution: str = ""
    degree_level: str = ""
    # Enum: High School / Equivalent, Associate, Bachelor, Master,
    # Doctorate, Professional Degree (JD, MD, etc.), Certificate / Diploma
    field_of_study: str = ""
    graduation_year: int | None = None
    honors: str = ""


class ClearanceHeld(BaseModel):
    """Security clearance held by a person."""

    clearance_type: str = ""
    jurisdiction: str = ""
    status: str = ""  # Active, Expired, Suspended, Under Review
    expiration_date: str | None = None


class LanguageProficiency(BaseModel):
    """Language proficiency of a person."""

    language: str = ""  # ISO 639-1
    proficiency_level: str = ""
    # Enum: Basic, Conversational, Professional Working,
    # Full Professional, Native / Bilingual


class IndustryExperience(BaseModel):
    """Industry experience entry."""

    industry: str = ""
    years: float | None = None


class ExperienceProfile(BaseModel):
    """Professional experience summary."""

    total_years_professional: float | None = None
    years_in_current_role: float | None = None
    years_in_current_domain: float | None = None
    years_at_enterprise: float | None = None
    industry_experience: list[IndustryExperience] = Field(default_factory=list)


class TrainingCompleted(BaseModel):
    """Training record for a person."""

    training_name: str = ""
    training_category: str = ""
    # Enum: Technical, Leadership, Compliance / Regulatory, Safety,
    # Product / Domain, Professional Development
    completion_date: str | None = None
    provider: str = ""
    hours: float | None = None
    expiration_date: str | None = None


class SkillsGapAssessment(BaseModel):
    """Skill gap analysis for a person relative to a role."""

    role_id: str = ""
    skill_id: str = ""
    skill_name: str = ""
    required_level: str = ""  # Awareness, Practitioner, Expert, Master
    actual_level: str = ""  # None, Awareness, Practitioner, Expert, Master
    gap_severity: str = ""
    # Enum: Critical Gap, Significant Gap, Minor Gap, No Gap, Exceeds
    development_plan_reference: str = ""


# ---------------------------------------------------------------------------
# Sub-models — Group 4: Performance & Development
# ---------------------------------------------------------------------------


class PerformanceRating(BaseModel):
    """Performance rating for a period."""

    rating: str = ""
    rating_scale: str = ""
    period: str = ""
    rated_by: str = ""
    calibrated: bool | None = None


class PotentialAssessment(BaseModel):
    """Talent potential assessment (confidential)."""

    potential_level: str = ""
    # Enum: High Potential, Growth Potential, Well-Placed, Career Transition
    assessment_methodology: str = ""
    # Enum: Formal Assessment Center, Manager + Skip Level Calibration,
    # Talent Review Panel, Self + Manager Assessment, Estimated
    assessed_date: str | None = None


class DevelopmentPlan(BaseModel):
    """Individual development plan."""

    plan_reference: str = ""
    focus_areas: list[str] = Field(default_factory=list)
    target_role: str = ""
    target_role_name: str = ""
    target_timeline: str = ""
    plan_status: str = ""
    # Enum: Active, On Track, Behind Schedule, Completed, Abandoned


class CareerAspirations(BaseModel):
    """Career aspiration preferences."""

    target_role_family: str = ""
    target_level: str = ""
    mobility_willingness: str = ""
    # Enum: Open to International Relocation, Open to Domestic Relocation,
    # Open to Travel — No Relocation, Current Location Only
    aspiration_timeline: str = ""


class RetentionAction(BaseModel):
    """Retention action taken for a person (confidential)."""

    action_description: str = ""
    action_type: str = ""
    # Enum: Compensation Adjustment, Role Expansion, Development Opportunity,
    # Mentorship Assignment, Flexible Work Arrangement, Retention Bonus,
    # Recognition, Other
    action_date: str | None = None
    status: str = ""
    # Enum: Planned, In Progress, Completed, Declined by Employee


# ---------------------------------------------------------------------------
# Sub-models — Group 5: Risk & Compliance
# ---------------------------------------------------------------------------


class BackgroundCheckStatus(BaseModel):
    """Background check status."""

    status: str = ""
    # Enum: Completed — Clear, Completed — Findings, In Progress,
    # Not Initiated, Expired, Waived
    check_type: list[str] = Field(default_factory=list)
    completion_date: str | None = None
    next_due_date: str | None = None
    provider: str = ""


class ConflictOfInterestDeclaration(BaseModel):
    """Conflict of interest declaration."""

    declaration_type: str = ""
    # Enum: Financial Interest, Outside Employment, Family Relationship,
    # Board Membership, Vendor Relationship, No Conflict Declared
    description: str = ""
    status: str = ""
    # Enum: Declared — Approved, Declared — Under Review,
    # Declared — Mitigated, Declared — Rejected, Not Declared
    review_date: str | None = None
    reviewer: str = ""


class RegulatoryFitness(BaseModel):
    """Regulatory fitness assessment."""

    regulation: str = ""
    fitness_status: str = ""
    # Enum: Fit and Proper — Confirmed, Under Assessment,
    # Conditions Applied, Not Required
    assessment_date: str | None = None
    next_assessment_date: str | None = None


class AccessPrivilege(BaseModel):
    """System access privilege for a person."""

    system_id: str = ""
    system_name: str = ""
    access_level: str = ""  # Admin, Privileged, Standard, Read Only
    last_access_review_date: str | None = None
    next_review_date: str | None = None
    access_justified: bool | None = None


class InsiderStatus(BaseModel):
    """Insider trading / regulatory insider status."""

    is_insider: bool = False
    insider_type: str = ""
    # Enum: Section 16 Insider, Designated Insider,
    # Project-Based Insider, Not Applicable
    effective_date: str | None = None
    trading_restrictions: str = ""


class MandatoryTrainingCompliance(BaseModel):
    """Mandatory training compliance tracking."""

    training_requirement: str = ""
    regulatory_basis: str = ""
    completion_status: str = ""
    # Enum: Completed, In Progress, Not Started, Overdue, Exempt
    due_date: str | None = None
    completion_date: str | None = None
    overdue_flag: bool = False
    overdue_days: int | None = None


# ---------------------------------------------------------------------------
# Sub-models — Group 6: Edge Interface Ports
# ---------------------------------------------------------------------------


class UnitMembership(BaseModel):
    """Organizational unit membership."""

    unit_id: str = ""
    membership_type: str = ""  # Primary, Secondary, Matrix, Project-Based


class SuccessionCandidacy(BaseModel):
    """Succession candidacy for a role (confidential)."""

    role_id: str = ""
    readiness: str = ""  # Ready Now, Ready in 1 Year, Ready in 2+ Years
    development_gaps: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Main entity
# ---------------------------------------------------------------------------


class Person(BaseEntity):
    """Represents a person in the organization.

    Extended from v0.1 (~10 fields) to full enterprise ontology (~64 attrs).
    Covers identity, current assignment, skills inventory, performance
    management, and risk/compliance for workforce management.
    """

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.PERSON
    entity_type: Literal[EntityType.PERSON] = EntityType.PERSON

    # --- v0.1 fields (preserved for backward compatibility) ---
    first_name: str
    last_name: str
    email: str
    title: str = ""
    employee_id: str = ""
    clearance_level: str = ""
    is_active: bool = True
    hire_date: str | None = None
    phone: str = ""
    department_id: str | None = None

    # --- Group 1: Identity ---
    person_id: str = ""  # PS-XXXXX
    person_name: PersonName = Field(default_factory=PersonName)
    employment_status: str = ""
    # Enum: Active, On Leave — Planned, On Leave — Unplanned, Notice Period,
    # Suspended, Terminated, Retired, Contingent Worker, Vendor Staff
    employment_type: str = ""
    # Enum: Full-Time, Part-Time, Fixed-Term Contract, Indefinite Contract,
    # Vendor-Provided, Intern / Trainee, Temporary / Seasonal
    original_hire_date: str | None = None
    acquisition_origin: AcquisitionOrigin | None = None
    location_primary: str = ""  # Reference to Location (L3)
    location_secondary: list[str] = Field(default_factory=list)

    # --- Group 2: Current Assignment ---
    current_roles: list[CurrentRoleAssignment] = Field(default_factory=list)
    organizational_unit_primary: str = ""  # Reference to OrganizationalUnit (L1)
    organizational_unit_secondary: list[str] = Field(default_factory=list)
    reporting_to: ReportingRelationship = Field(default_factory=ReportingRelationship)
    dotted_line_to: list[PersonDottedLine] = Field(default_factory=list)
    cost_center: str = ""
    work_arrangement: str = ""
    # Enum: On-Site, Hybrid — Primarily On-Site,
    # Hybrid — Primarily Remote, Fully Remote
    timezone: str = ""  # IANA timezone

    # --- Group 3: Skills & Competencies ---
    skills_inventory: list[SkillInventoryItem] = Field(default_factory=list)
    certifications_held: list[CertificationHeld] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    clearances_held: list[ClearanceHeld] = Field(default_factory=list)
    languages: list[LanguageProficiency] = Field(default_factory=list)
    experience_profile: ExperienceProfile = Field(default_factory=ExperienceProfile)
    training_completed: list[TrainingCompleted] = Field(default_factory=list)
    skills_gap_assessment: list[SkillsGapAssessment] = Field(default_factory=list)

    # --- Group 4: Performance & Development ---
    performance_rating_current: PerformanceRating | None = None
    performance_rating_history: list[PerformanceRating] = Field(default_factory=list)
    performance_trajectory: str = ""
    # Enum: High Performer — Accelerating, High Performer — Stable,
    # Solid Performer, Developing, Underperforming,
    # New — Not Yet Rated, Transitioning Roles — Resetting
    potential_assessment: PotentialAssessment | None = None
    development_plan: DevelopmentPlan | None = None
    career_aspirations: CareerAspirations | None = None
    flight_risk: str = ""  # High, Moderate, Low, Unknown
    retention_actions: list[RetentionAction] = Field(default_factory=list)

    # --- Group 5: Risk & Compliance ---
    background_check_status: BackgroundCheckStatus = Field(default_factory=BackgroundCheckStatus)
    conflict_of_interest_declarations: list[ConflictOfInterestDeclaration] = Field(
        default_factory=list
    )
    regulatory_fitness: list[RegulatoryFitness] = Field(default_factory=list)
    access_privileges: list[AccessPrivilege] = Field(default_factory=list)
    insider_status: InsiderStatus = Field(default_factory=InsiderStatus)
    mandatory_training_compliance: list[MandatoryTrainingCompliance] = Field(default_factory=list)

    # --- Group 6: Edge Interface Ports ---
    holds_roles: list[str] = Field(default_factory=list)  # Role IDs
    member_of_unit: list[UnitMembership] = Field(default_factory=list)
    located_at: list[str] = Field(default_factory=list)  # Location IDs
    has_system_access: list[str] = Field(default_factory=list)  # System IDs
    manages_vendor_relationships: list[str] = Field(default_factory=list)  # Vendor IDs
    subject_to_compliance: list[str] = Field(default_factory=list)  # Regulation IDs
    participates_in_initiatives: list[str] = Field(default_factory=list)  # Initiative IDs
    succession_candidate_for: list[SuccessionCandidacy] = Field(default_factory=list)
    mentors: list[str] = Field(default_factory=list)  # Person IDs
    mentored_by: str = ""  # Person ID

    # --- Group 7: Temporal & Versioning (shared) ---
    temporal: TemporalAndVersioning = Field(default_factory=TemporalAndVersioning)

    # --- Group 8: Provenance & Confidence (shared) ---
    provenance: ProvenanceAndConfidence = Field(default_factory=ProvenanceAndConfidence)
