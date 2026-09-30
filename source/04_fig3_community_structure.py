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
# Points show arithmetic means across the ten replicate simulations. Error bars
# show one standard deviation across the ten replicate-level values.
#
# Output
# ------
# The PNG is written to figures/main/.
# =============================================================================

"""
Manuscript Figure 3:
Static salinity - community metrics with error bars in a 2 x 2 grid.

Panel layout (as in the manuscript caption):
    a) top left:     biovolume per plant
    b) top right:    aboveground height
    c) bottom left:  AG/BG ratio
    d) bottom right: number of plants

Output:
    figures/main/fig3_community_structure.png
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


def mean_summaries():
    """
    Replicate mean and standard deviation for all metrics.

    The tables contain one mean-over-time value per replicate and scenario,
    so standard deviations are calculated across replicates.
    """
    grouped_pft_static = read_table("grouped_pft_static.csv")
    grouped_all_static = read_table("grouped_all_static.csv")

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


# =============================================================================
# Figure
# =============================================================================

_config.apply_style()

output_dir = _utils.ensure_dir(FIGURES_MAIN)

summaries, grouped_pft_static = mean_summaries()

fig = _utils.draw_structure_figure(
    summaries,
    salinity_levels=sorted(grouped_pft_static["salinity"].dropna().unique()),
    pft_levels=sorted(grouped_pft_static["pft"].dropna().unique()),
    ylabels=metrics_comm,
    panel_order=panel_order,
)

_config.save_figure(
    fig,
    os.path.join(output_dir, "fig3_community_structure.png"),
)
plt.close(fig)
