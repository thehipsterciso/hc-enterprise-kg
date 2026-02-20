"""Tests for shared sub-models from L00 definitions."""

from domain.shared import (
    AttestationStatus,
    AuditFinding,
    BackupStatus,
    CostBenchmark,
    CyberExposure,
    DataGap,
    DataQualityScore,
    IndustryClassification,
    MarketPosition,
    MaterialityAssessment,
    ProvenanceAndConfidence,
    RegulatoryApplicability,
    SanctionsScreening,
    SinglePointOfFailure,
    StrategicAlignment,
    TemporalAndVersioning,
)


class TestTemporalAndVersioning:
    def test_defaults(self):
        t = TemporalAndVersioning()
        assert t.schema_version == "1.0.0"
        assert t.effective_date is None

    def test_full_construction(self):
        t = TemporalAndVersioning(
            effective_date="2024-01-01",
            next_review_date="2025-01-01",
            change_reason="Annual review",
        )
        assert t.effective_date == "2024-01-01"
        assert t.change_reason == "Annual review"

    def test_json_roundtrip(self):
        t = TemporalAndVersioning(effective_date="2024-06-01")
        data = t.model_dump()
        t2 = TemporalAndVersioning.model_validate(data)
        assert t2.effective_date == "2024-06-01"


class TestProvenanceAndConfidence:
    def test_defaults(self):
        p = ProvenanceAndConfidence()
        assert p.confidence_level == ""
        assert p.data_quality_score.completeness_pct is None
        assert p.known_data_gaps == []

    def test_full_construction(self):
        p = ProvenanceAndConfidence(
            data_quality_score=DataQualityScore(
                completeness_pct=85.0,
                accuracy_confidence="High",
            ),
            primary_data_source="ServiceNow CMDB",
            confidence_level="Verified",
            attestation_status=AttestationStatus(
                attested_by="John Smith",
                attestation_date="2024-03-15",
            ),
            known_data_gaps=[
                DataGap(
                    attribute_name="owner_id",
                    gap_description="Owner not assigned",
                    priority="High",
                ),
            ],
        )
        assert p.data_quality_score.completeness_pct == 85.0
        assert p.attestation_status.attested_by == "John Smith"
        assert len(p.known_data_gaps) == 1

    def test_json_roundtrip(self):
        p = ProvenanceAndConfidence(
            confidence_level="High",
            known_data_gaps=[DataGap(attribute_name="x", priority="Low")],
        )
        data = p.model_dump()
        p2 = ProvenanceAndConfidence.model_validate(data)
        assert p2.confidence_level == "High"
        assert p2.known_data_gaps[0].attribute_name == "x"


class TestAuditFinding:
    def test_construction(self):
        f = AuditFinding(
            finding_id="AF-001",
            finding_severity="Critical",
            finding_source="External Audit",
            remediation_status="In Progress",
        )
        assert f.finding_severity == "Critical"

    def test_json_roundtrip(self):
        f = AuditFinding(finding_id="AF-002", finding_severity="High")
        data = f.model_dump()
        f2 = AuditFinding.model_validate(data)
        assert f2.finding_id == "AF-002"


class TestSanctionsScreening:
    def test_construction(self):
        s = SanctionsScreening(
            screening_status="Clear",
            lists_checked=["OFAC SDN", "EU Consolidated", "UN Security Council"],
        )
        assert len(s.lists_checked) == 3

    def test_json_roundtrip(self):
        s = SanctionsScreening(screening_status="Clear", screening_provider="Dow Jones")
        data = s.model_dump()
        s2 = SanctionsScreening.model_validate(data)
        assert s2.screening_provider == "Dow Jones"


class TestIndustryClassification:
    def test_construction(self):
        ic = IndustryClassification(
            naics_code="541511",
            naics_description="Custom Computer Programming Services",
            sic_code="7371",
        )
        assert ic.naics_code == "541511"


class TestMaterialityAssessment:
    def test_construction(self):
        m = MaterialityAssessment(
            pct_of_pretax_income=3.2,
            materiality_conclusion="Potentially Material",
        )
        assert m.pct_of_pretax_income == 3.2
        assert m.materiality_conclusion == "Potentially Material"


class TestMarketPosition:
    def test_construction(self):
        mp = MarketPosition(
            market_size_tam=50_000_000_000,
            market_size_sam=15_000_000_000,
            market_size_som=2_000_000_000,
            market_share_pct=13.3,
            market_share_rank=3,
        )
        assert mp.market_share_rank == 3
        assert mp.currency == "USD"


class TestSinglePointOfFailure:
    def test_construction(self):
        s = SinglePointOfFailure(
            spof_id="SPOF-001",
            spof_description="Single database server",
            mitigation_status="Partially Mitigated",
        )
        assert s.mitigation_status == "Partially Mitigated"


class TestStrategicAlignment:
    def test_construction(self):
        sa = StrategicAlignment(
            strategic_objective_id="SO-01",
            strategic_objective_name="Digital Transformation",
            alignment_strength="Primary Enabler",
        )
        assert sa.alignment_strength == "Primary Enabler"


class TestCostBenchmark:
    def test_construction(self):
        cb = CostBenchmark(
            benchmark_source="Gartner IT Key Metrics 2024",
            benchmark_value=12_500_000,
            percentile_position=65.0,
        )
        assert cb.percentile_position == 65.0


class TestRegulatoryApplicability:
    def test_construction(self):
        ra = RegulatoryApplicability(
            regulation_id="RG-001",
            regulation_name="GDPR",
            jurisdiction="EU",
            applicability_type="Directly Regulated",
            compliance_status="Partially Compliant",
        )
        assert ra.compliance_status == "Partially Compliant"


class TestCyberExposure:
    def test_construction(self):
        ce = CyberExposure(
            attack_surface_type="Internet Facing",
            threat_profile="Organized Crime Target",
        )
        assert ce.attack_surface_type == "Internet Facing"


class TestBackupStatus:
    def test_construction(self):
        bs = BackupStatus(
            backup_frequency="Daily",
            backup_type="Incremental",
            meets_rpo=True,
        )
        assert bs.meets_rpo is True
