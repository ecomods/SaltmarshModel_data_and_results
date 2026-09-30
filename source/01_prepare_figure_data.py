"""Prepare the 7 manuscript figure tables from pyMANGA Population.csv files.

The plant rows of the three setup families are loaded and cleaned with the
load_* functions in figure_utils.py and summarised per replicate. Only the
small tables read by the plotting scripts are written; the plant rows are
not saved. Use --output-dir to build a candidate without touching the
current figure data.
"""

import argparse
from pathlib import Path

import pandas as pd

import figure_config as config
import figure_utils as utils
from paths import DERIVED_FIGURE_DATA


def save(df, output_dir, filename, *, index=False):
    path = output_dir / filename
    df.to_csv(path, index=index)
    print(f"Saved: {path}", flush=True)


def total_volume_matrix(grouped_pft):
    """Salinity x PFT matrix of the mean total biovolume across replicates."""
    summary = (
        grouped_pft.groupby(["salinity", "pft"])["total_volume"]
        .mean()
        .reset_index(name="value")
    )
    return utils.complete_grid(summary, config.SAL_STATIC, config.PFTS)


def prepare_static_community(output_dir):
    df = utils.load_static_community()
    grouped_pft, grouped_all = utils.replicate_time_means(df, ["salinity"])
    save(total_volume_matrix(grouped_pft), output_dir, "comm_mat.csv", index=True)
    save(grouped_pft, output_dir, "grouped_pft_static.csv")
    save(grouped_all, output_dir, "grouped_all_static.csv")
    return df


def prepare_static_monoculture(output_dir):
    df = utils.load_static_monoculture()
    grouped_pft, _ = utils.replicate_time_means(df, ["salinity"])
    save(total_volume_matrix(grouped_pft), output_dir, "mono_mat.csv", index=True)
    save(grouped_pft, output_dir, "grouped_pft_mono_static.csv")


def prepare_dynamic(output_dir, static_community):
    # The static runs at the dynamic mean salinities are the V0 regime.
    v0 = static_community[static_community["salinity"].isin(config.SAL_DYN)].copy()
    v0["variant"] = "V0"
    v0["version"] = v0["salinity"].astype(str) + "_V0"

    df = pd.concat([v0, utils.load_dynamic_community()], ignore_index=True)
    df["time_days"] = df["time"] / 86400.0
    df["version"] = pd.Categorical(
        df["version"],
        categories=[f"{sal}_{var}" for sal in config.SAL_DYN for var in config.VARIANT_LEVELS],
        ordered=True,
    )
    df["variant"] = pd.Categorical(df["variant"], categories=config.VARIANT_LEVELS, ordered=True)

    grouped_pft, _ = utils.replicate_time_means(df, ["salinity", "variant"])
    save(
        utils.summary_minmax_mean(grouped_pft, ["salinity", "variant", "pft"], "total_volume"),
        output_dir, "summary_pft_tv.csv",
    )

    per_timestep = (
        df.groupby(["version", "pft", "n", "time_days"], observed=True)
        .agg(total_volume=("volume", "sum"))
        .reset_index()
    )
    save(utils.mean_ts(per_timestep, "total_volume"), output_dir, "ts_total_volume.csv")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir", type=Path, default=DERIVED_FIGURE_DATA,
        help="Directory for the 7 figure tables (default: data/derived_figure_data).",
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    static_community = prepare_static_community(args.output_dir)
    prepare_static_monoculture(args.output_dir)
    prepare_dynamic(args.output_dir, static_community)
    print("Figure-data preparation completed successfully.")


if __name__ == "__main__":
    main()
