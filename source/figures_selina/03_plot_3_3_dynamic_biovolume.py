# -*- coding: utf-8 -*-

# =============================================================================
# SCRIPT OVERVIEW
# =============================================================================
# Purpose
# -------
# This script creates the dynamic biovolume figure. It compares V0, V1, and V2
# across the three salinity levels and four PFTs. The left part of the figure shows
# time series, and the right column shows stacked total biovolume bars.
#
# Figure layout
# -------------
# Rows correspond to salinity levels (35, 70, 105 ppt). Columns 1-4 correspond to
# PFT 1-4. The final column shows total stacked PFT contributions for V0/V1/V2.
#
# Output
# ------
# The figure is written directly to figures/main/ as PNG and PDF.
# =============================================================================

"""
Figure 3.3:
Dynamic total biovolume time-series grid.

Rows: salinity scenarios (35, 70, 105 ppt)
Columns: PFT 1-4 time series plus one stacked total barplot column
Lines: V0, V1, V2
Bars: total biovolume by PFT for V0, V1, V2

This script creates only the dynamic total biovolume figure and saves it
straight to figures/main/.

Outputs:
- figures/main/plot_3_3_dynamic_biovolume.png
- figures/main/plot_3_3_dynamic_biovolume.pdf

"""

import os
import numpy as np
import pandas as pd
import importlib

import matplotlib.pyplot as plt
from matplotlib.patches import Patch

_config = importlib.import_module("03_figure_config")
_utils = importlib.import_module("03_figure_utils")

A4_W_IN = _config.A4_W_IN
A4_GRID_H_IN = _config.A4_GRID_H_IN
PFTS = _config.PFTS
VARIANT_LEVELS = _config.VARIANT_LEVELS
pft_color_map = _config.pft_color_map
DERIVED_DIR = _config.DERIVED_DIR
FIGURES_MAIN = _config.FIGURES_MAIN
ensure_dir = _utils.ensure_dir


# =============================================================================
# Paths and settings
# =============================================================================

output_dir = ensure_dir(FIGURES_MAIN)

OUT_PNG = os.path.join(output_dir, "plot_3_3_dynamic_biovolume.png")
OUT_PDF = os.path.join(output_dir, "plot_3_3_dynamic_biovolume.pdf")

sal_levels = [35, 70, 105]
variant_levels = VARIANT_LEVELS

variant_style = {
    "V0": {"color": "0.25", "linestyle": "--", "linewidth": 1.4},
    "V1": {"color": "#8c510a", "linestyle": "-", "linewidth": 1.6},
    "V2": {"color": "#2171b5", "linestyle": "-", "linewidth": 1.6},
}


# =============================================================================
# Input data
# =============================================================================

median_ts_total_volume = pd.read_csv(
    os.path.join(DERIVED_DIR, "median_ts_total_volume.csv")
)

summary_pft_tv = pd.read_csv(
    os.path.join(DERIVED_DIR, "summary_pft_tv.csv")
)


# =============================================================================
# Helper functions
# =============================================================================

def add_salinity_and_variant_columns(median_df):
    """
    Add salinity and variant columns from the version label.

    Expected version labels:
        35_V0, 35_V1, 35_V2, 70_V0, ..., 105_V2
    """
    dfm = median_df.copy()
    version = dfm["version"].astype(str)
    dfm["salinity"] = version.str.split("_").str[0].astype(int)
    dfm["variant"] = version.str.split("_").str[1]
    return dfm


def get_y_limits(median_df):
    """
    Determine shared y-limits from the time-series values.
    """
    vals = median_df["value"].to_numpy(dtype=float)
    vals = vals[np.isfinite(vals)]

    if len(vals) == 0:
        return 0.0, 1.0

    y_min = vals.min()
    y_max = vals.max()

    if y_max > y_min:
        pad = 0.05 * (y_max - y_min)
    else:
        pad = 1.0

    return y_min - pad, y_max + pad


def build_total_volume_lookup(summary_pft_tv):
    """
    Convert summary_pft_tv into a lookup dictionary:
        tv_lookup[(salinity, variant)][pft] = median total biovolume
    """
    tv_lookup = {}

    for (sal, var), sub in summary_pft_tv.groupby(["salinity", "variant"]):
        tv_lookup[(int(sal), str(var))] = {
            int(row["pft"]): float(row["median_value"])
            for _, row in sub.iterrows()
        }

    return tv_lookup


