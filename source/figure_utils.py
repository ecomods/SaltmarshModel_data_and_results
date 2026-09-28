# -*- coding: utf-8 -*-
"""
Reusable helper functions for data preparation and figure generation.

The helper functions fall into three groups:

1. Small IO helpers such as ensure_dir().
2. Input-table preparation functions for processed community/monoculture data.
3. Summary functions used to create derived figure tables and error bars.
4. Shared plotting functions used by several figure scripts.
"""

import os

import importlib

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Files with numeric prefixes are loaded via importlib because they cannot be
# imported with standard from-import syntax.
_config = importlib.import_module("figure_config")
PFTS = _config.PFTS
SAL_DYN = _config.SAL_DYN
SAL_STATIC = _config.SAL_STATIC


# =============================================================================
# Basic IO
# =============================================================================

def ensure_dir(path):
    """Create a directory if it does not exist and return the path object/string."""
    os.makedirs(path, exist_ok=True)
    return path


# =============================================================================
# Basic data normalization
# =============================================================================

def normalize_pft_to_int(series):
    """Convert PFT labels like 1, '1', '1.0', 'PFT_1' or 'Saltmarsh_1' to int."""
    return series.astype(str).str.extract(r"(\d+)")[0].astype(int)


# =============================================================================
# Input preparation
# =============================================================================

def prep_static_comm_df(path):
    """
    Apply manuscript filters to static community plant data.

    Input may be a DataFrame or a CSV path.
    Returned rows: community setup only (pfts == 'all'), seedling-filtered,
    static salinities 35/70/105/140, PFTs 1-4.
    """
    df = path if isinstance(path, pd.DataFrame) else pd.read_csv(path)
    df = df[df["pfts"] == "all"].copy()
    df = df[df["age"] >= 864000].copy()
    df["pft"] = normalize_pft_to_int(df["pft"])
    df["n"] = df["n"].astype(int)
    df = df[df["pft"].isin(PFTS) & df["salinity"].isin(SAL_STATIC)].copy()
    return df


def prep_static_mono_df(path):
    """
    Apply manuscript filters to static monoculture plant data.

    Input may be a DataFrame or a CSV path.
    In monoculture data, the setup PFT is stored in pfts. This value is copied
    to pft so the plotting code can use the same column name throughout.
    """
    df = path if isinstance(path, pd.DataFrame) else pd.read_csv(path)
    df = df[df["age"] >= 864000].copy()
    df["pft"] = normalize_pft_to_int(df["pfts"])
    df["n"] = df["n"].astype(int)
    df = df[df["pft"].isin(PFTS) & df["salinity"].isin(SAL_STATIC)].copy()
    return df


def prep_dynamic_comm_df(path):
    """
    Apply manuscript filters to dynamic community plant data.

    Input may be a DataFrame or a CSV path.
    Only community rows, PFTs 1-4 and salinities 35/70/105 are retained.
    """
    df = path if isinstance(path, pd.DataFrame) else pd.read_csv(path)
    if "pfts" in df.columns:
        df = df[df["pfts"] == "all"].copy()
    if "salinity" in df.columns:
        df["salinity"] = df["salinity"].replace(10, 105)
    df = df[df["salinity"].isin(SAL_DYN)].copy()
    df = df[df["age"] >= 864000].copy()
    df["pft"] = normalize_pft_to_int(df["pft"])
    df["n"] = df["n"].astype(int)
    return df


# =============================================================================
# Summary helpers
# =============================================================================

def replicate_median_over_time_totalvolume_by_pft(df, group_cols, pft_col="pft"):
    """
    Calculate median total biovolume per PFT across replicate time series.

    Calculation steps:
    1. Sum plant volume per timestep for each group/PFT/replicate.
    2. Take the median over time within each replicate.
    3. Take the median across replicate medians.
    """
    per_timestep = (
        df.groupby(group_cols + [pft_col, "n", "time"])["volume"]
        .sum()
        .reset_index(name="total_volume")
    )

    rep_median = (
        per_timestep.groupby(group_cols + [pft_col, "n"])["total_volume"]
        .median()
        .reset_index(name="rep_median_total_volume")
    )

    summary = (
        rep_median.groupby(group_cols + [pft_col])["rep_median_total_volume"]
        .median()
        .reset_index(name="value")
    )

    return summary


