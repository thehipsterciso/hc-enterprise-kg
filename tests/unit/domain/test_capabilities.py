"""Tests for L06: Business Capabilities entity type.

Covers BusinessCapability entity with full attribute group coverage,
sub-model instantiation, and JSON serialization roundtrip.
"""

from pydantic import TypeAdapter

from domain.base import EntityType
from domain.entities import AnyEntity
from domain.entities.business_capability import (
    BusinessCapability,
    BusinessImpactIfDegraded,
    BusinessModelRelevance,
    CapabilityDependency,
    CapabilityInterface,
    CapabilityLocalName,
    CapabilityTaxonomyLineage,
    CapacityUtilization,
    ControlReference,
    CostBreakdownItem,
    CostToOperate,
    DataSupport,
    FundingAmount,
    HeadcountAllocation,
    KPICurrentValue,
    KPIDefinition,
    MaturityByBusinessUnit,
    MaturityByRegion,
    MaturityDimension,
    MaturityTarget,
    RACIMatrix,
    RevenueAttribution,
    RiskFactor,
    SystemSupport,
    ValueStreamAlignment,
    VendorDependency,
)

_any_entity_adapter = TypeAdapter(AnyEntity)


# ===========================================================================
# BusinessCapability tests
# ===========================================================================


class TestBusinessCapability:
    def test_minimal_construction(self):
        cap = BusinessCapability(name="Risk Management")
        assert cap.entity_type == EntityType.BUSINESS_CAPABILITY
        assert cap.name == "Risk Management"
        assert cap.capability_id == ""

    def test_identity_classification(self):
        cap = BusinessCapability(
            name="Enterprise Risk Management",
            capability_id="BC-01.03.00",
            capability_description_extended="Includes: risk identification. Excludes: insurance.",
            tier="Strategic",
            tier_justification="Top-level risk capability",
            capability_type="Core Non-Differentiating",
            functional_domain="Risk & Compliance",
            functional_domain_secondary=["Strategy & Governance"],
            capability_name_local=[
                CapabilityLocalName(language_code="de", name="Risikomanagement", locale="DE")
            ],
            value_stream_alignment=[
                ValueStreamAlignment(
                    value_stream_id="VS-001",
                    value_stream_name="Risk-to-Mitigation",
                    contribution_type="Primary Driver",
                )
            ],
            business_model_relevance=[
                BusinessModelRelevance(
                    business_model_segment="Platform/Marketplace",
                    relevance_type="Supports Model",
                )
            ],
            taxonomy_lineage=[
                CapabilityTaxonomyLineage(
                    framework="APQC PCF",
                    framework_element_id="APQC 10.0 - Manage Enterprise Risk",
                    mapping_confidence="Exact Match",
                )
            ],
            origin="Organic",
        )
        assert cap.capability_id == "BC-01.03.00"
        assert cap.tier == "Strategic"
        assert len(cap.taxonomy_lineage) == 1
        assert cap.value_stream_alignment[0].contribution_type == "Primary Driver"

    def test_maturity_state(self):
        cap = BusinessCapability(
            name="Data Governance",
            maturity_model_reference="DCAM",
            maturity_composite_score=3.5,
            maturity_dimensions=[
                MaturityDimension(
                    dimension="Process Maturity",
                    score=4.0,
                    evidence_reference="DOC-MAT-001",
                    assessed_date="2024-06-01",
                ),
                MaturityDimension(
                    dimension="Data Quality",
                    score=3.0,
                    assessed_date="2024-06-01",
                ),
            ],
            maturity_by_region=[
                MaturityByRegion(
                    region_id="REG-NA",
                    region_name="North America",
                    maturity_composite_score=4.0,
                    assessed_date="2024-06-01",
                )
            ],
            maturity_by_business_unit=[
                MaturityByBusinessUnit(
                    business_unit_id="OU-FIN",
                    business_unit_name="Finance",
                    maturity_composite_score=3.0,
                )
            ],
            maturity_target=MaturityTarget(
                target_composite_score=4.5,
                target_date="2025-12-31",
                target_rationale="Board mandate",
            ),
            maturity_trajectory="Improving",
            lifecycle_state="Active",
            lifecycle_state_rationale="Fully operational across all BUs",
            lifecycle_transition_date="2022-01-15",
            lifecycle_next_state="Mature",
            lifecycle_next_state_target_date="2025-06-30",
        )
        assert cap.maturity_composite_score == 3.5
        assert len(cap.maturity_dimensions) == 2
        assert cap.maturity_by_region[0].maturity_composite_score == 4.0
        assert cap.maturity_target.target_composite_score == 4.5
        assert cap.lifecycle_state == "Active"

    def test_performance_measurement(self):
        cap = BusinessCapability(
            name="Incident Response",
            performance_status="Meeting",
            kpi_definitions=[
                KPIDefinition(
                    kpi_id="KPI-IR-001",
                    kpi_name="Mean Time to Containment",
                    kpi_description="Average time to contain a security incident",
                    measurement_frequency="Monthly",
                    unit_of_measure="hours",
                    target_value=4.0,
                    threshold_critical=24.0,
                    threshold_warning=8.0,
                )
            ],
            kpi_current_values=[
                KPICurrentValue(
                    kpi_id="KPI-IR-001",
                    current_value=3.5,
                    measurement_date="2024-11-01",
                    trend_direction="Improving",
                )
            ],
            cost_to_operate=CostToOperate(
                annual_cost=2500000,
                currency="USD",
                cost_type="Fully Loaded",
                cost_breakdown=[
                    CostBreakdownItem(category="Personnel", amount=1800000),
                    CostBreakdownItem(category="Technology", amount=500000),
                    CostBreakdownItem(category="Training", amount=200000),
                ],
            ),
            revenue_attribution=RevenueAttribution(
                attribution_type="Cost Avoidance",
                estimated_revenue_impact=15000000,
                confidence_level="Medium — Model Derived",
            ),
            capacity_utilization=CapacityUtilization(
                current_utilization_pct=65,
                peak_utilization_pct=95,
                measurement_basis="Incidents per month",
            ),
        )
        assert cap.performance_status == "Meeting"
        assert cap.kpi_definitions[0].target_value == 4.0
        assert cap.kpi_current_values[0].current_value == 3.5
        assert cap.cost_to_operate.annual_cost == 2500000
        assert len(cap.cost_to_operate.cost_breakdown) == 3
        assert cap.revenue_attribution.estimated_revenue_impact == 15000000

    def test_strategic_importance(self):
        cap = BusinessCapability(
            name="Customer Onboarding",
            business_criticality="Business Critical",
            criticality_justification="Direct revenue impact within 48 hours if degraded",
            business_impact_if_degraded=BusinessImpactIfDegraded(
                impact_description="New customer acquisition halts",
                estimated_financial_impact_per_day=500000,
                affected_value_streams=["VS-SALES", "VS-REV"],
                affected_customer_segments=["SEG-ENTERPRISE"],
                recovery_time_expectation="4 hours",
            ),
            differentiation_level="Differentiating",
            differentiation_evidence="Proprietary ML-driven onboarding reduces time by 60%",
            sourcing_suitability="Must Own",
            strategic_risk_if_lost="Loss of competitive advantage in enterprise segment",
        )
        assert cap.business_criticality == "Business Critical"
        assert cap.business_impact_if_degraded.estimated_financial_impact_per_day == 500000
        assert cap.differentiation_level == "Differentiating"
        assert cap.sourcing_suitability == "Must Own"

    def test_ownership_accountability(self):
        cap = BusinessCapability(
            name="Financial Reporting",
            executive_sponsor="RL-CFO",
            capability_owner="RL-CONTROLLER",
            governance_body="Finance Steering Committee",
            governance_cadence="Monthly",
            raci_matrix=RACIMatrix(
                responsible=["RL-FIN-ANALYST"],
                accountable=["RL-CONTROLLER"],
                consulted=["RL-AUDIT"],
                informed=["RL-CFO", "RL-CEO"],
            ),
            shared_service_model="Shared Service",
            funding_model="Centrally Funded",
            funding_amount=FundingAmount(
                annual_budget=5000000, currency="USD", fiscal_year="2024"
            ),
            headcount_allocation=HeadcountAllocation(
                fte_count=25, contractor_count=5, vendor_fte_count=3, total=33
            ),
        )
        assert cap.executive_sponsor == "RL-CFO"
        assert cap.raci_matrix.accountable == ["RL-CONTROLLER"]
        assert cap.funding_amount.annual_budget == 5000000
        assert cap.headcount_allocation.total == 33

    def test_risk_compliance(self):
        cap = BusinessCapability(
            name="Payment Processing",
            risk_exposure_inherent="High",
            risk_exposure_residual="Medium",
            risk_factors=[
                RiskFactor(
                    risk_id="RSK-PP-001",
                    risk_description="Fraud risk from card-not-present transactions",
                    risk_category="Financial",
                    likelihood="Likely",
                    impact="Major",
                    velocity="Sudden",
                )
            ],
            control_coverage="Substantial",
            control_references=[
                ControlReference(
                    control_id="CTL-PCI-001",
                    control_framework="Custom",
                    control_description="PCI DSS v4.0 compliance controls",
                    control_effectiveness="Effective",
                    last_tested_date="2024-09-15",
                )
            ],
            resilience_tier="Gold",
            rto=4.0,
            rpo=1.0,
        )
        assert cap.risk_exposure_inherent == "High"
        assert cap.risk_exposure_residual == "Medium"
        assert len(cap.risk_factors) == 1
        assert cap.risk_factors[0].velocity == "Sudden"
        assert cap.resilience_tier == "Gold"
        assert cap.rto == 4.0

    def test_dependencies_relationships(self):
        cap = BusinessCapability(
            name="Identity & Access Management",
            parent_capability="BC-07.00.00",
            child_capabilities=["BC-07.01.00", "BC-07.02.00"],
            depends_on_capabilities=[
                CapabilityDependency(
                    capability_id="BC-07.03.00",
                    dependency_type="Requires",
                    dependency_strength="Hard",
                )
            ],
            enables_capabilities=["BC-01.00.00", "BC-02.00.00"],
            interfaces_with=[
                CapabilityInterface(
                    capability_id="BC-08.01.00",
                    interface_type="Synchronous",
                    data_exchange_description="AuthN/AuthZ tokens",
                )
            ],
            supported_by_systems=[
                SystemSupport(
                    system_id="SYS-OKTA",
                    support_type="Primary Platform",
                )
            ],
            supported_by_data=[
                DataSupport(
                    data_asset_id="DA-IDENTITIES",
                    data_relationship_type="Primary Data Source",
                )
            ],
            delivered_through_products=["PROD-SSO"],
            owned_by_organization=["OU-IT-SEC"],
            staffed_by=["RL-IAM-ENG", "RL-IAM-ADMIN"],
            governed_by=["REG-SOX"],
            realized_by_initiatives=["INIT-ZT"],
            depends_on_vendors=[
                VendorDependency(
                    vendor_id="VENDOR-OKTA",
                    dependency_criticality="Critical — No Alternative",
                )
            ],
            serves_customers=["SEG-INTERNAL"],
        )
        assert cap.parent_capability == "BC-07.00.00"
        assert len(cap.child_capabilities) == 2
        assert cap.depends_on_capabilities[0].dependency_strength == "Hard"
        assert cap.supported_by_systems[0].support_type == "Primary Platform"
        assert cap.depends_on_vendors[0].dependency_criticality == "Critical — No Alternative"

    def test_json_roundtrip(self):
        cap = BusinessCapability(
            name="Cyber Threat Intelligence",
            capability_id="BC-01.05.01",
            tier="Component",
            capability_type="Core Differentiating",
            functional_domain="Risk & Compliance",
            maturity_composite_score=3.0,
            lifecycle_state="Active",
            performance_status="Meeting",
            business_criticality="Mission Critical",
            risk_exposure_inherent="High",
            risk_exposure_residual="Medium",
        )
        data = cap.model_dump(mode="json")
        restored = BusinessCapability.model_validate(data)
        assert restored.capability_id == "BC-01.05.01"
        assert restored.maturity_composite_score == 3.0
        assert restored.business_criticality == "Mission Critical"

    def test_any_entity_roundtrip(self):
        cap = BusinessCapability(
            name="AnyEntity Test Capability",
            capability_id="BC-99.99.99",
        )
        data = cap.model_dump(mode="json")
        restored = _any_entity_adapter.validate_python(data)
        assert isinstance(restored, BusinessCapability)
        assert restored.capability_id == "BC-99.99.99"

    def test_defaults_all_optional(self):
        """All fields should have defaults — only name is required (from BaseEntity)."""
        cap = BusinessCapability(name="Minimal")
        assert cap.capability_id == ""
        assert cap.maturity_dimensions == []
        assert cap.kpi_definitions == []
        assert cap.risk_factors == []
        assert cap.depends_on_capabilities == []
        assert cap.cost_to_operate is None
        assert cap.raci_matrix is None
        assert cap.maturity_target is None

    def test_capability_hierarchy(self):
        """Test parent-child decomposition hierarchy."""
        parent = BusinessCapability(
            name="Security Operations",
            capability_id="BC-01.00.00",
            tier="Strategic",
            child_capabilities=["BC-01.01.00", "BC-01.02.00", "BC-01.03.00"],
        )
        child = BusinessCapability(
            name="Vulnerability Management",
            capability_id="BC-01.01.00",
            tier="Business",
            parent_capability="BC-01.00.00",
        )
        assert child.parent_capability == parent.capability_id
        assert child.capability_id in parent.child_capabilities
