"""
Figure S2: porewater salinity in the three salinity regimes.

One panel per mean salinity (35, 70, 105 ppt), showing the first year of the
static (constant), seasonal (V1) and seasonal + tide (V2) input.

Input:  data_model_input/salinity/{35,70,105}_{V1,V2}.csv
Output: figures/appendix/figS2_porewater_salinity.png
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

import figure_config as _config
from source.utils.paths import FIGURES_APPENDIX, SALINITY_DIR


# =============================================================================
# Settings
# =============================================================================

OUT_DIR = FIGURES_APPENDIX
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_PNG = OUT_DIR / "figS2_porewater_salinity.png"

SALINITIES = _config.SAL_DYN
DYNAMIC_REGIMES = ["V1", "V2"]
REGIMES = ["V0"] + DYNAMIC_REGIMES

SECONDS_PER_DAY = 86400.0
DAYS_TO_PLOT = 366


# =============================================================================
# Functions
# =============================================================================

def read_salinity_file(salinity, regime):
    """Read one dynamic salinity input file as days and salinity in ppt."""
    input_path = SALINITY_DIR / f"{salinity}_{regime}.csv"
    if not input_path.is_file():
        raise FileNotFoundError(f"Missing salinity input file: {input_path}")

    df = pd.read_csv(input_path).iloc[:DAYS_TO_PLOT].copy()

    if "t_step" not in df.columns:
        raise ValueError(f"Missing column 't_step' in {input_path}")

    value_columns = [col for col in df.columns if col != "t_step"]
    if len(value_columns) == 0:
        raise ValueError(f"No salinity value column found in {input_path}")

    # The files have two identical salinity columns; plot the first.
    value_column = value_columns[0]

    return df["t_step"] / SECONDS_PER_DAY, df[value_column] * 1000.0


def main():
    _config.apply_style()

    fig, axes = plt.subplots(
        nrows=len(SALINITIES),
        ncols=1,
        figsize=_config.figsize_mm(_config.WIDTH_FULL_MM, 120),
        sharex=True,
        sharey=True,
    )

    y_max = 0.0
    for ax, salinity in zip(axes, SALINITIES):
        # Static regime: constant salinity at the mean value.
        ax.axhline(salinity, color=_config.regime_color_map["V0"],
                   linewidth=_config.REGIME_LINEWIDTH)

        for regime in DYNAMIC_REGIMES:
            day, salinity_ppt = read_salinity_file(salinity, regime)
            ax.plot(day, salinity_ppt, color=_config.regime_color_map[regime],
                    linewidth=_config.REGIME_LINEWIDTH)
            y_max = max(y_max, salinity_ppt.max())

        # Mean salinity as a row label at the right edge (as in Fig. 4).
        ax.yaxis.set_label_position("right")
        ax.set_ylabel(f"{salinity} ppt", rotation=270, va="bottom")

        ax.set_xlim(0, 365)
        ax.set_xticks(np.arange(0, 361, 60))
        ax.set_axisbelow(True)
        ax.grid(axis="y", linewidth=0.5, alpha=0.4)

    # Shared y-range covering all curves of all panels.
    axes[0].set_ylim(0, y_max * 1.05)

    # Tick marks only where there are tick labels (bottom row).
    for ax in axes[:-1]:
        ax.tick_params(axis="x", bottom=False)

    axes[-1].set_xlabel("Day of year")
    fig.supylabel("Porewater salinity (ppt)", fontsize="medium")

    handles = [
        Line2D([], [], color=_config.regime_color_map[regime],
               label=_config.REGIME_LABELS[regime])
        for regime in REGIMES
    ]
    # Legend below the panels, as in Fig. S1.
    legend = fig.legend(handles=handles, title="Salinity regime",
                        loc="outside lower center", ncols=len(handles))
    legend.set_alignment("left")

    _config.save_figure(fig, OUT_PNG)
    plt.close(fig)


if __name__ == "__main__":
    main()