def replicate_mean_over_time_totalvolume_by_pft(df, group_cols, pft_col="pft"):
    """
    Calculate mean total biovolume per PFT across replicate time series.

    Calculation steps:
    1. Sum plant volume per timestep for each group/PFT/replicate.
    2. Take the mean over time within each replicate.
    3. Take the mean across replicate means.
    """
    per_timestep = (
        df.groupby(group_cols + [pft_col, "n", "time"])["volume"]
        .sum()
        .reset_index(name="total_volume")
    )

    rep_mean = (
        per_timestep.groupby(group_cols + [pft_col, "n"])["total_volume"]
        .mean()
        .reset_index(name="rep_mean_total_volume")
    )

    summary = (
        rep_mean.groupby(group_cols + [pft_col])["rep_mean_total_volume"]
        .mean()
        .reset_index(name="value")
    )

    return summary


def complete_grid(summary_df, sal_levels, pft_levels):
    """Return a complete salinity x PFT matrix, filling missing combinations with 0."""
    grid = (
        pd.MultiIndex.from_product([sal_levels, pft_levels], names=["salinity", "pft"])
        .to_frame(index=False)
        .merge(summary_df, on=["salinity", "pft"], how="left")
    )
    grid["value"] = grid["value"].fillna(0.0)
    return (
        grid.pivot(index="salinity", columns="pft", values="value")
        .reindex(sal_levels)[pft_levels]
    )


def grouped_over_time_medians(df, keys_prefix, per_timestep_total_pft=None):
    """
    Create replicate-level medians over time for PFTs and the whole community.

    This is used for error-bar figures. The returned data are still replicate-
    level summaries; summary_minmax() then calculates median and
    25th/75th percentiles across replicates.

    per_timestep_total_pft may contain the already summed PFT totals grouped
    by keys_prefix + ["pft", "n", "time"], with a total_volume column.
    """
    dfc = df.copy()
    dfc["volume_per_plant"] = dfc["volume"]

    plant_counts_pft = (
        dfc.groupby(keys_prefix + ["pft", "n", "time"])
        .size()
        .reset_index(name="num_plants")
    )
    dfc = dfc.merge(plant_counts_pft, on=keys_prefix + ["pft", "n", "time"], how="left")

    if per_timestep_total_pft is None:
        per_ts_total_pft = (
            dfc.groupby(keys_prefix + ["pft", "n", "time"])["volume"]
            .sum()
            .reset_index(name="total_volume")
        )
    else:
        per_ts_total_pft = per_timestep_total_pft

    per_ts_other_pft = (
        dfc.groupby(keys_prefix + ["pft", "n", "time"])
        .agg({
            "volume_per_plant": "median",
            "h_ag": "median",
            "ag_bg_ratio": "median",
            "num_plants": "max",
        })
        .reset_index()
    )

    per_ts_pft = per_ts_total_pft.merge(
        per_ts_other_pft,
        on=keys_prefix + ["pft", "n", "time"],
        how="left",
    )

    grouped_pft = (
        per_ts_pft.groupby(keys_prefix + ["pft", "n"])
        .agg({
            "total_volume": "median",
            "volume_per_plant": "median",
            "h_ag": "median",
            "ag_bg_ratio": "median",
            "num_plants": "median",
        })
        .reset_index()
    )

    plant_counts_all = (
        dfc.groupby(keys_prefix + ["n", "time"])
        .size()
        .reset_index(name="num_plants")
    )
    per_ts_total_all = (
        dfc.groupby(keys_prefix + ["n", "time"])["volume"]
        .sum()
        .reset_index(name="total_volume")
    )
    per_ts_other_all = (
        dfc.groupby(keys_prefix + ["n", "time"])
        .agg({
            "volume_per_plant": "median",
            "h_ag": "median",
            "ag_bg_ratio": "median",
        })
        .reset_index()
    )

    per_ts_all = (
        per_ts_total_all
        .merge(per_ts_other_all, on=keys_prefix + ["n", "time"], how="left")
        .merge(plant_counts_all, on=keys_prefix + ["n", "time"], how="left")
    )

    grouped_all = (
        per_ts_all.groupby(keys_prefix + ["n"])
        .agg({
            "total_volume": "median",
            "volume_per_plant": "median",
            "h_ag": "median",
            "ag_bg_ratio": "median",
            "num_plants": "median",
        })
        .reset_index()
    )
    grouped_all["pft"] = 0

    return grouped_pft, grouped_all


