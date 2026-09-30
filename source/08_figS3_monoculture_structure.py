"""
Figure S3: plant structure in the static monoculture simulations.

Same panels and statistics as Figure 3, for each PFT grown alone (no
community point). Full PFT colours are used, because no community results
are shown next to them (unlike Figure 2).

Input:  data/grouped_pft_mono_static.csv
Output: figures/appendix/figS3_monoculture_structure.png
"""

import matplotlib.pyplot as plt
import pandas as pd

import figure_config as config
import figure_utils as utils
from paths import DATA, FIGURES_APPENDIX

OUT_PNG = FIGURES_APPENDIX / "figS3_monoculture_structure.png"

YLABELS = {
    "volume_per_plant": "Biovolume per plant (m³)",
    "h_ag": "Aboveground height (m)",
    "ag_bg_ratio": "AG/BG ratio (–)",
    "num_plants": "Number of plants",
}

PANEL_ORDER = ["volume_per_plant", "h_ag", "ag_bg_ratio", "num_plants"]

# Four points per salinity group (no community point): smaller group spacing
# than Fig. 3 gives the same gap between groups.
GROUP_SPACING = 3.25


def mean_summaries(grouped_pft):
    """
    Replicate mean and standard deviation for all metrics.

    The table contains one mean-over-time value per salinity, PFT and
    replicate (see replicate_time_means() in figure_utils.py), so standard
    deviations are calculated across replicates.
    """
    return {
        metric: utils.summary_mean_std(
            grouped_pft, ["salinity", "pft"], metric
        ).rename(columns={"mean_value": "value"})
        for metric in PANEL_ORDER
    }


def main():
    config.apply_style()

    grouped_pft = pd.read_csv(DATA / "grouped_pft_mono_static.csv")
    summaries = mean_summaries(grouped_pft)

    fig = utils.draw_structure_figure(
        {metric: (summary, None) for metric, summary in summaries.items()},
        salinity_levels=sorted(grouped_pft["salinity"].unique()),
        pft_levels=sorted(grouped_pft["pft"].unique()),
        ylabels=YLABELS,
        panel_order=PANEL_ORDER,
        show_community=False,
        group_spacing=GROUP_SPACING,
    )

    config.save_figure(fig, OUT_PNG)
    plt.close(fig)


if __name__ == "__main__":
    main()
