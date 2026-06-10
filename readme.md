# Saltmarsh manuscript repository manual

This repository contains the complete reproducible workflow for the saltmarsh manuscript simulations and figures. It is organized around three top-level scripts:

```text
create_setups.py
run_model.py
run_analysis.py
```

The intended workflow is:

```text
1. create_setups.py
   Create pyMANGA XML control files and the corresponding output folders.

2. run_model.py
   Run pyMANGA for all generated XML files and write raw outputs to data_raw/.

3. run_analysis.py
   Aggregate raw outputs, process data, prepare figure tables, and generate figures.
```

The expected local folder layout is:

```text
SourceCode/
├── pyMANGA-1/
│   └── MANGA.py
└── data_and_results/
    ├── create_setups.py
    ├── run_model.py
    ├── run_analysis.py
    └── ...
```

If your local folder layout differs, first check `source/utils/paths.py` and `run_model.py` before running simulations.

---

## Python version and command convention

This repository was tested with Python 3.12. Python 3.10 or newer is recommended. Older Python versions may work for parts of the workflow, but they are not tested and may cause dependency issues.

The command examples in this manual use `python` as a placeholder for the Python interpreter used for this project. Depending on the operating system and local Python installation, the correct command may differ. Common examples are:

```powershell
python --version
python3 --version
py --version
py -3.12 --version
```

Use the command that starts the Python version intended for this project. For example, the command shown in this manual as:

```powershell
python run_analysis.py
```

may need to be replaced by one of the following commands on another system:

```powershell
python3 run_analysis.py
py -3.12 run_analysis.py
```

---

## pyMANGA installation and folder layout

This repository contains the manuscript setup, input files, processing scripts, and figure scripts. It does not contain the full pyMANGA source code. To run the model simulations, pyMANGA must be installed separately.

Installation instructions for pyMANGA are available here:

