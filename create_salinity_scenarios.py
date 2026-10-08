"""
Generate daily porewater salinity scenarios and display them as in Figure S2.

Seasonal amplitudes are estimated from hourly model salinity and used to build
one year for 35 and 70 ppt, seasonal (V1) and seasonal + tide (V2). Each year
is rescaled to its target mean within 0-200 ppt (105 ppt: the 70 ppt curves
rescaled) and repeated 20 times. Calculations and CSVs use kg/kg, the plot
uses ppt.

The files in model_input/salinity/ are the inputs of the published
simulations. This script calculates without their intermediate rounding
(differences up to 4.5e-5 ppt) and overwrites them when run, so only run it
to create new scenarios.

Input:  model_input/salinity_from_model.npz
Output: model_input/salinity/{35,70,105}_{V1,V2}.csv

Usage (from the repository root):
    python create_salinity_scenarios.py
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from source.paths import MODEL_INPUT, SALINITY_DIR

NPZ_FILE = MODEL_INPUT / "salinity_from_model.npz"

ELEVATION = 4.50  # m
YEARS = 20


def seasonal_amplitudes():
    """
    Negative and positive seasonal amplitude (kg/kg) at ELEVATION, from the
    hourly extremes in the first soil layer at three elevations.
    """
    with np.load(NPZ_FILE) as data:
        heights = np.array([4.60, 4.90, 5.20])
        indices = [np.flatnonzero(data["heightlevels"] == height)[0] for height in heights]
        salinity = data["clay_array"][indices, :, 0]

    negative_deviation = 0.035 - salinity.min(axis=1)
    positive_deviation = salinity.max(axis=1) - 0.035
    negative_slope, negative_intercept = np.polyfit(heights, negative_deviation, 1)
    positive_slope, positive_intercept = np.polyfit(heights, positive_deviation, 1)
    return (negative_intercept + ELEVATION * negative_slope,
            positive_intercept + ELEVATION * positive_slope)


def rescale_salinity(values, target_mean):
    """Shift to target_mean and scale to the largest amplitude within 0-0.2 kg/kg."""
    centered = values - values.mean()
    scale = min(target_mean / -centered.min(), (0.2 - target_mean) / centered.max())
    return target_mean + scale * centered


def annual_cycles(negative_amplitude, positive_amplitude):
    """One year of daily salinity (kg/kg) per scenario, e.g. "35_V1"."""
    days = np.arange(365)
    wave = np.sin((days - 219) / 365 * 2 * np.pi)
    seasonal_deviation = wave * np.where(wave <= 0, negative_amplitude, positive_amplitude)
    period = round(365 / 26)
    tidal_exponent = 2e11 * np.exp(-5.297 * ELEVATION)
    # A 14-day tidal cycle pulls salinity toward the baseline between seasonal peaks.
    tidal_weight = (((days + 7) % period) / (period - 1)) ** tidal_exponent

    annual = {}
    for ppt in (35, 70):
        baseline = ppt / 1000
        seasonal = np.maximum(0, baseline + seasonal_deviation)
        tidal = np.maximum(0, baseline + tidal_weight * (seasonal - baseline))
        for regime, values in {"V1": seasonal, "V2": tidal}.items():
            annual[f"{ppt}_{regime}"] = rescale_salinity(values, baseline)
    for regime in ("V1", "V2"):
        annual[f"105_{regime}"] = rescale_salinity(annual[f"70_{regime}"], 0.105)
    return annual


def write_scenarios(annual, output_dir):
    """Repeat each year YEARS times and write one CSV per scenario."""
    output_dir.mkdir(parents=True, exist_ok=True)
    tables = {}
    for name, values in annual.items():
        values = np.tile(values, YEARS)
        # pyMANGA reads the columns by position (time, left and right boundary).
        # The different names match the committed inputs.
        boundaries = ("salinity_1", "salinity_2") if name.startswith("105_") else ("V1", "V27")
        table = pd.DataFrame({
            "t_step": np.arange(len(values)) * 86400,
            boundaries[0]: values,
            boundaries[1]: values,
        })
        path = output_dir / f"{name}.csv"
        table.to_csv(path, index=False, float_format="%.17g")
        print(f"Saved: {path}")
        tables[name] = table
    return tables


def plot_scenarios(tables):
    """One panel per mean salinity with all three regimes."""
    fig, axes = plt.subplots(3, 1, sharex=True, sharey=True, figsize=(8, 6),
                             layout="constrained")
    plot_days = np.arange(366)
    for ax, ppt in zip(axes, (35, 70, 105)):
        ax.plot(plot_days, np.full(366, ppt), label="Static (V0)")
        for regime, label in (("V1", "Seasonal (V1)"), ("V2", "Seasonal + tide (V2)")):
            # Day 365 is the first day of the repeated year.
            values = tables[f"{ppt}_{regime}"].iloc[:366, 1].to_numpy() * 1000
            ax.plot(plot_days, values, label=label)
        ax.set_xlim(0, 365)
        ax.set_ylim(0, 210)
        ax.set_xticks(np.arange(0, 361, 60))
        ax.set_ylabel(f"{ppt} ppt")
        ax.yaxis.set_label_position("right")
    axes[-1].set_xlabel("Day of year")
    fig.supylabel("Porewater salinity (ppt)")
    fig.legend(*axes[0].get_legend_handles_labels(), loc="outside lower center", ncols=3)
    plt.show()


def main():
    tables = write_scenarios(annual_cycles(*seasonal_amplitudes()), SALINITY_DIR)
    plot_scenarios(tables)


if __name__ == "__main__":
    main()
