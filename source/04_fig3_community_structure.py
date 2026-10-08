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


def main():
    config.apply_style()

    grouped_pft = pd.read_csv(FIGURE_DATA / "grouped_pft_static.csv")
    grouped_all = pd.read_csv(FIGURE_DATA / "grouped_all_static.csv")
    fig = utils.draw_structure_figure(utils.structure_summaries(grouped_pft, grouped_all))

    config.save_figure(fig, OUT_PNG)
    plt.close(fig)


if __name__ == "__main__":
    main()
