"""Base class for graph exporters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from engine.abstract import AbstractGraphEngine


class AbstractExporter(ABC):
    """Base class for graph exporters."""

    @abstractmethod
    def export(self, engine: AbstractGraphEngine, output_path: Path, **kwargs: Any) -> None:
        """Export the graph to the specified path."""
        ...

    @abstractmethod
    def export_string(self, engine: AbstractGraphEngine, **kwargs: Any) -> str:
        """Export the graph as a string."""
        ...
