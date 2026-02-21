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

    try:
        result = ingestor.ingest(Path(source))
    except Exception as exc:
        click.echo(f"Error reading {source}: {exc}", err=True)
        raise SystemExit(1) from None

    # Check for fatal ingest errors (e.g., invalid JSON, file not found)
    if not result.entities and result.errors:
        click.echo(f"Error: could not load {source}", err=True)
        for err in result.errors[:5]:
            click.echo(f"  {err}", err=True)
        raise SystemExit(1)

    kg.add_entities_bulk(result.entities)
    kg.add_relationships_bulk(result.relationships)

    stats = kg.statistics

    click.echo("Knowledge Graph Summary")
    click.echo("=" * 40)
    click.echo(f"Total entities:      {stats['entity_count']}")
    click.echo(f"Total relationships: {stats['relationship_count']}")
    click.echo(f"Graph density:       {stats['density']:.4f}")
    click.echo(f"Weakly connected:    {stats['is_weakly_connected']}")

    click.echo("\nEntity types:")
    for etype, count in sorted(stats["entity_types"].items()):
        click.echo(f"  {etype:20s} {count:>6d}")

    click.echo("\nRelationship types:")
    for rtype, count in sorted(stats.get("relationship_types", {}).items()):
        click.echo(f"  {rtype:20s} {count:>6d}")

    if result.errors:
        click.echo(f"\nIngestion errors: {len(result.errors)}")
        for err in result.errors[:5]:
            click.echo(f"  {err}")
