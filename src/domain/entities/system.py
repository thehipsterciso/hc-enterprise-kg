"""System entity representing applications, servers, and IT systems."""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import Field

from domain.base import BaseEntity, EntityType


class System(BaseEntity):
    """Represents an IT system, application, or server."""

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.SYSTEM
    entity_type: Literal[EntityType.SYSTEM] = EntityType.SYSTEM

    system_type: str = ""  # server, application, database, saas, etc.
    hostname: str = ""
    ip_address: str = ""
    os: str = ""
    version: str = ""
    vendor_id: str | None = None
    environment: str = "production"  # production, staging, development, test
    criticality: str = "medium"  # low, medium, high, critical
    is_internet_facing: bool = False
    owner_id: str | None = None
    department_id: str | None = None
    network_id: str | None = None
    ports: list[int] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
