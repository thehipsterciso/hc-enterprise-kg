"""CLI commands for automatic KG construction."""

from __future__ import annotations

from pathlib import Path

import click

from hc_enterprise_kg.graph.knowledge_graph import KnowledgeGraph


@click.group()
def auto() -> None:
    """Automatic knowledge graph construction."""
    pass


@auto.command()
@click.argument("source", type=click.Path(exists=True))
@click.option("--use-llm/--no-llm", default=False, help="Enable LLM-based extraction.")
@click.option("--use-embeddings/--no-embeddings", default=False, help="Enable embedding-based linking.")
@click.option("--llm-model", default="gpt-4o-mini", help="LLM model to use.")
@click.option("--output", type=click.Path(), default=None, help="Export result to JSON file.")
@click.pass_context
def build(
    ctx: click.Context,
    source: str,
    use_llm: bool,
    use_embeddings: bool,
    llm_model: str,
    output: str | None,
) -> None:
    """Build a KG automatically from a data source."""
    from hc_enterprise_kg.auto.pipeline import AutoKGPipeline

    backend = ctx.obj.get("backend", "networkx") if ctx.obj else "networkx"
    kg = KnowledgeGraph(backend=backend)

    pipeline = AutoKGPipeline(
        kg,
        use_llm=use_llm,
        use_embeddings=use_embeddings,
        llm_model=llm_model,
    )

    source_path = Path(source)
    if source_path.suffix == ".csv":
        data = source
    else:
        data = source_path.read_text()

    click.echo(f"Running auto-KG pipeline on {source}...")
    result = pipeline.run(data)

    click.echo("\nPipeline results:")
    for key, value in result.stats.items():
        click.echo(f"  {key}: {value}")

    if output:
        from hc_enterprise_kg.export.json_export import JSONExporter
        JSONExporter().export(kg.engine, Path(output))
        click.echo(f"\nExported to {output}")


@auto.command()
@click.argument("text")
@click.pass_context
def extract(ctx: click.Context, text: str) -> None:
    """Extract entities from text using rule-based patterns."""
    from hc_enterprise_kg.auto.extractors.rule_based import RuleBasedExtractor

    extractor = RuleBasedExtractor()
    result = extractor.extract(text)

    click.echo(f"Found {len(result.entities)} entities:")
    for entity in result.entities:
        click.echo(f"  [{entity.entity_type.value}] {entity.name}")

    if result.errors:
        click.echo(f"\nErrors: {result.errors}")
