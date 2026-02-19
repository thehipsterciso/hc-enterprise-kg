"""Person entity representing employees, contractors, etc."""

from __future__ import annotations

from typing import ClassVar, Literal

from domain.base import BaseEntity, EntityType


class Person(BaseEntity):
    """Represents a person in the organization."""

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.PERSON
    entity_type: Literal[EntityType.PERSON] = EntityType.PERSON

    first_name: str
    last_name: str
    email: str
    title: str = ""
    employee_id: str = ""
    clearance_level: str = ""
    is_active: bool = True
    hire_date: str | None = None
    phone: str = ""
    department_id: str | None = None
