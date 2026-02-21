"""Pre-ingest validation for import data quality."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from domain.base import EntityType


@dataclass
class ValidationResult:
    """Result of pre-ingest validation."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    entity_count: int = 0
    relationship_count: int = 0
    entity_type_counts: dict[str, int] = field(default_factory=dict)
    relationship_type_counts: dict[str, int] = field(default_factory=dict)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0


def _get_known_fields(entity_type: EntityType) -> set[str]:
    """Get the set of known field names for an entity type."""
    from domain.registry import EntityRegistry

    EntityRegistry.auto_discover()
    entity_class = EntityRegistry.get(entity_type)
    return set(entity_class.model_fields.keys())


def _check_entity_required_fields(
    raw: dict[str, Any],
    entity_type_str: str,
    index: int,
    errors: list[str],
) -> None:
    """Check entity-specific required fields."""
    name = raw.get("name")
    if not name or (isinstance(name, str) and not name.strip()):
        errors.append(f"Entity {index}: missing or empty 'name'")

    if entity_type_str == "person":
        for req in ("first_name", "last_name", "email"):
            if req not in raw or not raw[req]:
                errors.append(
                    f"Entity {index} ({raw.get('name', '?')}): "
                    f"missing required field '{req}'"
                )


def validate_json_import(data: dict[str, Any]) -> ValidationResult:
    """Validate JSON import data before ingestion.

    Checks structure, entity types, required fields, unknown fields,
    relationship validity, and referential integrity.
    """
    from domain.base import EntityType, RelationshipType

    result = ValidationResult()

    # --- Structure checks ---
    entities_raw = data.get("entities")
    if entities_raw is None:
        result.errors.append("Missing 'entities' key in JSON data")
        return result
    if not isinstance(entities_raw, list):
        result.errors.append("'entities' must be a list")
        return result

    relationships_raw = data.get("relationships", [])
    if not isinstance(relationships_raw, list):
        result.errors.append("'relationships' must be a list")
        relationships_raw = []

    # --- Entity validation ---
    entity_ids: set[str] = set()
    valid_et_values = {e.value for e in EntityType}

    for i, raw in enumerate(entities_raw):
        if not isinstance(raw, dict):
            result.errors.append(f"Entity {i}: must be a dict, got {type(raw).__name__}")
            continue

        # entity_type check
        et_str = raw.get("entity_type")
        if not et_str:
            result.errors.append(f"Entity {i}: missing 'entity_type'")
            continue
        if et_str not in valid_et_values:
            result.errors.append(
                f"Entity {i} ({raw.get('name', '?')}): "
                f"invalid entity_type '{et_str}'"
            )
            continue

        # Required fields
        _check_entity_required_fields(raw, et_str, i, result.errors)

        # Track entity ID
        eid = raw.get("id")
        if eid:
            entity_ids.add(eid)

        # Count by type
        result.entity_type_counts[et_str] = result.entity_type_counts.get(et_str, 0) + 1
        result.entity_count += 1

        # Unknown field detection
        try:
            et = EntityType(et_str)
            known = _get_known_fields(et)
            provided = set(raw.keys())
            unknown = provided - known
            if unknown:
                result.warnings.append(
                    f"Entity {i} ({raw.get('name', '?')}): "
                    f"unknown field(s) {sorted(unknown)} "
                    f"(not in {et_str} schema)"
                )
        except (ValueError, KeyError):
            pass  # Already reported as invalid entity_type

    # --- Relationship validation ---
    valid_rt_values = {r.value for r in RelationshipType}

    for i, raw in enumerate(relationships_raw):
        if not isinstance(raw, dict):
            result.errors.append(
                f"Relationship {i}: must be a dict, got {type(raw).__name__}"
            )
            continue

        rt_str = raw.get("relationship_type")
        if not rt_str:
            result.errors.append(f"Relationship {i}: missing 'relationship_type'")
            continue
        if rt_str not in valid_rt_values:
            result.errors.append(
                f"Relationship {i}: invalid relationship_type '{rt_str}'"
            )
            continue

        source_id = raw.get("source_id")
        target_id = raw.get("target_id")
        if not source_id:
            result.errors.append(f"Relationship {i}: missing 'source_id'")
        if not target_id:
            result.errors.append(f"Relationship {i}: missing 'target_id'")

        # Referential integrity (warnings, not errors — merge target may have them)
        if source_id and entity_ids and source_id not in entity_ids:
            result.warnings.append(
                f"Relationship {i}: source_id '{source_id}' "
                f"not found in imported entities"
            )
        if target_id and entity_ids and target_id not in entity_ids:
            result.warnings.append(
                f"Relationship {i}: target_id '{target_id}' "
                f"not found in imported entities"
            )

        # Count by type
        result.relationship_type_counts[rt_str] = (
            result.relationship_type_counts.get(rt_str, 0) + 1
        )
        result.relationship_count += 1

    return result


def validate_csv_import(
    headers: list[str],
    entity_type: EntityType,
) -> ValidationResult:
    """Validate CSV column names against entity model fields.

    Checks that headers are non-empty, flags unknown columns,
    and verifies entity-specific required fields are present.
    """
    result = ValidationResult()

    if not headers:
        result.errors.append("CSV has no column headers")
        return result

    known = _get_known_fields(entity_type)
    header_set = set(headers)

    # Unknown columns
    unknown = header_set - known
    if unknown:
        result.warnings.append(
            f"Unknown column(s) for {entity_type.value}: {sorted(unknown)} "
            f"(will be stored as extra fields)"
        )

    # Entity-specific required fields
    if entity_type.value == "person":
        for req in ("first_name", "last_name", "email"):
            if req not in header_set:
                result.errors.append(
                    f"CSV missing required column '{req}' for person import"
                )

    # Summary
    result.entity_count = 0  # Can't know row count from headers alone
    result.entity_type_counts[entity_type.value] = 0

    return result
