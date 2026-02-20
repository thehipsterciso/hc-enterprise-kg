"""CLI commands for synthetic KG generation."""

from __future__ import annotations

from pathlib import Path

import click

from cli.entity_overrides import entity_count_overrides
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
@click.option(
    "--output",
    type=click.Path(),
    default="graph.json",
    show_default=True,
    help="Export to JSON file.",
)
@entity_count_overrides
@click.pass_context
def org(
    ctx: click.Context,
    profile: str,
    employees: int,
    seed: int | None,
    output: str,
    count_overrides: dict[str, int],
) -> None:
    """Generate a full organizational knowledge graph.

    \b
    Override specific entity counts with dedicated flags:
        hckg generate org --employees 5000 --systems 500 --vendors 100
    """
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
    orchestrator = SyntheticOrchestrator(
        kg, org_profile, seed=seed, count_overrides=count_overrides
    )

    if count_overrides:
        click.echo(f"Entity count overrides: {count_overrides}")

    click.echo(f"Generating {org_profile.name} with ~{employees} employees...")
    counts = orchestrator.generate()

    click.echo("Generation complete:")
    for entity_type, count in counts.items():
        click.echo(f"  {entity_type}: {count}")

    stats = kg.statistics
    click.echo(f"\nTotal entities: {stats['entity_count']}")
    click.echo(f"Total relationships: {stats['relationship_count']}")

    from export.json_export import JSONExporter

    JSONExporter().export(kg.engine, Path(output))
    click.echo(f"\nExported to {output}")
