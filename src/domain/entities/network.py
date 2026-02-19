"""Network entity representing network segments and zones."""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import Field

from domain.base import BaseEntity, EntityType


class Network(BaseEntity):
    """Represents a network segment or zone."""

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.NETWORK
    entity_type: Literal[EntityType.NETWORK] = EntityType.NETWORK

    cidr: str = ""
    zone: str = "internal"  # dmz, internal, restricted, guest, external
    vlan_id: int | None = None
    gateway: str = ""
    dns_servers: list[str] = Field(default_factory=list)
    is_monitored: bool = True
    location_id: str | None = None
