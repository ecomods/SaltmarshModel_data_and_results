"""
Figure S3: plant structure in the static monoculture simulations.

Same panels and statistics as Figure 3, for each PFT grown alone (no
community point).

Input:  figure_data/grouped_pft_mono_static.csv
Output: figures/appendix/figS3_monoculture_structure.png
"""

import matplotlib.pyplot as plt
import pandas as pd

import figure_config as config
import figure_utils as utils
from paths import FIGURE_DATA, FIGURES_APPENDIX

OUT_PNG = FIGURES_APPENDIX / "figS3_monoculture_structure.png"

# Four points per salinity group (no community point): smaller group spacing
# than Fig. 3 gives the same gap between groups.
GROUP_SPACING = 3.25


def main():
    config.apply_style()

    grouped_pft = pd.read_csv(FIGURE_DATA / "grouped_pft_mono_static.csv")
    fig = utils.draw_structure_figure(utils.structure_summaries(grouped_pft),
                                      group_spacing=GROUP_SPACING)

    config.save_figure(fig, OUT_PNG)
    plt.close(fig)


if __name__ == "__main__":
    main()
