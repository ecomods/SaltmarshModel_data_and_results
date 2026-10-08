"""
Shared figure style, sizes, scenario order and colours.

Figure scripts call apply_style() before plotting, set sizes with
figsize_mm() and save with save_figure(). The scenario and PFT order is also
used by 01_prepare_figure_data.py.
"""

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

# =============================================================================
# Figure sizes
# =============================================================================

MM_TO_INCH = 1 / 25.4

# Figure widths (mm) for a 160 mm text width.
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

    All text sizes are relative to base_size; scripts should not set absolute
    font sizes.
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
        # Opaque legend background without border.
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
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    print(f"Saved: {path}")


# =============================================================================
# Scenario and PFT order
# =============================================================================

SAL_STATIC = [35, 70, 105, 140]
SAL_DYN = [35, 70, 105]
PFTS = [1, 2, 3, 4]
VARIANT_LEVELS = ["V0", "V1", "V2"]

# =============================================================================
# Colors
# =============================================================================

# PFT colours: scico "batlow" (Crameri) at 0.10, 0.32, 0.54 and 0.76.
pft_color_map = {1: "#0f3c5f", 2: "#376b58", 3: "#95872c", 4: "#f49f72"}

# Salinity regimes (Figs. 4 and S2).
REGIME_LABELS = {"V0": "Static (V0)", "V1": "Seasonal (V1)", "V2": "Seasonal + tide (V2)"}
regime_color_map = {"V0": "black", "V1": "#8E44AD", "V2": "#E78AC3"}
REGIME_LINEWIDTH = 1.2

# Static salinities from light (low) to dark blue (high) (Figs. 1 and S1).
_blues = plt.get_cmap("Blues")
salinity_color_map = {
    sal: _blues(level) for sal, level in zip(SAL_STATIC, [0.35, 0.55, 0.75, 0.9])
}
