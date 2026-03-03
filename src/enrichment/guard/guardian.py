"""Guardian agents that execute QualityContracts at pipeline checkpoints.

A Guardian assembles one or more QualityContracts and runs them at a
specific point in the enrichment pipeline. Three guardian types correspond
to the three pipeline checkpoints:

1. PreEnrichmentGuardian — Runs before enricher.enrich() to validate
   that the entity is eligible for the target tier.

2. PostEnrichmentGuardian — Runs after enricher.enrich() but before
   kg.update_entity() to validate proposed field updates against
   plausibility, staleness, and confidence rubric contracts.

3. CoherenceGuardian — Runs after a full enrichment pass (all entities
   at a tier) to validate cross-entity coherence invariants.

GraphGuard reference: Fraunhofer IAIS, "GraphGuard: A Quality Contract
Framework for Knowledge Graphs", 2023.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from enrichment.guard.contract import ContractSeverity, QualityContract
from enrichment.guard.reports import (
    ContractEvaluation,
    QualityValidationReport,
)

if TYPE_CHECKING:
    from domain.base import BaseEntity

logger = logging.getLogger(__name__)


class GuardianPhase(StrEnum):
    """Pipeline phase where a guardian operates."""

    PRE_ENRICHMENT = "pre_enrichment"
    POST_ENRICHMENT = "post_enrichment"
    COHERENCE = "coherence"


class AbstractGuardian(ABC):
    """Base class for guardian agents.

    A guardian holds a list of QualityContracts and runs them against
    entities and their proposed updates. It produces a QualityValidationReport
    and can optionally filter field_updates to remove rejected fields.

    Subclasses must implement:
        - phase: The GuardianPhase this guardian operates at.
        - contracts: The list of QualityContracts to execute.
    """

    @property
    @abstractmethod
    def phase(self) -> GuardianPhase:
        """The pipeline phase where this guardian operates."""
        ...

    @property
    @abstractmethod
    def contracts(self) -> list[QualityContract]:
        """The quality contracts this guardian executes."""
        ...

    def validate(
        self,
        entity: BaseEntity,
        field_updates: dict[str, Any],
        **kwargs: Any,
    ) -> tuple[dict[str, Any], QualityValidationReport]:
        """Run all contracts and return filtered updates + report.

        For each contract:
            - If severity is ERROR and a violation is found, the offending
              field is removed from the updates.
            - If severity is WARNING, the violation is logged but the field
              is kept.

        Args:
            entity: The entity being enriched.
            field_updates: Proposed field → value updates.
            **kwargs: Additional context passed through to contracts.

        Returns:
            Tuple of:
                - Filtered field_updates (ERROR violations removed)
                - QualityValidationReport with all evaluation results
        """
        report = QualityValidationReport(total_entities=1)
        filtered_updates = dict(field_updates)  # Copy to mutate
        all_blocking_fields: set[str] = set()

        for contract in self.contracts:
            violations = contract.evaluate(entity, filtered_updates, **kwargs)

            evaluation = ContractEvaluation(
                contract_id=contract.contract_id,
                entity_id=entity.id,
                passed=len(violations) == 0,
                violations=violations,
                fields_checked=len(filtered_updates),
            )
            report.add_evaluation(evaluation)

            # Collect fields to remove (ERROR-severity violations only)
            if contract.severity == ContractSeverity.ERROR:
                for violation in violations:
                    if violation.field_name and violation.is_blocking():
                        all_blocking_fields.add(violation.field_name)

            # Log warnings
            for violation in violations:
                if not violation.is_blocking():
                    logger.warning(
                        f"[{contract.contract_id}] WARNING for "
                        f"{entity.entity_type} {entity.id}: "
                        f"{violation.message}"
                    )

        # Remove fields that had blocking violations
        for field_name in all_blocking_fields:
            if field_name in filtered_updates:
                del filtered_updates[field_name]
                logger.info(
                    f"Guardian ({self.phase.value}) removed field "
                    f"'{field_name}' from {entity.id} due to contract violation"
                )

        return filtered_updates, report

    def __repr__(self) -> str:
        contract_ids = [c.contract_id for c in self.contracts]
        return f"<{self.__class__.__name__} phase={self.phase.value} contracts={contract_ids}>"
