"""Generate six daily salinity inputs and display the scenarios as in Figure S2.

Input: source/salinity_from_model.npz. Output: model_input/salinity/.
Calculations and CSVs use kg/kg; the final plot uses ppt.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from paths import REPO_ROOT, SALINITY_DIR


# Estimate seasonal amplitudes from hourly extrema in the first soil layer.
with np.load(REPO_ROOT / "source" / "salinity_from_model.npz") as data:
    heights = np.array([4.60, 4.90, 5.20])
    indices = [np.flatnonzero(data["heightlevels"] == height)[0] for height in heights]
    salinity = data["clay_array"][indices, :, 0]

negative_deviation = 0.035 - salinity.min(axis=1)
positive_deviation = salinity.max(axis=1) - 0.035
negative_slope, negative_intercept = np.polyfit(heights, negative_deviation, 1)
positive_slope, positive_intercept = np.polyfit(heights, positive_deviation, 1)
elevation = 4.50
negative_amplitude = negative_intercept + elevation * negative_slope
positive_amplitude = positive_intercept + elevation * positive_slope

# One annual cycle, with separate amplitudes for negative and positive halves.
days = np.arange(365)
wave = np.sin((days - 219) / 365 * 2 * np.pi)
seasonal_deviation = wave * np.where(wave <= 0, negative_amplitude, positive_amplitude)
period = round(365 / 26)
tidal_exponent = 2e11 * np.exp(-5.297 * elevation)
# A 14-day tidal cycle pulls salinity toward the baseline between seasonal peaks.
tidal_weight = (((days + 7) % period) / (period - 1)) ** tidal_exponent


def rescale_salinity(values, target_mean):
    """Set the annual mean and the largest amplitude within 0-200 ppt."""
    centered = values - values.mean()
    scale = min(target_mean / -centered.min(), (0.2 - target_mean) / centered.max())
    return target_mean + scale * centered


# Generate 35/70 ppt curves; rescale the 70 ppt curves to mean 105 ppt.
annual = {}
for ppt in (35, 70):
    baseline = ppt / 1000
    seasonal = np.maximum(0, baseline + seasonal_deviation)
    tidal = np.maximum(0, baseline + tidal_weight * (seasonal - baseline))
    for regime, values in {"V1": seasonal, "V2": tidal}.items():
        annual[f"{ppt}_{regime}"] = rescale_salinity(values, baseline)
for regime in ("V1", "V2"):
    annual[f"105_{regime}"] = rescale_salinity(annual[f"70_{regime}"], 0.105)

# Repeat each year 20 times and export both identical spatial boundaries.
SALINITY_DIR.mkdir(exist_ok=True)
scenarios = {}
for name, values in annual.items():
    values = np.tile(values, 20)
    boundaries = ("salinity_1", "salinity_2") if name.startswith("105_") else ("V1", "V27")
    table = pd.DataFrame({
        "t_step": np.arange(len(values)) * 86400,
        boundaries[0]: values,
        boundaries[1]: values,
    })
    scenarios[name] = table
    table.to_csv(SALINITY_DIR / f"{name}.csv", index=False, float_format="%.17g")

# One panel per mean salinity, with shared axes and all three regimes.
fig, axes = plt.subplots(3, 1, sharex=True, sharey=True, figsize=(8, 6), layout="constrained")
plot_days = np.arange(366)
for ax, ppt in zip(axes, (35, 70, 105)):
    ax.plot(plot_days, np.full(366, ppt), label="Static (V0)")
    for regime, label in (("V1", "Seasonal (V1)"), ("V2", "Seasonal + tide (V2)")):
        # Day 365 is the first day of the repeated year.
        values = scenarios[f"{ppt}_{regime}"].iloc[:366, 1].to_numpy() * 1000
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
