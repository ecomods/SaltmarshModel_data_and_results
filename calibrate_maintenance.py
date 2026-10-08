"""
Calibrate the PFT-specific maintenance factors p_maint.

A single plant without competition is grown for DAYS days at 70 ppt. PFT 1
keeps its p_maint (reference); for PFTs 2-4, p_maint is found by bisection so
that the plant reaches the same aboveground height as PFT 1. At 70 ppt this
height is already the steady-state height (checked with the one-plant pyMANGA
runs). All other parameters are the same for all PFTs, except the salinity
tolerance salt_effect_ui.

The growth step re-implements pyMANGA's Saltmarsh plant model
(PlantModelLib/Saltmarsh/Saltmarsh.py) with the FixedSalinity Forman response.
Geometry and parameters are read from model_input/species/Saltmarsh_*.py,
except p_maint of PFTs 2-4, which is calibrated here. The printed p_maint
values were rounded to four digits for those files.

Usage (from the repository root):
    python calibrate_maintenance.py
"""

import importlib.util
import math

import numpy as np

from source.paths import SPECIES_DIR


# =============================================================================
# Settings
# =============================================================================

DAYS = 200
DT_SECONDS = 86400.0

# Salinity in kg/kg as used by FixedSalinity (0.070 kg/kg = 70 ppt).
CALIBRATION_SALINITY = 0.070

PFTS = [1, 2, 3, 4]
REFERENCE_PFT = 1

# A single plant has the full aboveground resources (no competition).
ABOVEGROUND_FACTOR = 1.0

# Search range and number of bisection steps for p_maint (1/s).
P_MAINT_MIN = 1e-8
P_MAINT_MAX = 1e-5
BISECTION_ITERATIONS = 200

OUTPUT_DIGITS = 6


def load_pft(pft):
    """Return geometry and parameters of a PFT from its species file."""
    path = SPECIES_DIR / f"Saltmarsh_{pft}.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.createPlant()


# =============================================================================
# Resources
# =============================================================================

def calculate_belowground_factor(salinity, salt_effect_ui, salt_effect_d):
    """Forman response (-) for salinity in kg/kg; float32 exponent as in pyMANGA."""
    exponent = salt_effect_d * (salt_effect_ui - salinity * 1000.0)
    exponent = np.array(exponent, dtype=np.float32)
    return float(1.0 / (1.0 + np.exp(exponent)))


def calculate_aboveground_resources(r_ag, aboveground_factor, parameter):
    """Aboveground resources (J) for one time step."""
    return (
        aboveground_factor
        * math.pi
        * r_ag ** 2
        * parameter["p_sun"]
        * DT_SECONDS
    )


def calculate_belowground_resources(V_bg, h_ag, h_bg, belowground_factor, parameter):
    """Belowground resources (J) for one time step."""
    return (
        belowground_factor
        * V_bg
        * parameter["p_sun"]
        * parameter["p_conv,bg"]
        * 1.0 / (h_ag + 0.5 * h_bg)
        * DT_SECONDS
    )


# =============================================================================
# Growth
# =============================================================================

def calculate_volume(r_ag, h_ag, r_bg, h_bg):
    """Aboveground, belowground and total cylinder volume (m³)."""
    V_ag = math.pi * r_ag ** 2 * h_ag
    V_bg = math.pi * r_bg ** 2 * h_bg
    return V_ag, V_bg, V_ag + V_bg


def update_geometry_from_volume(V_ag, V_bg, parameter):
    """Radii and heights (m) from the above- and belowground volumes."""
    V_ag = max(V_ag, 0.0)
    V_bg = max(V_bg, 0.0)

    if V_ag > 0.0:
        h_ag = (V_ag / (math.pi * parameter["p_ratio_ag"] ** 2)) ** (1.0 / 3.0)
        r_ag = parameter["p_ratio_ag"] * h_ag
    else:
        h_ag = 0.0
        r_ag = 0.0

    if V_bg > 0.0:
        h_bg = (V_bg / (math.pi * parameter["p_ratio_bg"] ** 2)) ** (1.0 / 3.0)
        r_bg = parameter["p_ratio_bg"] * h_bg
    else:
        h_bg = 0.0
        r_bg = 0.0

    return r_ag, h_ag, r_bg, h_bg


def simulate_plant(geometry, parameter, p_maint, days):
    """Grow one isolated plant for the given days; return its final state."""
    r_ag = geometry["r_ag"]
    h_ag = geometry["h_ag"]
    r_bg = geometry["r_bg"]
    h_bg = geometry["h_bg"]

    aboveground_factor = ABOVEGROUND_FACTOR
    belowground_factor = calculate_belowground_factor(
        salinity=CALIBRATION_SALINITY,
        salt_effect_ui=parameter["salt_effect_ui"],
        salt_effect_d=parameter["salt_effect_d"],
    )

    for _ in range(days):
        V_ag, V_bg, volume = calculate_volume(r_ag, h_ag, r_bg, h_bg)

        maint = volume * p_maint * DT_SECONDS
        res_ag = calculate_aboveground_resources(r_ag, aboveground_factor, parameter)
        res_bg = calculate_belowground_resources(
            V_bg, h_ag, h_bg, belowground_factor, parameter
        )
        res_eff = min(res_ag, res_bg)
        grow = res_eff * parameter["p_grow"] - maint

        if grow < 0.0:
            grow *= parameter["p_dieback"]

        if grow > 0.0:
            # AG/BG allocation as in pyMANGA's Saltmarsh model.
            ratio_ag_bg = np.clip(
                aboveground_factor
                / (aboveground_factor + belowground_factor + 1e-22),
                1e-6,
                0.999999,
            )
            ratio_vol = V_ag / max(V_bg, 1e-22)
            f_ad = 0.5 - ratio_ag_bg

            if ratio_vol > 2.5 and f_ad < 0.0:
                pass
            elif ratio_vol < 0.15 and f_ad > 0.0:
                pass
            elif 0.15 <= ratio_vol <= 2.5:
                pass
            else:
                f_ad = 0.0  # prevent maladaptive adjustment

            w_ratio_ag_bg = parameter["p_ratio_ag_bg"] * (1.0 - f_ad)
            V_ag_incr = grow * (1.0 - w_ratio_ag_bg)
            V_bg_incr = grow * w_ratio_ag_bg
        else:
            V_ag_incr = grow * 0.5
            V_bg_incr = grow * 0.5

        r_ag, h_ag, r_bg, h_bg = update_geometry_from_volume(
            V_ag + V_ag_incr, V_bg + V_bg_incr, parameter
        )

    return {
        "h_ag_final": h_ag,
        "belowground_factor": belowground_factor,
    }


