"""Tests for L11: Strategic Initiatives — Initiative entity."""

from __future__ import annotations

import json

from pydantic import TypeAdapter

from domain.entities import AnyEntity
from domain.entities.initiative import (
    ActiveIssue,
    ActiveRisk,
    BudgetBreakdown,
    BudgetVariance,
    BusinessCaseSummary,
    Constraint,
    CostBenefitAnalysis,
    CriticalPathItem,
    DecisionLogEntry,
    ExpectedOutcome,
    ForecastAtCompletion,
    FundingSource,
    ImpactsCapability,
    ImpactsCustomer,
    ImpactsData,
    ImpactsLocation,
    ImpactsOrgUnit,
    ImpactsProduct,
    ImpactsRole,
    ImpactsSystem,
    ImpactsVendor,
    Initiative,
    InitiativeDependency,
    InitiativeGovernanceCadence,
    InitiativeRiskProfile,
    KeyMilestone,
    LessonLearned,
    Methodology,
    RelatedInitiative,
    ResourceAllocation,
    ResourceRequirements,
    RunRateImpact,
    ScheduleVariance,
    SpendToDate,
    StrategicObjective,
    SuccessCriterion,
    TaxonomyLineageInitiative,
    TechnologyRequirement,
    TotalBudget,
    TrainingRequirements,
    ValueRealized,
    VendorEngagement,
)


