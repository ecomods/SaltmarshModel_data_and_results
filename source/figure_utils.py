"""
Reusable helper functions for data preparation and figure generation.

The helper functions fall into four groups:

1. Species parameters: load_species_parameters() and forman_response().
2. Plant data: load_static_community(), load_static_monoculture() and
   load_dynamic_community() return the cleaned plant rows of the model runs
   and can be used for new analyses and figures.
3. Summary functions used to create derived figure tables and error bars.
4. Shared plotting functions used by several figure scripts.
"""

import functools
import importlib.util

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import figure_config as config
from paths import MODEL_OUTPUT, SPECIES_DIR


# =============================================================================
# Species parameters
# =============================================================================

def load_species_parameters(pft):
    """Return the parameter dictionary of the model input Saltmarsh_<pft>.py."""
    path = SPECIES_DIR / f"Saltmarsh_{pft}.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _geometry, parameter = module.createPlant()
    return parameter


def forman_response(salinity, u_i, d):
    """Belowground resource factor (Forman logistic function); salinity in ppt."""
    return 1.0 / (1.0 + np.exp(d * (u_i - salinity)))


# =============================================================================
# Plant data
# =============================================================================

REPLICATES = range(1, 11)
DYNAMIC_VARIANTS = ["V1", "V2"]

# Plants younger than 10 days (seedlings) are excluded from all analyses.
MIN_AGE_SECONDS = 10 * 86400


def read_population(path):
    """
    Read one pyMANGA Population.csv (one row per plant and output step).

    The model's own salinity column (salinity at the plant) is kept as
    plant_salinity, because salinity is used for the scenario value.
    """
    return pd.read_csv(path, sep="\t").rename(columns={"salinity": "plant_salinity"})


def clean_plant_data(df):
    """
    Add PFT and geometry-derived volumes, and remove seedlings.

    volume replaces the model's volume column by the sum of the above- and
    belowground cylinder volumes; ag_bg_ratio is the ratio for each plant.
    """
    df["ag_volume"] = np.pi * df["r_ag"] ** 2 * df["h_ag"]
    df["bg_volume"] = np.pi * df["r_bg"] ** 2 * df["h_bg"]
    df["volume"] = df["ag_volume"] + df["bg_volume"]
    df["ag_bg_ratio"] = df["ag_volume"] / df["bg_volume"]
    # Plant names look like Saltmarsh_<PFT>_<id>.
    df["pft"] = df["plant"].str.split("_").str[1].astype(int)
    return df[df["age"] >= MIN_AGE_SECONDS].copy()


def load_static_community():
    """Cleaned plant rows of the static community runs, with salinity and n."""
    tables = []
    for salinity in config.SAL_STATIC:
        for n in REPLICATES:
            path = (MODEL_OUTPUT / "community" / "static" / f"{salinity / 1000:.3f}"
                    / f"{n:02d}" / "Population.csv")
            tables.append(read_population(path).assign(salinity=salinity, n=n))
    return clean_plant_data(pd.concat(tables, ignore_index=True))


def load_static_monoculture():
    """Cleaned plant rows of the static monoculture runs, with salinity and n."""
    tables = []
    for salinity in config.SAL_STATIC:
        for pft in config.PFTS:
            for n in REPLICATES:
                path = (MODEL_OUTPUT / "monoculture" / "static" / f"{salinity / 1000:.3f}"
                        / f"PFT_{pft}" / f"{n:02d}" / "Population.csv")
                tables.append(read_population(path).assign(salinity=salinity, n=n))
    return clean_plant_data(pd.concat(tables, ignore_index=True))


def load_dynamic_community():
    """
    Cleaned plant rows of the dynamic community runs (V1 and V2), with
    salinity (mean of the scenario), variant, version (e.g. "35_V1") and n.
    """
    tables = []
    for salinity in config.SAL_DYN:
        for variant in DYNAMIC_VARIANTS:
            version = f"{salinity}_{variant}"
            for n in REPLICATES:
                path = MODEL_OUTPUT / "community" / "dynamic" / version / f"{n:02d}" / "Population.csv"
                tables.append(read_population(path).assign(
                    salinity=salinity, variant=variant, version=version, n=n,
                ))
    return clean_plant_data(pd.concat(tables, ignore_index=True))


# =============================================================================
# Summary helpers
# =============================================================================

def complete_grid(summary_df, sal_levels, pft_levels):
    """Return a complete salinity x PFT matrix, filling missing combinations with 0."""
    grid = (
        pd.MultiIndex.from_product([sal_levels, pft_levels], names=["salinity", "pft"])
        .to_frame(index=False)
        .merge(summary_df, on=["salinity", "pft"], how="left")
    )
    grid["value"] = grid["value"].fillna(0.0)
    return (
        grid.pivot(index="salinity", columns="pft", values="value")
        .reindex(sal_levels)[pft_levels]
    )


