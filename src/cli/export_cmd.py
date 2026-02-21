"""CLI commands for exporting the knowledge graph."""

from __future__ import annotations

from pathlib import Path

import click


@click.command()
@click.option("--format", "fmt", type=click.Choice(["json", "graphml"]), default="json")
@click.option("--output", type=click.Path(), required=True, help="Output file path.")
@click.option(
    "--source",
    type=click.Path(exists=True),
    required=True,
    help="Source JSON KG file to re-export.",
)
def export_cmd(fmt: str, output: str, source: str) -> None:
    """Export a knowledge graph to a file."""
    from graph.knowledge_graph import KnowledgeGraph
    from ingest.json_ingestor import JSONIngestor

    kg = KnowledgeGraph()

    # Load from source
    ingestor = JSONIngestor()
    try:
        result = ingestor.ingest(Path(source))
    except Exception as exc:
        click.echo(f"Error reading {source}: {exc}", err=True)
        raise SystemExit(1) from None

    if not result.entities and result.errors:
        click.echo(f"Error: could not load {source}", err=True)
        for err in result.errors[:5]:
            click.echo(f"  {err}", err=True)
        raise SystemExit(1)

    kg.add_entities_bulk(result.entities)
    kg.add_relationships_bulk(result.relationships)

    click.echo(f"Loaded {len(result.entities)} entities, {len(result.relationships)} relationships")

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        if fmt == "json":
            from export.json_export import JSONExporter

            JSONExporter().export(kg.engine, output_path)
        elif fmt == "graphml":
            from export.graphml_export import GraphMLExporter

            GraphMLExporter().export(kg.engine, output_path)
    except PermissionError:
        click.echo(f"Error: permission denied writing to {output_path}", err=True)
        raise SystemExit(1) from None
    except OSError as exc:
        click.echo(f"Error writing output file: {exc}", err=True)
        raise SystemExit(1) from None

    click.echo(f"Exported to {output_path} ({fmt})")
