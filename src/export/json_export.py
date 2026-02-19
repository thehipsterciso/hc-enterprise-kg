"""JSON exporter for the knowledge graph."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from engine.abstract import AbstractGraphEngine
from export.base import AbstractExporter


class JSONExporter(AbstractExporter):
    """Exports the knowledge graph as JSON.

    Output format:
    {
        "entities": [...],
        "relationships": [...],
        "statistics": {...}
    }
    """

    def export(self, engine: AbstractGraphEngine, output_path: Path, **kwargs: Any) -> None:
        content = self.export_string(engine, **kwargs)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content)

    def export_string(self, engine: AbstractGraphEngine, **kwargs: Any) -> str:
        entities = engine.list_entities()
        entity_dicts = []
        for entity in entities:
            d = entity.model_dump(mode="json")
            entity_dicts.append(d)

        # Collect all relationships
        rel_dicts = []
        seen_rel_ids: set[str] = set()
        for entity in entities:
            for direction in ("out", "in"):
                for rel in engine.get_relationships(entity.id, direction=direction):
                    if rel.id not in seen_rel_ids:
                        seen_rel_ids.add(rel.id)
                        rel_dicts.append(rel.model_dump(mode="json"))

        data = {
            "entities": entity_dicts,
            "relationships": rel_dicts,
            "statistics": engine.get_statistics(),
        }

        indent = kwargs.get("indent", 2)
        return json.dumps(data, indent=indent, default=str)
