# -*- coding: utf-8 -*-

# =============================================================================
# SCRIPT OVERVIEW
# =============================================================================
# Purpose
# -------
# This script creates a 2x2 grid figure for static community simulations. The four
# panels show biovolume per plant, aboveground height, AG/BG ratio, and number of
# plants. Total biovolume is intentionally not included here because it is shown
# separately in 03_plot_3_1_static_community_vs_mono.py.
#
# Error bar interpretation
# ------------------------
# - For plant-level metrics (biovolume per plant, height, AG/BG ratio), the point
#   is the median and the error bars show the range of individual plants.
# - For number of plants, the point is the median and the error bars show the
#   range of replicate-level aggregate values.
#
# Output
# ------
# The figure is written directly to figures/main/ as PNG and PDF.
# =============================================================================

"""
Figure 3.2:
Static salinity - community metrics with error bars in a 2 x 2 grid.

This script creates one combined figure for the static community setups.

Panel layout:
    top left:     Biovolume per Plant
    top right:    Aboveground Height
    bottom left:  AG/BG Ratio
    bottom right: Number of Plants

Error bars:
- volume_per_plant, h_ag, ag_bg_ratio:
    median of individual plants with error bars showing the range of
    individual plants.
- num_plants:
    median of aggregated replicate values with error bars showing the range
    of aggregated replicate values.

Output:
    figures/main/plot_3_2_static_community.png
    figures/main/plot_3_2_static_community.pdf

"""

import os
import numpy as np
import pandas as pd
import importlib

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

_config = importlib.import_module("03_figure_config")
_utils = importlib.import_module("03_figure_utils")

FIG_W = _config.FIG_W
FIG_H = _config.FIG_H
pft_color_map = _config.pft_color_map
DERIVED_DIR = _config.DERIVED_DIR
FIGURES_MAIN = _config.FIGURES_MAIN
ensure_dir = _utils.ensure_dir
summary_minmax = _utils.summary_minmax


# =============================================================================
# Settings
# =============================================================================

output_dir = ensure_dir(FIGURES_MAIN)

metrics_comm = {
    "volume_per_plant": "Biovolume per Plant [m³]",
    "h_ag": "Aboveground Height [m]",
    "ag_bg_ratio": "AG/BG Ratio [-]",
    "num_plants": "Number of Plants",
}

panel_order = [
    "volume_per_plant",
    "h_ag",
    "ag_bg_ratio",
    "num_plants",
]

plant_level_metrics = [
    "volume_per_plant",
    "h_ag",
    "ag_bg_ratio",
]

aggregate_metrics = [
    "num_plants",
]

OUTPUT_BASENAME = "plot_3_2_static_community"


# =============================================================================
# Input data
# =============================================================================

grouped_pft_static = pd.read_csv(
    os.path.join(DERIVED_DIR, "grouped_pft_static.csv")
)

grouped_all_static = pd.read_csv(
    os.path.join(DERIVED_DIR, "grouped_all_static.csv")
)

df_comm_prepared = pd.read_csv(
    os.path.join(DERIVED_DIR, "df_comm_prepared.csv")
)


# =============================================================================
# Data preparation
# =============================================================================

grouped_pft_static["salinity"] = pd.to_numeric(
    grouped_pft_static["salinity"], errors="coerce"
)

grouped_all_static["salinity"] = pd.to_numeric(
    grouped_all_static["salinity"], errors="coerce"
)

df_comm_prepared["salinity"] = pd.to_numeric(
    df_comm_prepared["salinity"], errors="coerce"
)

if "pft" in grouped_pft_static.columns:
    grouped_pft_static["pft"] = pd.to_numeric(
        grouped_pft_static["pft"], errors="coerce"
    ).astype("Int64")

if "pft" in df_comm_prepared.columns:
    df_comm_prepared["pft"] = pd.to_numeric(
        df_comm_prepared["pft"], errors="coerce"
    ).astype("Int64")

# In individual-plant data, one row corresponds to one plant.
# Therefore, volume_per_plant is identical to the plant's own volume.
if "volume_per_plant" not in df_comm_prepared.columns:
    if "volume" in df_comm_prepared.columns:
        df_comm_prepared["volume_per_plant"] = df_comm_prepared["volume"]
    else:
        raise KeyError(
            "Neither 'volume_per_plant' nor 'volume' was found in "
            "df_comm_prepared.csv."
        )


# =============================================================================
# Helper functions
# =============================================================================

def summary_minmax_individuals(df, group_cols, metric):
    """
    Summarise individual-plant values by median, minimum, and maximum.

    The returned error bars represent the range of individual plants:
        lower error = median - minimum
        upper error = maximum - median
    """

    if metric not in df.columns:
        raise KeyError(
            f"Metric '{metric}' was not found in df_comm_prepared.csv."
        )

    summary = (
        df
        .dropna(subset=group_cols + [metric])
        .groupby(group_cols, as_index=False)[metric]
        .agg(
            median_value="median",
            min_value="min",
            max_value="max",
        )
    )

    summary["err_lower"] = summary["median_value"] - summary["min_value"]
    summary["err_upper"] = summary["max_value"] - summary["median_value"]

    return summary


