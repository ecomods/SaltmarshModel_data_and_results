#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =============================================================================
# SCRIPT OVERVIEW
# =============================================================================
# Purpose
# -------
# This manuscript figure script visualizes the relationship between potential
# growth and maintenance costs as plant size increases. The calculation is shown
# separately for each plant functional type (PFT).
#
# Figure role in the manuscript
# -----------------------------
# The figure illustrates how PFT-specific salinity tolerance and maintenance
# costs can lead to different size ranges at which potential growth and
# maintenance costs balance.
#
# Output
# ------
# The figure is written directly to figures/appendix/ as PNG and PDF.
# =============================================================================

"""
Plot potential growth and maintenance costs for all four PFTs.

Outputs
-------
figures/appendix/plot_appendix_1_growth_pot_maint.png
figures/appendix/plot_appendix_1_growth_pot_maint.pdf

The figure contains four panels arranged as a 2 x 2 grid:
- PFT 1
- PFT 2
- PFT 3
- PFT 4

Each panel shows:
- maintenance costs as a function of above-ground height
- potential growth for the static salinity scenarios
- intersection points where potential growth and maintenance costs balance

The PFT-specific parameters are read from:
data_model_input/species/Saltmarsh_1.py
data_model_input/species/Saltmarsh_2.py
data_model_input/species/Saltmarsh_3.py
data_model_input/species/Saltmarsh_4.py
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

from source.utils.paths import FIGURES_APPENDIX, SPECIES_DIR


# =============================================================================
# Paths
# =============================================================================

OUT_DIR = FIGURES_APPENDIX
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_PNG = OUT_DIR / "plot_appendix_1_growth_pot_maint.png"
OUT_PDF = OUT_DIR / "plot_appendix_1_growth_pot_maint.pdf"


# =============================================================================
# Settings
# =============================================================================

TIME = 86400.0
SALINITIES = [35, 70, 105, 140]

H_AG_MIN = 0.0
H_AG_MAX = 1.85
N_POINTS = 1000

PFTS = [1, 2, 3, 4]

PFT_LABELS = {
    1: "PFT 1",
    2: "PFT 2",
    3: "PFT 3",
    4: "PFT 4",
}

SALINITY_COLORS = {
    35: "#0173b2",
    70: "#de8f05",
    105: "#029e73",
    140: "#d55e00",
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


def load_pft_parameters(pft):
    """Read the parameters required for the conceptual growth calculation."""
    species_file = SPECIES_DIR / f"Saltmarsh_{pft}.py"

    if not species_file.is_file():
        raise FileNotFoundError(f"Missing species file: {species_file}")

    module = load_species_module(species_file)
    geometry, parameter = module.createPlant()

    return {
        "p_sun": float(parameter["p_sun"]),
        "p_water": float(parameter["p_water"]),
        "p_grow": float(parameter["p_grow"]),
        "p_maint": float(parameter["p_maint"]),
        "p_ratio_ag": float(parameter["p_ratio_ag"]),
        "p_ratio_bg": float(parameter["p_ratio_bg"]),
        "salt_effect_ui": float(parameter["salt_effect_ui"]),
        "salt_effect_d": float(parameter["salt_effect_d"]),
    }


def forman_response(salinity, u_i, d):
    """Calculate the Forman/logistic salinity response."""
    return 1.0 / (1.0 + np.exp(d * (u_i - salinity)))


def calculate_geometry(h_ag, p_ratio_ag, p_ratio_bg):
    """Calculate AG and BG cylinder geometry from above-ground height."""
    r_ag = p_ratio_ag * h_ag
    h_bg = h_ag.copy()
    r_bg = p_ratio_bg * h_bg

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
    """Calculate maintenance costs for one time step."""
    return volume * p_maint * TIME


def calculate_growth_pot(geometry, salinity, params):
    """Calculate potential growth for a given PFT and salinity."""
    aboveground_factor = 1.0

    belowground_factor = forman_response(
        salinity,
        u_i=params["salt_effect_ui"],
        d=params["salt_effect_d"],
    )

    res_ag = (
        aboveground_factor
        * np.pi
        * geometry["r_ag"] ** 2
        * params["p_sun"]
        * TIME
    )

    denominator = geometry["h_ag"] + 0.5 * geometry["h_bg"]
    denominator = np.where(denominator <= 0, np.nan, denominator)

    res_bg = (
        belowground_factor
        * geometry["v_bg"]
        * params["p_sun"]
        * params["p_water"]
        * (1.0 / denominator)
        * TIME
    )

    res_eff = np.minimum(res_ag, res_bg)
    grow_pot = res_eff * params["p_grow"]

    return np.nan_to_num(grow_pot, nan=0.0)


def find_intersection(x, y1, y2):
    """Find the first non-trivial intersection between two curves."""
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


def prepare_pft_data(pft, h_ag):
    """Calculate maintenance, potential growth, and intersections for one PFT."""
    params = load_pft_parameters(pft)

    geometry = calculate_geometry(
        h_ag,
        p_ratio_ag=params["p_ratio_ag"],
        p_ratio_bg=params["p_ratio_bg"],
    )

    maintenance = calculate_maintenance(
        geometry["volume"],
        p_maint=params["p_maint"],
    )

    growth_curves = {}
    intersections = {}

    for salinity in SALINITIES:
        growth_pot = calculate_growth_pot(
            geometry,
            salinity,
            params,
        )

        growth_curves[salinity] = growth_pot
        intersections[salinity] = find_intersection(
            h_ag,
            maintenance,
            growth_pot,
        )

    return {
        "params": params,
        "maintenance": maintenance,
        "growth_curves": growth_curves,
        "intersections": intersections,
    }


def set_common_style():
    """Apply consistent matplotlib settings for the manuscript figure."""
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


# =============================================================================
# Main
# =============================================================================

def main():
    set_common_style()

    h_ag = np.linspace(H_AG_MIN, H_AG_MAX, N_POINTS)

    pft_results = {
        pft: prepare_pft_data(pft, h_ag)
        for pft in PFTS
    }

    y_max = 0.0
    for result in pft_results.values():
        y_max = max(y_max, float(np.nanmax(result["maintenance"])))
        for curve in result["growth_curves"].values():
            y_max = max(y_max, float(np.nanmax(curve)))

    y_max = max(0.1, y_max * 1.08)

    fig, axes = plt.subplots(
        nrows=2,
        ncols=2,
        figsize=(8.0, 6.2),
        sharex=True,
        sharey=True,
    )

    axes_flat = axes.ravel()

    legend_handles = []
    legend_labels = []

    for ax, pft in zip(axes_flat, PFTS):
        result = pft_results[pft]
        params = result["params"]
        maintenance = result["maintenance"]
        growth_curves = result["growth_curves"]
        intersections = result["intersections"]

        maintenance_line, = ax.plot(
            h_ag,
            maintenance,
            color="black",
            linestyle="-",
            linewidth=1.2,
            label="maintenance",
        )

        if not legend_handles:
            legend_handles.append(maintenance_line)
            legend_labels.append("maintenance")

        for salinity in SALINITIES:
            growth_line, = ax.plot(
                h_ag,
                growth_curves[salinity],
                color=SALINITY_COLORS[salinity],
                linestyle="--",
                linewidth=1.1,
                label=f"growth_pot ({salinity} ppt)",
            )

            if pft == PFTS[0]:
                legend_handles.append(growth_line)
                legend_labels.append(f"growth_pot ({salinity} ppt)")

        for salinity in SALINITIES:
            intersection = intersections[salinity]

            if intersection is None:
                continue

            x_int, y_int = intersection

            ax.scatter(
                x_int,
                y_int,
                color="black",
                s=16,
                zorder=5,
            )

            ax.annotate(
                f"{x_int:.2f} m",
                xy=(x_int, y_int),
                xytext=(4, 4),
                textcoords="offset points",
                fontsize=6,
                bbox=dict(
                    boxstyle="round,pad=0.15",
                    fc="white",
                    ec="gray",
                    alpha=0.85,
                ),
            )

        ax.set_title(
            f"{PFT_LABELS[pft]} (mf={params['p_maint']:.2e})",
            fontsize=9,
        )

        ax.set_xlim(0.0, H_AG_MAX)
        ax.set_ylim(0.0, y_max)
        ax.grid(True, alpha=0.25)

    axes[1, 0].set_xlabel("Above-ground height [m]")
    axes[1, 1].set_xlabel("Above-ground height [m]")
    axes[0, 0].set_ylabel("Daily volume increment [m$^3$]")
    axes[1, 0].set_ylabel("Daily volume increment [m$^3$]")

    fig.legend(
        legend_handles,
        legend_labels,
        loc="lower center",
        ncol=3,
        frameon=True,
        bbox_to_anchor=(0.5, 0.01),
    )

    fig.tight_layout(rect=[0.0, 0.08, 1.0, 1.0])

    fig.savefig(OUT_PNG, dpi=300, bbox_inches="tight")
    fig.savefig(OUT_PDF, bbox_inches="tight")

    plt.close(fig)

    print(f"Saved: {OUT_PNG}")
    print(f"Saved: {OUT_PDF}")


if __name__ == "__main__":
    main()
