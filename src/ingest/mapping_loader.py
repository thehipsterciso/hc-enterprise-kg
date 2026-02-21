"""Load declarative column mapping files for CSV import."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from domain.base import EntityType
    from ingest.mapping import SchemaMapping


@dataclass
class ColumnMapping:
    """A declarative column mapping loaded from a .mapping.json file."""

    name: str
    description: str
    entity_type: EntityType
    name_field: str
    columns: dict[str, str]  # source_column → target_field


@dataclass
class MappingLoadResult:
    """Result of loading a mapping file."""

    mapping: ColumnMapping | None = None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return self.mapping is not None and len(self.errors) == 0


def load_column_mapping(path: Path) -> MappingLoadResult:
    """Load and validate a .mapping.json file.

    Returns a MappingLoadResult with the parsed mapping, warnings, and errors.
    """
    from pathlib import Path as PathClass

    from domain.base import EntityType
    from domain.registry import EntityRegistry

    result = MappingLoadResult()
    path = PathClass(path)

    if not path.exists():
        result.errors.append(f"Mapping file not found: {path}")
        return result

    try:
        with open(path) as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        result.errors.append(f"Invalid JSON in mapping file: {exc}")
        return result

    if not isinstance(data, dict):
        result.errors.append("Mapping file must be a JSON object")
        return result

    # Validate required fields
    et_str = data.get("entity_type")
    if not et_str:
        result.errors.append("Mapping file missing required 'entity_type'")
        return result

    try:
        entity_type = EntityType(et_str)
    except ValueError:
        valid = sorted(e.value for e in EntityType)
        result.errors.append(
            f"Invalid entity_type '{et_str}'. Valid types: {', '.join(valid)}"
        )
        return result

    name_field = data.get("name_field")
    if not name_field:
        result.errors.append("Mapping file missing required 'name_field'")
        return result

    columns = data.get("columns", {})
    if not isinstance(columns, dict):
        result.errors.append("'columns' must be a dict mapping source → target fields")
        return result

    # Validate target fields against entity model
    EntityRegistry.auto_discover()
    entity_class = EntityRegistry.get(entity_type)
    known_fields = set(entity_class.model_fields.keys())

    for source_col, target_field in columns.items():
        if not isinstance(target_field, str):
            result.errors.append(
                f"Column mapping value for '{source_col}' must be a string, "
                f"got {type(target_field).__name__}"
            )
            continue
        if target_field not in known_fields:
            result.warnings.append(
                f"Target field '{target_field}' (from column '{source_col}') "
                f"is not in {et_str} schema"
            )

    if result.errors:
        return result

    result.mapping = ColumnMapping(
        name=data.get("name", path.stem),
        description=data.get("description", ""),
        entity_type=entity_type,
        name_field=name_field,
        columns=columns,
    )
    return result


def to_schema_mapping(mapping: ColumnMapping) -> SchemaMapping:
    """Convert a ColumnMapping to the existing SchemaMapping objects.

    Bridges declarative column mappings to the CSVIngestor API.
    """
    from ingest.mapping import EntityMapping, FieldMapping, SchemaMapping

    field_mappings = [
        FieldMapping(
            source_field=source_col,
            target_attribute=target_field,
        )
        for source_col, target_field in mapping.columns.items()
    ]

    entity_mapping = EntityMapping(
        source_type="csv",
        target_entity_type=mapping.entity_type,
        name_field=mapping.name_field,
        field_mappings=field_mappings,
    )

    return SchemaMapping(
        entity_mappings=[entity_mapping],
        relationship_mappings=[],
    )
