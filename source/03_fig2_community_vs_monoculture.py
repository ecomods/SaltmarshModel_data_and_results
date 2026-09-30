"""
Figure 2: total biovolume of community and monocultures under static salinity.

Community runs are shown as stacked PFT contributions, monocultures as pale
PFT bars. Values are means of the ten replicates of the mean total biovolume
in years 5-10.

Input:  data/derived_figure_data/comm_mat.csv, mono_mat.csv
Output: figures/main/fig2_community_vs_monoculture.png
"""

import os
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
from matplotlib.patches import Patch

import figure_config as _config
import figure_utils as _utils

SAL_STATIC = _config.SAL_STATIC
PFTS = _config.PFTS
pft_color_map = _config.pft_color_map
DERIVED_DIR = _config.DERIVED_DIR
FIGURES_MAIN = _config.FIGURES_MAIN
ensure_dir = _utils.ensure_dir

# Colour of the neutral legend entries for community / monoculture.
LEGEND_GREY = "0.4"


# =============================================================================
# Functions
# =============================================================================

def read_matrix(filename):
    """Read a salinity x PFT matrix with integer index and columns."""
    mat = pd.read_csv(os.path.join(DERIVED_DIR, filename), index_col=0)
    mat.index = mat.index.astype(int)
    mat.columns = mat.columns.astype(int)
    return mat


def community_style(color):
    """Full colour, no outline."""
    return {"facecolor": color, "linewidth": 0}


def monoculture_style(color):
    """Pale colour, no outline."""
    return {"facecolor": _config.pale(color), "linewidth": 0}


def draw_figure(comm_mat, mono_mat):
    """Draw community (stacked) and monoculture (pale) bars per salinity."""
    fig, ax = plt.subplots(figsize=_config.figsize_mm(_config.WIDTH_HALF_MM, 60))

    # Per salinity: one community bar followed by four monoculture bars.
    x_base = np.arange(len(SAL_STATIC))
    bar_gap = 0.16
    width = 0.13
    offsets = np.arange(1 + len(PFTS)) * bar_gap

    bottom = np.zeros(len(SAL_STATIC))
    for pft in PFTS:
        vals = comm_mat.loc[SAL_STATIC, pft].values
        ax.bar(x_base + offsets[0], vals, width, bottom=bottom,
               **community_style(pft_color_map[pft]))
        bottom += vals

    for i, pft in enumerate(PFTS, start=1):
        ax.bar(x_base + offsets[i], mono_mat.loc[SAL_STATIC, pft].values, width,
               **monoculture_style(pft_color_map[pft]))

    ax.set_xticks(x_base + offsets.mean(), [str(s) for s in SAL_STATIC])
    ax.set_xlabel("Salinity (ppt)")
    ax.set_ylabel("Total biovolume (m³)")
    ax.set_axisbelow(True)
    ax.grid(axis="y", linewidth=0.5, alpha=0.4)

    handles = [
        Patch(facecolor=pft_color_map[pft], edgecolor="none", label=f"PFT {pft}")
        for pft in PFTS
    ] + [
        Patch(label="Community", **community_style(LEGEND_GREY)),
        Patch(label="Monoculture", **monoculture_style(LEGEND_GREY)),
    ]
    ax.legend(handles=handles, loc="upper right")

    return fig


# =============================================================================
# Figures
# =============================================================================

_config.apply_style()

output_dir = ensure_dir(FIGURES_MAIN)

fig = draw_figure(read_matrix("comm_mat.csv"), read_matrix("mono_mat.csv"))
_config.save_figure(
    fig,
    os.path.join(output_dir, "fig2_community_vs_monoculture.png"),
)
plt.close(fig)
