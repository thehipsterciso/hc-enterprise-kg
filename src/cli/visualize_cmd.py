"""CLI command for interactive graph visualization."""

from __future__ import annotations

import json
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
    # CDAIO types
    "ai_model": "#17BECF",
    "data_product": "#BCBD22",
    "data_pipeline": "#7F7F7F",
}

# Node sizes by entity type — structurally important types are larger
ENTITY_SIZES: dict[str, int] = {
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
    # CDAIO types
    "ai_model": 20,
    "data_product": 22,
    "data_pipeline": 18,
}

# Per-theme color tokens used by both the vis.js options and the injected UI panels
THEMES: dict[str, dict[str, str]] = {
    "dark": {
        "bgcolor": "#1a1a2e",
        "font_color": "#e0e0e0",
        "panel_bg": "rgba(26,26,46,0.95)",
        "panel_border": "#333333",
        "text_color": "#e0e0e0",
        "text_muted": "#aaaaaa",
        "divider": "#444444",
        "edge_color": "#555555",
        "edge_highlight": "#cccccc",
        "edge_hover": "#999999",
        "input_bg": "rgba(255,255,255,0.07)",
        "input_border": "#555555",
        "input_text": "#e0e0e0",
        "btn_bg": "rgba(255,255,255,0.10)",
        "btn_border": "#555555",
        "btn_text": "#cccccc",
        "btn_hover_bg": "rgba(255,255,255,0.20)",
        "scroll_track": "rgba(255,255,255,0.04)",
        "scroll_thumb": "rgba(255,255,255,0.22)",
    },
    "light": {
        "bgcolor": "#f0f2f5",
        "font_color": "#222222",
        "panel_bg": "rgba(255,255,255,0.97)",
        "panel_border": "#dddddd",
        "text_color": "#222222",
        "text_muted": "#777777",
        "divider": "#e0e0e0",
        "edge_color": "#bbbbbb",
        "edge_highlight": "#333333",
        "edge_hover": "#777777",
        "input_bg": "#ffffff",
        "input_border": "#cccccc",
        "input_text": "#111111",
        "btn_bg": "#f0f0f0",
        "btn_border": "#cccccc",
        "btn_text": "#555555",
        "btn_hover_bg": "#e0e0e0",
        "scroll_track": "#f0f0f0",
        "scroll_thumb": "#cccccc",
    },
}

