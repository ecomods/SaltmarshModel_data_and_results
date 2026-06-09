# -*- coding: utf-8 -*-


# =============================================================================
# SCRIPT OVERVIEW
# =============================================================================
# Purpose
# -------
# This is the first main entry-point of the repository. It creates all pyMANGA
# XML control files and, importantly, all output folders that pyMANGA later writes
# into. You should run it whenever the repository is moved, renamed, or whenever
# one of the setup definitions is changed.
#
# What this script does in practice
# ---------------------------------
# 1. Defines the complete simulation design in the CONFIG dictionary:
#    - static salinity levels,
#    - dynamic salinity scenarios,
#    - replicate numbers,
#    - PFT numbers,
#    - domain size,
#    - time-loop settings,
#    - output settings,
#    - population settings.
# 2. Converts local repository paths into paths that are valid from pyMANGA's
#    working directory. This is necessary because run_model.py starts MANGA.py
#    from the pyMANGA-1 folder, not from this repository folder.
# 3. Writes one XML file for each individual simulation setup.
# 4. Creates the corresponding data_raw/... output directories before pyMANGA is
#    started.
#
# Typical usage
# -------------
# Run from the repository root:
#     py -3.12 create_setups.py
#
# Expected result
# ---------------
# - 300 XML files in data_model_input/xml_control_files/.
# - Matching empty output folders in data_raw/.
# =============================================================================

"""
Created March 2026

Generalized XML control-file generator for Saltmarsh parameter studies.

This script generates XML control files for:
- community static
- community dynamic
- monoculture static
- one plant static
- one plant dynamic

It also creates all output directories in data_raw/ that are referenced
by the XML files.

Current pyMANGA SaltmarshModel compatibility:
- growth outputs:
    aboveground_resources
    belowground_resources
    res_ag
    res_bg
    res_eff
    grow
    maint
    volume
    age
    salinity
    transpiration
"""

import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path

from source.utils.paths import (
    DATA_RAW,
    SPECIES_DIR,
    SALINITY_DIR,
    PLANT_DISTRIBUTION_DIR,
    XML_CONTROL_FILES,
    DEFAULT_MANGA_DIR,
    ensure_directories,
)


def path_for_xml(path):
    """
    Return a POSIX-style path for XML files, relative to pyMANGA's cwd.

    pyMANGA is started from DEFAULT_MANGA_DIR. Therefore all file paths written
    into XML files must be valid relative to DEFAULT_MANGA_DIR.
    """
    path = Path(path).resolve()
    base = DEFAULT_MANGA_DIR.resolve()

    try:
        return Path(os.path.relpath(path, start=base)).as_posix()
    except ValueError:
        return path.as_posix()


def make_output_dir(*parts):
    """
    Create an output directory under data_raw/ and return its XML path.

    Parameters
    ----------
    *parts : str
        Path components below DATA_RAW.

    Returns
    -------
    str
        POSIX-style path relative to pyMANGA's working directory.
    """
    output_dir = DATA_RAW.joinpath(*[str(p) for p in parts])
    output_dir.mkdir(parents=True, exist_ok=True)
    return path_for_xml(output_dir)


# ================================================================
# CONFIGURATION
# ================================================================

CONFIG = {
    "enabled_setups": {
        "community_static": True,
        "community_dynamic": True,
        "monoculture_static": True,
        "oneplant_static": True,
        "oneplant_dynamic": True,
    },

    "paths": {
        "xml_dir": str(XML_CONTROL_FILES),
        "species_dir": path_for_xml(SPECIES_DIR),
        "salinity_dir": path_for_xml(SALINITY_DIR),
        "oneplant_distribution_file": path_for_xml(
            PLANT_DISTRIBUTION_DIR / "one_plant.csv"
        ),
    },

    "domain": {
        "x_1": 0,
        "y_1": 0,
        "x_2": 2,
        "y_2": 2,
        "x_resolution": 40,
        "y_resolution": 40,
    },

    "time": {
        "t_start": 0,
        "t_end": 3.154e8,
        "delta_t": 86400,
        "terminal_print": "days",
    },

    "output": {
        "allow_previous_output": True,
        "community_output_each_nth_timestep": 10,
        "oneplant_output_each_nth_timestep": 1,
        "community_output_range": "[1.577e+8, 3.154e+8]",
        "oneplant_output_range": "[0,3.154e+8]",
    },

    "study": {
        "static_salinities": [0.035, 0.070, 0.105, 0.140],
        "dynamic_salinities": [35, 70, 105],
        "dynamic_variants": ["V1", "V2"],
        "replicates": list(range(1, 11)),
        "pfts": [1, 2, 3, 4],
    },

    "population": {
        "community": {
            "group_count": 4,
            "mortality": "Memory Random SizeThreshold",
            "n_recruitment_per_step": 4,
            "n_individuals": 40,
            "period": "3.154e+7*1",
            "threshold": "0.05",
            "probability": "0.25",
            "initial_population_type": "Random",
            "production_type": "FixedRate",
            "dispersal_type": "Uniform",
        },
        "monoculture": {
            "mortality": "Memory Random SizeThreshold",
            "n_recruitment_per_step": 16,
            "n_individuals": 160,
            "period": "3.154e+7*1",
            "threshold": "0.05",
            "probability": "0.25",
            "initial_population_type": "Random",
            "production_type": "FixedRate",
            "dispersal_type": "Uniform",
        },
        "oneplant": {
            "mortality": "Memory Random SizeThreshold",
            "n_recruitment_per_step": 0,
            "n_individuals": 1,
            "period": "3.154e+7*1",
            "threshold": "0.05",
            "initial_population_type": "FromFile",
            "production_type": "FixedRate",
            "dispersal_type": "Uniform",
        },
    },

    "belowground": {
        "type": "Merge",
        "modules": "FixedSalinity SymmetricZOI",
        "variant": "forman",
        "min_x": 0,
        "max_x": 2,
    },

    "aboveground": {
        "type": "AsymmetricZOI",
    },
}


