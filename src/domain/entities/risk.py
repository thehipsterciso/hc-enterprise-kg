"""Risk entity — discrete, assessed, owned enterprise risk.

Completes the governance model: Regulation drives Policy, Policy is
enforced by Control, Control mitigates Risk. Part of L01: Compliance
& Governance layer. Derived from L9 schema.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, Field

from domain.base import BaseEntity, EntityType
from domain.shared import MaterialityAssessment, ProvenanceAndConfidence, TemporalAndVersioning


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


class RiskTaxonomyRef(BaseModel):
    """Cross-reference to an external risk taxonomy."""

    taxonomy: str = ""  # SCF, COSO ERM, ISO 31000, FAIR, NIST RMF, etc.
    taxonomy_id: str = ""  # e.g., R-AC-4
    taxonomy_name: str = ""
    mapping_confidence: str = ""  # Exact Match, Strong, Moderate, Weak, Partial


class FinancialImpact(BaseModel):
    """Quantified financial impact of a risk."""

    estimated_loss_low: float | None = None
    estimated_loss_high: float | None = None
    currency: str = "USD"
    estimation_methodology: str = ""  # FAIR Analysis, Expert Judgment, etc.
    estimation_confidence: str = ""  # High, Medium, Low


class ImpactDimensions(BaseModel):
    """Multi-dimensional impact assessment."""

    financial: str = ""  # None, Low, Medium, High, Critical
    operational: str = ""
    reputational: str = ""
    regulatory: str = ""
    safety: str = ""


class ControlEffectivenessOnRisk(BaseModel):
    """Aggregate control effectiveness on a risk."""

    risk_reduction_pct: float | None = None
    control_count: int | None = None
    weakest_control: str = ""  # Reference to Control with lowest effectiveness


class RiskInterconnection(BaseModel):
    """Relationship between risks."""

    related_risk_id: str = ""
    relationship_type: str = ""  # Causes, Caused By, Amplifies, Amplified By, etc.
    description: str = ""


class RiskTolerance(BaseModel):
    """Specific threshold at which action is required."""

    tolerance_threshold: str = ""
    escalation_trigger: str = ""
    escalation_path: str = ""


class TreatmentPlan(BaseModel):
    """Plan for treating a risk."""

    plan_description: str = ""
    target_residual_risk_level: str = ""  # Critical, High, Medium, Low, Minimal
    actions: list[str] = Field(default_factory=list)
    target_completion_date: str | None = None
    investment_required: float | None = None
    currency: str = "USD"


class AcceptanceRecord(BaseModel):
    """Formal risk acceptance record."""

    accepted_by: str = ""  # Reference to L2 Role
    acceptance_date: str | None = None
    acceptance_rationale: str = ""
    acceptance_expiration: str | None = None
    review_frequency: str = ""


class TransferRecord(BaseModel):
    """Risk transfer record."""

    transfer_mechanism: str = ""  # Insurance, Contract, Outsourcing, etc.
    transfer_counterparty: str = ""
    coverage_limit: float | None = None
    currency: str = "USD"
    policy_or_contract_reference: str = ""


class RiskAssessmentHistory(BaseModel):
    """Historical assessment record for a risk."""

    assessment_date: str | None = None
    assessor: str = ""
    methodology: str = ""
    inherent_level: str = ""
    residual_level: str = ""
    findings: str = ""


class KeyRiskIndicator(BaseModel):
    """Leading indicator that signals a risk is materializing."""

    kri_name: str = ""
    metric: str = ""
    threshold_amber: str = ""
    threshold_red: str = ""
    current_value: str = ""
    measurement_frequency: str = ""
    data_source: str = ""


class RiskScenario(BaseModel):
    """Specific scenario for risk quantification and tabletop exercises."""

    scenario_name: str = ""
    scenario_description: str = ""
    probability: str = ""
    impact_estimate: float | None = None
    currency: str = "USD"


class LossEvent(BaseModel):
    """Historical loss event from this risk materializing."""

    event_date: str | None = None
    event_description: str = ""
    actual_impact: float | None = None
    currency: str = "USD"
    impact_type: str = ""
    root_cause: str = ""
    lessons_learned: str = ""


# ---------------------------------------------------------------------------
# Risk entity
# ---------------------------------------------------------------------------


class Risk(BaseEntity):
    """A discrete, named risk entity with lifecycle, ownership, and treatment.

    Covers the full enterprise risk spectrum: cybersecurity, data privacy,
    strategic, financial, operational, compliance, reputational, geopolitical,
    technology, people, environmental, supply chain, and AI/emerging technology.
    """

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.RISK
    entity_type: Literal[EntityType.RISK] = EntityType.RISK

    # --- Identity & classification ---
    risk_id: str = ""  # Format: RS-XXXXX
    risk_category: str = ""  # Cybersecurity, Data Privacy, Strategic, Financial, etc.
    risk_subcategory: str = ""
    risk_source: str = ""  # Internal, External, Third Party, Regulatory, etc.
    risk_taxonomy_references: list[RiskTaxonomyRef] = Field(default_factory=list)
    nist_csf_function: str = ""  # Govern, Identify, Protect, Detect, Respond, Recover
    risk_group: str = ""  # Logical grouping

    # --- Inherent risk assessment ---
    inherent_likelihood: str = ""  # Almost Certain, Likely, Possible, Unlikely, Rare
    inherent_impact: str = ""  # Catastrophic, Major, Moderate, Minor, Insignificant
    inherent_risk_level: str = ""  # Critical, High, Medium, Low, Minimal
    inherent_financial_impact: FinancialImpact = Field(
        default_factory=FinancialImpact
    )
    inherent_impact_dimensions: ImpactDimensions = Field(
        default_factory=ImpactDimensions
    )

    # --- Residual risk assessment ---
    residual_likelihood: str = ""
    residual_impact: str = ""
    residual_risk_level: str = ""
    control_effectiveness_on_risk: ControlEffectivenessOnRisk = Field(
        default_factory=ControlEffectivenessOnRisk
    )

    # --- Risk dynamics ---
    risk_velocity: str = ""  # Instant, Days, Weeks, Months, Quarters
    risk_trend: str = ""  # Increasing, Stable, Decreasing
    risk_interconnections: list[RiskInterconnection] = Field(default_factory=list)
    emerging_risk_flag: bool = False

    # --- Appetite, tolerance & materiality ---
    risk_appetite: str = ""  # Averse, Conservative, Moderate, Open, Aggressive
    risk_tolerance: RiskTolerance = Field(default_factory=RiskTolerance)
    materiality_assessment: MaterialityAssessment = Field(
        default_factory=MaterialityAssessment
    )
    board_reportable: bool = False

    # --- Ownership & treatment ---
    risk_owner: str = ""  # Reference to L2 Role
    risk_status: str = ""  # Identified, Assessed, Mitigated, Accepted, etc.
    risk_treatment: str = ""  # Mitigate, Accept, Transfer, Avoid
    treatment_plan: TreatmentPlan = Field(default_factory=TreatmentPlan)
    acceptance_record: AcceptanceRecord = Field(default_factory=AcceptanceRecord)
    transfer_record: TransferRecord = Field(default_factory=TransferRecord)

    # --- Assessment & monitoring ---
    last_assessed: str | None = None
    assessment_methodology: str = ""  # FAIR, Qualitative Matrix, Scenario Analysis, etc.
    assessment_cadence: str = ""  # Annual, Semi-Annual, Quarterly, etc.
    next_assessment: str | None = None
    assessment_history: list[RiskAssessmentHistory] = Field(default_factory=list)

    # --- Key risk indicators & loss history ---
    key_risk_indicators: list[KeyRiskIndicator] = Field(default_factory=list)
    risk_scenarios: list[RiskScenario] = Field(default_factory=list)
    loss_event_history: list[LossEvent] = Field(default_factory=list)

    # --- Temporal & provenance ---
    temporal: TemporalAndVersioning = Field(default_factory=TemporalAndVersioning)
    provenance: ProvenanceAndConfidence = Field(
        default_factory=ProvenanceAndConfidence
    )
