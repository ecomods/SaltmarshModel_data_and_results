"""
Create the pyMANGA XML control files and output folders for all simulations.

Writes one XML file per run to model_input/xml_control_files/ (300 runs:
community static and dynamic, monoculture static, one plant static and
dynamic) and creates the matching output folders in model_output/. The random
seed of a run is its replicate number (1 for one-plant runs).

Paths in the XML files are relative to the pyMANGA folder, because
run_model.py starts pyMANGA from there. Rerun this script after moving or
renaming the repository or pyMANGA.

Usage (from the repository root):
    python create_setups.py
"""

import os
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.dom import minidom

from source.paths import (
    DEFAULT_MANGA_DIR,
    MODEL_OUTPUT,
    PLANT_DISTRIBUTION_DIR,
    SALINITY_DIR,
    SPECIES_DIR,
    XML_CONTROL_FILES,
)


def path_for_xml(path):
    """POSIX path relative to the pyMANGA folder (absolute on another drive)."""
    path = Path(path).resolve()
    try:
        return Path(os.path.relpath(path, start=DEFAULT_MANGA_DIR.resolve())).as_posix()
    except ValueError:
        return path.as_posix()


def make_output_dir(*parts):
    """Create an output folder below model_output/ and return its XML path."""
    output_dir = MODEL_OUTPUT.joinpath(*parts)
    output_dir.mkdir(parents=True, exist_ok=True)
    return path_for_xml(output_dir)


# =============================================================================
# Configuration
# =============================================================================

