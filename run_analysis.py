# -*- coding: utf-8 -*-

# =============================================================================
# SCRIPT OVERVIEW
# =============================================================================
# Purpose
# -------
# This is the third main entry-point of the repository. It runs the complete
# post-processing pipeline after pyMANGA has produced Population.csv files in
# data_raw/.
#
# Pipeline order
# --------------
# 1. 01_read_raw_data.py
#       Collects all individual Population.csv files and writes combined raw CSVs.
# 2. 02_data_processing.py
#       Adds derived columns such as volume, AG/BG ratio, salinity labels, and PFT.
# 3. 03_main_prepare_figure_data.py
#       Creates compact summary tables used by the plotting scripts.
# 4. plot_*.py scripts
#       Create the final manuscript and appendix figures.
#
# Why subprocesses are used
# -------------------------
# Each source script is started as a separate Python process. This keeps the
# scripts independent and makes it easy to run individual scripts during debugging.
# The repository root is injected into PYTHONPATH so that imports such as
# source.utils.paths work even when scripts are called as subprocesses.
#
# Useful commands
# ---------------
# Full analysis and all figures:
#     py -3.12 run_analysis.py
#
# Only aggregate/process data, no figures:
#     py -3.12 run_analysis.py --prepare-data-only
#
# Only regenerate figures from existing processed data:
#     py -3.12 run_analysis.py --figures-only
# =============================================================================

"""
Run the complete manuscript analysis pipeline.

This script is the top-level entry point for data processing and figure
creation. It calls the existing source scripts in the required order:

1. Aggregate raw pyMANGA Population.csv files from data_raw/
2. Create processed data tables in data/
3. Prepare derived figure data in data/derived_figure_data/
4. Create manuscript figures in figures/main/ and figures/appendix/
"""

import argparse
import os
import subprocess
import sys

from source.utils.paths import REPO_ROOT, ensure_directories

PIPELINE_SCRIPTS = [
    "01_read_raw_data.py",
    "02_data_processing.py",
    "03_main_prepare_figure_data.py",
    "03_plot_2_1_porewater_salinity.py",
    "03_plot_2_2_forman.py",
    "03_plot_2_3_growth_pot_maint.py",
    "03_plot_3_1_static_community_vs_mono.py",
    "03_plot_3_2_static_community.py",
    "03_plot_3_3_dynamic_biovolume.py",
    "03_plot_appendix_1_static_monoculture.py",
]


def run_script(script_name):
    script_path = REPO_ROOT / "source" / script_name
    if not script_path.is_file():
        raise FileNotFoundError(f"Missing analysis script: {script_path}")

    print(f"\nRunning: {script_name}")

    # Make sure scripts in source/ can import modules such as
    # source.utils.paths when they are executed as subprocesses.
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    repo_root_str = str(REPO_ROOT)
    if existing_pythonpath:
        env["PYTHONPATH"] = repo_root_str + os.pathsep + existing_pythonpath
    else:
        env["PYTHONPATH"] = repo_root_str

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=REPO_ROOT,
        text=True,
        env=env,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Script failed: {script_name}")


def main():
    parser = argparse.ArgumentParser(description="Run manuscript analysis pipeline")
    parser.add_argument(
        "--figures-only",
        action="store_true",
        help="Skip raw-data aggregation and data processing; only prepare figure data and create figures.",
    )
    parser.add_argument(
        "--prepare-data-only",
        action="store_true",
        help="Only aggregate and process data; do not prepare figure data or create figures.",
    )
    args = parser.parse_args()

    ensure_directories()

    scripts = PIPELINE_SCRIPTS
    if args.figures_only:
        scripts = PIPELINE_SCRIPTS[2:]
    if args.prepare_data_only:
        scripts = PIPELINE_SCRIPTS[:2]

    for script in scripts:
        run_script(script)

    print("\nAnalysis pipeline completed successfully.")


if __name__ == "__main__":
    main()
