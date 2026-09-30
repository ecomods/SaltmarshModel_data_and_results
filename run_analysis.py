"""
Prepare the figure tables and create all manuscript figures.

Runs source/01_prepare_figure_data.py and then the figure scripts
02_fig1_... to 08_figS3_..., each as a separate Python process, so that
every script can also be run on its own.

Usage (from the repository root):
    python run_analysis.py                      # tables and figures
    python run_analysis.py --prepare-data-only  # only the tables
    python run_analysis.py --figures-only       # only the figures
"""

import argparse
import subprocess
import sys

from source.paths import REPO_ROOT

PIPELINE_SCRIPTS = [
    "01_prepare_figure_data.py",
    "02_fig1_salinity_response.py",
    "03_fig2_community_vs_monoculture.py",
    "04_fig3_community_structure.py",
    "05_fig4_dynamic_biovolume.py",
    "06_figS1_growth_vs_maintenance.py",
    "07_figS2_porewater_salinity.py",
    "08_figS3_monoculture_structure.py",
]


def run_script(script_name):
    print(f"\nRunning: {script_name}")
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "source" / script_name)],
        cwd=REPO_ROOT,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Script failed: {script_name}")


def main():
    parser = argparse.ArgumentParser(description="Run manuscript analysis pipeline")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--prepare-data-only",
        action="store_true",
        help="Prepare the 7 figure tables directly from raw model output; do not render figures.",
    )
    mode.add_argument(
        "--figures-only",
        action="store_true",
        help="Render all figures from existing figure data without preparing or changing any tables.",
    )
    args = parser.parse_args()

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
