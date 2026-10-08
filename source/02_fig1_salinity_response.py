"""
Figure 1: salinity response curves of the four PFTs.

Plots the belowground resource limitation (Forman logistic function) over
salinity, with the parameters read from the species files. Coloured vertical
lines and labels mark the static salinities of the simulations.

Input:  model_input/species/Saltmarsh_{1-4}.py
Output: figures/main/fig1_salinity_response.png
"""

import matplotlib.pyplot as plt
import numpy as np

import figure_config as config
import figure_utils as utils
from paths import FIGURES_MAIN

OUT_PNG = FIGURES_MAIN / "fig1_salinity_response.png"

SALINITY_RANGE = np.linspace(0, 160, 1000)


def main():
    config.apply_style()

    fig, ax = plt.subplots(figsize=config.figsize_mm(config.WIDTH_HALF_MM, 60))

    for pft in config.PFTS:
        params = utils.load_species_parameters(pft)
        ax.plot(
            SALINITY_RANGE,
            utils.forman_response(
                SALINITY_RANGE, params["salt_effect_ui"], params["salt_effect_d"]
            ),
            color=config.pft_color_map[pft],
            label=f"PFT {pft}",
        )

    # Vertical lines and labels at the simulated static salinities.
    for salinity in config.SAL_STATIC:
        ax.axvline(salinity, color=config.salinity_color_map[salinity], linewidth=1.0, zorder=1)
        ax.annotate(
            f"{salinity} ppt", xy=(salinity, 1), xycoords=("data", "axes fraction"),
            xytext=(0, 4), textcoords="offset points", ha="center", va="bottom",
            fontsize=plt.rcParams["xtick.labelsize"], annotation_clip=False,
        )

    ax.set_xlabel("Salinity (ppt)")
    ax.set_ylabel(r"$f_{\mathrm{reslim\_bg,Forman}}$ (–)")

    ax.set_xlim(0, 160)
    ax.set_ylim(0.0, 1.0)
    ax.set_xticks(np.arange(0, 161, 20))

    ax.set_axisbelow(True)
    ax.grid(axis="y", linewidth=0.5, alpha=0.4)

    ax.legend(loc="upper right")

    config.save_figure(fig, OUT_PNG)
    plt.close(fig)


if __name__ == "__main__":
    main()
