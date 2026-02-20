"""Regulation entity — external obligations imposed on the enterprise.

Laws, regulations, standards, and contractual compliance requirements.
Part of L01: Compliance & Governance layer. Derived from L9 schema.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, Field

from domain.base import BaseEntity, EntityType
from domain.shared import ProvenanceAndConfidence, TemporalAndVersioning

# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


class IssuingBody(BaseModel):
    """Governmental, regulatory, or standards body that issues the regulation."""

    body_name: str = ""
    body_type: str = ""  # National Government, State/Provincial, Regulatory Agency, etc.
    jurisdiction: str = ""


class ApplicabilityTrigger(BaseModel):
    """Condition that triggers regulatory applicability."""

    trigger_type: str = ""  # Revenue Threshold, Data Types Processed, Industry, etc.
    trigger_description: str = ""


class ApplicabilityCriteria(BaseModel):
    """Criteria determining whether a regulation applies to the enterprise."""

    criteria_description: str = ""
    triggers: list[ApplicabilityTrigger] = Field(default_factory=list)


class KeyRequirement(BaseModel):
    """A specific requirement within a regulation."""

    requirement_id: str = ""
    requirement_description: str = ""
    requirement_category: str = ""  # Technical, Administrative, Reporting, etc.


class Penalties(BaseModel):
    """Penalty structure for non-compliance."""

    penalty_type: str = ""  # Financial, Criminal, Civil, License Revocation, etc.
    maximum_penalty: str = ""  # e.g., "4% of global annual turnover or €20M"
    penalty_basis: str = ""
    enforcement_history: str = ""


class ComplianceStatus(BaseModel):
    """Current compliance status for a regulation."""

    status: str = ""  # Compliant, Substantially Compliant, Partially, Non-Compliant, Not Assessed
    last_assessed: str | None = None
    assessed_by: str = ""
    next_assessment: str | None = None


class ComplianceGap(BaseModel):
    """A specific gap in compliance with a regulation."""

    gap_description: str = ""
    severity: str = ""  # Critical, High, Medium, Low
    remediation_status: str = ""  # Open, In Progress, Remediated, Accepted, Deferred
    remediation_owner: str = ""  # Reference to L2 Role
    target_date: str | None = None


class MonitoringApproach(BaseModel):
    """How regulatory changes are monitored."""

    method: str = ""  # Regulatory Intelligence Service, Legal Counsel, etc.
    frequency: str = ""
    automated: bool = False
    responsible_party: str = ""


class RegulatoryChange(BaseModel):
    """An upcoming change in the regulatory landscape."""

    change_description: str = ""
    expected_effective_date: str | None = None
    impact_assessment: str = ""
    readiness: str = ""  # Ready, On Track, At Risk, Not Started, Not Assessed


class JurisdictionRef(BaseModel):
    """Reference to a jurisdiction where the regulation applies."""

    jurisdiction_id: str = ""
    jurisdiction_name: str = ""


# ---------------------------------------------------------------------------
# Regulation entity
# ---------------------------------------------------------------------------


class Regulation(BaseEntity):
    """An external obligation imposed on the enterprise.

    Includes laws, regulations, mandatory and voluntary standards,
    and contractual compliance requirements. The enterprise does not
    choose these — they are imposed by jurisdiction, industry, and
    business activity.
    """

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.REGULATION
    entity_type: Literal[EntityType.REGULATION] = EntityType.REGULATION

    # --- Identity ---
    regulation_id: str = ""  # Format: RG-XXXXX
    short_name: str = ""  # e.g., "GDPR"
    regulation_type: str = ""  # Law/Statute, Regulation/Rule, Executive Order, etc.
    regulation_category: str = ""  # Data Privacy, Financial Reporting, Cybersecurity, etc.

    # --- Issuing body ---
    issuing_body: IssuingBody = Field(default_factory=IssuingBody)

    # --- Applicability ---
    jurisdictions: list[JurisdictionRef] = Field(default_factory=list)
    applicability_criteria: ApplicabilityCriteria = Field(
        default_factory=ApplicabilityCriteria
    )
    applicability_status: str = ""  # Applicable, Partially, Not Applicable, Under Assessment
    effective_date: str | None = None
    last_amended_date: str | None = None

    # --- Requirements & penalties ---
    key_requirements: list[KeyRequirement] = Field(default_factory=list)
    penalties: Penalties = Field(default_factory=Penalties)

    # --- Compliance status ---
    compliance_status: ComplianceStatus = Field(default_factory=ComplianceStatus)
    compliance_gaps: list[ComplianceGap] = Field(default_factory=list)

    # --- Monitoring & change ---
    monitoring_approach: MonitoringApproach = Field(default_factory=MonitoringApproach)
    regulatory_change_pipeline: list[RegulatoryChange] = Field(default_factory=list)

    # --- Temporal & provenance ---
    temporal: TemporalAndVersioning = Field(default_factory=TemporalAndVersioning)
    provenance: ProvenanceAndConfidence = Field(
        default_factory=ProvenanceAndConfidence
    )
