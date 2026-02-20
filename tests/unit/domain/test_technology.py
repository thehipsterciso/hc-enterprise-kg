"""Tests for L02: Technology & Systems entity types.

Covers System (extended) and Integration (new) entities.
Tests construction, sub-model instantiation, and JSON serialization roundtrip.
"""

from pydantic import TypeAdapter

from domain.base import EntityType
from domain.entities import AnyEntity
from domain.entities.integration import (
    CrossesBoundary,
    DataExchanged,
    ErrorHandling,
    Integration,
    IntegrationAvailabilitySLA,
    IntegrationCost,
    IntegrationSecurityProfile,
    LatencyRequirement,
    MiddlewarePlatform,
    SystemRef,
)
from domain.entities.system import (
    ApiSurface,
    AuthenticationMechanism,
    AvailabilitySLA,
    BusinessImpactIfUnavailable,
    CapacityCurrent,
    ChangeVelocity,
    ComplianceCertification,
    ContainerProfile,
    ContractDetails,
    CostBreakdownItem,
    CostOptimizationOpportunity,
    CurrentUsers,
    DataResidencyConstraint,
    EncryptionProfile,
    FitnessScore,
    FormerName,
    IaCProfile,
    IncidentHistory,
    LicenseDetails,
    ObservabilityStack,
    PatchCompliance,
    PenetrationTestStatus,
    ProgrammingLanguage,
    ReplacementCandidate,
    SupportModel,
    System,
    TaxonomyLineage,
    TechStackEntry,
    TotalCostOfOwnership,
    VulnerabilityProfile,
)

_any_entity_adapter = TypeAdapter(AnyEntity)


# ===========================================================================
# System tests (extended)
# ===========================================================================


