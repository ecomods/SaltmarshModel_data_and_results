# -*- coding: utf-8 -*-
"""
PROTOTYPE / exploration for Figure 3.1 (static community vs monoculture).

Goal: make the *competition* question - does each PFT grow more or less in the
community than as a monoculture? - directly readable.

Produces two candidate figures in figures/figures_selina/:

    Option A: per-PFT small multiples (2x2). For each PFT, community contribution
              vs monoculture biovolume, grouped bars + min-max replicate range,
              per-panel y-axis.

    Option B: relative yield (community / monoculture) vs salinity, one line per
              PFT, reference line at 1 (= no competition effect).

Nothing here touches the manuscript pipeline; it only reads the prepared tables.
"""

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import importlib

import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

# Shared figure modules live one level up in source/.
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
# Data: median + min/max replicate range for community and monoculture
# =============================================================================
# Convention matches the manuscript: median over time per replicate, then
# median / min / max across replicates.

def summarise(replicate_df, value_col="total_volume"):
    """salinity x pft -> median/min/max across replicates."""
    g = (
        replicate_df.groupby(["salinity", "pft"])[value_col]
        .agg(median="median", lo="min", hi="max")
        .reset_index()
    )
    return g


# Community: replicate-level totals are already prepared.
grouped_pft = pd.read_csv(os.path.join(DERIVED_DIR, "grouped_pft_static.csv"))
comm_sum = summarise(grouped_pft, "total_volume")

# Monoculture: compute replicate medians from the prepared monoculture frame.
df_mono = pd.read_csv(os.path.join(DERIVED_DIR, "df_mono_prepared.csv"))
mono_per_ts = (
    df_mono.groupby(["salinity", "pft", "n", "time"])["volume"]
    .sum()
    .reset_index(name="total_volume")
)
mono_rep = (
    mono_per_ts.groupby(["salinity", "pft", "n"])["total_volume"]
    .median()
    .reset_index()
)
mono_sum = summarise(mono_rep, "total_volume")


def lookup(summary, sal, pft):
    """Return (median, lo, hi); zeros if the combination is absent."""
    row = summary[(summary["salinity"] == sal) & (summary["pft"] == pft)]
    if row.empty:
        return 0.0, 0.0, 0.0
    r = row.iloc[0]
    return float(r["median"]), float(r["lo"]), float(r["hi"])


# =============================================================================
# Option A: per-PFT small multiples
# =============================================================================

fig_a, axes = plt.subplots(2, 2, figsize=(7.0, 5.2))
x = np.arange(len(SAL_STATIC))
w = 0.38

for ax, pft in zip(axes.flat, PFTS):
    color = pft_color_map[pft]

    comm_med, comm_lo, comm_hi, mono_med, mono_lo, mono_hi = ([] for _ in range(6))
    for sal in SAL_STATIC:
        m, lo, hi = lookup(comm_sum, sal, pft)
        comm_med.append(m); comm_lo.append(m - lo); comm_hi.append(hi - m)
        m, lo, hi = lookup(mono_sum, sal, pft)
        mono_med.append(m); mono_lo.append(m - lo); mono_hi.append(hi - m)

    ax.bar(x - w / 2, comm_med, width=w, color=color, edgecolor="black",
           linewidth=0.5, label="community",
           yerr=[comm_lo, comm_hi], capsize=2,
           error_kw=dict(lw=0.6, capthick=0.6))
    ax.bar(x + w / 2, mono_med, width=w, color=color, edgecolor="black",
           linewidth=0.5, hatch="///", label="monoculture",
           yerr=[mono_lo, mono_hi], capsize=2,
           error_kw=dict(lw=0.6, capthick=0.6))

    ax.set_title(f"PFT {pft}", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels([str(s) for s in SAL_STATIC])
    ax.grid(axis="y", linestyle=":", linewidth=0.6, alpha=0.8)
    ax.set_ylim(bottom=0)

fig_a.supxlabel("Salinity [ppt]", fontsize=9)
fig_a.supylabel("Total biovolume [m³]", fontsize=9)

legend_handles = [
    Patch(facecolor="white", edgecolor="black", label="community"),
    Patch(facecolor="white", edgecolor="black", hatch="///", label="monoculture"),
]
fig_a.legend(handles=legend_handles, loc="upper center", ncol=2,
             bbox_to_anchor=(0.5, 1.02), frameon=False)

fig_a.tight_layout(rect=(0.02, 0.02, 1, 0.97))
out_a = os.path.join(output_dir, "plot_3_1_ALT_A_per_pft.png")
fig_a.savefig(out_a, dpi=200, bbox_inches="tight")


# =============================================================================
# Option B: relative yield (community / monoculture)
# =============================================================================

comm_mat = pd.read_csv(os.path.join(DERIVED_DIR, "comm_mat.csv"), index_col=0)
mono_mat = pd.read_csv(os.path.join(DERIVED_DIR, "mono_mat.csv"), index_col=0)
comm_mat.index = comm_mat.index.astype(int); comm_mat.columns = comm_mat.columns.astype(int)
mono_mat.index = mono_mat.index.astype(int); mono_mat.columns = mono_mat.columns.astype(int)

ratio = comm_mat / mono_mat.replace(0, np.nan)  # NaN where the PFT cannot grow alone

fig_b, axb = plt.subplots(figsize=(5.0, 3.6))
axb.axhline(1.0, color="0.4", linestyle="--", linewidth=0.8)
for pft in PFTS:
    axb.plot(SAL_STATIC, ratio.loc[SAL_STATIC, pft].values, marker="o",
             color=pft_color_map[pft], label=f"PFT {pft}")

axb.set_xlabel("Salinity [ppt]")
axb.set_ylabel("Relative yield\n(community / monoculture)")
axb.set_xticks(SAL_STATIC)
axb.set_ylim(bottom=0)
axb.grid(axis="y", linestyle=":", linewidth=0.6, alpha=0.8)
axb.legend(bbox_to_anchor=(1.02, 1), loc="upper left", frameon=False)
axb.annotate("= no competition effect", xy=(SAL_STATIC[0], 1.0),
             xytext=(0, 4), textcoords="offset points", fontsize=7, color="0.4")

fig_b.tight_layout()
out_b = os.path.join(output_dir, "plot_3_1_ALT_B_relative_yield.png")
fig_b.savefig(out_b, dpi=200, bbox_inches="tight")

print("Saved:", out_a)
print("Saved:", out_b)

plt.show()
