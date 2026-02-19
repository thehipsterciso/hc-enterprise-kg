"""CSV data ingestor."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from domain.base import EntityType
from domain.registry import EntityRegistry
from ingest.base import AbstractIngestor, IngestResult
from ingest.mapping import SchemaMapping


class CSVIngestor(AbstractIngestor):
    """Ingests entities from CSV files using schema mappings."""

    def can_handle(self, source: Path | str) -> bool:
        path = Path(source) if isinstance(source, str) else source
        return path.suffix.lower() == ".csv"

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
                                attrs[fm.target_attribute] = row[fm.source_field]
                        entity = entity_class.model_validate(attrs)
                        result.entities.append(entity)
                    except Exception as e:
                        result.errors.append(f"Row {i}: {e}")
        elif entity_type:
            entity_class = EntityRegistry.get(entity_type)
            columns = list(rows[0].keys())
            name_col = columns[0]
            for i, row in enumerate(rows):
                try:
                    attrs = {"entity_type": entity_type.value, "name": row.get(name_col, f"Row-{i}")}
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