# ================================================================
# HELPERS
# ================================================================

def prettify(elem):
    rough_string = ET.tostring(elem, "utf-8")
    return minidom.parseString(rough_string).toprettyxml(indent="    ")


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def add_domain(parent):
    d = CONFIG["domain"]

    domain = ET.SubElement(parent, "domain")
    ET.SubElement(domain, "x_1").text = str(d["x_1"])
    ET.SubElement(domain, "y_1").text = str(d["y_1"])
    ET.SubElement(domain, "x_2").text = str(d["x_2"])
    ET.SubElement(domain, "y_2").text = str(d["y_2"])


def add_resources(project, salinity_text):
    resources = ET.SubElement(project, "resources")

    ag = ET.SubElement(resources, "aboveground")
    ET.SubElement(ag, "type").text = CONFIG["aboveground"]["type"]
    add_domain(ag)
    ET.SubElement(ag, "x_resolution").text = str(CONFIG["domain"]["x_resolution"])
    ET.SubElement(ag, "y_resolution").text = str(CONFIG["domain"]["y_resolution"])

    bg = ET.SubElement(resources, "belowground")
    ET.SubElement(bg, "type").text = CONFIG["belowground"]["type"]
    ET.SubElement(bg, "modules").text = CONFIG["belowground"]["modules"]
    add_domain(bg)
    ET.SubElement(bg, "x_resolution").text = str(CONFIG["domain"]["x_resolution"])
    ET.SubElement(bg, "y_resolution").text = str(CONFIG["domain"]["y_resolution"])
    ET.SubElement(bg, "variant").text = str(CONFIG["belowground"]["variant"])
    ET.SubElement(bg, "min_x").text = str(CONFIG["belowground"]["min_x"])
    ET.SubElement(bg, "max_x").text = str(CONFIG["belowground"]["max_x"])
    ET.SubElement(bg, "salinity").text = salinity_text


def add_group_core(group, pft_idx, pop_cfg):
    paths = CONFIG["paths"]

    ET.SubElement(group, "name").text = f"Saltmarsh_{pft_idx}"
    ET.SubElement(group, "species").text = (
        f"{paths['species_dir']}/Saltmarsh_{pft_idx}.py"
    )
    ET.SubElement(group, "vegetation_model_type").text = "Saltmarsh"
    ET.SubElement(group, "mortality").text = pop_cfg["mortality"]
    ET.SubElement(group, "period").text = pop_cfg["period"]
    ET.SubElement(group, "threshold").text = pop_cfg["threshold"]

    if "probability" in pop_cfg:
        ET.SubElement(group, "probability").text = pop_cfg["probability"]

    add_domain(group)


def add_random_group(population, pft_idx, population_key):
    pop_cfg = CONFIG["population"][population_key]

    group = ET.SubElement(population, "group")
    add_group_core(group, pft_idx, pop_cfg)

    initial_population = ET.SubElement(group, "initial_population")
    ET.SubElement(initial_population, "type").text = pop_cfg["initial_population_type"]
    ET.SubElement(initial_population, "n_individuals").text = str(
        pop_cfg["n_individuals"]
    )

    production = ET.SubElement(group, "production")
    ET.SubElement(production, "type").text = pop_cfg["production_type"]
    ET.SubElement(production, "per_model_area").text = str(
        pop_cfg["n_recruitment_per_step"]
    )

    dispersal = ET.SubElement(group, "dispersal")
    ET.SubElement(dispersal, "type").text = pop_cfg["dispersal_type"]


