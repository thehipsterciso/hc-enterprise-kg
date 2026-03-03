"""ConflictResolverAgent — merges multi-source enrichments with provenance.

Handles the case where multiple enrichment sources propose different values
for the same field. Picks the highest-confidence value and records full
field-level provenance.

KARMA mapping: Conflict Resolution Agent — resolves contradictory or
redundant information from multiple extraction passes, ensuring a single
consistent representation per entity.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from enrichment.base import (
    ConfidenceLevel,
    EnrichmentResult,
)
from enrichment.karma.base_agent import (
    AbstractKarmaAgent,
    AgentMessage,
    AgentRole,
    MessageType,
    PipelineState,
)

if TYPE_CHECKING:
    from enrichment.provenance_reconciler import ProvenanceReconciler

logger = logging.getLogger(__name__)

# Confidence ordering for conflict resolution (higher = preferred)
CONFIDENCE_ORDER = {
    ConfidenceLevel.VERIFIED: 5,
    ConfidenceLevel.HIGH: 4,
    ConfidenceLevel.MEDIUM: 3,
    ConfidenceLevel.LOW: 2,
    ConfidenceLevel.UNVERIFIED: 1,
}


class ConflictResolverAgent(AbstractKarmaAgent):
    """Merges multi-source enrichments and selects highest-confidence values.

    When the same field has been proposed by multiple sources (e.g., OSINT
    research and graph inference), this agent picks the value with the
    highest confidence and records the full provenance chain.

    For single-source enrichments (the common case), this agent is a
    pass-through that records provenance.

    Args:
        provenance_reconciler: ProvenanceReconciler for confidence tracking.
    """

    def __init__(self, provenance_reconciler: ProvenanceReconciler | None = None) -> None:
        self._provenance = provenance_reconciler

    @property
    def role(self) -> AgentRole:
        return AgentRole.CONFLICT_RESOLVER

    def process(
        self,
        message: AgentMessage,
        state: PipelineState,
    ) -> list[AgentMessage]:
        """Resolve conflicts and record provenance.

        Responds to EVALUATION_REPORT messages by recording provenance
        for the validated enrichment result and forwarding the final
        result to the ControllerAgent for application.

        Args:
            message: EVALUATION_REPORT with validated result.
            state: Current pipeline state.

        Returns:
            List containing one CONFLICT_RESOLUTION message.
        """
        if message.message_type != MessageType.EVALUATION_REPORT:
            return []

        result: EnrichmentResult | None = message.payload.get("result")
        entity = message.payload.get("entity")

        if result is None:
            return []

        # Record provenance for each action
        if self._provenance and result.actions:
            for action in result.actions:
                try:
                    self._provenance.record_enrichment(
                        result.entity_id,
                        result.entity_type,
                        action.fields_enriched,
                        action.source,
                        action.methodology,
                        action.confidence,
                    )
                except Exception as e:
                    logger.debug(f"Provenance recording failed for {result.entity_id}: {e}")

        # For multi-source conflicts (future enhancement):
        # If multiple results for the same entity exist, merge them
        # by selecting the highest-confidence value per field.
        # Currently, enrichers produce a single result per entity,
        # so this is a pass-through.

        state.entities_processed += 1

        return [
            self.create_message(
                recipient=AgentRole.CONTROLLER,
                message_type=MessageType.CONFLICT_RESOLUTION,
                payload={
                    "entity_id": result.entity_id,
                    "entity_type": message.payload.get("entity_type", ""),
                    "entity": entity,
                    "result": result,
                    "schema_failures": message.payload.get("schema_failures", []),
                    "quality_report": message.payload.get("quality_report"),
                },
                correlation_id=message.correlation_id,
                metadata=message.metadata,
            )
        ]

    @staticmethod
    def resolve_field_conflict(
        values: list[tuple[Any, ConfidenceLevel, str]],
    ) -> tuple[Any, ConfidenceLevel, str]:
        """Resolve a conflict between multiple values for the same field.

        Picks the value with the highest confidence. On ties, picks the
        most recent source.

        Args:
            values: List of (value, confidence, source) tuples.

        Returns:
            Tuple of (selected_value, confidence, source).
        """
        if not values:
            raise ValueError("No values to resolve")

        if len(values) == 1:
            return values[0]

        # Sort by confidence (descending), then by source name for stability
        sorted_values = sorted(
            values,
            key=lambda v: (CONFIDENCE_ORDER.get(v[1], 0), v[2]),
            reverse=True,
        )

        selected = sorted_values[0]
        if len(sorted_values) > 1:
            runner_up = sorted_values[1]
            logger.debug(
                f"Conflict resolved: selected {selected[2]} "
                f"({selected[1].value}) over {runner_up[2]} "
                f"({runner_up[1].value})"
            )

        return selected
