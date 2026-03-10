"""JSON exporter for the knowledge graph."""

from __future__ import annotations

import json
import shutil
from typing import TYPE_CHECKING, Any

from export.base import AbstractExporter, atomic_write_text
from export.file_lock import GraphFileLock

if TYPE_CHECKING:
    from pathlib import Path

    from engine.abstract import AbstractGraphEngine

DEFAULT_MAX_BACKUPS = 3


def _rotate_backups(path: Path, max_backups: int = DEFAULT_MAX_BACKUPS) -> None:
    """Rotate ``path`` → ``path.1`` → ``path.2`` → … before overwrite.

    Does nothing if *max_backups* is 0 or the file does not yet exist.
    """
    if max_backups <= 0 or not path.exists():
        return
    # Shift existing backups: .3 → deleted, .2 → .3, .1 → .2
    for i in range(max_backups, 1, -1):
        src = path.with_name(f"{path.name}.{i - 1}")
        dst = path.with_name(f"{path.name}.{i}")
        if src.exists():
            shutil.copy2(src, dst)
    # Current file becomes .1
    shutil.copy2(path, path.with_name(f"{path.name}.1"))


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
        max_backups = kwargs.get("max_backups", DEFAULT_MAX_BACKUPS)
        with GraphFileLock(output_path, exclusive=True):
            _rotate_backups(output_path, max_backups)
            atomic_write_text(output_path, content)

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
