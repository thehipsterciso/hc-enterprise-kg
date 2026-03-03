"""CoherenceContract — cross-entity invariant validation.

Wraps the existing coherence_rules.py (6 rules) as a formal GraphGuard
contract. Validates that enrichment results maintain cross-entity
consistency: person skills align with role requirements, system costs
correlate with criticality, vendor risk matches contract exposure, etc.

Unlike other contracts that validate individual field updates, the
CoherenceContract operates on the full knowledge graph and is invoked
by the CoherenceGuardian after a complete enrichment pass.

Contract ID: GG-COHER-001
Severity: WARNING (logs inconsistencies; doesn't block individual updates)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from domain.base import BaseEntity

from enrichment.coherence_rules import (
    ALL_COHERENCE_RULES,
    CoherenceSeverity,
    CoherenceViolation,
    validate_all_rules,
)
from enrichment.guard.contract import ContractSeverity, QualityContract
from enrichment.guard.reports import ContractViolation as GGViolation

if TYPE_CHECKING:
    from graph.knowledge_graph import KnowledgeGraph


class CoherenceContract(QualityContract):
    """Validates cross-entity coherence invariants across the knowledge graph.

    Delegates to the 6 existing coherence rules:
        1. PersonSkillsAlignWithRole (COHERENCE-001)
        2. SystemCostMatchesCriticality (COHERENCE-002)
        3. VendorRiskMatchesContractValue (COHERENCE-003)
        4. ControlEffectivenessMatchesRiskResidual (COHERENCE-004)
        5. TemporalConsistency (COHERENCE-005)
        6. DataClassificationConsistency (COHERENCE-006)
    """

    CONTRACT_ID = "GG-COHER-001"
    DESCRIPTION = "Cross-entity coherence invariant validation"
    DEFAULT_SEVERITY = ContractSeverity.WARNING

    def evaluate(
        self,
        entity: BaseEntity,
        field_updates: dict[str, Any],
        **kwargs: Any,
    ) -> list[GGViolation]:
        """Run all coherence rules against the knowledge graph.

        Expects kwargs to contain:
            knowledge_graph: KnowledgeGraph — the full graph to validate.

        For per-entity validation (no knowledge_graph provided), returns
        an empty list. The CoherenceContract is designed to be run by the
        CoherenceGuardian at the graph level, not per-entity.

        Args:
            entity: Ignored for graph-level validation (required by ABC).
            field_updates: Ignored for graph-level validation.
            **kwargs: Must include 'knowledge_graph' for full validation.

        Returns:
            List of GGViolation mapped from coherence rule violations.
        """
        kg: KnowledgeGraph | None = kwargs.get("knowledge_graph")
        if kg is None:
            return []

        coherence_violations = validate_all_rules(kg)
        return [self._map_violation(cv) for cv in coherence_violations]

    def evaluate_graph(self, kg: KnowledgeGraph) -> list[GGViolation]:
        """Convenience method to validate an entire knowledge graph.

        Args:
            kg: The knowledge graph to validate.

        Returns:
            List of GGViolation mapped from all coherence rule violations.
        """
        coherence_violations = validate_all_rules(kg)
        return [self._map_violation(cv) for cv in coherence_violations]

    def _map_violation(self, cv: CoherenceViolation) -> GGViolation:
        """Map a CoherenceViolation to a GraphGuard ContractViolation."""
        # Map coherence severity to GraphGuard severity
        severity_map = {
            CoherenceSeverity.ERROR: "error",
            CoherenceSeverity.WARNING: "warning",
            CoherenceSeverity.INFO: "info",
        }

        return GGViolation(
            contract_id=f"{self.CONTRACT_ID}/{cv.rule_id}",
            severity=severity_map.get(cv.severity, "warning"),
            entity_id=cv.affected_entities[0] if cv.affected_entities else "",
            field_name="",  # Coherence violations are cross-entity
            message=cv.description,
            remediation=cv.remediation,
        )
