# -*- coding: utf-8 -*-

# =============================================================================
# SCRIPT OVERVIEW
# =============================================================================
# Purpose
# -------
# This script is the first analysis step. It reads the raw pyMANGA Population.csv
# files from data_raw/ and combines them into larger CSV files under data/.
#
# Why this step exists
# --------------------
# pyMANGA writes one Population.csv per simulation run. For the manuscript figures
# it is easier and safer to work with one combined table per setup family:
# - community/static,
# - community/dynamic,
# - monoculture/static.
#
# What information is added
# -------------------------
# The raw Population.csv files do not know, by themselves, which replicate,
# salinity scenario, dynamic variant, or monoculture PFT they belong to. That
# information is encoded in the folder structure. This script reads the folder
# names and adds those columns explicitly.
#
# Important expectation
# ---------------------
# This script assumes that run_model.py has already been run successfully and
# that the expected Population.csv files exist in data_raw/. If one expected file
# is missing, the script raises a FileNotFoundError so that incomplete simulation
# sets are detected early.
# =============================================================================

"""
Created December 2025

This script aggregates pyMANGA Population.csv outputs from different
simulation setups into unified CSV files for further analysis.

It
- merges community simulations (PFT 1-4) with static salinity
- merges community simulations (PFT 1-4) with dynamic salinity
- merges monoculture simulations (single PFT) with static salinity
"""

from pathlib import Path
import glob
import pandas as pd


# Allow this source/ script to be run directly with
#     python source/<script_name>.py
# as well as through run_analysis.py.
import sys
from pathlib import Path

REPO_ROOT_BOOTSTRAP = Path(__file__).resolve().parents[1]
if str(REPO_ROOT_BOOTSTRAP) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT_BOOTSTRAP))

from source.utils.paths import (
    DATA_RAW,
    COMMUNITY_STATIC_RAW,
    COMMUNITY_DYNAMIC_RAW,
    MONOCULTURE_STATIC_RAW,
    ensure_directories,
)

# list of salinities [kg/kg] as strings to match folder names
salinity = ["0.035", "0.070", "0.105", "0.140"]
versions = ["35_V1", "35_V2", "70_V1", "70_V2", "105_V1", "105_V2"]
replicates = range(1, 11)


def read_population(path):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Missing Population.csv: {path}")
    return pd.read_csv(path, sep="\t")


def add_plant_uid(df, columns):
    uid = df[columns[0]].astype(str)
    for column in columns[1:]:
        uid = uid + "_" + df[column].astype(str)
    df["plant_uid"] = uid
    return df


def aggregate_community_static():
    temp_dfs = []

    for sal in salinity:
        temp_dfs_2 = []

        for n in replicates:
            fp = DATA_RAW / "community" / "static" / sal / f"{n:02d}" / "Population.csv"
            temp_df = read_population(fp)

            temp_df["pfts"] = "all"
            temp_df["salinity"] = int(sal.split(".")[1])
            temp_df["setup"] = "static"
            temp_df["n"] = n

            temp_df = add_plant_uid(
                temp_df,
                ["setup", "salinity", "pfts", "n", "plant"],
            )

            temp_dfs_2.append(temp_df)

        temp_dfs.append(pd.concat(temp_dfs_2, ignore_index=True))

    df_community_static = pd.concat(temp_dfs, ignore_index=True)
    COMMUNITY_STATIC_RAW.parent.mkdir(parents=True, exist_ok=True)
    df_community_static.to_csv(COMMUNITY_STATIC_RAW, index=False)
    print(f"Saved: {COMMUNITY_STATIC_RAW}")


def aggregate_community_dynamic():
    temp_dfs = []

    for version in versions:
        temp_dfs_2 = []

        for n in replicates:
            fp = DATA_RAW / "community" / "dynamic" / version / f"{n:02d}" / "Population.csv"
            temp_df = read_population(fp)

            temp_df["pfts"] = "all"
            temp_df["version"] = version
            temp_df["salinity"] = temp_df["version"].str.split("_").str[0].astype(int)
            temp_df["setup"] = "dynamic"
            temp_df["n"] = n

            temp_df = add_plant_uid(
                temp_df,
                ["setup", "version", "pfts", "n", "plant"],
            )

            temp_dfs_2.append(temp_df)

        temp_dfs.append(pd.concat(temp_dfs_2, ignore_index=True))

    df_community_dynamic = pd.concat(temp_dfs, ignore_index=True)
    COMMUNITY_DYNAMIC_RAW.parent.mkdir(parents=True, exist_ok=True)
    df_community_dynamic.to_csv(COMMUNITY_DYNAMIC_RAW, index=False)
    print(f"Saved: {COMMUNITY_DYNAMIC_RAW}")


def aggregate_monoculture_static():
    mono_base = DATA_RAW / "monoculture" / "static"
    MONOCULTURE_STATIC_RAW.parent.mkdir(parents=True, exist_ok=True)

    pft_dirs = set()
    for sal in salinity:
        sal_dir = mono_base / sal
        if sal_dir.is_dir():
            # Current repository standard: PFT_1, PFT_2, ...
            # Backward-compatible fallback: pft_1, pft_2, ...
            for pattern in ["PFT_*", "pft_*"]:
                for d in glob.glob(str(sal_dir / pattern)):
                    if Path(d).is_dir():
                        pft_dirs.add(Path(d).name)

    pft_dirs = sorted(
        pft_dirs,
        key=lambda name: int(name.split("_")[-1]) if name.split("_")[-1].isdigit() else name,
    )
    temp_dfs = []

    for sal in salinity:
        for pft_folder in pft_dirs:
            temp_dfs_2 = []

            for n in replicates:
                fp = mono_base / sal / pft_folder / f"{n:02d}" / "Population.csv"
                if not fp.is_file():
                    continue

                temp_df = pd.read_csv(fp, sep="\t")
                if pft_folder.startswith("PFT_") or pft_folder.startswith("pft_"):
                    pft_id = pft_folder.split("_")[-1]
                else:
                    pft_id = pft_folder

                temp_df["pfts"] = str(pft_id)
                temp_df["salinity"] = int(sal.split(".")[1])
                temp_df["setup"] = "static"
                temp_df["n"] = n

                temp_df = add_plant_uid(
                    temp_df,
                    ["setup", "salinity", "pfts", "n", "plant"],
                )

                temp_dfs_2.append(temp_df)

            if len(temp_dfs_2) > 0:
                temp_dfs.append(pd.concat(temp_dfs_2, ignore_index=True))

    if len(temp_dfs) > 0:
        df_mono_static = pd.concat(temp_dfs, ignore_index=True)
        df_mono_static.to_csv(MONOCULTURE_STATIC_RAW, index=False)
    else:
        pd.DataFrame().to_csv(MONOCULTURE_STATIC_RAW, index=False)

    print(f"Saved: {MONOCULTURE_STATIC_RAW}")


def main():
    ensure_directories()
    aggregate_community_static()
    aggregate_community_dynamic()
    aggregate_monoculture_static()


if __name__ == "__main__":
    main()
