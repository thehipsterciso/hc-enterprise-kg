"""Abstract base for entity resolvers."""

from __future__ import annotations

from abc import ABC, abstractmethod

from hc_enterprise_kg.auto.base import ResolutionResult
from hc_enterprise_kg.domain.base import BaseEntity


class AbstractResolver(ABC):
    """Base class for entity resolvers that merge/deduplicate entities."""

    @abstractmethod
    def resolve(self, entities: list[BaseEntity]) -> ResolutionResult:
        """Identify and merge duplicate entities."""
        ...
