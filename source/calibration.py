#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Calibration of PFT-specific maintenance factors for the Saltmarsh model.

The script uses PFT 1 as reference and simulates one isolated plant for a
defined calibration period. The above-ground height reached by PFT 1 is used
as target height. For PFT 2, PFT 3 and PFT 4, the maintenance factor is
automatically calibrated so that the same above-ground height is reached.

All PFTs use the same growth factor and geometry. They differ only in their
salinity tolerance parameter and in the calibrated maintenance factor.
"""

import math
import numpy as np


# =============================================================================
# SETTINGS
# =============================================================================

DAYS = 200
DT_SECONDS = 86400.0

# Salinity used for calibration.
# The FixedSalinity module uses kg/kg internally.
# 0.070 kg/kg corresponds to 70 ppt.
CALIBRATION_SALINITY = 0.070

# Reference PFT
REFERENCE_PFT = 1
REFERENCE_P_MAINT = 1.5e-6

# Search range for maintenance factor
P_MAINT_MIN = 1e-8
P_MAINT_MAX = 1e-5

# Bisection settings
BISECTION_ITERATIONS = 200

# Output rounding
OUTPUT_DIGITS = 6


# =============================================================================
# MODEL PARAMETERS
# =============================================================================

PARAMETER = {
    "p_sun": 1361.0,
    "p_conv,bg": 1.5,

    "p_grow": 5e-9,
    "p_dieback": 1.0,

    "p_ratio_ag_bg": 0.5,
    "p_ratio_ag": 0.5,
    "p_ratio_bg": 0.5,

    "p_transpiration": 1.5e-5,

    "r_salinity": "forman",
    "salt_effect_d": -0.045,

    "aboveground_factor": 1.0,
}


GEOMETRY = {
    "r_ag": 0.05,
    "r_ag_thr": 0.05,
    "h_ag": 0.1,

    "r_bg": 0.05,
    "r_bg_thr": 0.05,
    "h_bg": 0.1,

    "volume_thr": 0.0015708,
}


PFTS = {
    1: {
        "name": "Saltmarsh_1",
        "salt_effect_ui": 60.0,
    },
    2: {
        "name": "Saltmarsh_2",
        "salt_effect_ui": 70.0,
    },
    3: {
        "name": "Saltmarsh_3",
        "salt_effect_ui": 80.0,
    },
    4: {
        "name": "Saltmarsh_4",
        "salt_effect_ui": 90.0,
    },
}


# =============================================================================
# RESOURCE FUNCTIONS
# =============================================================================

def calculate_belowground_factor(salinity, salt_effect_ui, salt_effect_d):
    """
    Calculate the below-ground resource factor using the Forman response.

    Parameters
    ----------
    salinity : float
        Salinity [kg/kg].
    salt_effect_ui : float
        PFT-specific salinity tolerance parameter [ppt].
    salt_effect_d : float
        Slope parameter of the response function.

    Returns
    -------
    float
        Below-ground resource factor [-].
    """
    exponent = salt_effect_d * (salt_effect_ui - salinity * 1000.0)
    exponent = np.array(exponent, dtype=np.float32)

    return float(1.0 / (1.0 + np.exp(exponent)))


def calculate_aboveground_resources(r_ag, aboveground_factor, parameter):
    """
    Calculate above-ground resources.

    Parameters
    ----------
    r_ag : float
        Above-ground radius [m].
    aboveground_factor : float
        Above-ground resource factor [-].
    parameter : dict
        Model parameters.

    Returns
    -------
    float
        Above-ground resources [J].
    """
    return (
        aboveground_factor
        * math.pi
        * r_ag ** 2
        * parameter["p_sun"]
        * DT_SECONDS
    )


def calculate_belowground_resources(
    V_bg,
    h_ag,
    h_bg,
    belowground_factor,
    parameter,
):
    """
    Calculate below-ground resources.

    Parameters
    ----------
    V_bg : float
        Below-ground volume [m³].
    h_ag : float
        Above-ground height [m].
    h_bg : float
        Below-ground height [m].
    belowground_factor : float
        Below-ground resource factor [-].
    parameter : dict
        Model parameters.

    Returns
    -------
    float
        Below-ground resources [J].
    """
    return (
        belowground_factor
        * V_bg
        * parameter["p_sun"]
        * parameter["p_conv,bg"]
        * 1.0 / (h_ag + 0.5 * h_bg)
        * DT_SECONDS
    )


# =============================================================================
# GROWTH MODEL
# =============================================================================

def calculate_volume(r_ag, h_ag, r_bg, h_bg):
    """
    Calculate above-ground, below-ground and total volume.

    Parameters
    ----------
    r_ag : float
        Above-ground radius [m].
    h_ag : float
        Above-ground height [m].
    r_bg : float
        Below-ground radius [m].
    h_bg : float
        Below-ground height [m].

    Returns
    -------
    tuple
        V_ag, V_bg, volume.
    """
    V_ag = math.pi * r_ag ** 2 * h_ag
    V_bg = math.pi * r_bg ** 2 * h_bg
    volume = V_ag + V_bg

    return V_ag, V_bg, volume


def update_geometry_from_volume(V_ag, V_bg, parameter):
    """
    Recalculate geometry from above-ground and below-ground volume.

    Parameters
    ----------
    V_ag : float
        Above-ground volume [m³].
    V_bg : float
        Below-ground volume [m³].
    parameter : dict
        Model parameters.

    Returns
    -------
    tuple
        r_ag, h_ag, r_bg, h_bg.
    """
    V_ag = max(V_ag, 0.0)
    V_bg = max(V_bg, 0.0)

    if V_ag > 0.0:
        h_ag = (
            V_ag / (math.pi * parameter["p_ratio_ag"] ** 2)
        ) ** (1.0 / 3.0)
        r_ag = parameter["p_ratio_ag"] * h_ag
    else:
        h_ag = 0.0
        r_ag = 0.0

    if V_bg > 0.0:
        h_bg = (
            V_bg / (math.pi * parameter["p_ratio_bg"] ** 2)
        ) ** (1.0 / 3.0)
        r_bg = parameter["p_ratio_bg"] * h_bg
    else:
        h_bg = 0.0
        r_bg = 0.0

    return r_ag, h_ag, r_bg, h_bg


def simulate_plant(pft, p_maint, days):
    """
    Simulate one isolated plant.

    Parameters
    ----------
    pft : dict
        PFT-specific parameters.
    p_maint : float
        Maintenance factor [1/s].
    days : int
        Number of simulated days.

    Returns
    -------
    dict
        Simulation result.
    """
    parameter = PARAMETER.copy()

    r_ag = GEOMETRY["r_ag"]
    h_ag = GEOMETRY["h_ag"]
    r_bg = GEOMETRY["r_bg"]
    h_bg = GEOMETRY["h_bg"]

    aboveground_factor = parameter["aboveground_factor"]
    belowground_factor = calculate_belowground_factor(
        salinity=CALIBRATION_SALINITY,
        salt_effect_ui=pft["salt_effect_ui"],
        salt_effect_d=parameter["salt_effect_d"],
    )

    series = {
        "day": [],
        "r_ag": [],
        "h_ag": [],
        "r_bg": [],
        "h_bg": [],
        "V_ag": [],
        "V_bg": [],
        "volume": [],
        "res_ag": [],
        "res_bg": [],
        "res_eff": [],
        "grow_pot": [],
        "maint": [],
        "grow": [],
        "aboveground_factor": [],
        "belowground_factor": [],
        "ratio_ag_bg": [],
        "f_ad": [],
        "w_ratio_ag_bg": [],
    }

    for day in range(days + 1):
        V_ag, V_bg, volume = calculate_volume(
            r_ag=r_ag,
            h_ag=h_ag,
            r_bg=r_bg,
            h_bg=h_bg,
        )

        series["day"].append(day)
        series["r_ag"].append(r_ag)
        series["h_ag"].append(h_ag)
        series["r_bg"].append(r_bg)
        series["h_bg"].append(h_bg)
        series["V_ag"].append(V_ag)
        series["V_bg"].append(V_bg)
        series["volume"].append(volume)
        series["aboveground_factor"].append(aboveground_factor)
        series["belowground_factor"].append(belowground_factor)

        if day == days:
            series["res_ag"].append(np.nan)
            series["res_bg"].append(np.nan)
            series["res_eff"].append(np.nan)
            series["grow_pot"].append(np.nan)
            series["maint"].append(np.nan)
            series["grow"].append(np.nan)
            series["ratio_ag_bg"].append(np.nan)
            series["f_ad"].append(np.nan)
            series["w_ratio_ag_bg"].append(np.nan)
            break

        maint = volume * p_maint * DT_SECONDS

        res_ag = calculate_aboveground_resources(
            r_ag=r_ag,
            aboveground_factor=aboveground_factor,
            parameter=parameter,
        )

        res_bg = calculate_belowground_resources(
            V_bg=V_bg,
            h_ag=h_ag,
            h_bg=h_bg,
            belowground_factor=belowground_factor,
            parameter=parameter,
        )

        res_eff = min(res_ag, res_bg)
        grow_pot = res_eff * parameter["p_grow"]
        grow = grow_pot - maint

        if grow < 0.0:
            grow *= parameter["p_dieback"]

        if grow > 0.0:
            ratio_ag_bg = np.clip(
                aboveground_factor
                / (aboveground_factor + belowground_factor + 1e-22),
                1e-6,
                0.999999,
            )

            ratio_vol = V_ag / max(V_bg, 1e-6)
            f_ad = 0.5 - ratio_ag_bg

            if ratio_vol > 2.5 and f_ad < 0.0:
                pass
            elif ratio_vol < 0.15 and f_ad > 0.0:
                pass
            elif 0.15 <= ratio_vol <= 2.5:
                pass
            else:
                f_ad = 0.0

            w_ratio_ag_bg = parameter["p_ratio_ag_bg"] * (1.0 - f_ad)

            V_ag_incr = grow * (1.0 - w_ratio_ag_bg)
            V_bg_incr = grow * w_ratio_ag_bg

        else:
            ratio_ag_bg = np.nan
            f_ad = np.nan
            w_ratio_ag_bg = np.nan

            V_ag_incr = grow * 0.5
            V_bg_incr = grow * 0.5

        V_ag_new = V_ag + V_ag_incr
        V_bg_new = V_bg + V_bg_incr

        r_ag, h_ag, r_bg, h_bg = update_geometry_from_volume(
            V_ag=V_ag_new,
            V_bg=V_bg_new,
            parameter=parameter,
        )

        series["res_ag"].append(res_ag)
        series["res_bg"].append(res_bg)
        series["res_eff"].append(res_eff)
        series["grow_pot"].append(grow_pot)
        series["maint"].append(maint)
        series["grow"].append(grow)
        series["ratio_ag_bg"].append(ratio_ag_bg)
        series["f_ad"].append(f_ad)
        series["w_ratio_ag_bg"].append(w_ratio_ag_bg)

    for key in series:
        series[key] = np.array(series[key])

    result = {
        "h_ag_final": float(series["h_ag"][-1]),
        "h_bg_final": float(series["h_bg"][-1]),
        "r_ag_final": float(series["r_ag"][-1]),
        "r_bg_final": float(series["r_bg"][-1]),
        "volume_final": float(series["volume"][-1]),
        "belowground_factor": belowground_factor,
        "series": series,
    }

    return result


# =============================================================================
# CALIBRATION
# =============================================================================

def calibrate_p_maint(pft, target_h_ag):
    """
    Calibrate the maintenance factor so that the target height is reached.

    Parameters
    ----------
    pft : dict
        PFT-specific parameters.
    target_h_ag : float
        Target above-ground height [m].

    Returns
    -------
    float
        Calibrated maintenance factor.
    """
    lo = P_MAINT_MIN
    hi = P_MAINT_MAX

    h_lo = simulate_plant(
        pft=pft,
        p_maint=lo,
        days=DAYS,
    )["h_ag_final"]

    h_hi = simulate_plant(
        pft=pft,
        p_maint=hi,
        days=DAYS,
    )["h_ag_final"]

    if not (h_lo >= target_h_ag >= h_hi):
        raise RuntimeError(
            "The target height is not within the selected search range.\n"
            f"target_h_ag = {target_h_ag:.12f}\n"
            f"h_ag at P_MAINT_MIN ({P_MAINT_MIN:.3e}) = {h_lo:.12f}\n"
            f"h_ag at P_MAINT_MAX ({P_MAINT_MAX:.3e}) = {h_hi:.12f}\n"
            "Please widen P_MAINT_MIN and P_MAINT_MAX."
        )

    for _ in range(BISECTION_ITERATIONS):
        mid = 0.5 * (lo + hi)

        h_mid = simulate_plant(
            pft=pft,
            p_maint=mid,
            days=DAYS,
        )["h_ag_final"]

        if h_mid > target_h_ag:
            lo = mid
        else:
            hi = mid

    return 0.5 * (lo + hi)


# =============================================================================
# OUTPUT
# =============================================================================

def print_species_file_block(pft_id, pft, p_maint):
    """
    Print a Species-file-style parameter block.

    Parameters
    ----------
    pft_id : int
        PFT number.
    pft : dict
        PFT-specific parameters.
    p_maint : float
        Calibrated maintenance factor.
    """
    print(f"# {pft['name']}")
    print(f"parameter['p_maint'] = {p_maint:.{OUTPUT_DIGITS}e}")
    print(f"parameter['p_grow'] = {PARAMETER['p_grow']:.{OUTPUT_DIGITS}e}")
    print(f"parameter['p_dieback'] = {PARAMETER['p_dieback']:.{OUTPUT_DIGITS}g}")
    print(f"parameter['p_ratio_ag_bg'] = {PARAMETER['p_ratio_ag_bg']:.{OUTPUT_DIGITS}g}")
    print(f"parameter['p_ratio_ag'] = {PARAMETER['p_ratio_ag']:.{OUTPUT_DIGITS}g}")
    print(f"parameter['p_ratio_bg'] = {PARAMETER['p_ratio_bg']:.{OUTPUT_DIGITS}g}")
    print(f"parameter['salt_effect_d'] = {PARAMETER['salt_effect_d']:.{OUTPUT_DIGITS}g}")
    print(f"parameter['salt_effect_ui'] = {pft['salt_effect_ui']:.{OUTPUT_DIGITS}g}")
    print()


def main():
    """
    Run the maintenance-factor calibration.
    """
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
    print(f"reference p_maint     = {REFERENCE_P_MAINT:.6e}")
    print(f"p_grow                = {PARAMETER['p_grow']:.6e}")
    print()

    reference_result = simulate_plant(
        pft=PFTS[REFERENCE_PFT],
        p_maint=REFERENCE_P_MAINT,
        days=DAYS,
    )

    target_h_ag = reference_result["h_ag_final"]

    print("Reference target")
    print("----------------")
    print(f"target h_ag after {DAYS} days = {target_h_ag:.12f} m")
    print()

    calibrated = {}

    for pft_id, pft in PFTS.items():
        if pft_id == REFERENCE_PFT:
            p_maint = REFERENCE_P_MAINT
        else:
            p_maint = calibrate_p_maint(
                pft=pft,
                target_h_ag=target_h_ag,
            )

        result = simulate_plant(
            pft=pft,
            p_maint=p_maint,
            days=DAYS,
        )

        calibrated[pft_id] = {
            "p_maint": p_maint,
            "result": result,
        }

    print("Calibration results")
    print("-------------------")
    print(
        "PFT  Ui    BG factor    p_maint          h_ag_final       "
        "h_ag_error"
    )
    print("-" * 75)

    for pft_id, pft in PFTS.items():
        p_maint = calibrated[pft_id]["p_maint"]
        result = calibrated[pft_id]["result"]
        h_error = result["h_ag_final"] - target_h_ag

        print(
            f"{pft_id:>3d}  "
            f"{pft['salt_effect_ui']:>4.0f}  "
            f"{result['belowground_factor']:>11.6f}  "
            f"{p_maint:>14.6e}  "
            f"{result['h_ag_final']:>14.9f}  "
            f"{h_error:>12.3e}"
        )

    print()
    print("Species-file parameter blocks")
    print("-----------------------------")
    print()

    for pft_id, pft in PFTS.items():
        print_species_file_block(
            pft_id=pft_id,
            pft=pft,
            p_maint=calibrated[pft_id]["p_maint"],
        )

    print("Copy-paste summary")
    print("------------------")
    for pft_id in PFTS:
        print(
            f"{PFTS[pft_id]['name']}: "
            f"p_maint = {calibrated[pft_id]['p_maint']:.{OUTPUT_DIGITS}e}"
        )


if __name__ == "__main__":
    main()
