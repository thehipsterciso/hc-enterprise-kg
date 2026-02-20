"""Tests for L08: Products & Services entity types.

Covers ProductPortfolio and Product entities with attribute group
coverage, sub-model instantiation, and JSON serialization roundtrip.
"""

from pydantic import TypeAdapter

from domain.base import EntityType
from domain.entities import AnyEntity
from domain.entities.product import (
    CapabilityLink,
    CertificationEntry,
    ChurnRate,
    CompetitorEntry,
    CostToDeliver,
    CustomerCount,
    CustomerLifetimeValue,
    CustomerSatisfaction,
    DeliveryChannel,
    DifferentiationFactor,
    EnvironmentalCompliance,
    ExportControlClassification,
    FulfillmentModel,
    Generation,
    LiabilityExposure,
    ManufacturingLocation,
    MarginProfile,
    PortfolioMembership,
    PricingRange,
    Product,
    ProductCategory,
    ProductFormerName,
    ProductLocalName,
    ProductMarketPosition,
    ProductRoles,
    ProductTaxonomyLineage,
    QualityMetrics,
    RecallEntry,
    RegulatoryApprovalStatus,
    RegulatoryClassification,
    RelatedProduct,
    RevenueByGeo,
    RevenueBySegment,
    RevenueCurrent,
    ScalabilityConstraint,
    ServiceLevelPerformance,
    ServiceLevelTargets,
    SystemLink,
    VendorLink,
    VersionCurrent,
    VersionEntry,
)
from domain.entities.product_portfolio import (
    PortfolioFinancialSummary,
    ProductPortfolio,
)
from domain.shared import MarketPosition

_any_entity_adapter = TypeAdapter(AnyEntity)


# ===========================================================================
# ProductPortfolio tests
# ===========================================================================


class TestProductPortfolio:
    def test_minimal_construction(self):
        pp = ProductPortfolio(name="Enterprise Software")
        assert pp.entity_type == EntityType.PRODUCT_PORTFOLIO
        assert pp.name == "Enterprise Software"
        assert pp.portfolio_id == ""

    def test_identity_and_strategy(self):
        pp = ProductPortfolio(
            name="Cloud Platform",
            portfolio_id="PP-00001",
            portfolio_type="Solution Portfolio",
            portfolio_level="Business Unit Portfolio",
            strategic_role="Growth Engine",
            lifecycle_stage="Growth",
            investment_priority="Invest Heavily",
            portfolio_owner="RL-VP-CLOUD",
            managing_org_unit="OU-CLOUD",
        )
        assert pp.portfolio_id == "PP-00001"
        assert pp.strategic_role == "Growth Engine"
        assert pp.portfolio_level == "Business Unit Portfolio"

    def test_hierarchy(self):
        pp = ProductPortfolio(
            name="Enterprise Portfolio",
            portfolio_id="PP-ROOT",
            parent_portfolio="",
            child_portfolios=["PP-CLOUD", "PP-DATA", "PP-SECURITY"],
        )
        assert len(pp.child_portfolios) == 3

    def test_financial_summary(self):
        pp = ProductPortfolio(
            name="Data Analytics",
            financial_summary=PortfolioFinancialSummary(
                annual_revenue=250_000_000,
                annual_cost=150_000_000,
                gross_margin_pct=40.0,
                contribution_margin_pct=25.0,
                currency="USD",
                fiscal_year="2024",
                yoy_growth_pct=18.5,
                revenue_pct_of_enterprise=12.0,
            ),
        )
        assert pp.financial_summary.annual_revenue == 250_000_000
        assert pp.financial_summary.yoy_growth_pct == 18.5

    def test_market_position(self):
        pp = ProductPortfolio(
            name="Security Suite",
            market_position=MarketPosition(
                market_size_tam=50_000_000_000,
                market_share_pct=3.5,
                market_share_rank=7,
                currency="USD",
            ),
        )
        assert pp.market_position.market_share_pct == 3.5

    def test_relationships(self):
        pp = ProductPortfolio(
            name="IoT Platform",
            contains_products=["PR-IOT-HUB", "PR-IOT-EDGE", "PR-IOT-ANALYTICS"],
            managed_by_org_unit="OU-IOT",
        )
        assert len(pp.contains_products) == 3

    def test_json_roundtrip(self):
        pp = ProductPortfolio(
            name="Test Portfolio",
            portfolio_id="PP-99999",
            portfolio_type="Product Line",
            strategic_role="Cash Generator",
        )
        data = pp.model_dump(mode="json")
        restored = ProductPortfolio.model_validate(data)
        assert restored.portfolio_id == "PP-99999"
        assert restored.strategic_role == "Cash Generator"

    def test_any_entity_roundtrip(self):
        pp = ProductPortfolio(name="AnyEntity Test", portfolio_id="PP-AE-001")
        data = pp.model_dump(mode="json")
        restored = _any_entity_adapter.validate_python(data)
        assert isinstance(restored, ProductPortfolio)
        assert restored.portfolio_id == "PP-AE-001"


