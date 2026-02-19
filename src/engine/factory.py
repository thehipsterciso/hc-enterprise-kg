"""Factory for creating graph engine instances."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from engine.abstract import AbstractGraphEngine


class GraphEngineFactory:
    """Factory for creating graph engine instances.

    Supports registration of custom backends.
    """

    _backends: dict[str, type[AbstractGraphEngine]] = {}

    @classmethod
    def register(cls, name: str, engine_class: type[AbstractGraphEngine]) -> None:
        cls._backends[name] = engine_class

    @classmethod
    def create(cls, backend: str = "networkx", **kwargs: Any) -> AbstractGraphEngine:
        if backend not in cls._backends:
            raise ValueError(
                f"Unknown backend '{backend}'. Available: {list(cls._backends.keys())}"
            )
        return cls._backends[backend](**kwargs)

    @classmethod
    def available_backends(cls) -> list[str]:
        return list(cls._backends.keys())

    @classmethod
    def auto_discover(cls) -> None:
        """Register all built-in engine backends."""
        from engine.networkx_engine import NetworkXGraphEngine

        cls.register("networkx", NetworkXGraphEngine)
