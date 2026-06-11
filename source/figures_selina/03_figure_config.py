# -*- coding: utf-8 -*-
"""
Shared configuration for manuscript figure scripts.

This module contains shared constants used by the figure and data-preparation
pipeline. Keeping this file small makes it clear which constants define the
manuscript figures.

Used by:
    - source/03_main_prepare_figure_data.py
    - source/03_figure_utils.py
    - source/03_plot_3_1_static_community_vs_mono.py
    - source/03_plot_3_2_static_community.py
    - source/03_plot_3_3_dynamic_biovolume.py
    - source/03_plot_appendix_1_static_monoculture.py

The parameterization figures plot_2_1, plot_2_2 and plot_2_3 use
source.utils.paths directly because they are based on model-input files rather
than processed model outputs.
"""

import matplotlib.pyplot as plt
import seaborn as sns


# Add the repository root to sys.path so this module works when executed
# directly and when called through run_analysis.py.
import sys
from pathlib import Path

REPO_ROOT_BOOTSTRAP = Path(__file__).resolve().parents[1]
if str(REPO_ROOT_BOOTSTRAP) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT_BOOTSTRAP))

from source.utils.paths import (
    COMMUNITY_DYNAMIC_DATA,
    COMMUNITY_STATIC_DATA,
    DERIVED_FIGURE_DATA,
    FIGURES_APPENDIX,
    FIGURES_MAIN,
    MONOCULTURE_STATIC_DATA,
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

# =============================================================================
# Global Matplotlib style
# =============================================================================

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

COMM_STATIC_PATH = COMMUNITY_STATIC_DATA
MONO_STATIC_PATH = MONOCULTURE_STATIC_DATA
DYNAMIC_PATH = COMMUNITY_DYNAMIC_DATA
DERIVED_DIR = DERIVED_FIGURE_DATA

# =============================================================================
# Colors
# =============================================================================

# Colorblind-friendly palette used consistently for PFT 1-4.
palette = sns.color_palette("colorblind", 4)
pft_color_map = {pft: palette[i] for i, pft in enumerate(PFTS)}
