"""Schema mapping for data ingestion."""

from __future__ import annotations

from pydantic import BaseModel, Field

from domain.base import EntityType, RelationshipType


class FieldMapping(BaseModel):
    """Maps a source field to an entity attribute."""

    source_field: str
    target_attribute: str
    transform: str | None = None


class EntityMapping(BaseModel):
    """Maps a source record type to a domain entity type."""

    source_type: str
    target_entity_type: EntityType
    field_mappings: list[FieldMapping]
    name_field: str


class RelationshipMapping(BaseModel):
    """Maps source data to a relationship."""

    source_field: str
    target_field: str
    relationship_type: RelationshipType


class SchemaMapping(BaseModel):
    """Complete mapping from a source schema to the KG domain model."""

    entity_mappings: list[EntityMapping] = Field(default_factory=list)
    relationship_mappings: list[RelationshipMapping] = Field(default_factory=list)
