"""CLI commands for automatic KG construction."""

from __future__ import annotations

from pathlib import Path

import click

from graph.knowledge_graph import KnowledgeGraph


@click.group()
def auto() -> None:
    """Automatic knowledge graph construction."""
    pass


@auto.command()
@click.argument("source", type=click.Path(exists=True), required=False, default=None)
@click.option(
    "--demo", is_flag=True, help="Run with dynamically generated sample data (no file needed)."
)
@click.option("--use-llm/--no-llm", default=False, help="Enable LLM-based extraction.")
@click.option(
    "--use-embeddings/--no-embeddings", default=False, help="Enable embedding-based linking."
)
@click.option("--llm-model", default="gpt-4o-mini", help="LLM model to use.")
@click.option("--output", type=click.Path(), default=None, help="Export result to JSON file.")
@click.pass_context
def build(
    ctx: click.Context,
    source: str | None,
    demo: bool,
    use_llm: bool,
    use_embeddings: bool,
    llm_model: str,
    output: str | None,
) -> None:
    """Build a KG automatically from a data source.

    \b
    Examples:
        hckg auto build data.csv --output result.json
        hckg auto build --demo --output result.json
    """
    from auto.pipeline import AutoKGPipeline

    if source is None and not demo:
        raise click.UsageError(
            "Provide a SOURCE file, or use --demo to run with generated sample data.\n\n"
            "Examples:\n"
            "  hckg auto build data.csv --output result.json\n"
            "  hckg auto build --demo --output result.json"
        )

    backend = ctx.obj.get("backend", "networkx") if ctx.obj else "networkx"
    kg = KnowledgeGraph(backend=backend)

    pipeline = AutoKGPipeline(
        kg,
        use_llm=use_llm,
        use_embeddings=use_embeddings,
        llm_model=llm_model,
    )

    if demo:
        import tempfile

        csv_content = _generate_demo_csv()
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, prefix="hckg_demo_"
        ) as tmp:
            tmp.write(csv_content)
            data = tmp.name
        click.echo("Running auto-KG pipeline on dynamically generated sample data...")
    else:
        source_path = Path(source)  # type: ignore[arg-type]
        data = source if source_path.suffix == ".csv" else source_path.read_text()  # type: ignore[assignment]
        click.echo(f"Running auto-KG pipeline on {source}...")

    result = pipeline.run(data)

    click.echo("\nPipeline results:")
    for key, value in result.stats.items():
        click.echo(f"  {key}: {value}")

    if output:
        from export.json_export import JSONExporter

        JSONExporter().export(kg.engine, Path(output))
        click.echo(f"\nExported to {output}")


def _generate_demo_csv() -> str:
    """Dynamically generate a sample CSV using Faker."""
    from faker import Faker

    fake = Faker()
    Faker.seed(42)

    departments = [
        "Engineering",
        "Marketing",
        "Sales",
        "Finance",
        "HR",
        "Security",
        "IT Operations",
    ]
    titles = {
        "Engineering": ["Software Engineer", "Senior Engineer", "Tech Lead", "DevOps Engineer"],
        "Marketing": ["Marketing Manager", "Content Strategist", "Growth Analyst"],
        "Sales": ["Account Executive", "Sales Director", "Business Development Rep"],
        "Finance": ["Financial Analyst", "Controller", "Accountant"],
        "HR": ["HR Director", "Recruiter", "HR Specialist"],
        "Security": ["Security Analyst", "CISO", "Penetration Tester"],
        "IT Operations": ["System Administrator", "Network Engineer", "DBA"],
    }
    locations = ["New York", "San Francisco", "Chicago", "Austin", "Seattle"]

    lines = ["name,first_name,last_name,email,department,title,location"]
    for _ in range(25):
        first = fake.first_name()
        last = fake.last_name()
        dept = fake.random_element(departments)
        title = fake.random_element(titles[dept])
        location = fake.random_element(locations)
        domain = fake.company().lower().replace(" ", "").replace(",", "")
        email = f"{first.lower()}.{last.lower()}@{domain}.com"
        lines.append(f"{first} {last},{first},{last},{email},{dept},{title},{location}")

    return "\n".join(lines)


@auto.command()
@click.argument("text")
@click.pass_context
def extract(ctx: click.Context, text: str) -> None:
    """Extract entities from text using rule-based patterns."""
    from auto.extractors.rule_based import RuleBasedExtractor

    extractor = RuleBasedExtractor()
    result = extractor.extract(text)

    click.echo(f"Found {len(result.entities)} entities:")
    for entity in result.entities:
        click.echo(f"  [{entity.entity_type.value}] {entity.name}")

    if result.errors:
        click.echo(f"\nErrors: {result.errors}")
