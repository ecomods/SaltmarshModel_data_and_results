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
# The script reads comm_mat.csv and mono_mat.csv from data/derived_figure_data/.
# Those matrices are prepared by 03_main_prepare_figure_data.py and contain median
# total biovolume values for each salinity/PFT combination.
#
# Output
# ------
# The figure is written directly to figures/main/ as PNG and PDF.
# =============================================================================

"""
Figure 3.1:
Static salinity - community (stacked) vs monoculture (hatched)

This script creates the static community-vs-monoculture total biovolume figure.

Output:
    figures/main/plot_3_1_static_community_vs_mono_biovolume_tot.png
    figures/main/plot_3_1_static_community_vs_mono_biovolume_tot.pdf

"""

import os
import numpy as np
import pandas as pd
import importlib

import matplotlib.pyplot as plt
from matplotlib.patches import Patch

_config = importlib.import_module("03_figure_config")
_utils = importlib.import_module("03_figure_utils")

FIG_W = _config.FIG_W
FIG_H = _config.FIG_H
SAL_STATIC = _config.SAL_STATIC
PFTS = _config.PFTS
pft_color_map = _config.pft_color_map
DERIVED_DIR = _config.DERIVED_DIR
FIGURES_MAIN = _config.FIGURES_MAIN
ensure_dir = _utils.ensure_dir


# =============================================================================
# Paths
# =============================================================================

output_dir = ensure_dir(FIGURES_MAIN)

out_png = os.path.join(
    output_dir,
    "plot_3_1_static_community_vs_mono_biovolume_tot.png",
)
out_pdf = os.path.join(
    output_dir,
    "plot_3_1_static_community_vs_mono_biovolume_tot.pdf",
)


# =============================================================================
# Input data
# =============================================================================

comm_mat = pd.read_csv(
    os.path.join(DERIVED_DIR, "comm_mat.csv"),
    index_col=0,
)
mono_mat = pd.read_csv(
    os.path.join(DERIVED_DIR, "mono_mat.csv"),
    index_col=0,
)

comm_mat.index = comm_mat.index.astype(int)
mono_mat.index = mono_mat.index.astype(int)
comm_mat.columns = comm_mat.columns.astype(int)
mono_mat.columns = mono_mat.columns.astype(int)


# =============================================================================
# Figure
# =============================================================================

fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))

x_base = np.arange(len(SAL_STATIC))
bar_gap = 0.16
width = 0.13

# community + 4 monoculture bars
offsets = np.array([0, 1, 2, 3, 4]) * bar_gap

x_comm = x_base + offsets[0]
x_mono = {
    pft: x_base + offsets[i]
    for i, pft in enumerate(PFTS, start=1)
}


# =============================================================================
# Community stacked bars
# =============================================================================

bottom = np.zeros(len(SAL_STATIC), dtype=float)

for pft in PFTS:
    vals = comm_mat.loc[SAL_STATIC, pft].values

    ax.bar(
        x_comm,
        vals,
        width=width,
        bottom=bottom,
        color=pft_color_map[pft],
        edgecolor="black",
        linewidth=0.5,
        alpha=1.0,
    )

    bottom += vals


# =============================================================================
# Monoculture bars
# =============================================================================

for pft in PFTS:
    ax.bar(
        x_mono[pft],
        mono_mat.loc[SAL_STATIC, pft].values,
        width=width,
        color=pft_color_map[pft],
        edgecolor="black",
        linewidth=0.5,
        alpha=1.0,
        hatch="///",
    )


# =============================================================================
# Axes
# =============================================================================

ax.set_ylabel("Total biovolume [m³]")
ax.grid(axis="y", linestyle=":", linewidth=0.6, alpha=0.8)

group_center = x_base + offsets.mean()
ax.set_xticks(group_center)
ax.set_xticklabels([str(s) for s in SAL_STATIC])
ax.set_xlabel("Salinity [ppt]")


# =============================================================================
# Legend
# =============================================================================

pft_handles = [
    Patch(
        facecolor=pft_color_map[pft],
        edgecolor="black",
        label=f"PFT {pft}",
    )
    for pft in PFTS
]

setup_handles = [
    Patch(
        facecolor="white",
        edgecolor="black",
        label="community",
        hatch=None,
    ),
    Patch(
        facecolor="white",
        edgecolor="black",
        label="monoculture",
        hatch="///",
    ),
]

handles = pft_handles + setup_handles

ax.legend(
    handles=handles,
    labels=[h.get_label() for h in handles],
    bbox_to_anchor=(1, 1),
)


# =============================================================================
# Save
# =============================================================================

plt.tight_layout()

plt.savefig(out_png, dpi=600, bbox_inches="tight")
plt.savefig(out_pdf, bbox_inches="tight")

plt.show()
plt.close()

print("Done: plot_3_1_static_community_vs_mono")
print(f"Saved: {out_png}")
print(f"Saved: {out_pdf}")
