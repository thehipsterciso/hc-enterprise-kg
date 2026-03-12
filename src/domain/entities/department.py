"""Department entity representing organizational units."""

from __future__ import annotations

from typing import ClassVar, Literal

from domain.base import BaseEntity, EntityType


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

    # --- Data/AI Fluency Indicators (added for CDAIO Module 12) ---
    data_fluency_level: int | None = None  # 1-5 (aware/literate/proficient/advanced/expert)
    fluency_assessed_date: str = ""
    training_program_active: bool | None = None
    analytics_adoption_pct: float | None = None  # % of dept actively using analytics
    data_culture_score: str = ""  # strong | developing | emerging | nascent | none
