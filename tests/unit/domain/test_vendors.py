"""Tests for L10: Vendors & Partners entity types.

Covers extended Vendor entity and new Contract entity with attribute group
coverage, sub-model instantiation, and JSON serialization roundtrip.
"""

from pydantic import TypeAdapter

from domain.base import EntityType
from domain.entities import AnyEntity
from domain.entities.contract import (
    Amendment,
    AssociatedContract,
    Contract,
    DataHandlingProvisions,
    EarlyTerminationPenalty,
    GoverningLaw,
    InsuranceRequirements,
    IPProvisions,
    LiabilityCaps,
    SLAEntry,
)
from domain.entities.vendor import (
    BusinessContinuity,
    CoInvestment,
    CostTrend,
    CybersecurityAssessment,
    DataProcessing,
    DeliveryPerformance,
    DiversityClassification,
    EscalationEvent,
    Exclusivity,
    FinancialStability,
    ForceMajeureExposure,
    GeographicConcentration,
    GovernanceCadence,
    IncidentHistory,
    InnovationContribution,
    JointGovernance,
    PerformanceDimension,
    PerformanceScorecard,
    ProvidesSystem,
    SharedIP,
    SLACompliance,
    SpendByBU,
    SpendByCategory,
    SpendConcentrationRisk,
    Substitutability,
    SuppliesProduct,
    TotalAnnualSpend,
    Vendor,
    VendorComplianceCertification,
    VendorDependency,
    VendorInsuranceCoverage,
    VendorLocation,
    VendorPaymentTerms,
    VendorQualityMetrics,
    VendorRiskProfile,
    VendorSanctionsScreening,
    VendorSize,
)

_any_entity_adapter = TypeAdapter(AnyEntity)


# ===========================================================================
# Vendor tests (extended)
# ===========================================================================


