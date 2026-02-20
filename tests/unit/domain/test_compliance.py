"""Tests for L01: Compliance & Governance entity types.

Covers Regulation, Policy (extended), Control, Risk, and Threat entities.
Tests construction, sub-model instantiation, and JSON serialization roundtrip.
"""

from pydantic import TypeAdapter

from domain.base import EntityType
from domain.entities import AnyEntity
from domain.entities.control import (
    ApplicabilityDimensions,
    AutomationDetails,
    Control,
    ControlEffectiveness,
    ControlException,
    ControlKPI,
    EvidenceRequirements,
    FrameworkMapping,
    GapStatus,
    PolicyRef,
    RegulationMapping,
    RiskMitigation,
    TestingApproach,
)
from domain.entities.policy import (
    CommunicationPlan,
    ComplianceMeasurement,
    EnforcementMechanism,
    Policy,
    PolicyAppliesTo,
    PolicyException,
    PolicyRequirement,
    PolicyVersion,
    RegulatoryDriver,
    RelatedPolicy,
    RiskDriver,
    TrainingRequirement,
)
from domain.entities.regulation import (
    ApplicabilityCriteria,
    ApplicabilityTrigger,
    ComplianceGap,
    ComplianceStatus,
    IssuingBody,
    JurisdictionRef,
    KeyRequirement,
    MonitoringApproach,
    Penalties,
    Regulation,
    RegulatoryChange,
)
from domain.entities.risk import (
    AcceptanceRecord,
    ControlEffectivenessOnRisk,
    FinancialImpact,
    ImpactDimensions,
    KeyRiskIndicator,
    LossEvent,
    Risk,
    RiskInterconnection,
    RiskScenario,
    RiskTaxonomyRef,
    RiskTolerance,
    TransferRecord,
    TreatmentPlan,
)
from domain.entities.threat import (
    GeographicApplicability,
    HistoricalFrequency,
    IndustryApplicability,
    RelatedThreat,
    SeasonalPattern,
    Threat,
    ThreatControlLink,
    ThreatRiskLink,
    ThreatTaxonomyRef,
)

_any_entity_adapter = TypeAdapter(AnyEntity)


# ===========================================================================
# Regulation tests
# ===========================================================================


class TestRegulation:
    def test_minimal_construction(self):
        reg = Regulation(name="GDPR")
        assert reg.entity_type == EntityType.REGULATION
        assert reg.name == "GDPR"
        assert reg.regulation_id == ""
        assert reg.compliance_gaps == []

    def test_full_construction(self):
        reg = Regulation(
            name="General Data Protection Regulation",
            regulation_id="RG-00001",
            short_name="GDPR",
            regulation_type="Law / Statute",
            regulation_category="Data Privacy",
            issuing_body=IssuingBody(
                body_name="European Union",
                body_type="Supranational Body",
                jurisdiction="EU",
            ),
            jurisdictions=[
                JurisdictionRef(
                    jurisdiction_id="JR-00001",
                    jurisdiction_name="European Union",
                ),
            ],
            applicability_criteria=ApplicabilityCriteria(
                criteria_description="Processes personal data of EU residents",
                triggers=[
                    ApplicabilityTrigger(
                        trigger_type="Data Types Processed",
                        trigger_description="Personal data of EU data subjects",
                    ),
                ],
            ),
            applicability_status="Applicable",
            effective_date="2018-05-25",
            key_requirements=[
                KeyRequirement(
                    requirement_id="GDPR-A6",
                    requirement_description="Lawful basis for processing",
                    requirement_category="Administrative",
                ),
            ],
            penalties=Penalties(
                penalty_type="Financial",
                maximum_penalty="4% of global annual turnover or €20M",
                penalty_basis="Per violation",
            ),
            compliance_status=ComplianceStatus(
                status="Substantially Compliant",
                last_assessed="2024-06-15",
                assessed_by="External Counsel",
                next_assessment="2025-06-15",
            ),
            compliance_gaps=[
                ComplianceGap(
                    gap_description="Cookie consent not fully automated",
                    severity="Medium",
                    remediation_status="In Progress",
                ),
            ],
            monitoring_approach=MonitoringApproach(
                method="Regulatory Intelligence Service",
                frequency="Monthly",
                automated=True,
            ),
            regulatory_change_pipeline=[
                RegulatoryChange(
                    change_description="ePrivacy Regulation adoption",
                    expected_effective_date="2025-12-01",
                    impact_assessment="Moderate impact on cookie policy",
                    readiness="On Track",
                ),
            ],
        )
        assert reg.regulation_id == "RG-00001"
        assert reg.issuing_body.body_name == "European Union"
        assert len(reg.jurisdictions) == 1
        assert reg.applicability_criteria.triggers[0].trigger_type == "Data Types Processed"
        assert reg.penalties.maximum_penalty == "4% of global annual turnover or €20M"
        assert reg.compliance_status.status == "Substantially Compliant"
        assert len(reg.compliance_gaps) == 1
        assert reg.monitoring_approach.automated is True
        assert len(reg.regulatory_change_pipeline) == 1

    def test_json_roundtrip(self):
        reg = Regulation(
            name="SOX",
            regulation_id="RG-00002",
            regulation_type="Law / Statute",
            compliance_status=ComplianceStatus(status="Compliant"),
        )
        data = reg.model_dump()
        reg2 = Regulation.model_validate(data)
        assert reg2.regulation_id == "RG-00002"
        assert reg2.compliance_status.status == "Compliant"

    def test_any_entity_roundtrip(self):
        data = {
            "entity_type": "regulation",
            "name": "PCI DSS",
            "regulation_id": "RG-00003",
            "regulation_category": "Cybersecurity",
        }
        entity = _any_entity_adapter.validate_python(data)
        assert isinstance(entity, Regulation)
        assert entity.regulation_category == "Cybersecurity"


