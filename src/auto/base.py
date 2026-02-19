"""Base classes for the automatic KG construction pipeline."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from domain.base import BaseEntity, BaseRelationship


class PipelineStage(str, Enum):
    """Stages in the auto KG pipeline."""

    EXTRACT = "extract"
    LINK = "link"
    RESOLVE = "resolve"
    SCORE = "score"


@dataclass
class ExtractionResult:
    """Result of an extraction stage."""

    entities: list[BaseEntity] = field(default_factory=list)
    relationships: list[BaseRelationship] = field(default_factory=list)
    source: str = ""
    errors: list[str] = field(default_factory=list)


@dataclass
class LinkingResult:
    """Result of a linking stage."""

    relationships: list[BaseRelationship] = field(default_factory=list)
    link_method: str = ""
    errors: list[str] = field(default_factory=list)


@dataclass
class ResolutionResult:
    """Result of a resolution/dedup stage."""

    merged_entity_ids: list[tuple[str, str]] = field(default_factory=list)  # (kept_id, removed_id)
    entities: list[BaseEntity] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class PipelineResult:
    """Overall result of the auto KG pipeline."""

    entities: list[BaseEntity] = field(default_factory=list)
    relationships: list[BaseRelationship] = field(default_factory=list)
    extraction_results: list[ExtractionResult] = field(default_factory=list)
    linking_results: list[LinkingResult] = field(default_factory=list)
    resolution_result: ResolutionResult | None = None
    stats: dict[str, Any] = field(default_factory=dict)
