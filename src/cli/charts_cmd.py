"""CLI command: hckg charts — generate analytics charts."""

from __future__ import annotations

from pathlib import Path

import click


@click.command()
@click.option(
    "--profiles",
    default="tech",
    help="Comma-separated profile names (tech, financial, healthcare).",
)
@click.option(
    "--scales",
    default="100,500,1000,5000",
    help="Comma-separated employee counts.",
)
@click.option(
    "--full",
    is_flag=True,
    default=False,
    help="Run all 3 profiles at 100, 500, 1000, 5000, 10000, 20000.",
)
@click.option(
    "--output",
    type=click.Path(),
    default="./charts",
    help="Output directory for chart files (default: ./charts).",
)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["png", "svg"]),
    default="png",
    help="Output format (default: png).",
)
@click.option("--seed", type=int, default=42, help="Random seed.")
@click.option("--dpi", type=int, default=150, help="Chart resolution (default: 150).")
@click.option("--scaling/--no-scaling", default=True, help="Scaling curves chart.")
@click.option("--entities/--no-entities", default=True, help="Entity distribution chart.")
@click.option(
    "--relationships/--no-relationships", default=True, help="Relationship distribution chart."
)
@click.option("--performance/--no-performance", default=True, help="Performance scaling chart.")
@click.option("--density/--no-density", default=True, help="Density vs scale chart.")
@click.option("--centrality/--no-centrality", default=True, help="Centrality distribution chart.")
@click.option("--quality/--no-quality", default=True, help="Quality radar chart.")
@click.option(
    "--profile-comparison/--no-profile-comparison",
    default=True,
    help="Profile comparison chart (requires 2+ profiles).",
)
def charts(
    profiles: str,
    scales: str,
    full: bool,
    output: str,
    fmt: str,
    seed: int,
    dpi: int,
    scaling: bool,
    entities: bool,
    relationships: bool,
    performance: bool,
    density: bool,
    centrality: bool,
    quality: bool,
    profile_comparison: bool,
) -> None:
    """Generate analytics charts from synthetic data at multiple scales.

    \b
    Quick charts (default):
        hckg charts

    \b
    Full suite (all profiles, all scales):
        hckg charts --full

    \b
    Custom:
        hckg charts --profiles tech,financial --scales 100,1000,5000

    \b
    SVG output:
        hckg charts --format svg --output ./charts-svg

    \b
    Selective charts:
        hckg charts --scaling --performance --no-quality
    """
    try:
        from analysis.charts import ChartConfig, generate_all_charts
    except ImportError:
        raise click.ClickException(
            "Charts require matplotlib. Install with: poetry install --extras viz"
        ) from None

    if full:
        profile_list = ["tech", "financial", "healthcare"]
        scale_list = [100, 500, 1000, 5000, 10000, 20000]
    else:
        profile_list = [p.strip() for p in profiles.split(",")]
        try:
            scale_list = [int(s.strip()) for s in scales.split(",")]
        except ValueError:
            raise click.BadParameter(
                f"Invalid scale values '{scales}'. Must be comma-separated integers.",
                param_hint="--scales",
            ) from None

    valid_profiles = {"tech", "financial", "healthcare"}
    for p in profile_list:
        if p not in valid_profiles:
            raise click.BadParameter(
                f"Unknown profile '{p}'. Valid: {', '.join(sorted(valid_profiles))}",
                param_hint="--profiles",
            )

    if not (1 <= dpi <= 600):
        raise click.BadParameter(
            f"DPI must be between 1 and 600, got {dpi}.",
            param_hint="--dpi",
        )

    output_path = Path(output)
    try:
        output_path.mkdir(parents=True, exist_ok=True)
    except (PermissionError, OSError) as exc:
        click.echo(f"Error creating output directory '{output}': {exc}", err=True)
        raise SystemExit(1) from None

    config = ChartConfig(
        output_dir=output,
        format=fmt,
        scales=scale_list,
        profiles=profile_list,
        seed=seed,
        dpi=dpi,
        render_scaling=scaling,
        render_entities=entities,
        render_relationships=relationships,
        render_performance=performance,
        render_density=density,
        render_centrality=centrality,
        render_quality=quality,
        render_profile_comparison=profile_comparison,
    )

    click.echo(f"Generating charts: profiles={profile_list}, scales={scale_list}")
    click.echo(f"Output: {output} ({fmt.upper()}, {dpi} DPI)")
    click.echo()

    def progress(profile: str, scale: int) -> None:
        click.echo(f"  Generating {profile} @ {scale:,} employees...")

    paths = generate_all_charts(config, progress_callback=progress)

    click.echo()
    click.echo(f"Generated {len(paths)} charts:")
    for p in paths:
        click.echo(f"  {p}")
