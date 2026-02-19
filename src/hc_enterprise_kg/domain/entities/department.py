"""Department entity representing organizational units."""

from __future__ import annotations

from typing import ClassVar, Literal

from hc_enterprise_kg.domain.base import BaseEntity, EntityType


class Department(BaseEntity):
    """Represents a department or business unit."""

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.DEPARTMENT
    entity_type: Literal[EntityType.DEPARTMENT] = EntityType.DEPARTMENT

    code: str = ""
    head_id: str | None = None
    parent_department_id: str | None = None
    budget: float | None = None
    headcount: int = 0
    location_id: str | None = None
