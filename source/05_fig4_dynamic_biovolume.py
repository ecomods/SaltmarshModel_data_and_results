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
# Rows correspond to salinity levels (35, 70, 105 ppt), labelled at the right.
# Columns 1-4 correspond to PFT 1-4. The final column shows total stacked PFT
# contributions for V0/V1/V2. All panels share one y-axis.
#
# Output
# ------
# The figure is written directly to figures/main/ as PNG.
# =============================================================================

"""
Manuscript Figure 4:
Dynamic total biovolume time-series grid.

Rows: salinity scenarios (35, 70, 105 ppt)
Columns: PFT 1-4 time series plus one stacked total barplot column
Lines: V0, V1, V2
Bars: total biovolume by PFT for V0, V1, V2

Lines and bars show means across the ten replicate simulations.

Output:
- figures/main/fig4_dynamic_biovolume.png

"""

import os
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

import figure_config as _config
import figure_utils as _utils

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

sal_levels = [35, 70, 105]
variant_levels = VARIANT_LEVELS

# Regime colours and display names are shared with Fig. S2 (figure_config);
# data keys stay V0/V1/V2.
variant_style = {
    var: {"color": color, "linestyle": "-", "linewidth": _config.REGIME_LINEWIDTH}
    for var, color in _config.regime_color_map.items()
}
VARIANT_LABELS = _config.REGIME_LABELS

DAYS_PER_YEAR = 365
YEAR_TICKS = [5, 6, 7, 8, 9, 10]


# =============================================================================
# Helper functions
# =============================================================================

def add_salinity_and_variant_columns(ts_df):
    """
    Add salinity and variant columns from the version label.

    Expected version labels:
        35_V0, 35_V1, 35_V2, 70_V0, ..., 105_V2
    """
    dfm = ts_df.copy()
    version = dfm["version"].astype(str)
    dfm["salinity"] = version.str.split("_").str[0].astype(int)
    dfm["variant"] = version.str.split("_").str[1]
    return dfm


def get_y_limits(ts_df, bar_totals):
    """
    Determine shared y-limits from the time-series values and the stacked
    bar totals, so that no bar is cut off.
    """
    vals = np.concatenate([
        ts_df["value"].to_numpy(dtype=float),
        np.asarray(bar_totals, dtype=float),
    ])
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
        tv_lookup[(salinity, variant)][pft] = mean total biovolume
    """
    tv_lookup = {}

    for (sal, var), sub in summary_pft_tv.groupby(["salinity", "variant"]):
        tv_lookup[(int(sal), str(var))] = {
            int(row["pft"]): float(row["mean_value"])
            for _, row in sub.iterrows()
        }

    return tv_lookup


def add_pft_legend(fig):
    """PFT colours in one column, above the figure at the top right."""
    pft_handles = [
        Patch(facecolor=pft_color_map[pft], edgecolor="none", label=f"PFT {pft}")
        for pft in PFTS
    ]
    return fig.legend(handles=pft_handles, loc="outside upper right")


def add_variant_legend(fig, pft_legend):
    """
    Salinity-regime lines in one column with a left-aligned header, placed at
    the top left, mirroring the PFT legend at the top right (same distance to
    the figure edge, same top). Call after the layout is frozen.
    """
    variant_handles = [
        Line2D([], [], label=VARIANT_LABELS[var], **variant_style[var])
        for var in variant_levels
    ]
    pft_box = pft_legend.get_window_extent().transformed(fig.transFigure.inverted())
    legend = fig.legend(
        handles=variant_handles,
        title="Salinity regime",
        loc="upper left",
        bbox_to_anchor=(1 - pft_box.x1, pft_box.y1),
        borderaxespad=0,
    )
    legend.set_alignment("left")


# =============================================================================
# Plot
# =============================================================================

def plot_dynamic_biovolume(ts_total_volume, summary_pft_tv, out_png):
    """
    Create the dynamic total biovolume figure.
    """
    dfm = add_salinity_and_variant_columns(ts_total_volume)
    dfm["time_years"] = dfm["time_days"] / DAYS_PER_YEAR
    tv_lookup = build_total_volume_lookup(summary_pft_tv)
    bar_totals = [sum(by_pft.values()) for by_pft in tv_lookup.values()]
    y_lim = get_y_limits(ts_total_volume, bar_totals)

    fig, axes = plt.subplots(
        nrows=len(sal_levels),
        ncols=len(PFTS) + 1,
        figsize=_config.figsize_mm(_config.WIDTH_FULL_MM, 135),
        sharey=True,
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
                ].sort_values("time_years")

                if sub.empty:
                    continue

                ax.plot(sub["time_years"], sub["value"], **variant_style[var])

            if row_i == 0:
                ax.set_title(f"PFT {pft}")

            ax.set_xticks(YEAR_TICKS)

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
            axb.bar(x, vals_bar, bottom=bottom, color=pft_color_map[pft], linewidth=0)
            bottom += vals_bar

        if row_i == 0:
            axb.set_title("Total")

        # Tilted labels: the column is too narrow for horizontal names.
        axb.set_xticks(
            x, [VARIANT_LABELS[var] for var in variant_levels],
            rotation=40, ha="right", rotation_mode="anchor",
        )

        # Salinity row label at the right edge.
        axb.yaxis.set_label_position("right")
        axb.set_ylabel(f"{sal} ppt", rotation=270, va="bottom")

    for ax in axes.ravel():
        ax.set_ylim(*y_lim)
        ax.set_axisbelow(True)
        ax.grid(axis="y", linewidth=0.5, alpha=0.4)

    # Tick marks and labels only on the outer panels (left column, bottom row).
    for ax in axes[:, 1:].ravel():
        ax.tick_params(axis="y", left=False)
    for ax in axes[:-1, :].ravel():
        ax.tick_params(axis="x", bottom=False, labelbottom=False)

    fig.supylabel("Total biovolume (m³)", fontsize="medium")
    pft_legend = add_pft_legend(fig)
    _utils.center_label_under(fig, axes[-1, :len(PFTS)], "Time (years)")
    add_variant_legend(fig, pft_legend)

    _config.save_figure(fig, out_png)
    plt.close(fig)


# =============================================================================
# Main
# =============================================================================

_config.apply_style()

plot_dynamic_biovolume(
    pd.read_csv(os.path.join(DERIVED_DIR, "ts_total_volume.csv")),
    pd.read_csv(os.path.join(DERIVED_DIR, "summary_pft_tv.csv")),
    os.path.join(output_dir, "fig4_dynamic_biovolume.png"),
)
