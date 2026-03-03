"""Knowledge Graph Enrichment Agency.

An intelligence-driven enrichment system that progressively deepens
entity attributes and relationship metadata across 5 maturity tiers
(CMMI/DCAM-aligned). No agent operates in a silo — every enrichment
decision considers the entity's graph neighborhood and uses OSINT
research for real-world grounding.

Architectural invariant: every enrichment result passes through the
AdversarialValidator BEFORE being applied to the graph. The validator
rejects updates that fail Pydantic model validation, violate confidence
rubric criteria, contain stale source data, or break cross-entity coherence.

Public API:
    EnrichmentOrchestrator  — Main coordinator
    AdversarialValidator    — Pre-application validation gate
    AbstractEnricher        — Base class for entity enrichers
    EnricherRegistry        — Registry for enricher lookup
    EnrichmentContext       — Shared context during a run
    EnrichmentResult        — Output of a single enrichment
    EnrichmentStats         — Aggregate run statistics
    GraphContextEngine      — Graph neighborhood retrieval
    ProvenanceReconciler    — Provenance & confidence tracking
"""

from __future__ import annotations

from enrichment.base import (
    AbstractEnricher,
    AdversarialValidator,
    AssessmentMethodology,
    CONFIDENCE_RUBRIC,
    ConfidenceLevel,
    EnrichmentAction,
    EnrichmentContext,
    EnrichmentResult,
    EnrichmentStats,
    EnrichmentTier,
    EnricherRegistry,
    EntityContext,
    FieldCategory,
    SOURCE_VALIDITY_WINDOWS,
    ValidationFailure,
)
from enrichment.graph_context import GraphContextEngine
from enrichment.orchestrator import EnrichmentOrchestrator
from enrichment.provenance_reconciler import ProvenanceReconciler

__all__ = [
    "AbstractEnricher",
    "AdversarialValidator",
    "AssessmentMethodology",
    "CONFIDENCE_RUBRIC",
    "ConfidenceLevel",
    "EnrichmentAction",
    "EnrichmentContext",
    "EnrichmentOrchestrator",
    "EnrichmentResult",
    "EnrichmentStats",
    "EnrichmentTier",
    "EnricherRegistry",
    "EntityContext",
    "FieldCategory",
    "GraphContextEngine",
    "ProvenanceReconciler",
    "SOURCE_VALIDITY_WINDOWS",
    "ValidationFailure",
]
