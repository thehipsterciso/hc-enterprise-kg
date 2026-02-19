"""CSV-based entity extraction using schema inference."""

from __future__ import annotations

import csv
import io
import uuid
from pathlib import Path
from typing import Any

from auto.base import ExtractionResult
from auto.confidence import ConfidenceSource, compute_confidence
from auto.extractors.base import AbstractExtractor
from auto.schema_inference import infer_entity_type, infer_name_field
from domain.base import BaseEntity, EntityType
from domain.registry import EntityRegistry


class CSVExtractor(AbstractExtractor):
    """Extracts entities from CSV data using schema inference or explicit mapping.

    If entity_type is not provided, attempts to infer it from column names.
    """

    def can_handle(self, data: Any) -> bool:
        if isinstance(data, (str, Path)):
            path = Path(data) if isinstance(data, str) else data
            return path.suffix.lower() == ".csv" or (isinstance(data, str) and "," in data)
        return False

    def extract(
        self,
        data: Any,
        entity_type: EntityType | None = None,
        name_field: str | None = None,
        field_mapping: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> ExtractionResult:
        """Extract entities from CSV data.

        Args:
            data: CSV file path or CSV string content.
            entity_type: Explicit entity type. If None, infers from columns.
            name_field: Column to use as entity name. If None, infers.
            field_mapping: Optional mapping of CSV columns to entity attributes.
        """
        rows = self._read_csv(data)
        if not rows:
            return ExtractionResult(source="csv", errors=["No data rows found"])

        columns = list(rows[0].keys())

        # Infer entity type if not provided
        if entity_type is None:
            entity_type = infer_entity_type(columns)
            if entity_type is None:
                return ExtractionResult(
                    source="csv",
                    errors=[f"Could not infer entity type from columns: {columns}"],
                )

        # Infer name field if not provided
        if name_field is None:
            name_field = infer_name_field(columns)

        confidence = compute_confidence(ConfidenceSource.CSV_STRUCTURED)
        entities: list[BaseEntity] = []
        errors: list[str] = []

        EntityRegistry.auto_discover()

        for i, row in enumerate(rows):
            try:
                # Build entity attributes
                attrs: dict[str, Any] = {
                    "entity_type": entity_type.value,
                    "name": row.get(name_field, f"Entity-{i}") if name_field else f"Entity-{i}",
                    "metadata": {"_confidence": confidence, "_source": "csv", "_row": i},
                }

                # Apply field mapping or pass through
                if field_mapping:
                    for csv_col, entity_attr in field_mapping.items():
                        if csv_col in row and row[csv_col]:
                            attrs[entity_attr] = row[csv_col]
                else:
                    for col, val in row.items():
                        if val and col != name_field:
                            attrs[col] = val

                entity_class = EntityRegistry.get(entity_type)
                entity = entity_class.model_validate(attrs)
                entities.append(entity)
            except Exception as e:
                errors.append(f"Row {i}: {e}")

        return ExtractionResult(entities=entities, source="csv", errors=errors)

    def _read_csv(self, data: Any) -> list[dict[str, str]]:
        """Read CSV from file path or string."""
        if isinstance(data, (str, Path)):
            path = Path(data)
            if path.exists() and path.is_file():
                with open(path, newline="") as f:
                    return list(csv.DictReader(f))

        if isinstance(data, str) and "," in data:
            return list(csv.DictReader(io.StringIO(data)))

        return []