class TestSystemExtended:
    def test_backward_compat_v01_fields(self):
        """v0.1 System JSON should still parse correctly."""
        data = {
            "entity_type": "system",
            "name": "WebApp",
            "hostname": "web01",
            "criticality": "high",
            "is_internet_facing": True,
            "ports": [80, 443],
        }
        entity = _any_entity_adapter.validate_python(data)
        assert isinstance(entity, System)
        assert entity.hostname == "web01"
        assert entity.criticality == "high"
        assert entity.is_internet_facing is True
        assert entity.ports == [80, 443]

    def test_new_fields_default_empty(self):
        s = System(name="Test System")
        assert s.system_id == ""
        assert s.technology_stack == []
        assert s.encryption_profile.data_at_rest == ""
        assert s.availability_sla.target_uptime_pct is None
        assert s.total_cost_of_ownership.annual_tco is None
        assert s.vulnerability_profile.critical_count is None
        assert s.system_owner == ""

    def test_identity_and_classification(self):
        s = System(
            name="SAP S/4HANA — Global ERP",
            system_id="SY-00142",
            system_name_common="SAP",
            system_name_former=[
                FormerName(
                    former_name="SAP ECC 6.0",
                    from_date="2010-01-01",
                    to_date="2023-06-30",
                    change_reason="Migration to S/4HANA",
                ),
            ],
            system_category="Enterprise Application",
            system_subcategory="ERP",
            deployment_model="Hybrid Cloud",
            hosting_model="Cloud Provider — AWS",
            architecture_type="n-Tier",
            system_tier="Tier 1 — Enterprise Platform",
            origin="Commercial Off-the-Shelf (COTS)",
            procurement_type="Enterprise License Agreement",
            functional_domain_primary="Finance & Accounting",
            functional_domain_secondary=["Supply Chain & Operations"],
            taxonomy_lineage=[
                TaxonomyLineage(
                    framework="TOGAF",
                    framework_element_id="APP-ERP-001",
                    mapping_confidence="Exact Match",
                ),
            ],
        )
        assert s.system_id == "SY-00142"
        assert s.system_name_common == "SAP"
        assert s.system_name_former[0].former_name == "SAP ECC 6.0"
        assert s.system_tier == "Tier 1 — Enterprise Platform"
        assert len(s.taxonomy_lineage) == 1

    def test_technical_profile(self):
        s = System(
            name="API Gateway",
            technology_stack=[
                TechStackEntry(
                    layer="Runtime",
                    technology="Node.js",
                    version="20.11",
                    vendor="OpenJS Foundation",
                ),
            ],
            programming_languages=[
                ProgrammingLanguage(language="TypeScript", version="5.3", usage_type="Primary"),
            ],
            api_surface=ApiSurface(
                api_count=47,
                api_types=["REST", "GraphQL"],
                api_documentation_status="Complete",
            ),
            authentication_mechanisms=[
                AuthenticationMechanism(
                    mechanism="OAuth 2.0",
                    protocol="OIDC",
                    mfa_supported=True,
                    mfa_enforced=True,
                ),
            ],
            encryption_profile=EncryptionProfile(
                data_at_rest="AES-256",
                data_in_transit="TLS 1.3",
                key_management="AWS KMS",
            ),
            containerized=ContainerProfile(
                is_containerized=True,
                container_platform="Docker",
                orchestration_platform="Kubernetes",
            ),
            infrastructure_as_code=IaCProfile(
                iac_enabled=True, iac_tool="Terraform", coverage_pct=95.0
            ),
            observability_stack=ObservabilityStack(
                logging_tool="Datadog",
                monitoring_tool="Datadog",
                tracing_tool="OpenTelemetry",
                alerting_tool="PagerDuty",
            ),
        )
        assert s.technology_stack[0].technology == "Node.js"
        assert s.api_surface.api_count == 47
        assert s.encryption_profile.key_management == "AWS KMS"
        assert s.containerized.orchestration_platform == "Kubernetes"
        assert s.infrastructure_as_code.coverage_pct == 95.0

    def test_operational_profile(self):
        s = System(
            name="Core Banking",
            availability_sla=AvailabilitySLA(
                target_uptime_pct=99.99,
                actual_uptime_pct=99.97,
                sla_breach_count_12m=2,
            ),
            current_users=CurrentUsers(
                total_licensed_users=5000,
                active_users_monthly=3200,
                peak_concurrent=800,
                user_growth_trend="Growing",
            ),
            support_model=SupportModel(
                support_provider="Vendor",
                support_tier="Premium",
                support_hours="24x7",
            ),
            incident_history=IncidentHistory(
                p1_count_12m=1,
                p2_count_12m=4,
                mttr_hours=2.5,
            ),
            change_velocity=ChangeVelocity(
                releases_per_month=4.0,
                deployment_frequency="Weekly",
                change_failure_rate_pct=3.5,
            ),
            capacity_current=CapacityCurrent(
                cpu_utilization_pct=65.0,
                memory_utilization_pct=72.0,
            ),
        )
        assert s.availability_sla.actual_uptime_pct == 99.97
        assert s.current_users.active_users_monthly == 3200
        assert s.change_velocity.change_failure_rate_pct == 3.5
        assert s.capacity_current.cpu_utilization_pct == 65.0

    def test_financial_profile(self):
        s = System(
            name="Salesforce CRM",
            total_cost_of_ownership=TotalCostOfOwnership(
                annual_tco=2_400_000,
                fiscal_year="FY2024",
            ),
            cost_breakdown=[
                CostBreakdownItem(category="License", amount=1_800_000, percentage_of_total=75.0),
                CostBreakdownItem(category="Support", amount=360_000, percentage_of_total=15.0),
            ],
            license_details=LicenseDetails(
                license_type="Per-User",
                license_count=3000,
                licenses_in_use=2400,
                license_utilization_pct=80.0,
            ),
            contract_details=ContractDetails(
                vendor="Salesforce",
                contract_end="2026-12-31",
                annual_value=1_800_000,
                auto_renewal=True,
                notice_period_days=90,
            ),
            cost_optimization_opportunities=[
                CostOptimizationOpportunity(
                    opportunity_description="Reduce unused licenses",
                    estimated_annual_savings=360_000,
                    effort_level="Low",
                    status="Identified",
                ),
            ],
        )
        assert s.total_cost_of_ownership.annual_tco == 2_400_000
        assert len(s.cost_breakdown) == 2
        assert s.license_details.license_utilization_pct == 80.0
        assert s.cost_optimization_opportunities[0].estimated_annual_savings == 360_000

    def test_strategic_importance(self):
        s = System(
            name="Legacy Mainframe",
            business_criticality="Mission Critical",
            strategic_classification="Migrate",
            strategic_classification_rationale="Mainframe skills shortage",
            replacement_candidate=ReplacementCandidate(
                has_replacement_planned=True,
                replacement_system_name="Cloud-native ERP",
                migration_complexity="Very High",
            ),
            business_impact_if_unavailable=BusinessImpactIfUnavailable(
                estimated_financial_impact_per_hour=500_000,
                affected_users=10_000,
            ),
            technical_fitness=FitnessScore(composite_score=2.1),
            business_fitness=FitnessScore(composite_score=4.5),
        )
        assert s.strategic_classification == "Migrate"
        assert s.replacement_candidate.migration_complexity == "Very High"
        assert s.business_impact_if_unavailable.estimated_financial_impact_per_hour == 500_000
        assert s.technical_fitness.composite_score == 2.1

    def test_security_and_compliance(self):
        s = System(
            name="Payment Gateway",
            risk_exposure_inherent="Critical",
            risk_exposure_residual="Medium",
            data_classification_handled=["Restricted", "Confidential"],
            vulnerability_profile=VulnerabilityProfile(
                critical_count=0,
                high_count=2,
                scan_tool="Qualys",
                trend="Improving",
            ),
            penetration_test_status=PenetrationTestStatus(
                last_test_date="2024-09-15",
                test_type="External",
                findings_critical=0,
                findings_high=1,
            ),
            patch_compliance=PatchCompliance(
                compliance_pct=98.0,
                days_to_patch_critical=3,
            ),
            compliance_certifications=[
                ComplianceCertification(
                    certification="PCI DSS",
                    status="Certified",
                ),
            ],
            data_residency_constraints=[
                DataResidencyConstraint(
                    jurisdiction_id="JR-001",
                    data_types=["PAN", "Cardholder Data"],
                    residency_requirement="Must remain in-region",
                ),
            ],
        )
        assert s.risk_exposure_inherent == "Critical"
        assert s.vulnerability_profile.high_count == 2
        assert s.patch_compliance.compliance_pct == 98.0
        assert s.compliance_certifications[0].certification == "PCI DSS"
        assert len(s.data_residency_constraints) == 1

    def test_json_roundtrip(self):
        s = System(
            name="Test System",
            system_id="SY-99999",
            hostname="test01",
            technology_stack=[
                TechStackEntry(layer="OS", technology="Linux", version="Ubuntu 22.04"),
            ],
            encryption_profile=EncryptionProfile(data_at_rest="AES-256"),
            total_cost_of_ownership=TotalCostOfOwnership(annual_tco=100_000),
        )
        data = s.model_dump()
        s2 = System.model_validate(data)
        assert s2.system_id == "SY-99999"
        assert s2.hostname == "test01"
        assert s2.technology_stack[0].technology == "Linux"
        assert s2.encryption_profile.data_at_rest == "AES-256"
        assert s2.total_cost_of_ownership.annual_tco == 100_000

    def test_any_entity_roundtrip(self):
        data = {
            "entity_type": "system",
            "name": "SCADA Controller",
            "system_id": "SY-00500",
            "system_category": "OT/ICS System",
            "network_zone": "OT",
        }
        entity = _any_entity_adapter.validate_python(data)
        assert isinstance(entity, System)
        assert entity.system_category == "OT/ICS System"
        assert entity.network_zone == "OT"


