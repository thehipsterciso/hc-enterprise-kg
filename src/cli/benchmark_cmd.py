"""CLI command: hckg benchmark — run performance benchmarks."""

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
    default="100,500",
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
    default=None,
    help="Save report to file.",
)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["markdown", "json"]),
    default="markdown",
    help="Report format (default: markdown).",
)
@click.option("--seed", type=int, default=42, help="Random seed.")
def benchmark(
    profiles: str,
    scales: str,
    full: bool,
    output: str | None,
    fmt: str,
    seed: int,
) -> None:
    """Run performance benchmarks across profiles and scales.

    \b
    Quick benchmark (default):
        hckg benchmark

    \b
    Full benchmark (all profiles, all scales):
        hckg benchmark --full

    \b
    Custom:
        hckg benchmark --profiles tech,financial --scales 100,1000,5000

    \b
    Save report:
        hckg benchmark --output report.md
        hckg benchmark --full --format json --output report.json
    """
    from analysis.benchmark import BenchmarkSuite

    if full:
        profile_list = ["tech", "financial", "healthcare"]
        scale_list = [100, 500, 1000, 5000, 10000, 20000]
    else:
        profile_list = [p.strip() for p in profiles.split(",")]
        scale_list = [int(s.strip()) for s in scales.split(",")]

    valid_profiles = {"tech", "financial", "healthcare"}
    for p in profile_list:
        if p not in valid_profiles:
            raise click.BadParameter(
                f"Unknown profile '{p}'. Valid: {', '.join(sorted(valid_profiles))}",
                param_hint="--profiles",
            )

    click.echo(f"Running benchmarks: profiles={profile_list}, scales={scale_list}")
    click.echo()

    suite = BenchmarkSuite(profiles=profile_list, scales=scale_list, seed=seed)

    def progress(phase: str) -> None:
        click.echo(f"  {phase}...")

    report = suite.run_all(progress_callback=progress)

    click.echo()
    click.echo(f"Completed: {len(report.results)} measurements")
    click.echo()

    content = report.to_json() if fmt == "json" else report.to_markdown()

    if output:
        out_path = Path(output)
        out_path.write_text(content)
        click.echo(f"Report saved to {out_path}")
    else:
        click.echo(content)