def add_oneplant_group(population, pft_idx):
    pop_cfg = CONFIG["population"]["oneplant"]

    group = ET.SubElement(population, "group")
    add_group_core(group, pft_idx, pop_cfg)

    initial_population = ET.SubElement(group, "initial_population")
    ET.SubElement(initial_population, "type").text = pop_cfg["initial_population_type"]
    ET.SubElement(initial_population, "filename").text = (
        CONFIG["paths"]["oneplant_distribution_file"]
    )

    production = ET.SubElement(group, "production")
    ET.SubElement(production, "type").text = pop_cfg["production_type"]
    ET.SubElement(production, "per_model_area").text = str(
        pop_cfg["n_recruitment_per_step"]
    )

    dispersal = ET.SubElement(group, "dispersal")
    ET.SubElement(dispersal, "type").text = pop_cfg["dispersal_type"]


def add_time_loop(project):
    t = CONFIG["time"]

    loop = ET.SubElement(project, "time_loop")
    ET.SubElement(loop, "type").text = "Simple"
    ET.SubElement(loop, "t_start").text = str(t["t_start"])
    ET.SubElement(loop, "t_end").text = str(t["t_end"])
    ET.SubElement(loop, "delta_t").text = str(t["delta_t"])
    ET.SubElement(loop, "terminal_print").text = t["terminal_print"]


def add_visualization(project):
    vis = ET.SubElement(project, "visualization")
    ET.SubElement(vis, "type").text = "NONE"


def add_output(project, output_dir, output_range, output_each_nth_timestep):
    out_cfg = CONFIG["output"]

    output = ET.SubElement(project, "output")
    ET.SubElement(output, "type").text = "OneFile"
    ET.SubElement(output, "output_time_range").text = output_range
    ET.SubElement(output, "allow_previous_output").text = str(
        out_cfg["allow_previous_output"]
    )
    ET.SubElement(output, "output_each_nth_timestep").text = (
        f"[0,{output_each_nth_timestep}]"
    )
    ET.SubElement(output, "output_dir").text = output_dir

    for g in ["r_ag", "h_ag", "r_bg", "h_bg"]:
        ET.SubElement(output, "geometry_output").text = g

    for g in [
        "aboveground_resources",
        "belowground_resources",
        "res_ag",
        "res_bg",
        "res_eff",
        "grow",
        "maint",
        "volume",
        "age",
        "salinity",
        "transpiration",
    ]:
        ET.SubElement(output, "growth_output").text = g


def write_xml(filepath, project):
    ensure_dir(os.path.dirname(filepath))

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(prettify(project))


# ================================================================
# SETUP WRITERS
# ================================================================

def write_community_static(filepath, salinity, replicate):
    project = ET.Element("MangaProject")
    add_resources(project, f"{salinity:.3f} {salinity:.3f}")

    population = ET.SubElement(project, "population")

    for pft_idx in range(1, CONFIG["population"]["community"]["group_count"] + 1):
        add_random_group(population, pft_idx, "community")

    add_time_loop(project)
    add_visualization(project)

    output_dir = make_output_dir(
        "community",
        "static",
        f"{salinity:.3f}",
        f"{replicate:02d}",
    )

    add_output(
        project,
        output_dir,
        CONFIG["output"]["community_output_range"],
        CONFIG["output"]["community_output_each_nth_timestep"],
    )

    write_xml(filepath, project)


def write_community_dynamic(filepath, salinity_id, replicate):
    project = ET.Element("MangaProject")
    add_resources(project, f"{CONFIG['paths']['salinity_dir']}/{salinity_id}.csv")

    population = ET.SubElement(project, "population")

    for pft_idx in range(1, CONFIG["population"]["community"]["group_count"] + 1):
        add_random_group(population, pft_idx, "community")

    add_time_loop(project)
    add_visualization(project)

    output_dir = make_output_dir(
        "community",
        "dynamic",
        salinity_id,
        f"{replicate:02d}",
    )

    add_output(
        project,
        output_dir,
        CONFIG["output"]["community_output_range"],
        CONFIG["output"]["community_output_each_nth_timestep"],
    )

    write_xml(filepath, project)


def write_monoculture_static(filepath, salinity, replicate, pft_idx):
    project = ET.Element("MangaProject")
    add_resources(project, f"{salinity:.3f} {salinity:.3f}")

    population = ET.SubElement(project, "population")
    add_random_group(population, pft_idx, "monoculture")

    add_time_loop(project)
    add_visualization(project)

    output_dir = make_output_dir(
        "monoculture",
        "static",
        f"{salinity:.3f}",
        f"PFT_{pft_idx}",
        f"{replicate:02d}",
    )

    add_output(
        project,
        output_dir,
        CONFIG["output"]["community_output_range"],
        CONFIG["output"]["community_output_each_nth_timestep"],
    )

    write_xml(filepath, project)


