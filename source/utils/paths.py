# -*- coding: utf-8 -*-

# =============================================================================
# SCRIPT OVERVIEW
# =============================================================================
# Purpose
# -------
# This module defines all important repository paths in one place. Every script
# should import paths from here instead of hard-coding ../data/... or ../figures/...
# paths. This makes the workflow robust when scripts are started from different
# working directories or from an IDE.
#
# Key idea
# --------
# REPO_ROOT is calculated from this file location. All other paths are then built
# from REPO_ROOT. This avoids ambiguity about whether a relative path refers to the
# repository root, the source/ folder, or the current shell directory.
# =============================================================================

"""
Central repository paths for the manuscript workflow.

All paths are resolved from the repository root so scripts can be started
from the top-level directory, from source/, or from an IDE.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

DATA_MODEL_INPUT = REPO_ROOT / "data_model_input"
DATA_RAW = REPO_ROOT / "data_raw"
DATA = REPO_ROOT / "data"
FIGURES = REPO_ROOT / "figures"
SOURCE = REPO_ROOT / "source"

PLANT_DISTRIBUTION_DIR = DATA_MODEL_INPUT / "plant_distribution"
SALINITY_DIR = DATA_MODEL_INPUT / "salinity"
SPECIES_DIR = DATA_MODEL_INPUT / "species"
XML_CONTROL_FILES = DATA_MODEL_INPUT / "xml_control_files"

LOG_DIR = DATA_RAW / "logs"
SIMULATION_LOG = LOG_DIR / "simulation_log.csv"

DERIVED_FIGURE_DATA = DATA / "derived_figure_data"

FIGURES_MAIN = FIGURES / "main"
FIGURES_APPENDIX = FIGURES / "appendix"

COMMUNITY_STATIC_DATA = DATA / "community" / "static" / "data.csv"
COMMUNITY_DYNAMIC_DATA = DATA / "community" / "dynamic" / "data.csv"
MONOCULTURE_STATIC_DATA = DATA / "monoculture" / "static" / "data.csv"

COMMUNITY_STATIC_RAW = DATA / "community" / "static" / "raw_data.csv"
COMMUNITY_DYNAMIC_RAW = DATA / "community" / "dynamic" / "raw_data.csv"
MONOCULTURE_STATIC_RAW = DATA / "monoculture" / "static" / "raw_data.csv"

# Expected pyMANGA location relative to this repository. Adjust in run_model.py
# if pyMANGA is stored elsewhere.
DEFAULT_MANGA_DIR = REPO_ROOT.parent / "pyMANGA-1"
DEFAULT_MANGA_SCRIPT = DEFAULT_MANGA_DIR / "MANGA.py"


def ensure_directories():
    """Create the standard output directories if they do not exist."""
    for path in [
        DATA_MODEL_INPUT,
        DATA_RAW,
        DATA,
        FIGURES,
        PLANT_DISTRIBUTION_DIR,
        SALINITY_DIR,
        SPECIES_DIR,
        XML_CONTROL_FILES,
        LOG_DIR,
        DERIVED_FIGURE_DATA,
        FIGURES_MAIN,
        FIGURES_APPENDIX,
    ]:
        path.mkdir(parents=True, exist_ok=True)
