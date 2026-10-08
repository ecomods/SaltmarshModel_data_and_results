"""
Run pyMANGA for the XML control files created by create_setups.py.

Runs are executed in parallel (MAX_WORKERS). Each run writes a log file to
model_output/logs/, and model_output/logs/simulation_log.csv records its exit
status. Runs marked OK there are skipped unless --include-done is given.

pyMANGA is expected next to this repository (../pyMANGA/MANGA.py). The
location is set in source/paths.py.

Usage (from the repository root):
    python run_model.py --list-only               # show the selected runs
    python run_model.py                           # run all categories
    python run_model.py --only community_static   # one or more categories
    python run_model.py --retry-errors            # rerun failed runs
    python run_model.py --include-done            # also rerun completed runs
"""

import argparse
import csv
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path, PureWindowsPath

from source.paths import DEFAULT_MANGA_SCRIPT, LOG_DIR, SIMULATION_LOG, XML_CONTROL_FILES

MAX_WORKERS = 6

# Simulation categories are the XML file name prefixes.
CATEGORIES = [
    "community_static",
    "community_dynamic",
    "monoculture_static",
    "oneplant_static",
    "oneplant_dynamic",
]

LOG_FIELDS = ["xml_file", "log_file", "start_time", "end_time",
              "duration_sec", "exit_code", "status"]


def run_simulation(xml_file):
    """Run pyMANGA for one XML file from the pyMANGA folder; output goes to a log file."""
    log_path = LOG_DIR / f"{xml_file.stem}.log"
    start_time = datetime.now()
    with open(log_path, "w", encoding="utf-8") as logfile:
        process = subprocess.run(
            [sys.executable, str(DEFAULT_MANGA_SCRIPT), "-i", str(xml_file)],
            cwd=DEFAULT_MANGA_SCRIPT.parent,
            stdout=logfile,
            stderr=logfile,
        )
    end_time = datetime.now()

    return {
        "xml_file": str(xml_file),
        "log_file": str(log_path),
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration_sec": (end_time - start_time).total_seconds(),
        "exit_code": process.returncode,
        "status": "OK" if process.returncode == 0 else "ERROR",
    }


def latest_status():
    """Latest logged status per XML file name; later rows overwrite earlier ones."""
    if not SIMULATION_LOG.is_file():
        return {}
    with open(SIMULATION_LOG, newline="", encoding="utf-8") as f:
        # Match by file name, so the log stays valid when the repository is
        # moved. PureWindowsPath reads both / and \ separators.
        return {PureWindowsPath(row["xml_file"]).name: row["status"]
                for row in csv.DictReader(f)}


def append_to_log(result):
    """Append one run result to the CSV log as soon as the run finishes."""
    new_file = not SIMULATION_LOG.is_file()
    with open(SIMULATION_LOG, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=LOG_FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerow(result)


def select_xml_files(categories, retry_only=False, include_done=False):
    """
    Select XML files by category and latest logged status.

    retry_only selects only files with a logged status other than OK and takes
    priority over include_done. Otherwise files marked OK are skipped unless
    include_done is set; files without a log entry are selected.
    """
    files = [p for p in sorted(XML_CONTROL_FILES.glob("*.xml"))
             if p.name.startswith(tuple(categories))]
    status = latest_status()
    if retry_only:
        return [p for p in files if status.get(p.name, "OK") != "OK"]
    if include_done:
        return files
    return [p for p in files if status.get(p.name) != "OK"]


def main():
    parser = argparse.ArgumentParser(description="Run pyMANGA for the XML control files.")
    parser.add_argument("--only", nargs="+", choices=CATEGORIES, default=CATEGORIES,
                        metavar="CATEGORY",
                        help=f"Run only these categories ({', '.join(CATEGORIES)})")
    parser.add_argument("--retry-errors", action="store_true",
                        help="Run only simulations that failed")
    parser.add_argument("--include-done", action="store_true",
                        help="Also run simulations marked OK in the log")
    parser.add_argument("--list-only", action="store_true",
                        help="Only list the selected simulations")
    args = parser.parse_args()

    xml_files = select_xml_files(args.only, args.retry_errors, args.include_done)
    if not xml_files:
        print("No simulations selected (selection empty or all done).")
        return

    print("Categories:", ", ".join(args.only))
    print(f"Include completed (OK in log): {args.include_done}")
    print("Selection:")
    for path in xml_files:
        print(" -", path.name)

    if args.list_only:
        print(f"\n{len(xml_files)} simulation(s) selected (list-only).")
        return

    print(f"\nRunning {len(xml_files)} simulations, up to {MAX_WORKERS} in parallel...\n")
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(run_simulation, path) for path in xml_files]
        for future in as_completed(futures):
            result = future.result()
            append_to_log(result)
            name = Path(result["xml_file"]).name
            if result["status"] == "OK":
                print(f"OK: {name} finished in {result['duration_sec']:.1f}s")
            else:
                print(f"ERROR: {name} failed (exit code: {result['exit_code']})")


if __name__ == "__main__":
    main()
