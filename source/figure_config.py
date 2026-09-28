# -*- coding: utf-8 -*-
"""
Shared configuration for manuscript figure scripts.

This module contains shared constants used by the figure and data-preparation
pipeline. Keeping this file small makes it clear which constants define the
manuscript figures.

Figure scripts call apply_style() before plotting, create figures with
figsize_mm() and save them with save_figure().

Used by:
    - source/01_prepare_figure_data.py
    - source/figure_utils.py
    - source/03_fig2_community_vs_monoculture.py
    - source/04_fig3_community_structure.py
    - source/05_fig4_dynamic_biovolume.py
    - source/08_figS3_monoculture_structure.py

The model-input and parameterization figures use source.utils.paths directly
because they are based on model-input files rather than processed model outputs.
"""

import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.colors import to_rgb


# Add the repository root to sys.path so this module works when executed
# directly and when called through run_analysis.py.
import sys
from pathlib import Path

REPO_ROOT_BOOTSTRAP = Path(__file__).resolve().parents[1]
if str(REPO_ROOT_BOOTSTRAP) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT_BOOTSTRAP))

from source.utils.paths import (
    DERIVED_FIGURE_DATA,
    FIGURES_APPENDIX,
    FIGURES_MAIN,
)

# =============================================================================
# Figure sizes
# =============================================================================

MM_TO_INCH = 1 / 25.4

# Compact manuscript figure size. Some multi-panel figures scale these values.
FIG_W = 85 * MM_TO_INCH
FIG_H = 60 * MM_TO_INCH

# A4-based dimensions for the large dynamic biovolume figure.
A4_W_IN = 210 * MM_TO_INCH
A4_GRID_H_IN = 170 * MM_TO_INCH

# Figure widths for an A4 document with about 160 mm text width. Figures are
# drawn at these sizes so that font sizes are the same in every figure.
WIDTH_HALF_MM = 80
WIDTH_MEDIUM_MM = 120
WIDTH_FULL_MM = 160


def figsize_mm(width_mm, height_mm):
    """Return a Matplotlib figsize tuple in inches from millimetres."""
    return (width_mm * MM_TO_INCH, height_mm * MM_TO_INCH)


# =============================================================================
# Global Matplotlib style
# =============================================================================

def apply_style(base_size=8):
    """
    Apply the shared manuscript figure style.

    All text sizes are relative to base_size, so changing it scales all text
    together. Figures use constrained layout, so they keep their exact size
    and labels are not cut off. Scripts should not set absolute font sizes.

    Axes, ticks and text are thin and dark grey, without top and right axis
    lines, so that the data stand out.
    """
    small_size = base_size * 7 / 8
    text_color = "0.15"
    axes_color = "0.35"

    mpl.rcdefaults()
    plt.rcParams.update({
        "font.size": base_size,
        "axes.titlesize": "medium",
        "xtick.labelsize": small_size,
        "ytick.labelsize": small_size,
        "legend.fontsize": small_size,
        "legend.title_fontsize": small_size,
        "text.color": text_color,
        "axes.labelcolor": text_color,
        "xtick.labelcolor": text_color,
        "ytick.labelcolor": text_color,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.6,
        "axes.edgecolor": axes_color,
        "xtick.color": axes_color,
        "ytick.color": axes_color,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "xtick.major.size": 3,
        "ytick.major.size": 3,
        # White legend background without border, so gridlines do not show
        # through the legend.
        "legend.edgecolor": "none",
        "legend.framealpha": 1,
        "figure.constrained_layout.use": True,
        "savefig.dpi": 600,
    })


def add_panel_labels(axes, labels="abcdefghijklmnopqrstuvwxyz"):
    """Label panels a), b), ... in bold at the top left of each axis."""
    for ax, label in zip(axes, labels):
        ax.set_title(f"{label})", loc="left", fontweight="bold")


def save_figure(fig, path):
    """Save a figure at its exact size, without trimming or padding."""
    fig.savefig(path)
    print(f"Saved: {path}")


# Previous style, still used by the result scripts that do not yet call
# apply_style(). Remove once all figure scripts use apply_style().
plt.rcParams.update({
    "font.size": 8,
    "axes.labelsize": 8,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "legend.fontsize": 7,
    "axes.linewidth": 0.8,
})

# =============================================================================
# Scenario and PFT order
# =============================================================================

SAL_STATIC = [35, 70, 105, 140]
SAL_DYN = [35, 70, 105]
PFTS = [1, 2, 3, 4]
VARIANT_LEVELS = ["V0", "V1", "V2"]

# =============================================================================
# Shared paths
# =============================================================================

DERIVED_DIR = DERIVED_FIGURE_DATA

# =============================================================================
# Colors
# =============================================================================

# Colorblind-friendly palette used consistently for PFT 1-4.
palette = sns.color_palette("colorblind", 4)
pft_color_map = {pft: palette[i] for i, pft in enumerate(PFTS)}


def pale(color, strength=0.45):
    """
    Opaque mix of a colour with white; strength 1 = original colour.

    Used for monocultures where they appear next to community results in full
    colour (Fig. 2).
    """
    return tuple(1 - strength * (1 - c) for c in to_rgb(color))

# Salinity regimes (static V0, seasonal V1, seasonal + tide V2): display names
# and line colours outside the PFT palette, shared by Figs. 4 and S2. The two
# dynamic regimes stay distinguishable with red-green colour blindness.
REGIME_LABELS = {"V0": "Static", "V1": "Seasonal", "V2": "Seasonal + tide"}
regime_color_map = {"V0": "#808080", "V1": "black", "V2": "#6a3d9a"}

# Ordered blue scale for salinity levels (light = low, dark = high), shared by
# the figures that colour lines by salinity (Figs. S1 and S2). The darkest
# shade stays distinguishable from black.
_blues = plt.get_cmap("Blues")
salinity_color_map = {
    sal: _blues(level) for sal, level in zip(SAL_STATIC, [0.35, 0.55, 0.75, 0.9])
}