def grouped_over_time_means(df, keys_prefix, per_timestep_total_pft=None):
    """
    Create replicate-level means over time for PFTs and the whole community.

    This is used for mean-based error-bar figures. The returned data are still
    replicate-level summaries; summary_mean_std() can calculate mean and
    standard deviation across replicates.

    per_timestep_total_pft has the same grouping and columns as in the median
    helper, so callers can reuse the same totals for both summaries.
    """
    dfc = df.copy()
    dfc["volume_per_plant"] = dfc["volume"]

    plant_counts_pft = (
        dfc.groupby(keys_prefix + ["pft", "n", "time"])
        .size()
        .reset_index(name="num_plants")
    )
    dfc = dfc.merge(plant_counts_pft, on=keys_prefix + ["pft", "n", "time"], how="left")

    if per_timestep_total_pft is None:
        per_ts_total_pft = (
            dfc.groupby(keys_prefix + ["pft", "n", "time"])["volume"]
            .sum()
            .reset_index(name="total_volume")
        )
    else:
        per_ts_total_pft = per_timestep_total_pft

    per_ts_other_pft = (
        dfc.groupby(keys_prefix + ["pft", "n", "time"])
        .agg({
            "volume_per_plant": "mean",
            "h_ag": "mean",
            "ag_bg_ratio": "mean",
            "num_plants": "max",
        })
        .reset_index()
    )

    per_ts_pft = per_ts_total_pft.merge(
        per_ts_other_pft,
        on=keys_prefix + ["pft", "n", "time"],
        how="left",
    )

    grouped_pft = (
        per_ts_pft.groupby(keys_prefix + ["pft", "n"])
        .agg({
            "total_volume": "mean",
            "volume_per_plant": "mean",
            "h_ag": "mean",
            "ag_bg_ratio": "mean",
            "num_plants": "mean",
        })
        .reset_index()
    )

    plant_counts_all = (
        dfc.groupby(keys_prefix + ["n", "time"])
        .size()
        .reset_index(name="num_plants")
    )
    per_ts_total_all = (
        dfc.groupby(keys_prefix + ["n", "time"])["volume"]
        .sum()
        .reset_index(name="total_volume")
    )
    per_ts_other_all = (
        dfc.groupby(keys_prefix + ["n", "time"])
        .agg({
            "volume_per_plant": "mean",
            "h_ag": "mean",
            "ag_bg_ratio": "mean",
        })
        .reset_index()
    )

    per_ts_all = (
        per_ts_total_all
        .merge(per_ts_other_all, on=keys_prefix + ["n", "time"], how="left")
        .merge(plant_counts_all, on=keys_prefix + ["n", "time"], how="left")
    )

    grouped_all = (
        per_ts_all.groupby(keys_prefix + ["n"])
        .agg({
            "total_volume": "mean",
            "volume_per_plant": "mean",
            "h_ag": "mean",
            "ag_bg_ratio": "mean",
            "num_plants": "mean",
        })
        .reset_index()
    )
    grouped_all["pft"] = 0

    return grouped_pft, grouped_all


def summary_minmax(grouped_df, keys, metric):
    """
    Calculate the median and interquartile range for grouped replicate values.

    Returned columns:
        median_value, q25_value, q75_value, err_lower, err_upper

    The error bars are asymmetric and extend from the median to the 25th and
    75th percentiles.
    """
    summary = (
        grouped_df.groupby(keys)[metric]
        .agg(
            median_value="median",
            q25_value=lambda x: x.quantile(0.25),
            q75_value=lambda x: x.quantile(0.75),
        )
        .reset_index()
    )
    summary["err_lower"] = summary["median_value"] - summary["q25_value"]
    summary["err_upper"] = summary["q75_value"] - summary["median_value"]
    return summary


def summary_minmax_mean(grouped_df, keys, metric):
    """
    Calculate mean and min/max range for a metric within grouped data.

    Returned columns:
        mean_value, min_value, max_value, err_lower, err_upper
    """
    summary = (
        grouped_df.groupby(keys)[metric]
        .agg(mean_value="mean", min_value="min", max_value="max")
        .reset_index()
    )
    summary["err_lower"] = summary["mean_value"] - summary["min_value"]
    summary["err_upper"] = summary["max_value"] - summary["mean_value"]
    return summary



def summary_mean_std(grouped_df, keys, metric):
    """
    Calculate mean and standard deviation across replicate-level values.

    The input table must contain one value per replicate and scenario. The
    returned error bars are symmetric and represent one standard deviation
    across the available replicates.
    """
    summary = (
        grouped_df.groupby(keys)[metric]
        .agg(mean_value="mean", std_value="std")
        .reset_index()
    )
    summary["std_value"] = summary["std_value"].fillna(0.0)
    summary["err_lower"] = summary["std_value"]
    summary["err_upper"] = summary["std_value"]
    return summary

