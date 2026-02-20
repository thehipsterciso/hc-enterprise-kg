"""Tests for L03: Data Assets entity types.

Covers DataAsset (extended), DataDomain (new), and DataFlow (new) entities.
Tests construction, sub-model instantiation, and JSON serialization roundtrip.
"""

from pydantic import TypeAdapter

from domain.base import EntityType
from domain.entities import AnyEntity
from domain.entities.data_asset import (
    AccessGovernance,
    AcquisitionSource,
    AITrainingUsage,
    AnonymizationStatus,
    BreachNotificationObligation,
    CatalogStatus,
    ConsentManagement,
    CrossBorderTransferStatus,
    CurrentAccessGrants,
    DataAsset,
    DataCostItem,
    DataCostOptimization,
    DataMaskingConfig,
    DataValueAssessment,
    DataVolume,
    EncryptionAtRest,
    FitnessForPurpose,
    GoldenRecordStatus,
    LineageEntry,
    PrivacyImpactAssessment,
    QualityDimension,
    QualityIssue,
    QualityMonitoring,
    QualityRule,
    QualityScoreComposite,
    ReplicationConfig,
    RetentionCompliance,
    StorageFormat,
    StorageTechnology,
    ThirdPartySharing,
    TotalDataCost,
)
from domain.entities.data_domain import (
    BusinessGlossaryReference,
    DataDomain,
    DataResidencyRequirement,
    GoverningPolicy,
    MaturityDimension,
    MonetizationPotential,
    QualityTargets,
    RegulatorySensitivity,
    RetentionPolicy,
    SensitivityFlags,
    SubDomain,
)
from domain.entities.data_flow import (
    DataFlow,
    FlowCost,
    FlowEndpoint,
    FlowErrorRate,
    FlowJurisdictionCrossing,
    FlowLatency,
    FlowSLA,
    FlowVolume,
    QualityGate,
    TransformationLogic,
)

_any_entity_adapter = TypeAdapter(AnyEntity)


# ===========================================================================
# DataAsset tests (extended)
# ===========================================================================


