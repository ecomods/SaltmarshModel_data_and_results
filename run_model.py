"""
Run pyMANGA for the XML control files created by create_setups.py.

Runs are executed in parallel (MAX_WORKERS). Each run writes a log file to
data_raw/logs/, and data_raw/logs/simulation_log.csv records its exit status.
Runs marked OK in that file are skipped unless --include-done is given.

pyMANGA is expected next to this repository (../pyMANGA/MANGA.py). The
location is set in source/paths.py.

Usage (from the repository root):
    python run_model.py --list-only       # show the selected runs
    python run_model.py                   # run CATEGORIES_TO_RUN
    python run_model.py --override-only community_static
    python run_model.py --retry-errors    # rerun failed runs
    python run_model.py --include-done    # also rerun completed runs
"""

import os
import glob
import subprocess
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import csv
import fnmatch
import sys

from source.paths import (
    XML_CONTROL_FILES,
    LOG_DIR as DEFAULT_LOG_DIR,
    SIMULATION_LOG,
    DEFAULT_MANGA_SCRIPT,
)

# ======================================================
# === USER CONFIGURATION ===============================
# ======================================================

MANGA_PATH = DEFAULT_MANGA_SCRIPT
XML_FOLDER = XML_CONTROL_FILES
PYTHON_EXEC = sys.executable
MAX_WORKERS = 6
LOG_DIR = DEFAULT_LOG_DIR
CSV_LOGFILE = SIMULATION_LOG

# Simulation categories selected for execution. Use ["all"] to run every XML file.
# Valid categories are community_static, community_dynamic, monoculture_static,
# oneplant_static, and oneplant_dynamic.
CATEGORIES_TO_RUN = [
    "community_static",
    "community_dynamic",
    "monoculture_static",
    "oneplant_static",
    "oneplant_dynamic",
]

# Set to True to run XML files even if they are marked as OK in the CSV log.
RECOMPUTE_COMPLETED = False

# ======================================================
# === INTERNAL CONFIG ==================================
# ======================================================

CATEGORY_PATTERNS = {
    "community_dynamic":    "community_dynamic*.xml",
    "community_static":     "community_static*.xml",
    "monoculture_static":   "monoculture_static*.xml",
    "oneplant_static":      "oneplant_static*.xml",
    "oneplant_dynamic":     "oneplant_dynamic*.xml",
    "all":                  "*.xml",
}


# ======================================================
# === CORE FUNCTIONS ===================================
# ======================================================

def run_simulation(xml_file):
    """Run pyMANGA for one XML file from the pyMANGA folder; output goes to a log file."""
    xml_file = os.path.abspath(xml_file)
    xml_name = os.path.splitext(os.path.basename(xml_file))[0]
    log_path = os.path.join(str(LOG_DIR), f"{xml_name}.log")

    manga_dir = os.path.abspath(os.path.dirname(str(MANGA_PATH)))
    manga_py = os.path.abspath(str(MANGA_PATH))

    start_time = datetime.now()
    with open(log_path, "w", encoding="utf-8") as logfile:
        process = subprocess.run(
            [PYTHON_EXEC, manga_py, "-i", xml_file],
            cwd=manga_dir,
            stdout=logfile,
            stderr=logfile,
        )
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    return {
        "xml_file": xml_file,
        "log_file": log_path,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration_sec": duration,
        "exit_code": process.returncode,
        "status": "OK" if process.returncode == 0 else "ERROR",
    }


