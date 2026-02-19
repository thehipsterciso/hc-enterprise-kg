"""Incident entity representing security incidents and events."""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import Field

from domain.base import BaseEntity, EntityType


class Incident(BaseEntity):
    """Represents a security incident."""

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.INCIDENT
    entity_type: Literal[EntityType.INCIDENT] = EntityType.INCIDENT

    incident_type: str = ""  # data_breach, malware, phishing, dos, insider_threat
    severity: str = "medium"  # low, medium, high, critical
    status: str = "open"  # open, investigating, contained, resolved, closed
    detection_method: str = ""  # siem, ids, user_report, threat_intel, audit
    occurred_at: str | None = None
    detected_at: str | None = None
    resolved_at: str | None = None
    impact_description: str = ""
    root_cause: str = ""
    affected_system_ids: list[str] = Field(default_factory=list)
    affected_data_asset_ids: list[str] = Field(default_factory=list)
    threat_actor_id: str | None = None
    responder_ids: list[str] = Field(default_factory=list)
    lessons_learned: str = ""
