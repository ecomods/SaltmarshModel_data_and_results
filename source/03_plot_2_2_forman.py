# -*- coding: utf-8 -*-

# =============================================================================
# SCRIPT OVERVIEW
# =============================================================================
# Purpose
# -------
# This manuscript figure script visualizes the PFT-specific Forman/logistic
# salinity response curves. It reads parameter values directly from the
# species files used by the model setup.
#
# Figure role in the manuscript
# -----------------------------
# This is a parameterization figure. It shows how the four PFTs differ in their
# belowground salinity limitation along the salinity gradient.
#
# Output
# ------
# The figure is written directly to figures/main/ as PNG and PDF.
# =============================================================================

"""
Plot PFT-specific Forman/logistic salinity response curves.

This script creates the conceptual parameterization figure showing:
- belowground salinity response curves for the four PFTs
- vertical reference lines for the simulated static salinity scenarios
- horizontal reference lines for PFT-specific maintenance costs

The parameter values are read from data_model_input/species/Saltmarsh_*.py
so the figure is generated from the same parameter files used by the model setup.

Outputs
-------
figures/main/plot_2_2_forman.png
figures/main/plot_2_2_forman.pdf
"""

import importlib.util

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import ScalarFormatter


# Allow this source/ script to be run directly with
#     python source/<script_name>.py
# as well as through run_analysis.py.
import sys
from pathlib import Path

REPO_ROOT_BOOTSTRAP = Path(__file__).resolve().parents[1]
if str(REPO_ROOT_BOOTSTRAP) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT_BOOTSTRAP))

from source.utils.paths import FIGURES_MAIN, SPECIES_DIR


# =============================================================================
# Settings
# =============================================================================

OUT_DIR = FIGURES_MAIN
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_PNG = OUT_DIR / "plot_2_2_forman.png"
OUT_PDF = OUT_DIR / "plot_2_2_forman.pdf"

U = np.linspace(0, 160, 1000)
SALINITY_LINES = [35, 70, 105, 140]
SALINITY_LABEL_COLORS = ["#c6dbef", "#9ecae1", "#6baed6", "#3182bd"]

PFT_COLORS = {
    1: "#0173b2",
    2: "#de8f05",
    3: "#029e73",
    4: "#d55e00",
}

PFT_LABELS = {
    1: "PFT 1: low cost / low tolerance",
    2: "PFT 2: high cost / medium tolerance",
    3: "PFT 3: low cost / medium tolerance",
    4: "PFT 4: high cost / high tolerance",
}


# =============================================================================
# Functions
# =============================================================================

def load_species_module(path):
    """Import a species file without requiring it to be on sys.path."""
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_pft_parameters():
    """Read salinity response and maintenance parameters from species files."""
    pft_parameters = {}

    for pft in [1, 2, 3, 4]:
        species_file = SPECIES_DIR / f"Saltmarsh_{pft}.py"
        if not species_file.is_file():
            raise FileNotFoundError(f"Missing species file: {species_file}")

        module = load_species_module(species_file)
        geometry, parameter = module.createPlant()

        pft_parameters[pft] = {
            "label": PFT_LABELS[pft],
            "U_i": float(parameter["salt_effect_ui"]),
            "d": float(parameter["salt_effect_d"]),
            "maintenance": float(parameter["p_maint"]),
            "color": PFT_COLORS[pft],
        }

    return pft_parameters


def logistic_curve(U, U_i, d):
    """Calculate the Forman/logistic salinity response."""
    return 1.0 / (1.0 + np.exp(d * (U_i - U)))


def main():
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["DejaVu Sans", "Arial"],
            "font.size": 10,
            "axes.labelsize": 10,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 8,
            "legend.title_fontsize": 9,
            "axes.linewidth": 0.8,
        }
    )

    pft_parameters = load_pft_parameters()

    fig, ax1 = plt.subplots(figsize=(10, 5.35))

    for pft, params in pft_parameters.items():
        y = logistic_curve(U, params["U_i"], params["d"])
        ax1.plot(
            U,
            y,
            color=params["color"],
            linewidth=1.1,
            label=params["label"],
        )

    for xpos, color in zip(SALINITY_LINES, SALINITY_LABEL_COLORS):
        ax1.axvline(
            x=xpos,
            color="deeppink",
            linestyle="--",
            linewidth=1.0,
            alpha=0.9,
        )
        ax1.text(
            xpos,
            1.012,
            f"{xpos} ppt",
            color=color,
            fontsize=6,
            ha="center",
            va="bottom",
            clip_on=False,
        )

    ax1.set_xlabel("Salinity [ppt]")
    ax1.set_ylabel("Belowground factor [-]")
    ax1.set_xlim(-8, 160)
    ax1.set_ylim(0.0, 1.0)
    ax1.set_xticks(np.arange(0, 161, 20))
    ax1.set_yticks(np.arange(0.0, 1.01, 0.2))
    ax1.grid(True, color="gray", alpha=0.35, linewidth=0.8)

    ax1.legend(
        title="PFT",
        loc="upper center",
        bbox_to_anchor=(0.5, 1.15),
        ncol=2,
        frameon=True,
        handlelength=2.0,
        columnspacing=1.4,
        borderaxespad=0.0,
    )

    ax2 = ax1.twinx()
    ax2.set_ylabel("Maintenance factor [s$^{-1}$]")

    maintenance_values = [params["maintenance"] for params in pft_parameters.values()]
    y_min = 1.0e-6
    y_max = 3.0e-6
    ax2.set_ylim(y_min, y_max)
    ax2.set_yticks(np.arange(y_min, y_max + 0.01e-6, 0.25e-6))

    formatter = ScalarFormatter(useMathText=True)
    formatter.set_scientific(True)
    formatter.set_powerlimits((-6, -6))
    ax2.yaxis.set_major_formatter(formatter)

    for pft, params in pft_parameters.items():
        ax2.axhline(
            y=params["maintenance"],
            color="black",
            linestyle="--",
            linewidth=0.7,
            alpha=0.65,
        )
        ax2.text(
            13,
            params["maintenance"] + 0.015e-6,
            params["label"],
            color=params["color"],
            fontsize=5,
            ha="left",
            va="bottom",
        )

    fig.subplots_adjust(left=0.10, right=0.78, bottom=0.14, top=0.85)
    fig.savefig(OUT_PNG, dpi=300, bbox_inches="tight")
    fig.savefig(OUT_PDF, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved: {OUT_PNG}")
    print(f"Saved: {OUT_PDF}")


if __name__ == "__main__":
    main()
