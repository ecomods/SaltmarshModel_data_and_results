# -*- coding: utf-8 -*-
"""
Prepare derived figure data for the manuscript figures.

This script creates the compact summary tables required by the figure scripts.

Inputs:
    data/community/static/data.csv
    data/community/dynamic/data.csv
    data/monoculture/static/data.csv

Outputs in data/derived_figure_data/:
    df_comm_prepared.csv          -> 03_plot_3_2_static_community.py
    df_mono_prepared.csv          -> 03_plot_appendix_1_static_monoculture.py
    comm_mat.csv                  -> 03_plot_3_1_static_community_vs_mono.py
    mono_mat.csv                  -> 03_plot_3_1_static_community_vs_mono.py
    grouped_pft_static.csv        -> 03_plot_3_2_static_community.py
    grouped_all_static.csv        -> 03_plot_3_2_static_community.py
    summary_pft_tv.csv            -> 03_plot_3_3_dynamic_biovolume.py
    median_ts_total_volume.csv    -> 03_plot_3_3_dynamic_biovolume.py
"""

import os

import importlib

import pandas as pd

# Files with numeric prefixes are loaded via importlib because they cannot be
# imported with standard from-import syntax.
_config = importlib.import_module("03_figure_config")
_utils = importlib.import_module("03_figure_utils")

COMM_STATIC_PATH = _config.COMM_STATIC_PATH
DERIVED_DIR = _config.DERIVED_DIR
DYNAMIC_PATH = _config.DYNAMIC_PATH
MONO_STATIC_PATH = _config.MONO_STATIC_PATH
PFTS = _config.PFTS
SAL_DYN = _config.SAL_DYN
SAL_STATIC = _config.SAL_STATIC
VARIANT_LEVELS = _config.VARIANT_LEVELS

complete_grid = _utils.complete_grid
ensure_dir = _utils.ensure_dir
grouped_over_time_medians = _utils.grouped_over_time_medians
median_ts = _utils.median_ts
normalize_pft_to_int = _utils.normalize_pft_to_int
prep_dynamic_comm_df = _utils.prep_dynamic_comm_df
prep_static_comm_df = _utils.prep_static_comm_df
prep_static_mono_df = _utils.prep_static_mono_df
replicate_median_over_time_totalvolume_by_pft = _utils.replicate_median_over_time_totalvolume_by_pft
summary_minmax = _utils.summary_minmax


# =============================================================================
# Load and store cleaned base datasets
# =============================================================================

ensure_dir(DERIVED_DIR)

# Static community and monoculture data are reused by several figures. They are
# stored once after applying the manuscript filters so figure scripts do not need
# to repeat these filtering steps.
df_comm = prep_static_comm_df(COMM_STATIC_PATH)
df_mono = prep_static_mono_df(MONO_STATIC_PATH)

df_comm.to_csv(os.path.join(DERIVED_DIR, "df_comm_prepared.csv"), index=False)
df_mono.to_csv(os.path.join(DERIVED_DIR, "df_mono_prepared.csv"), index=False)


# =============================================================================
# Figure 3.1: static community vs monoculture total biovolume
# =============================================================================

# The stacked-bar figure needs salinity x PFT matrices with median total
# biovolume values. These are calculated from replicate time series using the
# manuscript convention: median over time per replicate, then median across
# replicates.
comm_sum = replicate_median_over_time_totalvolume_by_pft(
    df_comm,
    group_cols=["salinity"],
    pft_col="pft",
)
mono_sum = replicate_median_over_time_totalvolume_by_pft(
    df_mono,
    group_cols=["salinity"],
    pft_col="pft",
)

comm_mat = complete_grid(comm_sum, SAL_STATIC, PFTS)
mono_mat = complete_grid(mono_sum, SAL_STATIC, PFTS)

comm_mat.to_csv(os.path.join(DERIVED_DIR, "comm_mat.csv"))
mono_mat.to_csv(os.path.join(DERIVED_DIR, "mono_mat.csv"))


# =============================================================================
# Figure 3.2: static community 2x2 error-bar figure
# =============================================================================

# The community figure needs replicate-level medians for the whole community and
# for each PFT. Error bars are calculated in 03_plot_3_2_static_community.py from
# these replicate-level values and from df_comm_prepared.csv.
grouped_pft_static, grouped_all_static = grouped_over_time_medians(
    df_comm,
    keys_prefix=["salinity"],
)

grouped_pft_static.to_csv(
    os.path.join(DERIVED_DIR, "grouped_pft_static.csv"),
    index=False,
)
grouped_all_static.to_csv(
    os.path.join(DERIVED_DIR, "grouped_all_static.csv"),
    index=False,
)


# =============================================================================
# Figure 3.3: dynamic biovolume, V0/V1/V2
# =============================================================================

# V0 is built from static community simulations and restricted to 35/70/105 ppt.
# V1 and V2 are loaded from the dynamic community simulations. The combined data
# frame allows the dynamic figure to compare static and dynamic salinity regimes
# in the same time-series panels.
df_v0 = df_comm[df_comm["salinity"].isin(SAL_DYN)].copy()
df_v0["salinity"] = df_v0["salinity"].astype(int)
df_v0["variant"] = "V0"
df_v0["version"] = df_v0["salinity"].astype(str) + "_V0"

df_v12 = prep_dynamic_comm_df(DYNAMIC_PATH)
df_v12["salinity"] = df_v12["salinity"].astype(int)
df_v12["variant"] = df_v12["version"].astype(str).str.split("_").str[1]
df_v12 = df_v12[df_v12["variant"].isin(["V1", "V2"])].copy()

df_dyn = pd.concat([df_v0, df_v12], ignore_index=True)
df_dyn["time_days"] = df_dyn["time"] / 86400.0
df_dyn["pft"] = normalize_pft_to_int(df_dyn["pft"])
df_dyn["n"] = df_dyn["n"].astype(int)

version_order = [
    "35_V0", "35_V1", "35_V2",
    "70_V0", "70_V1", "70_V2",
    "105_V0", "105_V1", "105_V2",
]
df_dyn["version"] = pd.Categorical(
    df_dyn["version"],
    categories=version_order,
    ordered=True,
)
df_dyn["variant"] = pd.Categorical(
    df_dyn["variant"],
    categories=VARIANT_LEVELS,
    ordered=True,
)

# Values for the stacked total bars on the right side of Figure 3.3.
grouped_pft_dyn, _ = grouped_over_time_medians(
    df_dyn,
    keys_prefix=["salinity", "variant"],
)
summary_pft_tv = summary_minmax(
    grouped_pft_dyn,
    ["salinity", "variant", "pft"],
    "total_volume",
)
summary_pft_tv.to_csv(os.path.join(DERIVED_DIR, "summary_pft_tv.csv"), index=False)

# Values for the PFT time-series panels of Figure 3.3.
per_timestep_pft_dyn = (
    df_dyn.groupby(["version", "pft", "n", "time_days"], observed=True)
    .agg(total_volume=("volume", "sum"))
    .reset_index()
)
median_ts_total_volume = median_ts(per_timestep_pft_dyn, "total_volume")
median_ts_total_volume.to_csv(
    os.path.join(DERIVED_DIR, "median_ts_total_volume.csv"),
    index=False,
)

print("Prepared figure data written to:", DERIVED_DIR)
print("Done: 03_main_prepare_figure_data.py")
