"""
Figure S3: plant structure in the static monoculture simulations.

Same panels and statistics as Figure 3, for each PFT grown alone (no
community point). Full PFT colours are used, because no community results
are shown next to them (unlike Figure 2).

Input:  data/derived_figure_data/grouped_pft_mono_static.csv
Output: figures/appendix/figS3_monoculture_structure.png
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
