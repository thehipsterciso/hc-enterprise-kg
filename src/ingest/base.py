"""Base classes for data ingestion."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from domain.base import BaseEntity, BaseRelationship


@dataclass
class IngestResult:
    """Result of an ingestion operation."""

    entities: list[BaseEntity] = field(default_factory=list)
    relationships: list[BaseRelationship] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def entity_count(self) -> int:
        return len(self.entities)

    @property
    def relationship_count(self) -> int:
        return len(self.relationships)


class AbstractIngestor(ABC):
    """Base class for all data ingestors."""

    @abstractmethod
    def ingest(self, source: Path | str, **kwargs: Any) -> IngestResult:
        """Ingest data from the given source."""
        ...

    @abstractmethod
    def can_handle(self, source: Path | str) -> bool:
        """Return True if this ingestor can handle the given source."""
        ...
