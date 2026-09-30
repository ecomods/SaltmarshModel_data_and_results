"""
Central paths of the repository.

All paths are built from the repository root, so scripts work from any
working directory. Scripts in source/ use `import paths`, scripts in the
repository root `from source.paths import ...`.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

DATA_MODEL_INPUT = REPO_ROOT / "data_model_input"
DATA_RAW = REPO_ROOT / "data_raw"
DATA = REPO_ROOT / "data"
FIGURES = REPO_ROOT / "figures"

PLANT_DISTRIBUTION_DIR = DATA_MODEL_INPUT / "plant_distribution"
SALINITY_DIR = DATA_MODEL_INPUT / "salinity"
SPECIES_DIR = DATA_MODEL_INPUT / "species"
XML_CONTROL_FILES = DATA_MODEL_INPUT / "xml_control_files"

LOG_DIR = DATA_RAW / "logs"
SIMULATION_LOG = LOG_DIR / "simulation_log.csv"

FIGURES_MAIN = FIGURES / "main"
FIGURES_APPENDIX = FIGURES / "appendix"

# pyMANGA is expected next to this repository. Change DEFAULT_MANGA_DIR if it
# is stored elsewhere, then rerun create_setups.py.
DEFAULT_MANGA_DIR = REPO_ROOT.parent / "pyMANGA"
DEFAULT_MANGA_SCRIPT = DEFAULT_MANGA_DIR / "MANGA.py"

