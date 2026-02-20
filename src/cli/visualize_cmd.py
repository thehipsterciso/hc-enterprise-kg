"""CLI command for interactive graph visualization."""

from __future__ import annotations

import webbrowser
from pathlib import Path

import click

# Color palette for entity types — visually distinct, accessible
ENTITY_COLORS: dict[str, str] = {
    # v0.1 original types
    "person": "#4E79A7",
    "department": "#F28E2B",
    "role": "#E15759",
    "system": "#76B7B2",
    "network": "#59A14F",
    "data_asset": "#EDC948",
    "policy": "#B07AA1",
    "vendor": "#FF9DA7",
    "location": "#9C755F",
    "vulnerability": "#BAB0AC",
    "threat_actor": "#D37295",
    "incident": "#FABFD2",
    # Enterprise ontology types
    "regulation": "#A0CBE8",
    "control": "#FFBE7D",
    "risk": "#8CD17D",
    "threat": "#B6992D",
    "integration": "#499894",
    "data_domain": "#86BCB6",
    "data_flow": "#F1CE63",
    "organizational_unit": "#E6A0C4",
    "business_capability": "#D4A6C8",
    "site": "#C49C94",
    "geography": "#DBDB8D",
    "jurisdiction": "#9EDAE5",
    "product_portfolio": "#AEC7E8",
    "product": "#98DF8A",
    "market_segment": "#C5B0D5",
    "customer": "#C7C7C7",
    "contract": "#FFBB78",
    "initiative": "#FF9896",
}

# Node sizes by entity type — structurally important types are larger
ENTITY_SIZES: dict[str, int] = {
    # v0.1 original types
    "person": 15,
    "department": 30,
    "role": 12,
    "system": 22,
    "network": 25,
    "data_asset": 18,
    "policy": 16,
    "vendor": 20,
    "location": 20,
    "vulnerability": 14,
    "threat_actor": 16,
    "incident": 18,
    # Enterprise ontology types
    "regulation": 20,
    "control": 14,
    "risk": 18,
    "threat": 16,
    "integration": 16,
    "data_domain": 24,
    "data_flow": 14,
    "organizational_unit": 28,
    "business_capability": 26,
    "site": 22,
    "geography": 20,
    "jurisdiction": 18,
    "product_portfolio": 24,
    "product": 20,
    "market_segment": 22,
    "customer": 18,
    "contract": 16,
    "initiative": 22,
}


def _get_node_label(data: dict) -> str:
    """Extract the best display label from node data."""
    for field in ("name", "hostname", "cve_id", "title", "label"):
        if field in data and data[field]:
            return str(data[field])
    return data.get("entity_type", "?")


def _build_tooltip(data: dict) -> str:
    """Build a rich HTML tooltip for a node."""
    skip = {"id", "created_at", "updated_at", "metadata"}
    lines = []
    for key, value in sorted(data.items()):
        if key in skip or value is None or value == "" or value == []:
            continue
        display_key = key.replace("_", " ").title()
        lines.append(f"<b>{display_key}:</b> {value}")
    return "<br>".join(lines)


