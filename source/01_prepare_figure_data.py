"""Prepare all 14 manuscript figure tables from pyMANGA Population.csv files.

The three setup families are read one at a time. Folder names supply scenario
metadata, plant geometry supplies the derived biovolume columns, and the
existing figure helpers apply the manuscript filters and summaries. Only the
tables consumed by plotting scripts are written. Use --output-dir to build a
candidate without touching the current figure data.
"""

import argparse
import glob
import importlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from source.utils.paths import DATA_RAW, DERIVED_FIGURE_DATA

config = importlib.import_module("03_figure_config")
utils = importlib.import_module("03_figure_utils")

SALINITIES = ["0.035", "0.070", "0.105", "0.140"]
VERSIONS = ["35_V1", "35_V2", "70_V1", "70_V2", "105_V1", "105_V2"]
REPLICATES = range(1, 11)


def read_population(path):
    if not path.is_file():
        raise FileNotFoundError(f"Missing Population.csv: {path}")
    return pd.read_csv(path, sep="\t")


def add_plant_uid(df, columns):
    uid = df[columns[0]].astype(str)
    for column in columns[1:]:
        uid = uid + "_" + df[column].astype(str)
    df["plant_uid"] = uid
    return df


def add_derived_metrics(df):
    """Keep all raw columns, replacing model volume with geometry-derived volume."""
    df["ag_volume"] = np.pi * df["r_ag"] ** 2 * df["h_ag"]
    df["bg_volume"] = np.pi * df["r_bg"] ** 2 * df["h_bg"]
    df["volume"] = df["ag_volume"] + df["bg_volume"]
    df["ag_bg_ratio"] = df["ag_volume"] / df["bg_volume"]
    df["pft"] = df["plant"].apply(lambda value: int("_".join(str(value).split("_")[1]))).astype(int)
    return df


def read_static_community():
    tables = []
    for sal in SALINITIES:
        for n in REPLICATES:
            path = DATA_RAW / "community" / "static" / sal / f"{n:02d}" / "Population.csv"
            df = read_population(path)
            df["pfts"] = "all"
            df["salinity"] = int(sal.split(".")[1])
            df["setup"] = "static"
            df["n"] = n
            tables.append(add_plant_uid(df, ["setup", "salinity", "pfts", "n", "plant"]))
    return add_derived_metrics(pd.concat(tables, ignore_index=True))


def read_static_monoculture():
    base = DATA_RAW / "monoculture" / "static"
    folders = set()
    for sal in SALINITIES:
        sal_dir = base / sal
        for pattern in ("PFT_*", "pft_*"):
            folders.update(Path(path).name for path in glob.glob(str(sal_dir / pattern)) if Path(path).is_dir())
    folders = sorted(
        folders,
        key=lambda name: int(name.split("_")[-1]) if name.split("_")[-1].isdigit() else name,
    )

    tables = []
    for sal in SALINITIES:
        for folder in folders:
            for n in REPLICATES:
                path = base / sal / folder / f"{n:02d}" / "Population.csv"
                if not path.is_file():
                    continue  # Preserve the previous monoculture missing-run behaviour.
                df = read_population(path)
                pft_id = folder.split("_")[-1] if folder.startswith(("PFT_", "pft_")) else folder
                df["pfts"] = str(pft_id)
                df["salinity"] = int(sal.split(".")[1])
                df["setup"] = "static"
                df["n"] = n
                tables.append(add_plant_uid(df, ["setup", "salinity", "pfts", "n", "plant"]))
    if not tables:
        raise FileNotFoundError(f"No monoculture Population.csv files found under {base}")
    return add_derived_metrics(pd.concat(tables, ignore_index=True))


def read_dynamic_community():
    tables = []
    for version in VERSIONS:
        for n in REPLICATES:
            path = DATA_RAW / "community" / "dynamic" / version / f"{n:02d}" / "Population.csv"
            df = read_population(path)
            df["pfts"] = "all"
            df["version"] = version
            df["salinity"] = df["version"].str.split("_").str[0].astype(int)
            df["setup"] = "dynamic"
            df["n"] = n
            tables.append(add_plant_uid(df, ["setup", "version", "pfts", "n", "plant"]))
    return add_derived_metrics(pd.concat(tables, ignore_index=True))


def save(df, output_dir, filename, *, index=False):
    path = output_dir / filename
    df.to_csv(path, index=index)
    print(f"Saved: {path}", flush=True)