[pyMANGA installation guide](https://pymanga.forst.tu-dresden.de/docs/getting_started/installation/)

For this manuscript workflow, pyMANGA must be available on the same folder level as this repository. The scripts assume the following directory layout:

```text
SourceCode/
├── pyMANGA-1/
│   ├── MANGA.py
│   └── ...
└── data_and_results/
    ├── create_setups.py
    ├── run_model.py
    ├── run_analysis.py
    ├── data_model_input/
    ├── source/
    └── ...
```

This folder layout is required because the XML setup files contain paths that are written relative to the pyMANGA working directory. When `run_model.py` starts a simulation, it runs `MANGA.py` from the pyMANGA folder and passes one XML file from `data_and_results/data_model_input/xml_control_files/`. The output paths in the XML files then point back to `data_and_results/data_raw/`.

If the repository and pyMANGA are not on the same folder level, the simulations may fail because pyMANGA cannot find input files, species files, salinity files, or output directories. In that case, either move the folders into the layout shown above or adapt the path settings in:

```text
source/utils/paths.py
run_model.py
```

After moving or renaming folders, always regenerate the XML files before running simulations:

```powershell
python create_setups.py
```

A quick check for the expected pyMANGA location is:

```powershell
Get-ChildItem ..\pyMANGA-1\MANGA.py
```

If this command does not find `MANGA.py`, the folder layout does not match the default configuration used by this repository.

---

## 1. Quick start

Before running the workflow, make sure that pyMANGA is installed and that the pyMANGA folder is located next to this repository as described above.

From the repository root:

```powershell
cd path\to\data_and_results
```

Create or activate a Python environment:

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Regenerate XML setups and output directories:

```powershell
python create_setups.py
```

List selected simulations without running them:

```powershell
python run_model.py --list-only
```

Run all simulations:

```powershell
python run_model.py
```

Run the complete analysis and figure pipeline:

```powershell
python run_analysis.py
```

If you only want to regenerate figures from existing processed data:

```powershell
python run_analysis.py --figures-only
```

If you only want to aggregate and process raw model output:

```powershell
python run_analysis.py --prepare-data-only
```

---

## 2. Repository structure

The repository is organized as follows:

```text
data_and_results/
├── data_model_input/
│   ├── plant_distribution/
│   ├── salinity/
│   ├── species/
│   └── xml_control_files/
│
├── data_raw/
│   ├── community/
│   ├── monoculture/
│   ├── one_plant/
│   └── logs/
│
├── data/
│   ├── community/
│   ├── monoculture/
│   └── derived_figure_data/
│
├── figures/
│   ├── main/
│   └── appendix/
│
├── source/
│   ├── utils/
│   │   ├── __init__.py
│   │   └── paths.py
│   ├── 01_read_raw_data.py
│   ├── 02_data_processing.py
│   ├── 03_figure_config.py
│   ├── 03_figure_utils.py
│   ├── 03_main_prepare_figure_data.py
│   ├── 03_plot_2_1_porewater_salinity.py
│   ├── 03_plot_2_2_forman.py
│   ├── 03_plot_2_3_growth_pot_maint.py
│   ├── 03_plot_3_1_static_community_vs_mono.py
│   ├── 03_plot_3_2_static_community.py
│   ├── 03_plot_3_3_dynamic_biovolume.py
│   └── 03_plot_appendix_1_static_monoculture.py
│
├── create_setups.py
├── run_model.py
├── run_analysis.py
├── requirements.txt
└── readme.md
```

### 2.1 `data_model_input/`

This folder contains everything that is needed before pyMANGA is run.

```text
data_model_input/
├── plant_distribution/
├── salinity/
├── species/
└── xml_control_files/
```

#### `data_model_input/plant_distribution/`

This folder stores fixed initial plant position files. The current one-plant reference setups use:

```text
one_plant.csv
```

The file is referenced from XML files generated by `create_setups.py`.

#### `data_model_input/salinity/`

This folder stores the dynamic porewater salinity input files:

```text
35_V1.csv
35_V2.csv
70_V1.csv
70_V2.csv
105_V1.csv
105_V2.csv
```

The naming convention is:

```text
<mean salinity>_<variant>.csv
```

where:

```text
V1 = seasonal porewater salinity scenario
V2 = seasonal porewater salinity scenario with additional tidal variability
```

Static salinity scenarios are not stored as CSV files. They are written directly into the XML files as constant values.

#### `data_model_input/species/`

This folder stores the active PFT parameter files used by pyMANGA:

```text
Saltmarsh_1.py
Saltmarsh_2.py
Saltmarsh_3.py
Saltmarsh_4.py
```

These files are the source of truth for PFT-specific model parameters. The figure script `03_plot_2_2_forman.py` reads relevant parameters from these files so that the salinity-response figure stays consistent with the active model setup.

Always change numerical PFT parameters in the species files, not in figure scripts.

#### `data_model_input/xml_control_files/`

This folder stores pyMANGA XML control files generated by:

```powershell
python create_setups.py
```

Do not edit these XML files manually. If you change paths, setup definitions, salinity scenarios, PFTs, outputs, or pyMANGA compatibility settings, rerun `create_setups.py`.

The current setup generator creates 300 XML files:

```text
community_static:      40 XML files
community_dynamic:     60 XML files
monoculture_static:   160 XML files
oneplant_static:       16 XML files
oneplant_dynamic:      24 XML files
```

### 2.2 `data_raw/`

This folder receives raw pyMANGA outputs. It is intentionally separated from processed data.

After running all simulations, the expected raw output structure is:

```text
data_raw/
├── community/
│   ├── static/
│   │   ├── 0.035/
│   │   │   ├── 01/Population.csv
│   │   │   ├── 02/Population.csv
│   │   │   └── ...
│   │   ├── 0.070/
│   │   ├── 0.105/
│   │   └── 0.140/
│   └── dynamic/
│       ├── 35_V1/
│       ├── 35_V2/
│       ├── 70_V1/
│       ├── 70_V2/
│       ├── 105_V1/
│       └── 105_V2/
│
├── monoculture/
│   └── static/
│       ├── 0.035/PFT_1/01/Population.csv
│       ├── 0.035/PFT_2/01/Population.csv
│       └── ...
│
├── one_plant/
│   ├── static/
│   └── dynamic/
│
└── logs/
```

The main manuscript analysis uses:

```text
data_raw/community/static/
data_raw/community/dynamic/
data_raw/monoculture/static/
```

The one-plant outputs are generated for reference but are not used by the current main analysis pipeline.

#### `data_raw/logs/`

`run_model.py` writes one log file per simulation and a central CSV log:

```text
data_raw/logs/simulation_log.csv
```

This CSV is used to skip simulations that already finished successfully. If `run_model.py` says no XML files need to run even though you expect simulations to run, check or remove this log file.

### 2.3 `data/`

This folder stores processed model output and derived figure data.

Expected structure after analysis:

```text
data/
├── community/
│   ├── static/
│   │   ├── raw_data.csv
│   │   └── data.csv
│   └── dynamic/
│       ├── raw_data.csv
│       └── data.csv
│
├── monoculture/
│   └── static/
│       ├── raw_data.csv
│       └── data.csv
│
└── derived_figure_data/
```

The `raw_data.csv` files are combined versions of many pyMANGA `Population.csv` files. The `data.csv` files contain derived columns such as plant volume and AG/BG ratio.

`data/derived_figure_data/` contains intermediate summary tables used by the figure scripts. These files are not manually edited.

### 2.4 `figures/`

Final figures are written to:

```text
figures/main/
figures/appendix/
```

The current standardized figure scripts write:

```text
figures/main/plot_2_1_porewater_salinity.png
figures/main/plot_2_1_porewater_salinity.pdf
figures/main/plot_2_2_forman.png
figures/main/plot_2_2_forman.pdf
figures/main/plot_2_3_growth_pot_maint.png
figures/main/plot_2_3_growth_pot_maint.pdf
figures/main/plot_3_1_static_community_vs_mono_biovolume_tot.png
figures/main/plot_3_1_static_community_vs_mono_biovolume_tot.pdf
figures/main/plot_3_2_static_community.png
figures/main/plot_3_2_static_community.pdf
figures/main/plot_3_3_dynamic_biovolume.png
figures/main/plot_3_3_dynamic_biovolume.pdf
figures/appendix/plot_appendix_1_static_monoculture.png
figures/appendix/plot_appendix_1_static_monoculture.pdf
```

---

## 3. Python dependencies

Install dependencies with:

```powershell
pip install -r requirements.txt
```

The requirements file lists external packages only, for example:

```text
numpy
pandas
matplotlib
seaborn
```

Standard-library modules such as the following are not listed because they come with Python:

```text
os
pathlib
subprocess
argparse
csv
datetime
glob
fnmatch
xml.etree.ElementTree
xml.dom.minidom
```

This repository was tested with Python 3.12. Python 3.10 or newer is recommended. The command examples in this manual use `python` as a placeholder for the interpreter selected for this project.

---

## 4. Main scripts

### 4.1 `create_setups.py`

`create_setups.py` is the setup generator. It creates XML control files for pyMANGA and prepares all corresponding output directories.

Run:

```powershell
python create_setups.py
```

This script defines the entire simulation design in one `CONFIG` dictionary. Important settings include:

```text
static salinities: 0.035, 0.070, 0.105, 0.140
dynamic salinities: 35, 70, 105
dynamic variants: V1, V2
replicates: 01 to 10
PFTs: 1 to 4
domain: 2 m × 2 m
time step: 86400 s
simulation end: 3.154e8 s
```

The script writes XMLs for:

```text
community_static
community_dynamic
monoculture_static
oneplant_static
oneplant_dynamic
```

The current growth outputs written by XML are:

```text
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
```

The current geometry outputs are:

```text
r_ag
h_ag
r_bg
h_bg
```

After running the setup script, check:

```powershell
Get-ChildItem data_model_input\xml_control_files\*.xml | Measure-Object
```

Expected:

```text
Count : 300
```

### 4.2 `run_model.py`

`run_model.py` runs pyMANGA simulations for the generated XML files. It assumes that the pyMANGA folder is located next to this repository and that `MANGA.py` is available at the path configured in `source/utils/paths.py`.

List selected XMLs:

```powershell
python run_model.py --list-only
```

Run all selected simulations:

```powershell
python run_model.py
```

Run only one category:

```powershell
python run_model.py --override-only community_static
```

Available categories are:

```text
community_static
community_dynamic
monoculture_static
oneplant_static
oneplant_dynamic
all
```

Rerun simulations even if they are already logged as successful:

```powershell
python run_model.py --include-done
```

Retry only failed simulations:

```powershell
python run_model.py --retry-errors
```

After running all simulations, check how many `Population.csv` files were written:

```powershell
Get-ChildItem data_raw -Recurse -Filter Population.csv | Measure-Object
```

Expected if all XMLs were run successfully:

```text
Count : 300
```

For the main manuscript analysis, at least these are required:

```text
community_static:      40 Population.csv files
community_dynamic:     60 Population.csv files
monoculture_static:   160 Population.csv files
```

### 4.3 `run_analysis.py`

`run_analysis.py` runs the post-processing and figure workflow.

Full workflow:

```powershell
python run_analysis.py
```

Data preparation only:

```powershell
python run_analysis.py --prepare-data-only
```

Figures only:

```powershell
python run_analysis.py --figures-only
```

The script runs these source scripts in order:

```text
01_read_raw_data.py
02_data_processing.py
03_main_prepare_figure_data.py
03_plot_2_1_porewater_salinity.py
03_plot_2_2_forman.py
03_plot_2_3_growth_pot_maint.py
03_plot_3_1_static_community_vs_mono.py
03_plot_3_2_static_community.py
03_plot_3_3_dynamic_biovolume.py
03_plot_appendix_1_static_monoculture.py
```

---

## 5. Source scripts

### 5.1 `source/01_read_raw_data.py`

This script reads all `Population.csv` files from `data_raw/` and writes combined raw tables to `data/`.

It adds metadata that are encoded in folder names, such as:

```text
salinity
version
variant
replicate
pft setup
```

This script intentionally fails if an expected `Population.csv` file is missing. This makes incomplete model runs visible immediately.

### 5.2 `source/02_data_processing.py`

This script reads the combined raw tables and calculates derived variables:

```text
ag_volume
bg_volume
volume
volume_per_plant
ag_bg_ratio
salinity labels
PFT identifiers
```

It also applies the seedling/age filter.

### 5.3 `source/03_main_prepare_figure_data.py`

This script prepares all intermediate CSV files needed by the figure scripts.

The current active outputs are:

```text
df_comm_prepared.csv
df_mono_prepared.csv
comm_mat.csv
mono_mat.csv
grouped_pft_static.csv
grouped_all_static.csv
summary_pft_tv.csv
median_ts_total_volume.csv
```

These files are stored in:

```text
data/derived_figure_data/
```

### 5.4 `source/03_figure_config.py`

This script stores shared plotting constants:

```text
figure sizes
PFT order
salinity order
PFT colors
input data paths
figure output paths
```

Changing PFT colors or global figure dimensions should be done here.

### 5.5 `source/03_figure_utils.py`

This script stores reusable helper functions for summaries, error bars, directories, and figure preparation.

### 5.6 `source/utils/paths.py`

This script defines all central repository paths. Scripts should import paths from here rather than hard-coding paths.

The most important paths are:

```text
REPO_ROOT
DATA_MODEL_INPUT
DATA_RAW
DATA
FIGURES
FIGURES_MAIN
FIGURES_APPENDIX
XML_CONTROL_FILES
DERIVED_FIGURE_DATA
DEFAULT_MANGA_SCRIPT
```

---

## 6. Figure scripts

### 6.1 `03_plot_2_1_porewater_salinity.py`

Creates the porewater salinity scenario figure 2.1.

Input:

```text
data_model_input/salinity/*.csv
```

Output:

```text
figures/main/plot_2_1_porewater_salinity.png
figures/main/plot_2_1_porewater_salinity.pdf
```

### 6.2 `03_plot_2_2_forman.py`

Creates the PFT-specific porewater salinity response figure 2.2.

Input:

```text
data_model_input/species/Saltmarsh_*.py
```

Output:

```text
figures/main/plot_2_2_forman.png
figures/main/plot_2_2_forman.pdf
```

### 6.3 `03_plot_2_3_growth_pot_maint.py`

Creates the conceptual growth-potential versus maintenance figure 2.3.

Output:

```text
figures/main/plot_2_3_growth_pot_maint.png
figures/main/plot_2_3_growth_pot_maint.pdf
```

### 6.4 `03_plot_3_1_static_community_vs_mono.py`

Creates the static total biovolume comparison between community and monoculture simulations figure 3.1.

Output:

```text
figures/main/plot_3_1_static_community_vs_mono_biovolume_tot.png
figures/main/plot_3_1_static_community_vs_mono_biovolume_tot.pdf
```

### 6.5 `03_plot_3_2_static_community.py`

Creates the static community figure 2.2.

Panels:

```text
upper left:  biovolume per plant
upper right: aboveground height
lower left:  AG/BG ratio
lower right: number of plants
```

Error bars:

```text
plant-level metrics: individual-plant range
number of plants: replicate-level aggregate range
```

Output:

```text
figures/main/plot_3_2_static_community.png
figures/main/plot_3_2_static_community.pdf
```

### 6.6 `03_plot_3_3_dynamic_biovolume.py`

Creates the dynamic biovolume time-series and stacked-bar figure 2.3.

Layout:

```text
rows: salinity levels 35, 70, 105 ppt
columns: PFT 1, PFT 2, PFT 3, PFT 4, Total
lines: V0, V1, V2
bars: stacked PFT contributions for V0, V1, V2
```

Output:

```text
figures/main/plot_3_3_dynamic_biovolume.png
figures/main/plot_3_3_dynamic_biovolume.pdf
```

### 6.7 `03_plot_appendix_1_static_monoculture.py`

Creates the static monoculture figure.

Output:

```text
figures/appendix/plot_appendix_1_static_monoculture.png
figures/appendix/plot_appendix_1_static_monoculture.pdf
```

---

## 8. Troubleshooting

### Problem: `FileNotFoundError: Missing Population.csv`

Cause: `run_analysis.py` was started before all required simulations were completed, or outputs were written to a different folder.

Check:

```powershell
Get-ChildItem data_raw -Recurse -Filter Population.csv | Measure-Object
```

If the count is too low, rerun missing simulations.

### Problem: `No XML files to run`

Cause: `run_model.py` found that all selected XMLs are already marked as OK in `data_raw/logs/simulation_log.csv`.

Solutions:

```powershell
python run_model.py --include-done
```

or remove the simulation log:

```powershell
Remove-Item data_raw\logs\simulation_log.csv
```

### Problem: pyMANGA cannot find an output directory

Run:

```powershell
python create_setups.py
```

This regenerates XML files and creates all expected output directories under `data_raw/`.

### Problem: figures are not updated

Regenerate figure data and figures:

```powershell
python run_analysis.py
```

If processed data already exists and only figure styles changed:

```powershell
python run_analysis.py --figures-only
```

---

## 10. Notes on reproducibility

- The XML files are generated, not manually curated.
- The species files define active model parameters.
- `data_raw/` should contain unmodified pyMANGA outputs.
- `data/` is derived from `data_raw/`.
- `figures/` is derived from `data/` and `data_model_input/`.
- The figure scripts are standardized by manuscript figure numbering.
- The repository assumes pyMANGA's `SaltmarshModel` branch and the current `SizeThreshold` mortality module name.

---

## 11. Minimal command summary

```powershell
python create_setups.py
python run_model.py --list-only
python run_model.py
python run_analysis.py
```

For debugging:

```powershell
python run_model.py --override-only community_static
python run_analysis.py --prepare-data-only
python run_analysis.py --figures-only
```
