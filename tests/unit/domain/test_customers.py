"""Tests for L09: Customers & Markets entity types.

Covers MarketSegment and Customer entities with attribute group
coverage, sub-model instantiation, and JSON serialization roundtrip.
"""

from pydantic import TypeAdapter

from domain.base import EntityType
from domain.entities import AnyEntity
from domain.entities.customer import (
    AccountTeam,
    ActiveProduct,
    BelongsToSegment,
    BuysProduct,
    ContractValue,
    CreditProfile,
    Customer,
    CustomerComplianceCertification,
    CustomerFormerName,
    CustomerIndustryClassification,
    CustomerLocation,
    CustomerRevenueCurrent,
    CustomerRiskProfile,
    CustomerSanctionsScreening,
    CustomerSize,
    Customization,
    DataPrivacyObligations,
    DataSharedWith,
    DeploymentModel,
    ExpansionPotential,
    ExportControlStatus,
    HealthScore,
    HistoricalProduct,
    IntegrationPoint,
    KycStatus,
    PaymentTerms,
    PrimaryContact,
    Profitability,
    RevenueByProduct,
    RevenueConcentrationRisk,
    RevenueLifetime,
    SatisfactionCurrent,
    ServiceAgreement,
    WalletShare,
)
from domain.entities.market_segment import (
    EntryBarrier,
    GrowthRate,
    MarketSegment,
    MarketSizing,
    SegmentCriterion,
    SegmentFinancialSummary,
    SegmentRegulatoryEnvironment,
    ServedByProduct,
    WinRate,
)

_any_entity_adapter = TypeAdapter(AnyEntity)


# ===========================================================================
# MarketSegment tests
# ===========================================================================


class TestMarketSegment:
    def test_minimal_construction(self):
        ms = MarketSegment(name="Financial Services")
        assert ms.entity_type == EntityType.MARKET_SEGMENT
        assert ms.name == "Financial Services"
        assert ms.segment_id == ""

    def test_identity_hierarchy(self):
        ms = MarketSegment(
            name="Enterprise Banking",
            segment_id="MK-00001",
            segment_type="Industry Vertical",
            segment_level="Segment",
            parent_segment="MK-FINSERV",
            child_segments=["MK-RETAIL-BANK", "MK-INVEST-BANK"],
            segment_criteria=[
                SegmentCriterion(
                    criterion_type="Industry Code",
                    criterion_value="NAICS 522110",
                    criterion_description="Commercial banking",
                ),
                SegmentCriterion(
                    criterion_type="Revenue Range",
                    criterion_value="> $1B annual revenue",
                ),
            ],
        )
        assert ms.segment_id == "MK-00001"
        assert ms.segment_level == "Segment"
        assert len(ms.child_segments) == 2
        assert len(ms.segment_criteria) == 2

    def test_market_sizing_performance(self):
        ms = MarketSegment(
            name="Healthcare IT",
            market_sizing=MarketSizing(
                tam=150_000_000_000,
                sam=45_000_000_000,
                som=5_000_000_000,
                currency="USD",
                methodology="Top-Down TAM Analysis",
                as_of_date="2024-06-01",
            ),
            growth_rate=GrowthRate(
                current_yoy_pct=12.5,
                projected_3yr_cagr=15.0,
                growth_driver="Digital health transformation",
            ),
            competitive_intensity="Intense",
            win_rate=WinRate(
                current_pct=35.0,
                trend="Improving",
                measurement_period="Last 12 months",
            ),
            strategic_priority="Primary Target",
            segment_financial_summary=SegmentFinancialSummary(
                annual_revenue=120_000_000,
                customer_count=45,
                average_deal_size=2_600_000,
                fiscal_year="2024",
                revenue_pct_of_enterprise=8.0,
            ),
            regulatory_environment=SegmentRegulatoryEnvironment(
                primary_regulations=["HIPAA", "HITECH", "21 CFR Part 11"],
                compliance_complexity="Very High",
                description="Heavily regulated healthcare data handling",
            ),
            entry_barriers=[
                EntryBarrier(
                    barrier_type="Regulatory Certification",
                    barrier_description="HITRUST CSF certification required",
                    severity="High",
                )
            ],
        )
        assert ms.market_sizing.tam == 150_000_000_000
        assert ms.growth_rate.projected_3yr_cagr == 15.0
        assert ms.competitive_intensity == "Intense"
        assert ms.win_rate.current_pct == 35.0
        assert ms.segment_financial_summary.customer_count == 45
        assert len(ms.regulatory_environment.primary_regulations) == 3
        assert ms.entry_barriers[0].severity == "High"

    def test_relationships(self):
        ms = MarketSegment(
            name="Federal Government",
            contains_customers=["CU-DOD", "CU-DHS", "CU-VA"],
            served_by_products=[
                ServedByProduct(
                    product_id="PR-GOVCLOUD",
                    product_name="GovCloud Platform",
                    revenue_in_segment=50_000_000,
                )
            ],
            managing_org_unit="OU-GOV",
        )
        assert len(ms.contains_customers) == 3
        assert ms.served_by_products[0].revenue_in_segment == 50_000_000

    def test_json_roundtrip(self):
        ms = MarketSegment(
            name="Test Segment",
            segment_id="MK-99999",
            segment_type="Size-Based",
            strategic_priority="Secondary Target",
        )
        data = ms.model_dump(mode="json")
        restored = MarketSegment.model_validate(data)
        assert restored.segment_id == "MK-99999"
        assert restored.strategic_priority == "Secondary Target"

    def test_any_entity_roundtrip(self):
        ms = MarketSegment(name="AnyEntity Test", segment_id="MK-AE-001")
        data = ms.model_dump(mode="json")
        restored = _any_entity_adapter.validate_python(data)
        assert isinstance(restored, MarketSegment)
        assert restored.segment_id == "MK-AE-001"