# =============================================================================
# Calibration
# =============================================================================

def calibrate_p_maint(geometry, parameter, target_h_ag):
    """Find p_maint by bisection so that the plant reaches target_h_ag (m)."""
    lo = P_MAINT_MIN
    hi = P_MAINT_MAX

    h_lo = simulate_plant(geometry, parameter, lo, DAYS)["h_ag_final"]
    h_hi = simulate_plant(geometry, parameter, hi, DAYS)["h_ag_final"]

    if not (h_lo >= target_h_ag >= h_hi):
        raise RuntimeError(
            "The target height is not within the search range.\n"
            f"target_h_ag = {target_h_ag:.12f}\n"
            f"h_ag at P_MAINT_MIN ({P_MAINT_MIN:.3e}) = {h_lo:.12f}\n"
            f"h_ag at P_MAINT_MAX ({P_MAINT_MAX:.3e}) = {h_hi:.12f}\n"
            "Widen P_MAINT_MIN and P_MAINT_MAX."
        )

    for _ in range(BISECTION_ITERATIONS):
        mid = 0.5 * (lo + hi)
        if simulate_plant(geometry, parameter, mid, DAYS)["h_ag_final"] > target_h_ag:
            lo = mid
        else:
            hi = mid

    return 0.5 * (lo + hi)


# =============================================================================
# Output
# =============================================================================

def print_species_file_block(pft, parameter, p_maint):
    """Print the parameter lines for a species file."""
    print(f"# Saltmarsh_{pft}")
    print(f"parameter['p_maint'] = {p_maint:.{OUTPUT_DIGITS}e}")
    print(f"parameter['p_grow'] = {parameter['p_grow']:.{OUTPUT_DIGITS}e}")
    for key in ["p_dieback", "p_ratio_ag_bg", "p_ratio_ag", "p_ratio_bg",
                "salt_effect_d", "salt_effect_ui"]:
        print(f"parameter['{key}'] = {parameter[key]:.{OUTPUT_DIGITS}g}")
    print()


def main():
    geometries, parameters = {}, {}
    for pft in PFTS:
        geometries[pft], parameters[pft] = load_pft(pft)
    reference_p_maint = parameters[REFERENCE_PFT]["p_maint"]

    print("============================================================")
    print("Saltmarsh PFT maintenance-factor calibration")
    print("============================================================")
    print()

    print("Calibration settings")
    print("--------------------")
    print(f"calibration days      = {DAYS}")
    print(f"salinity              = {CALIBRATION_SALINITY:.6f} kg/kg")
    print(f"salinity              = {CALIBRATION_SALINITY * 1000.0:.1f} ppt")
    print(f"reference PFT         = PFT {REFERENCE_PFT}")
    print(f"reference p_maint     = {reference_p_maint:.6e}")
    print(f"p_grow                = {parameters[REFERENCE_PFT]['p_grow']:.6e}")
    print()

    target_h_ag = simulate_plant(
        geometries[REFERENCE_PFT], parameters[REFERENCE_PFT], reference_p_maint, DAYS
    )["h_ag_final"]

    print("Reference target")
    print("----------------")
    print(f"target h_ag after {DAYS} days = {target_h_ag:.12f} m")
    print()

    calibrated = {}
    for pft in PFTS:
        if pft == REFERENCE_PFT:
            p_maint = reference_p_maint
        else:
            p_maint = calibrate_p_maint(geometries[pft], parameters[pft], target_h_ag)
        calibrated[pft] = {
            "p_maint": p_maint,
            "result": simulate_plant(geometries[pft], parameters[pft], p_maint, DAYS),
        }

    print("Calibration results")
    print("-------------------")
    print(
        "PFT  Ui    BG factor    p_maint          h_ag_final       "
        "h_ag_error"
    )
    print("-" * 75)

    for pft in PFTS:
        p_maint = calibrated[pft]["p_maint"]
        result = calibrated[pft]["result"]
        h_error = result["h_ag_final"] - target_h_ag
        print(
            f"{pft:>3d}  "
            f"{parameters[pft]['salt_effect_ui']:>4.0f}  "
            f"{result['belowground_factor']:>11.6f}  "
            f"{p_maint:>14.6e}  "
            f"{result['h_ag_final']:>14.9f}  "
            f"{h_error:>12.3e}"
        )

    print()
    print("Species-file parameter blocks")
    print("-----------------------------")
    print()
    for pft in PFTS:
        print_species_file_block(pft, parameters[pft], calibrated[pft]["p_maint"])

    print("Copy-paste summary")
    print("------------------")
    for pft in PFTS:
        print(f"Saltmarsh_{pft}: p_maint = {calibrated[pft]['p_maint']:.{OUTPUT_DIGITS}e}")


if __name__ == "__main__":
    main()