def read_logfile():
    if not os.path.isfile(str(CSV_LOGFILE)):
        return []
    with open(str(CSV_LOGFILE), newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def append_to_logfile(result):
    """Append one run result to the CSV log (written as soon as a run finishes)."""
    file_exists = os.path.isfile(str(CSV_LOGFILE))
    with open(str(CSV_LOGFILE), "a", newline="", encoding="utf-8") as f:
        fieldnames = ["xml_file", "log_file", "start_time", "end_time",
                      "duration_sec", "exit_code", "status"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(result)


def list_all_xml():
    return sorted(glob.glob(os.path.join(str(XML_FOLDER), "*.xml")))


def _patterns_for(cats):
    pats = []
    for c in cats:
        pat = CATEGORY_PATTERNS.get(c)
        if pat is not None:
            pats.append(os.path.join(str(XML_FOLDER), pat))
    return pats


def filter_by_categories(files, only_categories=None, exclude_categories=None):
    """Filter XML files by simulation category using glob patterns."""
    if not files:
        return []

    selected = files

    # Keep only the selected categories.
    if only_categories:
        # The category "all" keeps the complete selected file list.
        if "all" not in only_categories:
            only_pats = _patterns_for(only_categories)
            selected = [
                f for f in selected
                if any(fnmatch.fnmatch(f, pat) for pat in only_pats)
            ]

    # Remove excluded categories.
    if exclude_categories:
        excl_pats = _patterns_for(exclude_categories)
        selected = [
            f for f in selected
            if not any(fnmatch.fnmatch(f, pat) for pat in excl_pats)
        ]

    return selected


def select_xml_files(
    retry_only=False,
    only_categories=None,
    exclude_categories=None,
    include_done=False
):
    """
    Select XML files for execution.

    Selection steps:
    1. Start from all XML files in the XML folder.
    2. Apply optional category filters.
    3. If retry_only is enabled, keep only files whose latest status is not OK.
    4. Unless include_done is enabled, skip files whose latest status is OK.
    """
    all_xml = list_all_xml()
    filtered = filter_by_categories(all_xml, only_categories, exclude_categories)

    # The log only grows; later rows overwrite earlier ones for the same file.
    latest_status = {os.path.abspath(row["xml_file"]): row["status"] for row in read_logfile()}

    if retry_only:
        return sorted(
            f for f in filtered
            if latest_status.get(os.path.abspath(f), "OK") != "OK"
        )

    if include_done:
        return filtered

    return [f for f in filtered if latest_status.get(os.path.abspath(f)) != "OK"]


# ======================================================
# === MAIN =============================================
# ======================================================

def main():
    # Include "all" in the allowed command-line category choices.
    choices = list(CATEGORY_PATTERNS.keys())

    parser = argparse.ArgumentParser(description="MANGA simulation controller")
    parser.add_argument("--retry-errors", action="store_true",
                        help="Rerun only failed simulations")
    parser.add_argument("--exclude", nargs="+", choices=[c for c in choices if c != "all"],
                        default=[],
                        help="Exclude these categories")
    parser.add_argument("--list-only", action="store_true",
                        help="Only list selected XMLs and exit")
    parser.add_argument("--override-only", nargs="+", choices=choices,
                        help="Override CATEGORIES_TO_RUN temporarily (supports 'all')")
    parser.add_argument("--include-done", action="store_true",
                        help="Include files already marked as OK in the log (recompute completed)")

    args = parser.parse_args()

    # Determine the category selection.
    only_categories = args.override_only if args.override_only else CATEGORIES_TO_RUN
    # Use all categories if the configured category list is empty.
    if not only_categories:
        only_categories = ["all"]

    # The command-line flag takes precedence over the in-script setting.
    include_done = args.include_done or RECOMPUTE_COMPLETED

    xml_files = select_xml_files(
        retry_only=args.retry_errors,
        only_categories=only_categories,
        exclude_categories=args.exclude,
        include_done=include_done
    )

    if not xml_files:
        print("No XML files to run (selection empty or all done).")
        return

    print("Categories used:", ", ".join(only_categories))
    if args.exclude:
        print("Excluded:", ", ".join(args.exclude))
    print(f"Include completed (OK in log): {include_done}")
    print("Selection:")
    for f in xml_files:
        print(" -", os.path.relpath(f, str(XML_FOLDER)))

    if args.list_only:
        print(f"\n{len(xml_files)} XML file(s) selected (list-only).")
        return

    print(f"\nRunning {len(xml_files)} simulations with up to {MAX_WORKERS} parallel threads...\n")

    os.makedirs(LOG_DIR, exist_ok=True)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(run_simulation, xml) for xml in xml_files]
        for future in as_completed(futures):
            res = future.result()
            append_to_logfile(res)
            name = os.path.basename(res["xml_file"])
            if res["status"] == "OK":
                print(f"OK: {name} finished in {res['duration_sec']:.1f}s")
            else:
                print(f"ERROR: {name} failed (exit code: {res['exit_code']})")


if __name__ == "__main__":
    main()
