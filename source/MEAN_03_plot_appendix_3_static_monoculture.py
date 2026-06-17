# -*- coding: utf-8 -*-

# =============================================================================
# SCRIPT OVERVIEW
# =============================================================================
# Purpose
# -------
# This appendix script creates the mean-based 2x2 grid figure for static
# monoculture simulations. It mirrors 03_plot_appendix_3_static_monoculture.py
# but uses arithmetic means instead of medians.
#
# Error bar interpretation
# ------------------------
# Points show arithmetic means across the ten replicate simulations. Error bars
# show one standard deviation across the ten replicate-level values.
#
# Output
# ------
# The figure is written to figures/appendix/ as PNG and PDF.
# =============================================================================

"""
Appendix Figure 3:
Mean-based static salinity - monoculture metrics with error bars in a 2 x 2 grid.

Panel layout:
    top left:     Biovolume per Plant
    top right:    Aboveground Height
    bottom left:  AG/BG Ratio
    bottom right: Number of Plants

Output:
    figures/appendix/MEAN_plot_appendix_3_static_monoculture.png
    figures/appendix/MEAN_plot_appendix_3_static_monoculture.pdf
"""

import os
import importlib

import numpy as np
import pandas as pd
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
summary_mean_std = _utils.summary_mean_std


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

OUTPUT_BASENAME = "MEAN_plot_appendix_3_static_monoculture"


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

def build_replicate_level_means(df):
    """
    Create one mean-over-time value per salinity, PFT, replicate, and metric.

    Plant-level metrics are first averaged across plants within each timestep.
    The resulting timestep values are then averaged over time for each replicate.
    Plant number is counted per timestep and then averaged over time for each
    replicate.
    """
    required_cols = ["salinity", "pft", "n", "time"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise KeyError(
            "Missing required columns for monoculture summary: "
            + ", ".join(missing_cols)
        )

    dfc = df.copy().dropna(subset=required_cols)

    plant_metrics = (
        dfc.groupby(["salinity", "pft", "n", "time"], as_index=False)
        .agg({
            "volume_per_plant": "mean",
            "h_ag": "mean",
            "ag_bg_ratio": "mean",
        })
    )

    plant_counts = (
        dfc.groupby(["salinity", "pft", "n", "time"], as_index=False)
        .size()
        .rename(columns={"size": "num_plants"})
    )

    per_timestep = plant_metrics.merge(
        plant_counts,
        on=["salinity", "pft", "n", "time"],
        how="left",
    )

    replicate_means = (
        per_timestep.groupby(["salinity", "pft", "n"], as_index=False)
        .agg({
            "volume_per_plant": "mean",
            "h_ag": "mean",
            "ag_bg_ratio": "mean",
            "num_plants": "mean",
        })
    )

    return replicate_means


def get_summary_table(metric):
    """Return mean and standard-deviation summaries for one metric."""
    return summary_mean_std(
        replicate_level_means,
        ["salinity", "pft"],
        metric,
    )


def plot_metric_panel(ax, metric, ylabel, show_xlabel=False):
    """Plot one monoculture metric into one panel."""
    summary = get_summary_table(metric)

    for i, pft in enumerate(pft_levels_mono):
        dfp = summary[summary["pft"] == pft].copy()

        if dfp.empty:
            continue

        dfp["x_pos"] = dfp["salinity"].map(sal_to_x) + within_offsets_static[i]

        ax.errorbar(
            dfp["x_pos"],
            dfp["mean_value"],
            yerr=[dfp["err_lower"], dfp["err_upper"]],
            fmt="o",
            capsize=3,
            linewidth=1.2,
            color=pft_color_map[int(pft)],
            ecolor=pft_color_map[int(pft)],
            label=f"PFT {int(pft)}",
        )

    ax.set_xticks(group_centers)
    ax.set_xticklabels([str(int(s)) for s in salinity_levels_mono])

    if show_xlabel:
        ax.set_xlabel("Salinity [ppt]")
    else:
        ax.set_xlabel("")

    ax.set_ylabel(ylabel)

    for k in range(len(group_centers) - 1):
        mid = (group_right[k] + group_left[k + 1]) / 2
        ax.axvline(mid, color="0.55", linewidth=1.0, zorder=1)

    ax.grid(axis="y", linestyle=":", linewidth=0.5, alpha=0.8)
    ax.set_axisbelow(True)


# =============================================================================
# Plot layout
# =============================================================================

replicate_level_means = build_replicate_level_means(df_mono_prepared)

salinity_levels_mono = sorted(replicate_level_means["salinity"].dropna().unique())
pft_levels_mono = sorted(replicate_level_means["pft"].dropna().unique())

group_spacing = 2.75
x_group = np.arange(len(salinity_levels_mono)) * group_spacing
sal_to_x = {sal: x_group[i] for i, sal in enumerate(salinity_levels_mono)}

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

print("Done: MEAN_plot_appendix_3_static_monoculture")
print(f"Saved: figures/appendix/{OUTPUT_BASENAME}.png")
print(f"Saved: figures/appendix/{OUTPUT_BASENAME}.pdf")