# ===========================================================================
# Policy tests (extended)
# ===========================================================================


class TestPolicyExtended:
    def test_backward_compat_v01_fields(self):
        """v0.1 Policy JSON should still parse correctly."""
        data = {
            "entity_type": "policy",
            "name": "Access Control",
            "is_enforced": True,
            "severity": "high",
            "framework": "NIST",
        }
        entity = _any_entity_adapter.validate_python(data)
        assert isinstance(entity, Policy)
        assert entity.is_enforced is True
        assert entity.severity == "high"
        assert entity.framework == "NIST"

    def test_new_fields_default_empty(self):
        p = Policy(name="Test Policy")
        assert p.policy_id == ""
        assert p.driven_by_regulations == []
        assert p.applies_to.org_units == []
        assert p.exceptions == []
        assert p.enforcement_mechanism.mechanism_type == ""

    def test_full_construction(self):
        p = Policy(
            name="Enterprise Data Classification Policy",
            policy_id="PL-00001",
            policy_type="Data Classification",
            policy_scope="Enterprise-Wide",
            policy_status="Active",
            policy_owner="CISO",
            approving_authority="Board of Directors",
            effective_date="2024-01-01",
            review_cadence="Annual",
            next_review_date="2025-01-01",
            current_version=PolicyVersion(
                version="3.0",
                effective_date="2024-01-01",
                change_summary="Added AI data classification",
            ),
            driven_by_regulations=[
                RegulatoryDriver(
                    regulation_id="RG-00001",
                    regulation_name="GDPR",
                    specific_requirements=["Article 5", "Article 9"],
                ),
            ],
            driven_by_risks=[
                RiskDriver(
                    risk_id="RS-00001",
                    risk_description="Data breach risk",
                    risk_level="High",
                ),
            ],
            policy_requirements=[
                PolicyRequirement(
                    requirement_id="PL-00001-R1",
                    requirement_description="All data must be classified",
                    requirement_type="Mandatory",
                ),
            ],
            applies_to=PolicyAppliesTo(
                org_units=["OU-001", "OU-002"],
                systems=["SYS-001"],
                data_domains=["DD-001"],
            ),
            exceptions=[
                PolicyException(
                    exception_id="EX-001",
                    description="Legacy system exemption",
                    approved_by="CISO",
                    expiration_date="2025-06-30",
                ),
            ],
            enforcement_mechanism=EnforcementMechanism(
                mechanism_type="Technical Control",
                automated=True,
            ),
            compliance_measurement=ComplianceMeasurement(
                metric="Classification coverage",
                target="100%",
                current_value="87%",
            ),
            training_requirement=TrainingRequirement(
                required=True,
                training_program="Data Classification 101",
                completion_target_pct=95.0,
                current_completion_pct=89.0,
            ),
            communication_plan=CommunicationPlan(
                acknowledgment_required=True,
                acknowledgment_rate_pct=92.0,
            ),
            related_policies=[
                RelatedPolicy(
                    policy_id="PL-00002",
                    relationship_type="Parent",
                ),
            ],
        )
        assert p.policy_id == "PL-00001"
        assert p.current_version.version == "3.0"
        assert len(p.driven_by_regulations) == 1
        assert p.applies_to.org_units == ["OU-001", "OU-002"]
        assert p.training_requirement.current_completion_pct == 89.0
        assert p.communication_plan.acknowledgment_rate_pct == 92.0

    def test_json_roundtrip(self):
        p = Policy(
            name="Test",
            policy_id="PL-00099",
            driven_by_regulations=[
                RegulatoryDriver(regulation_id="RG-1", regulation_name="GDPR"),
            ],
        )
        data = p.model_dump()
        p2 = Policy.model_validate(data)
        assert p2.policy_id == "PL-00099"
        assert p2.driven_by_regulations[0].regulation_name == "GDPR"