def add_variant_legend(fig, axes):
    """
    Add V0/V1/V2 line legend above the figure.
    """
    handles = []
    labels = []

    for var in variant_levels:
        h, = axes[0, 0].plot([], [], **variant_style[var])
        handles.append(h)
        labels.append(var)

    fig.legend(
        handles,
        labels,
        title="Variant",
        loc="upper center",
        ncol=3,
        frameon=True,
        fontsize=8,
        title_fontsize=8,
    )


def add_pft_legend(fig):
    """
    Add PFT color legend at the upper right.
    """
    pft_handles = [
        Patch(facecolor=pft_color_map[pft], edgecolor="black", label=f"PFT {pft}")
        for pft in PFTS
    ]

    fig.legend(
        handles=pft_handles,
        labels=[handle.get_label() for handle in pft_handles],
        loc="upper right",
        bbox_to_anchor=(1.01, 1),
        frameon=True,
        fontsize=8,
    )


# =============================================================================
# Plot
# =============================================================================

def plot_dynamic_biovolume():
    """
    Create the dynamic total biovolume figure.
    """
    y_lim = get_y_limits(median_ts_total_volume)
    dfm = add_salinity_and_variant_columns(median_ts_total_volume)
    tv_lookup = build_total_volume_lookup(summary_pft_tv)

    fig, axes = plt.subplots(
        nrows=len(sal_levels),
        ncols=len(PFTS) + 1,
        figsize=(A4_W_IN, A4_GRID_H_IN),
        sharex=False,
        sharey=False,
        gridspec_kw={"width_ratios": [1, 1, 1, 1, 1.05]},
    )

    # -------------------------------------------------------------------------
    # Time-series panels: columns 0..3
    # -------------------------------------------------------------------------

    for row_i, sal in enumerate(sal_levels):
        for col_i, pft in enumerate(PFTS):
            ax = axes[row_i, col_i]

            for var in variant_levels:
                sub = dfm[
                    (dfm["salinity"] == sal) &
                    (dfm["pft"] == pft) &
                    (dfm["variant"] == var)
                ].sort_values("time_days")

                if sub.empty:
                    continue

                ax.plot(
                    sub["time_days"],
                    sub["value"],
                    **variant_style[var],
                )

            if row_i == 0:
                ax.set_title(f"PFT {pft}", fontsize=9)

            if col_i == 0:
                ax.set_ylabel(f"{sal} ppt\nTotal Biovolume [m³]", fontsize=9)

            ax.grid(True, alpha=0.25)
            ax.tick_params(labelsize=7)
            ax.set_ylim(*y_lim)

    for ax in axes[-1, 0:4]:
        ax.set_xlabel("t [d]", fontsize=8)

    # -------------------------------------------------------------------------
    # Stacked total barplot column: column 4
    # -------------------------------------------------------------------------

    for row_i, sal in enumerate(sal_levels):
        axb = axes[row_i, 4]
        x = np.arange(len(variant_levels))
        bottom = np.zeros(len(variant_levels), dtype=float)

        for pft in PFTS:
            vals_bar = np.array(
                [float(tv_lookup.get((sal, var), {}).get(pft, 0.0)) for var in variant_levels],
                dtype=float,
            )

            axb.bar(
                x,
                vals_bar,
                bottom=bottom,
                color=pft_color_map[pft],
                edgecolor="black",
                linewidth=0.6,
            )

            bottom += vals_bar

        if row_i == 0:
            axb.set_title("Total", fontsize=9)

        axb.set_xticks(x)
        axb.set_xticklabels(variant_levels, rotation=0)
        axb.grid(axis="y", linestyle=":", linewidth=0.5, alpha=0.8)
        axb.set_axisbelow(True)
        axb.set_ylim(*y_lim)
        axb.tick_params(labelsize=7)
        axb.set_ylabel("")

        if row_i == len(sal_levels) - 1:
            axb.set_xlabel("Variant", fontsize=8)
        else:
            axb.set_xlabel("")

    add_variant_legend(fig, axes)
    add_pft_legend(fig)

    plt.tight_layout(rect=[0, 0, 1, 0.90])

    plt.savefig(OUT_PNG, bbox_inches="tight", dpi=300)
    plt.savefig(OUT_PDF, bbox_inches="tight")

    plt.show()
    plt.close(fig)


# =============================================================================
# Main
# =============================================================================

plot_dynamic_biovolume()

print("Done: plot_3_3_dynamic_biovolume")
print(f"Saved: {OUT_PNG}")
print(f"Saved: {OUT_PDF}")
