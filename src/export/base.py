"""Base class for graph exporters."""

from __future__ import annotations

import contextlib
import os
import tempfile
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

    from engine.abstract import AbstractGraphEngine


def atomic_write_text(path: Path, content: str) -> None:
    """Atomically write *content* to *path* via temp-file-then-rename.

    Ensures readers never see a partially-written file.  On POSIX
    ``os.replace`` is atomic; on Windows it is as close as the OS allows.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    try:
        try:
            os.write(fd, content.encode("utf-8"))
        finally:
            os.close(fd)
        os.replace(tmp, str(path))
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


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
