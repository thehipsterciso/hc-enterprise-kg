"""Tests for L07: Locations & Facilities entity types.

Covers Site, Geography, and Jurisdiction entities with attribute group
coverage, sub-model instantiation, and JSON serialization roundtrip.
"""

from pydantic import TypeAdapter

from domain.base import EntityType
from domain.entities import AnyEntity
from domain.entities.geography import (
    CountryEntry,
    GeographicStrategicImportance,
    Geography,
    MarketCharacteristics,
    RegionalLeadership,
)
from domain.entities.jurisdiction import (
    BreachNotificationRequirement,
    CrossBorderTransferRules,
    DataResidencyRequirements,
    GoverningBody,
    Jurisdiction,
    JurisdictionLocalName,
    LaborLawSummary,
    PrivacyRegulation,
    RegulatoryAgency,
    RegulatoryFrameworkSummary,
    SanctionsStatus,
    TaxRegime,
    TransferPricingRules,
    WithholdingTaxRates,
)
from domain.entities.site import (
    AnnualCost,
    CapitalInvestment,
    ClimateRiskAssessment,
    Coordinates,
    CurrentOccupancy,
    DesignCapacity,
    EnvironmentalCertification,
    EvacuationPlan,
    ExpansionPotential,
    GeographyReference,
    JurisdictionReference,
    LeaseDetails,
    NaturalHazard,
    NetworkConnectivity,
    OccupancyByUnit,
    PhysicalSecuritySystem,
    PowerSupply,
    Site,
    SiteAddress,
    SiteConnection,
    SiteSPOF,
    SystemHosting,
    UtilizationRate,
    VendorService,
)

_any_entity_adapter = TypeAdapter(AnyEntity)


# ===========================================================================
# Site tests
# ===========================================================================


