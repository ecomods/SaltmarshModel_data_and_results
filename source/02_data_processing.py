# -*- coding: utf-8 -*-

# =============================================================================
# SCRIPT OVERVIEW
# =============================================================================
# Purpose
# -------
# This script turns combined raw tables into analysis-ready tables. It calculates
# biological variables that are not stored directly in pyMANGA output, for example
# aboveground volume, belowground volume, total volume, and AG/BG ratio.
#
# Input
# -----
# The script reads raw_data.csv files created by 01_read_raw_data.py.
#
# Output
# ------
# The script writes data.csv files that are used by 03_main_prepare_figure_data.py
# and by the plotting scripts.
#
# Important filtering rule
# ------------------------
# Very young seedlings are excluded using the manuscript age threshold. This is
# done before summary statistics are calculated so that all figures are based on
# the same filtered plant population.
# =============================================================================

"""
Created December 2025

This script adds derived plant metrics to the aggregated raw CSV files and
writes processed data files used by the figure pipeline.
"""

import pandas as pd
import numpy as np
from matplotlib import rcParams


# Allow this source/ script to be run directly with
#     python source/<script_name>.py
# as well as through run_analysis.py.
import sys
from pathlib import Path

REPO_ROOT_BOOTSTRAP = Path(__file__).resolve().parents[1]
if str(REPO_ROOT_BOOTSTRAP) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT_BOOTSTRAP))

from source.utils.paths import (
    COMMUNITY_STATIC_RAW,
    COMMUNITY_DYNAMIC_RAW,
    MONOCULTURE_STATIC_RAW,
    COMMUNITY_STATIC_DATA,
    COMMUNITY_DYNAMIC_DATA,
    MONOCULTURE_STATIC_DATA,
    DATA,
    ensure_directories,
)

rcParams["font.family"] = "Courier New"


def extract_pft_from_plant_id(value):
    return int("_".join(str(value).split("_")[1]))


def add_derived_metrics(df):
    df = df.copy()
    df["ag_volume"] = np.pi * df["r_ag"]**2 * df["h_ag"]
    df["bg_volume"] = np.pi * df["r_bg"]**2 * df["h_bg"]
    df["volume"] = df["ag_volume"] + df["bg_volume"]
    df["ag_bg_ratio"] = df["ag_volume"] / df["bg_volume"]
    df["pft"] = df["plant"].apply(extract_pft_from_plant_id).astype(int)
    return df


def process_community_static():
    df = pd.read_csv(COMMUNITY_STATIC_RAW)
    df = add_derived_metrics(df)

    COMMUNITY_STATIC_DATA.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(COMMUNITY_STATIC_DATA, index=False)

    for sal in [35, 70, 105, 140]:
        outdir = DATA / "community" / "static" / str(sal)
        outdir.mkdir(parents=True, exist_ok=True)

        df_filtered = df[
            (df["setup"] == "static") &
            (df["pfts"] == "all") &
            (df["salinity"] == sal)
        ]
        df_filtered.to_csv(outdir / "data.csv", index=False)

    print(f"Saved: {COMMUNITY_STATIC_DATA}")


def process_community_dynamic():
    df = pd.read_csv(COMMUNITY_DYNAMIC_RAW)
    df = add_derived_metrics(df)

    COMMUNITY_DYNAMIC_DATA.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(COMMUNITY_DYNAMIC_DATA, index=False)

    for version in ["35_V1", "35_V2", "70_V1", "70_V2", "105_V1", "105_V2"]:
        outdir = DATA / "community" / "dynamic" / version
        outdir.mkdir(parents=True, exist_ok=True)

        df_filtered = df[
            (df["setup"] == "dynamic") &
            (df["pfts"] == "all") &
            (df["salinity"] == int(version.split("_")[0])) &
            (df["version"] == version)
        ]
        df_filtered.to_csv(outdir / "data.csv", index=False)

    print(f"Saved: {COMMUNITY_DYNAMIC_DATA}")


def process_monoculture_static():
    df = pd.read_csv(MONOCULTURE_STATIC_RAW)
    df = add_derived_metrics(df)

    MONOCULTURE_STATIC_DATA.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(MONOCULTURE_STATIC_DATA, index=False)

    for sal in [35, 70, 105, 140]:
        for pft in ["1", "2", "3", "4"]:
            outdir = DATA / "monoculture" / "static" / str(sal) / f"PFT_{pft}"
            outdir.mkdir(parents=True, exist_ok=True)

            df_filtered = df[
                (df["salinity"] == sal) &
                (df["pfts"].astype(str) == pft)
            ]
            df_filtered.to_csv(outdir / "data.csv", index=False)

    print(f"Saved: {MONOCULTURE_STATIC_DATA}")


def main():
    ensure_directories()
    process_community_static()
    process_community_dynamic()
    process_monoculture_static()


if __name__ == "__main__":
    main()