@click.command()
@click.argument("source", type=click.Path(exists=True))
@click.option(
    "--output",
    type=click.Path(),
    default=None,
    help="Output HTML file path. Defaults to <source-stem>_viz.html.",
)
@click.option(
    "--height",
    type=str,
    default="900px",
    help="Visualization height (e.g., '900px', '100%%').",
)
@click.option(
    "--width",
    type=str,
    default="100%",
    help="Visualization width.",
)
@click.option(
    "--physics/--no-physics",
    default=True,
    help="Enable physics simulation for layout.",
)
@click.option(
    "--open/--no-open",
    "open_browser",
    default=True,
    help="Automatically open in browser.",
)
def visualize_cmd(
    source: str,
    output: str | None,
    height: str,
    width: str,
    physics: bool,
    open_browser: bool,
) -> None:
    """Visualize a knowledge graph as an interactive HTML network.

    \b
    Loads a JSON graph file and renders it as an interactive, color-coded
    network diagram in your browser. Each entity type gets a distinct color
    and size. Hover over nodes for details.

    \b
    Requires the viz extras:
        poetry install --extras viz

    \b
    Examples:
        hckg visualize graph.json
        hckg visualize graph.json --output my_viz.html --no-open
        hckg visualize graph.json --no-physics --height 1200px
    """
    try:
        from pyvis.network import Network
    except ImportError as err:
        raise click.ClickException(
            "Visualization requires pyvis. Install it with:\n  poetry install --extras viz"
        ) from err

    from graph.knowledge_graph import KnowledgeGraph
    from ingest.json_ingestor import JSONIngestor

    # Ingest the graph
    click.echo(f"Loading {source}...")
    kg = KnowledgeGraph()
    ingestor = JSONIngestor()
    result = ingestor.ingest(Path(source))
    kg.add_entities_bulk(result.entities)
    kg.add_relationships_bulk(result.relationships)

    stats = kg.statistics
    click.echo(f"  {stats['entity_count']} entities, {stats['relationship_count']} relationships")

    # Build pyvis network
    net = Network(
        height=height,
        width=width,
        directed=True,
        bgcolor="#1a1a2e",
        font_color="#e0e0e0",
        select_menu=True,
        filter_menu=True,
    )

    # Physics configuration for readable layouts
    if physics:
        net.set_options("""
        {
            "physics": {
                "forceAtlas2Based": {
                    "gravitationalConstant": -80,
                    "centralGravity": 0.01,
                    "springLength": 150,
                    "springConstant": 0.02,
                    "damping": 0.4
                },
                "solver": "forceAtlas2Based",
                "stabilization": {
                    "iterations": 200,
                    "updateInterval": 25
                }
            },
            "interaction": {
                "hover": true,
                "tooltipDelay": 100,
                "navigationButtons": true,
                "keyboard": true
            },
            "edges": {
                "smooth": {
                    "type": "continuous",
                    "forceDirection": "none"
                },
                "color": {
                    "color": "#555555",
                    "highlight": "#ffffff",
                    "hover": "#aaaaaa"
                },
                "arrows": {
                    "to": {
                        "enabled": true,
                        "scaleFactor": 0.5
                    }
                }
            }
        }
        """)
    else:
        net.set_options("""
        {
            "physics": {
                "enabled": false
            },
            "interaction": {
                "hover": true,
                "tooltipDelay": 100,
                "navigationButtons": true,
                "keyboard": true
            },
            "edges": {
                "smooth": {
                    "type": "continuous",
                    "forceDirection": "none"
                },
                "color": {
                    "color": "#555555",
                    "highlight": "#ffffff",
                    "hover": "#aaaaaa"
                },
                "arrows": {
                    "to": {
                        "enabled": true,
                        "scaleFactor": 0.5
                    }
                }
            }
        }
        """)

    # Add nodes
    native_graph = kg.engine.get_native_graph()
    for node_id, data in native_graph.nodes(data=True):
        entity_type = data.get("entity_type", "unknown")
        color = ENTITY_COLORS.get(entity_type, "#cccccc")
        size = ENTITY_SIZES.get(entity_type, 15)
        label = _get_node_label(data)
        title = _build_tooltip(data)

        net.add_node(
            node_id,
            label=label,
            title=title,
            color=color,
            size=size,
            group=entity_type,
            borderWidth=2,
            borderWidthSelected=4,
        )

    # Add edges
    for u, v, _key, data in native_graph.edges(keys=True, data=True):
        rel_type = data.get("relationship_type", "related_to")
        label = rel_type.replace("_", " ")
        net.add_edge(
            u,
            v,
            title=label,
            label=label,
            font={"size": 8, "color": "#888888"},
        )

    # Determine output path
    if output is None:
        source_stem = Path(source).stem
        output_path = Path(f"{source_stem}_viz.html")
    else:
        output_path = Path(output)

    # Write HTML
    net.write_html(str(output_path))

    # Inject a legend into the HTML
    _inject_legend(output_path, stats)

    click.echo(f"  Visualization saved to {output_path.resolve()}")

    if open_browser:
        click.echo("  Opening in browser...")
        webbrowser.open(f"file://{output_path.resolve()}")


def _inject_legend(html_path: Path, stats: dict) -> None:
    """Inject a floating legend and title bar into the visualization HTML."""
    entity_types_in_graph = set(stats.get("entity_types", {}).keys())

    legend_items = []
    for etype, color in ENTITY_COLORS.items():
        if etype in entity_types_in_graph:
            display = etype.replace("_", " ").title()
            count = stats["entity_types"].get(etype, 0)
            legend_items.append(
                f'<div style="display:flex;align-items:center;margin:3px 0;">'
                f'<span style="display:inline-block;width:12px;height:12px;'
                f"border-radius:50%;background:{color};margin-right:8px;"
                f'flex-shrink:0;"></span>'
                f'<span style="font-size:12px;">{display} ({count})</span></div>'
            )

    legend_html = (
        '<div id="kg-legend" style="'
        "position:fixed;top:10px;right:10px;background:rgba(26,26,46,0.92);"
        "border:1px solid #333;border-radius:8px;padding:14px 16px;"
        "z-index:9999;color:#e0e0e0;font-family:system-ui,sans-serif;"
        'max-width:200px;backdrop-filter:blur(8px);">'
        '<div style="font-weight:600;font-size:13px;margin-bottom:8px;'
        'border-bottom:1px solid #444;padding-bottom:6px;">Entity Types</div>'
        + "\n".join(legend_items)
        + "</div>"
    )

    title_html = (
        '<div style="'
        "position:fixed;top:10px;left:10px;background:rgba(26,26,46,0.92);"
        "border:1px solid #333;border-radius:8px;padding:12px 16px;"
        "z-index:9999;color:#e0e0e0;font-family:system-ui,sans-serif;"
        'backdrop-filter:blur(8px);">'
        '<div style="font-weight:700;font-size:15px;">hc-enterprise-kg</div>'
        f'<div style="font-size:12px;color:#aaa;margin-top:2px;">'
        f"{stats['entity_count']} entities &middot; "
        f"{stats['relationship_count']} relationships</div>"
        "</div>"
    )

    content = html_path.read_text()
    content = content.replace("</body>", f"{legend_html}\n{title_html}\n</body>")
    html_path.write_text(content)
