"""Policy entity — internal governance instrument.

Translates regulatory requirements and strategic intent into
organizational rules. Part of L01: Compliance & Governance layer.
Derived from L9 schema. Extends original v0.1 Policy with full
enterprise ontology attributes.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, Field

from domain.base import BaseEntity, EntityType
from domain.shared import ProvenanceAndConfidence, TemporalAndVersioning

# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


class PolicyVersion(BaseModel):
    """Version tracking for a policy."""

    version: str = ""
    effective_date: str | None = None
    change_summary: str = ""
    retired_date: str | None = None


class RegulatoryDriver(BaseModel):
    """Regulation that drives a policy."""

    regulation_id: str = ""
    regulation_name: str = ""
    specific_requirements: list[str] = Field(default_factory=list)


class RiskDriver(BaseModel):
    """Risk that drives a policy."""

    risk_id: str = ""
    risk_description: str = ""
    risk_level: str = ""  # Critical, High, Medium, Low, Minimal


class PolicyRequirement(BaseModel):
    """A specific requirement within a policy."""

    requirement_id: str = ""
    requirement_description: str = ""
    requirement_type: str = ""  # Mandatory, Conditional, Recommended


class PolicyAppliesTo(BaseModel):
    """Universal governance connector — scope of a policy across layers."""

    org_units: list[str] = Field(default_factory=list)
    roles: list[str] = Field(default_factory=list)
    systems: list[str] = Field(default_factory=list)
    data_domains: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    products: list[str] = Field(default_factory=list)
    vendors: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
    customer_segments: list[str] = Field(default_factory=list)


class PolicyException(BaseModel):
    """Documented exception to a policy."""

    exception_id: str = ""
    description: str = ""
    approved_by: str = ""
    approval_date: str | None = None
    expiration_date: str | None = None
    justification: str = ""
    compensating_controls: list[str] = Field(default_factory=list)


class EnforcementMechanism(BaseModel):
    """How a policy is enforced."""

    mechanism_type: str = ""  # Technical Control, Manual Review, Audit, etc.
    description: str = ""
    automated: bool = False


class ComplianceMeasurement(BaseModel):
    """How compliance with a policy is measured."""

    metric: str = ""
    target: str = ""
    current_value: str = ""
    measurement_method: str = ""
    frequency: str = ""


class TrainingRequirement(BaseModel):
    """Training required for policy compliance."""

    required: bool = False
    training_program: str = ""
    completion_target_pct: float | None = None
    current_completion_pct: float | None = None
    recertification_frequency: str = ""


class CommunicationPlan(BaseModel):
    """How a policy is communicated to stakeholders."""

    last_communicated: str | None = None
    communication_channel: str = ""
    acknowledgment_required: bool = False
    acknowledgment_rate_pct: float | None = None


class RelatedPolicy(BaseModel):
    """A related policy with relationship type."""

    policy_id: str = ""
    relationship_type: str = ""  # Parent, Child, Supersedes, Superseded By, Related, Conflicts With


# ---------------------------------------------------------------------------
# Policy entity
# ---------------------------------------------------------------------------


class Policy(BaseEntity):
    """An internal governance instrument.

    Translates regulatory requirements and strategic intent into
    organizational rules. A single regulation may drive multiple
    policies. Policies also exist independent of regulation.
    The universal governance connector — applies_to references span
    all layers.
    """

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.POLICY
    entity_type: Literal[EntityType.POLICY] = EntityType.POLICY

    # --- v0.1 fields (preserved for backward compatibility) ---
    policy_type: str = ""
    framework: str = ""
    control_id: str = ""
    severity: str = "medium"
    is_enforced: bool = True
    review_frequency_days: int = 365
    owner_id: str | None = None
    applicable_systems: list[str] = Field(default_factory=list)

    # --- L01 Identity ---
    policy_id: str = ""  # Format: PL-XXXXX
    policy_scope: str = ""  # Enterprise-Wide, Business Unit, Function, Regional, Department

    # --- Status & lifecycle ---
    policy_status: str = ""  # Draft, Under Review, Approved, Active, Under Revision, etc.
    policy_owner: str = ""  # Reference to L2 Role
    policy_author: str = ""  # Reference to L2 Role
    approving_authority: str = ""  # Reference to L2 Role or governance body
    approval_date: str | None = None
    effective_date: str | None = None
    review_cadence: str = ""  # Annual, Semi-Annual, Quarterly, Monthly, As Needed
    last_reviewed_date: str | None = None
    next_review_date: str | None = None
    current_version: PolicyVersion = Field(default_factory=PolicyVersion)
    version_history: list[PolicyVersion] = Field(default_factory=list)

    # --- Drivers ---
    driven_by_regulations: list[RegulatoryDriver] = Field(default_factory=list)
    driven_by_risks: list[RiskDriver] = Field(default_factory=list)

    # --- Requirements & scope ---
    policy_requirements: list[PolicyRequirement] = Field(default_factory=list)
    applies_to: PolicyAppliesTo = Field(default_factory=PolicyAppliesTo)

    # --- Exceptions ---
    exceptions: list[PolicyException] = Field(default_factory=list)

    # --- Enforcement & measurement ---
    enforcement_mechanism: EnforcementMechanism = Field(
        default_factory=EnforcementMechanism
    )
    compliance_measurement: ComplianceMeasurement = Field(
        default_factory=ComplianceMeasurement
    )
    training_requirement: TrainingRequirement = Field(
        default_factory=TrainingRequirement
    )
    communication_plan: CommunicationPlan = Field(default_factory=CommunicationPlan)

    # --- Related policies ---
    related_policies: list[RelatedPolicy] = Field(default_factory=list)

    # --- Temporal & provenance ---
    temporal: TemporalAndVersioning = Field(default_factory=TemporalAndVersioning)
    provenance: ProvenanceAndConfidence = Field(
        default_factory=ProvenanceAndConfidence
    )
