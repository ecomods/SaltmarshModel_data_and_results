# -*- coding: utf-8 -*-

# =============================================================================
# SCRIPT OVERVIEW
# =============================================================================
# Purpose
# -------
# This appendix script creates a 2x2 grid figure for static monoculture
# simulations. It uses the same layout as 04_fig3_community_structure.py
# (shared draw_structure_figure in figure_utils.py) but shows only
# monoculture PFT results, without a community point. Full PFT colours are
# used: pale colours only work as contrast to community results in the same
# figure (as in Fig. 2).
#
# Points show arithmetic means across the ten replicate simulations. Error bars
# show one standard deviation across the replicate-level means over time.
#
# Output
# ------
# The PNG is written to figures/appendix/.
# =============================================================================

"""
Supplementary Figure S3:
Static salinity - monoculture metrics with error bars in a 2 x 2 grid.

Panel layout (as in Fig. 3):
    a) top left:     biovolume per plant
    b) top right:    aboveground height
    c) bottom left:  AG/BG ratio
    d) bottom right: number of plants

Output:
    figures/appendix/figS3_monoculture_structure.png
"""

import os

import pandas as pd
import matplotlib.pyplot as plt

import figure_config as _config
import figure_utils as _utils

DERIVED_DIR = _config.DERIVED_DIR
FIGURES_APPENDIX = _config.FIGURES_APPENDIX


# =============================================================================
# Settings
# =============================================================================

metrics_mono = {
    "volume_per_plant": "Biovolume per plant (m³)",
    "h_ag": "Aboveground height (m)",
    "ag_bg_ratio": "AG/BG ratio (–)",
    "num_plants": "Number of plants",
}

panel_order = [
    "volume_per_plant",
    "h_ag",
    "ag_bg_ratio",
    "num_plants",
]

# Four points per salinity group (no community point): smaller group spacing
# than Fig. 3 gives the same gap between groups.
GROUP_SPACING = 3.25


# =============================================================================
# Input data
# =============================================================================

def read_mono_prepared():
    """Read the monoculture plant table with numeric key columns."""
    df_mono_prepared = pd.read_csv(
        os.path.join(DERIVED_DIR, "df_mono_prepared.csv")
    )

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

    return df_mono_prepared


# =============================================================================
# Summaries
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


def mean_summaries(df_mono_prepared):
    """Replicate mean and standard deviation for all metrics."""
    replicate_level_means = build_replicate_level_means(df_mono_prepared)
    return {
        metric: _utils.summary_mean_std(
            replicate_level_means, ["salinity", "pft"], metric
        ).rename(columns={"mean_value": "value"})
        for metric in panel_order
    }


# =============================================================================
# Figures
# =============================================================================

def main():
    _config.apply_style()
    output_dir = _utils.ensure_dir(FIGURES_APPENDIX)
    df_mono_prepared = read_mono_prepared()

    summaries = mean_summaries(df_mono_prepared)

    fig = _utils.draw_structure_figure(
        {metric: (summary, None) for metric, summary in summaries.items()},
        salinity_levels=sorted(df_mono_prepared["salinity"].dropna().unique()),
        pft_levels=sorted(df_mono_prepared["pft"].dropna().unique()),
        ylabels=metrics_mono,
        panel_order=panel_order,
        show_community=False,
        group_spacing=GROUP_SPACING,
    )

    _config.save_figure(
        fig,
        os.path.join(output_dir, "figS3_monoculture_structure.png"),
    )
    plt.close(fig)


if __name__ == "__main__":
    main()
