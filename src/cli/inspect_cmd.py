"""CLI commands for inspecting the knowledge graph."""

from __future__ import annotations

from pathlib import Path

import click


@click.command()
@click.argument("source", type=click.Path(exists=True))
def inspect_cmd(source: str) -> None:
    """Inspect a knowledge graph JSON file."""
    from graph.knowledge_graph import KnowledgeGraph
    from ingest.json_ingestor import JSONIngestor

    kg = KnowledgeGraph()

    ingestor = JSONIngestor()
    result = ingestor.ingest(Path(source))
    kg.add_entities_bulk(result.entities)
    kg.add_relationships_bulk(result.relationships)

    stats = kg.statistics

    click.echo("Knowledge Graph Summary")
    click.echo("=" * 40)
    click.echo(f"Total entities:      {stats['total_entities']}")
    click.echo(f"Total relationships: {stats['total_relationships']}")
    click.echo(f"Graph density:       {stats['density']:.4f}")
    click.echo(f"Weakly connected:    {stats['is_weakly_connected']}")

    click.echo("\nEntity types:")
    for etype, count in sorted(stats["entity_type_counts"].items()):
        click.echo(f"  {etype:20s} {count:>6d}")

    click.echo("\nRelationship types:")
    for rtype, count in sorted(stats.get("relationship_type_counts", {}).items()):
        click.echo(f"  {rtype:20s} {count:>6d}")

    if result.errors:
        click.echo(f"\nIngestion errors: {len(result.errors)}")
        for err in result.errors[:5]:
            click.echo(f"  {err}")