# ===========================================================================
# Customer tests
# ===========================================================================


class TestCustomer:
    def test_minimal_construction(self):
        c = Customer(name="Acme Corp")
        assert c.entity_type == EntityType.CUSTOMER
        assert c.name == "Acme Corp"
        assert c.customer_id == ""

    def test_identity_classification(self):
        c = Customer(
            name="Global Financial Services Inc.",
            customer_id="CU-00001",
            customer_name_common="GFS",
            customer_name_former=[
                CustomerFormerName(
                    former_name="First National Holdings",
                    from_date="2010-01-01",
                    to_date="2020-06-30",
                    change_reason="Corporate rebrand",
                )
            ],
            customer_type="Enterprise",
            customer_subtype="Tier 1 Bank",
            industry_classification=CustomerIndustryClassification(
                classification_standard="NAICS",
                code="522110",
                description="Commercial Banking",
            ),
            parent_customer="CU-GFS-HOLDING",
            subsidiaries=["CU-GFS-UK", "CU-GFS-ASIA"],
            headquarters_location="GEO-NA",
            customer_locations=[
                CustomerLocation(
                    location_id="ST-NYC",
                    location_name="New York HQ",
                    business_conducted=True,
                )
            ],
            customer_size=CustomerSize(
                annual_revenue=45_000_000_000,
                employee_count=85000,
                as_of_date="2024-12-31",
            ),
            origin="Organic — Sales Won",
        )
        assert c.customer_id == "CU-00001"
        assert c.customer_name_common == "GFS"
        assert c.industry_classification.code == "522110"
        assert c.customer_size.employee_count == 85000
        assert len(c.subsidiaries) == 2

    def test_relationship_engagement(self):
        c = Customer(
            name="MegaTech Solutions",
            relationship_status="Active Customer",
            relationship_start_date="2015-03-15",
            relationship_tenure_years=9.5,
            account_tier="Strategic",
            engagement_model="Named Account — Dedicated Team",
            primary_contact=PrimaryContact(
                contact_name="Jane Smith",
                contact_title="CTO",
                contact_email="jsmith@megatech.example",
            ),
            account_team=AccountTeam(
                account_manager="RL-AM-001",
                sales_rep="RL-SR-001",
                customer_success_manager="RL-CSM-001",
                executive_sponsor="RL-EVP-001",
            ),
            satisfaction_current=SatisfactionCurrent(
                score=78.0,
                methodology="NPS",
                measurement_date="2024-09-01",
                trend="Improving",
            ),
            health_score=HealthScore(
                score=85.0,
                scale="0–100",
                methodology="Composite Score",
                risk_factors=["Upcoming renewal", "Executive change"],
                last_calculated="2024-11-01",
            ),
        )
        assert c.relationship_status == "Active Customer"
        assert c.account_tier == "Strategic"
        assert c.primary_contact.contact_name == "Jane Smith"
        assert c.account_team.customer_success_manager == "RL-CSM-001"
        assert c.satisfaction_current.score == 78.0
        assert c.health_score.score == 85.0
        assert len(c.health_score.risk_factors) == 2

    def test_financial_profile(self):
        c = Customer(
            name="DataCorp",
            revenue_current=CustomerRevenueCurrent(
                annual_revenue=8_500_000,
                currency="USD",
                fiscal_year="2024",
                yoy_growth_pct=15.0,
            ),
            revenue_lifetime=RevenueLifetime(
                total_revenue=42_000_000,
                since_date="2018-01-01",
            ),
            revenue_by_product=[
                RevenueByProduct(
                    product_id="PR-ANALYTICS",
                    product_name="AnalyticsPro",
                    revenue=5_000_000,
                ),
                RevenueByProduct(
                    product_id="PR-CONNECT",
                    product_name="SecureConnect",
                    revenue=3_500_000,
                ),
            ],
            revenue_concentration_risk=RevenueConcentrationRisk(
                pct_of_enterprise_revenue=0.6,
                concentration_tier="Standard",
            ),
            contract_value=ContractValue(
                total_contract_value=25_000_000,
                annual_contract_value=8_500_000,
                contract_end_date="2027-12-31",
            ),
            payment_terms=PaymentTerms(
                standard_terms="Net 30",
                actual_terms="Net 45",
                days_sales_outstanding=42.0,
            ),
            credit_profile=CreditProfile(
                credit_rating="A+",
                credit_limit=15_000_000,
                credit_risk_level="Low",
            ),
            profitability=Profitability(
                gross_margin_pct=72.0,
                cost_to_serve=1_200_000,
                profit_contribution=5_000_000,
            ),
            wallet_share=WalletShare(
                estimated_total_spend_in_category=25_000_000,
                our_share_pct=34.0,
            ),
            expansion_potential=ExpansionPotential(
                estimated_expansion_revenue=3_000_000,
                confidence="High",
                expansion_products=["PR-AI-SUITE", "PR-DATA-GOV"],
            ),
        )
        assert c.revenue_current.annual_revenue == 8_500_000
        assert c.revenue_lifetime.total_revenue == 42_000_000
        assert len(c.revenue_by_product) == 2
        assert c.credit_profile.credit_rating == "A+"
        assert c.profitability.gross_margin_pct == 72.0
        assert c.wallet_share.our_share_pct == 34.0
        assert len(c.expansion_potential.expansion_products) == 2

    def test_risk_compliance(self):
        c = Customer(
            name="GlobalPharma Ltd",
            customer_risk_profile=CustomerRiskProfile(
                overall_risk="Medium",
                financial_risk="Low",
                operational_risk="Medium",
                reputational_risk="Low",
                regulatory_risk="High",
            ),
            sanctions_screening=CustomerSanctionsScreening(
                screened=True,
                screening_date="2024-10-01",
                screening_tool="Dow Jones Risk & Compliance",
                result="Clear",
                screening_lists=["OFAC SDN", "EU Consolidated", "UN Security Council"],
            ),
            kyc_status=KycStatus(
                completed=True,
                completion_date="2024-01-15",
                next_review_date="2025-01-15",
                kyc_level="Enhanced Due Diligence",
            ),
            export_control_status=ExportControlStatus(
                classification="EAR99",
                license_required=False,
                end_use_statement_on_file=True,
            ),
            data_privacy_obligations=DataPrivacyObligations(
                jurisdictions=["EU", "US", "UK"],
                data_processing_agreement_in_place=True,
                dpa_reference="DPA-GP-2024-001",
                data_classification_of_shared_data="Confidential",
            ),
            customer_compliance_certifications=[
                CustomerComplianceCertification(
                    certification="ISO 27001",
                    issuing_body="BSI",
                    status="Active",
                    relevance="Information security assurance",
                )
            ],
        )
        assert c.customer_risk_profile.regulatory_risk == "High"
        assert c.sanctions_screening.result == "Clear"
        assert len(c.sanctions_screening.screening_lists) == 3
        assert c.kyc_status.kyc_level == "Enhanced Due Diligence"
        assert c.data_privacy_obligations.data_processing_agreement_in_place is True
        assert len(c.customer_compliance_certifications) == 1

    def test_products_consumed(self):
        c = Customer(
            name="TechStartup Inc",
            products_active=[
                ActiveProduct(
                    product_id="PR-PLATFORM",
                    product_name="Cloud Platform",
                    subscription_status="Active",
                    start_date="2023-01-01",
                    renewal_date="2025-01-01",
                )
            ],
            products_historical=[
                HistoricalProduct(
                    product_id="PR-LEGACY",
                    product_name="Legacy Suite",
                    start_date="2020-01-01",
                    end_date="2022-12-31",
                    end_reason="Replaced by Upgrade",
                )
            ],
            service_agreements=[
                ServiceAgreement(
                    agreement_id="SA-001",
                    agreement_type="SLA",
                    sla_tier="Gold",
                    start_date="2023-01-01",
                    end_date="2025-01-01",
                )
            ],
            customizations=[
                Customization(
                    customization_description="Custom SSO integration",
                    complexity="Moderate Customization",
                    annual_cost=50_000,
                )
            ],
            integration_points=[
                IntegrationPoint(
                    integration_description="Salesforce CRM sync",
                    integration_type="REST API",
                    our_system_id="SYS-PLATFORM",
                    customer_system="Salesforce",
                )
            ],
            deployment_model=DeploymentModel(
                model_type="Cloud — Multi-Tenant",
                environment_count=2,
            ),
        )
        assert len(c.products_active) == 1
        assert c.products_active[0].subscription_status == "Active"
        assert c.products_historical[0].end_reason == "Replaced by Upgrade"
        assert c.service_agreements[0].sla_tier == "Gold"
        assert c.customizations[0].annual_cost == 50_000
        assert c.deployment_model.model_type == "Cloud — Multi-Tenant"

    def test_dependencies_relationships(self):
        c = Customer(
            name="RetailCo",
            belongs_to_segment=[
                BelongsToSegment(
                    segment_id="MK-RETAIL",
                    segment_name="Retail",
                    primary_segment=True,
                )
            ],
            buys_products=[
                BuysProduct(
                    product_id="PR-POS",
                    annual_revenue=2_000_000,
                    contract_status="Active",
                )
            ],
            managed_by_org_unit="OU-SALES-NA",
            account_roles=["RL-AM-RETAIL", "RL-CSM-RETAIL"],
            located_in=["GEO-NA", "GEO-EMEA"],
            data_shared_with=[
                DataSharedWith(
                    data_asset_id="DA-ORDERS",
                    sharing_direction="Bidirectional",
                    data_classification="Confidential",
                )
            ],
            managed_through_vendors=["VENDOR-CHANNEL-01"],
        )
        assert c.belongs_to_segment[0].primary_segment is True
        assert c.buys_products[0].annual_revenue == 2_000_000
        assert len(c.account_roles) == 2
        assert len(c.located_in) == 2
        assert c.data_shared_with[0].sharing_direction == "Bidirectional"

    def test_defaults(self):
        c = Customer(name="Defaults Test")
        assert c.customer_id == ""
        assert c.customer_type == ""
        assert c.revenue_current is None
        assert c.customer_risk_profile is None
        assert c.products_active == []
        assert c.belongs_to_segment == []

    def test_json_roundtrip(self):
        c = Customer(
            name="Test Customer",
            customer_id="CU-99999",
            customer_type="Enterprise",
            relationship_status="Active Customer",
            account_tier="Key",
        )
        data = c.model_dump(mode="json")
        restored = Customer.model_validate(data)
        assert restored.customer_id == "CU-99999"
        assert restored.account_tier == "Key"

    def test_any_entity_roundtrip(self):
        c = Customer(name="AnyEntity Test", customer_id="CU-AE-001")
        data = c.model_dump(mode="json")
        restored = _any_entity_adapter.validate_python(data)
        assert isinstance(restored, Customer)
        assert restored.customer_id == "CU-AE-001"
