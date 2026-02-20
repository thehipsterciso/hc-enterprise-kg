"""Control entity — operational mechanism enforcing policies and mitigating risks.

A specific technical, administrative, or physical mechanism that enforces
a policy or mitigates a risk. Part of L01: Compliance & Governance layer.
Derived from L9 schema.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, Field

from domain.base import BaseEntity, EntityType
from domain.shared import (
    AuditFinding,
    ProvenanceAndConfidence,
    TemporalAndVersioning,
)

# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


class ApplicabilityDimensions(BaseModel):
    """SCF PPTDF applicability model — five-dimension control classification."""

    people: bool = False
    process: bool = False
    technology: bool = False
    data: bool = False
    facility: bool = False


class PrivacyPrincipleMapping(BaseModel):
    """Mapping to SCF Data Privacy Management Principles."""

    principle_id: str = ""
    principle_name: str = ""
    privacy_domain: str = ""  # Data Privacy by Design, Data Subject Participation, etc.


class FrameworkMapping(BaseModel):
    """Mapping to an external compliance framework."""

    framework: str = ""  # NIST CSF 2.0, ISO 27001, CIS Controls v8, SOC 2, etc.
    framework_version: str = ""
    control_id_in_framework: str = ""
    control_name_in_framework: str = ""
    mapping_confidence: str = ""  # Exact Match, Strong, Moderate, Weak, Partial


class RegulationMapping(BaseModel):
    """Mapping from control to a specific regulation requirement."""

    regulation_id: str = ""
    regulation_name: str = ""
    requirement_id: str = ""
    requirement_description: str = ""


class RiskMitigation(BaseModel):
    """How a control mitigates a specific risk."""

    risk_id: str = ""
    risk_description: str = ""
    mitigation_effectiveness: str = ""  # Fully, Substantially, Partially, Minimally


class ControlEffectiveness(BaseModel):
    """Assessment of how well a control achieves its objectives."""

    rating: str = ""  # Effective, Largely Effective, Partially Effective, Ineffective, Not Assessed
    methodology: str = ""
    last_assessed: str | None = None
    assessed_by: str = ""


class AssessmentRecord(BaseModel):
    """Historical assessment record for a control."""

    assessment_date: str | None = None
    assessor: str = ""
    methodology: str = ""
    rating: str = ""
    findings: str = ""


class TestingApproach(BaseModel):
    """How control effectiveness is tested."""

    test_type: str = ""  # Design Effectiveness, Operating Effectiveness, Both
    test_frequency: str = ""
    last_test_date: str | None = None
    test_result: str = ""  # Pass, Pass with Exceptions, Fail, Not Tested


class EvidenceRequirements(BaseModel):
    """Evidence needed to demonstrate control effectiveness."""

    evidence_types: list[str] = Field(default_factory=list)
    evidence_location: str = ""
    retention_period: str = ""
    evidence_collection_automated: bool = False


class AutomationDetails(BaseModel):
    """Details for automated or semi-automated controls."""

    tool_name: str = ""
    system_id: str = ""  # Reference to L4 System
    configuration_reference: str = ""


class ControlKPI(BaseModel):
    """Key performance indicator for a control."""

    metric_name: str = ""
    target: str = ""
    current_value: str = ""
    trend: str = ""  # Improving, Stable, Declining
    measurement_frequency: str = ""


class ControlDependency(BaseModel):
    """Dependency on another control, system, process, or personnel."""

    dependency_type: str = ""  # Requires Control, Requires System, etc.
    dependency_reference: str = ""
    dependency_description: str = ""


class ControlException(BaseModel):
    """Exception to a control's application."""

    exception_id: str = ""
    description: str = ""
    approved_by: str = ""
    approval_date: str | None = None
    expiration_date: str | None = None
    compensating_control: str = ""
    risk_acceptance_reference: str = ""


class GapStatus(BaseModel):
    """Control gap assessment."""

    gap_exists: bool = False
    gap_description: str = ""
    remediation_status: str = ""  # Open, In Progress, Remediated, Accepted, Deferred
    remediation_plan: str = ""
    target_date: str | None = None


class PolicyRef(BaseModel):
    """Reference to a policy this control implements."""

    policy_id: str = ""
    policy_name: str = ""


# ---------------------------------------------------------------------------
# Control entity
# ---------------------------------------------------------------------------


class Control(BaseEntity):
    """A specific mechanism that enforces a policy or mitigates a risk.

    Controls are the operational layer — the thing that actually prevents,
    detects, or corrects. Multi-framework mapping is the highest-value
    attribute: one enterprise control may satisfy requirements across
    NIST CSF, ISO 27001, CIS Controls, and SOC 2 simultaneously.
    """

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.CONTROL
    entity_type: Literal[EntityType.CONTROL] = EntityType.CONTROL

    # --- Identity & classification ---
    control_id: str = ""  # Format: CL-XXXXX
    control_type: str = ""  # Preventive, Detective, Corrective, Deterrent, Compensating
    control_category: str = ""  # Technical, Administrative, Physical
    control_class: str = ""  # Automated, Semi-Automated, Manual
    control_domain: str = ""  # SCF domain: Cybersecurity & Data Privacy Governance, etc.
    control_status: str = ""  # Implemented, Partially Implemented, Planned, etc.
    control_weighting: int | None = None  # 1-10, SCF relative importance

    # --- SCF-specific ---
    applicability_dimensions: ApplicabilityDimensions = Field(
        default_factory=ApplicabilityDimensions
    )
    assessment_question: str = ""  # SCF audit-ready question
    privacy_principle_mappings: list[PrivacyPrincipleMapping] = Field(
        default_factory=list
    )

    # --- Ownership ---
    control_owner: str = ""  # Reference to L2 Role
    control_operator: str = ""  # Reference to L2 Role
    implementing_org_unit: str = ""  # Reference to L1 Organizational Unit

    # --- Framework mapping ---
    implements_policies: list[PolicyRef] = Field(default_factory=list)
    maps_to_frameworks: list[FrameworkMapping] = Field(default_factory=list)
    maps_to_regulations: list[RegulationMapping] = Field(default_factory=list)
    mitigates_risks: list[RiskMitigation] = Field(default_factory=list)

    # --- Effectiveness & assessment ---
    control_effectiveness: ControlEffectiveness = Field(
        default_factory=ControlEffectiveness
    )
    assessment_history: list[AssessmentRecord] = Field(default_factory=list)
    assessment_cadence: str = ""  # Annual, Semi-Annual, Quarterly, etc.
    next_assessment_date: str | None = None
    testing_approach: TestingApproach = Field(default_factory=TestingApproach)
    evidence_requirements: EvidenceRequirements = Field(
        default_factory=EvidenceRequirements
    )

    # --- Implementation ---
    automation_details: AutomationDetails = Field(
        default_factory=AutomationDetails
    )
    kpi: ControlKPI = Field(default_factory=ControlKPI)

    # --- Dependencies & coverage ---
    dependencies: list[ControlDependency] = Field(default_factory=list)
    compensating_controls: list[str] = Field(default_factory=list)
    exceptions: list[ControlException] = Field(default_factory=list)
    gap_status: GapStatus = Field(default_factory=GapStatus)
    audit_findings: list[AuditFinding] = Field(default_factory=list)

    # --- Temporal & provenance ---
    temporal: TemporalAndVersioning = Field(default_factory=TemporalAndVersioning)
    provenance: ProvenanceAndConfidence = Field(
        default_factory=ProvenanceAndConfidence
    )
