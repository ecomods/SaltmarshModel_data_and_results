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
# Summaries
# =============================================================================

def mean_summaries():
    """
    Replicate mean and standard deviation for all metrics.

    The table contains one mean-over-time value per salinity, PFT and
    replicate (see replicate_time_means() in figure_utils.py), so standard
    deviations are calculated across replicates.
    """
    grouped_pft = pd.read_csv(os.path.join(DERIVED_DIR, "grouped_pft_mono_static.csv"))
    summaries = {
        metric: _utils.summary_mean_std(
            grouped_pft, ["salinity", "pft"], metric
        ).rename(columns={"mean_value": "value"})
        for metric in panel_order
    }
    return summaries, grouped_pft


# =============================================================================
# Figures
# =============================================================================

def main():
    _config.apply_style()
    output_dir = _utils.ensure_dir(FIGURES_APPENDIX)

    summaries, grouped_pft = mean_summaries()

    fig = _utils.draw_structure_figure(
        {metric: (summary, None) for metric, summary in summaries.items()},
        salinity_levels=sorted(grouped_pft["salinity"].unique()),
        pft_levels=sorted(grouped_pft["pft"].unique()),
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