class TestSite:
    def test_minimal_construction(self):
        site = Site(name="NYC HQ")
        assert site.entity_type == EntityType.SITE
        assert site.name == "NYC HQ"
        assert site.site_id == ""

    def test_identity_classification(self):
        site = Site(
            name="London Office",
            site_id="ST-00001",
            site_type="Regional Headquarters",
            site_status="Active",
            site_status_rationale="Fully operational EMEA hub",
            ownership_type="Leased",
            strategic_designation="Core Operations",
            origin="Organic — Leased",
            address=SiteAddress(
                street_line_1="1 Canada Square",
                city="London",
                state_province="Greater London",
                postal_code="E14 5AB",
                country_code="GB",
                country_name="United Kingdom",
            ),
        )
        assert site.site_id == "ST-00001"
        assert site.site_type == "Regional Headquarters"
        assert site.address.city == "London"

    def test_physical_characteristics(self):
        site = Site(
            name="Primary DC",
            coordinates=Coordinates(latitude=40.7128, longitude=-74.0060),
            design_capacity=DesignCapacity(
                max_occupants=200,
                max_workstations=150,
                current_configured_workstations=120,
                current_utilization_pct=80,
            ),
            environmental_certifications=[
                EnvironmentalCertification(
                    certification="LEED",
                    level="Gold",
                    date_achieved="2022-03-15",
                )
            ],
        )
        assert site.coordinates.latitude == 40.7128
        assert site.design_capacity.max_occupants == 200
        assert len(site.environmental_certifications) == 1

    def test_infrastructure_utilities(self):
        site = Site(
            name="Data Center East",
            physical_security_tier="Tier 4 — High Security",
            power_supply=PowerSupply(
                primary_source="Grid — Dual Feed",
                total_capacity_kw=5000,
                redundancy_level="2N",
                renewable_energy_pct=30,
            ),
            network_connectivity=NetworkConnectivity(
                primary_carrier="AT&T",
                secondary_carrier="Verizon",
                redundancy_level="Carrier Diverse + Path Diverse",
                bandwidth_mbps=10000,
                sd_wan_enabled=True,
            ),
            physical_security_systems=[
                PhysicalSecuritySystem(
                    system_type="Access Control — Biometric",
                    coverage="Full Site",
                    monitoring="24x7 Live Monitoring",
                )
            ],
        )
        assert site.power_supply.redundancy_level == "2N"
        assert site.network_connectivity.bandwidth_mbps == 10000
        assert site.physical_security_tier == "Tier 4 — High Security"

    def test_financial_profile(self):
        site = Site(
            name="Chicago Office",
            annual_operating_cost=AnnualCost(amount=8500000, currency="USD", fiscal_year="2024"),
            lease_details=LeaseDetails(
                landlord="Boston Properties",
                lease_type="Full Service / Gross",
                lease_start_date="2020-01-01",
                lease_end_date="2030-12-31",
                annual_base_rent=5000000,
                remaining_lease_obligation=30000000,
            ),
            capital_investment_planned=[
                CapitalInvestment(
                    investment_description="Floor 12 renovation",
                    amount=2000000,
                    investment_type="Renovation",
                    approval_status="Approved",
                )
            ],
        )
        assert site.annual_operating_cost.amount == 8500000
        assert site.lease_details.remaining_lease_obligation == 30000000

    def test_capacity_utilization(self):
        site = Site(
            name="Austin Campus",
            current_occupancy=CurrentOccupancy(headcount=1200, as_of_date="2024-11-01"),
            occupancy_by_unit=[
                OccupancyByUnit(unit_id="OU-ENG", unit_name="Engineering", headcount=600)
            ],
            utilization_rate=UtilizationRate(
                current_pct=72, peak_pct=90, measurement_methodology="Badge Swipe Data"
            ),
            expansion_potential=ExpansionPotential(
                expandable=True,
                expansion_type="Horizontal (Adjacent Land)",
                max_additional_capacity="500 workstations",
            ),
        )
        assert site.current_occupancy.headcount == 1200
        assert site.utilization_rate.current_pct == 72

    def test_risk_resilience(self):
        site = Site(
            name="Miami Office",
            risk_exposure_inherent="High",
            risk_exposure_residual="Medium",
            natural_hazard_profile=[
                NaturalHazard(
                    hazard_type="Hurricane / Cyclone / Typhoon",
                    risk_level="Very High",
                    basis="FEMA Zone A flood map",
                )
            ],
            climate_risk_assessment=ClimateRiskAssessment(
                physical_risk_score=4.5,
                physical_risk_drivers=["Sea level rise", "Storm surge"],
                transition_risk_score=2.0,
                scenario="RCP 4.5",
                time_horizon="2050",
            ),
            business_continuity_tier="Gold",
            disaster_recovery_role="Primary Production Site",
            evacuation_plan=EvacuationPlan(
                plan_reference="EP-MIA-2024",
                last_drill_date="2024-06-15",
                max_evacuation_time_minutes=15,
                drill_results="Successful",
            ),
            single_points_of_failure=[
                SiteSPOF(
                    spof_id="SPOF-MIA-001",
                    spof_description="Single fiber route",
                    spof_type="Network",
                    mitigation_status="Partially Mitigated",
                )
            ],
        )
        assert site.risk_exposure_inherent == "High"
        assert site.natural_hazard_profile[0].risk_level == "Very High"
        assert site.climate_risk_assessment.physical_risk_score == 4.5
        assert site.business_continuity_tier == "Gold"

    def test_dependencies_relationships(self):
        site = Site(
            name="Frankfurt DC",
            located_in_geography=[
                GeographyReference(geography_id="GEO-EMEA", geography_level="Region")
            ],
            subject_to_jurisdictions=[
                JurisdictionReference(
                    jurisdiction_id="JR-DE", jurisdiction_type="Federal / National"
                )
            ],
            connected_to_sites=[
                SiteConnection(
                    site_id="ST-LDN",
                    connection_type="Network — Dedicated Circuit",
                    capacity="10Gbps",
                    latency="8ms",
                )
            ],
            backup_site="ST-AMS",
            hosts_systems=[SystemHosting(system_id="SYS-SAP", hosting_type="Primary Production")],
            managed_by_vendors=[
                VendorService(vendor_id="VENDOR-JLL", service_type="Facility Management")
            ],
        )
        assert len(site.located_in_geography) == 1
        assert site.backup_site == "ST-AMS"
        assert site.hosts_systems[0].hosting_type == "Primary Production"

    def test_json_roundtrip(self):
        site = Site(
            name="Test Site",
            site_id="ST-99999",
            site_type="Office",
            site_status="Active",
            risk_exposure_inherent="Medium",
            business_continuity_tier="Silver",
        )
        data = site.model_dump(mode="json")
        restored = Site.model_validate(data)
        assert restored.site_id == "ST-99999"
        assert restored.business_continuity_tier == "Silver"

    def test_any_entity_roundtrip(self):
        site = Site(name="AnyEntity Test", site_id="ST-AE-001")
        data = site.model_dump(mode="json")
        restored = _any_entity_adapter.validate_python(data)
        assert isinstance(restored, Site)
        assert restored.site_id == "ST-AE-001"


# ===========================================================================
# Geography tests
# ===========================================================================


