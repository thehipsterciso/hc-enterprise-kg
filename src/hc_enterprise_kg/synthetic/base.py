"""Base classes for synthetic data generation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar

from faker import Faker

from hc_enterprise_kg.domain.base import BaseEntity, EntityType

T = TypeVar("T", bound=BaseEntity)


class GenerationContext:
    """Shared context passed to all generators during a generation run.

    Holds the org profile parameters, the Faker instance, previously
    generated entities (so generators can reference each other), and
    the random seed for reproducibility.
    """

    def __init__(
        self,
        profile: "OrgProfile",  # noqa: F821 — forward ref
        seed: int | None = None,
    ) -> None:
        self.profile = profile
        self.seed = seed
        self.faker = Faker()
        if seed is not None:
            Faker.seed(seed)
            import random

            random.seed(seed)
        self.generated: dict[EntityType, list[BaseEntity]] = {}
        self.id_pool: dict[EntityType, list[str]] = {}

    def get_entities(self, entity_type: EntityType) -> list[BaseEntity]:
        return self.generated.get(entity_type, [])

    def get_ids(self, entity_type: EntityType) -> list[str]:
        return self.id_pool.get(entity_type, [])

    def store(self, entity_type: EntityType, entities: list[BaseEntity]) -> None:
        self.generated[entity_type] = entities
        self.id_pool[entity_type] = [e.id for e in entities]


class AbstractGenerator(ABC):
    """Base class for all entity generators."""

    GENERATES: EntityType

    @abstractmethod
    def generate(self, count: int, context: GenerationContext) -> list[BaseEntity]:
        """Generate `count` entities using the provided context."""
        ...


class GeneratorRegistry:
    """Registry for entity generators. Supports dynamic registration."""

    _registry: dict[EntityType, type[AbstractGenerator]] = {}

    @classmethod
    def register(cls, generator_class: type[AbstractGenerator]) -> type[AbstractGenerator]:
        """Can be used as a decorator: @GeneratorRegistry.register"""
        cls._registry[generator_class.GENERATES] = generator_class
        return generator_class

    @classmethod
    def get(cls, entity_type: EntityType) -> type[AbstractGenerator]:
        if entity_type not in cls._registry:
            raise KeyError(f"No generator registered for type: {entity_type}")
        return cls._registry[entity_type]

    @classmethod
    def all(cls) -> dict[EntityType, type[AbstractGenerator]]:
        return dict(cls._registry)

    @classmethod
    def is_registered(cls, entity_type: EntityType) -> bool:
        return entity_type in cls._registry

    @classmethod
    def clear(cls) -> None:
        cls._registry.clear()
