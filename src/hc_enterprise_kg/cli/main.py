"""Root CLI for hckg — Enterprise Knowledge Graph."""

from __future__ import annotations

import click

from hc_enterprise_kg.graph.knowledge_graph import KnowledgeGraph


@click.group()
@click.version_option(package_name="hc-enterprise-kg")
@click.option("--backend", default="networkx", help="Graph backend to use.")
@click.pass_context
def cli(ctx: click.Context, backend: str) -> None:
    """hckg — Enterprise Knowledge Graph CLI"""
    ctx.ensure_object(dict)
    ctx.obj["backend"] = backend


# Import and register subcommand groups
from hc_enterprise_kg.cli.generate import generate  # noqa: E402
from hc_enterprise_kg.cli.auto_cmd import auto  # noqa: E402
from hc_enterprise_kg.cli.export_cmd import export_cmd  # noqa: E402
from hc_enterprise_kg.cli.inspect_cmd import inspect_cmd  # noqa: E402

cli.add_command(generate)
cli.add_command(auto)
cli.add_command(export_cmd, name="export")
cli.add_command(inspect_cmd, name="inspect")


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
