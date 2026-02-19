"""Policy entity representing security policies, controls, and compliance frameworks."""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import Field

from domain.base import BaseEntity, EntityType


class Policy(BaseEntity):
    """Represents a security policy, control, or compliance requirement."""

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.POLICY
    entity_type: Literal[EntityType.POLICY] = EntityType.POLICY

    policy_type: str = ""  # access_control, data_protection, incident_response, etc.
    framework: str = ""  # NIST, ISO27001, CIS, SOC2, etc.
    control_id: str = ""  # e.g., AC-1, A.9.1.1
    severity: str = "medium"  # low, medium, high, critical
    is_enforced: bool = True
    review_frequency_days: int = 365
    owner_id: str | None = None
    applicable_systems: list[str] = Field(default_factory=list)
