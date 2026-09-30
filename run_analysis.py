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
import os
import subprocess
import sys

from source.utils.paths import REPO_ROOT, ensure_directories

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
        help="Prepare the 7 figure tables directly from raw model output; do not render figures.",
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
