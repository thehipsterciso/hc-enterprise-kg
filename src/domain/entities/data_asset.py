"""Data asset entity representing datasets, databases, and data stores."""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import Field

from domain.base import BaseEntity, EntityType


class DataAsset(BaseEntity):
    """Represents a data asset (database, dataset, file store, etc.)."""

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.DATA_ASSET
    entity_type: Literal[EntityType.DATA_ASSET] = EntityType.DATA_ASSET

    data_type: str = ""  # pii, phi, financial, intellectual_property, public
    classification: str = "internal"  # public, internal, confidential, restricted
    format: str = ""  # sql, nosql, file, api, stream
    retention_days: int | None = None
    is_encrypted: bool = False
    owner_id: str | None = None
    system_id: str | None = None
    record_count: int | None = None
    regulations: list[str] = Field(default_factory=list)  # GDPR, HIPAA, PCI-DSS, etc.
