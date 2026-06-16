# -*- coding: utf-8 -*-
"""
Reusable helper functions for data preparation and figure generation.

The helper functions fall into three groups:

1. Small IO helpers such as ensure_dir().
2. Input-table preparation functions for processed community/monoculture data.
3. Summary functions used to create derived figure tables and error bars.
"""

import os

import importlib

import pandas as pd

# Files with numeric prefixes are loaded via importlib because they cannot be
# imported with standard from-import syntax.
_config = importlib.import_module("03_figure_config")
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
    Load processed static community data and apply manuscript filters.

    Expected input: data/community/static/data.csv
    Returned rows: community setup only (pfts == 'all'), seedling-filtered,
    static salinities 35/70/105/140, PFTs 1-4.
    """
    df = pd.read_csv(path)
    df = df[df["pfts"] == "all"].copy()
    df = df[df["age"] >= 864000].copy()
    df["pft"] = normalize_pft_to_int(df["pft"])
    df["n"] = df["n"].astype(int)
    df = df[df["pft"].isin(PFTS) & df["salinity"].isin(SAL_STATIC)].copy()
    return df


def prep_static_mono_df(path):
    """
    Load processed static monoculture data and apply manuscript filters.

    Expected input: data/monoculture/static/data.csv
    In monoculture data, the setup PFT is stored in pfts. This value is copied
    to pft so the plotting code can use the same column name throughout.
    """
    df = pd.read_csv(path)
    df = df[df["age"] >= 864000].copy()
    df["pft"] = normalize_pft_to_int(df["pfts"])
    df["n"] = df["n"].astype(int)
    df = df[df["pft"].isin(PFTS) & df["salinity"].isin(SAL_STATIC)].copy()
    return df


def prep_dynamic_comm_df(path):
    """
    Load processed dynamic community data and apply manuscript filters.

    Expected input: data/community/dynamic/data.csv
    Only community rows, PFTs 1-4 and salinities 35/70/105 are retained.
    """
    df = pd.read_csv(path)
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


def grouped_over_time_medians(df, keys_prefix):
    """
    Create replicate-level medians over time for PFTs and the whole community.

    This is used for error-bar figures. The returned data are still replicate-
    level summaries; summary_minmax() then calculates median and
    25th/75th percentiles across replicates.
    """
    dfc = df.copy()
    dfc["volume_per_plant"] = dfc["volume"]

    plant_counts_pft = (
        dfc.groupby(keys_prefix + ["pft", "n", "time"])
        .size()
        .reset_index(name="num_plants")
    )
    dfc = dfc.merge(plant_counts_pft, on=keys_prefix + ["pft", "n", "time"], how="left")

    per_ts_total_pft = (
        dfc.groupby(keys_prefix + ["pft", "n", "time"])["volume"]
        .sum()
        .reset_index(name="total_volume")
    )

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


def grouped_over_time_means(df, keys_prefix):
    """
    Create replicate-level means over time for PFTs and the whole community.

    This is used for mean-based error-bar figures. The returned data are still
    replicate-level summaries; summary_mean_std() can calculate mean and
    standard deviation across replicates.
    """
    dfc = df.copy()
    dfc["volume_per_plant"] = dfc["volume"]

    plant_counts_pft = (
        dfc.groupby(keys_prefix + ["pft", "n", "time"])
        .size()
        .reset_index(name="num_plants")
    )
    dfc = dfc.merge(plant_counts_pft, on=keys_prefix + ["pft", "n", "time"], how="left")

    per_ts_total_pft = (
        dfc.groupby(keys_prefix + ["pft", "n", "time"])["volume"]
        .sum()
        .reset_index(name="total_volume")
    )

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
