"""
Central paths of the repository.

All paths are built from the repository root, so scripts work from any
working directory. Scripts in source/ use `import paths`, scripts in the
repository root `from source.paths import ...`.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

MODEL_INPUT = REPO_ROOT / "model_input"
MODEL_OUTPUT = REPO_ROOT / "model_output"
FIGURE_DATA = REPO_ROOT / "figure_data"
FIGURES = REPO_ROOT / "figures"

PLANT_DISTRIBUTION_DIR = MODEL_INPUT / "plant_distribution"
SALINITY_DIR = MODEL_INPUT / "salinity"
SPECIES_DIR = MODEL_INPUT / "species"
XML_CONTROL_FILES = MODEL_INPUT / "xml_control_files"

LOG_DIR = MODEL_OUTPUT / "logs"
SIMULATION_LOG = LOG_DIR / "simulation_log.csv"

FIGURES_MAIN = FIGURES / "main"
FIGURES_APPENDIX = FIGURES / "appendix"

# pyMANGA is expected next to this repository. Change DEFAULT_MANGA_DIR if it
# is stored elsewhere, then rerun create_setups.py.
DEFAULT_MANGA_DIR = REPO_ROOT.parent / "pyMANGA"
DEFAULT_MANGA_SCRIPT = DEFAULT_MANGA_DIR / "MANGA.py"

