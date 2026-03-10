"""Tests for schema version handling in export and import."""

from __future__ import annotations

import json

from export.json_export import SCHEMA_VERSION
from ingest.json_ingestor import JSONIngestor


class TestSchemaVersionExport:
    """Schema version is included in exported JSON."""

    def test_export_string_includes_schema_version(self):
        """export_string() output contains schema_version key."""
        from unittest.mock import MagicMock

        from export.json_export import JSONExporter

        engine = MagicMock()
        engine.list_entities.return_value = []
        engine.get_statistics.return_value = {}

        exporter = JSONExporter()
        raw = exporter.export_string(engine)
        data = json.loads(raw)
        assert data["schema_version"] == SCHEMA_VERSION

    def test_schema_version_is_first_key(self):
        """schema_version appears first in the JSON output."""
        from unittest.mock import MagicMock

        from export.json_export import JSONExporter

        engine = MagicMock()
        engine.list_entities.return_value = []
        engine.get_statistics.return_value = {}

        exporter = JSONExporter()
        raw = exporter.export_string(engine)
        data = json.loads(raw)
        assert list(data.keys())[0] == "schema_version"


class TestSchemaVersionIngest:
    """Schema version is read, stored, and validated on import."""

    def test_stores_schema_version_from_file(self):
        """IngestResult.schema_version is populated from the JSON."""
        ingestor = JSONIngestor()
        result = ingestor.ingest_string(
            json.dumps(
                {
                    "schema_version": "1.0.0",
                    "entities": [],
                    "relationships": [],
                }
            )
        )
        assert result.schema_version == "1.0.0"

    def test_no_schema_version_field_stays_none(self):
        """Legacy files without schema_version are accepted."""
        ingestor = JSONIngestor()
        result = ingestor.ingest_string(
            json.dumps(
                {
                    "entities": [],
                    "relationships": [],
                }
            )
        )
        assert result.schema_version is None
        assert not result.warnings

    def test_same_major_version_no_warning(self):
        """Matching major version produces no warnings."""
        ingestor = JSONIngestor()
        result = ingestor.ingest_string(
            json.dumps(
                {
                    "schema_version": SCHEMA_VERSION,
                    "entities": [],
                }
            )
        )
        assert not result.warnings

    def test_minor_patch_difference_no_warning(self):
        """Different minor/patch with same major produces no warnings."""
        ingestor = JSONIngestor()
        major = SCHEMA_VERSION.split(".")[0]
        result = ingestor.ingest_string(
            json.dumps(
                {
                    "schema_version": f"{major}.99.99",
                    "entities": [],
                }
            )
        )
        assert not result.warnings

    def test_major_version_mismatch_warns(self):
        """Different major version produces a warning."""
        ingestor = JSONIngestor()
        current_major = int(SCHEMA_VERSION.split(".")[0])
        future_version = f"{current_major + 1}.0.0"
        result = ingestor.ingest_string(
            json.dumps(
                {
                    "schema_version": future_version,
                    "entities": [],
                }
            )
        )
        assert len(result.warnings) == 1
        assert "mismatch" in result.warnings[0].lower()
        assert future_version in result.warnings[0]

    def test_major_version_mismatch_still_ingests(self):
        """Entities are still parsed despite major version mismatch."""
        ingestor = JSONIngestor()
        current_major = int(SCHEMA_VERSION.split(".")[0])
        result = ingestor.ingest_string(
            json.dumps(
                {
                    "schema_version": f"{current_major + 1}.0.0",
                    "entities": [{"entity_type": "department", "name": "Engineering"}],
                }
            )
        )
        assert len(result.warnings) == 1
        assert result.entity_count == 1

    def test_unrecognised_version_format_warns(self):
        """Non-semver version string produces a warning."""
        ingestor = JSONIngestor()
        result = ingestor.ingest_string(
            json.dumps(
                {
                    "schema_version": "not-a-version",
                    "entities": [],
                }
            )
        )
        assert len(result.warnings) == 1
        assert "unrecognised" in result.warnings[0].lower()

    def test_schema_version_round_trip(self):
        """Export → import preserves schema_version."""
        from unittest.mock import MagicMock

        from export.json_export import JSONExporter

        engine = MagicMock()
        engine.list_entities.return_value = []
        engine.get_statistics.return_value = {}

        exporter = JSONExporter()
        exported = exporter.export_string(engine)

        ingestor = JSONIngestor()
        result = ingestor.ingest_string(exported)
        assert result.schema_version == SCHEMA_VERSION
        assert not result.warnings
        assert not result.errors