class TestGeography:
    def test_minimal_construction(self):
        geo = Geography(name="North America")
        assert geo.entity_type == EntityType.GEOGRAPHY
        assert geo.geography_id == ""

    def test_full_geography(self):
        geo = Geography(
            name="Europe, Middle East & Africa",
            geography_id="GEO-EMEA",
            geography_name_short="EMEA",
            geography_type="Super-Region",
            geography_description="Enterprise EMEA operating region",
            parent_geography="GEO-GLOBAL",
            child_geographies=["GEO-EUR", "GEO-MEA"],
            countries_included=[
                CountryEntry(country_code="GB", country_name="United Kingdom"),
                CountryEntry(country_code="DE", country_name="Germany"),
            ],
            regional_leadership=RegionalLeadership(
                org_unit_id="OU-EMEA",
                leader_role_id="RL-EMEA-HEAD",
                leader_person_id="PS-EMEA-001",
            ),
            time_zones=["Europe/London", "Europe/Berlin", "Asia/Dubai"],
            primary_languages=["en", "de", "fr", "ar"],
            market_characteristics=MarketCharacteristics(
                total_gdp=25000000000000,
                population=2500000000,
                gdp_growth_rate=1.5,
                economic_classification="Mixed",
                currency_primary="EUR",
            ),
            strategic_importance=GeographicStrategicImportance(
                importance_level="Core Established Market",
                revenue_contribution_pct=35,
                employee_count=5000,
                site_count=12,
            ),
            sites_in_geography=["ST-LDN", "ST-FRA", "ST-DXB"],
            overlaps_with_jurisdictions=["JR-EU", "JR-GB", "JR-DE"],
            confidence_level="Verified",
        )
        assert geo.geography_id == "GEO-EMEA"
        assert geo.geography_type == "Super-Region"
        assert len(geo.countries_included) == 2
        assert geo.strategic_importance.revenue_contribution_pct == 35

    def test_json_roundtrip(self):
        geo = Geography(
            name="Asia Pacific",
            geography_id="GEO-APAC",
            geography_type="Super-Region",
        )
        data = geo.model_dump(mode="json")
        restored = Geography.model_validate(data)
        assert restored.geography_id == "GEO-APAC"

    def test_any_entity_roundtrip(self):
        geo = Geography(name="LATAM", geography_id="GEO-LATAM")
        data = geo.model_dump(mode="json")
        restored = _any_entity_adapter.validate_python(data)
        assert isinstance(restored, Geography)


# ===========================================================================
# Jurisdiction tests
# ===========================================================================


class TestJurisdiction:
    def test_minimal_construction(self):
        jur = Jurisdiction(name="United States")
        assert jur.entity_type == EntityType.JURISDICTION
        assert jur.jurisdiction_id == ""

    def test_full_jurisdiction(self):
        jur = Jurisdiction(
            name="European Union",
            jurisdiction_id="JR-EU",
            jurisdiction_name_local=JurisdictionLocalName(
                language_code="fr", name="Union européenne"
            ),
            jurisdiction_type="Supranational",
            jurisdiction_code="EU",
            parent_jurisdiction="",
            child_jurisdictions=["JR-DE", "JR-FR", "JR-NL"],
            governing_body=GoverningBody(
                name="European Commission",
                regulatory_agencies=[
                    RegulatoryAgency(
                        agency_name="European Data Protection Board",
                        regulatory_domain="Data Protection",
                    )
                ],
            ),
            regulatory_framework_summary=RegulatoryFrameworkSummary(
                legal_system_type="Civil Law",
                regulatory_intensity="Heavy",
                key_characteristics="GDPR, Digital Services Act, AI Act",
            ),
            data_residency_requirements=DataResidencyRequirements(
                has_requirements=True,
                requirement_description="Adequacy decisions required for transfers",
                localization_required=False,
                transfer_mechanisms_available=["SCCs", "BCRs", "Adequacy Decision"],
            ),
            labor_law_summary=LaborLawSummary(
                employment_at_will=False,
                notice_period_statutory="1-3 months varies by member state",
                works_council_required=True,
                works_council_threshold="50 employees (varies)",
                union_prevalence="Moderate",
            ),
            tax_regime=TaxRegime(
                corporate_tax_rate=21.0,
                vat_gst_rate=20.0,
                withholding_tax_rates=WithholdingTaxRates(dividends=15, interest=15, royalties=15),
                transfer_pricing_rules=TransferPricingRules(
                    documentation_required=True,
                    country_by_country_reporting=True,
                    arm_length_standard=True,
                ),
            ),
            privacy_regulation=PrivacyRegulation(
                primary_regulation="GDPR",
                supervisory_authority="EDPB",
                breach_notification_requirement=BreachNotificationRequirement(
                    required=True,
                    timeframe_hours=72,
                    authority_notification=True,
                    individual_notification=True,
                ),
                cross_border_transfer_restrictions="Requires adequacy or safeguards",
            ),
            cross_border_transfer_rules=CrossBorderTransferRules(
                data_transfer_restricted=True,
                export_controls=["EU Dual-Use Regulation"],
            ),
            sanctions_status=SanctionsStatus(sanctioned=False, sanction_type="None"),
            sites_in_jurisdiction=["ST-FRA", "ST-AMS", "ST-PAR"],
            confidence_level="Verified",
        )
        assert jur.jurisdiction_id == "JR-EU"
        assert jur.jurisdiction_type == "Supranational"
        assert jur.privacy_regulation.breach_notification_requirement.timeframe_hours == 72
        assert jur.tax_regime.corporate_tax_rate == 21.0
        assert jur.labor_law_summary.works_council_required is True

    def test_json_roundtrip(self):
        jur = Jurisdiction(
            name="Germany",
            jurisdiction_id="JR-DE",
            jurisdiction_type="Federal / National",
            jurisdiction_code="DE",
        )
        data = jur.model_dump(mode="json")
        restored = Jurisdiction.model_validate(data)
        assert restored.jurisdiction_id == "JR-DE"
        assert restored.jurisdiction_code == "DE"

    def test_any_entity_roundtrip(self):
        jur = Jurisdiction(name="UK", jurisdiction_id="JR-GB")
        data = jur.model_dump(mode="json")
        restored = _any_entity_adapter.validate_python(data)
        assert isinstance(restored, Jurisdiction)
