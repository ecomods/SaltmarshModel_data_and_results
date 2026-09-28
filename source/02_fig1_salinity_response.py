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
# figures/main/fig1_salinity_response.png
# =============================================================================

"""
Plot PFT-specific Forman/logistic salinity response curves.

The parameter values are read from data_model_input/species/Saltmarsh_*.py
so the figure is generated from the same parameter files used by the model setup.
"""

import importlib.util

import matplotlib.pyplot as plt
import numpy as np

import figure_config as _config
from source.utils.paths import FIGURES_MAIN, SPECIES_DIR


# =============================================================================
# Settings
# =============================================================================

OUT_DIR = FIGURES_MAIN
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_PNG = OUT_DIR / "fig1_salinity_response.png"

SALINITY_RANGE = np.linspace(0, 160, 1000)

# Static salinities of the simulations, marked by vertical reference lines.
SALINITY_LINES = _config.SAL_STATIC


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

    for pft in _config.PFTS:
        species_file = SPECIES_DIR / f"Saltmarsh_{pft}.py"

        if not species_file.is_file():
            raise FileNotFoundError(f"Missing species file: {species_file}")

        module = load_species_module(species_file)
        geometry, parameter = module.createPlant()

        pft_parameters[pft] = {
            "U_i": float(parameter["salt_effect_ui"]),
            "d": float(parameter["salt_effect_d"]),
        }

    return pft_parameters


def logistic_curve(salinity, u_i, d):
    """Calculate the Forman/logistic belowground salinity response."""
    return 1.0 / (1.0 + np.exp(d * (u_i - salinity)))


# =============================================================================
# Main
# =============================================================================

def main():
    _config.apply_style()

    pft_parameters = load_pft_parameters()

    fig, ax = plt.subplots(figsize=_config.figsize_mm(_config.WIDTH_HALF_MM, 60))

    for pft, params in pft_parameters.items():
        ax.plot(
            SALINITY_RANGE,
            logistic_curve(SALINITY_RANGE, params["U_i"], params["d"]),
            color=_config.pft_color_map[pft],
            label=f"PFT {pft}",
        )

    # Reference lines at the simulated salinities. The grid is horizontal only,
    # so these are the only vertical lines.
    for salinity in SALINITY_LINES:
        ax.axvline(salinity, color="0.45", linewidth=0.8, zorder=1)

    ax.set_xlabel("Salinity (ppt)")
    ax.set_ylabel(r"$f_{\mathrm{reslim\_bg,Forman}}$ (–)")

    ax.set_xlim(0, 160)
    ax.set_ylim(0.0, 1.0)
    ax.set_xticks(np.arange(0, 161, 20))

    ax.set_axisbelow(True)
    ax.grid(axis="y", linewidth=0.5, alpha=0.4)

    ax.legend(loc="upper right")

    _config.save_figure(fig, OUT_PNG)
    plt.close(fig)


if __name__ == "__main__":
    main()
