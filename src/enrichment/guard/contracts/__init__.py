"""Concrete QualityContract implementations.

Each contract validates a single quality criterion extracted from the
original AdversarialValidator monolith. Contracts are independently
testable and composable via Guardians.

Contracts:
    PlausibilityContract     — Domain bounds for numeric fields
    StalenessContract        — Source freshness enforcement
    ConfidenceRubricContract — Confidence claim verification
    CoherenceContract        — Cross-entity invariant validation
    CompletenessContract     — Weighted completeness thresholds
"""

from __future__ import annotations

from enrichment.guard.contracts.coherence import CoherenceContract
from enrichment.guard.contracts.completeness import CompletenessContract
from enrichment.guard.contracts.confidence_rubric import ConfidenceRubricContract
from enrichment.guard.contracts.plausibility import PlausibilityContract
from enrichment.guard.contracts.staleness import StalenessContract

__all__ = [
    "PlausibilityContract",
    "StalenessContract",
    "ConfidenceRubricContract",
    "CoherenceContract",
    "CompletenessContract",
]
