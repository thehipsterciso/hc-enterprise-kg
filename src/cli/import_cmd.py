"""Import real organizational data into the knowledge graph."""

from __future__ import annotations

import click


@click.command("import")
@click.argument("source", type=click.Path(exists=True))
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    default="graph.json",
    help="Output graph file path.",
    show_default=True,
)
@click.option(
    "-t",
    "--entity-type",
    "entity_type_str",
    type=str,
    default=None,
    help="Entity type for CSV import (auto-detected if omitted).",
)
@click.option(
    "-m",
    "--merge",
    "merge_path",
    type=click.Path(exists=True),
    default=None,
    help="Merge into an existing graph file.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Validate only, do not write output.",
)
@click.option(
    "--strict",
    is_flag=True,
    default=False,
    help="Treat warnings as errors.",
)
@click.pass_context
def import_cmd(
    ctx: click.Context,
    source: str,
    output: str,
    entity_type_str: str | None,
    merge_path: str | None,
    dry_run: bool,
    strict: bool,
) -> None:
    """Import JSON or CSV data into the knowledge graph.

    Validates data before importing and reports any issues.
    Supports merging into an existing graph.

    \b
    Examples:
        hckg import org-data.json -o graph.json
        hckg import employees.csv -t person -o graph.json
        hckg import systems.csv -t system -m existing.json -o combined.json
        hckg import data.json --dry-run --strict
    """
    from pathlib import Path

    source_path = Path(source)
    ext = source_path.suffix.lower()

    if ext == ".json":
        _import_json(ctx, source_path, output, merge_path, dry_run, strict)
    elif ext == ".csv":
        _import_csv(
            ctx, source_path, output, entity_type_str, merge_path, dry_run, strict
        )
    else:
        click.echo(
            f"Error: unsupported file format '{ext}'. Use .json or .csv.",
            err=True,
        )
        raise SystemExit(1) from None


def _import_json(
    ctx: click.Context,
    source_path: object,
    output: str,
    merge_path: str | None,
    dry_run: bool,
    strict: bool,
) -> None:
    """Handle JSON import path."""
    import json
    from pathlib import Path

    source_path = Path(source_path)  # type: ignore[arg-type]

    click.echo(f"Importing {source_path.name}...")
    click.echo()

    # Parse JSON
    try:
        with open(source_path) as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        click.echo(f"Error: invalid JSON in {source_path.name}: {exc}", err=True)
        raise SystemExit(1) from None
    except UnicodeDecodeError:
        click.echo(
            f"Error: {source_path.name} contains invalid encoding. Expected UTF-8.",
            err=True,
        )
        raise SystemExit(1) from None

    if not isinstance(data, dict):
        click.echo("Error: JSON root must be an object with 'entities' key.", err=True)
        raise SystemExit(1) from None

    # Validate
    from ingest.validator import validate_json_import

    vr = validate_json_import(data)
    _display_validation(vr)

    if not vr.is_valid:
        click.echo("Import aborted due to validation errors.", err=True)
        raise SystemExit(1) from None
    if strict and vr.warnings:
        click.echo("Import aborted: --strict mode and warnings present.", err=True)
        raise SystemExit(1) from None
    if dry_run:
        click.echo("Dry run complete. No output written.")
        return

    # Ingest
    from graph.knowledge_graph import KnowledgeGraph
    from ingest.json_ingestor import JSONIngestor

    backend = ctx.obj.get("backend", "networkx") if ctx.obj else "networkx"
    kg = KnowledgeGraph(backend=backend)

    # Merge existing graph if requested
    if merge_path:
        _merge_existing(kg, merge_path)

    ingestor = JSONIngestor()
    result = ingestor.ingest(source_path)
    if not result.entities and result.errors:
        click.echo(f"Error: could not ingest {source_path.name}", err=True)
        for err in result.errors[:5]:
            click.echo(f"  {err}", err=True)
        raise SystemExit(1) from None

    kg.add_entities_bulk(result.entities)
    kg.add_relationships_bulk(result.relationships)

    # Export
    _export_graph(kg, output, vr)