@functools.cache
def output_times():
    """
    Output times (s) of the community and monoculture runs: every 10th day in
    years 5-10 and the last time step. All these runs have the same output
    times, so they are read from one run (all rows, including seedlings).
    """
    path = MODEL_OUTPUT / "community" / "static" / "0.035" / "01" / "Population.csv"
    return tuple(np.sort(pd.read_csv(path, sep="\t", usecols=["time"])["time"].unique()))


def fill_missing_steps(per_step, levels):
    """
    Add the output steps without plants to a per-step table.

    pyMANGA writes one row per living plant, so an output step without plants
    (after removing seedlings) has no rows and would be skipped in time means.
    per_step is indexed by the names in levels, n and time; levels maps each
    name to all its values (e.g. {"salinity": [35, 70], "pft": [1, 2]}). The
    added steps get 0 total biovolume and 0 plants; per-plant metrics stay
    NaN, because they are undefined without plants.
    """
    index = pd.MultiIndex.from_product(
        [*levels.values(), REPLICATES, output_times()],
        names=[*levels, "n", "time"],
    )
    if not per_step.index.isin(index).all():
        raise ValueError("Per-step table has rows outside the expected runs or output times.")
    filled = per_step.reindex(index)
    for col in ["total_volume", "num_plants"]:
        if col in filled.columns:
            filled[col] = filled[col].fillna(0.0)
    return filled


def replicate_time_means(df, levels):
    """
    One mean-over-time value per scenario, PFT and replicate.

    levels maps the scenario columns to all their values, e.g.
    {"salinity": config.SAL_STATIC}. For each output step: total biovolume
    (sum over plants), mean biovolume per plant, mean height and mean AG/BG
    ratio of the plants, and number of plants. Steps without plants count as
    0 total biovolume and 0 plants; the per-plant metrics are averaged only
    over steps with plants. The values are then averaged over the output
    steps of each replicate. Returns the table by PFT and the table for the
    whole community (pft = 0). summary_mean_std() then summarises across
    replicates.
    """
    def per_replicate(group_levels):
        group_cols = list(group_levels)
        per_step = (
            df.groupby(group_cols + ["n", "time"], observed=True)
            .agg(
                total_volume=("volume", "sum"),
                volume_per_plant=("volume", "mean"),
                h_ag=("h_ag", "mean"),
                ag_bg_ratio=("ag_bg_ratio", "mean"),
                num_plants=("volume", "size"),
            )
        )
        per_step = fill_missing_steps(per_step, group_levels)
        # mean() skips NaN, so per-plant metrics use only steps with plants.
        return per_step.groupby(group_cols + ["n"]).mean().reset_index()

    by_pft = per_replicate({**levels, "pft": config.PFTS})
    community = per_replicate(levels)
    community["pft"] = 0
    return by_pft, community


def summary_minmax_mean(grouped_df, keys, metric):
    """
    Calculate mean and min/max range for a metric within grouped data.

    Returned columns:
        mean_value, min_value, max_value, err_lower, err_upper
    """
    summary = (
        grouped_df.groupby(keys)[metric]
        .agg(mean_value="mean", min_value="min", max_value="max")
        .reset_index()
    )
    summary["err_lower"] = summary["mean_value"] - summary["min_value"]
    summary["err_upper"] = summary["max_value"] - summary["mean_value"]
    return summary


def summary_mean_std(grouped_df, keys, metric):
    """
    Calculate mean and standard deviation across replicate-level values.

    The input table must contain one value per replicate and scenario. The
    returned error bars are symmetric and represent one standard deviation
    across the available replicates.
    """
    summary = (
        grouped_df.groupby(keys)[metric]
        .agg(mean_value="mean", std_value="std")
        .reset_index()
    )
    summary["std_value"] = summary["std_value"].fillna(0.0)
    summary["err_lower"] = summary["std_value"]
    summary["err_upper"] = summary["std_value"]
    return summary


def mean_ts(df, col):
    """Return mean time series across replicates for one per-timestep metric."""
    return (
        df.groupby(["version", "pft", "time_days"], observed=True)[col]
        .mean()
        .reset_index(name="value")
    )


# =============================================================================
# Shared plotting
# =============================================================================

def center_label_under(fig, axes_row, label):
    """
    Replace the x-axis labels of axes_row by one label centred below them.

    Must be called after all other layout elements exist: the figure is laid
    out once, then the layout is frozen so the space reserved for the
    (now hidden) axis labels is kept.
    """
    for ax in axes_row:
        ax.set_xlabel(label)
    fig.canvas.draw()
    fig.set_layout_engine("none")

    to_fig = fig.transFigure.inverted()
    y = to_fig.transform(axes_row[0].xaxis.label.get_window_extent())[:, 1].mean()
    x = (axes_row[0].get_position().x0 + axes_row[-1].get_position().x1) / 2
    for ax in axes_row:
        ax.xaxis.label.set_visible(False)
    fig.text(x, y, label, ha="center", va="center",
             fontsize=axes_row[0].xaxis.label.get_fontsize(),
             color=axes_row[0].xaxis.label.get_color())