def median_ts(df, col):
    """Return median time series across replicates for one per-timestep metric."""
    return (
        df.groupby(["version", "pft", "time_days"], observed=True)[col]
        .median()
        .reset_index(name="value")
    )


def mean_ts(df, col):
    """Return mean time series across replicates for one per-timestep metric."""
    return (
        df.groupby(["version", "pft", "time_days"], observed=True)[col]
        .mean()
        .reset_index(name="value")
    )


# =============================================================================
# Shared plotting
# =============================================================================

def center_label_under(fig, axes_row, label):
    """
    Replace the x-axis labels of axes_row by one label centred below them.

    Must be called after all other layout elements exist: the figure is laid
    out once, then the layout is frozen so the space reserved for the
    (now hidden) axis labels is kept.
    """
    for ax in axes_row:
        ax.set_xlabel(label)
    fig.canvas.draw()
    fig.set_layout_engine("none")

    to_fig = fig.transFigure.inverted()
    y = to_fig.transform(axes_row[0].xaxis.label.get_window_extent())[:, 1].mean()
    x = (axes_row[0].get_position().x0 + axes_row[-1].get_position().x1) / 2
    for ax in axes_row:
        ax.xaxis.label.set_visible(False)
    fig.text(x, y, label, ha="center", va="center",
             fontsize=axes_row[0].xaxis.label.get_fontsize(),
             color=axes_row[0].xaxis.label.get_color())


def draw_structure_figure(summaries, salinity_levels, pft_levels, ylabels,
                          panel_order, show_community=True, group_spacing=3.8,
                          pft_colors=None):
    """
    Draw the 2 x 2 point/error-bar figure of plant-structure metrics
    (Figs. 3 and S3) in the shared style and return the figure.

    summaries maps each metric to (summary_pft, summary_all). Both tables have
    the columns salinity, value, err_lower and err_upper; summary_pft also has
    pft. summary_all is the community reference and is only used when
    show_community is True. Within each salinity group, points are placed in
    the order community (optional), PFT 1, ..., PFT 4. Salinity groups are
    separated only by a wider gap (group_spacing), not by lines. Panels are labelled
    a)-d) in panel_order; the legend sits in the top-right panel.
    pft_colors defaults to the shared PFT palette.
    """
    pft_color_map = pft_colors or _config.pft_color_map

    x_group = np.arange(len(salinity_levels)) * group_spacing
    sal_to_x = {sal: x_group[i] for i, sal in enumerate(salinity_levels)}

    n_series = len(pft_levels) + (1 if show_community else 0)
    within_offsets = np.array([0.0, 0.55, 1.10, 1.65, 2.20])[:n_series]
    first_pft_slot = 1 if show_community else 0

    group_centers = x_group + np.mean(within_offsets)

    def draw_series(ax, summary, x_offset, color, label):
        ax.errorbar(
            summary["salinity"].map(sal_to_x) + x_offset,
            summary["value"],
            yerr=[summary["err_lower"], summary["err_upper"]],
            fmt="o",
            markersize=4,
            capsize=2,
            linewidth=0.8,
            color=color,
            label=label,
        )

    fig, axes = plt.subplots(
        nrows=2,
        ncols=2,
        figsize=_config.figsize_mm(_config.WIDTH_FULL_MM, 110),
        sharex=True,
    )

    for i_panel, (ax, metric) in enumerate(zip(axes.ravel(), panel_order)):
        summary_pft, summary_all = summaries[metric]

        if show_community:
            draw_series(ax, summary_all, within_offsets[0], "black", "Community")

        for i, pft in enumerate(pft_levels, start=first_pft_slot):
            dfp = summary_pft[summary_pft["pft"] == pft]
            if dfp.empty:
                continue
            color = pft_color_map[int(pft)]
            draw_series(ax, dfp, within_offsets[i], color, f"PFT {int(pft)}")

        ax.set_xticks(group_centers, [str(int(s)) for s in salinity_levels])
        # Only the bottom row gets an x-axis label.
        if i_panel >= 2:
            ax.set_xlabel("Salinity (ppt)")
        ax.set_ylabel(ylabels[metric])

        ax.set_axisbelow(True)
        ax.grid(axis="y", linewidth=0.5, alpha=0.4)

    _config.add_panel_labels(axes.ravel())

    # Legend inside the top-right panel, using the handles drawn there.
    axes[0, 1].legend(loc="upper right")

    return fig
