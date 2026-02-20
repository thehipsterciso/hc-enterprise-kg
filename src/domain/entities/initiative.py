"""Initiative entity — strategic initiative, program, project, or workstream.

Replaces the L11 stub with a full implementation covering all planned and
active change across the enterprise. Everything else in the graph represents
what the enterprise IS; L11 represents what it is trying to BECOME.

Attribute groups
----------------
1. Identity & Classification (~12 attrs)
2. Strategic Alignment (~8 attrs)
3. Timeline & Status (~10 attrs)
4. Financial Profile (~8 attrs)
5. Governance & Accountability (~8 attrs)
6. Risk & Issues (~6 attrs)
7. Resource Profile (~5 attrs)
8. Dependencies & Relationships — Typed Impact Edges (~12 attrs)
9. Temporal & Provenance

Framework provenance: PMI PMBOK 7th Ed, PRINCE2, SAFe 6.0, MoSCoW,
Stage-Gate, COSO ERM, Val IT, BRM, OKR framework.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, Field

from domain.base import BaseEntity, EntityType
from domain.shared import (
    ProvenanceAndConfidence,
    StrategicAlignment,
    TemporalAndVersioning,
)

# ===========================================================================
# Group 1: Identity & Classification — sub-models
# ===========================================================================


class TaxonomyLineageInitiative(BaseModel):
    """Taxonomy lineage mapping for initiative classification."""

    framework: str = ""
    framework_element_id: str = ""
    mapping_confidence: str = ""


# ===========================================================================
# Group 2: Strategic Alignment — sub-models
# ===========================================================================


class StrategicObjective(BaseModel):
    """Strategic objective that this initiative supports."""

    objective_id: str = ""
    objective_name: str = ""
    alignment_strength: str = ""  # Primary Enabler, Contributing, Tangential
    contribution_description: str = ""


class BusinessCaseSummary(BaseModel):
    """Business case financial summary."""

    problem_statement: str = ""
    proposed_solution: str = ""
    expected_benefits: str = ""
    expected_costs: float | None = None
    currency: str = "USD"
    roi_estimate_pct: float | None = None
    payback_period_months: int | None = None
    npv: float | None = None
    irr_pct: float | None = None


class SuccessCriterion(BaseModel):
    """Measurable success criterion for the initiative."""

    criterion: str = ""
    metric: str = ""
    target: str = ""
    measurement_method: str = ""


class ExpectedOutcome(BaseModel):
    """Expected outcome with quantification."""

    outcome_description: str = ""
    outcome_type: str = ""  # Revenue Growth, Cost Reduction, Risk Reduction, etc.
    quantified_value: float | None = None
    currency: str = "USD"
    confidence: str = ""  # High, Medium, Low


class ValueRealized(BaseModel):
    """Post-implementation value tracking."""

    realized_to_date: float | None = None
    currency: str = "USD"
    realization_methodology: str = ""
    realization_pct_of_expected: float | None = None
    last_measured: str = ""


# ===========================================================================
# Group 3: Timeline & Status — sub-models
# ===========================================================================


class ScheduleVariance(BaseModel):
    """Schedule variance metrics."""

    variance_days: int | None = None  # Positive = behind, negative = ahead
    variance_pct: float | None = None
    trend: str = ""  # Improving, Stable, Worsening


class KeyMilestone(BaseModel):
    """Key milestone with tracking."""

    milestone_name: str = ""
    planned_date: str = ""
    actual_date: str = ""
    status: str = ""  # Not Started, On Track, At Risk, Missed, Completed
    milestone_type: str = ""  # Gate Review, Go-Live, Regulatory Deadline, etc.


class CriticalPathItem(BaseModel):
    """Critical path item requiring tracking."""

    item_description: str = ""
    owner: str = ""
    deadline: str = ""
    status: str = ""  # On Track, At Risk, Blocked, Completed


# ===========================================================================
# Group 4: Financial Profile — sub-models
# ===========================================================================


class TotalBudget(BaseModel):
    """Total approved budget for the initiative."""

    approved_budget: float | None = None
    currency: str = "USD"
    budget_type: str = ""  # Capital, Operating, Mixed


class BudgetBreakdown(BaseModel):
    """Budget breakdown by category."""

    category: str = ""  # Personnel/Labor, Technology/Licensing, etc.
    amount: float | None = None
    currency: str = "USD"


class SpendToDate(BaseModel):
    """Cumulative spend tracking."""

    amount: float | None = None
    currency: str = "USD"
    as_of_date: str = ""


class BudgetVariance(BaseModel):
    """Budget variance metrics."""

    variance_amount: float | None = None  # Positive = over budget
    variance_pct: float | None = None
    trend: str = ""  # Improving, Stable, Worsening


class ForecastAtCompletion(BaseModel):
    """Forecast total cost at completion."""

    amount: float | None = None
    currency: str = "USD"
    confidence: str = ""  # High, Medium, Low


class FundingSource(BaseModel):
    """Funding source for the initiative."""

    source_type: str = ""  # Operating Budget, Capital Budget, etc.
    source_description: str = ""


class CostBenefitAnalysis(BaseModel):
    """Cost-benefit analysis summary."""

    total_cost: float | None = None
    total_benefit: float | None = None
    net_benefit: float | None = None
    currency: str = "USD"
    analysis_period_years: int | None = None
    discount_rate_pct: float | None = None


class RunRateImpact(BaseModel):
    """Ongoing cost/savings after initiative completes."""

    annual_run_rate_change: float | None = None  # Positive = cost increase, negative = savings
    currency: str = "USD"
    effective_date: str = ""


# ===========================================================================
# Group 5: Governance & Accountability — sub-models
# ===========================================================================


class InitiativeGovernanceCadence(BaseModel):
    """Governance review cadence for the initiative."""

    review_frequency: str = ""
    review_forum: str = ""
    last_review_date: str = ""
    next_review_date: str = ""


class DecisionLogEntry(BaseModel):
    """Decision log entry."""

    decision_date: str = ""
    decision_description: str = ""
    decided_by: str = ""
    impact: str = ""


class Methodology(BaseModel):
    """Delivery methodology for the initiative."""

    framework: str = ""  # Waterfall, Agile — Scrum, SAFe, Hybrid, etc.
    adaptation_notes: str = ""


# ===========================================================================
# Group 6: Risk & Issues — sub-models
# ===========================================================================


class InitiativeRiskProfile(BaseModel):
    """Multi-dimensional initiative risk assessment."""

    overall_risk: str = ""
    schedule_risk: str = ""
    budget_risk: str = ""
    scope_risk: str = ""
    resource_risk: str = ""
    technical_risk: str = ""
    organizational_risk: str = ""


class ActiveRisk(BaseModel):
    """Active risk item with mitigation."""

    risk_id: str = ""
    description: str = ""
    probability: str = ""  # Very High, High, Medium, Low, Very Low
    impact: str = ""  # Critical, High, Medium, Low
    risk_level: str = ""
    mitigation_plan: str = ""
    owner: str = ""


class ActiveIssue(BaseModel):
    """Active issue requiring resolution."""

    issue_id: str = ""
    description: str = ""
    severity: str = ""  # Critical, High, Medium, Low
    status: str = ""  # Open, In Progress, Escalated, Resolved, Accepted
    owner: str = ""
    target_resolution_date: str = ""


class InitiativeDependency(BaseModel):
    """Dependency on another initiative."""

    initiative_id: str = ""
    dependency_type: str = ""  # Must Complete Before, Shared Resource, etc.
    dependency_description: str = ""
    impact_if_delayed: str = ""


class Constraint(BaseModel):
    """Constraint on the initiative."""

    constraint_type: str = ""  # Regulatory Deadline, Budget Ceiling, etc.
    description: str = ""
    impact: str = ""


class LessonLearned(BaseModel):
    """Lesson learned — on the node for queryable organizational learning."""

    lesson: str = ""
    category: str = ""  # Planning, Execution, Technology, etc.
    applicable_to_future: str = ""


# ===========================================================================
# Group 7: Resource Profile — sub-models
# ===========================================================================


class ResourceRequirements(BaseModel):
    """Resource requirements summary."""

    total_fte: float | None = None
    internal_fte: float | None = None
    external_fte: float | None = None
    key_skill_gaps: list[str] = Field(default_factory=list)


class ResourceAllocation(BaseModel):
    """Resource allocation from an organizational unit."""

    org_unit_id: str = ""
    org_unit_name: str = ""
    fte_allocated: float | None = None
    role_type: str = ""


class VendorEngagement(BaseModel):
    """Vendor engagement for the initiative."""

    vendor_id: str = ""
    vendor_name: str = ""
    engagement_type: str = ""  # Implementation Partner, Consulting, etc.
    contract_id: str = ""
    spend: float | None = None
    currency: str = "USD"


class TechnologyRequirement(BaseModel):
    """Technology requirement for the initiative."""

    requirement_description: str = ""
    system_id: str = ""
    new_or_existing: str = ""  # New — To Be Procured, Existing — To Be Modified, etc.


class TrainingRequirements(BaseModel):
    """Training requirements for the initiative."""

    training_needed: bool | None = None
    training_plan: str = ""
    affected_roles: list[str] = Field(default_factory=list)
    affected_headcount: int | None = None


# ===========================================================================
# Group 8: Dependencies & Relationships — typed impact edges
# ===========================================================================


class ImpactsCapability(BaseModel):
    """Impact on a business capability."""

    capability_id: str = ""
    impact_type: str = ""  # Creates, Enhances, Transforms, Retires, No Change
    impact_description: str = ""


class ImpactsOrgUnit(BaseModel):
    """Impact on an organizational unit."""

    org_unit_id: str = ""
    impact_type: str = ""  # Creates, Restructures, Merges, Eliminates, Expands, Contracts


class ImpactsRole(BaseModel):
    """Impact on roles."""

    role_id: str = ""
    impact_type: str = ""  # Creates Roles, Eliminates Roles, etc.


class ImpactsLocation(BaseModel):
    """Impact on a location/site."""

    site_id: str = ""
    impact_type: str = ""  # Opens, Closes, Consolidates, Expands, Repurposes


class ImpactsSystem(BaseModel):
    """Impact on a system."""

    system_id: str = ""
    impact_type: str = ""  # Implements New, Migrates, Upgrades, Decommissions, etc.


class ImpactsData(BaseModel):
    """Impact on a data asset."""

    data_asset_id: str = ""
    impact_type: str = ""  # Creates, Migrates, Transforms, Cleanses, etc.


class ImpactsProduct(BaseModel):
    """Impact on a product."""

    product_id: str = ""
    impact_type: str = ""  # Launches, Enhances, Repositions, Retires, Bundles


class ImpactsCustomer(BaseModel):
    """Impact on a customer."""

    customer_id: str = ""
    impact_type: str = ""  # Onboards, Migrates, Changes Service Model, etc.


class ImpactsVendor(BaseModel):
    """Impact on a vendor."""

    vendor_id: str = ""
    impact_type: str = ""  # Onboards, Transitions Away From, Renegotiates, etc.


class RelatedInitiative(BaseModel):
    """Related initiative with relationship type."""

    initiative_id: str = ""
    relationship_type: str = ""  # Depends On, Enables, Conflicts With, etc.


# ===========================================================================
# Initiative entity
# ===========================================================================


class Initiative(BaseEntity):
    """A discrete effort to change the enterprise.

    Hierarchical — Portfolios contain Programs contain Projects contain
    Workstreams. Typed impact edges connect to every other layer, carrying
    not just "this initiative touches that node" but how (Creates, Migrates,
    Decommissions, Transforms).

    Replaces the L11 stub with full enterprise attributes covering identity,
    strategic alignment, timeline, financials, governance, risk, resources,
    and cross-layer impact edges.
    """

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.INITIATIVE
    entity_type: Literal[EntityType.INITIATIVE] = EntityType.INITIATIVE

    # --- Group 1: Identity & Classification ---
    initiative_id: str = ""
    initiative_description_extended: str = ""
    initiative_tier: str = ""  # Portfolio, Program, Project, Workstream, Task
    initiative_type: str = ""  # Digital Transformation, M&A Integration, etc.
    initiative_category: str = ""  # Strategic, Operational, Regulatory, Remediation
    parent_initiative: str = ""
    child_initiatives: list[str] = Field(default_factory=list)
    functional_domain_primary: str = ""
    functional_domain_secondary: list[str] = Field(default_factory=list)
    origin: str = ""  # Strategic Planning, Board Directive, Audit Finding, etc.
    taxonomy_lineage: list[TaxonomyLineageInitiative] = Field(default_factory=list)

    # --- Group 2: Strategic Alignment ---
    strategic_objectives: list[StrategicObjective] = Field(default_factory=list)
    business_case_summary: BusinessCaseSummary | None = None
    strategic_priority: str = ""  # Must Do, Should Do, Could Do, Won't Do
    investment_thesis: str = ""
    success_criteria: list[SuccessCriterion] = Field(default_factory=list)
    expected_outcomes: list[ExpectedOutcome] = Field(default_factory=list)
    value_realized: ValueRealized | None = None
    strategic_alignment: StrategicAlignment | None = None

    # --- Group 3: Timeline & Status ---
    current_status: str = ""  # Proposed, Approved, Planning, In Progress, etc.
    status_rationale: str = ""
    phase: str = ""  # Initiation, Planning, Execution, etc.
    planned_start_date: str = ""
    actual_start_date: str = ""
    planned_end_date: str = ""
    actual_end_date: str = ""
    planned_duration_months: float | None = None
    schedule_variance: ScheduleVariance | None = None
    key_milestones: list[KeyMilestone] = Field(default_factory=list)
    critical_path_items: list[CriticalPathItem] = Field(default_factory=list)

    # --- Group 4: Financial Profile ---
    total_budget: TotalBudget | None = None
    budget_breakdown: list[BudgetBreakdown] = Field(default_factory=list)
    spend_to_date: SpendToDate | None = None
    budget_variance: BudgetVariance | None = None
    forecast_at_completion: ForecastAtCompletion | None = None
    funding_source: FundingSource | None = None
    cost_benefit_analysis: CostBenefitAnalysis | None = None
    run_rate_impact: RunRateImpact | None = None

    # --- Group 5: Governance & Accountability ---
    executive_sponsor: str = ""
    initiative_lead: str = ""
    program_manager: str = ""
    steering_committee: list[str] = Field(default_factory=list)
    owning_org_unit: str = ""
    governance_cadence: InitiativeGovernanceCadence | None = None
    decision_log: list[DecisionLogEntry] = Field(default_factory=list)
    methodology: Methodology | None = None

    # --- Group 6: Risk & Issues ---
    initiative_risk_profile: InitiativeRiskProfile | None = None
    active_risks: list[ActiveRisk] = Field(default_factory=list)
    active_issues: list[ActiveIssue] = Field(default_factory=list)
    dependencies_on_other_initiatives: list[InitiativeDependency] = Field(
        default_factory=list
    )
    constraints: list[Constraint] = Field(default_factory=list)
    lessons_learned: list[LessonLearned] = Field(default_factory=list)

    # --- Group 7: Resource Profile ---
    resource_requirements: ResourceRequirements | None = None
    resource_allocation: list[ResourceAllocation] = Field(default_factory=list)
    vendor_engagement: list[VendorEngagement] = Field(default_factory=list)
    technology_requirements: list[TechnologyRequirement] = Field(default_factory=list)
    training_requirements: TrainingRequirements | None = None

    # --- Group 8: Dependencies & Relationships — typed impact edges ---
    impacts_capabilities: list[ImpactsCapability] = Field(default_factory=list)
    impacts_org_units: list[ImpactsOrgUnit] = Field(default_factory=list)
    impacts_roles: list[ImpactsRole] = Field(default_factory=list)
    impacts_locations: list[ImpactsLocation] = Field(default_factory=list)
    impacts_systems: list[ImpactsSystem] = Field(default_factory=list)
    impacts_data: list[ImpactsData] = Field(default_factory=list)
    impacts_products: list[ImpactsProduct] = Field(default_factory=list)
    impacts_customers: list[ImpactsCustomer] = Field(default_factory=list)
    impacts_vendors: list[ImpactsVendor] = Field(default_factory=list)
    related_initiatives: list[RelatedInitiative] = Field(default_factory=list)

    # --- Group 9: Temporal & Provenance ---
    temporal_and_versioning: TemporalAndVersioning = Field(
        default_factory=TemporalAndVersioning
    )
    provenance_and_confidence: ProvenanceAndConfidence = Field(
        default_factory=ProvenanceAndConfidence
    )
