"""JSON data ingestor."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from domain.base import BaseRelationship, EntityType
from domain.registry import EntityRegistry
from ingest.base import AbstractIngestor, IngestResult


class JSONIngestor(AbstractIngestor):
    """Ingests entities and relationships from JSON files.

    Expected JSON format:
    {
        "entities": [{"entity_type": "person", "name": "...", ...}, ...],
        "relationships": [
            {"relationship_type": "works_in", "source_id": "...", ...},
            ...
        ]
    }
    """

    def can_handle(self, source: Path | str) -> bool:
        path = Path(source) if isinstance(source, str) else source
        return path.suffix.lower() == ".json"

    def ingest(self, source: Path | str, **kwargs: Any) -> IngestResult:
        path = Path(source) if isinstance(source, str) else source
        result = IngestResult()

        if not path.exists():
            result.errors.append(f"File not found: {path}")
            return result

        try:
            with open(path) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            result.errors.append(f"Invalid JSON: {e}")
            return result

        return self._ingest_data(data)

    def ingest_string(self, json_str: str) -> IngestResult:
        """Ingest entities and relationships from a JSON string."""
        result = IngestResult()
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            result.errors.append(f"Invalid JSON: {e}")
            return result
        return self._ingest_data(data)

    def _ingest_data(self, data: dict[str, Any]) -> IngestResult:
        """Core ingestion logic shared by ingest() and ingest_string()."""
        result = IngestResult()
        EntityRegistry.auto_discover()

        # Parse entities
        for i, raw in enumerate(data.get("entities", [])):
            try:
                entity_type = EntityType(raw["entity_type"])
                entity_class = EntityRegistry.get(entity_type)
                entity = entity_class.model_validate(raw)
                result.entities.append(entity)
            except Exception as e:
                result.errors.append(f"Entity {i}: {e}")

        # Parse relationships
        for i, raw in enumerate(data.get("relationships", [])):
            try:
                rel = BaseRelationship.model_validate(raw)
                result.relationships.append(rel)
            except Exception as e:
                result.errors.append(f"Relationship {i}: {e}")

        return result
