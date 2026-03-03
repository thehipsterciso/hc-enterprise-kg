"""CompletenessContract — weighted completeness threshold enforcement.

Validates that entities meet minimum completeness thresholds per tier.
Uses weighted completeness scoring where critical fields count 3x,
operational fields 2x, and metadata fields 1x.

This contract operates as a post-enrichment check: after all field
updates are proposed, it verifies that the entity would meet the
completeness target for its tier. It does not block individual field
updates but reports whether the overall enrichment is sufficient.

Contract ID: GG-COMPL-001
Severity: WARNING (reports insufficient completeness; doesn't block)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from enrichment.base import FieldCategory
from enrichment.guard.contract import ContractSeverity, QualityContract
from enrichment.guard.reports import ContractViolation

if TYPE_CHECKING:
    from domain.base import BaseEntity

# Minimum weighted completeness thresholds per tier (percentage)
TIER_COMPLETENESS_THRESHOLDS: dict[int, float] = {
    1: 0.10,  # Tier 1: 10% — identity fields only
    2: 0.30,  # Tier 2: 30% — operational fields populated
    3: 0.50,  # Tier 3: 50% — cross-entity coherence
    4: 0.70,  # Tier 4: 70% — quantitative metrics
    5: 0.85,  # Tier 5: 85% — full fidelity (some gaps acceptable)
}

# Field category weights for completeness calculation
CATEGORY_WEIGHTS: dict[FieldCategory, float] = {
    FieldCategory.CRITICAL: 3.0,
    FieldCategory.OPERATIONAL: 2.0,
    FieldCategory.METADATA: 1.0,
}


class CompletenessContract(QualityContract):
    """Validates weighted completeness against tier thresholds.

    After enrichment, calculates the weighted completeness of the entity
    (considering the proposed field updates) and checks it against the
    minimum threshold for the target tier.
    """

    CONTRACT_ID = "GG-COMPL-001"
    DESCRIPTION = "Weighted completeness threshold enforcement per tier"
    DEFAULT_SEVERITY = ContractSeverity.WARNING

    def evaluate(
        self,
        entity: BaseEntity,
        field_updates: dict[str, Any],
        **kwargs: Any,
    ) -> list[ContractViolation]:
        """Check weighted completeness against tier threshold.

        Expects kwargs to contain:
            tier: int — the target enrichment tier (1-5).
            tier_fields: list[str] — fields expected at this tier.
            field_categories: dict[str, FieldCategory] — category per field.

        Args:
            entity: The entity being enriched.
            field_updates: Proposed field → value updates.
            **kwargs: Must include tier, tier_fields, field_categories.

        Returns:
            List of ContractViolation if completeness is below threshold.
        """
        tier: int = kwargs.get("tier", 2)
        tier_fields: list[str] = kwargs.get("tier_fields", [])
        field_categories: dict[str, FieldCategory] = kwargs.get("field_categories", {})

        if not tier_fields:
            return []

        threshold = TIER_COMPLETENESS_THRESHOLDS.get(tier, 0.30)

        # Calculate weighted completeness considering both existing
        # entity fields and proposed updates
        entity_dict = entity.model_dump() if hasattr(entity, "model_dump") else {}

        # Merge existing values with proposed updates
        merged = {}
        for f in tier_fields:
            current = entity_dict.get(f)
            proposed = field_updates.get(f)
            merged[f] = proposed if proposed is not None else current

        # Calculate weighted completeness
        weighted_filled = 0.0
        weighted_total = 0.0

        for f in tier_fields:
            category = field_categories.get(f, FieldCategory.METADATA)
            weight = CATEGORY_WEIGHTS.get(category, 1.0)
            weighted_total += weight

            value = merged.get(f)
            if value is not None and value != "" and value != []:
                weighted_filled += weight

        if weighted_total == 0:
            return []

        completeness = weighted_filled / weighted_total

        violations: list[ContractViolation] = []

        if completeness < threshold:
            # Find missing critical fields
            missing_critical = [
                f
                for f in tier_fields
                if field_categories.get(f) == FieldCategory.CRITICAL
                and merged.get(f) in (None, "", [])
            ]

            violations.append(
                ContractViolation(
                    contract_id=self.CONTRACT_ID,
                    severity=self.DEFAULT_SEVERITY.value,
                    entity_id=entity.id,
                    field_name="(overall)",
                    message=(
                        f"Weighted completeness {completeness:.1%} is below "
                        f"tier {tier} threshold of {threshold:.0%}. "
                        f"Missing critical fields: {missing_critical[:5]}"
                    ),
                    attempted_value=f"{completeness:.1%}",
                    expected_range=f">= {threshold:.0%}",
                    remediation=(
                        f"Enrich {len(missing_critical)} missing critical "
                        f"fields to meet tier {tier} threshold"
                    ),
                )
            )

        return violations
