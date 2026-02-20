"""CSV data ingestor."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import TYPE_CHECKING, Any

from domain.base import BaseRelationship
from domain.registry import EntityRegistry
from ingest.base import AbstractIngestor, IngestResult

if TYPE_CHECKING:
    from domain.base import EntityType
    from ingest.mapping import RelationshipMapping, SchemaMapping


class CSVIngestor(AbstractIngestor):
    """Ingests entities from CSV files using schema mappings."""

    _TRANSFORMS: dict[str, Any] = {
        "lowercase": lambda v: str(v).lower(),
        "uppercase": lambda v: str(v).upper(),
        "strip": lambda v: str(v).strip(),
        "int": lambda v: int(v),
        "float": lambda v: float(v),
        "bool": lambda v: str(v).lower() in ("true", "1", "yes"),
    }

    def can_handle(self, source: Path | str) -> bool:
        path = Path(source) if isinstance(source, str) else source
        return path.suffix.lower() == ".csv"

    @staticmethod
    def _apply_transform(value: str, transform: str | None) -> Any:
        """Apply a named transform to a field value."""
        if transform is None:
            return value
        fn = CSVIngestor._TRANSFORMS.get(transform)
        if fn is None:
            return value
        return fn(value)

    def ingest(
        self,
        source: Path | str,
        mapping: SchemaMapping | None = None,
        entity_type: EntityType | None = None,
        **kwargs: Any,
    ) -> IngestResult:
        path = Path(source) if isinstance(source, str) else source
        result = IngestResult()

        if not path.exists():
            result.errors.append(f"File not found: {path}")
            return result

        EntityRegistry.auto_discover()

        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        if not rows:
            result.warnings.append("CSV file is empty")
            return result

        if mapping and mapping.entity_mappings:
            for em in mapping.entity_mappings:
                entity_class = EntityRegistry.get(em.target_entity_type)
                for i, row in enumerate(rows):
                    try:
                        attrs: dict[str, Any] = {
                            "entity_type": em.target_entity_type.value,
                            "name": row.get(em.name_field, f"Row-{i}"),
                        }
                        for fm in em.field_mappings:
                            if fm.source_field in row:
                                attrs[fm.target_attribute] = self._apply_transform(
                                    row[fm.source_field], fm.transform
                                )
                        entity = entity_class.model_validate(attrs)
                        result.entities.append(entity)
                    except Exception as e:
                        result.errors.append(f"Row {i}: {e}")

            # Process relationship mappings after entities are ingested
            if mapping.relationship_mappings:
                self._process_relationship_mappings(
                    mapping.relationship_mappings, result
                )
        elif entity_type:
            entity_class = EntityRegistry.get(entity_type)
            columns = list(rows[0].keys())
            name_col = columns[0]
            for i, row in enumerate(rows):
                try:
                    attrs = {
                        "entity_type": entity_type.value,
                        "name": row.get(name_col, f"Row-{i}"),
                    }
                    for col, val in row.items():
                        if val and col != name_col:
                            attrs[col] = val
                    entity = entity_class.model_validate(attrs)
                    result.entities.append(entity)
                except Exception as e:
                    result.errors.append(f"Row {i}: {e}")
        else:
            result.errors.append("No mapping or entity_type provided")

        return result

    @staticmethod
    def _process_relationship_mappings(
        rel_mappings: list[RelationshipMapping],
        result: IngestResult,
    ) -> None:
        """Create relationships from relationship mappings using ingested entities.

        For each relationship mapping, looks up entity IDs by name from the
        ingested entities and creates relationships between matched pairs.
        """
        # Build name → entity_id lookup from ingested entities
        name_to_id: dict[str, str] = {}
        for entity in result.entities:
            name_to_id[entity.name] = entity.id

        for rm in rel_mappings:
            for entity in result.entities:
                raw = entity.model_dump(mode="python")
                # source_field/target_field refer to attribute names that hold
                # the name (or id) of the related entity
                target_ref = raw.get(rm.target_field)
                if not target_ref:
                    continue
                target_id = name_to_id.get(str(target_ref))
                if target_id and target_id != entity.id:
                    try:
                        rel = BaseRelationship(
                            relationship_type=rm.relationship_type,
                            source_id=entity.id,
                            target_id=target_id,
                        )
                        result.relationships.append(rel)
                    except Exception as e:
                        result.errors.append(
                            f"Relationship {rm.relationship_type}: {e}"
                        )