class TestVendorExtended:
    def test_backward_compat(self):
        """v0.1 fields still work."""
        v = Vendor(
            name="Old-Style Vendor",
            vendor_type="saas",
            contract_value=50000,
            risk_tier="high",
            has_data_access=True,
            data_classification_access=["confidential"],
            compliance_certifications=["SOC2"],
            contract_expiry="2025-12-31",
            primary_contact="John Doe",
            sla_uptime=99.9,
        )
        assert v.entity_type == EntityType.VENDOR
        assert v.vendor_type == "saas"
        assert v.risk_tier == "high"
        assert v.sla_uptime == 99.9

    def test_identity_classification(self):
        v = Vendor(
            name="TechCorp Solutions",
            vendor_id="VN-00001",
            vendor_name_common="TechCorp",
            vendor_type="Strategic Partner",
            vendor_category="Technology — Cloud / SaaS",
            vendor_subcategory="Cloud Infrastructure",
            headquarters_location="GEO-NA",
            vendor_locations=[
                VendorLocation(
                    location_id="ST-SFO",
                    location_name="San Francisco HQ",
                    location_role="Headquarters",
                )
            ],
            vendor_size=VendorSize(
                annual_revenue=15_000_000_000,
                employee_count=50000,
            ),
            ownership_structure="Public",
            origin="Organic — Procurement Sourced",
            diversity_classification=DiversityClassification(
                certified=False,
            ),
            parent_company="",
            subsidiaries=["VN-TC-EU", "VN-TC-APAC"],
        )
        assert v.vendor_id == "VN-00001"
        assert v.vendor_category == "Technology — Cloud / SaaS"
        assert v.vendor_size.employee_count == 50000
        assert len(v.subsidiaries) == 2

    def test_relationship_engagement(self):
        v = Vendor(
            name="Consulting Partners",
            relationship_status="Active",
            relationship_start_date="2018-06-01",
            relationship_tenure_years=6.5,
            strategic_importance="Critical",
            engagement_model="Strategic Partnership",
            vendor_manager="RL-VM-001",
            executive_sponsor="RL-EVP-002",
            governance_cadence=GovernanceCadence(
                review_frequency="Quarterly",
                last_review_date="2024-09-15",
                next_review_date="2024-12-15",
                review_format="Executive Business Review",
            ),
        )
        assert v.strategic_importance == "Critical"
        assert v.governance_cadence.review_format == "Executive Business Review"

    def test_financial_profile(self):
        v = Vendor(
            name="Component Supplier",
            total_annual_spend=TotalAnnualSpend(
                amount=12_000_000,
                fiscal_year="2024",
                yoy_change_pct=8.5,
            ),
            spend_by_category=[
                SpendByCategory(category="Raw Materials", amount=8_000_000),
                SpendByCategory(category="Logistics", amount=4_000_000),
            ],
            spend_by_business_unit=[
                SpendByBU(
                    org_unit_id="OU-MFG",
                    org_unit_name="Manufacturing",
                    amount=10_000_000,
                )
            ],
            spend_concentration_risk=SpendConcentrationRisk(
                pct_of_category_spend=35.0,
                concentration_tier="Critical",
            ),
            payment_terms=VendorPaymentTerms(
                standard_terms="Net 45",
                actual_terms="Net 60",
                average_days_to_pay=55.0,
            ),
            cost_trend=CostTrend(
                three_yr_cagr_pct=5.2,
                trend_driver="Raw material price increases",
            ),
        )
        assert v.total_annual_spend.amount == 12_000_000
        assert len(v.spend_by_category) == 2
        assert v.spend_concentration_risk.concentration_tier == "Critical"

    def test_performance_quality(self):
        v = Vendor(
            name="Cloud Provider",
            performance_scorecard=PerformanceScorecard(
                overall_score=4.2,
                scale="1–5",
                methodology="Weighted Composite",
                last_assessed="2024-10-01",
            ),
            performance_dimensions=[
                PerformanceDimension(dimension="Quality", score=4.5, weight=0.3),
                PerformanceDimension(dimension="Responsiveness", score=3.8, weight=0.2),
            ],
            sla_compliance=SLACompliance(
                sla_count=15,
                slas_met=14,
                sla_compliance_pct=93.3,
                sla_breaches_12m=3,
            ),
            quality_metrics=VendorQualityMetrics(
                defect_rate=0.001,
                quality_trend="Improving",
            ),
            delivery_performance=DeliveryPerformance(
                on_time_delivery_pct=97.5,
                lead_time_average="3 weeks",
                lead_time_trend="Stable",
            ),
            incident_history=IncidentHistory(
                p1_count_12m=1,
                p2_count_12m=5,
                mttr_hours=2.5,
            ),
            escalation_history=[
                EscalationEvent(
                    escalation_date="2024-03-15",
                    reason="SLA breach on response time",
                    resolution="Process improvement implemented",
                    days_to_resolve=14,
                )
            ],
            innovation_contribution=InnovationContribution(
                contributes_innovation=True,
                examples=["Joint AI/ML research", "Co-developed API gateway"],
                joint_patents=2,
                co_development_active=True,
            ),
        )
        assert v.performance_scorecard.overall_score == 4.2
        assert len(v.performance_dimensions) == 2
        assert v.sla_compliance.sla_compliance_pct == 93.3
        assert v.delivery_performance.on_time_delivery_pct == 97.5
        assert v.innovation_contribution.joint_patents == 2

    def test_risk_compliance(self):
        v = Vendor(
            name="Data Processing Vendor",
            vendor_risk_profile=VendorRiskProfile(
                overall_risk="Medium",
                financial_risk="Low",
                cybersecurity_risk="Medium",
                geopolitical_risk="Low",
            ),
            financial_stability=FinancialStability(
                credit_rating="BBB+",
                credit_agency="S&P",
                financial_health_indicator="Stable",
                bankruptcy_risk="Low",
            ),
            cybersecurity_assessment=CybersecurityAssessment(
                assessed=True,
                assessment_date="2024-08-01",
                assessment_methodology="SIG Full",
                risk_rating="Medium",
                open_findings_count=3,
            ),
            business_continuity=BusinessContinuity(
                bcp_exists=True,
                bcp_tested=True,
                rto="4 hours",
                rpo="1 hour",
                geographic_redundancy=True,
                disaster_recovery_plan=True,
            ),
            vendor_compliance_certifications=[
                VendorComplianceCertification(
                    certification="ISO 27001",
                    issuing_body="BSI",
                    status="Active",
                    expiration_date="2026-03-15",
                    scope="Cloud services",
                )
            ],
            sanctions_screening=VendorSanctionsScreening(
                screened=True,
                result="Clear",
                screening_lists=["OFAC SDN", "EU Consolidated"],
            ),
            data_processing=DataProcessing(
                processes_our_data=True,
                data_classification_handled=["Confidential", "Internal"],
                data_processing_agreement=True,
                dpa_reference="DPA-VN-2024-001",
                sub_processors_disclosed=True,
                sub_processor_count=3,
            ),
            insurance_coverage=VendorInsuranceCoverage(
                cyber_insurance=True,
                cyber_insurance_limit=25_000_000,
                general_liability=True,
                professional_liability=True,
            ),
        )
        assert v.vendor_risk_profile.cybersecurity_risk == "Medium"
        assert v.financial_stability.credit_rating == "BBB+"
        assert v.cybersecurity_assessment.open_findings_count == 3
        assert v.business_continuity.rto == "4 hours"
        assert v.data_processing.sub_processor_count == 3
        assert v.insurance_coverage.cyber_insurance_limit == 25_000_000

    def test_supply_chain(self):
        v = Vendor(
            name="Critical Supplier",
            supply_chain_role="Tier 1",
            substitutability=Substitutability(
                alternative_vendor_count=2,
                switching_cost=5_000_000,
                switching_time="12 months",
                switching_complexity="Complex",
            ),
            geographic_concentration=GeographicConcentration(
                primary_delivery_location="GEO-APAC",
                backup_locations=["GEO-EMEA"],
                single_geography_risk=True,
                risk_description="90% of production in single region",
            ),
            dependency_on_vendor=[
                VendorDependency(
                    product_or_service="Custom ASIC chips",
                    dependency_strength="Critical",
                    impact_if_unavailable="Production halt within 30 days",
                )
            ],
            force_majeure_exposure=ForceMajeureExposure(
                natural_disaster_risk="High",
                geopolitical_risk="Medium",
                pandemic_risk="Medium",
                mitigation_plan="Dual-source qualification in progress",
            ),
        )
        assert v.supply_chain_role == "Tier 1"
        assert v.substitutability.switching_complexity == "Complex"
        assert v.geographic_concentration.single_geography_risk is True
        assert v.force_majeure_exposure.natural_disaster_risk == "High"

    def test_partnership_attributes(self):
        v = Vendor(
            name="Strategic Alliance Partner",
            partnership_structure="Strategic Alliance",
            joint_governance=JointGovernance(
                governance_body="Joint Steering Committee",
                meeting_frequency="Monthly",
                escalation_path="CTO → CEO",
            ),
            shared_ip=SharedIP(
                ip_exists=True,
                ip_ownership_model="Joint Ownership",
                ip_reference="IP-JOINT-2024-001",
            ),
            co_investment=CoInvestment(
                joint_investment_exists=True,
                investment_amount=10_000_000,
                investment_purpose="Joint R&D lab",
            ),
            exclusivity=Exclusivity(
                exclusivity_exists=True,
                exclusivity_scope="North America",
                exclusivity_term="3 years",
            ),
        )
        assert v.partnership_structure == "Strategic Alliance"
        assert v.shared_ip.ip_ownership_model == "Joint Ownership"
        assert v.co_investment.investment_amount == 10_000_000
        assert v.exclusivity.exclusivity_scope == "North America"

    def test_relationships(self):
        v = Vendor(
            name="Multi-Service Vendor",
            holds_contracts=["CT-MSA-001", "CT-SOW-001"],
            supplies_products=[SuppliesProduct(product_id="PR-WIDGET", supply_type="Component")],
            managed_by_org_unit="OU-PROCUREMENT",
            provides_systems=[
                ProvidesSystem(
                    system_id="SYS-CRM",
                    relationship_type="Software Vendor",
                )
            ],
        )
        assert len(v.holds_contracts) == 2
        assert v.supplies_products[0].supply_type == "Component"
        assert v.provides_systems[0].relationship_type == "Software Vendor"

    def test_json_roundtrip(self):
        v = Vendor(
            name="Test Vendor",
            vendor_id="VN-99999",
            vendor_type="Preferred Vendor",
            strategic_importance="High",
        )
        data = v.model_dump(mode="json")
        restored = Vendor.model_validate(data)
        assert restored.vendor_id == "VN-99999"
        assert restored.strategic_importance == "High"

    def test_any_entity_roundtrip(self):
        v = Vendor(name="AnyEntity Test", vendor_id="VN-AE-001")
        data = v.model_dump(mode="json")
        restored = _any_entity_adapter.validate_python(data)
        assert isinstance(restored, Vendor)
        assert restored.vendor_id == "VN-AE-001"