class TestDataAssetExtended:
    def test_backward_compat_v01_fields(self):
        """v0.1 DataAsset JSON should still parse correctly."""
        data = {
            "entity_type": "data_asset",
            "name": "Customer DB",
            "data_type": "pii",
            "classification": "confidential",
            "format": "sql",
            "retention_days": 365,
            "is_encrypted": True,
            "owner_id": "person-001",
            "system_id": "sys-001",
            "record_count": 1_000_000,
            "regulations": ["GDPR", "CCPA"],
        }
        entity = _any_entity_adapter.validate_python(data)
        assert isinstance(entity, DataAsset)
        assert entity.data_type == "pii"
        assert entity.classification == "confidential"
        assert entity.is_encrypted is True
        assert entity.record_count == 1_000_000
        assert entity.regulations == ["GDPR", "CCPA"]

    def test_new_fields_default_empty(self):
        da = DataAsset(name="Test Asset")
        assert da.asset_id == ""
        assert da.asset_type == ""
        assert da.quality_trend == ""
        assert da.storage_technology.system_id == ""
        assert da.encryption_at_rest.encrypted is False
        assert da.quality_score_composite.score is None
        assert da.retention_compliance.legal_hold_flag is False
        assert da.ai_training_usage.used_for_ai_training is False
        assert da.total_data_cost.annual_total is None

    def test_identity_and_classification(self):
        da = DataAsset(
            name="Customer Master Data — Global",
            asset_id="DA-00100",
            asset_name_common="Customer MDM",
            asset_type="Master Data Repository",
            asset_subtype="Customer",
            data_domain_primary="DD-00001",
            data_domain_secondary=["DD-00005"],
            data_classification="Confidential",
            pii_categories=["Name", "Email", "Phone"],
            data_format="Structured",
            origin="Organic — Internal Generation",
            acquisition_source=AcquisitionSource(
                source_name="CRM System",
                acquisition_date="2020-01-15",
            ),
            functional_domain_primary="Sales & Marketing",
        )
        assert da.asset_id == "DA-00100"
        assert da.asset_type == "Master Data Repository"
        assert da.data_domain_primary == "DD-00001"
        assert len(da.pii_categories) == 3
        assert da.acquisition_source.source_name == "CRM System"

    def test_data_architecture(self):
        da = DataAsset(
            name="Data Warehouse — Finance",
            storage_technology=StorageTechnology(
                system_id="SY-00200",
                system_name="Snowflake",
                storage_service="snowflake-warehouse",
            ),
            storage_format=StorageFormat(
                format_type="Parquet",
                schema_definition_exists=True,
                schema_evolution_strategy="Backward Compatible",
            ),
            volume=DataVolume(
                current_size=2.5,
                size_unit="TB",
                growth_rate_monthly_pct=3.0,
            ),
            replication=ReplicationConfig(
                is_replicated=True,
                replication_type="Asynchronous",
                replica_locations=["us-east-1", "eu-west-1"],
            ),
            encryption_at_rest=EncryptionAtRest(
                encrypted=True,
                algorithm="AES-256",
                key_management="Cloud KMS",
            ),
            data_masking=DataMaskingConfig(
                masking_applied=True,
                masking_type="Dynamic Masking",
                masked_fields=["ssn", "credit_card"],
            ),
        )
        assert da.storage_technology.system_name == "Snowflake"
        assert da.storage_format.schema_evolution_strategy == "Backward Compatible"
        assert da.volume.current_size == 2.5
        assert da.replication.replica_locations == ["us-east-1", "eu-west-1"]
        assert da.encryption_at_rest.key_management == "Cloud KMS"
        assert da.data_masking.masked_fields == ["ssn", "credit_card"]

    def test_data_quality(self):
        da = DataAsset(
            name="Product Catalog",
            quality_score_composite=QualityScoreComposite(score=4.2, assessed_date="2024-09-01"),
            quality_dimensions=[
                QualityDimension(
                    dimension="Completeness",
                    score=95.0,
                    threshold=90.0,
                    meets_threshold=True,
                ),
                QualityDimension(
                    dimension="Accuracy",
                    score=88.0,
                    threshold=95.0,
                    meets_threshold=False,
                ),
            ],
            quality_rules=[
                QualityRule(
                    rule_id="QR-001",
                    rule_type="Completeness Check",
                    pass_rate_pct=98.5,
                    automated=True,
                ),
            ],
            quality_trend="Improving",
            quality_issues_open=[
                QualityIssue(
                    issue_id="QI-001",
                    severity="Medium",
                    affected_records_pct=2.5,
                    remediation_status="In Progress",
                ),
            ],
            quality_monitoring=QualityMonitoring(
                automated_monitoring=True,
                monitoring_tool="Great Expectations",
                alerting_configured=True,
            ),
            golden_record_status=GoldenRecordStatus(
                is_golden_source=True,
                conflict_resolution_method="Most Recent Wins",
            ),
            fitness_for_purpose=[
                FitnessForPurpose(
                    use_case="Pricing Engine",
                    fitness_rating="Fit",
                ),
            ],
        )
        assert da.quality_score_composite.score == 4.2
        assert len(da.quality_dimensions) == 2
        assert da.quality_dimensions[1].meets_threshold is False
        assert da.quality_rules[0].automated is True
        assert da.quality_trend == "Improving"
        assert da.quality_monitoring.monitoring_tool == "Great Expectations"
        assert da.golden_record_status.is_golden_source is True

    def test_governance_and_lineage(self):
        da = DataAsset(
            name="Sales Transactions",
            data_owner="Chief Revenue Officer",
            data_steward="Sales Data Steward",
            data_custodian="DBA Team Lead",
            access_governance=AccessGovernance(
                access_request_process="ServiceNow",
                approval_authority="Data Owner",
                access_review_frequency="Quarterly",
            ),
            access_control_model="RBAC",
            current_access_grants=CurrentAccessGrants(
                total_users_with_access=250,
                roles_with_access=["Sales Analyst", "Finance Analyst"],
            ),
            consent_management=ConsentManagement(
                requires_consent=True,
                consent_type="Contractual Basis",
            ),
            lineage_upstream=[
                LineageEntry(
                    asset_id="DA-00050",
                    asset_name="CRM Raw",
                    transformation_type="Mapping",
                    refresh_frequency="Daily",
                ),
            ],
            lineage_downstream=[
                LineageEntry(
                    asset_id="DA-00200",
                    asset_name="Revenue Dashboard",
                    transformation_type="Aggregation",
                    dependency_strength="Strong",
                ),
            ],
            lineage_completeness="Substantially Documented",
            catalog_status=CatalogStatus(
                cataloged=True,
                catalog_platform="Alation",
                metadata_completeness_pct=85.0,
            ),
            retention_compliance=RetentionCompliance(
                policy_reference="POL-RET-001",
                required_retention="7 years",
                actual_retention="7 years",
                compliant=True,
            ),
        )
        assert da.data_owner == "Chief Revenue Officer"
        assert da.access_control_model == "RBAC"
        assert da.current_access_grants.total_users_with_access == 250
        assert da.lineage_upstream[0].transformation_type == "Mapping"
        assert da.lineage_downstream[0].dependency_strength == "Strong"
        assert da.catalog_status.metadata_completeness_pct == 85.0
        assert da.retention_compliance.compliant is True

    def test_regulatory_compliance(self):
        da = DataAsset(
            name="Employee PII Store",
            cross_border_transfer_status=CrossBorderTransferStatus(
                data_crosses_borders=True,
                source_jurisdictions=["EU"],
                destination_jurisdictions=["US"],
                transfer_mechanisms=["SCCs"],
                compliant=True,
            ),
            data_subject_rights_applicable=True,
            privacy_impact_assessment=PrivacyImpactAssessment(
                pia_required=True,
                pia_completed=True,
                pia_date="2024-06-15",
            ),
            breach_notification_obligation=BreachNotificationObligation(
                applicable=True,
                notification_timeframe_hours=72,
                authority_notification=True,
                individual_notification=True,
                jurisdiction="EU",
            ),
            third_party_sharing=[
                ThirdPartySharing(
                    third_party_name="Payroll Provider",
                    sharing_purpose="Payroll Processing",
                    legal_basis="Contractual Basis",
                    data_types_shared=["Name", "Salary", "Bank Details"],
                ),
            ],
            ai_training_usage=AITrainingUsage(
                used_for_ai_training=True,
                model_references=["ML-001"],
                bias_assessment_completed=True,
                eu_ai_act_risk_category="Limited",
            ),
            anonymization_status=AnonymizationStatus(
                anonymized=False,
                anonymization_method="",
                re_identification_risk_level="Medium",
            ),
        )
        assert da.cross_border_transfer_status.transfer_mechanisms == ["SCCs"]
        assert da.data_subject_rights_applicable is True
        assert da.privacy_impact_assessment.pia_completed is True
        assert da.breach_notification_obligation.notification_timeframe_hours == 72
        assert da.third_party_sharing[0].data_types_shared == ["Name", "Salary", "Bank Details"]
        assert da.ai_training_usage.eu_ai_act_risk_category == "Limited"

    def test_financial_profile(self):
        da = DataAsset(
            name="Market Data Feed",
            storage_cost=DataCostItem(annual_cost=120_000, cost_driver="Volume"),
            processing_cost=DataCostItem(annual_cost=80_000, cost_driver="Compute"),
            value_assessment=DataValueAssessment(
                estimated_value=5_000_000,
                valuation_method="Revenue Attribution",
                confidence="High",
            ),
            cost_optimization_opportunities=[
                DataCostOptimization(
                    opportunity_description="Move cold data to glacier",
                    estimated_annual_savings=40_000,
                    effort_level="Moderate Effort",
                    status="Approved",
                ),
            ],
            total_data_cost=TotalDataCost(annual_total=200_000),
        )
        assert da.storage_cost.annual_cost == 120_000
        assert da.processing_cost.cost_driver == "Compute"
        assert da.value_assessment.estimated_value == 5_000_000
        assert da.cost_optimization_opportunities[0].estimated_annual_savings == 40_000
        assert da.total_data_cost.annual_total == 200_000

    def test_json_roundtrip(self):
        da = DataAsset(
            name="Test Asset",
            asset_id="DA-99999",
            data_type="financial",
            classification="restricted",
            quality_score_composite=QualityScoreComposite(score=3.8),
            storage_technology=StorageTechnology(system_id="SY-001", system_name="Postgres"),
            encryption_at_rest=EncryptionAtRest(encrypted=True, algorithm="AES-256"),
            total_data_cost=TotalDataCost(annual_total=50_000),
        )
        data = da.model_dump()
        da2 = DataAsset.model_validate(data)
        assert da2.asset_id == "DA-99999"
        assert da2.data_type == "financial"
        assert da2.quality_score_composite.score == 3.8
        assert da2.storage_technology.system_name == "Postgres"
        assert da2.encryption_at_rest.encrypted is True
        assert da2.total_data_cost.annual_total == 50_000

    def test_any_entity_roundtrip(self):
        data = {
            "entity_type": "data_asset",
            "name": "Clickstream Data Lake",
            "asset_id": "DA-00500",
            "asset_type": "Data Lake Zone",
            "data_format": "Semi-Structured",
        }
        entity = _any_entity_adapter.validate_python(data)
        assert isinstance(entity, DataAsset)
        assert entity.asset_type == "Data Lake Zone"
        assert entity.data_format == "Semi-Structured"