CONFIG = {
    "paths": {
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


# =============================================================================
# XML elements
# =============================================================================

def add_domain(parent):
    d = CONFIG["domain"]
    domain = ET.SubElement(parent, "domain")
    for key in ["x_1", "y_1", "x_2", "y_2"]:
        ET.SubElement(domain, key).text = str(d[key])


def add_resources(project, salinity_text):
    d = CONFIG["domain"]
    bg_cfg = CONFIG["belowground"]
    resources = ET.SubElement(project, "resources")

    ag = ET.SubElement(resources, "aboveground")
    ET.SubElement(ag, "type").text = CONFIG["aboveground"]["type"]
    add_domain(ag)
    ET.SubElement(ag, "x_resolution").text = str(d["x_resolution"])
    ET.SubElement(ag, "y_resolution").text = str(d["y_resolution"])

    bg = ET.SubElement(resources, "belowground")
    ET.SubElement(bg, "type").text = bg_cfg["type"]
    ET.SubElement(bg, "modules").text = bg_cfg["modules"]
    add_domain(bg)
    ET.SubElement(bg, "x_resolution").text = str(d["x_resolution"])
    ET.SubElement(bg, "y_resolution").text = str(d["y_resolution"])
    for key in ["variant", "min_x", "max_x"]:
        ET.SubElement(bg, key).text = str(bg_cfg[key])
    ET.SubElement(bg, "salinity").text = salinity_text


def add_group(population, pft, pop_cfg):
    """One plant group (PFT); one-plant runs read the plant from a file."""
    group = ET.SubElement(population, "group")
    ET.SubElement(group, "name").text = f"Saltmarsh_{pft}"
    ET.SubElement(group, "species").text = f"{CONFIG['paths']['species_dir']}/Saltmarsh_{pft}.py"
    ET.SubElement(group, "vegetation_model_type").text = "Saltmarsh"
    ET.SubElement(group, "mortality").text = pop_cfg["mortality"]
    ET.SubElement(group, "period").text = pop_cfg["period"]
    ET.SubElement(group, "threshold").text = pop_cfg["threshold"]
    if "probability" in pop_cfg:
        ET.SubElement(group, "probability").text = pop_cfg["probability"]
    add_domain(group)

    initial_population = ET.SubElement(group, "initial_population")
    ET.SubElement(initial_population, "type").text = pop_cfg["initial_population_type"]
    if pop_cfg["initial_population_type"] == "FromFile":
        ET.SubElement(initial_population, "filename").text = (
            CONFIG["paths"]["oneplant_distribution_file"]
        )
    else:
        ET.SubElement(initial_population, "n_individuals").text = str(pop_cfg["n_individuals"])

    production = ET.SubElement(group, "production")
    ET.SubElement(production, "type").text = pop_cfg["production_type"]
    ET.SubElement(production, "per_model_area").text = str(pop_cfg["n_recruitment_per_step"])

    dispersal = ET.SubElement(group, "dispersal")
    ET.SubElement(dispersal, "type").text = pop_cfg["dispersal_type"]


def add_time_loop(project):
    t = CONFIG["time"]
    loop = ET.SubElement(project, "time_loop")
    ET.SubElement(loop, "type").text = "Simple"
    for key in ["t_start", "t_end", "delta_t", "terminal_print"]:
        ET.SubElement(loop, key).text = str(t[key])


def add_output(project, output_dir, run_type):
    """Output settings; run_type "oneplant" or "community" (also monocultures)."""
    out_cfg = CONFIG["output"]
    output = ET.SubElement(project, "output")
    ET.SubElement(output, "type").text = "OneFile"
    ET.SubElement(output, "output_time_range").text = out_cfg[f"{run_type}_output_range"]
    ET.SubElement(output, "allow_previous_output").text = str(out_cfg["allow_previous_output"])
    ET.SubElement(output, "output_each_nth_timestep").text = (
        f"[0,{out_cfg[f'{run_type}_output_each_nth_timestep']}]"
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


# =============================================================================
# Setups
# =============================================================================

def static_salinity(salinity):
    """Constant salinity (kg/kg) at both ends of the domain."""
    return f"{salinity:.3f} {salinity:.3f}"


def salinity_file(salinity_id):
    """Salinity input file, e.g. 35_V1."""
    return f"{CONFIG['paths']['salinity_dir']}/{salinity_id}.csv"


def write_setup(name, salinity_text, population_key, pfts, seed, output_parts):
    """Write one XML control file and create its output folder."""
    project = ET.Element("MangaProject")
    ET.SubElement(project, "random_seed").text = str(seed)
    add_resources(project, salinity_text)

    population = ET.SubElement(project, "population")
    for pft in pfts:
        add_group(population, pft, CONFIG["population"][population_key])

    add_time_loop(project)
    ET.SubElement(ET.SubElement(project, "visualization"), "type").text = "NONE"
    run_type = "oneplant" if population_key == "oneplant" else "community"
    add_output(project, make_output_dir(*output_parts), run_type)

    xml = minidom.parseString(ET.tostring(project, "utf-8")).toprettyxml(indent="    ")
    with open(XML_CONTROL_FILES / f"{name}.xml", "w", encoding="utf-8") as f:
        f.write(xml)


def main():
    study = CONFIG["study"]
    XML_CONTROL_FILES.mkdir(parents=True, exist_ok=True)

    for sal in study["static_salinities"]:
        for n in study["replicates"]:
            write_setup(f"community_static_{sal:.3f}_{n:02d}", static_salinity(sal),
                        "community", study["pfts"], n,
                        ["community", "static", f"{sal:.3f}", f"{n:02d}"])

    for sal in study["dynamic_salinities"]:
        for variant in study["dynamic_variants"]:
            salinity_id = f"{sal}_{variant}"
            for n in study["replicates"]:
                write_setup(f"community_dynamic_{salinity_id}_{n:02d}",
                            salinity_file(salinity_id), "community", study["pfts"], n,
                            ["community", "dynamic", salinity_id, f"{n:02d}"])

    for sal in study["static_salinities"]:
        for pft in study["pfts"]:
            for n in study["replicates"]:
                write_setup(f"monoculture_static_pft{pft}_{sal:.3f}_{n:02d}",
                            static_salinity(sal), "monoculture", [pft], n,
                            ["monoculture", "static", f"{sal:.3f}", f"PFT_{pft}", f"{n:02d}"])

    for sal in study["static_salinities"]:
        for pft in study["pfts"]:
            write_setup(f"oneplant_static_{sal:.3f}_pft{pft}", static_salinity(sal),
                        "oneplant", [pft], 1,
                        ["one_plant", "static", f"{sal:.3f}", f"PFT_{pft}"])

    for sal in study["dynamic_salinities"]:
        for variant in study["dynamic_variants"]:
            salinity_id = f"{sal}_{variant}"
            for pft in study["pfts"]:
                write_setup(f"oneplant_dynamic_{salinity_id}_pft{pft}",
                            salinity_file(salinity_id), "oneplant", [pft], 1,
                            ["one_plant", "dynamic", salinity_id, f"PFT_{pft}"])

    print(f"XML files written to: {XML_CONTROL_FILES}")
    print(f"Output folders created under: {MODEL_OUTPUT}")


if __name__ == "__main__":
    main()
