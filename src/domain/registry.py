"""Entity and relationship type registry for plugin discovery."""

from __future__ import annotations

from typing import Type

from domain.base import BaseEntity, EntityType


class EntityRegistry:
    """Registry for entity type classes.

    Supports dynamic registration so users can add custom entity types
    without modifying core code.
    """

    _registry: dict[EntityType, Type[BaseEntity]] = {}

    @classmethod
    def register(cls, entity_type: EntityType, entity_class: Type[BaseEntity]) -> None:
        cls._registry[entity_type] = entity_class

    @classmethod
    def get(cls, entity_type: EntityType) -> Type[BaseEntity]:
        if entity_type not in cls._registry:
            raise KeyError(f"No entity class registered for type: {entity_type}")
        return cls._registry[entity_type]

    @classmethod
    def all_types(cls) -> list[EntityType]:
        return list(cls._registry.keys())

    @classmethod
    def is_registered(cls, entity_type: EntityType) -> bool:
        return entity_type in cls._registry

    @classmethod
    def clear(cls) -> None:
        cls._registry.clear()

    @classmethod
    def auto_discover(cls) -> None:
        """Auto-register all built-in entity classes."""
        from domain.entities import (
            DataAsset,
            Department,
            Incident,
            Location,
            Network,
            Person,
            Policy,
            Role,
            System,
            ThreatActor,
            Vendor,
            Vulnerability,
        )

        for entity_class in [
            Person,
            Department,
            Role,
            System,
            Network,
            DataAsset,
            Policy,
            Vendor,
            Location,
            Vulnerability,
            ThreatActor,
            Incident,
        ]:
            cls.register(entity_class.ENTITY_TYPE, entity_class)
