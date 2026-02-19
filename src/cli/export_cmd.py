"""CLI commands for exporting the knowledge graph."""

from __future__ import annotations

from pathlib import Path

import click


@click.command()
@click.option("--format", "fmt", type=click.Choice(["json", "graphml"]), default="json")
@click.option("--output", type=click.Path(), required=True, help="Output file path.")
@click.option("--source", type=click.Path(exists=True), required=True, help="Source JSON KG file to re-export.")
def export_cmd(fmt: str, output: str, source: str) -> None:
    """Export a knowledge graph to a file."""
    from graph.knowledge_graph import KnowledgeGraph
    from ingest.json_ingestor import JSONIngestor

    kg = KnowledgeGraph()

    # Load from source
    ingestor = JSONIngestor()
    result = ingestor.ingest(Path(source))
    kg.add_entities_bulk(result.entities)
    kg.add_relationships_bulk(result.relationships)

    click.echo(f"Loaded {len(result.entities)} entities, {len(result.relationships)} relationships")

    output_path = Path(output)
    if fmt == "json":
        from export.json_export import JSONExporter
        JSONExporter().export(kg.engine, output_path)
    elif fmt == "graphml":
        from export.graphml_export import GraphMLExporter
        GraphMLExporter().export(kg.engine, output_path)

    click.echo(f"Exported to {output_path} ({fmt})")
