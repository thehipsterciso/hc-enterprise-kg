"""CLI stub: AI-powered enrichment has moved to hc-enterprise-kg-enrich."""

from __future__ import annotations

import click


@click.command()
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def enrich(args: tuple[str, ...]) -> None:
    """AI-powered knowledge graph enrichment (moved to hc-enterprise-kg-enrich).

    \b
    Real-world enrichment using LLM reasoning, web search, confidence tiers,
    GraphGuard contracts, and provenance tracking has moved to a dedicated package:

        pip install hc-enterprise-kg-enrich
        hckg-enrich run --graph graph.json --out enriched.json

    \b
    hc-enterprise-kg-enrich features:
      - 7-agent pipeline (Prioritization → Context → Search → Reasoning
                          → Confidence → Coherence → Commit)
      - 8 GraphGuard contracts (parallel, fail-closed)
      - T1-T4 confidence tiers with provenance audit trail
      - Prometheus metrics + OpenTelemetry tracing
      - Audit log (--audit-log) and metrics export (--metrics)

    \b
    Source: https://github.com/thehipsterciso/hc-enterprise-kg-enrich
    """
    click.echo(
        "hckg enrich has moved to hc-enterprise-kg-enrich.\n\n"
        "Install:  pip install hc-enterprise-kg-enrich\n"
        "Run:      hckg-enrich run --graph graph.json --out enriched.json\n\n"
        "See: https://github.com/thehipsterciso/hc-enterprise-kg-enrich",
        err=False,
    )
    raise SystemExit(0)