# ===========================================================================
# Integration tests
# ===========================================================================


class TestIntegration:
    def test_minimal_construction(self):
        i = Integration(name="SAP-to-Warehouse")
        assert i.entity_type == EntityType.INTEGRATION
        assert i.integration_id == ""
        assert i.source_systems == []

    def test_full_construction(self):
        i = Integration(
            name="SAP S/4HANA → Snowflake Data Warehouse",
            integration_id="IN-00001",
            integration_type="API",
            integration_pattern="Batch",
            source_systems=[
                SystemRef(system_id="SY-00142", system_name="SAP S/4HANA"),
            ],
            target_systems=[
                SystemRef(system_id="SY-00200", system_name="Snowflake"),
            ],
            direction="Unidirectional",
            middleware_platform=MiddlewarePlatform(
                platform_name="MuleSoft Anypoint",
                platform_system_id="SY-00050",
                managed_by="Integration Team",
            ),
            data_exchanged=DataExchanged(
                data_description="Financial GL journal entries",
                data_classification="Confidential",
                data_domains=["Finance", "Accounting"],
                volume_per_day="2.5 GB",
                record_count_per_day=500_000,
            ),
            frequency="Daily",
            latency_requirement=LatencyRequirement(
                max_acceptable_ms=300_000,
                actual_p95_ms=180_000,
                meets_requirement=True,
            ),
            error_handling=ErrorHandling(
                retry_mechanism="Exponential Backoff",
                dead_letter_queue=True,
                alerting=True,
                error_rate_pct=0.02,
            ),
            availability_sla=IntegrationAvailabilitySLA(
                target_uptime_pct=99.9,
                actual_uptime_pct=99.95,
            ),
            operational_status="Active",
            security_profile=IntegrationSecurityProfile(
                authentication="OAuth 2.0",
                encryption_in_transit=True,
                encryption_protocol="TLS 1.3",
                rate_limiting=True,
            ),
            crosses_boundary=CrossesBoundary(
                crosses_network_boundary=True,
                boundary_type="Cloud/On-Prem",
                crosses_jurisdiction=True,
                source_jurisdiction="EU",
                target_jurisdiction="US",
                cross_border_transfer_mechanism="SCCs",
            ),
            owner="Integration Architect",
            integration_support_team="Enterprise Integration Team",
            annual_cost=IntegrationCost(
                amount=85_000,
                cost_components=["MuleSoft license", "CloudHub workers"],
            ),
            monitoring_status="Fully Monitored",
            effective_date="2023-06-15",
        )
        assert i.integration_id == "IN-00001"
        assert i.source_systems[0].system_name == "SAP S/4HANA"
        assert i.data_exchanged.record_count_per_day == 500_000
        assert i.latency_requirement.meets_requirement is True
        assert i.error_handling.dead_letter_queue is True
        assert i.security_profile.encryption_protocol == "TLS 1.3"
        assert i.crosses_boundary.crosses_jurisdiction is True
        assert i.crosses_boundary.cross_border_transfer_mechanism == "SCCs"
        assert i.annual_cost.amount == 85_000

    def test_json_roundtrip(self):
        i = Integration(
            name="CRM to Marketing",
            integration_id="IN-00010",
            integration_type="Event Stream",
            integration_pattern="Pub-Sub",
            source_systems=[SystemRef(system_id="SY-001", system_name="Salesforce")],
            target_systems=[SystemRef(system_id="SY-002", system_name="Marketo")],
        )
        data = i.model_dump()
        i2 = Integration.model_validate(data)
        assert i2.integration_id == "IN-00010"
        assert i2.integration_pattern == "Pub-Sub"
        assert i2.source_systems[0].system_name == "Salesforce"

    def test_any_entity_roundtrip(self):
        data = {
            "entity_type": "integration",
            "name": "SCADA to Historian",
            "integration_id": "IN-00020",
            "integration_type": "OPC-UA",
            "direction": "Unidirectional",
        }
        entity = _any_entity_adapter.validate_python(data)
        assert isinstance(entity, Integration)
        assert entity.integration_type == "OPC-UA"

    def test_boundary_crossing_defaults(self):
        i = Integration(name="Internal sync")
        assert i.crosses_boundary.crosses_network_boundary is False
        assert i.crosses_boundary.crosses_jurisdiction is False
        assert i.security_profile.encryption_in_transit is False
