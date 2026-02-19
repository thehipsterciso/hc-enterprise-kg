"""Threat actor entity representing adversaries and threat groups."""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import Field

from hc_enterprise_kg.domain.base import BaseEntity, EntityType


class ThreatActor(BaseEntity):
    """Represents a threat actor or adversary group."""

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.THREAT_ACTOR
    entity_type: Literal[EntityType.THREAT_ACTOR] = EntityType.THREAT_ACTOR

    actor_type: str = ""  # nation_state, cybercriminal, hacktivist, insider, apt
    sophistication: str = "medium"  # low, medium, high, advanced
    motivation: str = ""  # financial, espionage, disruption, ideological
    origin_country: str = ""
    first_seen: str | None = None
    last_seen: str | None = None
    aliases: list[str] = Field(default_factory=list)
    ttps: list[str] = Field(default_factory=list)  # MITRE ATT&CK TTPs
    target_industries: list[str] = Field(default_factory=list)
    iocs: list[str] = Field(default_factory=list)
