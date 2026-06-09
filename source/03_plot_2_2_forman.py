# -*- coding: utf-8 -*-

# =============================================================================
# SCRIPT OVERVIEW
# =============================================================================
# Purpose
# -------
# This script visualizes the PFT-specific Forman/logistic salinity response
# curves. Parameter values are read directly from the species files used by the
# model setup.
#
# Figure role in the manuscript
# -----------------------------
# The figure shows how the four PFTs differ in their belowground salinity
# limitation along the salinity gradient.
#
# Output
# ------
# figures/main/plot_2_2_forman.png
# figures/main/plot_2_2_forman.pdf
# =============================================================================

"""
Plot PFT-specific Forman/logistic salinity response curves.

The parameter values are read from data_model_input/species/Saltmarsh_*.py
so the figure is generated from the same parameter files used by the model setup.
"""

import importlib.util
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


# Allow this source/ script to be run directly with
#     python source/<script_name>.py
# as well as through run_analysis.py.
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

SALINITY_RANGE = np.linspace(0, 160, 1000)

SALINITY_LINES = [35, 70, 105, 140]
SALINITY_LABEL_COLORS = {
    35: "#c6dbef",
    70: "#9ecae1",
    105: "#6baed6",
    140: "#3182bd",
}

PFT_COLORS = {
    1: "#0173b2",
    2: "#de8f05",
    3: "#029e73",
    4: "#d55e00",
}

PFT_LABELS = {
    1: "PFT 1",
    2: "PFT 2",
    3: "PFT 3",
    4: "PFT 4",
}


# =============================================================================
# Functions
# =============================================================================

def load_species_module(path):
    """Import a species file from an explicit file path."""
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_pft_parameters():
    """Read salinity response parameters from the four species files."""
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
            "color": PFT_COLORS[pft],
        }

    return pft_parameters


def logistic_curve(salinity, u_i, d):
    """Calculate the Forman/logistic belowground salinity response."""
    return 1.0 / (1.0 + np.exp(d * (u_i - salinity)))


# =============================================================================
# Main
# =============================================================================

def main():
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["DejaVu Sans", "Arial"],
            "font.size": 11,
            "axes.labelsize": 12,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "legend.fontsize": 10,
            "axes.linewidth": 1.0,
        }
    )

    pft_parameters = load_pft_parameters()

    fig, ax = plt.subplots(figsize=(5.8, 4.4))

    for pft, params in pft_parameters.items():
        belowground_factor = logistic_curve(
            SALINITY_RANGE,
            params["U_i"],
            params["d"],
        )

        ax.plot(
            SALINITY_RANGE,
            belowground_factor,
            color=params["color"],
            linewidth=1.4,
            label=params["label"],
        )

    for salinity in SALINITY_LINES:
        ax.axvline(
            x=salinity,
            color="deeppink",
            linestyle="--",
            linewidth=1.0,
            alpha=0.9,
        )

        ax.text(
            salinity,
            1.02,
            f"{salinity} ppt",
            color=SALINITY_LABEL_COLORS[salinity],
            fontsize=12,
            ha="center",
            va="bottom",
            clip_on=False,
        )

    ax.set_xlabel("Salinity [ppt]")
    ax.set_ylabel("Belowground Factor [-]")

    ax.set_xlim(-8, 160)
    ax.set_ylim(0.0, 1.0)

    ax.set_xticks(np.arange(0, 161, 20))
    ax.set_yticks(np.arange(0.0, 1.01, 0.2))

    ax.grid(
        True,
        color="gray",
        alpha=0.35,
        linewidth=0.8,
    )

    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.18),
        ncol=4,
        frameon=True,
        handlelength=2.2,
        columnspacing=1.8,
    )

    fig.tight_layout()

    fig.savefig(
        OUT_PNG,
        dpi=300,
        bbox_inches="tight",
    )

    fig.savefig(
        OUT_PDF,
        bbox_inches="tight",
    )

    plt.close(fig)

    print(f"Saved: {OUT_PNG}")
    print(f"Saved: {OUT_PDF}")


if __name__ == "__main__":
    main()