def get_summary_tables(metric):
    """
    Select the correct summary logic for each metric.
    """

    if metric in plant_level_metrics:
        summary_pft = summary_minmax_individuals(
            df_comm_prepared,
            ["salinity", "pft"],
            metric,
        )

        summary_all = summary_minmax_individuals(
            df_comm_prepared,
            ["salinity"],
            metric,
        )

    elif metric in aggregate_metrics:
        summary_pft = summary_minmax(
            grouped_pft_static,
            ["salinity", "pft"],
            metric,
        )

        summary_all = summary_minmax(
            grouped_all_static,
            ["salinity"],
            metric,
        )

    else:
        raise ValueError(
            f"Metric '{metric}' is neither listed as plant-level nor "
            "aggregate metric."
        )

    return summary_pft, summary_all


def plot_metric_panel(ax, metric, ylabel, show_xlabel=False):
    """
    Plot one metric into one panel.
    """

    summary_pft, summary_all = get_summary_tables(metric)

    # Community summary
    x_all = summary_all["salinity"].map(sal_to_x) + within_offsets_static[0]

    ax.errorbar(
        x_all,
        summary_all["median_value"],
        yerr=[
            summary_all["err_lower"],
            summary_all["err_upper"],
        ],
        fmt="o",
        capsize=3,
        linewidth=1.2,
        color="black",
        ecolor="black",
        label="community",
    )

    # PFT summaries
    for i, pft in enumerate(pft_levels_comm, start=1):
        dfp = summary_pft[summary_pft["pft"] == pft].copy()

        if dfp.empty:
            continue

        dfp["x_pos"] = (
            dfp["salinity"].map(sal_to_x) + within_offsets_static[i]
        )

        ax.errorbar(
            dfp["x_pos"],
            dfp["median_value"],
            yerr=[
                dfp["err_lower"],
                dfp["err_upper"],
            ],
            fmt="o",
            capsize=3,
            linewidth=1.2,
            color=pft_color_map[int(pft)],
            ecolor=pft_color_map[int(pft)],
            label=f"PFT {int(pft)}",
        )

    # Axes and separators
    ax.set_xticks(group_centers)
    ax.set_xticklabels([str(int(s)) for s in salinity_levels_comm])

    if show_xlabel:
        ax.set_xlabel("Salinity [ppt]")
    else:
        ax.set_xlabel("")

    ax.set_ylabel(ylabel)

    for k in range(len(group_centers) - 1):
        mid = (group_right[k] + group_left[k + 1]) / 2
        ax.axvline(
            mid,
            color="0.55",
            linewidth=1.0,
            zorder=1,
        )

    ax.grid(
        axis="y",
        linestyle=":",
        linewidth=0.5,
        alpha=0.8,
    )

    ax.set_axisbelow(True)


# =============================================================================
# Plot layout
# =============================================================================

salinity_levels_comm = sorted(grouped_pft_static["salinity"].dropna().unique())
pft_levels_comm = sorted(grouped_pft_static["pft"].dropna().unique())

group_spacing = 3.1
x_group = np.arange(len(salinity_levels_comm)) * group_spacing
sal_to_x = {
    sal: x_group[i]
    for i, sal in enumerate(salinity_levels_comm)
}

within_offsets_static = np.array([0.0, 0.55, 1.10, 1.65, 2.20])

group_left = x_group + within_offsets_static[0] - 0.28
group_right = x_group + within_offsets_static[-1] + 0.28
group_centers = x_group + np.mean(within_offsets_static)


# =============================================================================
# Figure
# =============================================================================

fig, axes = plt.subplots(
    nrows=2,
    ncols=2,
    figsize=(FIG_W * 2.15, FIG_H * 2.35),
    sharex=True,
)

axes_flat = axes.ravel()

for ax, metric in zip(axes_flat, panel_order):
    show_xlabel = metric in ["ag_bg_ratio", "num_plants"]
    plot_metric_panel(
        ax=ax,
        metric=metric,
        ylabel=metrics_comm[metric],
        show_xlabel=show_xlabel,
    )

# Legend below all panels.
legend_handles = [
    Line2D(
        [0],
        [0],
        marker="o",
        color="black",
        linestyle="None",
        markersize=5,
        label="community",
    )
]

for pft in pft_levels_comm:
    legend_handles.append(
        Line2D(
            [0],
            [0],
            marker="o",
            color=pft_color_map[int(pft)],
            linestyle="None",
            markersize=5,
            label=f"PFT {int(pft)}",
        )
    )

fig.legend(
    handles=legend_handles,
    labels=[handle.get_label() for handle in legend_handles],
    loc="lower center",
    ncol=5,
    frameon=True,
    bbox_to_anchor=(0.5, 0.01),
)

plt.tight_layout(rect=[0, 0.08, 1, 1])

# =============================================================================
# Output
# =============================================================================

plt.savefig(
    os.path.join(output_dir, f"{OUTPUT_BASENAME}.png"),
    dpi=600,
    bbox_inches="tight",
)

plt.savefig(
    os.path.join(output_dir, f"{OUTPUT_BASENAME}.pdf"),
    bbox_inches="tight",
)

plt.show()
plt.close(fig)


print("Done: plot_3_2_static_community")
print(f"Saved: figures/main/{OUTPUT_BASENAME}.png")
print(f"Saved: figures/main/{OUTPUT_BASENAME}.pdf")
