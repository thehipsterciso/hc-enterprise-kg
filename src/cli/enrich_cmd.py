"""CLI command for enriching a knowledge graph to specified maturity tier."""

from __future__ import annotations

from pathlib import Path

import click

from enrichment.profiles.financial import FinancialEnrichmentProfile
from enrichment.profiles.healthcare import HealthcareEnrichmentProfile
from enrichment.profiles.tech import TechEnrichmentProfile


@click.command()
@click.option(
    "--tier",
    type=int,
    default=3,
    help="Target enrichment tier (1-5). Tier 1 is generator output. Tier 5 is full fidelity.",
)
@click.option(
    "--profile",
    type=click.Choice(["tech", "financial", "healthcare"]),
    default="tech",
    help="Enrichment profile (industry focus).",
)
@click.option(
    "--graph-path",
    type=click.Path(exists=True),
    default=None,
    help="Path to graph.json. If not provided, uses graph.json in current directory.",
)
@click.option(
    "--all-tiers/--no-all-tiers",
    default=False,
    help="Enrich all tiers from 2 to target tier, not just the target.",
)
@click.option(
    "--assess-quality/--no-assess-quality",
    default=True,
    help="Run quality assessment after enrichment.",
)
@click.option(
    "--osint-enabled/--no-osint",
    default=False,
    help="Enable OSINT enrichment (requires external data sources).",
)
@click.option(
    "--seed",
    type=int,
    default=42,
    help="Random seed for reproducibility.",
)
@click.option(
    "--verbose/--quiet",
    default=False,
    help="Verbose output.",
)
@click.option(
    "--dry-run/--no-dry-run",
    default=False,
    help="Preview enrichment without modifying the graph.",
)
def enrich(
    tier: int,
    profile: str,
    graph_path: str | None,
    all_tiers: bool,
    assess_quality: bool,
    osint_enabled: bool,
    seed: int,
    verbose: bool,
    dry_run: bool,
) -> None:
    """Enrich a knowledge graph to specified maturity tier.

    \b
    Enrichment adds depth to entities and relationships:
    - Tier 1: Generator output (identity only)
    - Tier 2: Managed (core operational fields)
    - Tier 3: Defined (cross-entity coherence)
    - Tier 4: Measured (quantitative metrics)
    - Tier 5: Optimized (full fidelity & predictive)

    \b
    Example:
        hckg enrich --tier 3 --profile tech
        hckg enrich --tier 5 --profile financial --graph-path my_graph.json
        hckg enrich --tier 2 --all-tiers --assess-quality
    """
    from enrichment.quality import assess_enrichment_quality
    from export.json_export import JSONExporter
    from graph.knowledge_graph import KnowledgeGraph
    from ingest.json_ingest import JSONIngestor

    # Validate tier
    if tier < 1 or tier > 5:
        click.echo(f"Error: Tier must be 1-5, got {tier}", err=True)
        raise SystemExit(1)

    # Resolve graph path
    if graph_path is None:
        graph_path = "graph.json"
    graph_path_obj = Path(graph_path)
    if not graph_path_obj.exists():
        click.echo(f"Error: Graph file not found: {graph_path}", err=True)
        raise SystemExit(1)

    # Load graph
    click.echo(f"Loading graph from {graph_path}...")
    kg = KnowledgeGraph()
    try:
        ingestor = JSONIngestor()
        ingestor.ingest(kg, graph_path_obj)
    except Exception as exc:
        click.echo(f"Error loading graph: {exc}", err=True)
        raise SystemExit(1) from None

    stats = kg.statistics
    click.echo(
        f"Loaded: {stats['entity_count']} entities, {stats['relationship_count']} relationships"
    )

    # Select enrichment profile
    profile_map = {
        "tech": TechEnrichmentProfile(),
        "financial": FinancialEnrichmentProfile(),
        "healthcare": HealthcareEnrichmentProfile(),
    }
    enrich_profile = profile_map[profile]
    click.echo(f"Using profile: {enrich_profile.name}")
    click.echo(f"Focus areas: {', '.join(enrich_profile.get_focus_areas())}")
    click.echo(
        f"Enrichment priority: {', '.join(str(e) for e in enrich_profile.get_enrichment_priority()[:3])}..."
    )

    if osint_enabled:
        click.echo(f"OSINT sources: {', '.join(enrich_profile.get_osint_sources()[:3])}...")
    else:
        click.echo("OSINT: disabled (use --osint-enabled to enable)")

    # Dry-run: print what would be enriched
    if dry_run:
        click.echo("\n=== DRY RUN ===")
        click.echo(f"Would enrich to tier {tier} using {profile} profile")
        if all_tiers:
            click.echo(f"Would process all tiers from 2 to {tier}")
        else:
            click.echo(f"Would process tier {tier} only")
        click.echo("Entity priority for enrichment:")
        for i, etype in enumerate(enrich_profile.get_enrichment_priority()[:5], 1):
            click.echo(f"  {i}. {etype.value}")
        click.echo("")
        click.echo("No changes made (dry-run mode)")
        return

    # Perform enrichment
    click.echo(f"\n{'=' * 60}")
    click.echo(f"Enriching to tier {tier}...")
    click.echo(f"{'=' * 60}\n")

    try:
        from enrichment.orchestrator import EnrichmentOrchestrator

        orchestrator = EnrichmentOrchestrator(kg, enrich_profile, seed=seed)

        # Enrich each tier
        tiers_to_enrich = range(2, tier + 1) if all_tiers else [tier]
        for enrich_tier in tiers_to_enrich:
            click.echo(f"Enriching tier {enrich_tier}...")
            try:
                orchestrator.enrich(enrich_tier, osint_enabled=osint_enabled, verbose=verbose)
                if verbose:
                    click.echo(f"  ✓ Tier {enrich_tier} complete")
            except Exception as exc:
                click.echo(f"Warning: Enrichment for tier {enrich_tier} failed: {exc}", err=True)
                if verbose:
                    import traceback

                    traceback.print_exc()

        click.echo("")
    except ImportError as exc:
        click.echo(f"Error: Could not import enrichment orchestrator: {exc}", err=True)
        raise SystemExit(1) from None
    except Exception as exc:
        click.echo(f"Error during enrichment: {exc}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        raise SystemExit(1) from None

    # Export enriched graph
    output_path = graph_path_obj.parent / f"enriched_{graph_path_obj.stem}_{tier}.json"
    click.echo(f"Exporting enriched graph to {output_path}...")
    try:
        JSONExporter().export(kg.engine, output_path)
        click.echo(f"✓ Exported: {output_path.resolve()}")
    except Exception as exc:
        click.echo(f"Warning: Could not export: {exc}", err=True)

    # Assess quality if requested
    if assess_quality:
        click.echo("\n=== QUALITY ASSESSMENT ===\n")
        try:
            quality_report = assess_enrichment_quality(kg, tier)
            click.echo(quality_report.summary())
            click.echo("")
        except Exception as exc:
            click.echo(f"Warning: Quality assessment failed: {exc}", err=True)

    click.echo("\n=== ENRICHMENT SUMMARY ===\n")
    final_stats = kg.statistics
    click.echo(f"Final entity count:       {final_stats['entity_count']}")
    click.echo(f"Final relationship count: {final_stats['relationship_count']}")
    click.echo(f"Target tier reached:      {tier}")
    click.echo("")
    click.echo("Next steps:")
    click.echo(f"  hckg inspect {output_path.name}")
    click.echo(f"  hckg visualize {output_path.name}")
    click.echo(f"  hckg export --source {output_path.name} --format graphml")
