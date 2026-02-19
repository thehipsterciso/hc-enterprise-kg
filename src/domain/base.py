"""Core domain model: base types, enums, and mixins for the knowledge graph."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field


class EntityType(StrEnum):
    """Enumeration of all entity types in the knowledge graph."""

    PERSON = "person"
    DEPARTMENT = "department"
    ROLE = "role"
    SYSTEM = "system"
    NETWORK = "network"
    DATA_ASSET = "data_asset"
    POLICY = "policy"
    VENDOR = "vendor"
    LOCATION = "location"
    VULNERABILITY = "vulnerability"
    THREAT_ACTOR = "threat_actor"
    INCIDENT = "incident"


class RelationshipType(StrEnum):
    """Enumeration of all relationship types in the knowledge graph."""

    # Organizational
    WORKS_IN = "works_in"
    MANAGES = "manages"
    REPORTS_TO = "reports_to"
    HAS_ROLE = "has_role"
    MEMBER_OF = "member_of"
    # Technical
    HOSTS = "hosts"
    CONNECTS_TO = "connects_to"
    DEPENDS_ON = "depends_on"
    STORES = "stores"
    RUNS_ON = "runs_on"
    # Security
    GOVERNS = "governs"
    EXPLOITS = "exploits"
    TARGETS = "targets"
    MITIGATES = "mitigates"
    AFFECTS = "affects"
    # Operational
    PROVIDES_SERVICE = "provides_service"
    LOCATED_AT = "located_at"
    SUPPLIED_BY = "supplied_by"
    RESPONSIBLE_FOR = "responsible_for"


class TemporalMixin(BaseModel):
    """Mixin that adds temporal tracking to any entity or relationship."""

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    version: int = 1


class BaseEntity(TemporalMixin):
    """Abstract base for all knowledge graph entities."""

    model_config = ConfigDict(extra="allow")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity_type: EntityType
    name: str
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    ENTITY_TYPE: ClassVar[EntityType]


class BaseRelationship(TemporalMixin):
    """Abstract base for all knowledge graph relationships."""

    model_config = ConfigDict(extra="allow")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    relationship_type: RelationshipType
    source_id: str
    target_id: str
    weight: float = 1.0
    confidence: float = 1.0
    properties: dict[str, Any] = Field(default_factory=dict)
