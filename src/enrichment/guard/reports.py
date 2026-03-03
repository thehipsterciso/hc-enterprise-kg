"""Quality validation reports and contract violation records.

Provides the audit trail for GraphGuard contract evaluations. Every
enrichment update produces a QualityValidationReport that records which
contracts were evaluated, which passed, and which produced violations.

Reports are queryable: filter by entity, contract, severity, or field
to answer questions like "which entities had plausibility violations?"
or "what percentage of confidence claims were downgraded?"
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# UTC timezone (Python 3.11+) or fallback
try:
    from datetime import UTC
except ImportError:
    UTC = UTC


@dataclass
class ContractViolation:
    """A single violation produced by a QualityContract evaluation.

    Captures what was violated, why, and what the enricher attempted,
    providing full context for debugging and audit purposes.

    Attributes:
        contract_id: The QualityContract that produced this violation.
        severity: ERROR, WARNING, or INFO.
        entity_id: The entity that the violation relates to.
        field_name: The specific field that violated the contract (if applicable).
        message: Human-readable description of the violation.
        attempted_value: The value the enricher tried to set.
        expected_range: What the contract expected (for plausibility violations).
        enricher_source: Which enricher or source produced the rejected value.
        remediation: Suggested fix for the violation.
        timestamp: When the violation was detected.
    """

    contract_id: str
    severity: str  # "error", "warning", "info"
    entity_id: str = ""
    field_name: str = ""
    message: str = ""
    attempted_value: Any = None
    expected_range: str = ""
    enricher_source: str = ""
    remediation: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def is_blocking(self) -> bool:
        """Return True if this violation should block the update."""
        return self.severity == "error"


@dataclass
class ContractEvaluation:
    """Record of a single contract evaluation (pass or fail).

    Attributes:
        contract_id: Which contract was evaluated.
        entity_id: Which entity was checked.
        passed: Whether the contract was satisfied.
        violations: List of violations if the contract failed.
        fields_checked: Number of fields evaluated.
        duration_ms: How long the evaluation took.
    """

    contract_id: str
    entity_id: str
    passed: bool
    violations: list[ContractViolation] = field(default_factory=list)
    fields_checked: int = 0
    duration_ms: float = 0.0


@dataclass
class QualityValidationReport:
    """Aggregate report from a full validation pass.

    Collects all contract evaluations for a batch of entities,
    providing queryable access to the results.

    Attributes:
        evaluations: All individual contract evaluations.
        total_entities: Number of entities validated.
        total_contracts_run: Number of contract evaluations performed.
        total_violations: Total violations across all evaluations.
        blocking_violations: Violations that blocked updates.
        warning_violations: Violations logged as warnings.
        start_time: When the validation started.
        end_time: When the validation completed.
    """

    evaluations: list[ContractEvaluation] = field(default_factory=list)
    total_entities: int = 0
    total_contracts_run: int = 0
    total_violations: int = 0
    blocking_violations: int = 0
    warning_violations: int = 0
    start_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    end_time: datetime | None = None

    def add_evaluation(self, evaluation: ContractEvaluation) -> None:
        """Add a contract evaluation to the report."""
        self.evaluations.append(evaluation)
        self.total_contracts_run += 1
        violation_count = len(evaluation.violations)
        self.total_violations += violation_count
        self.blocking_violations += sum(1 for v in evaluation.violations if v.is_blocking())
        self.warning_violations += sum(1 for v in evaluation.violations if not v.is_blocking())

    def get_violations_for_entity(self, entity_id: str) -> list[ContractViolation]:
        """Get all violations for a specific entity."""
        violations = []
        for evaluation in self.evaluations:
            if evaluation.entity_id == entity_id:
                violations.extend(evaluation.violations)
        return violations

    def get_violations_by_contract(self, contract_id: str) -> list[ContractViolation]:
        """Get all violations from a specific contract."""
        violations = []
        for evaluation in self.evaluations:
            if evaluation.contract_id == contract_id:
                violations.extend(evaluation.violations)
        return violations

    def get_violations_by_severity(self, severity: str) -> list[ContractViolation]:
        """Get all violations of a specific severity level."""
        violations = []
        for evaluation in self.evaluations:
            violations.extend(v for v in evaluation.violations if v.severity == severity)
        return violations

    def pass_rate(self) -> float:
        """Percentage of contract evaluations that passed."""
        if self.total_contracts_run == 0:
            return 100.0
        passed = sum(1 for e in self.evaluations if e.passed)
        return (passed / self.total_contracts_run) * 100.0

    def entity_ids_with_violations(self) -> set[str]:
        """Return set of entity IDs that had at least one violation."""
        return {e.entity_id for e in self.evaluations if not e.passed}

    def summary(self) -> dict[str, Any]:
        """Return a summary dict suitable for logging or reporting."""
        return {
            "total_entities": self.total_entities,
            "total_contracts_run": self.total_contracts_run,
            "total_violations": self.total_violations,
            "blocking_violations": self.blocking_violations,
            "warning_violations": self.warning_violations,
            "pass_rate_pct": round(self.pass_rate(), 2),
            "entities_with_violations": len(self.entity_ids_with_violations()),
        }