# ===========================================================================
# DataDomain tests
# ===========================================================================


class TestDataDomain:
    def test_minimal_construction(self):
        dd = DataDomain(name="Customer Data")
        assert dd.entity_type == EntityType.DATA_DOMAIN
        assert dd.domain_id == ""
        assert dd.sub_domains == []
        assert dd.sensitivity_flags.pii_flag is False

    def test_full_construction(self):
        dd = DataDomain(
            name="Finance & Accounting Data",
            domain_id="DD-00002",
            domain_type="Transactional Data",
            domain_scope="Enterprise-Wide",
            sub_domains=[
                SubDomain(
                    sub_domain_name="General Ledger",
                    sub_domain_description="GL journal entries and chart of accounts",
                ),
                SubDomain(
                    sub_domain_name="Accounts Payable",
                    sub_domain_description="Vendor invoices and payment records",
                ),
            ],
            business_glossary_reference=BusinessGlossaryReference(
                glossary_platform="Collibra",
                term_count=450,
                last_updated="2024-08-01",
            ),
            domain_owner="Chief Financial Officer",
            domain_steward="Finance Data Steward",
            governing_policies=[
                GoverningPolicy(
                    policy_id="POL-001",
                    policy_name="Data Retention Policy",
                    policy_type="Data Retention Policy",
                ),
            ],
            data_classification="Confidential",
            sensitivity_flags=SensitivityFlags(
                financial_data_flag=True,
                pii_flag=True,
            ),
            regulatory_sensitivity=[
                RegulatorySensitivity(
                    regulation="SOX",
                    sensitivity_description="Financial reporting data",
                    handling_requirements="7-year retention",
                ),
            ],
            data_residency_requirements=[
                DataResidencyRequirement(
                    jurisdiction_id="JR-001",
                    jurisdiction_name="United States",
                    localization_required=True,
                    compliant=True,
                ),
            ],
            retention_policy=RetentionPolicy(
                minimum_retention="7 years",
                minimum_retention_basis="SOX Requirement",
                destruction_method="Cryptographic Erasure",
                legal_hold_status="No Active Hold",
            ),
            quality_targets=QualityTargets(
                completeness_target_pct=99.0,
                accuracy_target_pct=99.5,
                current_composite_score=4.3,
                meets_targets=True,
            ),
            maturity_level="Managed",
            maturity_dimensions=[
                MaturityDimension(
                    dimension="Data Governance",
                    score=4.0,
                    assessed_date="2024-06-01",
                ),
                MaturityDimension(
                    dimension="Data Quality Management",
                    score=4.5,
                    assessed_date="2024-06-01",
                ),
            ],
            strategic_value="Compliance Required",
            monetization_potential=MonetizationPotential(
                potential_type="Process Optimization",
                estimated_annual_value=500_000,
                confidence="Medium — Modeled",
            ),
        )
        assert dd.domain_id == "DD-00002"
        assert dd.domain_type == "Transactional Data"
        assert len(dd.sub_domains) == 2
        assert dd.sub_domains[0].sub_domain_name == "General Ledger"
        assert dd.business_glossary_reference.term_count == 450
        assert dd.governing_policies[0].policy_type == "Data Retention Policy"
        assert dd.sensitivity_flags.financial_data_flag is True
        assert dd.regulatory_sensitivity[0].regulation == "SOX"
        assert dd.data_residency_requirements[0].compliant is True
        assert dd.retention_policy.destruction_method == "Cryptographic Erasure"
        assert dd.quality_targets.current_composite_score == 4.3
        assert len(dd.maturity_dimensions) == 2
        assert dd.monetization_potential.estimated_annual_value == 500_000

    def test_json_roundtrip(self):
        dd = DataDomain(
            name="Customer Data",
            domain_id="DD-00001",
            domain_type="Master Data",
            domain_scope="Enterprise-Wide",
            sensitivity_flags=SensitivityFlags(pii_flag=True, phi_flag=True),
            quality_targets=QualityTargets(completeness_target_pct=95.0),
        )
        data = dd.model_dump()
        dd2 = DataDomain.model_validate(data)
        assert dd2.domain_id == "DD-00001"
        assert dd2.domain_type == "Master Data"
        assert dd2.sensitivity_flags.pii_flag is True
        assert dd2.sensitivity_flags.phi_flag is True
        assert dd2.quality_targets.completeness_target_pct == 95.0

    def test_any_entity_roundtrip(self):
        data = {
            "entity_type": "data_domain",
            "name": "HR Data",
            "domain_id": "DD-00010",
            "domain_type": "Operational Data",
            "strategic_value": "Compliance Required",
        }
        entity = _any_entity_adapter.validate_python(data)
        assert isinstance(entity, DataDomain)
        assert entity.domain_type == "Operational Data"
        assert entity.strategic_value == "Compliance Required"


