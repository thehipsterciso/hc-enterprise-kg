"""GraphML exporter for the knowledge graph."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import networkx as nx

from hc_enterprise_kg.engine.abstract import AbstractGraphEngine
from hc_enterprise_kg.export.base import AbstractExporter


class GraphMLExporter(AbstractExporter):
    """Exports the knowledge graph as GraphML.

    Uses NetworkX's built-in GraphML writer. Converts complex attributes
    to strings for GraphML compatibility.
    """

    def export(self, engine: AbstractGraphEngine, output_path: Path, **kwargs: Any) -> None:
        g = self._prepare_graph(engine)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        nx.write_graphml(g, str(output_path))

    def export_string(self, engine: AbstractGraphEngine, **kwargs: Any) -> str:
        import io

        g = self._prepare_graph(engine)
        buf = io.BytesIO()
        nx.write_graphml(g, buf)
        return buf.getvalue().decode("utf-8")

    def _prepare_graph(self, engine: AbstractGraphEngine) -> nx.MultiDiGraph:
        """Prepare a GraphML-compatible graph with string attributes."""
        native = engine.get_native_graph()
        g = native.copy()

        # Convert complex attributes to strings for GraphML compatibility
        for node_id, data in g.nodes(data=True):
            for key, value in list(data.items()):
                if isinstance(value, (list, dict)):
                    data[key] = str(value)
                elif isinstance(value, bool):
                    data[key] = str(value).lower()
                elif value is None:
                    data[key] = ""

        for u, v, key, data in g.edges(keys=True, data=True):
            for k, value in list(data.items()):
                if isinstance(value, (list, dict)):
                    data[k] = str(value)
                elif isinstance(value, bool):
                    data[k] = str(value).lower()
                elif value is None:
                    data[k] = ""

        return g