# ===========================================================================
# Control tests
# ===========================================================================


class TestControl:
    def test_minimal_construction(self):
        c = Control(name="Encryption at Rest")
        assert c.entity_type == EntityType.CONTROL
        assert c.control_id == ""
        assert c.maps_to_frameworks == []

    def test_full_construction(self):
        c = Control(
            name="Encryption at Rest — AES-256",
            control_id="CL-00001",
            control_type="Preventive",
            control_category="Technical",
            control_class="Automated",
            control_domain="Cryptographic Protections",
            control_status="Implemented",
            control_weighting=9,
            applicability_dimensions=ApplicabilityDimensions(
                technology=True, data=True, process=True,
            ),
            assessment_question="Is AES-256 encryption applied to all restricted data at rest?",
            control_owner="Security Engineering Lead",
            control_operator="Cloud Platform Team",
            implements_policies=[
                PolicyRef(policy_id="PL-00001", policy_name="Data Classification"),
            ],
            maps_to_frameworks=[
                FrameworkMapping(
                    framework="NIST CSF 2.0",
                    control_id_in_framework="PR.DS-01",
                    control_name_in_framework="Data-at-rest is protected",
                    mapping_confidence="Exact Match",
                ),
                FrameworkMapping(
                    framework="ISO 27001:2022",
                    control_id_in_framework="A.8.24",
                    mapping_confidence="Strong",
                ),
            ],
            maps_to_regulations=[
                RegulationMapping(
                    regulation_id="RG-00001",
                    regulation_name="GDPR",
                    requirement_id="Art-32",
                    requirement_description="Security of processing",
                ),
            ],
            mitigates_risks=[
                RiskMitigation(
                    risk_id="RS-00001",
                    mitigation_effectiveness="Substantially Mitigates",
                ),
            ],
            control_effectiveness=ControlEffectiveness(
                rating="Effective",
                methodology="SOC 2 Type II",
                last_assessed="2024-09-01",
            ),
            testing_approach=TestingApproach(
                test_type="Both",
                test_result="Pass",
            ),
            evidence_requirements=EvidenceRequirements(
                evidence_types=["KMS configuration", "Encryption audit logs"],
                evidence_collection_automated=True,
            ),
            automation_details=AutomationDetails(
                tool_name="AWS KMS",
                system_id="SYS-AWS-001",
            ),
            kpi=ControlKPI(
                metric_name="Encryption coverage",
                target="100%",
                current_value="99.7%",
                trend="Stable",
            ),
            exceptions=[
                ControlException(
                    exception_id="CE-001",
                    description="Legacy Oracle DB — uses TDE instead",
                    compensating_control="CL-00042",
                ),
            ],
            gap_status=GapStatus(gap_exists=False),
        )
        assert c.control_id == "CL-00001"
        assert c.control_weighting == 9
        assert c.applicability_dimensions.technology is True
        assert c.applicability_dimensions.facility is False
        assert len(c.maps_to_frameworks) == 2
        assert c.control_effectiveness.rating == "Effective"
        assert c.kpi.current_value == "99.7%"

    def test_json_roundtrip(self):
        c = Control(
            name="MFA Enforcement",
            control_id="CL-00002",
            maps_to_frameworks=[
                FrameworkMapping(
                    framework="CIS Controls v8",
                    control_id_in_framework="6.3",
                ),
            ],
        )
        data = c.model_dump()
        c2 = Control.model_validate(data)
        assert c2.control_id == "CL-00002"
        assert c2.maps_to_frameworks[0].framework == "CIS Controls v8"

    def test_any_entity_roundtrip(self):
        data = {
            "entity_type": "control",
            "name": "Network Segmentation",
            "control_id": "CL-00003",
            "control_type": "Preventive",
        }
        entity = _any_entity_adapter.validate_python(data)
        assert isinstance(entity, Control)
        assert entity.control_type == "Preventive"