# Plant-structure metrics of Figs. 3 and S3 and their y-axis labels, in panel
# order a)-d).
STRUCTURE_YLABELS = {
    "volume_per_plant": "Biovolume per plant (m³)",
    "h_ag": "Aboveground height (m)",
    "ag_bg_ratio": "AG/BG ratio (–)",
    "num_plants": "Number of plants",
}


def structure_summaries(grouped_pft, grouped_all=None):
    """
    Replicate mean and standard deviation of each plant-structure metric.

    The tables contain one mean-over-time value per scenario and replicate
    (see replicate_time_means()), so standard deviations are calculated
    across replicates. Returns {metric: (summary_pft, summary_all)} for
    draw_structure_figure(); summary_all is None without a community table.
    """
    summaries = {}
    for metric in STRUCTURE_YLABELS:
        summary_pft = summary_mean_std(grouped_pft, ["salinity", "pft"], metric)
        summary_all = None
        if grouped_all is not None:
            summary_all = summary_mean_std(grouped_all, ["salinity"], metric)
        summaries[metric] = (summary_pft, summary_all)
    return summaries


def draw_structure_figure(summaries, group_spacing=3.8):
    """
    Draw the 2 x 2 point/error-bar figure of plant-structure metrics
    (Figs. 3 and S3) in the shared style and return the figure.

    summaries comes from structure_summaries(). Within each salinity group,
    points are placed in the order community (if summary_all is given),
    PFT 1, ..., PFT 4. Salinity groups are separated by a wider gap
    (group_spacing) and alternating light-grey background bands. The legend
    sits in the top-right panel.
    """
    salinity_levels = config.SAL_STATIC
    pft_levels = config.PFTS
    show_community = next(iter(summaries.values()))[1] is not None

    x_group = np.arange(len(salinity_levels)) * group_spacing
    sal_to_x = {sal: x_group[i] for i, sal in enumerate(salinity_levels)}

    n_series = len(pft_levels) + (1 if show_community else 0)
    within_offsets = np.array([0.0, 0.55, 1.10, 1.65, 2.20])[:n_series]
    first_pft_slot = 1 if show_community else 0

    group_centers = x_group + np.mean(within_offsets)

    def draw_series(ax, summary, x_offset, color, label):
        ax.errorbar(
            summary["salinity"].map(sal_to_x) + x_offset,
            summary["mean_value"],
            yerr=[summary["err_lower"], summary["err_upper"]],
            fmt="o",
            markersize=4,
            capsize=2,
            linewidth=0.8,
            color=color,
            label=label,
        )

    fig, axes = plt.subplots(
        nrows=2,
        ncols=2,
        figsize=config.figsize_mm(config.WIDTH_FULL_MM, 110),
        sharex=True,
    )

    for i_panel, (ax, metric) in enumerate(zip(axes.ravel(), STRUCTURE_YLABELS)):
        summary_pft, summary_all = summaries[metric]

        if show_community:
            draw_series(ax, summary_all, within_offsets[0], "black", "Community")

        for i, pft in enumerate(pft_levels, start=first_pft_slot):
            draw_series(ax, summary_pft[summary_pft["pft"] == pft], within_offsets[i],
                        config.pft_color_map[pft], f"PFT {pft}")

        ax.set_xticks(group_centers, [str(s) for s in salinity_levels])
        # Only the bottom row gets an x-axis label.
        if i_panel >= 2:
            ax.set_xlabel("Salinity (ppt)")
        ax.set_ylabel(STRUCTURE_YLABELS[metric])

        ax.set_axisbelow(True)
        ax.grid(axis="y", linewidth=0.5, alpha=0.4)

    config.add_panel_labels(axes.ravel())

    # Legend inside the top-right panel, using the handles drawn there.
    axes[0, 1].legend(loc="upper right")

    # Add bands after all series have set the shared x-limits. Boundaries lie
    # halfway between scenario centres; shading must not expand the axes.
    xlim = axes[0, 0].get_xlim()
    boundaries = np.r_[xlim[0], (group_centers[:-1] + group_centers[1:]) / 2, xlim[1]]
    for ax in axes.ravel():
        ax.set_xlim(xlim)
    for ax in axes.ravel():
        for index in range(0, len(group_centers), 2):
            band = ax.axvspan(boundaries[index], boundaries[index + 1],
                             facecolor="0.95", edgecolor="none", zorder=-1)
            band.set_in_layout(False)

    return fig
