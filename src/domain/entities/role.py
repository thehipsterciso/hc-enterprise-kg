"""Role entity representing job roles and access levels."""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import Field

from domain.base import BaseEntity, EntityType


class Role(BaseEntity):
    """Represents a role within the organization."""

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.ROLE
    entity_type: Literal[EntityType.ROLE] = EntityType.ROLE

    department_id: str | None = None
    access_level: str = "standard"
    is_privileged: bool = False
    permissions: list[str] = Field(default_factory=list)
    max_headcount: int | None = None
