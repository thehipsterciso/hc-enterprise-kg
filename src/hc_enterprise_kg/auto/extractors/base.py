"""Abstract base for entity extractors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from hc_enterprise_kg.auto.base import ExtractionResult


class AbstractExtractor(ABC):
    """Base class for all entity extractors in the auto KG pipeline."""

    @abstractmethod
    def extract(self, data: Any, **kwargs: Any) -> ExtractionResult:
        """Extract entities and relationships from the given data."""
        ...

    @abstractmethod
    def can_handle(self, data: Any) -> bool:
        """Return True if this extractor can process the given data."""
        ...
