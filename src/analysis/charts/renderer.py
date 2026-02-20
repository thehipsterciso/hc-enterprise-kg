"""Chart renderer using matplotlib to produce analytics visualizations."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from analysis.charts.theme import (
    ENTITY_TYPE_GROUPS,
    FIGURE_SIZE_STANDARD,
    FIGURE_SIZE_WIDE,
    FONT_LABEL,
    FONT_TICK,
    FONT_TITLE,
    GROUP_COLORS,
    PROFILE_COLORS,
)

if TYPE_CHECKING:
    from analysis.charts.models import ChartConfig, ChartDataSet


def _get_plt() -> Any:
    """Lazy-import matplotlib with Agg backend."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


class ChartRenderer:
    """Renders analytics charts from a ChartDataSet using matplotlib."""

    def __init__(self, dataset: ChartDataSet, config: ChartConfig) -> None:
        self._data = dataset
        self._config = config

    def render_all(self) -> list[str]:
        """Render all enabled charts. Returns list of output file paths."""
        paths: list[str] = []
        if self._config.render_scaling:
            paths.append(self.render_scaling_curves())
        if self._config.render_entities:
            paths.append(self.render_entity_distribution())
        return paths

    def _save_figure(self, fig: Any, name: str) -> str:
        """Save a matplotlib figure and return the output path."""
        out_dir = Path(self._config.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        ext = self._config.format
        path = out_dir / f"{name}.{ext}"
        fig.savefig(str(path), dpi=self._config.dpi, bbox_inches="tight")
        plt = _get_plt()
        plt.close(fig)
        return str(path)

    # ------------------------------------------------------------------
    # Chart 1: Scaling Curves
    # ------------------------------------------------------------------

    def render_scaling_curves(self) -> str:
        """Entity count vs employee count — multi-line chart by entity type group."""
        plt = _get_plt()

        fig, (ax_ent, ax_rel) = plt.subplots(1, 2, figsize=FIGURE_SIZE_WIDE)

        for profile_name in self._data.profiles:
            snapshots = self._data.by_profile(profile_name)
            if not snapshots:
                continue

            scales = [s.scale for s in snapshots]
            suffix = f" ({profile_name})" if len(self._data.profiles) > 1 else ""

            # Left panel: entity counts by group
            for group_name, type_list in ENTITY_TYPE_GROUPS.items():
                group_totals = []
                for snap in snapshots:
                    total = sum(snap.entity_types.get(t, 0) for t in type_list)
                    group_totals.append(total)
                color = GROUP_COLORS.get(group_name, "#888888")
                ax_ent.plot(
                    scales,
                    group_totals,
                    marker="o",
                    markersize=4,
                    label=f"{group_name}{suffix}",
                    color=color,
                    alpha=0.8 if len(self._data.profiles) == 1 else 0.6,
                    linestyle="-" if profile_name == self._data.profiles[0] else "--",
                )

            # Bold total line
            totals = [s.entity_count for s in snapshots]
            profile_color = PROFILE_COLORS.get(profile_name, "#333333")
            ax_ent.plot(
                scales,
                totals,
                marker="s",
                markersize=6,
                linewidth=2.5,
                label=f"Total Entities{suffix}",
                color=profile_color,
            )

            # Right panel: relationship totals
            rel_totals = [s.relationship_count for s in snapshots]
            ax_rel.plot(
                scales,
                rel_totals,
                marker="s",
                markersize=6,
                linewidth=2.5,
                label=f"Relationships{suffix}",
                color=profile_color,
            )

        ax_ent.set_xlabel("Employee Count", fontsize=FONT_LABEL)
        ax_ent.set_ylabel("Entity Count", fontsize=FONT_LABEL)
        ax_ent.set_title("Entity Scaling by Type Group", fontsize=FONT_TITLE)
        ax_ent.legend(fontsize=FONT_TICK, loc="upper left")
        ax_ent.grid(True, alpha=0.3)
        ax_ent.tick_params(labelsize=FONT_TICK)

        ax_rel.set_xlabel("Employee Count", fontsize=FONT_LABEL)
        ax_rel.set_ylabel("Relationship Count", fontsize=FONT_LABEL)
        ax_rel.set_title("Relationship Scaling", fontsize=FONT_TITLE)
        ax_rel.legend(fontsize=FONT_TICK)
        ax_rel.grid(True, alpha=0.3)
        ax_rel.tick_params(labelsize=FONT_TICK)

        fig.suptitle("Knowledge Graph Scaling Curves", fontsize=FONT_TITLE + 2, y=1.02)
        fig.tight_layout()

        return self._save_figure(fig, "scaling_curves")

    # ------------------------------------------------------------------
    # Chart 2: Entity Distribution
    # ------------------------------------------------------------------

    def render_entity_distribution(self) -> str:
        """Stacked bar chart showing entity type breakdown across scales."""
        plt = _get_plt()
        import numpy as np

        # Use first profile (or largest profile) for distribution
        profile_name = self._data.profiles[0]
        snapshots = self._data.by_profile(profile_name)
        if not snapshots:
            fig, ax = plt.subplots(figsize=FIGURE_SIZE_STANDARD)
            ax.text(0.5, 0.5, "No data", ha="center", va="center")
            return self._save_figure(fig, f"entity_distribution_{profile_name}")

        scales = [s.scale for s in snapshots]
        x = np.arange(len(scales))
        bar_width = 0.6

        fig, ax = plt.subplots(figsize=FIGURE_SIZE_STANDARD)

        bottoms = np.zeros(len(scales))
        for group_name, type_list in ENTITY_TYPE_GROUPS.items():
            group_counts = []
            for snap in snapshots:
                total = sum(snap.entity_types.get(t, 0) for t in type_list)
                group_counts.append(total)
            color = GROUP_COLORS.get(group_name, "#888888")
            ax.bar(
                x,
                group_counts,
                bar_width,
                bottom=bottoms,
                label=group_name,
                color=color,
                edgecolor="white",
                linewidth=0.5,
            )
            bottoms += np.array(group_counts)

        ax.set_xlabel("Employee Count", fontsize=FONT_LABEL)
        ax.set_ylabel("Entity Count", fontsize=FONT_LABEL)
        ax.set_title(
            f"Entity Distribution by Type Group ({profile_name})", fontsize=FONT_TITLE
        )
        ax.set_xticks(x)
        ax.set_xticklabels([str(s) for s in scales], fontsize=FONT_TICK)
        ax.legend(fontsize=FONT_TICK, loc="upper left")
        ax.grid(True, axis="y", alpha=0.3)
        ax.tick_params(labelsize=FONT_TICK)

        fig.tight_layout()
        return self._save_figure(fig, f"entity_distribution_{profile_name}")
