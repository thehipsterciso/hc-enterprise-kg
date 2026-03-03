"""ControllerAgent — central coordinator for the KARMA enrichment pipeline.

Orchestrates the 9-agent pipeline by dispatching messages between agents
in the correct order. Manages tier progression, pipeline state, and
final application of enrichment results to the knowledge graph.

Replaces the monolithic EnrichmentOrchestrator loop with a formal
agent-based coordination protocol.

KARMA mapping: Central Controller Agent — manages the overall pipeline,
coordinates agent communication, and maintains pipeline state.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from domain.base import EntityType
from enrichment.base import (
    EnrichmentResult,
    EnrichmentStats,
    ValidationFailure,
)
from enrichment.coherence_rules import CoherenceSeverity, validate_all_rules
from enrichment.guard.contracts.coherence import CoherenceContract
from enrichment.karma.base_agent import (
    AbstractKarmaAgent,
    AgentMessage,
    AgentRole,
    MessageType,
    PipelineState,
    PipelineStatus,
)
from enrichment.karma.conflict_resolver import ConflictResolverAgent
from enrichment.karma.entity_extractor import EntityExtractorAgent
from enrichment.karma.evaluator import EvaluatorAgent
from enrichment.karma.ingestion import IngestionAgent
from enrichment.karma.reader import ReaderAgent
from enrichment.karma.relationship_extractor import RelExtractorAgent
from enrichment.karma.schema_aligner import SchemaAlignerAgent
from enrichment.karma.summarizer import SummarizerAgent

if TYPE_CHECKING:
    from graph.knowledge_graph import KnowledgeGraph
    from enrichment.graph_context import GraphContextEngine
    from enrichment.osint_agent import OSINTResearchAgent
    from enrichment.provenance_reconciler import ProvenanceReconciler

# UTC timezone
try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc

logger = logging.getLogger(__name__)


class ControllerAgent(AbstractKarmaAgent):
    """Central coordinator for the KARMA enrichment pipeline.

    Instantiates all 8 specialist agents, dispatches messages through
    the pipeline in sequence, and applies validated results to the
    knowledge graph.

    Pipeline flow for each entity:
        Ingestion → Reader → Summarizer → EntityExtractor
        → RelExtractor → SchemaAligner → Evaluator → ConflictResolver
        → Controller (applies to graph)

    After all entities in a tier are processed, the Controller runs
    the CoherenceGuardian for cross-entity validation.

    Args:
        knowledge_graph: The KnowledgeGraph to enrich.
        graph_context_engine: GraphContextEngine for neighborhood retrieval.
        provenance_reconciler: ProvenanceReconciler for confidence tracking.
        osint_agent: Optional OSINTResearchAgent for external research.
    """

    def __init__(
        self,
        knowledge_graph: KnowledgeGraph,
        graph_context_engine: GraphContextEngine,
        provenance_reconciler: ProvenanceReconciler,
        osint_agent: OSINTResearchAgent | None = None,
    ) -> None:
        self._kg = knowledge_graph
        self._graph_context = graph_context_engine
        self._provenance = provenance_reconciler
        self._state = PipelineState()

        # Instantiate specialist agents
        self._agents: dict[AgentRole, AbstractKarmaAgent] = {
            AgentRole.INGESTION: IngestionAgent(knowledge_graph),
            AgentRole.READER: ReaderAgent(
                knowledge_graph, graph_context_engine, osint_agent
            ),
            AgentRole.SUMMARIZER: SummarizerAgent(graph_context_engine),
            AgentRole.ENTITY_EXTRACTOR: EntityExtractorAgent(),
            AgentRole.RELATIONSHIP_EXTRACTOR: RelExtractorAgent(),
            AgentRole.SCHEMA_ALIGNER: SchemaAlignerAgent(),
            AgentRole.EVALUATOR: EvaluatorAgent(),
            AgentRole.CONFLICT_RESOLVER: ConflictResolverAgent(provenance_reconciler),
        }

        # Coherence contract for post-pass validation
        self._coherence_contract = CoherenceContract()

    @property
    def role(self) -> AgentRole:
        return AgentRole.CONTROLLER

    def process(
        self,
        message: AgentMessage,
        state: PipelineState,
    ) -> list[AgentMessage]:
        """Handle CONFLICT_RESOLUTION messages by applying results to graph.

        This is called when a fully validated enrichment result arrives
        back at the controller from the pipeline.

        Args:
            message: CONFLICT_RESOLUTION with validated result.
            state: Current pipeline state.

        Returns:
            Empty list (controller is the terminal agent).
        """
        if message.message_type != MessageType.CONFLICT_RESOLUTION:
            return []

        result: EnrichmentResult | None = message.payload.get("result")
        entity = message.payload.get("entity")
        schema_failures = message.payload.get("schema_failures", [])

        if result is None:
            return []

        # Apply to graph
        if result.has_updates():
            self._apply_result(result)

        return []

    def run_pipeline(self, tier_level: int) -> EnrichmentStats:
        """Run the full KARMA pipeline for a tier level.

        Progressively enriches from Tier 2 through the specified tier,
        running all 9 agents for each entity and then performing
        cross-entity coherence validation.

        Args:
            tier_level: Target tier level (1-5).

        Returns:
            EnrichmentStats with aggregate results.
        """
        if not 1 <= tier_level <= 5:
            raise ValueError(f"Tier level must be 1-5, got {tier_level}")

        overall_stats = EnrichmentStats()
        self._state = PipelineState(
            status=PipelineStatus.RUNNING,
            start_time=datetime.now(UTC),
        )

        # Notify agents of pipeline start
        for agent in self._agents.values():
            agent.on_pipeline_start(self._state)

        logger.info(f"KARMA pipeline: starting enrichment to tier {tier_level}")

        for current_tier in range(2, tier_level + 1):
            self._state.current_tier = current_tier
            self._state.current_phase = f"Tier {current_tier}"

            tier_stats = self._run_tier(current_tier)
            self._merge_stats(overall_stats, tier_stats)

        # Post-pipeline: coherence validation
        self._state.current_phase = "Coherence validation"
        self._run_coherence_validation()

        # Finalize
        self._state.status = PipelineStatus.COMPLETED
        self._state.end_time = datetime.now(UTC)
        overall_stats.end_time = datetime.now(UTC)

        # Notify agents of pipeline end
        for agent in self._agents.values():
            agent.on_pipeline_end(self._state)

        logger.info(
            f"KARMA pipeline complete. Enriched {overall_stats.total_entities_enriched} "
            f"entities, {overall_stats.total_fields_enriched} fields in "
            f"{overall_stats.duration_seconds():.2f}s. "
            f"Rejections: {overall_stats.total_validation_failures} "
            f"({overall_stats.rejection_rate():.1%})"
        )

        return overall_stats

    def _run_tier(self, tier_level: int) -> EnrichmentStats:
        """Run the pipeline for a single tier."""
        tier_stats = EnrichmentStats()
        tier_start = time.time()

        logger.info(f"KARMA pipeline: enriching tier {tier_level}")

        # Phase 1: Ingestion — load entities in generation order
        start_message = AgentMessage(
            sender=AgentRole.CONTROLLER,
            recipient=AgentRole.INGESTION,
            message_type=MessageType.PIPELINE_START,
            payload={"tier": tier_level},
            metadata={"tier": tier_level},
        )

        batch_messages = self._dispatch(AgentRole.INGESTION, start_message)

        # Phase 2: For each entity batch, run through the pipeline
        for batch_msg in batch_messages:
            # Reader: get graph context for each entity in batch
            context_messages = self._dispatch(AgentRole.READER, batch_msg)

            for ctx_msg in context_messages:
                # Summarizer: build holistic profile
                summary_messages = self._dispatch(AgentRole.SUMMARIZER, ctx_msg)

                for sum_msg in summary_messages:
                    # EntityExtractor: run the enricher
                    result_messages = self._dispatch(
                        AgentRole.ENTITY_EXTRACTOR, sum_msg
                    )

                    for res_msg in result_messages:
                        # RelExtractor: process relationships
                        rel_messages = self._dispatch(
                            AgentRole.RELATIONSHIP_EXTRACTOR, res_msg
                        )

                        for rel_msg in rel_messages:
                            # SchemaAligner: validate against Pydantic
                            schema_messages = self._dispatch(
                                AgentRole.SCHEMA_ALIGNER, rel_msg
                            )

                            for schema_msg in schema_messages:
                                # Evaluator: run GraphGuard contracts
                                eval_messages = self._dispatch(
                                    AgentRole.EVALUATOR, schema_msg
                                )

                                for eval_msg in eval_messages:
                                    # ConflictResolver: merge + provenance
                                    resolve_messages = self._dispatch(
                                        AgentRole.CONFLICT_RESOLVER, eval_msg
                                    )

                                    # Controller: apply to graph
                                    for final_msg in resolve_messages:
                                        self.process(final_msg, self._state)
                                        self._update_tier_stats(
                                            tier_stats, final_msg
                                        )

        tier_duration = time.time() - tier_start
        tier_stats.end_time = datetime.now(UTC)
        logger.info(
            f"KARMA tier {tier_level} complete in {tier_duration:.2f}s: "
            f"{tier_stats.total_entities_enriched} entities, "
            f"{tier_stats.total_fields_enriched} fields"
        )

        return tier_stats

    def _dispatch(
        self, agent_role: AgentRole, message: AgentMessage
    ) -> list[AgentMessage]:
        """Dispatch a message to an agent and return its response messages.

        Args:
            agent_role: Which agent to dispatch to.
            message: The message to send.

        Returns:
            List of response messages from the agent.
        """
        agent = self._agents.get(agent_role)
        if agent is None:
            logger.error(f"No agent registered for role {agent_role}")
            return []

        self._state.messages_exchanged += 1

        try:
            return agent.process(message, self._state)
        except Exception as e:
            logger.error(
                f"Agent {agent_role.value} failed: {e}", exc_info=True
            )
            self._state.errors.append(f"{agent_role.value}: {e}")
            return []

    def _apply_result(self, result: EnrichmentResult) -> None:
        """Apply a validated enrichment result to the knowledge graph."""
        entity = self._kg.get_entity(result.entity_id)
        if not entity:
            logger.warning(f"Entity {result.entity_id} not found")
            return

        # Apply field updates
        if result.field_updates:
            try:
                self._kg.update_entity(result.entity_id, **result.field_updates)
            except Exception as e:
                logger.error(
                    f"Error updating entity {result.entity_id}: {e}"
                )

        # Apply provenance
        if result.actions:
            provenance_field = self._provenance.get_provenance_field_name(
                result.entity_type
            )
            for action in result.actions:
                try:
                    provenance = self._provenance.record_enrichment(
                        result.entity_id,
                        result.entity_type,
                        action.fields_enriched,
                        action.source,
                        action.methodology,
                        action.confidence,
                    )
                    self._kg.update_entity(
                        result.entity_id, **{provenance_field: provenance}
                    )
                except Exception as e:
                    logger.debug(f"Provenance update failed for {result.entity_id}: {e}")

    def _run_coherence_validation(self) -> None:
        """Run cross-entity coherence validation after enrichment."""
        logger.debug("Running cross-entity coherence validation")
        try:
            violations = validate_all_rules(self._kg)
            if violations:
                error_count = sum(
                    1 for v in violations
                    if v.severity == CoherenceSeverity.ERROR
                )
                warn_count = sum(
                    1 for v in violations
                    if v.severity == CoherenceSeverity.WARNING
                )
                logger.info(
                    f"Coherence validation: {len(violations)} violations "
                    f"({error_count} errors, {warn_count} warnings)"
                )
                for violation in violations[:10]:
                    logger.debug(
                        f"  [{violation.severity.value}] {violation.rule_id}: "
                        f"{violation.description}"
                    )
        except Exception as e:
            logger.error(f"Coherence validation error: {e}", exc_info=True)

    def _update_tier_stats(
        self, stats: EnrichmentStats, message: AgentMessage
    ) -> None:
        """Update tier stats from a CONFLICT_RESOLUTION message."""
        result: EnrichmentResult | None = message.payload.get("result")
        schema_failures = message.payload.get("schema_failures", [])
        quality_report = message.payload.get("quality_report")

        if result and result.has_updates():
            stats.total_entities_enriched += 1
            stats.total_fields_enriched += len(result.field_updates)
            stats.total_relationships_suggested += len(
                result.relationship_suggestions
            )
            stats.total_gaps_identified += len(result.known_gaps)
            stats.actions.extend(result.actions)

        # Track validation failures from schema alignment
        if schema_failures:
            stats.total_validation_failures += len(schema_failures)
            stats.validation_failures.extend(schema_failures)

        # Track fields attempted
        fields_attempted = message.payload.get("fields_attempted", 0)
        if fields_attempted:
            stats.total_fields_attempted += fields_attempted

        # Track quality report rejections
        fields_rejected = message.payload.get("fields_rejected", 0)
        if fields_rejected:
            stats.total_validation_failures += fields_rejected

    @staticmethod
    def _merge_stats(overall: EnrichmentStats, tier: EnrichmentStats) -> None:
        """Merge tier stats into overall stats."""
        overall.total_entities_enriched += tier.total_entities_enriched
        overall.total_fields_enriched += tier.total_fields_enriched
        overall.total_relationships_suggested += tier.total_relationships_suggested
        overall.total_gaps_identified += tier.total_gaps_identified
        overall.total_fields_attempted += tier.total_fields_attempted
        overall.total_validation_failures += tier.total_validation_failures
        overall.validation_failures.extend(tier.validation_failures)
        overall.actions.extend(tier.actions)

    @property
    def state(self) -> PipelineState:
        """Return the current pipeline state."""
        return self._state

    @property
    def agents(self) -> dict[AgentRole, AbstractKarmaAgent]:
        """Return all registered agents."""
        return self._agents