# ===========================================================================
# Risk tests
# ===========================================================================


class TestRisk:
    def test_minimal_construction(self):
        r = Risk(name="Data Breach")
        assert r.entity_type == EntityType.RISK
        assert r.risk_id == ""
        assert r.emerging_risk_flag is False

    def test_full_construction(self):
        r = Risk(
            name="Unauthorized access to enterprise systems",
            risk_id="RS-00001",
            risk_category="Cybersecurity",
            risk_source="External",
            risk_taxonomy_references=[
                RiskTaxonomyRef(
                    taxonomy="SCF 2025.1.1",
                    taxonomy_id="R-AC-1",
                    mapping_confidence="Exact Match",
                ),
            ],
            nist_csf_function="Protect",
            inherent_likelihood="Likely",
            inherent_impact="Major",
            inherent_risk_level="High",
            inherent_financial_impact=FinancialImpact(
                estimated_loss_low=5_000_000,
                estimated_loss_high=50_000_000,
                estimation_methodology="FAIR Analysis",
                estimation_confidence="Medium",
            ),
            inherent_impact_dimensions=ImpactDimensions(
                financial="High",
                operational="High",
                reputational="Critical",
                regulatory="High",
            ),
            residual_likelihood="Possible",
            residual_impact="Moderate",
            residual_risk_level="Medium",
            control_effectiveness_on_risk=ControlEffectivenessOnRisk(
                risk_reduction_pct=65.0,
                control_count=12,
            ),
            risk_velocity="Instant",
            risk_trend="Increasing",
            risk_interconnections=[
                RiskInterconnection(
                    related_risk_id="RS-00005",
                    relationship_type="Causes",
                    description="Breach causes reputational damage",
                ),
            ],
            risk_appetite="Conservative",
            risk_tolerance=RiskTolerance(
                tolerance_threshold="Residual risk must remain Medium or below",
                escalation_trigger="Any Critical finding",
                escalation_path="CISO → Board Risk Committee",
            ),
            board_reportable=True,
            risk_owner="CISO",
            risk_status="Mitigated",
            risk_treatment="Mitigate",
            treatment_plan=TreatmentPlan(
                plan_description="Zero Trust architecture rollout",
                target_residual_risk_level="Low",
                actions=["Deploy ZTNA", "Implement micro-segmentation"],
                investment_required=2_500_000,
            ),
            last_assessed="2024-09-01",
            assessment_methodology="FAIR Quantitative",
            assessment_cadence="Quarterly",
            key_risk_indicators=[
                KeyRiskIndicator(
                    kri_name="Failed login attempts",
                    metric="Count per day",
                    threshold_amber="1000",
                    threshold_red="5000",
                    current_value="450",
                ),
            ],
            risk_scenarios=[
                RiskScenario(
                    scenario_name="Nation-state APT compromise",
                    probability="Possible",
                    impact_estimate=25_000_000,
                ),
            ],
            loss_event_history=[
                LossEvent(
                    event_date="2023-03-15",
                    event_description="Credential stuffing incident",
                    actual_impact=150_000,
                    root_cause="Weak MFA enforcement",
                ),
            ],
        )
        assert r.risk_id == "RS-00001"
        assert r.inherent_financial_impact.estimated_loss_high == 50_000_000
        assert r.inherent_impact_dimensions.reputational == "Critical"
        assert r.control_effectiveness_on_risk.risk_reduction_pct == 65.0
        assert r.risk_interconnections[0].relationship_type == "Causes"
        assert r.treatment_plan.investment_required == 2_500_000
        assert r.key_risk_indicators[0].kri_name == "Failed login attempts"
        assert r.loss_event_history[0].actual_impact == 150_000

    def test_json_roundtrip(self):
        r = Risk(
            name="Supply chain disruption",
            risk_id="RS-00010",
            risk_category="Supply Chain",
            inherent_risk_level="High",
        )
        data = r.model_dump()
        r2 = Risk.model_validate(data)
        assert r2.risk_category == "Supply Chain"
        assert r2.inherent_risk_level == "High"

    def test_any_entity_roundtrip(self):
        data = {
            "entity_type": "risk",
            "name": "AI Model Drift",
            "risk_id": "RS-00020",
            "risk_category": "AI & Emerging Technology",
            "emerging_risk_flag": True,
        }
        entity = _any_entity_adapter.validate_python(data)
        assert isinstance(entity, Risk)
        assert entity.emerging_risk_flag is True

    def test_acceptance_and_transfer_records(self):
        r = Risk(
            name="Currency exposure",
            risk_treatment="Transfer",
            acceptance_record=AcceptanceRecord(
                accepted_by="CFO",
                acceptance_rationale="Within risk appetite",
            ),
            transfer_record=TransferRecord(
                transfer_mechanism="Insurance",
                coverage_limit=10_000_000,
                policy_or_contract_reference="INS-2024-001",
            ),
        )
        assert r.transfer_record.coverage_limit == 10_000_000
        assert r.acceptance_record.accepted_by == "CFO"


