"""
Figure S1: potential growth and maintenance costs over plant height.

For each PFT, daily potential growth at the four static salinities and daily
maintenance costs are calculated for a single plant with fixed geometry
(radii and belowground height proportional to aboveground height). Points
mark where growth equals maintenance (potential height, Table S1).

Input:  model_input/species/Saltmarsh_{1-4}.py
Output: figures/appendix/figS1_growth_vs_maintenance.png
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

import figure_config as config
import figure_utils as utils
from paths import FIGURES_APPENDIX

OUT_PNG = FIGURES_APPENDIX / "figS1_growth_vs_maintenance.png"

TIME = 86400.0  # one day in seconds
SALINITIES = config.SAL_STATIC

H_AG_MIN = 0.0
H_AG_MAX = 1.85
N_POINTS = 1000

SALINITY_COLORS = config.salinity_color_map


# =============================================================================
# Functions
# =============================================================================

def calculate_geometry(h_ag, p_ratio_ag, p_ratio_bg):
    """Calculate AG and BG cylinder geometry from above-ground height."""
    r_ag = p_ratio_ag * h_ag
    h_bg = h_ag.copy()
    r_bg = p_ratio_bg * h_bg

    v_ag = np.pi * r_ag**2 * h_ag
    v_bg = np.pi * r_bg**2 * h_bg
    volume = v_ag + v_bg

    return {
        "h_ag": h_ag,
        "r_ag": r_ag,
        "h_bg": h_bg,
        "r_bg": r_bg,
        "v_ag": v_ag,
        "v_bg": v_bg,
        "volume": volume,
    }


def calculate_maintenance(volume, p_maint):
    """Calculate maintenance costs for one time step."""
    return volume * p_maint * TIME


def calculate_growth_pot(geometry, salinity, params):
    """Calculate potential growth for a given PFT and salinity."""
    aboveground_factor = 1.0

    belowground_factor = utils.forman_response(
        salinity,
        u_i=params["salt_effect_ui"],
        d=params["salt_effect_d"],
    )

    res_ag = (
        aboveground_factor
        * np.pi
        * geometry["r_ag"] ** 2
        * params["p_sun"]
        * TIME
    )

    denominator = geometry["h_ag"] + 0.5 * geometry["h_bg"]
    denominator = np.where(denominator <= 0, np.nan, denominator)

    res_bg = (
        belowground_factor
        * geometry["v_bg"]
        * params["p_sun"]
        * params["p_conv,bg"]
        * (1.0 / denominator)
        * TIME
    )

    res_eff = np.minimum(res_ag, res_bg)
    grow_pot = res_eff * params["p_grow"]

    return np.nan_to_num(grow_pot, nan=0.0)


def find_intersection(x, y1, y2):
    """Find the first non-trivial intersection between two curves."""
    diff = y1 - y2
    sign_change_idx = np.where(np.diff(np.sign(diff)) != 0)[0]
    sign_change_idx = [idx for idx in sign_change_idx if x[idx] > 0.01]

    if len(sign_change_idx) == 0:
        return None

    idx = sign_change_idx[0]
    x0, x1 = x[idx], x[idx + 1]
    y0, y1_diff = diff[idx], diff[idx + 1]

    if y1_diff == y0:
        x_intersection = x0
    else:
        x_intersection = x0 - y0 * (x1 - x0) / (y1_diff - y0)

    y_intersection = np.interp(x_intersection, x, y1)

    return x_intersection, y_intersection


def prepare_pft_data(pft, h_ag):
    """Calculate maintenance, potential growth, and intersections for one PFT."""
    params = utils.load_species_parameters(pft)

    geometry = calculate_geometry(
        h_ag,
        p_ratio_ag=params["p_ratio_ag"],
        p_ratio_bg=params["p_ratio_bg"],
    )

    maintenance = calculate_maintenance(
        geometry["volume"],
        p_maint=params["p_maint"],
    )

    growth_curves = {}
    intersections = {}

    for salinity in SALINITIES:
        growth_pot = calculate_growth_pot(
            geometry,
            salinity,
            params,
        )

        growth_curves[salinity] = growth_pot
        intersections[salinity] = find_intersection(
            h_ag,
            maintenance,
            growth_pot,
        )

    return {
        "params": params,
        "maintenance": maintenance,
        "growth_curves": growth_curves,
        "intersections": intersections,
    }


def panel_title(pft, p_maint):
    """Panel title with the maintenance parameter in scientific notation."""
    mantissa, exponent = f"{p_maint:.2e}".split("e")
    return (
        rf"PFT {pft} ($p_{{\mathrm{{maint}}}}$ = {mantissa} × "
        rf"10$^{{{int(exponent)}}}$)"
    )


def add_growth_legend(fig):
    """
    Salinity colours under the header "Potential growth at", below the
    panels. Added before the layout is frozen so its space is reserved.
    """
    growth_handles = [
        Line2D([], [], color=SALINITY_COLORS[sal], label=f"{sal} ppt")
        for sal in SALINITIES
    ]
    growth_legend = fig.legend(
        handles=growth_handles,
        title="Potential growth at",
        loc="outside lower center",
        ncols=len(growth_handles),
    )
    growth_legend.set_alignment("left")
    return growth_legend


def add_maintenance_legend(fig, growth_legend):
    """
    Black maintenance line as a second legend block; both blocks are then
    centred side by side below the panels. Call after the layout is frozen.
    """
    maintenance_legend = fig.legend(
        handles=[Line2D([], [], color="black", label="Maintenance")],
        loc="lower left",
        borderaxespad=0,
    )
    fig.canvas.draw()

    to_fig = fig.transFigure.inverted()
    growth_box = growth_legend.get_window_extent().transformed(to_fig)
    maint_width = maintenance_legend.get_window_extent().transformed(to_fig).width
    gap = 0.07
    left = 0.5 - (maint_width + gap + growth_box.width) / 2

    maintenance_legend.set_bbox_to_anchor((left, growth_box.y0))
    growth_legend.set_loc("lower left")
    growth_legend.borderaxespad = 0
    growth_legend.set_bbox_to_anchor((left + maint_width + gap, growth_box.y0))


# =============================================================================
# Main
# =============================================================================

def main():
    config.apply_style()

    h_ag = np.linspace(H_AG_MIN, H_AG_MAX, N_POINTS)

    pft_results = {
        pft: prepare_pft_data(pft, h_ag)
        for pft in config.PFTS
    }

    y_max = 0.0
    for result in pft_results.values():
        y_max = max(y_max, float(np.nanmax(result["maintenance"])))
        for curve in result["growth_curves"].values():
            y_max = max(y_max, float(np.nanmax(curve)))

    y_max = max(0.1, y_max * 1.08)

    fig, axes = plt.subplots(
        nrows=2,
        ncols=2,
        figsize=config.figsize_mm(config.WIDTH_FULL_MM, 120),
        sharex=True,
        sharey=True,
    )

    for ax, pft in zip(axes.ravel(), config.PFTS):
        result = pft_results[pft]

        # Potential growth per salinity (colours), then maintenance on top.
        for salinity in SALINITIES:
            ax.plot(h_ag, result["growth_curves"][salinity],
                    color=SALINITY_COLORS[salinity], linewidth=1.0)
        ax.plot(h_ag, result["maintenance"], color="black", linewidth=1.0)

        # Intersections = potential heights (values listed in Table S1).
        for intersection in result["intersections"].values():
            if intersection is not None:
                ax.scatter(*intersection, color="black", s=10, zorder=5)

        ax.set_title(panel_title(pft, result["params"]["p_maint"]))
        ax.set_xlim(0.0, H_AG_MAX)
        ax.set_ylim(0.0, y_max)
        ax.set_axisbelow(True)
        ax.grid(axis="y", linewidth=0.5, alpha=0.4)

    # One shared label per axis for all four panels, legends below them.
    fig.supylabel("Daily volume increment (m³)", fontsize="medium")
    growth_legend = add_growth_legend(fig)
    utils.center_label_under(fig, axes[1, :], "Aboveground height (m)")
    add_maintenance_legend(fig, growth_legend)

    config.save_figure(fig, OUT_PNG)
    plt.close(fig)


if __name__ == "__main__":
    main()
