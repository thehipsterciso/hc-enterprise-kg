"""One-command demo: generates a KG, exports it, and prints a summary."""

from __future__ import annotations

from pathlib import Path

import click


@click.command()
@click.option(
    "--profile",
    type=click.Choice(["tech", "healthcare", "financial"]),
    default="tech",
    help="Organization profile.",
)
@click.option("--employees", type=int, default=100, help="Number of employees.")
@click.option("--seed", type=int, default=42, help="Random seed.")
@click.option("--output", type=click.Path(), default="graph.json", help="Output file path.")
@click.option(
    "--format", "fmt", type=click.Choice(["json", "graphml"]), default="json", help="Output format."
)
@click.option(
    "--clean",
    is_flag=True,
    default=False,
    help="Remove previous output files (graph.json, graph.graphml, *_viz.html) before generating.",
)
def demo(profile: str, employees: int, seed: int, output: str, fmt: str, clean: bool) -> None:
    """Generate a full enterprise KG, export it, and print a summary.

    \b
    Just run:
        hckg demo

    That's it. You'll get a graph.json with a complete enterprise knowledge graph.

    \b
    Use --clean to remove previous output files first:
        hckg demo --clean --employees 200
    """
    from graph.knowledge_graph import KnowledgeGraph
    from synthetic.orchestrator import SyntheticOrchestrator

    # Clean previous outputs if requested
    if clean:
        _clean_outputs()

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

    kg = KnowledgeGraph()
    orchestrator = SyntheticOrchestrator(kg, org_profile, seed=seed)

    click.echo(f"Generating {org_profile.name} ({employees} employees, seed={seed})...")
    orchestrator.generate()

    # Export
    output_path = Path(output)
    if fmt == "graphml":
        from export.graphml_export import GraphMLExporter

        GraphMLExporter().export(kg.engine, output_path)
    else:
        from export.json_export import JSONExporter

        JSONExporter().export(kg.engine, output_path)

    # Print summary
    stats = kg.statistics
    click.echo("")
    click.echo("Entity breakdown:")
    for etype, ecount in sorted(stats["entity_types"].items()):
        click.echo(f"  {etype:20s} {ecount:>6d}")

    click.echo("")
    click.echo(f"Total entities:      {stats['entity_count']}")
    click.echo(f"Total relationships: {stats['relationship_count']}")
    click.echo(f"Output:              {output_path.resolve()}")
    click.echo("")
    click.echo("Next steps:")
    click.echo(f"  hckg inspect {output}")
    click.echo(f"  hckg visualize {output}")
    click.echo(f"  hckg export --source {output} --format graphml --output graph.graphml")


# Default patterns to clean — covers standard output files
_CLEAN_PATTERNS = ["graph.json", "graph.graphml", "result.json", "*_viz.html"]


def _clean_outputs() -> None:
    """Remove previous output files from the current directory."""
    import glob

    cwd = Path(".")
    removed = []
    for pattern in _CLEAN_PATTERNS:
        for match in glob.glob(str(cwd / pattern)):
            p = Path(match)
            if p.is_file():
                p.unlink()
                removed.append(p.name)

    if removed:
        click.echo(f"Cleaned: {', '.join(removed)}")
    else:
        click.echo("Nothing to clean.")
