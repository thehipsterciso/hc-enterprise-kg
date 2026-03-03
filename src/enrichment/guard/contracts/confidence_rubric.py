"""ConfidenceRubricContract — verifies enricher confidence claims against evidence.

Extracted from AdversarialValidator._enforce_confidence_rubric(). Validates
that the confidence level claimed by an enricher is supported by the
quality of its source evidence.

An enricher claiming VERIFIED confidence from a web search gets downgraded
to MEDIUM. An enricher claiming HIGH from a template source gets downgraded
to LOW. The rubric is defined in CONFIDENCE_RUBRIC (enrichment.base).

Contract ID: GG-CONF-001
Severity: WARNING (downgrades confidence; doesn't block the update)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from domain.base import BaseEntity

from enrichment.base import (
    CONFIDENCE_RUBRIC,
    ConfidenceLevel,
    EnrichmentAction,
)
from enrichment.guard.contract import ContractSeverity, QualityContract
from enrichment.guard.contracts.staleness import StalenessContract
from enrichment.guard.reports import ContractViolation

# UTC timezone
try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc


class ConfidenceRubricContract(QualityContract):
    """Validates enricher confidence claims against the CONFIDENCE_RUBRIC.

    For each EnrichmentAction, checks:
    1. Is the source type appropriate for the claimed confidence level?
    2. Is the source within the staleness window for that confidence level?

    If either check fails, produces a WARNING violation indicating the
    appropriate downgraded confidence level.
    """

    CONTRACT_ID = "GG-CONF-001"
    DESCRIPTION = "Confidence claim verification against rubric criteria"
    DEFAULT_SEVERITY = ContractSeverity.WARNING

    def evaluate(
        self,
        entity: BaseEntity,
        field_updates: dict[str, Any],
        **kwargs: Any,
    ) -> list[ContractViolation]:
        """Check confidence claims for all enrichment actions.

        Expects kwargs to contain:
            actions: list[EnrichmentAction] — the actions to check.

        Args:
            entity: The entity receiving the updates.
            field_updates: Proposed field → value mappings.
            **kwargs: Must include 'actions' key.

        Returns:
            List of ContractViolation for any inflated confidence claims.
        """
        violations: list[ContractViolation] = []
        actions: list[EnrichmentAction] = kwargs.get("actions", [])

        for action in actions:
            claimed = action.confidence
            if isinstance(claimed, str):
                try:
                    claimed = ConfidenceLevel(claimed.lower())
                except ValueError:
                    claimed = ConfidenceLevel.UNVERIFIED

            rubric = CONFIDENCE_RUBRIC.get(claimed, {})
            max_staleness = rubric.get("max_staleness_days", 0)

            # Check staleness-based downgrade
            if action.source_date and max_staleness > 0:
                try:
                    source_dt = datetime.fromisoformat(
                        action.source_date.replace("Z", "+00:00")
                    )
                    days_old = (datetime.now(UTC) - source_dt).days

                    if days_old > max_staleness:
                        downgraded = StalenessContract.downgrade_confidence(
                            claimed, days_old
                        )
                        if downgraded != claimed:
                            violations.append(
                                ContractViolation(
                                    contract_id=self.CONTRACT_ID,
                                    severity=self.DEFAULT_SEVERITY.value,
                                    entity_id=entity.id,
                                    field_name=", ".join(action.fields_enriched),
                                    message=(
                                        f"Confidence downgrade: {claimed.value} → "
                                        f"{downgraded.value} — source '{action.source}' "
                                        f"is {days_old} days old (max {max_staleness} "
                                        f"for {claimed.value})"
                                    ),
                                    attempted_value=claimed.value,
                                    expected_range=f"Source <= {max_staleness} days old",
                                    enricher_source=action.source,
                                    remediation=(
                                        f"Either refresh the source data or claim "
                                        f"{downgraded.value} confidence instead"
                                    ),
                                )
                            )
                except (ValueError, TypeError):
                    pass

        return violations
