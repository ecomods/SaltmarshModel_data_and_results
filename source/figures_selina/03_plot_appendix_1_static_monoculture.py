# -*- coding: utf-8 -*-

# =============================================================================
# SCRIPT OVERVIEW
# =============================================================================
# Purpose
# -------
# This appendix script creates a 2x2 grid figure for static monoculture
# simulations. It mirrors the structure of 03_plot_3_2_static_community.py but shows
# only monoculture PFT results, without a community reference point.
#
# Error bar interpretation
# ------------------------
# - For plant-level metrics, error bars show the range of individual plants.
# - For number of plants, error bars show the range of replicate-level aggregate
#   values.
#
# Output
# ------
# The figure is written to figures/appendix/ as PNG and PDF.
# =============================================================================

"""
Appendix Figure 1:
Static salinity - monoculture metrics with error bars in a 2 x 2 grid.

This script creates one combined figure for the static monoculture setups.

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
    figures/appendix/plot_appendix_1_static_monoculture.png
    figures/appendix/plot_appendix_1_static_monoculture.pdf

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
FIGURES_APPENDIX = _config.FIGURES_APPENDIX
ensure_dir = _utils.ensure_dir


# =============================================================================
# Settings
# =============================================================================

output_dir = ensure_dir(FIGURES_APPENDIX)

metrics_mono = {
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

OUTPUT_BASENAME = "plot_appendix_1_static_monoculture"


# =============================================================================
# Input data
# =============================================================================

df_mono_prepared = pd.read_csv(
    os.path.join(DERIVED_DIR, "df_mono_prepared.csv")
)


# =============================================================================
# Data preparation
# =============================================================================

df_mono_prepared["salinity"] = pd.to_numeric(
    df_mono_prepared["salinity"], errors="coerce"
)

df_mono_prepared["pft"] = pd.to_numeric(
    df_mono_prepared["pft"], errors="coerce"
).astype("Int64")

if "n" in df_mono_prepared.columns:
    df_mono_prepared["n"] = pd.to_numeric(
        df_mono_prepared["n"], errors="coerce"
    ).astype("Int64")

# In individual-plant data, one row corresponds to one plant.
# Therefore, volume_per_plant is identical to the plant's own volume.
if "volume_per_plant" not in df_mono_prepared.columns:
    if "volume" in df_mono_prepared.columns:
        df_mono_prepared["volume_per_plant"] = df_mono_prepared["volume"]
    else:
        raise KeyError(
            "Neither 'volume_per_plant' nor 'volume' was found in "
            "df_mono_prepared.csv."
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
            f"Metric '{metric}' was not found in df_mono_prepared.csv."
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


def summary_minmax_num_plants(df):
    """
    Summarise plant numbers for monoculture setups.

    Step 1: count plants per salinity, PFT, replicate, and timestep.
    Step 2: calculate the median over time for each replicate.
    Step 3: calculate median, minimum, and maximum across replicates.

    The returned error bars represent the range of replicate-level medians.
    """

    required_cols = ["salinity", "pft", "n", "time"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise KeyError(
            "Missing required columns for num_plants summary: "
            + ", ".join(missing_cols)
        )

    per_timestep = (
        df
        .dropna(subset=required_cols)
        .groupby(required_cols, as_index=False)
        .size()
        .rename(columns={"size": "num_plants"})
    )

    rep_median = (
        per_timestep
        .groupby(["salinity", "pft", "n"], as_index=False)["num_plants"]
        .median()
        .rename(columns={"num_plants": "rep_median_num_plants"})
    )

    summary = (
        rep_median
        .groupby(["salinity", "pft"], as_index=False)["rep_median_num_plants"]
        .agg(
            median_value="median",
            min_value="min",
            max_value="max",
        )
    )

    summary["err_lower"] = summary["median_value"] - summary["min_value"]
    summary["err_upper"] = summary["max_value"] - summary["median_value"]

    return summary


def get_summary_table(metric):
    """
    Select the correct summary logic for each metric.
    """

    if metric in plant_level_metrics:
        summary = summary_minmax_individuals(
            df_mono_prepared,
            ["salinity", "pft"],
            metric,
        )

    elif metric in aggregate_metrics:
        summary = summary_minmax_num_plants(df_mono_prepared)

    else:
        raise ValueError(
            f"Metric '{metric}' is neither listed as plant-level nor "
            "aggregate metric."
        )

    return summary


def plot_metric_panel(ax, metric, ylabel, show_xlabel=False):
    """
    Plot one monoculture metric into one panel.
    """

    summary = get_summary_table(metric)

    for i, pft in enumerate(pft_levels_mono):
        dfp = summary[summary["pft"] == pft].copy()

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
    ax.set_xticklabels([str(int(s)) for s in salinity_levels_mono])

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

salinity_levels_mono = sorted(df_mono_prepared["salinity"].dropna().unique())
pft_levels_mono = sorted(df_mono_prepared["pft"].dropna().unique())

group_spacing = 2.75
x_group = np.arange(len(salinity_levels_mono)) * group_spacing
sal_to_x = {
    sal: x_group[i]
    for i, sal in enumerate(salinity_levels_mono)
}

within_offsets_static = np.array([0.0, 0.55, 1.10, 1.65])

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
        ylabel=metrics_mono[metric],
        show_xlabel=show_xlabel,
    )

# Legend below all panels.
legend_handles = []

for pft in pft_levels_mono:
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
    ncol=4,
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


print("Done: plot_appendix_1_static_monoculture")
print(f"Saved: figures/appendix/{OUTPUT_BASENAME}.png")
print(f"Saved: figures/appendix/{OUTPUT_BASENAME}.pdf")
