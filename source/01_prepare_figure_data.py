"""
Prepare the 7 manuscript figure tables from pyMANGA Population.csv files.

The plant rows of the three setup families are loaded and cleaned with the
load_* functions in figure_utils.py and summarised per replicate. Only the
small tables read by the plotting scripts are written; the plant rows are
not saved. --output-dir writes the tables to another folder, for example
for comparisons.

Input:  model_output/community/static, community/dynamic, monoculture/static
Output: figure_data/comm_mat.csv, grouped_pft_static.csv,
        grouped_all_static.csv, mono_mat.csv, grouped_pft_mono_static.csv,
        summary_pft_tv.csv, ts_total_volume.csv
"""

import argparse
from pathlib import Path

import pandas as pd

import figure_config as config
import figure_utils as utils
from paths import FIGURE_DATA


def save(df, output_dir, filename, *, index=False):
    """Write one figure table as CSV and print its path."""
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
    """Tables for Figs. 2 and 3; returns the plant rows for prepare_dynamic()."""
    df = utils.load_static_community()
    grouped_pft, grouped_all = utils.replicate_time_means(df, {"salinity": config.SAL_STATIC})
    save(total_volume_matrix(grouped_pft), output_dir, "comm_mat.csv", index=True)
    save(grouped_pft, output_dir, "grouped_pft_static.csv")
    save(grouped_all, output_dir, "grouped_all_static.csv")
    return df


def prepare_static_monoculture(output_dir):
    """Tables for Figs. 2 and S3."""
    df = utils.load_static_monoculture()
    # All four PFTs are run alone at every salinity, so the full grid applies.
    grouped_pft, _ = utils.replicate_time_means(df, {"salinity": config.SAL_STATIC})
    save(total_volume_matrix(grouped_pft), output_dir, "mono_mat.csv", index=True)
    save(grouped_pft, output_dir, "grouped_pft_mono_static.csv")


def prepare_dynamic(output_dir, static_community):
    """Tables for Fig. 4 (V0 from the static runs, V1 and V2 from the dynamic runs)."""
    # The static runs at the dynamic mean salinities are the V0 regime.
    v0 = static_community[static_community["salinity"].isin(config.SAL_DYN)].copy()
    v0["variant"] = "V0"
    v0["version"] = v0["salinity"].astype(str) + "_V0"

    df = pd.concat([v0, utils.load_dynamic_community()], ignore_index=True)

    grouped_pft, _ = utils.replicate_time_means(
        df, {"salinity": config.SAL_DYN, "variant": config.VARIANT_LEVELS},
    )
    save(
        utils.summary_minmax_mean(grouped_pft, ["salinity", "variant", "pft"], "total_volume"),
        output_dir, "summary_pft_tv.csv",
    )

    # Total biovolume per output step; steps without plants count as 0.
    versions = [f"{sal}_{var}" for sal in config.SAL_DYN for var in config.VARIANT_LEVELS]
    per_timestep = utils.fill_missing_steps(
        df.groupby(["version", "pft", "n", "time"]).agg(total_volume=("volume", "sum")),
        {"version": versions, "pft": config.PFTS},
    ).reset_index()
    per_timestep["version"] = pd.Categorical(per_timestep["version"], categories=versions, ordered=True)
    per_timestep["time_days"] = per_timestep["time"] / 86400.0
    save(utils.mean_ts(per_timestep, "total_volume"), output_dir, "ts_total_volume.csv")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir", type=Path, default=FIGURE_DATA,
        help="Directory for the 7 figure tables (default: figure_data/).",
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    static_community = prepare_static_community(args.output_dir)
    prepare_static_monoculture(args.output_dir)
    prepare_dynamic(args.output_dir, static_community)
    print("Figure-data preparation completed successfully.")


if __name__ == "__main__":
    main()
