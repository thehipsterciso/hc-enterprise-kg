"""Input validation for MCP write tools.

Centralises validation logic so every write tool enforces the same
rules: enum membership, entity existence, domain/range schema, and
basic field constraints.
"""

from __future__ import annotations

import math
import re
from typing import TYPE_CHECKING

from domain.base import EntityType, RelationshipType
from domain.relationship_schema import validate_relationship

if TYPE_CHECKING:
    from graph.knowledge_graph import KnowledgeGraph

MAX_NAME_LENGTH = 255
MAX_DESCRIPTION_LENGTH = 4096
MAX_BLAST_RADIUS_DEPTH = 10
MAX_LIST_LIMIT = 10_000
MAX_IMPORT_FILE_BYTES = 500 * 1024 * 1024  # 500 MB
SAFE_ID_RE = re.compile(r"^[a-zA-Z0-9_:.-]+$")

# Fields that must NOT be overridden via the properties dict in
# add_entity_tool.  These are either auto-generated (id, timestamps,
# version) or controlled by explicit parameters (name, description,
# entity_type).
RESERVED_ENTITY_FIELDS = frozenset(
    {
        "id",
        "entity_type",
        "created_at",
        "updated_at",
        "valid_from",
        "valid_until",
        "version",
    }
)

# Fields that must NOT be changed via update_entity_tool.
IMMUTABLE_ENTITY_FIELDS = frozenset(
    {
        "id",
        "entity_type",
        "created_at",
    }
)

# Control characters (C0 range except tab/newline/carriage-return)
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def validate_id_format(value: str) -> tuple[bool, str]:
    """Check that an ID contains only safe characters.

    Returns (True, "") if valid, or (False, reason) if not.
    """
    if not value:
        return False, "ID must not be empty."
    if not SAFE_ID_RE.match(value):
        return False, (
            f"ID '{value}' contains invalid characters. "
            "Only alphanumeric, underscore, colon, dot, and hyphen are allowed."
        )
    return True, ""


def validate_relationship_type(value: str) -> tuple[bool, str]:
    """Validate that a string is a valid RelationshipType enum value."""
    try:
        RelationshipType(value)
    except ValueError:
        valid = sorted(r.value for r in RelationshipType)
        return False, f"Unknown relationship_type '{value}'. Valid types: {valid}"
    return True, ""


def validate_entity_type(value: str) -> tuple[bool, str]:
    """Validate that a string is a valid EntityType enum value."""
    try:
        EntityType(value)
    except ValueError:
        valid = sorted(e.value for e in EntityType)
        return False, f"Unknown entity_type '{value}'. Valid types: {valid}"
    return True, ""


def validate_relationship_input(
    kg: KnowledgeGraph,
    relationship_type: str,
    source_id: str,
    target_id: str,
) -> tuple[bool, str]:
    """Full validation for an add_relationship call.

    Checks:
    1. relationship_type is a valid enum value
    2. source_id and target_id entities exist in the graph
    3. The relationship satisfies domain/range schema constraints

    Returns (True, "") if valid, or (False, reason) if not.
    """
    # 1. Enum check
    ok, reason = validate_relationship_type(relationship_type)
    if not ok:
        return False, reason

    # 2. Entity existence
    source = kg.get_entity(source_id)
    if source is None:
        return False, f"Source entity '{source_id}' not found in graph."

    target = kg.get_entity(target_id)
    if target is None:
        return False, f"Target entity '{target_id}' not found in graph."

    # 3. Domain/range schema
    rt = RelationshipType(relationship_type)
    ok, reason = validate_relationship(rt, source.entity_type, target.entity_type)
    if not ok:
        return False, reason

    return True, ""


def validate_entity_input(
    entity_type: str,
    name: str,
    description: str = "",
) -> tuple[bool, str]:
    """Validate basic fields for an add_entity call.

    Checks:
    1. entity_type is a valid enum value
    2. name is non-empty and within length limit
    3. description is within length limit
    """
    ok, reason = validate_entity_type(entity_type)
    if not ok:
        return False, reason

    if not name or not name.strip():
        return False, "Entity name must not be empty."

    if len(name) > MAX_NAME_LENGTH:
        return False, (f"Entity name exceeds {MAX_NAME_LENGTH} characters ({len(name)} given).")

    if len(description) > MAX_DESCRIPTION_LENGTH:
        return False, (
            f"Entity description exceeds {MAX_DESCRIPTION_LENGTH} characters "
            f"({len(description)} given)."
        )

    # Reject control characters (null bytes, etc.) in name
    if _CONTROL_CHAR_RE.search(name):
        return False, "Entity name contains invalid control characters."

    return True, ""


def sanitize_properties(properties: dict) -> tuple[dict, list[str]]:
    """Strip reserved fields from a properties dict.

    Returns the cleaned dict and a list of stripped field names
    (for warning the caller).
    """
    stripped: list[str] = []
    clean = {}
    for k, v in properties.items():
        if k in RESERVED_ENTITY_FIELDS:
            stripped.append(k)
        else:
            clean[k] = v
    return clean, stripped


def sanitize_updates(updates: dict) -> tuple[dict, list[str]]:
    """Strip immutable fields from an updates dict.

    Returns the cleaned dict and a list of stripped field names.
    """
    stripped: list[str] = []
    clean = {}
    for k, v in updates.items():
        if k in IMMUTABLE_ENTITY_FIELDS:
            stripped.append(k)
        else:
            clean[k] = v
    return clean, stripped


def clamp_float(value: float, low: float = 0.0, high: float = 1.0) -> float:
    """Clamp a float to [low, high], treating NaN/Inf as the default."""
    if math.isnan(value) or math.isinf(value):
        return high if value > 0 else low
    return max(low, min(high, value))
