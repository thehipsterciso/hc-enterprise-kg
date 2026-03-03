"""GraphGuard Quality Contract Framework for Knowledge Graph Enrichment.

Implements the GraphGuard pattern (Fraunhofer 2023) for declarative
quality validation of enrichment results. The framework has three layers:

1. **QualityContracts** — Declarative rules that define quality criteria
   (plausibility bounds, staleness windows, confidence rubrics, etc.).
   Contracts are independently testable and composable.

2. **Guardians** — Agents that execute contracts at specific points in
   the enrichment pipeline (pre-enrichment, post-enrichment, coherence).

3. **QualityValidationReports** — Queryable audit records of every
   contract evaluation, capturing what was checked, what passed, and
   what was rejected with full provenance.

See ADR-015 for architectural rationale.
"""

from __future__ import annotations

from enrichment.guard.contract import (
    ContractSeverity,
    QualityContract,
)
from enrichment.guard.guardian import (
    AbstractGuardian,
    GuardianPhase,
)
from enrichment.guard.reports import (
    ContractViolation,
    QualityValidationReport,
)

__all__ = [
    "AbstractGuardian",
    "ContractSeverity",
    "ContractViolation",
    "GuardianPhase",
    "QualityContract",
    "QualityValidationReport",
]