def write_oneplant_static(filepath, salinity, pft_idx):
    project = ET.Element("MangaProject")
    add_resources(project, f"{salinity:.3f} {salinity:.3f}")

    population = ET.SubElement(project, "population")
    add_oneplant_group(population, pft_idx)

    add_time_loop(project)
    add_visualization(project)

    output_dir = make_output_dir(
        "one_plant",
        "static",
        f"{salinity:.3f}",
        f"PFT_{pft_idx}",
    )

    add_output(
        project,
        output_dir,
        CONFIG["output"]["oneplant_output_range"],
        CONFIG["output"]["oneplant_output_each_nth_timestep"],
    )

    write_xml(filepath, project)


def write_oneplant_dynamic(filepath, salinity, version, pft_idx):
    project = ET.Element("MangaProject")
    add_resources(project, f"{CONFIG['paths']['salinity_dir']}/{salinity}_{version}.csv")

    population = ET.SubElement(project, "population")
    add_oneplant_group(population, pft_idx)

    add_time_loop(project)
    add_visualization(project)

    output_dir = make_output_dir(
        "one_plant",
        "dynamic",
        f"{salinity}_{version}",
        f"PFT_{pft_idx}",
    )

    add_output(
        project,
        output_dir,
        CONFIG["output"]["oneplant_output_range"],
        CONFIG["output"]["oneplant_output_each_nth_timestep"],
    )

    write_xml(filepath, project)


# ================================================================
# GENERATORS
# ================================================================

def generate_community_static():
    for salinity in CONFIG["study"]["static_salinities"]:
        for replicate in CONFIG["study"]["replicates"]:
            xml_path = (
                f"{CONFIG['paths']['xml_dir']}/"
                f"community_static_{salinity:.3f}_{replicate:02d}.xml"
            )
            write_community_static(xml_path, salinity, replicate)


def generate_community_dynamic():
    for salinity in CONFIG["study"]["dynamic_salinities"]:
        for variant in CONFIG["study"]["dynamic_variants"]:
            salinity_id = f"{salinity}_{variant}"

            for replicate in CONFIG["study"]["replicates"]:
                xml_path = (
                    f"{CONFIG['paths']['xml_dir']}/"
                    f"community_dynamic_{salinity_id}_{replicate:02d}.xml"
                )
                write_community_dynamic(xml_path, salinity_id, replicate)


def generate_monoculture_static():
    for salinity in CONFIG["study"]["static_salinities"]:
        for pft_idx in CONFIG["study"]["pfts"]:
            for replicate in CONFIG["study"]["replicates"]:
                xml_path = (
                    f"{CONFIG['paths']['xml_dir']}/"
                    f"monoculture_static_pft{pft_idx}_{salinity:.3f}_{replicate:02d}.xml"
                )
                write_monoculture_static(xml_path, salinity, replicate, pft_idx)


def generate_oneplant_static():
    for salinity in CONFIG["study"]["static_salinities"]:
        for pft_idx in CONFIG["study"]["pfts"]:
            xml_path = (
                f"{CONFIG['paths']['xml_dir']}/"
                f"oneplant_static_{salinity:.3f}_pft{pft_idx}.xml"
            )
            write_oneplant_static(xml_path, salinity, pft_idx)


def generate_oneplant_dynamic():
    for salinity in CONFIG["study"]["dynamic_salinities"]:
        for variant in CONFIG["study"]["dynamic_variants"]:
            for pft_idx in CONFIG["study"]["pfts"]:
                xml_path = (
                    f"{CONFIG['paths']['xml_dir']}/"
                    f"oneplant_dynamic_{salinity}_{variant}_pft{pft_idx}.xml"
                )
                write_oneplant_dynamic(xml_path, salinity, variant, pft_idx)


# ================================================================
# MAIN
# ================================================================

def main():
    ensure_directories()
    ensure_dir(CONFIG["paths"]["xml_dir"])

    if CONFIG["enabled_setups"]["community_static"]:
        generate_community_static()

    if CONFIG["enabled_setups"]["community_dynamic"]:
        generate_community_dynamic()

    if CONFIG["enabled_setups"]["monoculture_static"]:
        generate_monoculture_static()

    if CONFIG["enabled_setups"]["oneplant_static"]:
        generate_oneplant_static()

    if CONFIG["enabled_setups"]["oneplant_dynamic"]:
        generate_oneplant_dynamic()

    print("Done: create_setups.py")
    print(f"XML files written to: {XML_CONTROL_FILES}")
    print(f"Output directories created under: {DATA_RAW}")


if __name__ == "__main__":
    main()