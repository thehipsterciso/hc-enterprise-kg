"""Base agent abstraction for the KARMA multi-agent pipeline.

Defines the AbstractKarmaAgent interface, inter-agent messaging protocol,
and pipeline state management. All KARMA agents inherit from this base
and communicate through typed AgentMessage objects.

The design follows KARMA's central controller pattern: the ControllerAgent
dispatches messages to specialist agents, which process their input and
return results through the same messaging protocol.

Reference: Lu et al., "KARMA: Augmenting Embodied AI Agents with
Long-and-Short Term Memory for Multi-Agent Knowledge Graph Enrichment",
NeurIPS 2025.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

# UTC timezone (Python 3.11+) or fallback
try:
    from datetime import UTC
except ImportError:
    UTC = UTC

logger = logging.getLogger(__name__)


class AgentRole(StrEnum):
    """Role identifiers for each agent in the KARMA pipeline."""

    CONTROLLER = "controller"
    INGESTION = "ingestion"
    READER = "reader"
    SUMMARIZER = "summarizer"
    ENTITY_EXTRACTOR = "entity_extractor"
    RELATIONSHIP_EXTRACTOR = "relationship_extractor"
    SCHEMA_ALIGNER = "schema_aligner"
    CONFLICT_RESOLVER = "conflict_resolver"
    EVALUATOR = "evaluator"


class MessageType(StrEnum):
    """Types of messages exchanged between agents."""

    # Pipeline lifecycle
    PIPELINE_START = "pipeline_start"
    PIPELINE_COMPLETE = "pipeline_complete"
    PIPELINE_ERROR = "pipeline_error"

    # Agent-to-agent data flow
    ENTITY_BATCH = "entity_batch"
    ENTITY_CONTEXT = "entity_context"
    ENTITY_SUMMARY = "entity_summary"
    ENRICHMENT_RESULT = "enrichment_result"
    RELATIONSHIP_SUGGESTION = "relationship_suggestion"
    SCHEMA_VALIDATION = "schema_validation"
    CONFLICT_RESOLUTION = "conflict_resolution"
    EVALUATION_REPORT = "evaluation_report"

    # Control signals
    TIER_ADVANCE = "tier_advance"
    AGENT_READY = "agent_ready"
    AGENT_ERROR = "agent_error"


class PipelineStatus(StrEnum):
    """Status of the enrichment pipeline."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentMessage:
    """Typed message exchanged between KARMA agents.

    Every inter-agent communication goes through this structure,
    providing full traceability of data flow through the pipeline.

    Attributes:
        sender: The AgentRole that created this message.
        recipient: The AgentRole this message is addressed to.
        message_type: Categorization of the message content.
        payload: The actual data being communicated (varies by message type).
        correlation_id: Links related messages across agents (e.g., all
            messages for a single entity's enrichment share a correlation_id).
        timestamp: When the message was created.
        metadata: Optional additional context (tier, profile, entity_id, etc.).
    """

    sender: AgentRole
    recipient: AgentRole
    message_type: MessageType
    payload: dict[str, Any] = field(default_factory=dict)
    correlation_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineState:
    """Shared state for the KARMA pipeline.

    Tracks which entities have been processed, which tier is active,
    cumulative statistics, and any errors encountered. The ControllerAgent
    owns this state and passes a read-only view to other agents.

    Attributes:
        status: Current pipeline status.
        current_tier: The enrichment tier being processed (1-5).
        entities_queued: Total entities queued for processing.
        entities_processed: Entities that have completed the pipeline.
        entities_failed: Entities that encountered errors.
        messages_exchanged: Total inter-agent messages sent.
        current_phase: Human-readable description of the current phase.
        errors: List of error messages encountered.
        start_time: When the pipeline started.
        end_time: When the pipeline completed (or None if still running).
    """

    status: PipelineStatus = PipelineStatus.IDLE
    current_tier: int = 2
    entities_queued: int = 0
    entities_processed: int = 0
    entities_failed: int = 0
    messages_exchanged: int = 0
    current_phase: str = ""
    errors: list[str] = field(default_factory=list)
    start_time: datetime | None = None
    end_time: datetime | None = None

    def duration_seconds(self) -> float:
        """Return pipeline duration in seconds."""
        if self.start_time is None:
            return 0.0
        end = self.end_time or datetime.now(UTC)
        return (end - self.start_time).total_seconds()

    def progress_pct(self) -> float:
        """Return processing progress as a percentage."""
        if self.entities_queued == 0:
            return 0.0
        return (self.entities_processed / self.entities_queued) * 100.0


class AbstractKarmaAgent(ABC):
    """Base class for all KARMA pipeline agents.

    Each agent has a defined role, processes incoming messages, and
    produces outgoing messages. The ControllerAgent dispatches messages
    to agents based on the pipeline phase.

    Subclasses must implement:
        - role: The agent's AgentRole
        - process(): Handle an incoming message and return response(s)

    Agents are stateless between pipeline runs. Per-run state is held
    in PipelineState (owned by the ControllerAgent).
    """

    @property
    @abstractmethod
    def role(self) -> AgentRole:
        """The agent's role identifier."""
        ...

    @abstractmethod
    def process(
        self,
        message: AgentMessage,
        state: PipelineState,
    ) -> list[AgentMessage]:
        """Process an incoming message and return response messages.

        Args:
            message: The incoming message to process.
            state: Read-only view of the pipeline state.

        Returns:
            List of messages to send to other agents (may be empty).
        """
        ...

    def on_pipeline_start(self, state: PipelineState) -> None:  # noqa: B027
        """Hook called when the pipeline starts. Override for initialization."""

    def on_pipeline_end(self, state: PipelineState) -> None:  # noqa: B027
        """Hook called when the pipeline completes. Override for cleanup."""

    def create_message(
        self,
        recipient: AgentRole,
        message_type: MessageType,
        payload: dict[str, Any] | None = None,
        correlation_id: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> AgentMessage:
        """Convenience method to create a message from this agent.

        Args:
            recipient: Target agent role.
            message_type: Type of message.
            payload: Message data.
            correlation_id: Correlation ID for tracing.
            metadata: Additional context.

        Returns:
            A new AgentMessage with sender set to this agent's role.
        """
        return AgentMessage(
            sender=self.role,
            recipient=recipient,
            message_type=message_type,
            payload=payload or {},
            correlation_id=correlation_id,
            metadata=metadata or {},
        )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} role={self.role.value}>"
