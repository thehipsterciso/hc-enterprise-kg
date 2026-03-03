"""PlausibilityContract — domain bounds validation for enrichment field values.

Extracted from AdversarialValidator._check_plausibility(). Validates that
numeric field values fall within domain-specific plausible ranges.

Examples of what this contract catches:
    - CVSS score of 15 (max is 10.0)
    - Negative headcount
    - Annual salary of $50M (cap at $15M)
    - Availability target of 200% (max is 100%)

Contract ID: GG-PLAUS-001
Severity: ERROR (blocks the update — implausible values never reach the graph)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from enrichment.guard.contract import ContractSeverity, QualityContract
from enrichment.guard.reports import ContractViolation

if TYPE_CHECKING:
    from domain.base import BaseEntity


class PlausibilityContract(QualityContract):
    """Validates numeric field values against domain-specific bounds.

    Uses the same PLAUSIBILITY_BOUNDS as the original AdversarialValidator,
    now expressed as a declarative contract.
    """

    CONTRACT_ID = "GG-PLAUS-001"
    DESCRIPTION = "Domain bounds check for numeric field values"
    DEFAULT_SEVERITY = ContractSeverity.ERROR

    # Domain-specific bounds: entity_type → field_name → (min, max)
    PLAUSIBILITY_BOUNDS: ClassVar[dict[str, dict[str, tuple[float, float]]]] = {
        "person": {
            "annual_compensation": (15_000, 15_000_000),
            "years_experience": (0, 60),
            "direct_reports_count": (0, 500),
        },
        "system": {
            "annual_cost": (0, 500_000_000),
            "availability_target": (0, 100),
        },
        "risk": {
            "probability": (0.0, 1.0),
            "impact_score": (0, 100),
            "cvss_score": (0.0, 10.0),
        },
        "vulnerability": {
            "cvss_score": (0.0, 10.0),
        },
        "department": {
            "head_count": (0, 100_000),
            "budget": (0, 50_000_000_000),
        },
        "vendor": {
            "annual_spend": (0, 10_000_000_000),
        },
    }

    def evaluate(
        self,
        entity: BaseEntity,
        field_updates: dict[str, Any],
        **kwargs: Any,
    ) -> list[ContractViolation]:
        """Check each numeric field update against plausibility bounds.

        Args:
            entity: The entity receiving the updates.
            field_updates: Proposed field → value mappings.

        Returns:
            List of ContractViolation for any out-of-bounds values.
        """
        violations: list[ContractViolation] = []

        entity_type_str = self._normalize_entity_type(entity)
        bounds = self.PLAUSIBILITY_BOUNDS.get(entity_type_str, {})

        for field_name, value in field_updates.items():
            if field_name not in bounds:
                continue
            if not isinstance(value, int | float):
                continue

            low, high = bounds[field_name]
            if value < low or value > high:
                violations.append(
                    ContractViolation(
                        contract_id=self.CONTRACT_ID,
                        severity=self.DEFAULT_SEVERITY.value,
                        entity_id=entity.id,
                        field_name=field_name,
                        message=(
                            f"Value {value} for '{field_name}' on "
                            f"{entity_type_str} outside plausible range "
                            f"[{low}, {high}]"
                        ),
                        attempted_value=value,
                        expected_range=f"[{low}, {high}]",
                        remediation=(f"Ensure {field_name} is between {low} and {high}"),
                    )
                )

        return violations

    @staticmethod
    def _normalize_entity_type(entity: BaseEntity) -> str:
        """Normalize entity type to lowercase string for bounds lookup."""
        et = entity.entity_type
        if isinstance(et, str):
            return et.lower()
        if hasattr(et, "value"):
            return et.value.lower()
        return str(et).lower()
