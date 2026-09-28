# -*- coding: utf-8 -*-

# =============================================================================
# SCRIPT OVERVIEW
# =============================================================================
# Purpose
# -------
# This script creates the main static community-vs-monoculture total biovolume
# figure. Community simulations are shown as stacked PFT contributions, while
# monoculture simulations are shown as hatched PFT-specific bars.
#
# Data basis
# ----------
# The script reads the total biovolume matrices (salinity x PFT) prepared by
# 01_prepare_figure_data.py in data/derived_figure_data/:
#     median version: comm_mat.csv, mono_mat.csv
#     mean version:   MEAN_comm_mat.csv, MEAN_mono_mat.csv
#
# Output
# ------
# One PNG per version is written to figures/main/.
# =============================================================================

"""
Manuscript Figure 2:
Static salinity - community (stacked) vs monoculture (hatched)

Output:
    figures/main/fig2_community_vs_monoculture_median.png
    figures/main/fig2_community_vs_monoculture_mean.png
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

# Statistical version -> file prefix of its input tables.
VERSION_PREFIXES = {"median": "", "mean": "MEAN_"}

HATCH = "///"


# =============================================================================
# Functions
# =============================================================================

def read_matrix(filename):
    """Read a salinity x PFT matrix with integer index and columns."""
    mat = pd.read_csv(os.path.join(DERIVED_DIR, filename), index_col=0)
    mat.index = mat.index.astype(int)
    mat.columns = mat.columns.astype(int)
    return mat


def draw_figure(comm_mat, mono_mat):
    """Draw community (stacked) and monoculture (hatched) bars per salinity."""
    fig, ax = plt.subplots(figsize=_config.figsize_mm(_config.WIDTH_HALF_MM, 65))

    # Per salinity: one community bar followed by four monoculture bars.
    x_base = np.arange(len(SAL_STATIC))
    bar_gap = 0.16
    width = 0.13
    offsets = np.arange(1 + len(PFTS)) * bar_gap
    bar_style = {"width": width, "edgecolor": "black", "linewidth": 0.5}

    bottom = np.zeros(len(SAL_STATIC))
    for pft in PFTS:
        vals = comm_mat.loc[SAL_STATIC, pft].values
        ax.bar(x_base + offsets[0], vals, bottom=bottom,
               color=pft_color_map[pft], **bar_style)
        bottom += vals

    for i, pft in enumerate(PFTS, start=1):
        ax.bar(x_base + offsets[i], mono_mat.loc[SAL_STATIC, pft].values,
               color=pft_color_map[pft], hatch=HATCH, **bar_style)

    ax.set_xticks(x_base + offsets.mean(), [str(s) for s in SAL_STATIC])
    ax.set_xlabel("Salinity (ppt)")
    ax.set_ylabel("Total biovolume (m³)")
    ax.set_axisbelow(True)
    ax.grid(axis="y", linewidth=0.5, alpha=0.4)

    patch_style = {"edgecolor": "black", "linewidth": 0.5}
    handles = [
        Patch(facecolor=pft_color_map[pft], label=f"PFT {pft}", **patch_style)
        for pft in PFTS
    ] + [
        Patch(facecolor="white", label="Community", **patch_style),
        Patch(facecolor="white", hatch=HATCH, label="Monoculture", **patch_style),
    ]
    ax.legend(handles=handles, loc="upper right")

    return fig


# =============================================================================
# Figures
# =============================================================================

_config.apply_style()
plt.rcParams["hatch.linewidth"] = 0.5

output_dir = ensure_dir(FIGURES_MAIN)

for version, prefix in VERSION_PREFIXES.items():
    fig = draw_figure(
        read_matrix(f"{prefix}comm_mat.csv"),
        read_matrix(f"{prefix}mono_mat.csv"),
    )
    _config.save_figure(
        fig,
        os.path.join(output_dir, f"fig2_community_vs_monoculture_{version}.png"),
    )
    plt.close(fig)