def _import_csv(
    ctx: click.Context,
    source_path: object,
    output: str,
    entity_type_str: str | None,
    merge_path: str | None,
    dry_run: bool,
    strict: bool,
) -> None:
    """Handle CSV import path."""
    import csv
    from pathlib import Path

    from domain.base import EntityType

    source_path = Path(source_path)  # type: ignore[arg-type]

    click.echo(f"Importing {source_path.name}...")
    click.echo()

    # Read headers
    try:
        with open(source_path, newline="") as f:
            reader = csv.reader(f)
            try:
                headers = next(reader)
            except StopIteration:
                click.echo(f"Error: {source_path.name} is empty.", err=True)
                raise SystemExit(1) from None
    except UnicodeDecodeError:
        click.echo(
            f"Error: {source_path.name} contains invalid encoding. Expected UTF-8.",
            err=True,
        )
        raise SystemExit(1) from None

    # Determine entity type
    if entity_type_str:
        try:
            entity_type = EntityType(entity_type_str)
        except ValueError:
            valid = sorted(e.value for e in EntityType)
            click.echo(
                f"Error: unknown entity type '{entity_type_str}'.\n"
                f"Valid types: {', '.join(valid)}",
                err=True,
            )
            raise SystemExit(1) from None
    else:
        from auto.schema_inference import infer_entity_type

        entity_type = infer_entity_type(headers)
        if entity_type is None:
            valid = sorted(e.value for e in EntityType)
            click.echo(
                f"Error: could not auto-detect entity type from CSV columns.\n"
                f"Use --entity-type to specify. Valid types: {', '.join(valid)}",
                err=True,
            )
            raise SystemExit(1) from None
        click.echo(f"  Auto-detected entity type: {entity_type.value}")

    # Validate columns
    from ingest.validator import validate_csv_import

    vr = validate_csv_import(headers, entity_type)
    _display_validation(vr)

    if not vr.is_valid:
        click.echo("Import aborted due to validation errors.", err=True)
        raise SystemExit(1) from None
    if strict and vr.warnings:
        click.echo("Import aborted: --strict mode and warnings present.", err=True)
        raise SystemExit(1) from None
    if dry_run:
        click.echo("Dry run complete. No output written.")
        return

    # Ingest
    from graph.knowledge_graph import KnowledgeGraph
    from ingest.csv_ingestor import CSVIngestor

    backend = ctx.obj.get("backend", "networkx") if ctx.obj else "networkx"
    kg = KnowledgeGraph(backend=backend)

    if merge_path:
        _merge_existing(kg, merge_path)

    ingestor = CSVIngestor()
    result = ingestor.ingest(source_path, entity_type=entity_type)
    if not result.entities and result.errors:
        click.echo(f"Error: could not ingest {source_path.name}", err=True)
        for err in result.errors[:5]:
            click.echo(f"  {err}", err=True)
        raise SystemExit(1) from None

    kg.add_entities_bulk(result.entities)
    kg.add_relationships_bulk(result.relationships)

    # Update validation counts from actual ingest
    vr.entity_count = result.entity_count
    vr.relationship_count = result.relationship_count
    vr.entity_type_counts = {entity_type.value: result.entity_count}
    vr.relationship_type_counts = {}

    _export_graph(kg, output, vr)


def _merge_existing(kg: object, merge_path: str) -> None:
    """Load an existing graph file and add its data to the KG."""
    from pathlib import Path

    from ingest.json_ingestor import JSONIngestor

    click.echo(f"  Merging with existing graph: {merge_path}")
    ingestor = JSONIngestor()
    result = ingestor.ingest(Path(merge_path))
    if not result.entities and result.errors:
        click.echo(f"Error: could not load merge file {merge_path}", err=True)
        for err in result.errors[:5]:
            click.echo(f"  {err}", err=True)
        raise SystemExit(1) from None

    kg.add_entities_bulk(result.entities)  # type: ignore[attr-defined]
    kg.add_relationships_bulk(result.relationships)  # type: ignore[attr-defined]
    click.echo(
        f"  Loaded {result.entity_count} entities, "
        f"{result.relationship_count} relationships from merge file"
    )


def _display_validation(vr: object) -> None:
    """Display validation results to the user."""
    from ingest.validator import ValidationResult

    if not isinstance(vr, ValidationResult):  # pragma: no cover
        return

    click.echo("Validation")
    if vr.entity_count:
        click.echo(f"  {vr.entity_count} entities validated")
    if vr.relationship_count:
        click.echo(f"  {vr.relationship_count} relationships validated")

    if vr.errors:
        click.echo(f"  {len(vr.errors)} error(s):")
        for err in vr.errors:
            click.echo(f"    {err}")

    if vr.warnings:
        click.echo(f"  {len(vr.warnings)} warning(s):")
        for warn in vr.warnings:
            click.echo(f"    {warn}")

    if not vr.errors and not vr.warnings:
        click.echo("  No issues found")

    click.echo()


def _display_summary(vr: object) -> None:
    """Display import summary."""
    from ingest.validator import ValidationResult

    if not isinstance(vr, ValidationResult):  # pragma: no cover
        return

    click.echo("Import Summary")
    if vr.entity_type_counts:
        total = sum(vr.entity_type_counts.values())
        click.echo(f"  Entities:        {total:>5}")
        for etype, count in sorted(vr.entity_type_counts.items()):
            click.echo(f"    {etype:20s} {count:>5}")
    if vr.relationship_type_counts:
        total = sum(vr.relationship_type_counts.values())
        click.echo(f"  Relationships:   {total:>5}")
        for rtype, count in sorted(vr.relationship_type_counts.items()):
            click.echo(f"    {rtype:20s} {count:>5}")


def _export_graph(kg: object, output: str, vr: object) -> None:
    """Export the knowledge graph to a file."""
    from pathlib import Path

    from export.json_export import JSONExporter

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        JSONExporter().export(kg.engine, output_path)  # type: ignore[attr-defined]
    except PermissionError:
        click.echo(f"Error: permission denied writing to {output_path}", err=True)
        raise SystemExit(1) from None
    except OSError as exc:
        click.echo(f"Error writing output file: {exc}", err=True)
        raise SystemExit(1) from None

    _display_summary(vr)
    click.echo()
    click.echo(f"Output: {output_path}")

    # Sync Claude Desktop config if registered
    try:
        from cli.install_cmd import sync_claude_graph_path

        if sync_claude_graph_path(output_path):
            click.echo(f"Claude Desktop config updated: {output_path.resolve()}")
    except Exception:  # noqa: S110
        pass  # sync is best-effort
