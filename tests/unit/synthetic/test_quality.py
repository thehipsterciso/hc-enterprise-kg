"""Tests for synthetic data quality scoring."""

from __future__ import annotations

from graph.knowledge_graph import KnowledgeGraph
from synthetic.orchestrator import SyntheticOrchestrator
from synthetic.profiles.tech_company import mid_size_tech_company
from synthetic.quality import assess_quality


def _make_context(emp: int = 100):
    """Generate a graph and return the orchestrator context."""
    kg = KnowledgeGraph()
    orch = SyntheticOrchestrator(kg, mid_size_tech_company(emp), seed=42)
    orch.generate()
    return orch.context, orch


class TestQualityScoring:
    """Quality scoring module tests."""

    def test_overall_quality_above_threshold(self):
        """Overall quality score should be >= 0.7 on a 100-employee graph."""
        ctx, orch = _make_context(100)
        report = assess_quality(ctx)
        assert report.overall_score >= 0.7, (
            f"Quality score {report.overall_score:.2f} below threshold.\n{report.summary()}"
        )

    def test_risk_math_consistency(self):
        """Risk levels should derive from likelihood x impact matrix."""
        ctx, _ = _make_context(100)
        report = assess_quality(ctx)
        assert report.risk_math_consistency >= 0.95, (
            f"Risk math consistency {report.risk_math_consistency:.2f} below 0.95"
        )

    def test_no_lorem_ipsum_descriptions(self):
        """No entity descriptions should contain lorem ipsum patterns."""
        ctx, _ = _make_context(100)
        report = assess_quality(ctx)
        assert report.description_quality >= 0.95, (
            f"Description quality {report.description_quality:.2f} below 0.95"
        )

    def test_tech_stack_coherence_above_80pct(self):
        """System tech stacks should be coherent with system type."""
        ctx, _ = _make_context(100)
        report = assess_quality(ctx)
        assert report.tech_stack_coherence >= 0.80, (
            f"Tech stack coherence {report.tech_stack_coherence:.2f} below 0.80"
        )

    def test_encryption_classification_correlation(self):
        """Restricted/confidential data flows should be encrypted."""
        ctx, _ = _make_context(100)
        report = assess_quality(ctx)
        assert report.encryption_classification_consistency >= 0.80, (
            f"Encryption consistency {report.encryption_classification_consistency:.2f} below 0.80"
        )

    def test_field_correlation_score(self):
        """Correlated fields should agree."""
        ctx, _ = _make_context(100)
        report = assess_quality(ctx)
        assert report.field_correlation_score >= 0.70, (
            f"Field correlation score {report.field_correlation_score:.2f} below 0.70"
        )

    def test_orchestrator_exposes_quality_report(self):
        """Orchestrator should expose quality report after generation."""
        _, orch = _make_context(100)
        report = orch.quality_report
        assert report.overall_score > 0, "Quality report should have non-zero score"

    def test_quality_report_summary(self):
        """Quality report summary should be a non-empty string."""
        ctx, _ = _make_context(50)
        report = assess_quality(ctx)
        summary = report.summary()
        assert "Overall Score" in summary
        assert len(summary) > 50
