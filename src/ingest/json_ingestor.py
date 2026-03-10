"""JSON data ingestor."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from domain.base import BaseRelationship, EntityType
from domain.registry import EntityRegistry
from export.json_export import SCHEMA_VERSION
from ingest.base import AbstractIngestor, IngestResult

logger = logging.getLogger(__name__)

# 500 MB hard limit on import file size
MAX_IMPORT_FILE_BYTES = 500 * 1024 * 1024


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
            file_size = path.stat().st_size
        except OSError:
            file_size = 0
        if file_size > MAX_IMPORT_FILE_BYTES:
            mb = file_size / (1024 * 1024)
            result.errors.append(f"File too large ({mb:.0f} MB). Maximum is 500 MB.")
            return result

        try:
            with open(path) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            result.errors.append(f"Invalid JSON: {e}")
            return result
        except UnicodeDecodeError as e:
            result.errors.append(f"File is not valid UTF-8 text: {e}")
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

        if not isinstance(data, dict):
            result.errors.append(f"Expected a JSON object (dict), got {type(data).__name__}.")
            return result

        # Schema version handling
        raw_version = data.get("schema_version")
        if raw_version is not None:
            result.schema_version = str(raw_version)
            self._check_schema_version(result, raw_version)

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

    @staticmethod
    def _check_schema_version(result: IngestResult, raw_version: Any) -> None:
        """Validate schema version and warn on incompatibility."""
        version_str = str(raw_version)
        try:
            parts = version_str.split(".")
            file_major = int(parts[0])
        except (ValueError, IndexError):
            result.warnings.append(
                f"Unrecognised schema_version '{version_str}'; proceeding anyway."
            )
            return

        current_major = int(SCHEMA_VERSION.split(".")[0])
        if file_major != current_major:
            result.warnings.append(
                f"Schema major version mismatch: file has v{version_str}, "
                f"current is v{SCHEMA_VERSION}. Data may not import correctly."
            )
