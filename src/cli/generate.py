"""CLI commands for synthetic KG generation."""

from __future__ import annotations

from pathlib import Path

import click

from graph.knowledge_graph import KnowledgeGraph


@click.group()
def generate() -> None:
    """Generate synthetic knowledge graphs."""
    pass


@generate.command()
@click.option(
    "--profile",
    type=click.Choice(["tech", "healthcare", "financial"]),
    default="tech",
    help="Organization profile to use.",
)
@click.option("--employees", type=int, default=500, help="Number of employees.")
@click.option("--seed", type=int, default=None, help="Random seed for reproducibility.")
@click.option("--output", type=click.Path(), default=None, help="Export to JSON file.")
@click.pass_context
def org(ctx: click.Context, profile: str, employees: int, seed: int | None, output: str | None) -> None:
    """Generate a full organizational knowledge graph."""
    from synthetic.orchestrator import SyntheticOrchestrator

    # Load profile
    if profile == "tech":
        from synthetic.profiles.tech_company import mid_size_tech_company
        org_profile = mid_size_tech_company(employees)
    elif profile == "healthcare":
        from synthetic.profiles.healthcare_org import healthcare_org
        org_profile = healthcare_org(employees)
    elif profile == "financial":
        from synthetic.profiles.financial_org import financial_org
        org_profile = financial_org(employees)
    else:
        raise click.BadParameter(f"Unknown profile: {profile}")

    backend = ctx.obj.get("backend", "networkx") if ctx.obj else "networkx"
    kg = KnowledgeGraph(backend=backend)
    orchestrator = SyntheticOrchestrator(kg, org_profile, seed=seed)

    click.echo(f"Generating {org_profile.name} with ~{employees} employees...")
    counts = orchestrator.generate()

    click.echo("Generation complete:")
    for entity_type, count in counts.items():
        click.echo(f"  {entity_type}: {count}")

    stats = kg.statistics
    click.echo(f"\nTotal entities: {stats['entity_count']}")
    click.echo(f"Total relationships: {stats['relationship_count']}")

    if output:
        from export.json_export import JSONExporter
        JSONExporter().export(kg.engine, Path(output))
        click.echo(f"\nExported to {output}")
