"""Serialisation helpers for MCP tool responses."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from domain.base import BaseEntity


def compact_entity(entity: BaseEntity) -> dict[str, Any]:
    """Serialise an entity to a compact JSON-safe dict.

    Strips None/empty values and internal temporal/metadata fields to keep
    MCP responses small and LLM-friendly.
    """
    raw = entity.model_dump(mode="json")
    skip = {"created_at", "updated_at", "metadata", "valid_from", "valid_until", "version"}
    return {k: v for k, v in raw.items() if k not in skip and v is not None and v != "" and v != []}


def compact_relationship(rel: Any) -> dict[str, Any]:
    """Serialise a relationship to a compact JSON-safe dict."""
    raw = rel.model_dump(mode="json")
    skip = {"created_at", "updated_at", "valid_from", "valid_until", "version"}
    return {k: v for k, v in raw.items() if k not in skip and v is not None and v != "" and v != {}}
