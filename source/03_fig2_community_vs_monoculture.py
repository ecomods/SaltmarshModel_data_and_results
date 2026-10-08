"""
Figure 2: total biovolume of community and monocultures under static salinity.

Community runs are shown as stacked PFT contributions, monocultures as striped
PFT bars. Values are means of the ten replicate time means in years 5-10;
output steps without plants count as 0. Error bars show one sample SD across
the replicate time means and are drawn behind the bars. For the community,
the SD is calculated from the replicate totals over all PFTs.

Input:  figure_data/comm_mat.csv, mono_mat.csv,
        grouped_all_static.csv, grouped_pft_mono_static.csv
Output: figures/main/fig2_community_vs_monoculture.png
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

import figure_config as config
from paths import FIGURE_DATA, FIGURES_MAIN

OUT_PNG = FIGURES_MAIN / "fig2_community_vs_monoculture.png"

# Colour of the neutral legend entries for community / monoculture.
LEGEND_GREY = "0.4"


def read_matrix(filename):
    """Read a salinity x PFT matrix with integer index and columns."""
    mat = pd.read_csv(FIGURE_DATA / filename, index_col=0)
    mat.index = mat.index.astype(int)
    mat.columns = mat.columns.astype(int)
    return mat


def community_style(color):
    """Full colour, no outline."""
    return {"facecolor": color, "linewidth": 0}


def monoculture_style(color):
    """Opaque PFT colour with translucent white stripes and no outline."""
    return {"facecolor": color, "edgecolor": (1, 1, 1, 0.60),
            "hatch": "////", "linewidth": 0}


def read_replicate_stats():
    """
    Mean and sample SD of the community totals (pft 0) and of each
    monoculture, across replicates.
    """
    data = pd.concat([
        pd.read_csv(FIGURE_DATA / "grouped_all_static.csv"),
        pd.read_csv(FIGURE_DATA / "grouped_pft_mono_static.csv"),
    ], ignore_index=True)
    return data.groupby(["salinity", "pft"]).total_volume.agg(
        mean="mean", sd="std").reset_index()


def draw_figure(comm_mat, mono_mat, stats):
    """Draw stacked communities and striped monocultures with SD behind bars."""
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

    for i, pft in enumerate([0, *pfts]):
        sub = stats[stats.pft == pft].set_index("salinity").loc[salinities]
        # Do not draw error-cap marks for absent PFTs with zero mean and SD.
        visible = (sub["mean"] != 0) | (sub["sd"] != 0)
        ax.errorbar((x_base + offsets[i])[visible], sub["mean"][visible],
                    yerr=sub["sd"][visible], fmt="none", ecolor="0.15",
                    elinewidth=0.65, capsize=1.6, capthick=0.65, zorder=0.8)

    ax.set_xticks(x_base + offsets.mean(), [str(s) for s in salinities])
    ax.set_xlabel("Salinity (ppt)")
    ax.set_ylabel("Total biovolume (m³)")
    ax.set_ylim(0, float((stats["mean"] + stats.sd).max()) * 1.05)
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
    plt.rcParams["hatch.linewidth"] = 0.45
    fig = draw_figure(read_matrix("comm_mat.csv"), read_matrix("mono_mat.csv"),
                      read_replicate_stats())
    config.save_figure(fig, OUT_PNG)
    plt.close(fig)


if __name__ == "__main__":
    main()
