#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =============================================================================
# SCRIPT OVERVIEW
# =============================================================================
# Purpose
# -------
# This manuscript figure script visualizes the relationship between potential
# growth and maintenance costs as plant size increases. It is a conceptual check
# of the model formulation rather than a plot of simulation output.
#
# Figure role in the manuscript
# -----------------------------
# The figure helps explain why different salinity levels and maintenance costs can
# lead to different equilibrium plant sizes.
#
# Output
# ------
# The figure is written directly to figures/main/ as PNG and PDF.
# =============================================================================

"""
Plot maintenance costs and potential growth across aboveground height.

This script creates the conceptual figure showing:
- maintenance as a function of plant size
- growth_pot for different static porewater salinities
- equilibrium heights where maintenance and growth_pot intersect

The salinity response and maintenance factor are read from
Saltmarsh_4.py, i.e. the high-tolerance PFT used for this conceptual
single-plant illustration.

Outputs
-------
figures/main/plot_2_3_growth_pot_maint.png
figures/main/plot_2_3_growth_pot_maint.pdf
"""

import importlib.util

import matplotlib.pyplot as plt
import numpy as np


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
# Paths
# =============================================================================

OUT_DIR = FIGURES_MAIN
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_PNG = OUT_DIR / "plot_2_3_growth_pot_maint.png"
OUT_PDF = OUT_DIR / "plot_2_3_growth_pot_maint.pdf"


# =============================================================================
# Parameters
# =============================================================================

TIME = 86400.0       # [s], one day
P_SUN = 1361.0       # [J m-2 s-1]
P_WATER = 1.5        # [-]
P_GROW = 5e-9        # [m3 J-1]
P_RATIO_AG = 0.5     # r_ag = P_RATIO_AG * h_ag
P_RATIO_BG = 0.5     # r_bg = P_RATIO_BG * h_bg

SALINITIES = [35, 70, 105, 140]
H_AG_MIN = 0.0
H_AG_MAX = 1.85
N_POINTS = 1000


# =============================================================================
# Functions
# =============================================================================

def load_species_module(path):
    """Import a species file without requiring it to be on sys.path."""
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_reference_pft_parameters():
    """Load the high-tolerance PFT parameters from Saltmarsh_4.py."""
    species_file = SPECIES_DIR / "Saltmarsh_4.py"
    if not species_file.is_file():
        raise FileNotFoundError(f"Missing species file: {species_file}")

    module = load_species_module(species_file)
    geometry, parameter = module.createPlant()

    return {
        "p_maint": float(parameter["p_maint"]),
        "salt_effect_ui": float(parameter["salt_effect_ui"]),
        "salt_effect_d": float(parameter["salt_effect_d"]),
    }


def forman_response(salinity, u_i, d):
    """Calculate the Forman/logistic salinity response."""
    return 1.0 / (1.0 + np.exp(d * (u_i - salinity)))


def calculate_geometry(h_ag):
    """Calculate AG and BG cylinder geometry from aboveground height."""
    r_ag = P_RATIO_AG * h_ag
    h_bg = h_ag.copy()
    r_bg = P_RATIO_BG * h_bg

    v_ag = np.pi * r_ag**2 * h_ag
    v_bg = np.pi * r_bg**2 * h_bg
    volume = v_ag + v_bg

    return {
        "h_ag": h_ag,
        "r_ag": r_ag,
        "h_bg": h_bg,
        "r_bg": r_bg,
        "v_ag": v_ag,
        "v_bg": v_bg,
        "volume": volume,
    }


def calculate_maintenance(volume, p_maint):
    """Calculate maintenance costs."""
    return volume * p_maint * TIME


def calculate_growth_pot(geometry, salinity, u_i, d):
    """Calculate potential growth for a given salinity."""
    aboveground_factor = 1.0
    belowground_factor = forman_response(salinity, u_i=u_i, d=d)

    res_ag = (
        aboveground_factor
        * np.pi
        * geometry["r_ag"] ** 2
        * P_SUN
        * TIME
    )

    denominator = geometry["h_ag"] + 0.5 * geometry["h_bg"]
    denominator = np.where(denominator <= 0, np.nan, denominator)

    res_bg = (
        belowground_factor
        * geometry["v_bg"]
        * P_SUN
        * P_WATER
        * (1.0 / denominator)
        * TIME
    )

    res_eff = np.minimum(res_ag, res_bg)
    grow_pot = res_eff * P_GROW
    return np.nan_to_num(grow_pot, nan=0.0)


def find_intersection(x, y1, y2):
    """Find the first non-trivial intersection between y1 and y2."""
    diff = y1 - y2
    sign_change_idx = np.where(np.diff(np.sign(diff)) != 0)[0]
    sign_change_idx = [idx for idx in sign_change_idx if x[idx] > 0.01]

    if len(sign_change_idx) == 0:
        return None

    idx = sign_change_idx[0]
    x0, x1 = x[idx], x[idx + 1]
    y0, y1_diff = diff[idx], diff[idx + 1]

    if y1_diff == y0:
        x_intersection = x0
    else:
        x_intersection = x0 - y0 * (x1 - x0) / (y1_diff - y0)

    y_intersection = np.interp(x_intersection, x, y1)
    return x_intersection, y_intersection


def main():
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["DejaVu Sans", "Arial"],
            "font.size": 9,
            "axes.labelsize": 9,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 8,
            "axes.linewidth": 0.8,
        }
    )

    pft_parameters = load_reference_pft_parameters()
    p_maint = pft_parameters["p_maint"]
    u_i = pft_parameters["salt_effect_ui"]
    d = pft_parameters["salt_effect_d"]

    h_ag = np.linspace(H_AG_MIN, H_AG_MAX, N_POINTS)
    geometry = calculate_geometry(h_ag)
    maintenance = calculate_maintenance(geometry["volume"], p_maint=p_maint)

    growth_curves = {}
    intersections = {}

    for salinity in SALINITIES:
        growth_pot = calculate_growth_pot(
            geometry,
            salinity,
            u_i=u_i,
            d=d,
        )
        growth_curves[salinity] = growth_pot
        intersections[salinity] = find_intersection(h_ag, maintenance, growth_pot)

    fig, ax = plt.subplots(figsize=(7.5, 5.0))

    ax.plot(
        h_ag,
        maintenance,
        label=f"maintenance (mf={p_maint:.2e})",
        linestyle="-",
        linewidth=1.2,
    )

    for salinity in SALINITIES:
        ax.plot(
            h_ag,
            growth_curves[salinity],
            linestyle="--",
            linewidth=1.1,
            label=f"growth_pot (Sal={salinity} ppt)",
        )

    for salinity in SALINITIES:
        intersection = intersections[salinity]
        if intersection is None:
            continue

        x_int, y_int = intersection
        ax.scatter(x_int, y_int, color="black", s=25, zorder=5)
        ax.annotate(
            f"h_ag = {x_int:.2f} m",
            xy=(x_int, y_int),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8,
            bbox=dict(
                boxstyle="round,pad=0.2",
                fc="white",
                ec="gray",
                alpha=0.9,
            ),
        )

    ax.set_xlim(0.0, H_AG_MAX)
    ax.set_ylim(0.0, 0.7)
    ax.set_xlabel("Aboveground height [m]")
    ax.set_ylabel("Daily volume increment [m$^3$]")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="upper left", fontsize=8)

    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=300, bbox_inches="tight")
    fig.savefig(OUT_PDF, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved: {OUT_PNG}")
    print(f"Saved: {OUT_PDF}")


if __name__ == "__main__":
    main()
