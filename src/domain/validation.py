"""Strict validation utilities for entity and relationship data quality."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.base import BaseEntity, BaseRelationship

logger = logging.getLogger(__name__)

# Strict mode: set HCKG_STRICT=1 to raise on extra fields
STRICT_MODE = os.environ.get("HCKG_STRICT", "0") == "1"


def check_extra_fields(entity: BaseEntity) -> list[str]:
    """Return list of extra field names that landed in __pydantic_extra__.

    These are fields not defined in the entity's schema — likely typos.
    """
    extras = entity.__pydantic_extra__ or {}
    return list(extras.keys())


def warn_extra_fields(entity: BaseEntity) -> None:
    """Log a warning if an entity has extra fields. Raise in strict mode."""
    extra_keys = check_extra_fields(entity)
    if not extra_keys:
        return

    msg = (
        f"{entity.__class__.__name__} '{entity.name}' (id={entity.id}) "
        f"has {len(extra_keys)} extra field(s) not in schema: {extra_keys}"
    )

    if STRICT_MODE:
        raise ValueError(msg)

    logger.warning(msg)


def validate_entity_strict(entity: BaseEntity) -> list[str]:
    """Run all strict validation checks on an entity.

    Returns a list of warning strings (empty = clean).
    """
    warnings: list[str] = []
    extra_keys = check_extra_fields(entity)
    if extra_keys:
        warnings.append(
            f"Extra fields on {entity.__class__.__name__} '{entity.name}': {extra_keys}"
        )
    return warnings


def validate_relationship_types(
    relationship: BaseRelationship,
    source_type: str,
    target_type: str,
) -> list[str]:
    """Validate a relationship against the domain/range schema.

    Returns a list of warning strings (empty = valid).
    """
    from domain.base import EntityType, RelationshipType
    from domain.relationship_schema import validate_relationship

    try:
        rt = RelationshipType(relationship.relationship_type)
        st = EntityType(source_type)
        tt = EntityType(target_type)
    except ValueError:
        return []  # Unknown types — can't validate

    valid, reason = validate_relationship(rt, st, tt)
    if not valid:
        return [reason]
    return []
