# -*- coding: utf-8 -*-
"""
PROTOTYPE / exploration for Figure 3.2 (static community structure).

Two candidate directions, to compare the kinds of variability we can show:

  Prototype 1 (consistent replicate summary):
      The same 2x2 metrics, but EVERY panel summarised the same way:
      per-replicate value (already in grouped_pft_static) -> median + IQR
      across the 10 replicates. Robust, consistent, answers "how reproducible".

  Prototype 2 (plant-size distribution):
      Biovolume per plant shown as the full distribution of individual plants,
      one observation per plant (each plant collapsed to its median over time,
      so a plant is not counted ~14x). One panel per PFT. Shows the
      "few large -> many small" structure directly.

Reads only prepared tables; writes PNGs to figures/figures_selina/.
"""

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import importlib

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

_SOURCE_DIR = Path(__file__).resolve().parent.parent
if str(_SOURCE_DIR) not in sys.path:
    sys.path.insert(0, str(_SOURCE_DIR))

_config = importlib.import_module("03_figure_config")
_utils = importlib.import_module("03_figure_utils")

SAL_STATIC = _config.SAL_STATIC
PFTS = _config.PFTS
pft_color_map = _config.pft_color_map
DERIVED_DIR = _config.DERIVED_DIR
FIGURES_MAIN = _config.FIGURES_MAIN
ensure_dir = _utils.ensure_dir

FIGURES_SELINA = os.path.join(os.path.dirname(FIGURES_MAIN), "figures_selina")
output_dir = ensure_dir(FIGURES_SELINA)


# =============================================================================
# Prototype 1: consistent across-replicate summary (median + IQR)
# =============================================================================
# grouped_pft_static / grouped_all_static already hold ONE value per replicate
# (median over time) for every metric, so we only summarise across replicates.

grouped_pft = pd.read_csv(os.path.join(DERIVED_DIR, "grouped_pft_static.csv"))
grouped_all = pd.read_csv(os.path.join(DERIVED_DIR, "grouped_all_static.csv"))

metrics = {
    "volume_per_plant": "Biovolume per plant [m³]",
    "h_ag": "Aboveground height [m]",
    "ag_bg_ratio": "AG/BG ratio [-]",
    "num_plants": "Number of plants",
}


def across_replicate(df, metric):
    """salinity x pft -> median + IQR (q25/q75) across replicates."""
    return (
        df.groupby(["salinity", "pft"])[metric]
        .agg(med="median",
             q25=lambda s: s.quantile(0.25),
             q75=lambda s: s.quantile(0.75))
        .reset_index()
    )


fig1, axes = plt.subplots(2, 2, figsize=(8.0, 6.0), sharex=True)
x = np.arange(len(SAL_STATIC))
within = np.linspace(-0.28, 0.28, len(PFTS) + 1)  # community + 4 PFTs

for ax, (metric, ylabel) in zip(axes.flat, metrics.items()):
    # community (pft == 0 in grouped_all)
    comm = across_replicate(grouped_all, metric)
    comm = comm.set_index("salinity").reindex(SAL_STATIC)
    ax.errorbar(x + within[0], comm["med"],
                yerr=[comm["med"] - comm["q25"], comm["q75"] - comm["med"]],
                fmt="o", ms=4, color="black", capsize=2,
                elinewidth=0.8, capthick=0.8, label="community")

    # per PFT
    pft_sum = across_replicate(grouped_pft, metric)
    for i, pft in enumerate(PFTS, start=1):
        d = pft_sum[pft_sum["pft"] == pft].set_index("salinity").reindex(SAL_STATIC)
        ax.errorbar(x + within[i], d["med"],
                    yerr=[d["med"] - d["q25"], d["q75"] - d["med"]],
                    fmt="o", ms=4, color=pft_color_map[pft], capsize=2,
                    elinewidth=0.8, capthick=0.8, label=f"PFT {pft}")

    ax.set_ylabel(ylabel, fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels([str(s) for s in SAL_STATIC])
    ax.grid(axis="y", linestyle=":", linewidth=0.5, alpha=0.8)
    ax.set_axisbelow(True)

for ax in axes[1, :]:
    ax.set_xlabel("Salinity [ppt]")

handles = [Line2D([0], [0], marker="o", linestyle="None", color="black", label="community")]
handles += [Line2D([0], [0], marker="o", linestyle="None",
                   color=pft_color_map[p], label=f"PFT {p}") for p in PFTS]
fig1.legend(handles=handles, loc="lower center", ncol=5, frameon=True,
            bbox_to_anchor=(0.5, -0.02))
fig1.suptitle("Prototype 1 — consistent across-replicate summary (median + IQR)", fontsize=10)
fig1.tight_layout(rect=(0, 0.05, 1, 0.97))
out1 = os.path.join(output_dir, "plot_3_2_ALT1_replicate_iqr.png")
fig1.savefig(out1, dpi=200, bbox_inches="tight")


# =============================================================================
# Prototype 2: plant-size distribution (one observation per plant)
# =============================================================================

df = pd.read_csv(os.path.join(DERIVED_DIR, "df_comm_prepared.csv"))
df["salinity"] = pd.to_numeric(df["salinity"], errors="coerce")
df["pft"] = pd.to_numeric(df["pft"], errors="coerce")

# Collapse each plant (per replicate) to its median-over-time volume so a plant
# is counted once, not ~14x. plant_uid is unique per replicate.
per_plant = (
    df.groupby(["salinity", "pft", "n", "plant_uid"])["volume"]
    .median()
    .reset_index(name="vol")
)

fig2, axes2 = plt.subplots(2, 2, figsize=(8.0, 6.0))
for ax, pft in zip(axes2.flat, PFTS):
    data, positions = [], []
    for j, sal in enumerate(SAL_STATIC):
        vals = per_plant[(per_plant.salinity == sal) & (per_plant.pft == pft)]["vol"].values
        if len(vals) >= 2:
            data.append(vals)
            positions.append(j)
    if data:
        parts = ax.violinplot(data, positions=positions, showmedians=True,
                              widths=0.8)
        for b in parts["bodies"]:
            b.set_facecolor(pft_color_map[pft]); b.set_alpha(0.6); b.set_edgecolor("black")
        for key in ("cbars", "cmins", "cmaxes", "cmedians"):
            if key in parts:
                parts[key].set_color("black"); parts[key].set_linewidth(0.8)
    ax.set_title(f"PFT {pft}", fontsize=9)
    ax.set_xticks(range(len(SAL_STATIC)))
    ax.set_xticklabels([str(s) for s in SAL_STATIC])
    ax.grid(axis="y", linestyle=":", linewidth=0.5, alpha=0.8)
    ax.set_axisbelow(True)

fig2.supxlabel("Salinity [ppt]", fontsize=9)
fig2.supylabel("Biovolume per plant [m³]  (one point per plant)", fontsize=9)
fig2.suptitle("Prototype 2 — individual-plant size distribution", fontsize=10)
fig2.tight_layout(rect=(0.02, 0.02, 1, 0.96))
out2 = os.path.join(output_dir, "plot_3_2_ALT2_plant_distribution.png")
fig2.savefig(out2, dpi=200, bbox_inches="tight")

print("Saved:", out1)
print("Saved:", out2)
plt.show()
