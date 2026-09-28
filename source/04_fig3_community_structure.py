# -*- coding: utf-8 -*-

# =============================================================================
# SCRIPT OVERVIEW
# =============================================================================
# Purpose
# -------
# This script creates a 2x2 grid figure for static community simulations. The four
# panels show biovolume per plant, aboveground height, AG/BG ratio, and number of
# plants. Total biovolume is intentionally not included here because it is shown
# separately in 03_fig2_community_vs_monoculture.py.
#
# Two statistical versions are written with the same layout:
#
# Median version
# --------------
# - For plant-level metrics (biovolume per plant, height, AG/BG ratio), the point
#   is the median and the error bars extend to the 25th and 75th percentiles of
#   the individual-plant values.
# - For number of plants, the point is the median and the error bars extend to
#   the 25th and 75th percentiles of replicate-level aggregate values.
#
# Mean version
# ------------
# Points show arithmetic means across the ten replicate simulations. Error bars
# show one standard deviation across the ten replicate-level values.
#
# Output
# ------
# One PNG per version is written to figures/main/.
# =============================================================================

"""
Manuscript Figure 3:
Static salinity - community metrics with error bars in a 2 x 2 grid.

Panel layout:
    top left:     Biovolume per Plant
    top right:    Aboveground Height
    bottom left:  Number of Plants
    bottom right: AG/BG Ratio

Output:
    figures/main/fig3_community_structure_median.png
    figures/main/fig3_community_structure_mean.png
"""

import os

import pandas as pd
import matplotlib.pyplot as plt

import figure_config as _config
import figure_utils as _utils

DERIVED_DIR = _config.DERIVED_DIR
FIGURES_MAIN = _config.FIGURES_MAIN


# =============================================================================
# Settings
# =============================================================================

metrics_comm = {
    "volume_per_plant": "Biovolume per Plant [m³]",
    "h_ag": "Aboveground Height [m]",
    "ag_bg_ratio": "AG/BG Ratio [-]",
    "num_plants": "Number of Plants",
}

panel_order = [
    "volume_per_plant",
    "h_ag",
    "num_plants",
    "ag_bg_ratio",
]

plant_level_metrics = [
    "volume_per_plant",
    "h_ag",
    "ag_bg_ratio",
]

aggregate_metrics = [
    "num_plants",
]


# =============================================================================
# Helper functions
# =============================================================================

def read_table(filename):
    """Read a derived figure table with numeric salinity and PFT columns."""
    df = pd.read_csv(os.path.join(DERIVED_DIR, filename))
    df["salinity"] = pd.to_numeric(df["salinity"], errors="coerce")
    if "pft" in df.columns:
        df["pft"] = pd.to_numeric(df["pft"], errors="coerce").astype("Int64")
    return df


def summary_minmax_individuals(df, group_cols, metric):
    """
    Summarise individual-plant values by median and interquartile range.

    The returned error bars extend from the median to the 25th and 75th
    percentiles of the individual-plant values.
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
            q25_value=lambda x: x.quantile(0.25),
            q75_value=lambda x: x.quantile(0.75),
        )
    )

    summary["err_lower"] = summary["median_value"] - summary["q25_value"]
    summary["err_upper"] = summary["q75_value"] - summary["median_value"]

    return summary


def median_summaries():
    """
    Median version: return per-metric (summary_pft, summary_all) tables with a
    common value column, plus the salinity and PFT levels.
    """
    grouped_pft_static = read_table("grouped_pft_static.csv")
    grouped_all_static = read_table("grouped_all_static.csv")
    df_comm_prepared = read_table("df_comm_prepared.csv")

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

    summaries = {}
    for metric in panel_order:
        if metric in plant_level_metrics:
            summary_pft = summary_minmax_individuals(
                df_comm_prepared, ["salinity", "pft"], metric
            )
            summary_all = summary_minmax_individuals(
                df_comm_prepared, ["salinity"], metric
            )
        elif metric in aggregate_metrics:
            summary_pft = _utils.summary_minmax(
                grouped_pft_static, ["salinity", "pft"], metric
            )
            summary_all = _utils.summary_minmax(
                grouped_all_static, ["salinity"], metric
            )
        else:
            raise ValueError(
                f"Metric '{metric}' is neither listed as plant-level nor "
                "aggregate metric."
            )
        summaries[metric] = tuple(
            s.rename(columns={"median_value": "value"})
            for s in (summary_pft, summary_all)
        )

    return summaries, grouped_pft_static


def mean_summaries():
    """
    Mean version: replicate mean and standard deviation for all metrics.

    The MEAN tables contain one mean-over-time value per replicate and
    scenario, so standard deviations are calculated across replicates.
    """
    grouped_pft_static = read_table("MEAN_grouped_pft_static.csv")
    grouped_all_static = read_table("MEAN_grouped_all_static.csv")

    summaries = {}
    for metric in panel_order:
        summary_pft = _utils.summary_mean_std(
            grouped_pft_static, ["salinity", "pft"], metric
        )
        summary_all = _utils.summary_mean_std(
            grouped_all_static, ["salinity"], metric
        )
        summaries[metric] = tuple(
            s.rename(columns={"mean_value": "value"})
            for s in (summary_pft, summary_all)
        )

    return summaries, grouped_pft_static


# Statistical version -> function returning its summaries.
VERSIONS = {"median": median_summaries, "mean": mean_summaries}


# =============================================================================
# Figures
# =============================================================================

output_dir = _utils.ensure_dir(FIGURES_MAIN)

for version, get_summaries in VERSIONS.items():
    summaries, grouped_pft_static = get_summaries()

    fig = _utils.draw_structure_figure(
        summaries,
        salinity_levels=sorted(grouped_pft_static["salinity"].dropna().unique()),
        pft_levels=sorted(grouped_pft_static["pft"].dropna().unique()),
        ylabels=metrics_comm,
        panel_order=panel_order,
    )

    out_png = os.path.join(output_dir, f"fig3_community_structure_{version}.png")
    plt.savefig(out_png, dpi=600, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_png}")
