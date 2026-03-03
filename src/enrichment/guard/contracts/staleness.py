"""StalenessContract — source freshness enforcement for enrichment data.

Extracted from AdversarialValidator._downgrade_for_staleness() and
SOURCE_VALIDITY_WINDOWS. Validates that enrichment source data is within
its authoritative validity window.

When a source exceeds its validity window, the associated confidence
level is downgraded. For example:
    - A SOC 2 report older than 18 months → confidence downgraded
    - A NIST reference older than 2 years → confidence downgraded
    - A web search result older than 90 days → confidence downgraded

Contract ID: GG-STALE-001
Severity: WARNING (downgrades confidence but doesn't block the update)
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from enrichment.base import (
    CONFIDENCE_RUBRIC,
    SOURCE_VALIDITY_WINDOWS,
    ConfidenceLevel,
    EnrichmentAction,
)
from enrichment.guard.contract import ContractSeverity, QualityContract
from enrichment.guard.reports import ContractViolation

if TYPE_CHECKING:
    from domain.base import BaseEntity

# UTC timezone (Python 3.11+) or fallback
try:
    from datetime import UTC
except ImportError:
    UTC = UTC


class StalenessContract(QualityContract):
    """Validates that enrichment source data is within its validity window.

    For each EnrichmentAction in the kwargs, checks the source_date against
    the appropriate validity window from SOURCE_VALIDITY_WINDOWS or the
    action's own validity_window_days.

    This contract produces WARNING-severity violations (the update proceeds
    but confidence is flagged for downgrade by the confidence rubric contract).
    """

    CONTRACT_ID = "GG-STALE-001"
    DESCRIPTION = "Source freshness enforcement against validity windows"
    DEFAULT_SEVERITY = ContractSeverity.WARNING

    def evaluate(
        self,
        entity: BaseEntity,
        field_updates: dict[str, Any],
        **kwargs: Any,
    ) -> list[ContractViolation]:
        """Check source staleness for all enrichment actions.

        Expects kwargs to contain:
            actions: list[EnrichmentAction] — the actions to check.

        Args:
            entity: The entity receiving the updates.
            field_updates: Proposed field → value mappings.
            **kwargs: Must include 'actions' key.

        Returns:
            List of ContractViolation for any stale sources.
        """
        violations: list[ContractViolation] = []
        actions: list[EnrichmentAction] = kwargs.get("actions", [])

        for action in actions:
            if not action.source_date:
                continue

            try:
                source_dt = datetime.fromisoformat(action.source_date.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                continue

            days_old = (datetime.now(UTC) - source_dt).days

            # Determine validity window
            validity_days = action.validity_window_days
            if validity_days is None:
                # Look up from source type
                source_lower = action.source.lower().replace(" ", "_")
                validity_days = self._get_validity_window(source_lower)

            if validity_days is not None and validity_days > 0 and days_old > validity_days:
                violations.append(
                    ContractViolation(
                        contract_id=self.CONTRACT_ID,
                        severity=self.DEFAULT_SEVERITY.value,
                        entity_id=entity.id,
                        field_name=", ".join(action.fields_enriched),
                        message=(
                            f"Source '{action.source}' is {days_old} days old, "
                            f"exceeding validity window of {validity_days} days"
                        ),
                        attempted_value=action.source_date,
                        expected_range=f"<= {validity_days} days",
                        enricher_source=action.source,
                        remediation=(
                            f"Re-verify source data from '{action.source}' — "
                            f"current data is {days_old - validity_days} days "
                            f"past its validity window"
                        ),
                    )
                )

        return violations

    @staticmethod
    def _get_validity_window(source_key: str) -> int | None:
        """Look up validity window for a source type.

        Tries exact match first, then substring matching against
        SOURCE_VALIDITY_WINDOWS keys.
        """
        if source_key in SOURCE_VALIDITY_WINDOWS:
            return SOURCE_VALIDITY_WINDOWS[source_key]

        # Substring matching: "nist_sp_800-53" → match "nist"
        for key, window in SOURCE_VALIDITY_WINDOWS.items():
            if key in source_key or source_key.startswith(key):
                return window

        return None

    @staticmethod
    def downgrade_confidence(current: ConfidenceLevel, days_old: int) -> ConfidenceLevel:
        """Determine the appropriate confidence level given source age.

        Walks down the confidence ladder until finding a level whose
        staleness window accommodates the source age. This is used by
        the ConfidenceRubricContract to adjust confidence after staleness
        violations are detected.

        Args:
            current: The currently claimed confidence level.
            days_old: How many days old the source is.

        Returns:
            The appropriate confidence level (may be same as current).
        """
        levels = [
            ConfidenceLevel.VERIFIED,
            ConfidenceLevel.HIGH,
            ConfidenceLevel.MEDIUM,
            ConfidenceLevel.LOW,
            ConfidenceLevel.UNVERIFIED,
        ]

        start_idx = levels.index(current)
        for level in levels[start_idx:]:
            max_days = CONFIDENCE_RUBRIC[level].get("max_staleness_days", 0)
            if max_days == 0 or days_old <= max_days:
                return level

        return ConfidenceLevel.UNVERIFIED
