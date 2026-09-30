"""
Figure 2: total biovolume of community and monocultures under static salinity.

Community runs are shown as stacked PFT contributions, monocultures as pale
PFT bars. Values are means of the ten replicates of the mean total biovolume
in years 5-10.

Input:  data/comm_mat.csv, mono_mat.csv
Output: figures/main/fig2_community_vs_monoculture.png
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

import figure_config as config
from paths import DATA, FIGURES_MAIN

OUT_PNG = FIGURES_MAIN / "fig2_community_vs_monoculture.png"

# Colour of the neutral legend entries for community / monoculture.
LEGEND_GREY = "0.4"


def read_matrix(filename):
    """Read a salinity x PFT matrix with integer index and columns."""
    mat = pd.read_csv(DATA / filename, index_col=0)
    mat.index = mat.index.astype(int)
    mat.columns = mat.columns.astype(int)
    return mat


def community_style(color):
    """Full colour, no outline."""
    return {"facecolor": color, "linewidth": 0}


def monoculture_style(color):
    """Pale colour, no outline."""
    return {"facecolor": config.pale(color), "linewidth": 0}


def draw_figure(comm_mat, mono_mat):
    """Draw community (stacked) and monoculture (pale) bars per salinity."""
    salinities = config.SAL_STATIC
    pfts = config.PFTS
    colors = config.pft_color_map

    fig, ax = plt.subplots(figsize=config.figsize_mm(config.WIDTH_HALF_MM, 60))

    # Per salinity: one community bar followed by four monoculture bars.
    x_base = np.arange(len(salinities))
    bar_gap = 0.16
    width = 0.13
    offsets = np.arange(1 + len(pfts)) * bar_gap

    bottom = np.zeros(len(salinities))
    for pft in pfts:
        vals = comm_mat.loc[salinities, pft].values
        ax.bar(x_base + offsets[0], vals, width, bottom=bottom,
               **community_style(colors[pft]))
        bottom += vals

    for i, pft in enumerate(pfts, start=1):
        ax.bar(x_base + offsets[i], mono_mat.loc[salinities, pft].values, width,
               **monoculture_style(colors[pft]))

    ax.set_xticks(x_base + offsets.mean(), [str(s) for s in salinities])
    ax.set_xlabel("Salinity (ppt)")
    ax.set_ylabel("Total biovolume (m³)")
    ax.set_axisbelow(True)
    ax.grid(axis="y", linewidth=0.5, alpha=0.4)

    handles = [
        Patch(facecolor=colors[pft], edgecolor="none", label=f"PFT {pft}")
        for pft in pfts
    ] + [
        Patch(label="Community", **community_style(LEGEND_GREY)),
        Patch(label="Monoculture", **monoculture_style(LEGEND_GREY)),
    ]
    ax.legend(handles=handles, loc="upper right")

    return fig


def main():
    config.apply_style()
    fig = draw_figure(read_matrix("comm_mat.csv"), read_matrix("mono_mat.csv"))
    config.save_figure(fig, OUT_PNG)
    plt.close(fig)


if __name__ == "__main__":
    main()
