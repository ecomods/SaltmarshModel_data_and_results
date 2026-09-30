"""
Figure 3: plant structure in the static community simulations.

Panels: a) biovolume per plant, b) aboveground height, c) AG/BG ratio,
d) number of plants, for the whole community (black) and each PFT. For each
replicate, plant values are averaged per output step and then over years
5-10. Steps without plants count as 0 plants in d); a)-c) use only steps
with plants. Points show the mean of the ten replicates, error bars one
standard deviation.

Input:  figure_data/grouped_pft_static.csv, grouped_all_static.csv
Output: figures/main/fig3_community_structure.png
"""

import matplotlib.pyplot as plt
import pandas as pd

import figure_config as config
import figure_utils as utils
from paths import FIGURE_DATA, FIGURES_MAIN

OUT_PNG = FIGURES_MAIN / "fig3_community_structure.png"

YLABELS = {
    "volume_per_plant": "Biovolume per plant (m³)",
    "h_ag": "Aboveground height (m)",
    "ag_bg_ratio": "AG/BG ratio (–)",
    "num_plants": "Number of plants",
}

PANEL_ORDER = ["volume_per_plant", "h_ag", "ag_bg_ratio", "num_plants"]


def mean_summaries(grouped_pft, grouped_all):
    """
    Replicate mean and standard deviation for all metrics.

    The tables contain one mean-over-time value per replicate and scenario,
    so standard deviations are calculated across replicates.
    """
    summaries = {}
    for metric in PANEL_ORDER:
        summary_pft = utils.summary_mean_std(grouped_pft, ["salinity", "pft"], metric)
        summary_all = utils.summary_mean_std(grouped_all, ["salinity"], metric)
        summaries[metric] = tuple(
            s.rename(columns={"mean_value": "value"})
            for s in (summary_pft, summary_all)
        )
    return summaries


def main():
    config.apply_style()

    grouped_pft = pd.read_csv(FIGURE_DATA / "grouped_pft_static.csv")
    grouped_all = pd.read_csv(FIGURE_DATA / "grouped_all_static.csv")

    fig = utils.draw_structure_figure(
        mean_summaries(grouped_pft, grouped_all),
        salinity_levels=sorted(grouped_pft["salinity"].unique()),
        pft_levels=sorted(grouped_pft["pft"].unique()),
        ylabels=YLABELS,
        panel_order=PANEL_ORDER,
    )

    config.save_figure(fig, OUT_PNG)
    plt.close(fig)


if __name__ == "__main__":
    main()
