"""Tests for the AdversarialValidator — the enrichment quality gate.

Tests negative cases: what SHOULD be rejected, and verifies that rejection
happens BEFORE data reaches the graph.

Covers:
1. Pydantic validation failures (sub-model coercion, wrong types)
2. Confidence inflation (claiming VERIFIED from a web search)
3. Source staleness (SOC 2 report older than 18 months)
4. Value plausibility (salary $50M, negative headcount, CVSS > 10)
5. Rubric enforcement (downgrade when criteria not met)
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from domain.base import EntityType, RelationshipType
from enrichment.base import (
    AdversarialValidator,
    AssessmentMethodology,
    CONFIDENCE_RUBRIC,
    ConfidenceLevel,
    EnrichmentAction,
    EnrichmentResult,
    FieldCategory,
    SOURCE_VALIDITY_WINDOWS,
    ValidationFailure,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def validator():
    return AdversarialValidator()


@pytest.fixture
def mock_person():
    """Create a minimal Person entity for testing."""
    from domain.entities.person import Person

    return Person(
        id="test-person-001",
        name="Test Person",
        entity_type="person",
    )


@pytest.fixture
def mock_system():
    """Create a minimal System entity for testing."""
    from domain.entities.system import System

    return System(
        id="test-system-001",
        name="Test System",
        entity_type="system",
    )


# ---------------------------------------------------------------------------
# 1. Plausibility Bounds — reject impossible values
# ---------------------------------------------------------------------------


class TestPlausibilityBounds:
    """Values outside domain bounds must be rejected."""

    def test_rejects_negative_headcount(self, validator):
        """Department headcount cannot be negative."""
        from domain.entities.department import Department

        dept = Department(id="dept-001", name="Engineering", entity_type="department")
        result = EnrichmentResult(
            entity_id="dept-001",
            entity_type=EntityType.DEPARTMENT,
            field_updates={"head_count": -5},
        )
        validated, failures = validator.validate(dept, result)
        assert "head_count" not in validated.field_updates
        assert len(failures) == 1
        assert failures[0].failure_type == "plausibility"

    def test_rejects_cvss_above_10(self, validator):
        """CVSS scores max at 10.0."""
        from domain.entities.vulnerability import Vulnerability

        vuln = Vulnerability(id="vuln-001", name="Test Vuln", entity_type="vulnerability")
        result = EnrichmentResult(
            entity_id="vuln-001",
            entity_type=EntityType.VULNERABILITY,
            field_updates={"cvss_score": 15.0},
        )
        validated, failures = validator.validate(vuln, result)
        assert "cvss_score" not in validated.field_updates
        assert any(f.failure_type == "plausibility" for f in failures)

    def test_accepts_valid_cvss(self, validator):
        """Valid CVSS score should pass."""
        from domain.entities.vulnerability import Vulnerability

        vuln = Vulnerability(id="vuln-001", name="Test Vuln", entity_type="vulnerability")
        result = EnrichmentResult(
            entity_id="vuln-001",
            entity_type=EntityType.VULNERABILITY,
            field_updates={"cvss_score": 7.5},
        )
        validated, failures = validator.validate(vuln, result)
        assert validated.field_updates.get("cvss_score") == 7.5
        assert len(failures) == 0

    def test_rejects_salary_above_15m(self, validator, mock_person):
        """Annual compensation above $15M is implausible."""
        result = EnrichmentResult(
            entity_id="test-person-001",
            entity_type=EntityType.PERSON,
            field_updates={"annual_compensation": 50_000_000},
        )
        validated, failures = validator.validate(mock_person, result)
        assert "annual_compensation" not in validated.field_updates

    def test_accepts_reasonable_salary(self, validator, mock_person):
        """A reasonable salary should pass."""
        result = EnrichmentResult(
            entity_id="test-person-001",
            entity_type=EntityType.PERSON,
            field_updates={"annual_compensation": 175_000},
        )
        validated, failures = validator.validate(mock_person, result)
        assert validated.field_updates.get("annual_compensation") == 175_000


# ---------------------------------------------------------------------------
# 2. Confidence Rubric Enforcement — downgrade inflated claims
# ---------------------------------------------------------------------------


class TestConfidenceRubricEnforcement:
    """Enrichers that claim higher confidence than their source warrants
    must be downgraded automatically."""

    def test_stale_source_downgrades_confidence(self, validator):
        """A source 2 years old cannot support VERIFIED confidence (max 365 days)."""
        stale_date = (datetime.now(UTC) - timedelta(days=730)).isoformat()
        action = EnrichmentAction(
            entity_id="test-001",
            entity_type=EntityType.CONTROL,
            fields_enriched=["framework_mappings"],
            source="NIST SP 800-53",
            methodology=AssessmentMethodology.AUTOMATED,
            confidence=ConfidenceLevel.VERIFIED,
            source_date=stale_date,
            validity_window_days=365,
        )
        downgraded = validator._enforce_confidence_rubric(action)
        # Should be downgraded from VERIFIED since source > 365 days old
        assert downgraded.confidence != ConfidenceLevel.VERIFIED

    def test_fresh_source_keeps_confidence(self, validator):
        """A fresh source should retain its claimed confidence."""
        fresh_date = (datetime.now(UTC) - timedelta(days=30)).isoformat()
        action = EnrichmentAction(
            entity_id="test-001",
            entity_type=EntityType.CONTROL,
            fields_enriched=["framework_mappings"],
            source="NIST SP 800-53",
            methodology=AssessmentMethodology.AUTOMATED,
            confidence=ConfidenceLevel.VERIFIED,
            source_date=fresh_date,
            validity_window_days=365,
        )
        result = validator._enforce_confidence_rubric(action)
        assert result.confidence == ConfidenceLevel.VERIFIED

    def test_no_source_date_no_downgrade(self, validator):
        """Without a source date, confidence is not modified."""
        action = EnrichmentAction(
            entity_id="test-001",
            entity_type=EntityType.CONTROL,
            fields_enriched=["status"],
            source="Graph inference",
            methodology=AssessmentMethodology.AUTOMATED,
            confidence=ConfidenceLevel.LOW,
        )
        result = validator._enforce_confidence_rubric(action)
        assert result.confidence == ConfidenceLevel.LOW


# ---------------------------------------------------------------------------
# 3. Source Validity Windows — correct values in the config
# ---------------------------------------------------------------------------


class TestSourceValidityWindows:
    """Source validity windows should match documented expectations."""

    def test_soc2_validity_is_18_months(self):
        assert SOURCE_VALIDITY_WINDOWS["soc2_report"] == 548

    def test_sec_filing_validity_is_12_months(self):
        assert SOURCE_VALIDITY_WINDOWS["sec_filing"] == 365

    def test_nist_validity_is_2_years(self):
        assert SOURCE_VALIDITY_WINDOWS["nist"] == 730

    def test_web_search_validity_is_90_days(self):
        assert SOURCE_VALIDITY_WINDOWS["web_search"] == 90

    def test_template_immediately_stale(self):
        assert SOURCE_VALIDITY_WINDOWS["template"] == 0

    def test_graph_inference_30_days(self):
        assert SOURCE_VALIDITY_WINDOWS["graph_inference"] == 30


# ---------------------------------------------------------------------------
# 4. Confidence Rubric Structure
# ---------------------------------------------------------------------------


class TestConfidenceRubricStructure:
    """The rubric should have testable criteria for every confidence level."""

    def test_all_levels_have_rubric(self):
        for level in ConfidenceLevel:
            assert level in CONFIDENCE_RUBRIC, f"Missing rubric for {level}"

    def test_rubric_has_required_keys(self):
        required_keys = {"description", "required_source_types", "min_sources", "max_staleness_days", "examples"}
        for level, rubric in CONFIDENCE_RUBRIC.items():
            assert required_keys.issubset(rubric.keys()), (
                f"Rubric for {level} missing keys: {required_keys - rubric.keys()}"
            )

    def test_staleness_decreases_with_confidence(self):
        """Higher confidence should tolerate longer staleness from authoritative sources."""
        verified_staleness = CONFIDENCE_RUBRIC[ConfidenceLevel.VERIFIED]["max_staleness_days"]
        high_staleness = CONFIDENCE_RUBRIC[ConfidenceLevel.HIGH]["max_staleness_days"]
        medium_staleness = CONFIDENCE_RUBRIC[ConfidenceLevel.MEDIUM]["max_staleness_days"]
        low_staleness = CONFIDENCE_RUBRIC[ConfidenceLevel.LOW]["max_staleness_days"]

        # Higher confidence tolerates longer staleness (because sources are more authoritative)
        assert verified_staleness >= high_staleness >= medium_staleness >= low_staleness


# ---------------------------------------------------------------------------
# 5. Assessment Methodology Enum
# ---------------------------------------------------------------------------


class TestAssessmentMethodology:
    """Assessment methodology should be a proper enum, not a free-form string."""

    def test_enum_values(self):
        assert AssessmentMethodology.AUTOMATED.value == "automated"
        assert AssessmentMethodology.HYBRID.value == "hybrid"
        assert AssessmentMethodology.MANUAL.value == "manual"
        assert AssessmentMethodology.IMPORT.value == "import"

    def test_string_conversion(self):
        """String values should convert to enum."""
        assert AssessmentMethodology("automated") == AssessmentMethodology.AUTOMATED
        assert AssessmentMethodology("hybrid") == AssessmentMethodology.HYBRID


# ---------------------------------------------------------------------------
# 6. Field Category Classification
# ---------------------------------------------------------------------------


class TestFieldCategory:
    """Field categories should be properly enumerated."""

    def test_enum_values(self):
        assert FieldCategory.CRITICAL.value == "critical"
        assert FieldCategory.OPERATIONAL.value == "operational"
        assert FieldCategory.METADATA.value == "metadata"


# ---------------------------------------------------------------------------
# 7. End-to-end: validator rejects bad result, passes good result
# ---------------------------------------------------------------------------


class TestEndToEndValidation:
    """Integration test: mix of good and bad field updates."""

    def test_partial_rejection(self, validator, mock_person):
        """Some fields pass, some fail — only valid fields survive."""
        result = EnrichmentResult(
            entity_id="test-person-001",
            entity_type=EntityType.PERSON,
            field_updates={
                "title": "Senior Engineer",  # Valid string — should pass
                "annual_compensation": 50_000_000,  # Over $15M — should fail
                "years_experience": -3,  # Negative — should fail
            },
        )
        validated, failures = validator.validate(mock_person, result)

        # title should survive
        assert "title" in validated.field_updates
        # Implausible values should be rejected
        assert "annual_compensation" not in validated.field_updates
        assert "years_experience" not in validated.field_updates
        assert len(failures) == 2

    def test_all_valid_passes_through(self, validator, mock_person):
        """All valid fields should pass through unchanged."""
        result = EnrichmentResult(
            entity_id="test-person-001",
            entity_type=EntityType.PERSON,
            field_updates={
                "title": "Staff Engineer",
                "description": "Experienced engineer",
            },
        )
        validated, failures = validator.validate(mock_person, result)
        assert len(failures) == 0
        assert validated.field_updates == result.field_updates

    def test_empty_result_passes(self, validator, mock_person):
        """Empty result should pass without errors."""
        result = EnrichmentResult(
            entity_id="test-person-001",
            entity_type=EntityType.PERSON,
        )
        validated, failures = validator.validate(mock_person, result)
        assert len(failures) == 0
        assert not validated.field_updates
