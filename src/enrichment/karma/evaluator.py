"""EvaluatorAgent — runs GraphGuard quality contracts on enrichment results.

Integrates the GraphGuard quality layer into the KARMA pipeline. For each
enrichment result, runs the PostEnrichmentGuardian contracts (plausibility,
staleness, confidence rubric) and produces a QualityValidationReport.

KARMA mapping: Evaluator Agent — assesses the quality and correctness
of the enriched knowledge graph entries.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from enrichment.base import EnrichmentResult, ValidationFailure
from enrichment.guard.contracts.confidence_rubric import ConfidenceRubricContract
from enrichment.guard.contracts.plausibility import PlausibilityContract
from enrichment.guard.contracts.staleness import StalenessContract
from enrichment.guard.guardian import AbstractGuardian, GuardianPhase
from enrichment.karma.base_agent import (
    AbstractKarmaAgent,
    AgentMessage,
    AgentRole,
    MessageType,
    PipelineState,
)

if TYPE_CHECKING:
    from enrichment.guard.contract import QualityContract

logger = logging.getLogger(__name__)


class PostEnrichmentGuardian(AbstractGuardian):
    """Guardian that runs after entity enrichment, before graph update.

    Executes plausibility, staleness, and confidence rubric contracts.
    """

    def __init__(self) -> None:
        self._contracts = [
            PlausibilityContract(),
            StalenessContract(),
            ConfidenceRubricContract(),
        ]

    @property
    def phase(self) -> GuardianPhase:
        return GuardianPhase.POST_ENRICHMENT

    @property
    def contracts(self) -> list[QualityContract]:
        return self._contracts


class EvaluatorAgent(AbstractKarmaAgent):
    """Runs GraphGuard quality contracts on each enrichment result.

    For each SCHEMA_VALIDATION message:
    1. Runs the PostEnrichmentGuardian (plausibility + staleness + rubric)
    2. Collects any validation failures
    3. Filters out fields that fail ERROR-severity contracts
    4. Produces an EVALUATION_REPORT with the filtered result + report

    The EvaluatorAgent replaces the monolithic AdversarialValidator.validate()
    with a composable, contract-based validation pipeline.
    """

    def __init__(self) -> None:
        self._guardian = PostEnrichmentGuardian()

    @property
    def role(self) -> AgentRole:
        return AgentRole.EVALUATOR

    def process(
        self,
        message: AgentMessage,
        state: PipelineState,
    ) -> list[AgentMessage]:
        """Run quality contracts and filter enrichment results.

        Responds to SCHEMA_VALIDATION messages by running the guardian
        contracts and producing EVALUATION_REPORT messages.

        Args:
            message: SCHEMA_VALIDATION with validated result.
            state: Current pipeline state.

        Returns:
            List containing one EVALUATION_REPORT message.
        """
        if message.message_type != MessageType.SCHEMA_VALIDATION:
            return []

        entity = message.payload.get("entity")
        result: EnrichmentResult | None = message.payload.get("result")
        schema_failures: list[ValidationFailure] = message.payload.get("schema_failures", [])

        if entity is None or result is None:
            return []

        # Run GraphGuard contracts via the guardian
        filtered_updates, quality_report = self._guardian.validate(
            entity,
            result.field_updates,
            actions=result.actions,
        )

        # Build filtered result with only validated fields
        filtered_result = EnrichmentResult(
            entity_id=result.entity_id,
            entity_type=result.entity_type,
            field_updates=filtered_updates,
            provenance_update=result.provenance_update,
            relationship_suggestions=result.relationship_suggestions,
            known_gaps=result.known_gaps,
            actions=result.actions,
        )

        # Log summary
        rejected_count = len(result.field_updates) - len(filtered_updates)
        if rejected_count > 0:
            logger.info(
                f"EvaluatorAgent: {rejected_count} field(s) rejected for "
                f"{entity.entity_type} {entity.id}"
            )

        return [
            self.create_message(
                recipient=AgentRole.CONFLICT_RESOLVER,
                message_type=MessageType.EVALUATION_REPORT,
                payload={
                    "entity_id": result.entity_id,
                    "entity_type": message.payload.get("entity_type", ""),
                    "entity": entity,
                    "result": filtered_result,
                    "schema_failures": schema_failures,
                    "quality_report": quality_report,
                    "fields_attempted": message.payload.get("fields_attempted", 0),
                    "fields_rejected": rejected_count,
                },
                correlation_id=message.correlation_id,
                metadata=message.metadata,
            )
        ]
