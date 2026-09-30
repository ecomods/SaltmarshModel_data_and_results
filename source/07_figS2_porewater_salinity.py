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

import figure_config as config
from paths import FIGURES_APPENDIX, SALINITY_DIR

OUT_PNG = FIGURES_APPENDIX / "figS2_porewater_salinity.png"

SALINITIES = config.SAL_DYN
DYNAMIC_REGIMES = ["V1", "V2"]
REGIMES = ["V0"] + DYNAMIC_REGIMES

SECONDS_PER_DAY = 86400.0
DAYS_TO_PLOT = 366


def read_salinity_file(salinity, regime):
    """Read one dynamic salinity input file as days and salinity in ppt."""
    df = pd.read_csv(SALINITY_DIR / f"{salinity}_{regime}.csv").iloc[:DAYS_TO_PLOT]
    # Columns: t_step (s) and two identical salinity columns (kg/kg); plot the first.
    return df["t_step"] / SECONDS_PER_DAY, df.iloc[:, 1] * 1000.0


def main():
    config.apply_style()

    fig, axes = plt.subplots(
        nrows=len(SALINITIES),
        ncols=1,
        figsize=config.figsize_mm(config.WIDTH_FULL_MM, 120),
        sharex=True,
        sharey=True,
    )

    y_max = 0.0
    for ax, salinity in zip(axes, SALINITIES):
        # Static regime: constant salinity at the mean value.
        ax.axhline(salinity, color=config.regime_color_map["V0"],
                   linewidth=config.REGIME_LINEWIDTH)

        for regime in DYNAMIC_REGIMES:
            day, salinity_ppt = read_salinity_file(salinity, regime)
            ax.plot(day, salinity_ppt, color=config.regime_color_map[regime],
                    linewidth=config.REGIME_LINEWIDTH)
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
        Line2D([], [], color=config.regime_color_map[regime],
               linewidth=config.REGIME_LINEWIDTH, label=config.REGIME_LABELS[regime])
        for regime in REGIMES
    ]
    # Legend below the panels, as in Fig. S1.
    legend = fig.legend(handles=handles, title="Salinity regime",
                        loc="outside lower center", ncols=len(handles))
    legend.set_alignment("left")

    config.save_figure(fig, OUT_PNG)
    plt.close(fig)


if __name__ == "__main__":
    main()
