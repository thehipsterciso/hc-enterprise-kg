"""Vendor entity representing third-party suppliers and service providers."""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import Field

from hc_enterprise_kg.domain.base import BaseEntity, EntityType


class Vendor(BaseEntity):
    """Represents a third-party vendor or service provider."""

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.VENDOR
    entity_type: Literal[EntityType.VENDOR] = EntityType.VENDOR

    vendor_type: str = ""  # saas, iaas, consulting, hardware, managed_service
    contract_value: float | None = None
    risk_tier: str = "medium"  # low, medium, high, critical
    has_data_access: bool = False
    data_classification_access: list[str] = Field(default_factory=list)
    compliance_certifications: list[str] = Field(default_factory=list)
    contract_expiry: str | None = None
    primary_contact: str = ""
    sla_uptime: float | None = None
