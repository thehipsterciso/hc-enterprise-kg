"""Tests for L04: Organization entity type.

Covers OrganizationalUnit (new) entity with multi-hierarchy structures,
type-specific extensions, and full attribute group coverage.
Tests construction, sub-model instantiation, and JSON serialization roundtrip.
"""

from pydantic import TypeAdapter

from domain.base import EntityType
from domain.entities import AnyEntity
from domain.entities.organizational_unit import (
    AttritionRate,
    BudgetAuthority,
    CenterOfExcellenceDetails,
    CharterDocument,
    CoEAdoptionMetrics,
    CoEStandard,
    ControlEnvironmentMaturity,
    CostBreakdownItemOU,
    CostStructure,
    DelegationOfAuthority,
    EmployeeCount,
    EmployeeCountByLocation,
    FormerUnitName,
    GeographicPresence,
    HierarchyMembership,
    IntercompanyRelationship,
    JointVentureDetails,
    JVPartnerEntity,
    KeyPersonDependency,
    LeadershipTeamMember,
    LegalEntityDetails,
    LitigationExposure,
    MarketPositionOU,
    MatrixRelationship,
    OperatingHours,
    OrganizationalUnit,
    OrgHealthScore,
    ParentReportingRelationship,
    RegulatoryEnvironment,
    RevenueAttribution,
    RiskFactor,
    SharedServiceDetails,
    SpanOfControl,
    StatutoryReportingObligation,
    TaxJurisdiction,
)

_any_entity_adapter = TypeAdapter(AnyEntity)


# ===========================================================================
# OrganizationalUnit tests
# ===========================================================================


