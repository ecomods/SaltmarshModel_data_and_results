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
# 1. 01_prepare_figure_data.py
#       Reads Population.csv files and writes the 14 plot-facing tables.
# 2. plot_*.py scripts
#       Create the final manuscript and appendix figures, including the optional
#       mean-based versions of the plot_3* figures.
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
#     python run_analysis.py
#
# Only prepare the plot-facing tables, no figures:
#     python run_analysis.py --prepare-data-only
#
# Only render figures from existing figure tables:
#     python run_analysis.py --figures-only
# =============================================================================

"""
Run the complete manuscript analysis pipeline.

This script is the top-level entry point for data processing and figure
creation. It calls the existing source scripts in the required order:

1. Prepare plot-facing tables directly from pyMANGA Population.csv files
2. Create manuscript figures in figures/main/ and figures/appendix/
"""

import argparse
import os
import subprocess
import sys

from source.utils.paths import REPO_ROOT, ensure_directories

PIPELINE_SCRIPTS = [
    "01_prepare_figure_data.py",
    "02_plot_appendix_2_porewater_salinity.py",
    "02_plot_2_2_forman.py",
    "02_plot_appendix_1_growth_pot_maint.py",
    "02_plot_3_1_static_community_vs_mono.py",
    "02_plot_3_2_static_community.py",
    "02_MEAN_plot_3_2_static_community.py",
    "02_plot_3_3_dynamic_biovolume.py",
    "02_MEAN_plot_3_3_dynamic_biovolume.py",
    "02_plot_appendix_3_static_monoculture.py",
    "02_MEAN_plot_appendix_3_static_monoculture.py",
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
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--prepare-data-only",
        action="store_true",
        help="Prepare the 14 figure tables directly from raw model output; do not render figures.",
    )
    mode.add_argument(
        "--figures-only",
        action="store_true",
        help="Render all figures from existing figure data without preparing or changing any tables.",
    )
    args = parser.parse_args()

    if not args.figures_only:
        ensure_directories()

    scripts = PIPELINE_SCRIPTS
    if args.prepare_data_only:
        scripts = PIPELINE_SCRIPTS[:1]
    elif args.figures_only:
        scripts = PIPELINE_SCRIPTS[1:]

    for script in scripts:
        run_script(script)

    print("\nAnalysis pipeline completed successfully.")


if __name__ == "__main__":
    main()