class TestInitiative:
    """Tests for the Initiative entity."""

    def test_minimal_construction(self) -> None:
        """Initiative can be created with just a name."""
        init = Initiative(name="Data Platform Modernization")
        assert init.entity_type == "initiative"
        assert init.name == "Data Platform Modernization"
        assert init.initiative_tier == ""
        assert init.current_status == ""

    def test_identity_and_classification(self) -> None:
        """Group 1: Identity & Classification attributes."""
        init = Initiative(
            name="Enterprise Data Platform Modernization",
            initiative_id="SI-00042",
            initiative_tier="Program",
            initiative_type="Digital Transformation",
            initiative_category="Strategic",
            parent_initiative="SI-00001",
            child_initiatives=["SI-00043", "SI-00044", "SI-00045"],
            functional_domain_primary="Technology",
            functional_domain_secondary=["Data & Analytics", "Operations"],
            origin="Strategic Planning",
            taxonomy_lineage=[
                TaxonomyLineageInitiative(
                    framework="PMI",
                    framework_element_id="PMI-PROG-001",
                    mapping_confidence="High",
                )
            ],
        )
        assert init.initiative_id == "SI-00042"
        assert init.initiative_tier == "Program"
        assert init.initiative_type == "Digital Transformation"
        assert init.initiative_category == "Strategic"
        assert init.parent_initiative == "SI-00001"
        assert len(init.child_initiatives) == 3
        assert init.origin == "Strategic Planning"
        assert init.taxonomy_lineage[0].framework == "PMI"

    def test_strategic_alignment(self) -> None:
        """Group 2: Strategic Alignment attributes."""
        init = Initiative(
            name="Cloud Migration",
            strategic_objectives=[
                StrategicObjective(
                    objective_id="SO-001",
                    objective_name="Technology Modernization",
                    alignment_strength="Primary Enabler",
                    contribution_description="Core enabler of cloud-first strategy",
                )
            ],
            business_case_summary=BusinessCaseSummary(
                problem_statement="Legacy infrastructure at end of life",
                proposed_solution="Migrate to cloud-native architecture",
                expected_benefits="40% reduction in infrastructure costs",
                expected_costs=12_000_000,
                currency="USD",
                roi_estimate_pct=180.0,
                payback_period_months=24,
                npv=8_500_000,
                irr_pct=35.0,
            ),
            strategic_priority="Must Do",
            investment_thesis="Avoid $20M infrastructure refresh cycle",
            success_criteria=[
                SuccessCriterion(
                    criterion="Cloud migration complete",
                    metric="Workloads migrated",
                    target="100%",
                    measurement_method="Cloud management console",
                )
            ],
            expected_outcomes=[
                ExpectedOutcome(
                    outcome_description="Infrastructure cost reduction",
                    outcome_type="Cost Reduction",
                    quantified_value=4_800_000,
                    currency="USD",
                    confidence="High",
                )
            ],
            value_realized=ValueRealized(
                realized_to_date=2_100_000,
                currency="USD",
                realization_methodology="Finance-validated savings",
                realization_pct_of_expected=43.75,
                last_measured="2025-12-31",
            ),
        )
        assert init.strategic_priority == "Must Do"
        assert init.business_case_summary.npv == 8_500_000
        assert init.business_case_summary.irr_pct == 35.0
        assert init.success_criteria[0].metric == "Workloads migrated"
        assert init.expected_outcomes[0].quantified_value == 4_800_000
        assert init.value_realized.realization_pct_of_expected == 43.75

    def test_timeline_and_status(self) -> None:
        """Group 3: Timeline & Status attributes."""
        init = Initiative(
            name="ERP Upgrade",
            current_status="In Progress",
            status_rationale="On track for Q3 go-live",
            phase="Execution",
            planned_start_date="2025-01-15",
            actual_start_date="2025-02-01",
            planned_end_date="2025-09-30",
            planned_duration_months=9.0,
            schedule_variance=ScheduleVariance(
                variance_days=17,
                variance_pct=6.3,
                trend="Stable",
            ),
            key_milestones=[
                KeyMilestone(
                    milestone_name="Go-Live",
                    planned_date="2025-09-15",
                    status="On Track",
                    milestone_type="Go-Live",
                )
            ],
            critical_path_items=[
                CriticalPathItem(
                    item_description="Data migration validation",
                    owner="Data Engineering Lead",
                    deadline="2025-07-15",
                    status="On Track",
                )
            ],
        )
        assert init.current_status == "In Progress"
        assert init.phase == "Execution"
        assert init.schedule_variance.variance_days == 17
        assert init.key_milestones[0].milestone_type == "Go-Live"
        assert init.critical_path_items[0].owner == "Data Engineering Lead"

    def test_financial_profile(self) -> None:
        """Group 4: Financial Profile attributes."""
        init = Initiative(
            name="Security Remediation",
            total_budget=TotalBudget(
                approved_budget=5_000_000,
                currency="USD",
                budget_type="Mixed",
            ),
            budget_breakdown=[
                BudgetBreakdown(category="Technology / Licensing", amount=2_000_000),
                BudgetBreakdown(category="Professional Services", amount=1_500_000),
                BudgetBreakdown(category="Personnel / Labor", amount=1_200_000),
                BudgetBreakdown(category="Contingency", amount=300_000),
            ],
            spend_to_date=SpendToDate(
                amount=3_200_000,
                currency="USD",
                as_of_date="2025-11-30",
            ),
            budget_variance=BudgetVariance(
                variance_amount=200_000,
                variance_pct=4.0,
                trend="Stable",
            ),
            forecast_at_completion=ForecastAtCompletion(
                amount=5_200_000,
                currency="USD",
                confidence="Medium",
            ),
            funding_source=FundingSource(
                source_type="Regulatory Reserve",
                source_description="Allocated from regulatory compliance fund",
            ),
            cost_benefit_analysis=CostBenefitAnalysis(
                total_cost=5_200_000,
                total_benefit=15_000_000,
                net_benefit=9_800_000,
                currency="USD",
                analysis_period_years=5,
                discount_rate_pct=8.0,
            ),
            run_rate_impact=RunRateImpact(
                annual_run_rate_change=-800_000,
                currency="USD",
                effective_date="2026-01-01",
            ),
        )
        assert init.total_budget.approved_budget == 5_000_000
        assert len(init.budget_breakdown) == 4
        assert init.spend_to_date.amount == 3_200_000
        assert init.budget_variance.variance_amount == 200_000
        assert init.forecast_at_completion.confidence == "Medium"
        assert init.funding_source.source_type == "Regulatory Reserve"
        assert init.cost_benefit_analysis.net_benefit == 9_800_000
        assert init.run_rate_impact.annual_run_rate_change == -800_000

    def test_governance_and_accountability(self) -> None:
        """Group 5: Governance & Accountability attributes."""
        init = Initiative(
            name="M&A Integration",
            executive_sponsor="CTO",
            initiative_lead="VP Engineering",
            program_manager="PMO Director",
            steering_committee=["CTO", "CFO", "CHRO", "COO"],
            owning_org_unit="OU-00010",
            governance_cadence=InitiativeGovernanceCadence(
                review_frequency="Bi-weekly",
                review_forum="Integration Steering Committee",
                last_review_date="2025-12-15",
                next_review_date="2025-12-29",
            ),
            decision_log=[
                DecisionLogEntry(
                    decision_date="2025-11-01",
                    decision_description="Approved Phase 2 scope expansion",
                    decided_by="Steering Committee",
                    impact="Budget increase of $500K, timeline extended 6 weeks",
                )
            ],
            methodology=Methodology(
                framework="Hybrid",
                adaptation_notes="Waterfall for infrastructure, Agile for application workstreams",
            ),
        )
        assert init.executive_sponsor == "CTO"
        assert len(init.steering_committee) == 4
        assert init.governance_cadence.review_frequency == "Bi-weekly"
        assert init.decision_log[0].decided_by == "Steering Committee"
        assert init.methodology.framework == "Hybrid"

    def test_risk_and_issues(self) -> None:
        """Group 6: Risk & Issues attributes."""
        init = Initiative(
            name="Regulatory Compliance Program",
            initiative_risk_profile=InitiativeRiskProfile(
                overall_risk="High",
                schedule_risk="Medium",
                budget_risk="Low",
                scope_risk="Medium",
                resource_risk="High",
                technical_risk="Low",
                organizational_risk="Medium",
            ),
            active_risks=[
                ActiveRisk(
                    risk_id="R-001",
                    description="Key SME departure risk",
                    probability="Medium",
                    impact="High",
                    risk_level="High",
                    mitigation_plan="Cross-training and documentation",
                    owner="Program Manager",
                )
            ],
            active_issues=[
                ActiveIssue(
                    issue_id="I-001",
                    description="Vendor delivery delay on module 3",
                    severity="High",
                    status="In Progress",
                    owner="Vendor Manager",
                    target_resolution_date="2026-01-15",
                )
            ],
            dependencies_on_other_initiatives=[
                InitiativeDependency(
                    initiative_id="SI-00010",
                    dependency_type="Must Complete Before",
                    dependency_description="Data migration must complete before reporting",
                    impact_if_delayed="Regulatory deadline at risk",
                )
            ],
            constraints=[
                Constraint(
                    constraint_type="Regulatory Deadline",
                    description="Must be compliant by Q2 2026",
                    impact="Non-compliance penalties",
                )
            ],
            lessons_learned=[
                LessonLearned(
                    lesson="Early stakeholder engagement reduced change resistance by 60%",
                    category="Stakeholder Management",
                    applicable_to_future="All enterprise-wide programs",
                )
            ],
        )
        assert init.initiative_risk_profile.overall_risk == "High"
        assert init.active_risks[0].probability == "Medium"
        assert init.active_issues[0].severity == "High"
        assert init.dependencies_on_other_initiatives[0].dependency_type == "Must Complete Before"
        assert init.constraints[0].constraint_type == "Regulatory Deadline"
        assert init.lessons_learned[0].category == "Stakeholder Management"

    def test_resource_profile(self) -> None:
        """Group 7: Resource Profile attributes."""
        init = Initiative(
            name="AI Platform Build",
            resource_requirements=ResourceRequirements(
                total_fte=45.0,
                internal_fte=30.0,
                external_fte=15.0,
                key_skill_gaps=["MLOps", "Data Engineering", "AI Ethics"],
            ),
            resource_allocation=[
                ResourceAllocation(
                    org_unit_id="OU-00005",
                    org_unit_name="Technology",
                    fte_allocated=20.0,
                    role_type="Engineering",
                ),
                ResourceAllocation(
                    org_unit_id="OU-00008",
                    org_unit_name="Data & Analytics",
                    fte_allocated=10.0,
                    role_type="Data Science",
                ),
            ],
            vendor_engagement=[
                VendorEngagement(
                    vendor_id="V-00042",
                    vendor_name="CloudAI Corp",
                    engagement_type="Implementation Partner",
                    contract_id="C-00099",
                    spend=2_500_000,
                    currency="USD",
                )
            ],
            technology_requirements=[
                TechnologyRequirement(
                    requirement_description="GPU compute cluster",
                    system_id="SYS-00150",
                    new_or_existing="New — To Be Procured",
                )
            ],
            training_requirements=TrainingRequirements(
                training_needed=True,
                training_plan="ML fundamentals + platform certification",
                affected_roles=["Data Analyst", "Software Engineer", "Product Manager"],
                affected_headcount=120,
            ),
        )
        assert init.resource_requirements.total_fte == 45.0
        assert len(init.resource_requirements.key_skill_gaps) == 3
        assert len(init.resource_allocation) == 2
        assert init.vendor_engagement[0].spend == 2_500_000
        assert init.technology_requirements[0].new_or_existing == "New — To Be Procured"
        assert init.training_requirements.affected_headcount == 120

    def test_typed_impact_edges(self) -> None:
        """Group 8: Dependencies & Relationships — typed impact edges."""
        init = Initiative(
            name="Digital Transformation",
            impacts_capabilities=[
                ImpactsCapability(
                    capability_id="BC-00010",
                    impact_type="Transforms",
                    impact_description="Digitizes end-to-end customer journey",
                )
            ],
            impacts_org_units=[ImpactsOrgUnit(org_unit_id="OU-00003", impact_type="Restructures")],
            impacts_roles=[ImpactsRole(role_id="R-00015", impact_type="Changes Responsibilities")],
            impacts_locations=[ImpactsLocation(site_id="SITE-00020", impact_type="Consolidates")],
            impacts_systems=[
                ImpactsSystem(system_id="SYS-00042", impact_type="Decommissions"),
                ImpactsSystem(system_id="SYS-00099", impact_type="Implements New"),
            ],
            impacts_data=[ImpactsData(data_asset_id="DA-00030", impact_type="Migrates")],
            impacts_products=[ImpactsProduct(product_id="PRD-00005", impact_type="Enhances")],
            impacts_customers=[ImpactsCustomer(customer_id="CUST-00100", impact_type="Migrates")],
            impacts_vendors=[
                ImpactsVendor(vendor_id="V-00010", impact_type="Transitions Away From")
            ],
            related_initiatives=[
                RelatedInitiative(
                    initiative_id="SI-00005",
                    relationship_type="Depends On",
                ),
                RelatedInitiative(
                    initiative_id="SI-00015",
                    relationship_type="Complementary",
                ),
            ],
        )
        assert len(init.impacts_capabilities) == 1
        assert init.impacts_capabilities[0].impact_type == "Transforms"
        assert init.impacts_org_units[0].impact_type == "Restructures"
        assert init.impacts_roles[0].impact_type == "Changes Responsibilities"
        assert init.impacts_locations[0].impact_type == "Consolidates"
        assert len(init.impacts_systems) == 2
        assert init.impacts_data[0].impact_type == "Migrates"
        assert init.impacts_products[0].impact_type == "Enhances"
        assert init.impacts_customers[0].impact_type == "Migrates"
        assert init.impacts_vendors[0].impact_type == "Transitions Away From"
        assert len(init.related_initiatives) == 2

    def test_json_roundtrip(self) -> None:
        """Initiative survives JSON serialization/deserialization."""
        init = Initiative(
            name="Test Roundtrip Initiative",
            initiative_id="SI-99999",
            initiative_tier="Project",
            initiative_type="Technology Migration / Modernization",
            current_status="In Progress",
            total_budget=TotalBudget(approved_budget=1_000_000, budget_type="Capital"),
            key_milestones=[
                KeyMilestone(
                    milestone_name="Go-Live",
                    planned_date="2026-06-01",
                    status="Not Started",
                    milestone_type="Go-Live",
                )
            ],
            impacts_systems=[ImpactsSystem(system_id="SYS-001", impact_type="Migrates")],
        )
        data = json.loads(init.model_dump_json())
        restored = Initiative(**data)
        assert restored.initiative_id == "SI-99999"
        assert restored.total_budget.approved_budget == 1_000_000
        assert restored.key_milestones[0].milestone_name == "Go-Live"
        assert restored.impacts_systems[0].impact_type == "Migrates"

    def test_any_entity_roundtrip(self) -> None:
        """Initiative can be parsed through the AnyEntity discriminated union."""
        init = Initiative(
            name="AnyEntity Test",
            initiative_tier="Workstream",
            current_status="Proposed",
        )
        raw = json.loads(init.model_dump_json())
        adapter = TypeAdapter(AnyEntity)
        parsed = adapter.validate_python(raw)
        assert isinstance(parsed, Initiative)
        assert parsed.initiative_tier == "Workstream"
        assert parsed.current_status == "Proposed"

    def test_defaults(self) -> None:
        """All optional fields default correctly."""
        init = Initiative(name="Defaults Test")
        assert init.initiative_id == ""
        assert init.initiative_tier == ""
        assert init.initiative_type == ""
        assert init.initiative_category == ""
        assert init.parent_initiative == ""
        assert init.child_initiatives == []
        assert init.strategic_objectives == []
        assert init.business_case_summary is None
        assert init.strategic_priority == ""
        assert init.success_criteria == []
        assert init.current_status == ""
        assert init.planned_start_date == ""
        assert init.planned_end_date == ""
        assert init.schedule_variance is None
        assert init.key_milestones == []
        assert init.total_budget is None
        assert init.budget_breakdown == []
        assert init.executive_sponsor == ""
        assert init.steering_committee == []
        assert init.initiative_risk_profile is None
        assert init.active_risks == []
        assert init.resource_requirements is None
        assert init.vendor_engagement == []
        assert init.impacts_capabilities == []
        assert init.impacts_systems == []
        assert init.related_initiatives == []
        assert init.temporal_and_versioning is not None
        assert init.provenance_and_confidence is not None

    def test_hierarchy_parent_child(self) -> None:
        """Initiative hierarchy through parent/child references."""
        portfolio = Initiative(
            name="Digital Portfolio",
            initiative_id="SI-00001",
            initiative_tier="Portfolio",
            child_initiatives=["SI-00010", "SI-00011"],
        )
        program = Initiative(
            name="Cloud Program",
            initiative_id="SI-00010",
            initiative_tier="Program",
            parent_initiative="SI-00001",
            child_initiatives=["SI-00100", "SI-00101"],
        )
        project = Initiative(
            name="AWS Migration",
            initiative_id="SI-00100",
            initiative_tier="Project",
            parent_initiative="SI-00010",
        )
        assert portfolio.initiative_tier == "Portfolio"
        assert program.parent_initiative == "SI-00001"
        assert project.parent_initiative == "SI-00010"
        assert "SI-00010" in portfolio.child_initiatives

    def test_full_enterprise_initiative(self) -> None:
        """Full enterprise initiative with attributes from all groups."""
        init = Initiative(
            name="Enterprise Data Platform Modernization",
            initiative_id="SI-00042",
            initiative_tier="Program",
            initiative_type="Digital Transformation",
            initiative_category="Strategic",
            origin="Strategic Planning",
            strategic_priority="Must Do",
            business_case_summary=BusinessCaseSummary(
                expected_costs=12_000_000,
                roi_estimate_pct=180.0,
            ),
            current_status="In Progress",
            phase="Execution",
            planned_start_date="2025-01-15",
            planned_end_date="2026-06-30",
            total_budget=TotalBudget(approved_budget=12_000_000, budget_type="Mixed"),
            executive_sponsor="CTO",
            initiative_lead="VP Data Engineering",
            owning_org_unit="OU-00005",
            initiative_risk_profile=InitiativeRiskProfile(overall_risk="Medium"),
            resource_requirements=ResourceRequirements(total_fte=60.0),
            impacts_systems=[
                ImpactsSystem(system_id="SYS-001", impact_type="Decommissions"),
                ImpactsSystem(system_id="SYS-002", impact_type="Implements New"),
            ],
            impacts_data=[
                ImpactsData(data_asset_id="DA-001", impact_type="Migrates"),
            ],
        )
        assert init.initiative_id == "SI-00042"
        assert init.strategic_priority == "Must Do"
        assert init.total_budget.approved_budget == 12_000_000
        assert init.initiative_risk_profile.overall_risk == "Medium"
        assert init.resource_requirements.total_fte == 60.0
        assert len(init.impacts_systems) == 2