# ===========================================================================
# Contract tests
# ===========================================================================


class TestContract:
    def test_minimal_construction(self):
        c = Contract(name="Cloud Services MSA")
        assert c.entity_type == EntityType.CONTRACT
        assert c.name == "Cloud Services MSA"
        assert c.contract_id == ""

    def test_identity_and_parties(self):
        c = Contract(
            name="Enterprise SaaS Agreement",
            contract_id="CT-00001",
            contract_type="SaaS Subscription",
            contract_status="Active",
            vendor_id="VN-TECHCORP",
            contract_owner="RL-BIZ-OWNER",
            legal_owner="RL-LEGAL-001",
            procurement_owner="RL-PROC-001",
            contracting_org_unit="OU-IT",
        )
        assert c.contract_id == "CT-00001"
        assert c.contract_type == "SaaS Subscription"
        assert c.vendor_id == "VN-TECHCORP"

    def test_financial_terms(self):
        c = Contract(
            name="Supply Agreement",
            total_contract_value=15_000_000,
            annual_value=5_000_000,
            currency="USD",
            payment_schedule="Quarterly",
            payment_terms="Net 30",
        )
        assert c.total_contract_value == 15_000_000
        assert c.annual_value == 5_000_000
        assert c.payment_schedule == "Quarterly"

    def test_duration_renewal(self):
        c = Contract(
            name="Multi-Year MSA",
            start_date="2022-01-01",
            end_date="2025-12-31",
            initial_term="36 months",
            current_term="Year 3 of 3",
            auto_renewal=True,
            renewal_term="12 months",
            notice_period_days=90,
            opt_out_deadline="2025-09-30",
            renewal_cap_pct=5.0,
        )
        assert c.auto_renewal is True
        assert c.notice_period_days == 90
        assert c.renewal_cap_pct == 5.0

    def test_termination(self):
        c = Contract(
            name="Consulting SOW",
            termination_for_convenience=True,
            termination_notice_days=30,
            early_termination_penalty=EarlyTerminationPenalty(
                penalty_exists=True,
                penalty_description="50% of remaining contract value",
                penalty_amount=2_500_000,
            ),
        )
        assert c.termination_for_convenience is True
        assert c.early_termination_penalty.penalty_amount == 2_500_000

    def test_slas(self):
        c = Contract(
            name="Managed Services",
            sla_summary=[
                SLAEntry(
                    sla_name="Uptime",
                    metric="Availability",
                    target="99.95%",
                    measurement_method="Monthly rolling",
                    penalty_for_breach="5% credit per 0.1% below target",
                ),
                SLAEntry(
                    sla_name="Response Time",
                    metric="P1 response",
                    target="< 15 minutes",
                ),
            ],
        )
        assert len(c.sla_summary) == 2
        assert c.sla_summary[0].target == "99.95%"

    def test_key_provisions(self):
        c = Contract(
            name="Data Processing Agreement",
            data_handling_provisions=DataHandlingProvisions(
                data_classification=["Confidential", "PII"],
                data_return_clause=True,
                data_destruction_clause=True,
                breach_notification_hours=72,
                sub_processor_approval_required=True,
            ),
            insurance_requirements=InsuranceRequirements(
                cyber_insurance_required=True,
                minimum_coverage=10_000_000,
                verified=True,
            ),
            liability_caps=LiabilityCaps(
                liability_cap=50_000_000,
                liability_type="Direct Damages Only",
                unlimited_liability_carve_outs=[
                    "Data breach",
                    "IP infringement",
                    "Confidentiality",
                ],
            ),
            ip_provisions=IPProvisions(
                ip_ownership="Vendor Retains",
                work_product_ownership="Enterprise Owns",
            ),
            governing_law=GoverningLaw(
                jurisdiction="State of Delaware, USA",
                dispute_resolution_mechanism="Arbitration",
            ),
        )
        assert c.data_handling_provisions.breach_notification_hours == 72
        assert c.insurance_requirements.minimum_coverage == 10_000_000
        assert len(c.liability_caps.unlimited_liability_carve_outs) == 3
        assert c.governing_law.dispute_resolution_mechanism == "Arbitration"

    def test_amendments_related(self):
        c = Contract(
            name="Amended MSA",
            amendments=[
                Amendment(
                    amendment_id="AMD-001",
                    amendment_date="2024-06-01",
                    description="Added cloud migration services",
                    financial_impact=500_000,
                )
            ],
            associated_contracts=[
                AssociatedContract(
                    contract_id="CT-NDA-001",
                    relationship="Related NDA",
                ),
                AssociatedContract(
                    contract_id="CT-DPA-001",
                    relationship="Related DPA",
                ),
            ],
        )
        assert len(c.amendments) == 1
        assert c.amendments[0].financial_impact == 500_000
        assert len(c.associated_contracts) == 2

    def test_relationships(self):
        c = Contract(
            name="Platform License",
            with_vendor="VN-PLATFORM",
            covers_systems=["SYS-ERP", "SYS-CRM"],
            covers_data=["DA-CUSTOMER", "DA-ORDERS"],
            covers_products=["PR-PLATFORM"],
        )
        assert c.with_vendor == "VN-PLATFORM"
        assert len(c.covers_systems) == 2

    def test_json_roundtrip(self):
        c = Contract(
            name="Test Contract",
            contract_id="CT-99999",
            contract_type="Master Services Agreement",
            contract_status="Active",
        )
        data = c.model_dump(mode="json")
        restored = Contract.model_validate(data)
        assert restored.contract_id == "CT-99999"

    def test_any_entity_roundtrip(self):
        c = Contract(name="AnyEntity Test", contract_id="CT-AE-001")
        data = c.model_dump(mode="json")
        restored = _any_entity_adapter.validate_python(data)
        assert isinstance(restored, Contract)
        assert restored.contract_id == "CT-AE-001"