# ===========================================================================
# Product tests
# ===========================================================================


class TestProduct:
    def test_minimal_construction(self):
        p = Product(name="CloudGuard Pro")
        assert p.entity_type == EntityType.PRODUCT
        assert p.name == "CloudGuard Pro"
        assert p.product_id == ""

    def test_identity_classification(self):
        p = Product(
            name="CloudGuard Pro",
            product_id="PR-00001",
            product_name_internal="CG-PRO",
            product_name_local=[
                ProductLocalName(language_code="de", name="CloudGuard Pro", locale="DE")
            ],
            product_name_former=[
                ProductFormerName(
                    former_name="CloudShield",
                    from_date="2019-01-01",
                    to_date="2022-06-30",
                    change_reason="Brand consolidation",
                )
            ],
            offering_type="Software Product",
            offering_subtype="Enterprise Platform",
            product_category=ProductCategory(
                taxonomy="Enterprise", category_code="SEC-CSPM", category_name="CSPM"
            ),
            sku_count=5,
            functional_domain_primary="Information Security",
            origin="Organic Development",
            taxonomy_lineage=[
                ProductTaxonomyLineage(
                    framework="UNSPSC",
                    framework_element_id="43232300",
                    mapping_confidence="High",
                )
            ],
        )
        assert p.product_id == "PR-00001"
        assert p.offering_type == "Software Product"
        assert p.product_category.category_code == "SEC-CSPM"
        assert len(p.product_name_local) == 1
        assert len(p.product_name_former) == 1

    def test_lifecycle_maturity(self):
        p = Product(
            name="DataSync v3",
            lifecycle_stage="Maturity",
            lifecycle_stage_rationale="Stable revenue, market saturated",
            launch_date="2018-03-15",
            planned_retirement_date="2028-12-31",
            version_current=VersionCurrent(version="3.8.2", release_date="2024-10-01"),
            version_history=[
                VersionEntry(
                    version="3.0.0",
                    release_date="2021-01-15",
                    end_of_support_date="2023-01-15",
                )
            ],
            generation=Generation(
                current_generation=3,
                generation_name="Gen 3 — Cloud Native",
                generation_launch_date="2021-01-15",
            ),
            regulatory_approval_status=RegulatoryApprovalStatus(
                approved=True,
                approval_body="FedRAMP",
                approval_date="2023-06-01",
            ),
        )
        assert p.lifecycle_stage == "Maturity"
        assert p.version_current.version == "3.8.2"
        assert p.generation.current_generation == 3
        assert p.regulatory_approval_status.approved is True

    def test_market_revenue(self):
        p = Product(
            name="AnalyticsPro",
            revenue_current=RevenueCurrent(
                annual_revenue=45_000_000,
                currency="USD",
                fiscal_year="2024",
                revenue_type="Subscription / Recurring",
                recurring_revenue_pct=92.0,
            ),
            revenue_trend="Growing > 10%",
            revenue_by_geography=[
                RevenueByGeo(
                    geography_id="GEO-NA",
                    geography_name="North America",
                    revenue=30_000_000,
                )
            ],
            revenue_by_segment=[
                RevenueBySegment(
                    customer_segment="Enterprise",
                    revenue=35_000_000,
                )
            ],
            pricing_model="Subscription — Tiered",
            pricing_range=PricingRange(
                minimum=5000, maximum=500_000, currency="USD", unit="Per Year"
            ),
            margin_profile=MarginProfile(
                gross_margin_pct=78.0,
                contribution_margin_pct=45.0,
                target_margin_pct=50.0,
                margin_trend="Improving",
            ),
            cost_to_deliver=CostToDeliver(
                annual_cost=10_000_000, cost_type="Fully Loaded"
            ),
            customer_count=CustomerCount(
                active_customers=850,
                total_customers_lifetime=1200,
                customer_count_trend="Growing",
            ),
            market_position=ProductMarketPosition(
                competitive_rank=3,
                market_share_pct=8.5,
                tam=10_000_000_000,
                sam=3_000_000_000,
                som=500_000_000,
            ),
            competitive_landscape=[
                CompetitorEntry(
                    competitor_name="Acme Corp",
                    competitor_product="Acme Analytics",
                    relative_position="Leader",
                    competitive_advantage="Broader feature set",
                    competitive_vulnerability="Higher price point",
                )
            ],
            differentiation_factors=[
                DifferentiationFactor(
                    factor="AI-Powered Insights",
                    strength="Strong",
                    defensibility="Patent Protected",
                )
            ],
        )
        assert p.revenue_current.annual_revenue == 45_000_000
        assert p.revenue_current.recurring_revenue_pct == 92.0
        assert p.margin_profile.gross_margin_pct == 78.0
        assert p.market_position.som == 500_000_000
        assert len(p.competitive_landscape) == 1
        assert len(p.differentiation_factors) == 1

    def test_quality_customer_experience(self):
        p = Product(
            name="SupportHub",
            customer_satisfaction=CustomerSatisfaction(
                score=72.0,
                methodology="NPS",
                sample_size=5000,
                measurement_date="2024-09-01",
            ),
            quality_metrics=QualityMetrics(
                defect_rate=0.02,
                return_rate_pct=0.5,
                quality_trend="Improving",
            ),
            service_level_targets=ServiceLevelTargets(
                availability_target_pct=99.95,
                response_time_target="< 200ms",
            ),
            service_level_performance=ServiceLevelPerformance(
                availability_actual_pct=99.97,
                sla_breaches_12m=2,
            ),
            churn_rate=ChurnRate(
                annual_churn_pct=8.5,
                monthly_churn_pct=0.7,
                logo_churn_pct=6.0,
                revenue_churn_pct=4.5,
                trend="Improving",
            ),
            customer_lifetime_value=CustomerLifetimeValue(
                average_clv=150_000,
                currency="USD",
                methodology="Discounted Cash Flow",
                payback_period_months=14,
            ),
        )
        assert p.customer_satisfaction.score == 72.0
        assert p.service_level_performance.availability_actual_pct == 99.97
        assert p.churn_rate.annual_churn_pct == 8.5
        assert p.customer_lifetime_value.average_clv == 150_000

    def test_regulatory_compliance(self):
        p = Product(
            name="MedDevice Controller",
            regulatory_classification=RegulatoryClassification(
                classification="Class II Medical Device",
                classification_body="FDA",
                jurisdiction="US",
                classification_date="2023-01-15",
            ),
            certifications_required=[
                CertificationEntry(
                    certification="CE Marking",
                    issuing_body="EU Notified Body",
                    status="Active",
                    jurisdiction="EU",
                    expiration_date="2026-12-31",
                )
            ],
            export_control_classification=ExportControlClassification(
                classification_number="EAR99",
                control_regime="EAR",
                jurisdiction="US",
                restrictions_summary="No license required for most destinations",
            ),
            environmental_compliance=EnvironmentalCompliance(
                rohs_compliant=True,
                reach_compliant=True,
                weee_applicable=True,
                conflict_minerals_status="Conflict-Free Certified",
            ),
            safety_certifications=[],
            recall_history=[
                RecallEntry(
                    recall_date="2022-08-15",
                    recall_scope="US Only",
                    reason="Firmware update issue",
                    units_affected=1500,
                    resolution="OTA patch",
                    regulatory_body="FDA",
                )
            ],
            liability_exposure=LiabilityExposure(
                product_liability_insurance=True,
                coverage_limit=50_000_000,
                claims_history_12m=0,
            ),
        )
        assert p.regulatory_classification.classification == "Class II Medical Device"
        assert p.environmental_compliance.rohs_compliant is True
        assert p.recall_history[0].units_affected == 1500
        assert p.liability_exposure.coverage_limit == 50_000_000

    def test_delivery_operations(self):
        p = Product(
            name="Industrial Sensor Kit",
            delivery_model="Manufactured & Shipped",
            delivery_channels=[
                DeliveryChannel(
                    channel_type="Direct Sales",
                    channel_name="Enterprise Sales",
                    revenue_pct=60.0,
                ),
                DeliveryChannel(
                    channel_type="Distributor",
                    channel_name="Arrow Electronics",
                    revenue_pct=40.0,
                ),
            ],
            supply_chain_complexity="Complex",
            manufacturing_locations=[
                ManufacturingLocation(
                    site_id="ST-SHZ",
                    site_name="Shenzhen Factory",
                    production_type="Primary",
                )
            ],
            fulfillment_model=FulfillmentModel(
                model_type="Make to Order",
                average_lead_time="6 weeks",
                on_time_delivery_pct=94.5,
            ),
            scalability_constraints=[
                ScalabilityConstraint(
                    constraint_type="Raw Material Availability",
                    constraint_description="Rare earth elements supply",
                    impact="Limiting Growth",
                    mitigation_plan="Secondary supplier qualification",
                )
            ],
        )
        assert p.delivery_model == "Manufactured & Shipped"
        assert len(p.delivery_channels) == 2
        assert p.fulfillment_model.on_time_delivery_pct == 94.5
        assert p.scalability_constraints[0].impact == "Limiting Growth"

    def test_dependencies_relationships(self):
        p = Product(
            name="SecureConnect",
            belongs_to_portfolio=[
                PortfolioMembership(
                    portfolio_id="PP-SEC", relationship_type="Primary"
                )
            ],
            enabled_by_capabilities=[
                CapabilityLink(
                    capability_id="BC-NET-SEC",
                    enablement_type="Core Delivery",
                )
            ],
            managed_by_org_unit="OU-SECURITY",
            product_roles=ProductRoles(
                product_manager="RL-PM-SC",
                engineering_lead="RL-ENG-SC",
            ),
            delivered_from_locations=["ST-AWS-USEAST", "ST-AWS-EUWEST"],
            enabled_by_systems=[
                SystemLink(
                    system_id="SYS-K8S", enablement_type="Core Platform"
                )
            ],
            serves_customers=[],
            depends_on_vendors=[
                VendorLink(
                    vendor_id="VENDOR-AWS",
                    dependency_type="Technology Provider",
                    dependency_criticality="Critical",
                )
            ],
            related_products=[
                RelatedProduct(
                    product_id="PR-FIREWALL",
                    relationship_type="Complementary",
                )
            ],
        )
        assert p.belongs_to_portfolio[0].portfolio_id == "PP-SEC"
        assert p.product_roles.product_manager == "RL-PM-SC"
        assert len(p.delivered_from_locations) == 2
        assert p.depends_on_vendors[0].dependency_criticality == "Critical"
        assert p.related_products[0].relationship_type == "Complementary"

    def test_defaults(self):
        p = Product(name="Defaults Test")
        assert p.product_id == ""
        assert p.offering_type == ""
        assert p.lifecycle_stage == ""
        assert p.revenue_current is None
        assert p.customer_satisfaction is None
        assert p.regulatory_classification is None
        assert p.delivery_model == ""
        assert p.belongs_to_portfolio == []
        assert p.competitive_landscape == []

    def test_json_roundtrip(self):
        p = Product(
            name="Test Product",
            product_id="PR-99999",
            offering_type="SaaS",
            lifecycle_stage="Growth",
            delivery_model="SaaS / Cloud",
        )
        data = p.model_dump(mode="json")
        restored = Product.model_validate(data)
        assert restored.product_id == "PR-99999"
        assert restored.delivery_model == "SaaS / Cloud"

    def test_any_entity_roundtrip(self):
        p = Product(name="AnyEntity Test", product_id="PR-AE-001")
        data = p.model_dump(mode="json")
        restored = _any_entity_adapter.validate_python(data)
        assert isinstance(restored, Product)
        assert restored.product_id == "PR-AE-001"
