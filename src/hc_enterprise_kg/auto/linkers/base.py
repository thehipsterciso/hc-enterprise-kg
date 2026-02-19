"""Abstract base for entity linkers."""

from __future__ import annotations

from abc import ABC, abstractmethod

from hc_enterprise_kg.auto.base import LinkingResult
from hc_enterprise_kg.domain.base import BaseEntity


class AbstractLinker(ABC):
    """Base class for entity linkers that discover relationships."""

    @abstractmethod
    def link(self, entities: list[BaseEntity]) -> LinkingResult:
        """Discover and propose relationships between entities."""
        ...