# Per-theme color tokens used by both the vis.js options and the injected UI panels
THEMES: dict[str, dict[str, str]] = {
    "dark": {
        "bgcolor": "#1a1a2e",
        "font_color": "#e0e0e0",
        "panel_bg": "rgba(26,26,46,0.95)",
        "panel_border": "#333333",
        "text_color": "#e0e0e0",
        "text_muted": "#aaaaaa",
        "divider": "#444444",
        "edge_color": "#555555",
        "edge_highlight": "#cccccc",
        "edge_hover": "#999999",
        "input_bg": "rgba(255,255,255,0.07)",
        "input_border": "#555555",
        "input_text": "#e0e0e0",
        "btn_bg": "rgba(255,255,255,0.10)",
        "btn_border": "#555555",
        "btn_text": "#cccccc",
        "btn_hover_bg": "rgba(255,255,255,0.20)",
        "scroll_track": "rgba(255,255,255,0.04)",
        "scroll_thumb": "rgba(255,255,255,0.22)",
    },
    "light": {
        "bgcolor": "#f0f2f5",
        "font_color": "#222222",
        "panel_bg": "rgba(255,255,255,0.97)",
        "panel_border": "#dddddd",
        "text_color": "#222222",
        "text_muted": "#777777",
        "divider": "#e0e0e0",
        "edge_color": "#bbbbbb",
        "edge_highlight": "#333333",
        "edge_hover": "#777777",
        "input_bg": "#ffffff",
        "input_border": "#cccccc",
        "input_text": "#111111",
        "btn_bg": "#f0f0f0",
        "btn_border": "#cccccc",
        "btn_text": "#555555",
        "btn_hover_bg": "#e0e0e0",
        "scroll_track": "#f0f0f0",
        "scroll_thumb": "#cccccc",
    },
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


def _build_vis_options(physics: bool, t: dict[str, str]) -> dict:
    """Build the vis.js network options dict, theme-aware."""
    edge_opts: dict = {
        "smooth": {"type": "continuous", "forceDirection": "none"},
        "color": {
            "color": t["edge_color"],
            "highlight": t["edge_highlight"],
            "hover": t["edge_hover"],
            "inherit": False,
        },
        "arrows": {"to": {"enabled": True, "scaleFactor": 0.5}},
        "width": 0.8,
        "selectionWidth": 2.5,
        "hoverWidth": 1.5,
    }
    interaction_opts: dict = {
        "hover": True,
        "tooltipDelay": 80,
        "navigationButtons": True,
        "keyboard": True,
    }
    physics_opts: dict = (
        {
            "forceAtlas2Based": {
                "gravitationalConstant": -80,
                "centralGravity": 0.01,
                "springLength": 150,
                "springConstant": 0.02,
                "damping": 0.4,
            },
            "solver": "forceAtlas2Based",
            "stabilization": {"iterations": 200, "updateInterval": 25},
        }
        if physics
        else {"enabled": False}
    )
    return {"physics": physics_opts, "interaction": interaction_opts, "edges": edge_opts}


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
@click.option(
    "--theme",
    type=click.Choice(["dark", "light"]),
    default="dark",
    show_default=True,
    help="Color theme.",
)
def visualize_cmd(
    source: str,
    output: str | None,
    height: str,
    width: str,
    physics: bool,
    open_browser: bool,
    theme: str,
) -> None:
    """Visualize a knowledge graph as an interactive HTML network.

    \b
    Loads a JSON graph file and renders it as an interactive, color-coded
    network diagram in your browser. Each entity type gets a distinct color
    and size. Hover over nodes for details. The filter panel uses the exact
    same colors as the nodes in the graph.

    \b
    Requires the viz extras:
        poetry install --extras viz

    \b
    Examples:
        hckg visualize graph.json
        hckg visualize graph.json --theme light
        hckg visualize graph.json --output my_viz.html --no-open
        hckg visualize graph.json --no-physics --height 1200px
    """
    try:
        from pyvis.network import Network  # type: ignore[import-untyped]
    except ImportError as err:
        raise click.ClickException(
            "Visualization requires pyvis. Install it with:\n  poetry install --extras viz"
        ) from err

    from graph.knowledge_graph import KnowledgeGraph
    from ingest.json_ingestor import JSONIngestor

    click.echo(f"Loading {source}...")
    kg = KnowledgeGraph()
    ingestor = JSONIngestor()
    try:
        result = ingestor.ingest(Path(source))
    except Exception as exc:
        click.echo(f"Error reading {source}: {exc}", err=True)
        raise SystemExit(1) from None

    if not result.entities and result.errors:
        click.echo(f"Error: could not load {source}", err=True)
        for error_msg in result.errors[:5]:
            click.echo(f"  {error_msg}", err=True)
        raise SystemExit(1)

    kg.add_entities_bulk(result.entities)
    kg.add_relationships_bulk(result.relationships)

    stats = kg.statistics
    click.echo(f"  {stats['entity_count']} entities, {stats['relationship_count']} relationships")

    t = THEMES[theme]

    # No select_menu / filter_menu — pyvis's built-in menus use vis.js's internal
    # group-color palette which does not match our per-node ENTITY_COLORS.
    # We inject a fully custom filter panel below instead.
    net = Network(
        height=height,
        width=width,
        directed=True,
        bgcolor=t["bgcolor"],
        font_color=t["font_color"],
    )

    net.set_options(json.dumps(_build_vis_options(physics, t)))

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

    # title= provides hover tooltip; label= is intentionally omitted so edge
    # relationship text is not rendered permanently on every edge (too noisy).
    for u, v, _key, data in native_graph.edges(keys=True, data=True):
        rel_type = data.get("relationship_type", "related_to")
        net.add_edge(u, v, title=rel_type.replace("_", " "))

    if output is None:
        source_stem = Path(source).stem
        output_path = Path(f"{source_stem}_viz.html")
    else:
        output_path = Path(output)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    net.write_html(str(output_path))

    _inject_custom_ui(output_path, stats, theme)

    click.echo(f"  Visualization saved to {output_path.resolve()}")

    if open_browser:
        click.echo("  Opening in browser...")
        webbrowser.open(f"file://{output_path.resolve()}")


def _inject_custom_ui(html_path: Path, stats: dict, theme: str) -> None:
    """Inject a themed, interactive filter + search UI overlay into the HTML.

    Replaces the old static legend.  The filter panel uses ENTITY_COLORS
    directly so every colored dot is pixel-identical to the corresponding
    node in the graph.  Type visibility is toggled via the vis.js DataSet
    API (hidden property), which automatically hides connected edges too.
    """
    t = THEMES[theme]
    entity_types = stats.get("entity_types", {})
    entity_count = stats["entity_count"]
    rel_count = stats["relationship_count"]

    # Only entity types present in this graph, sorted by count descending
    present = [
        (
            etype,
            {
                "color": ENTITY_COLORS.get(etype, "#cccccc"),
                "count": entity_types[etype],
                "label": etype.replace("_", " ").title(),
            },
        )
        for etype in ENTITY_COLORS
        if etype in entity_types
    ]
    present.sort(key=lambda x: x[1]["count"], reverse=True)

    # Embed type metadata for JS (color + count, keyed by entity type string)
    type_data_js = json.dumps({k: v for k, v in present})

    filter_items_html = "\n".join(
        f'<label class="kg-fi" title="{info["label"]} \u2014 {info["count"]} nodes">'
        f'<input type="checkbox" class="kg-cb" data-type="{etype}" checked '
        f"onchange=\"window.kgToggleType('{etype}', this.checked)\">"
        f'<span class="kg-dot" style="background:{info["color"]}"></span>'
        f'<span class="kg-fn">{info["label"]}</span>'
        f'<span class="kg-fc">{info["count"]}</span>'
        f"</label>"
        for etype, info in present
    )

    css = f"""<style>
  .kg-panel {{
    position: fixed; z-index: 9999;
    background: {t["panel_bg"]};
    border: 1px solid {t["panel_border"]};
    border-radius: 10px; padding: 14px 16px;
    color: {t["text_color"]};
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
    font-size: 13px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.14);
    backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
  }}
  #kg-tp {{ top: 12px; left: 12px; min-width: 220px; max-width: 270px; }}
  #kg-fp {{
    top: 12px; right: 12px; min-width: 200px; max-width: 228px;
    max-height: calc(100vh - 40px);
    display: flex; flex-direction: column; overflow: hidden;
  }}
  .kg-title {{ font-weight: 700; font-size: 15px; margin-bottom: 2px; }}
  .kg-stats {{ font-size: 12px; color: {t["text_muted"]}; margin-bottom: 10px; }}
  .kg-sw {{ position: relative; }}
  #kg-s {{
    width: 100%; box-sizing: border-box;
    background: {t["input_bg"]}; border: 1px solid {t["input_border"]};
    border-radius: 6px; color: {t["input_text"]};
    padding: 6px 26px 6px 10px; font-size: 12px;
    outline: none; font-family: inherit;
    transition: border-color 0.15s;
  }}
  #kg-s:focus {{ border-color: #4E79A7; }}
  #kg-s::placeholder {{ color: {t["text_muted"]}; opacity: 1; }}
  #kg-sc {{
    position: absolute; right: 7px; top: 50%; transform: translateY(-50%);
    cursor: pointer; color: {t["text_muted"]}; font-size: 16px;
    line-height: 1; display: none;
    background: none; border: none; padding: 0 2px; font-family: inherit;
  }}
  #kg-sc:hover {{ color: {t["text_color"]}; }}
  #kg-ss {{
    font-size: 11px; color: {t["text_muted"]};
    margin-top: 5px; min-height: 15px; line-height: 15px;
  }}
  .kg-ph {{
    display: flex; align-items: center; justify-content: space-between;
    font-weight: 600; font-size: 13px;
    margin-bottom: 8px; padding-bottom: 8px;
    border-bottom: 1px solid {t["divider"]}; flex-shrink: 0;
  }}
  .kg-fbs {{ display: flex; gap: 4px; }}
  .kg-btn {{
    background: {t["btn_bg"]}; border: 1px solid {t["btn_border"]};
    color: {t["btn_text"]}; border-radius: 4px; padding: 2px 8px;
    font-size: 11px; cursor: pointer; font-family: inherit;
    transition: background 0.12s;
  }}
  .kg-btn:hover {{ background: {t["btn_hover_bg"]}; }}
  .kg-fl {{
    overflow-y: auto; flex: 1;
    scrollbar-width: thin;
    scrollbar-color: {t["scroll_thumb"]} {t["scroll_track"]};
  }}
  .kg-fl::-webkit-scrollbar {{ width: 5px; }}
  .kg-fl::-webkit-scrollbar-track {{ background: {t["scroll_track"]}; border-radius: 3px; }}
  .kg-fl::-webkit-scrollbar-thumb {{ background: {t["scroll_thumb"]}; border-radius: 3px; }}
  .kg-fi {{
    display: flex; align-items: center; gap: 7px;
    padding: 4px 3px; cursor: pointer; border-radius: 5px;
    transition: background 0.1s; user-select: none;
  }}
  .kg-fi:hover {{ background: rgba(128,128,128,0.10); }}
  .kg-fi input[type="checkbox"] {{
    width: 13px; height: 13px; flex-shrink: 0;
    cursor: pointer; margin: 0; accent-color: #4E79A7;
  }}
  .kg-dot {{
    width: 11px; height: 11px; border-radius: 50%; flex-shrink: 0;
    border: 1.5px solid rgba(0,0,0,0.18);
  }}
  .kg-fn {{ flex: 1; font-size: 12px; }}
  .kg-fc {{ font-size: 11px; color: {t["text_muted"]}; flex-shrink: 0; }}
  .kg-fi[data-hidden="1"] .kg-fn,
  .kg-fi[data-hidden="1"] .kg-fc {{ opacity: 0.38; }}
</style>"""

    title_panel = (
        f'<div id="kg-tp" class="kg-panel">'
        f'<div class="kg-title">hc-enterprise-kg</div>'
        f'<div class="kg-stats">'
        f"{entity_count:,} entities &middot; {rel_count:,} relationships</div>"
        f'<div class="kg-sw">'
        f'<input id="kg-s" type="text" placeholder="Search entities\u2026"'
        f' autocomplete="off" spellcheck="false">'
        f'<button id="kg-sc" onclick="window.kgClearSearch()" title="Clear">&times;</button>'
        f"</div>"
        f'<div id="kg-ss"></div>'
        f"</div>"
    )

    filter_panel = (
        f'<div id="kg-fp" class="kg-panel">'
        f'<div class="kg-ph">Entity Types'
        f'<div class="kg-fbs">'
        f'<button class="kg-btn" onclick="window.kgSetAllFilters(true)">All</button>'
        f'<button class="kg-btn" onclick="window.kgSetAllFilters(false)">None</button>'
        f"</div></div>"
        f'<div class="kg-fl">{filter_items_html}</div>'
        f"</div>"
    )

    js = f"""<script>
(function () {{
  // Type metadata injected by Python: color + count per entity type
  var TYPE_DATA = {type_data_js};

  // Lazily built map: entity_type -> [node_id, ...]
  // Uses node.group which pyvis sets from our group= parameter.
  var _tm = null;
  function tm() {{
    if (_tm) return _tm;
    _tm = {{}};
    network.body.data.nodes.forEach(function (n) {{
      if (!_tm[n.group]) _tm[n.group] = [];
      _tm[n.group].push(n.id);
    }});
    return _tm;
  }}

  // Toggle one entity type on/off.
  // vis.js automatically hides/shows connected edges when a node is hidden.
  window.kgToggleType = function (type, visible) {{
    var ids = tm()[type] || [];
    network.body.data.nodes.update(ids.map(function (id) {{
      return {{ id: id, hidden: !visible }};
    }}));
    var label = document.querySelector('.kg-cb[data-type="' + type + '"]');
    if (label) label.closest('.kg-fi').dataset.hidden = visible ? '0' : '1';
  }};

  // Toggle all entity types at once.
  window.kgSetAllFilters = function (visible) {{
    var updates = [];
    network.body.data.nodes.forEach(function (n) {{
      updates.push({{ id: n.id, hidden: !visible }});
    }});
    network.body.data.nodes.update(updates);
    document.querySelectorAll('.kg-cb').forEach(function (cb) {{
      cb.checked = visible;
      cb.closest('.kg-fi').dataset.hidden = visible ? '0' : '1';
    }});
  }};

  // Search — highlights and fits to matching visible nodes.
  var inp = document.getElementById('kg-s');
  var clr = document.getElementById('kg-sc');
  var sta = document.getElementById('kg-ss');

  window.kgClearSearch = function () {{
    inp.value = '';
    inp.dispatchEvent(new Event('input'));
    inp.focus();
  }};

  inp.addEventListener('input', function () {{
    var q = this.value.trim().toLowerCase();
    clr.style.display = q ? 'block' : 'none';
    if (!q) {{
      network.unselectAll();
      sta.textContent = '';
      return;
    }}
    var hits = [];
    network.body.data.nodes.forEach(function (n) {{
      if (!n.hidden && n.label && n.label.toLowerCase().indexOf(q) !== -1) hits.push(n.id);
    }});
    network.unselectAll();
    if (hits.length) {{
      network.selectNodes(hits);
      var anim = {{ duration: 400, easingFunction: 'easeInOutQuad' }};
      network.fit({{ nodes: hits, animation: anim }});
      sta.textContent = hits.length + ' match' + (hits.length !== 1 ? 'es' : '');
      sta.style.color = '{t["text_muted"]}';
    }} else {{
      sta.textContent = 'No matches found';
      sta.style.color = '#e05252';
    }}
  }});

  document.addEventListener('keydown', function (e) {{
    if (e.key === 'Escape' && document.activeElement === inp) window.kgClearSearch();
  }});
}})();
</script>"""

    content = html_path.read_text()
    if "</body>" not in content:
        click.echo("  Warning: could not inject UI (no </body> tag found)", err=True)
        return
    injection = css + "\n" + title_panel + "\n" + filter_panel + "\n" + js + "\n"
    content = content.replace("</body>", injection + "</body>")
    html_path.write_text(content)
