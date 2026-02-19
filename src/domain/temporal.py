"""Temporal event tracking for knowledge graph mutations."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class MutationType(str, Enum):
    """Types of mutations that can occur on the knowledge graph."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LINK = "link"
    UNLINK = "unlink"


class GraphEvent(BaseModel):
    """Immutable record of a mutation to the knowledge graph."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    mutation_type: MutationType
    entity_type: str | None = None
    entity_id: str | None = None
    relationship_id: str | None = None
    before_snapshot: dict | None = None
    after_snapshot: dict | None = None
    source: str = "system"