# ===========================================================================
# DataFlow tests
# ===========================================================================


class TestDataFlow:
    def test_minimal_construction(self):
        df = DataFlow(name="CRM to Warehouse")
        assert df.entity_type == EntityType.DATA_FLOW
        assert df.flow_id == ""
        assert df.source_assets == []
        assert df.crosses_jurisdiction.crosses_border is False

    def test_full_construction(self):
        df = DataFlow(
            name="SAP GL → Snowflake Finance DW (Daily Batch)",
            flow_id="DF-00001",
            flow_type="Ingestion",
            source_assets=[
                FlowEndpoint(asset_id="DA-00100", system_id="SY-00142"),
            ],
            target_assets=[
                FlowEndpoint(asset_id="DA-00200", system_id="SY-00200"),
            ],
            transformation_logic=TransformationLogic(
                description="Extract GL journal entries, map to unified COA",
                complexity="Moderate",
                transformation_type="Mapping",
            ),
            data_classification_in_flow="Confidential",
            volume_per_execution=FlowVolume(records=500_000, size=2.5, size_unit="GB"),
            frequency="Daily",
            latency=FlowLatency(target_ms=300_000, actual_p95_ms=180_000, meets_target=True),
            quality_gates=[
                QualityGate(
                    gate_type="Completeness Check",
                    rule_description="All required GL fields populated",
                    pass_rate_pct=99.8,
                    action_on_failure="Quarantine",
                ),
                QualityGate(
                    gate_type="Referential Integrity",
                    rule_description="All cost centers exist in COA",
                    pass_rate_pct=100.0,
                    action_on_failure="Reject Record",
                ),
            ],
            crosses_jurisdiction=FlowJurisdictionCrossing(
                crosses_border=True,
                source_jurisdiction_id="JR-EU",
                target_jurisdiction_id="JR-US",
                transfer_mechanism="SCCs",
                compliant=True,
            ),
            integration_references=["IN-00001"],
            owner="Finance Data Engineer",
            support_team="Data Platform Team",
            operational_status="Active",
            error_rate=FlowErrorRate(current_pct=0.02, threshold_pct=1.0, trend="Stable"),
            monitoring_status="Fully Monitored",
            sla=FlowSLA(
                freshness_target="T+1 Day",
                completeness_target_pct=99.5,
                actual_freshness="T+1 Day",
                actual_completeness_pct=99.8,
                meets_sla=True,
            ),
            annual_cost=FlowCost(
                amount=45_000,
                cost_components=["Snowflake compute", "Fivetran license"],
            ),
        )
        assert df.flow_id == "DF-00001"
        assert df.flow_type == "Ingestion"
        assert df.source_assets[0].system_id == "SY-00142"
        assert df.transformation_logic.complexity == "Moderate"
        assert df.volume_per_execution.records == 500_000
        assert df.latency.meets_target is True
        assert len(df.quality_gates) == 2
        assert df.quality_gates[0].action_on_failure == "Quarantine"
        assert df.crosses_jurisdiction.transfer_mechanism == "SCCs"
        assert df.integration_references == ["IN-00001"]
        assert df.error_rate.current_pct == 0.02
        assert df.sla.meets_sla is True
        assert df.annual_cost.amount == 45_000

    def test_json_roundtrip(self):
        df = DataFlow(
            name="CDC Sync",
            flow_id="DF-00010",
            flow_type="CDC (Change Data Capture)",
            frequency="Real-Time",
            source_assets=[FlowEndpoint(asset_id="DA-001", system_id="SY-001")],
            target_assets=[FlowEndpoint(asset_id="DA-002", system_id="SY-002")],
        )
        data = df.model_dump()
        df2 = DataFlow.model_validate(data)
        assert df2.flow_id == "DF-00010"
        assert df2.flow_type == "CDC (Change Data Capture)"
        assert df2.frequency == "Real-Time"
        assert df2.source_assets[0].asset_id == "DA-001"

    def test_any_entity_roundtrip(self):
        data = {
            "entity_type": "data_flow",
            "name": "Export to Partner",
            "flow_id": "DF-00020",
            "flow_type": "Export to Third Party",
            "frequency": "Weekly",
        }
        entity = _any_entity_adapter.validate_python(data)
        assert isinstance(entity, DataFlow)
        assert entity.flow_type == "Export to Third Party"
        assert entity.frequency == "Weekly"

    def test_jurisdiction_crossing_defaults(self):
        df = DataFlow(name="Internal sync")
        assert df.crosses_jurisdiction.crosses_border is False
        assert df.crosses_jurisdiction.compliant is None
        assert df.error_rate.current_pct is None
        assert df.sla.meets_sla is None
