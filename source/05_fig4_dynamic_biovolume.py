"""
Figure 4: community biovolume under static and dynamic salinity.

Rows are the mean salinities 35, 70 and 105 ppt. Columns 1-4 show the total
biovolume of each PFT in years 5-10 for the three salinity regimes (static
V0, seasonal V1, seasonal + tide V2). The last column shows the time mean per
regime, stacked by PFT. Lines and bars are means of the ten replicates.

Input:  data/ts_total_volume.csv, summary_pft_tv.csv
Output: figures/main/fig4_dynamic_biovolume.png
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

import figure_config as config
import figure_utils as utils
from paths import DATA, FIGURES_MAIN

OUT_PNG = FIGURES_MAIN / "fig4_dynamic_biovolume.png"

PFTS = config.PFTS
SALINITIES = config.SAL_DYN
VARIANTS = config.VARIANT_LEVELS

# Regime colours and display names are shared with Fig. S2 (figure_config);
# data keys stay V0/V1/V2.
variant_style = {
    var: {"color": color, "linestyle": "-", "linewidth": config.REGIME_LINEWIDTH}
    for var, color in config.regime_color_map.items()
}

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
        Patch(facecolor=config.pft_color_map[pft], edgecolor="none", label=f"PFT {pft}")
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
        Line2D([], [], label=config.REGIME_LABELS[var], **variant_style[var])
        for var in VARIANTS
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

def draw_figure(ts_total_volume, summary_pft_tv):
    """Draw the time series and stacked bars and return the figure."""
    dfm = add_salinity_and_variant_columns(ts_total_volume)
    dfm["time_years"] = dfm["time_days"] / DAYS_PER_YEAR
    tv_lookup = build_total_volume_lookup(summary_pft_tv)
    bar_totals = [sum(by_pft.values()) for by_pft in tv_lookup.values()]
    y_lim = get_y_limits(ts_total_volume, bar_totals)

    fig, axes = plt.subplots(
        nrows=len(SALINITIES),
        ncols=len(PFTS) + 1,
        figsize=config.figsize_mm(config.WIDTH_FULL_MM, 135),
        sharey=True,
        gridspec_kw={"width_ratios": [1, 1, 1, 1, 1.05]},
    )

    # Time series of each PFT (columns 0-3).
    for row_i, sal in enumerate(SALINITIES):
        for col_i, pft in enumerate(PFTS):
            ax = axes[row_i, col_i]

            for var in VARIANTS:
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

    # Time mean per regime, stacked by PFT (column 4).
    for row_i, sal in enumerate(SALINITIES):
        axb = axes[row_i, 4]
        x = np.arange(len(VARIANTS))
        bottom = np.zeros(len(VARIANTS), dtype=float)

        for pft in PFTS:
            vals_bar = np.array(
                [float(tv_lookup.get((sal, var), {}).get(pft, 0.0)) for var in VARIANTS],
                dtype=float,
            )
            axb.bar(x, vals_bar, bottom=bottom, color=config.pft_color_map[pft], linewidth=0)
            bottom += vals_bar

        if row_i == 0:
            axb.set_title("Total")

        # Tilted labels: the column is too narrow for horizontal names.
        axb.set_xticks(
            x, [config.REGIME_LABELS[var] for var in VARIANTS],
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
    utils.center_label_under(fig, axes[-1, :len(PFTS)], "Time (years)")
    add_variant_legend(fig, pft_legend)

    return fig


def main():
    config.apply_style()
    fig = draw_figure(
        pd.read_csv(DATA / "ts_total_volume.csv"),
        pd.read_csv(DATA / "summary_pft_tv.csv"),
    )
    config.save_figure(fig, OUT_PNG)
    plt.close(fig)


if __name__ == "__main__":
    main()