# ===========================================================================
# Threat tests
# ===========================================================================


class TestThreat:
    def test_minimal_construction(self):
        t = Threat(name="Ransomware")
        assert t.entity_type == EntityType.THREAT
        assert t.threat_id == ""
        assert t.related_threats == []

    def test_full_construction(self):
        t = Threat(
            name="Hacking & Other Cybersecurity Crimes",
            threat_id="TH-00001",
            threat_group="Man-Made Threat — Intentional",
            threat_category="Cyber — External Actor",
            threat_source_type="Organized Criminal",
            threat_taxonomy_references=[
                ThreatTaxonomyRef(
                    taxonomy="SCF 2025.1.1",
                    taxonomy_id="MT-2",
                    mapping_confidence="Exact Match",
                ),
                ThreatTaxonomyRef(
                    taxonomy="MITRE ATT&CK",
                    taxonomy_id="TA0001",
                    taxonomy_name="Initial Access",
                ),
            ],
            origin="SCF Threat Catalog",
            relevance_to_enterprise="Critical",
            relevance_rationale="Financial services primary target",
            geographic_applicability=[
                GeographicApplicability(
                    location_id="GEO-001",
                    location_name="North America",
                    applicability_level="High",
                ),
            ],
            industry_applicability=[
                IndustryApplicability(
                    industry="Financial Services",
                    applicability_level="High",
                ),
            ],
            seasonal_pattern=SeasonalPattern(
                is_seasonal=True,
                peak_period="Q4 (holiday season)",
                pattern_description="Phishing increases during holidays",
            ),
            historical_frequency=HistoricalFrequency(
                events_per_year_industry=1500.0,
                events_per_year_enterprise=12.0,
                data_source="Verizon DBIR 2024",
            ),
            threat_trend="Increasing",
            threat_velocity="Instant",
            creates_risks=[
                ThreatRiskLink(
                    risk_id="RS-00001",
                    causal_description="Exploitation leads to unauthorized access",
                ),
            ],
            addressed_by_controls=[
                ThreatControlLink(
                    control_id="CL-00001",
                    effectiveness_against_threat="Partially Addresses",
                ),
            ],
            related_threats=[
                RelatedThreat(
                    threat_id="TH-00005",
                    relationship_type="Enables",
                ),
            ],
        )
        assert t.threat_id == "TH-00001"
        assert len(t.threat_taxonomy_references) == 2
        assert t.seasonal_pattern.is_seasonal is True
        assert t.historical_frequency.events_per_year_enterprise == 12.0
        assert t.creates_risks[0].risk_id == "RS-00001"
        assert t.addressed_by_controls[0].effectiveness_against_threat == "Partially Addresses"

    def test_json_roundtrip(self):
        t = Threat(
            name="Earthquake",
            threat_id="TH-00010",
            threat_group="Natural Threat",
            threat_category="Seismic / Geological",
        )
        data = t.model_dump()
        t2 = Threat.model_validate(data)
        assert t2.threat_group == "Natural Threat"
        assert t2.threat_category == "Seismic / Geological"

    def test_any_entity_roundtrip(self):
        data = {
            "entity_type": "threat",
            "name": "Pandemic",
            "threat_id": "TH-00020",
            "threat_group": "Natural Threat",
        }
        entity = _any_entity_adapter.validate_python(data)
        assert isinstance(entity, Threat)
        assert entity.threat_group == "Natural Threat"

    def test_materiality_assessment(self):
        from domain.shared import MaterialityAssessment

        t = Threat(
            name="Supply Chain Attack",
            materiality_assessment=MaterialityAssessment(
                pct_of_pretax_income=7.5,
                materiality_conclusion="Material",
            ),
        )
        assert t.materiality_assessment.pct_of_pretax_income == 7.5
        assert t.materiality_assessment.materiality_conclusion == "Material"