def prepare_static_community(output_dir):
    df = utils.prep_static_comm_df(read_static_community())
    save(df, output_dir, "df_comm_prepared.csv")

    v0 = df[df["salinity"].isin(config.SAL_DYN)].copy()
    v0["salinity"] = v0["salinity"].astype(int)
    v0["variant"] = "V0"
    v0["version"] = v0["salinity"].astype(str) + "_V0"

    comm_sum = utils.replicate_median_over_time_totalvolume_by_pft(df, ["salinity"])
    mean_comm_sum = utils.replicate_mean_over_time_totalvolume_by_pft(df, ["salinity"])
    save(utils.complete_grid(comm_sum, config.SAL_STATIC, config.PFTS), output_dir, "comm_mat.csv", index=True)
    save(utils.complete_grid(mean_comm_sum, config.SAL_STATIC, config.PFTS), output_dir, "MEAN_comm_mat.csv", index=True)

    grouped_pft, grouped_all = utils.grouped_over_time_medians(df, ["salinity"])
    save(grouped_pft, output_dir, "grouped_pft_static.csv")
    save(grouped_all, output_dir, "grouped_all_static.csv")
    grouped_pft, grouped_all = utils.grouped_over_time_means(df, ["salinity"])
    save(grouped_pft, output_dir, "MEAN_grouped_pft_static.csv")
    save(grouped_all, output_dir, "MEAN_grouped_all_static.csv")
    return v0


def prepare_static_monoculture(output_dir):
    df = utils.prep_static_mono_df(read_static_monoculture())
    save(df, output_dir, "df_mono_prepared.csv")
    mono_sum = utils.replicate_median_over_time_totalvolume_by_pft(df, ["salinity"])
    mean_mono_sum = utils.replicate_mean_over_time_totalvolume_by_pft(df, ["salinity"])
    save(utils.complete_grid(mono_sum, config.SAL_STATIC, config.PFTS), output_dir, "mono_mat.csv", index=True)
    save(utils.complete_grid(mean_mono_sum, config.SAL_STATIC, config.PFTS), output_dir, "MEAN_mono_mat.csv", index=True)


def prepare_dynamic(output_dir, v0):
    v12 = utils.prep_dynamic_comm_df(read_dynamic_community())
    v12["salinity"] = v12["salinity"].astype(int)
    v12["variant"] = v12["version"].astype(str).str.split("_").str[1]
    v12 = v12[v12["variant"].isin(["V1", "V2"])].copy()

    df = pd.concat([v0, v12], ignore_index=True)
    df["time_days"] = df["time"] / 86400.0
    df["pft"] = utils.normalize_pft_to_int(df["pft"])
    df["n"] = df["n"].astype(int)
    df["version"] = pd.Categorical(
        df["version"],
        categories=[
            "35_V0", "35_V1", "35_V2", "70_V0", "70_V1", "70_V2",
            "105_V0", "105_V1", "105_V2",
        ],
        ordered=True,
    )
    df["variant"] = pd.Categorical(df["variant"], categories=config.VARIANT_LEVELS, ordered=True)

    totals = (
        df.groupby(["salinity", "variant", "pft", "n", "time"])["volume"]
        .sum()
        .reset_index(name="total_volume")
    )
    grouped_pft, _ = utils.grouped_over_time_medians(
        df, ["salinity", "variant"], per_timestep_total_pft=totals,
    )
    save(
        utils.summary_minmax(grouped_pft, ["salinity", "variant", "pft"], "total_volume"),
        output_dir, "summary_pft_tv.csv",
    )
    grouped_pft, _ = utils.grouped_over_time_means(
        df, ["salinity", "variant"], per_timestep_total_pft=totals,
    )
    save(
        utils.summary_minmax_mean(grouped_pft, ["salinity", "variant", "pft"], "total_volume"),
        output_dir, "MEAN_summary_pft_tv.csv",
    )

    per_timestep = (
        df.groupby(["version", "pft", "n", "time_days"], observed=True)
        .agg(total_volume=("volume", "sum"))
        .reset_index()
    )
    save(utils.median_ts(per_timestep, "total_volume"), output_dir, "median_ts_total_volume.csv")
    save(utils.mean_ts(per_timestep, "total_volume"), output_dir, "MEAN_ts_total_volume.csv")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir", type=Path, default=DERIVED_FIGURE_DATA,
        help="Directory for the 14 figure tables (default: data/derived_figure_data).",
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    v0 = prepare_static_community(args.output_dir)
    prepare_static_monoculture(args.output_dir)
    prepare_dynamic(args.output_dir, v0)
    print("Figure-data preparation completed successfully.")


if __name__ == "__main__":
    main()