class TestOrganizationalUnit:
    def test_minimal_construction(self):
        ou = OrganizationalUnit(name="Engineering")
        assert ou.entity_type == EntityType.ORGANIZATIONAL_UNIT
        assert ou.unit_id == ""
        assert ou.unit_type == ""
        assert ou.hierarchy_memberships == []
        assert ou.pl_accountability is False
        assert ou.employee_count.fte is None
        assert ou.legal_entity_details.jurisdiction == ""

    def test_identity_and_classification(self):
        ou = OrganizationalUnit(
            name="Global Technology & Digital",
            unit_id="OU-00100",
            unit_type="Division",
            unit_subtype="Technology",
            functional_domain_primary="Technology & Digital",
            functional_domain_secondary=["Data & Analytics"],
            operating_model="Matrix",
            unit_name_former=[
                FormerUnitName(
                    former_name="IT Department",
                    from_date="2015-01-01",
                    to_date="2022-06-30",
                    change_reason="Digital transformation rebrand",
                ),
            ],
            hierarchy_memberships=[
                HierarchyMembership(
                    hierarchy_type="Operational",
                    parent_unit_id="OU-00001",
                    position_in_hierarchy=2,
                    is_root=False,
                    effective_date="2022-07-01",
                ),
                HierarchyMembership(
                    hierarchy_type="Financial",
                    parent_unit_id="OU-00002",
                    position_in_hierarchy=3,
                ),
            ],
            matrix_relationships=[
                MatrixRelationship(
                    related_unit_id="OU-00050",
                    relationship_direction="Influences",
                    influence_strength="Strong",
                    relationship_description="Technology standards",
                ),
            ],
            origin="Organic",
            formation_date="2022-07-01",
        )
        assert ou.unit_id == "OU-00100"
        assert ou.unit_type == "Division"
        assert ou.operating_model == "Matrix"
        assert len(ou.hierarchy_memberships) == 2
        assert ou.hierarchy_memberships[0].hierarchy_type == "Operational"
        assert ou.hierarchy_memberships[1].hierarchy_type == "Financial"
        assert ou.matrix_relationships[0].influence_strength == "Strong"
        assert ou.unit_name_former[0].change_reason == "Digital transformation rebrand"

    def test_operational_profile(self):
        ou = OrganizationalUnit(
            name="APAC Operations",
            operational_status="Active",
            operational_status_rationale="Fully operational across all geographies",
            employee_count=EmployeeCount(fte=2500, contractor=300, vendor_fte=150, total=2950),
            employee_count_by_location=[
                EmployeeCountByLocation(
                    location_id="SITE-001",
                    location_name="Singapore Hub",
                    fte=800,
                    contractor=50,
                ),
                EmployeeCountByLocation(
                    location_id="SITE-002",
                    location_name="Tokyo Office",
                    fte=600,
                ),
            ],
            geographic_scope="Multi-Regional",
            geographic_presence=[
                GeographicPresence(
                    location_id="SITE-001",
                    location_name="Singapore Hub",
                    presence_type="Regional Hub",
                ),
            ],
            operating_hours=OperatingHours(
                timezone_primary="Asia/Singapore",
                timezones_all=["Asia/Singapore", "Asia/Tokyo", "Australia/Sydney"],
                operating_model="Follow-the-Sun",
            ),
            language_primary="en",
            languages_supported=["ja", "zh", "ko"],
            organizational_health_score=OrgHealthScore(
                score=3.8, methodology="McKinsey OHI", assessed_date="2024-06-01"
            ),
            attrition_rate=AttritionRate(
                annual_total_pct=12.5, voluntary_pct=8.0, regrettable_pct=3.5
            ),
            span_of_control=SpanOfControl(
                average_direct_reports=7.2, min_direct_reports=3, max_direct_reports=15
            ),
            management_layers=5,
        )
        assert ou.employee_count.total == 2950
        assert len(ou.employee_count_by_location) == 2
        assert ou.geographic_scope == "Multi-Regional"
        assert ou.operating_hours.operating_model == "Follow-the-Sun"
        assert ou.organizational_health_score.score == 3.8
        assert ou.attrition_rate.regrettable_pct == 3.5
        assert ou.span_of_control.average_direct_reports == 7.2
        assert ou.management_layers == 5

    def test_financial_profile(self):
        ou = OrganizationalUnit(
            name="Commercial Banking Division",
            pl_accountability=True,
            revenue_attribution=RevenueAttribution(
                annual_revenue=850_000_000,
                fiscal_year="FY2024",
                revenue_type="Direct",
            ),
            cost_structure=CostStructure(
                annual_opex=320_000_000,
                annual_capex=45_000_000,
                total_annual_cost=365_000_000,
                fiscal_year="FY2024",
            ),
            cost_breakdown=[
                CostBreakdownItemOU(
                    category="Personnel Salary",
                    amount=200_000_000,
                    percentage_of_total=54.8,
                ),
                CostBreakdownItemOU(
                    category="Technology Software",
                    amount=65_000_000,
                    percentage_of_total=17.8,
                ),
            ],
            budget_authority=BudgetAuthority(
                approval_limit=5_000_000,
                hiring_authority=True,
                contract_authority=True,
            ),
            intercompany_relationships=[
                IntercompanyRelationship(
                    counterparty_unit_id="OU-00200",
                    relationship_type="Service Consumer",
                    annual_volume=12_000_000,
                    agreement_reference="ICA-2024-001",
                ),
            ],
            cost_center_id="CC-4100",
            profit_center_id="PC-4100",
            audit_scope="In Scope — External Audit",
        )
        assert ou.pl_accountability is True
        assert ou.revenue_attribution.annual_revenue == 850_000_000
        assert ou.cost_structure.total_annual_cost == 365_000_000
        assert len(ou.cost_breakdown) == 2
        assert ou.budget_authority.approval_limit == 5_000_000
        assert ou.intercompany_relationships[0].annual_volume == 12_000_000
        assert ou.audit_scope == "In Scope — External Audit"

    def test_strategic_importance(self):
        ou = OrganizationalUnit(
            name="Digital Innovation Lab",
            strategic_role="Venture/Incubation",
            strategic_role_rationale="Incubating next-gen digital products",
            business_criticality="Business Critical",
            criticality_justification="Drives future revenue pipeline",
            market_position=MarketPositionOU(
                position_description="Top 3 in fintech innovation",
                competitive_rank=2,
                market_share_pct=15.0,
            ),
            transformation_stage="Mid-Transformation",
            divestiture_candidacy="Not Considered",
        )
        assert ou.strategic_role == "Venture/Incubation"
        assert ou.business_criticality == "Business Critical"
        assert ou.market_position.competitive_rank == 2
        assert ou.transformation_stage == "Mid-Transformation"

    def test_ownership_and_governance(self):
        ou = OrganizationalUnit(
            name="Risk Management",
            unit_leader="CRO-001",
            unit_leader_title="Chief Risk Officer",
            leadership_team=[
                LeadershipTeamMember(
                    role_id="ROLE-001",
                    title="VP Credit Risk",
                    functional_responsibility="Credit risk management",
                ),
                LeadershipTeamMember(
                    role_id="ROLE-002",
                    title="VP Operational Risk",
                    functional_responsibility="Operational risk framework",
                ),
            ],
            governance_cadence="Monthly",
            parent_reporting_relationship=ParentReportingRelationship(
                reports_to_unit_id="OU-00001",
                reports_to_leader="CEO-001",
                reporting_cadence="Monthly",
            ),
            delegation_of_authority=DelegationOfAuthority(
                financial_limit=2_000_000,
                hiring_authority=True,
                policy_authority=True,
            ),
            compliance_officer="COMP-001",
            charter_document=CharterDocument(
                document_reference="DOC-RM-2024-001",
                last_reviewed_date="2024-03-15",
            ),
        )
        assert ou.unit_leader_title == "Chief Risk Officer"
        assert len(ou.leadership_team) == 2
        assert ou.governance_cadence == "Monthly"
        assert ou.parent_reporting_relationship.reports_to_unit_id == "OU-00001"
        assert ou.delegation_of_authority.policy_authority is True
        assert ou.charter_document.document_reference == "DOC-RM-2024-001"

    def test_risk_and_compliance(self):
        ou = OrganizationalUnit(
            name="Treasury Operations",
            risk_exposure_inherent="Critical",
            risk_exposure_residual="High",
            risk_factors=[
                RiskFactor(
                    risk_id="RISK-001",
                    risk_category="Financial",
                    likelihood="Possible",
                    impact="Critical",
                    velocity="Immediate",
                ),
            ],
            regulatory_environment=[
                RegulatoryEnvironment(
                    regulation="Basel III",
                    jurisdiction="Global",
                    compliance_status="Compliant",
                    regulatory_body="BIS",
                ),
            ],
            control_environment_maturity=ControlEnvironmentMaturity(
                overall_score=4.2,
                assessed_date="2024-09-01",
                assessed_by="Internal Audit",
            ),
            litigation_exposure=LitigationExposure(
                active_matters_count=2,
                severity_assessment="Medium",
                total_exposure_estimate=15_000_000,
            ),
            sanctions_screening_status="Cleared",
            business_continuity_tier="Platinum",
            key_person_dependencies=[
                KeyPersonDependency(
                    person_reference="PERSON-001",
                    role="Head of Treasury",
                    criticality="Critical",
                    succession_plan_exists=True,
                    successor_identified=True,
                    successor_readiness="Ready in 1 Year",
                ),
            ],
        )
        assert ou.risk_exposure_inherent == "Critical"
        assert ou.risk_factors[0].velocity == "Immediate"
        assert ou.regulatory_environment[0].regulation == "Basel III"
        assert ou.control_environment_maturity.overall_score == 4.2
        assert ou.litigation_exposure.total_exposure_estimate == 15_000_000
        assert ou.business_continuity_tier == "Platinum"
        assert ou.key_person_dependencies[0].successor_readiness == "Ready in 1 Year"

    def test_legal_entity_details(self):
        ou = OrganizationalUnit(
            name="Acme Financial Services Ltd",
            unit_type="Legal Entity",
            legal_entity_details=LegalEntityDetails(
                jurisdiction="United Kingdom",
                registration_id="12345678",
                entity_type_legal="Operating Subsidiary",
                incorporation_date="2005-03-15",
                ownership_percentage=100.0,
            ),
            tax_jurisdictions=[
                TaxJurisdiction(
                    jurisdiction_name="UK",
                    tax_id="GB123456789",
                    tax_status="Active",
                ),
            ],
            statutory_reporting_obligations=[
                StatutoryReportingObligation(
                    obligation="Annual Accounts",
                    jurisdiction="UK",
                    frequency="Annual",
                    governing_body="Companies House",
                    compliance_status="Compliant",
                ),
            ],
        )
        assert ou.legal_entity_details.entity_type_legal == "Operating Subsidiary"
        assert ou.legal_entity_details.ownership_percentage == 100.0
        assert ou.tax_jurisdictions[0].tax_status == "Active"
        assert ou.statutory_reporting_obligations[0].governing_body == "Companies House"

    def test_shared_service_center_details(self):
        ou = OrganizationalUnit(
            name="Global Business Services",
            unit_type="Shared Service Center",
            shared_service_details=SharedServiceDetails(
                chargeback_model="Full Chargeback",
                client_units=[
                    {
                        "unit_id": "OU-00100",
                        "annual_charge": 5_000_000,
                        "satisfaction_score": 4.1,
                    },
                ],
            ),
        )
        assert ou.shared_service_details.chargeback_model == "Full Chargeback"
        assert ou.shared_service_details.client_units[0].annual_charge == 5_000_000

    def test_center_of_excellence_details(self):
        ou = OrganizationalUnit(
            name="Data & AI CoE",
            unit_type="Center of Excellence",
            center_of_excellence_details=CenterOfExcellenceDetails(
                expertise_domains=["Machine Learning", "Data Engineering", "MLOps"],
                standards_published=[
                    CoEStandard(
                        standard_name="ML Model Governance",
                        adoption_rate_pct=78.0,
                    ),
                ],
                adoption_metrics=CoEAdoptionMetrics(
                    enterprise_adoption_pct=65.0,
                    units_engaged=12,
                    units_total=18,
                ),
            ),
        )
        assert len(ou.center_of_excellence_details.expertise_domains) == 3
        assert ou.center_of_excellence_details.standards_published[0].adoption_rate_pct == 78.0
        assert ou.center_of_excellence_details.adoption_metrics.units_engaged == 12

    def test_joint_venture_details(self):
        ou = OrganizationalUnit(
            name="CloudPay JV",
            unit_type="Joint Venture Unit",
            joint_venture_details=JointVentureDetails(
                partner_entities=[
                    JVPartnerEntity(
                        partner_name="CloudTech Inc",
                        ownership_pct=49.0,
                        governance_rights="Board Seat + Veto on Major Decisions",
                    ),
                ],
                jv_term_years=10.0,
                exit_triggers=["Material breach", "Change of control"],
            ),
        )
        assert ou.joint_venture_details.partner_entities[0].ownership_pct == 49.0
        assert ou.joint_venture_details.jv_term_years == 10.0
        assert len(ou.joint_venture_details.exit_triggers) == 2

    def test_json_roundtrip(self):
        ou = OrganizationalUnit(
            name="Test Unit",
            unit_id="OU-99999",
            unit_type="Department",
            operational_status="Active",
            employee_count=EmployeeCount(fte=50, total=55),
            hierarchy_memberships=[
                HierarchyMembership(
                    hierarchy_type="Operational",
                    parent_unit_id="OU-00001",
                ),
            ],
            cost_structure=CostStructure(total_annual_cost=2_000_000, fiscal_year="FY2024"),
        )
        data = ou.model_dump()
        ou2 = OrganizationalUnit.model_validate(data)
        assert ou2.unit_id == "OU-99999"
        assert ou2.employee_count.fte == 50
        assert ou2.hierarchy_memberships[0].parent_unit_id == "OU-00001"
        assert ou2.cost_structure.total_annual_cost == 2_000_000

    def test_any_entity_roundtrip(self):
        data = {
            "entity_type": "organizational_unit",
            "name": "Finance & Accounting",
            "unit_id": "OU-00300",
            "unit_type": "Department",
            "functional_domain_primary": "Finance & Accounting",
        }
        entity = _any_entity_adapter.validate_python(data)
        assert isinstance(entity, OrganizationalUnit)
        assert entity.unit_type == "Department"
        assert entity.functional_domain_primary == "Finance & Accounting"

    def test_multi_hierarchy_structure(self):
        """Multi-hierarchy is the core structural concept for org units."""
        ou = OrganizationalUnit(
            name="EMEA Shared Services",
            hierarchy_memberships=[
                HierarchyMembership(
                    hierarchy_type="Legal",
                    parent_unit_id="OU-LEGAL-001",
                    is_root=False,
                ),
                HierarchyMembership(
                    hierarchy_type="Operational",
                    parent_unit_id="OU-OPS-001",
                    is_root=False,
                ),
                HierarchyMembership(
                    hierarchy_type="Financial",
                    parent_unit_id="OU-FIN-001",
                    is_root=False,
                ),
                HierarchyMembership(
                    hierarchy_type="Geographic",
                    parent_unit_id="OU-GEO-EMEA",
                    is_root=True,
                ),
            ],
        )
        assert len(ou.hierarchy_memberships) == 4
        types = [h.hierarchy_type for h in ou.hierarchy_memberships]
        assert "Legal" in types
        assert "Operational" in types
        assert "Financial" in types
        assert "Geographic" in types
        geo = [h for h in ou.hierarchy_memberships if h.hierarchy_type == "Geographic"][0]
        assert geo.is_root is True
