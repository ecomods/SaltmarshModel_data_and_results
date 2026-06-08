# -*- coding: utf-8 -*-

# =============================================================================
# SCRIPT OVERVIEW
# =============================================================================
# Purpose
# -------
# This manuscript figure script visualizes the porewater salinity scenarios used
# as model input. It reads the dynamic salinity CSV files from data_model_input/
# salinity/ and compares them with the static V0 reference conditions.
#
# Figure role in the manuscript
# -----------------------------
# This is a model-input/parameterization figure. It explains what the plants
# experience as salinity forcing before any model output is analyzed.
#
# Output
# ------
# The figure is written directly to figures/main/ as PNG and PDF.
# =============================================================================

"""
Plot porewater salinity input scenarios.

This script creates the conceptual/input-data figure for the dynamic
porewater salinity scenarios used in the model setup.

Outputs
-------
figures/main/plot_2_1_porewater_salinity.png
figures/main/plot_2_1_porewater_salinity.pdf
"""


import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Allow this source/ script to be run directly with
#     python source/<script_name>.py
# as well as through run_analysis.py.
import sys
from pathlib import Path

REPO_ROOT_BOOTSTRAP = Path(__file__).resolve().parents[1]
if str(REPO_ROOT_BOOTSTRAP) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT_BOOTSTRAP))

from source.utils.paths import FIGURES_MAIN, SALINITY_DIR


# =============================================================================
# Settings
# =============================================================================

OUT_DIR = FIGURES_MAIN
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_PNG = OUT_DIR / "plot_2_1_porewater_salinity.png"
OUT_PDF = OUT_DIR / "plot_2_1_porewater_salinity.pdf"

SCENARIO_FILES = {
    "35_V1": "35_V1.csv",
    "35_V2": "35_V2.csv",
    "70_V1": "70_V1.csv",
    "70_V2": "70_V2.csv",
    "105_V1": "105_V1.csv",
    "105_V2": "105_V2.csv",
}

SCENARIO_LABELS = {
    "35_V1": "35 ppt seasonality",
    "35_V2": "35 ppt seasonality + tide",
    "70_V1": "70 ppt seasonality",
    "70_V2": "70 ppt seasonality + tide",
    "105_V1": "105 ppt seasonality",
    "105_V2": "105 ppt seasonality + tide",
}

SCENARIO_ORDER = [
    "35_V1",
    "35_V2",
    "70_V1",
    "70_V2",
    "105_V1",
    "105_V2",
]

# Same blue sequence used for the salinity scenarios in earlier figures.
SCENARIO_COLORS = {
    "35_V1": "#c6dbef",
    "35_V2": "#9ecae1",
    "70_V1": "#6baed6",
    "70_V2": "#4292c6",
    "105_V1": "#2171b5",
    "105_V2": "#084594",
}

SCENARIO_LINESTYLES = {
    "35_V1": (0, (4, 2)),
    "35_V2": (0, (1, 2)),
    "70_V1": (0, (4, 2)),
    "70_V2": (0, (1, 2)),
    "105_V1": (0, (4, 2)),
    "105_V2": (0, (1, 2)),
}

SECONDS_PER_DAY = 86400.0
DAYS_TO_PLOT = 366


# =============================================================================
# Functions
# =============================================================================

def read_salinity_file(scenario, filename):
    """Read one salinity input file and return a clean plotting table."""
    input_path = SALINITY_DIR / filename
    if not input_path.is_file():
        raise FileNotFoundError(f"Missing salinity input file: {input_path}")

    df = pd.read_csv(input_path).iloc[:DAYS_TO_PLOT].copy()

    if "t_step" not in df.columns:
        raise ValueError(f"Missing column 't_step' in {input_path}")

    value_columns = [col for col in df.columns if col != "t_step"]
    if len(value_columns) == 0:
        raise ValueError(f"No salinity value column found in {input_path}")

    # The files contain one or more salinity value columns. For plotting the
    # scenario, use the first non-time column, as in the original script.
    value_column = value_columns[0]

    return pd.DataFrame(
        {
            "day": df["t_step"] / SECONDS_PER_DAY,
            "salinity_ppt": df[value_column] * 1000.0,
            "scenario": scenario,
            "label": SCENARIO_LABELS[scenario],
        }
    )


def load_plot_data():
    """Load all dynamic salinity scenarios."""
    data_frames = []
    for scenario in SCENARIO_ORDER:
        data_frames.append(read_salinity_file(scenario, SCENARIO_FILES[scenario]))
    return pd.concat(data_frames, ignore_index=True)


def main():
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["DejaVu Sans", "Arial"],
            "font.size": 9,
            "axes.labelsize": 9,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 7,
            "axes.linewidth": 0.8,
        }
    )

    df_long = load_plot_data()

    fig, ax = plt.subplots(figsize=(7.2, 3.8))

    for scenario in SCENARIO_ORDER:
        subset = df_long[df_long["scenario"] == scenario]
        ax.plot(
            subset["day"],
            subset["salinity_ppt"],
            label=SCENARIO_LABELS[scenario],
            color=SCENARIO_COLORS[scenario],
            linestyle=SCENARIO_LINESTYLES[scenario],
            linewidth=1.2,
        )

    ax.set_xlabel("Day of year")
    ax.set_ylabel("Porewater salinity [ppt]")
    ax.set_xlim(0, 365)
    ax.set_xticks(np.arange(0, 361, 60))
    ax.grid(True, alpha=0.35, linewidth=0.7)

    ax.legend(
        title="Scenario",
        frameon=True,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.27),
        ncol=3,
        title_fontsize=8,
    )

    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=300, bbox_inches="tight")
    fig.savefig(OUT_PDF, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved: {OUT_PNG}")
    print(f"Saved: {OUT_PDF}")


if __name__ == "__main__":
    main()
