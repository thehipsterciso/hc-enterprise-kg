"""Location entity representing physical sites and facilities."""

from __future__ import annotations

from typing import ClassVar, Literal

from domain.base import BaseEntity, EntityType


class Location(BaseEntity):
    """Represents a physical location or facility."""

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.LOCATION
    entity_type: Literal[EntityType.LOCATION] = EntityType.LOCATION

    address: str = ""
    city: str = ""
    state: str = ""
    country: str = ""
    zip_code: str = ""
    location_type: str = ""  # headquarters, office, data_center, warehouse, remote
    capacity: int | None = None
    is_primary: bool = False
    security_level: str = "standard"  # standard, enhanced, restricted
    has_physical_security: bool = True
