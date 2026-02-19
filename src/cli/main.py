"""Root CLI for hckg — Enterprise Knowledge Graph."""

from __future__ import annotations

import click


@click.group()
@click.version_option(package_name="hc-enterprise-kg")
@click.option("--backend", default="networkx", help="Graph backend to use.")
@click.pass_context
def cli(ctx: click.Context, backend: str) -> None:
    """hckg — Enterprise Knowledge Graph CLI"""
    ctx.ensure_object(dict)
    ctx.obj["backend"] = backend


# Import and register subcommand groups
from cli.auto_cmd import auto  # noqa: E402
from cli.demo_cmd import demo  # noqa: E402
from cli.export_cmd import export_cmd  # noqa: E402
from cli.generate import generate  # noqa: E402
from cli.inspect_cmd import inspect_cmd  # noqa: E402
from cli.mcp_cmd import mcp_group  # noqa: E402
from cli.serve_cmd import serve_cmd  # noqa: E402
from cli.visualize_cmd import visualize_cmd  # noqa: E402

cli.add_command(demo)
cli.add_command(generate)
cli.add_command(auto)
cli.add_command(export_cmd, name="export")
cli.add_command(inspect_cmd, name="inspect")
cli.add_command(visualize_cmd, name="visualize")
cli.add_command(serve_cmd, name="serve")
cli.add_command(mcp_group, name="mcp")


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
