"""QualityContract ABC — declarative quality rules for enrichment validation.

A QualityContract defines a single, testable quality criterion that enrichment
results must satisfy before being applied to the knowledge graph. Contracts
are composable: a Guardian assembles multiple contracts into a validation
pipeline.

Each contract:
    - Has a unique CONTRACT_ID (e.g., "GG-PLAUS-001")
    - Declares its severity (ERROR blocks the update; WARNING logs but allows)
    - Implements evaluate() returning a list of ContractViolation objects
    - Is independently unit-testable

GraphGuard reference: Fraunhofer IAIS, "GraphGuard: A Quality Contract
Framework for Knowledge Graphs", 2023.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Any

from domain.base import BaseEntity

from enrichment.guard.reports import ContractViolation


class ContractSeverity(StrEnum):
    """Severity level of a quality contract.

    - ERROR: Violation blocks the enrichment update. The field is rejected.
    - WARNING: Violation is logged but the update proceeds. Useful for
      data quality monitoring without blocking enrichment flow.
    - INFO: Informational observation. No action taken.
    """

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class QualityContract(ABC):
    """Abstract base class for quality contracts.

    Subclasses implement a single quality criterion. The evaluate() method
    receives the entity and proposed field updates, returning any violations
    found.

    Class attributes:
        CONTRACT_ID: Unique identifier (e.g., "GG-PLAUS-001").
        DESCRIPTION: Human-readable description of what the contract checks.
        DEFAULT_SEVERITY: Default severity for violations from this contract.

    Example:
        class PlausibilityContract(QualityContract):
            CONTRACT_ID = "GG-PLAUS-001"
            DESCRIPTION = "Domain bounds check for numeric field values"
            DEFAULT_SEVERITY = ContractSeverity.ERROR

            def evaluate(self, entity, field_updates, **kwargs):
                violations = []
                for field, value in field_updates.items():
                    if not self._in_bounds(entity, field, value):
                        violations.append(ContractViolation(...))
                return violations
    """

    CONTRACT_ID: str = ""
    DESCRIPTION: str = ""
    DEFAULT_SEVERITY: ContractSeverity = ContractSeverity.ERROR

    @abstractmethod
    def evaluate(
        self,
        entity: BaseEntity,
        field_updates: dict[str, Any],
        **kwargs: Any,
    ) -> list[ContractViolation]:
        """Evaluate proposed field updates against this contract.

        Args:
            entity: The entity that would receive the updates.
            field_updates: Proposed field name → value mappings.
            **kwargs: Additional context (tier, profile, actions, etc.).

        Returns:
            List of ContractViolation objects for any violations found.
            Empty list means the contract is satisfied.
        """
        ...

    @property
    def contract_id(self) -> str:
        """Return the contract's unique identifier."""
        return self.CONTRACT_ID

    @property
    def severity(self) -> ContractSeverity:
        """Return the contract's default severity."""
        return self.DEFAULT_SEVERITY

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.CONTRACT_ID}>"
