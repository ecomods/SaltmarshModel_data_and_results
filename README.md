# Salinity tolerance trade-offs in salt-marsh plant communities

Model setup, simulation output and analysis code for the manuscript:

Vollhüter, J., Baldauf, S., Wimmler, M.-C., Berger, U., Peters, R.,
Mehlig, U., & Tietjen, B. (submitted). Salinity tolerance trade-offs shape plant communities across static and dynamic salinity regimes: insights from an individual-based model.

The simulations use the individual-based model
[pyMANGA](https://github.com/pymanga/pyMANGA) with four plant functional
types (PFTs) that differ only in salinity tolerance and maintenance costs.
All figures of the manuscript and the supplement can be recreated from this
repository. Rerunning the simulations also requires downloading [pyMANGA v3.3.0](https://github.com/pymanga/pyMANGA/releases/tag/v3.3.0).

Code authors: Jonas Vollhüter, Selina Baldauf

Contact: selina.baldauf@fu-berlin.de

## Repository contents

```text
model_input/      species parameters, salinity scenarios, XML control files
model_output/     pyMANGA output, one Population.csv per simulation
figure_data/      seven model output summary tables used by the figure scripts
figures/          main/ (Figures 1-4) and appendix/ (Figures S1-S3)
source/           figure-table preparation, figure scripts, shared functions

create_setups.py              write the XML control files for the simulations
run_model.py                  run the simulations with pyMANGA
run_analysis.py               create the figure tables and figures
calibrate_maintenance.py      calibrate the PFT maintenance factors
create_salinity_scenarios.py  create the salinity scenarios
```

Detailed data file descriptions are in [model_output/README.md](model_output/README.md) and [figure_data/README.md](figure_data/README.md).

## Installation

The results were produced with Python 3.13.1 and the package versions in
`requirements.txt`. Run these commands from the repository root to set up
an environment and install the dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1    # macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Recreating the figures

Run the following scripts to re-create the figures

```powershell
python run_analysis.py --figures-only   # figures from the tables in figure_data/
python run_analysis.py                  # first recreate figure_data/ from model_output/ (about 30 s)
```

`source/01_prepare_figure_data.py` creates the seven tables in `figure_data/`
from the simulation output. See [figure_data/README.md](figure_data/README.md)
for their contents and summary methods.

| Figure | Script in `source/` | Output in `figures/` |
| --- | --- | --- |
| 1 | `02_fig1_salinity_response.py` | `main/fig1_salinity_response.png` |
| 2 | `03_fig2_community_vs_monoculture.py` | `main/fig2_community_vs_monoculture.png` |
| 3 | `04_fig3_community_structure.py` | `main/fig3_community_structure.png` |
| 4 | `05_fig4_dynamic_biovolume.py` | `main/fig4_dynamic_biovolume.png` |
| S1 | `06_figS1_growth_vs_maintenance.py` | `appendix/figS1_growth_vs_maintenance.png` |
| S2 | `07_figS2_porewater_salinity.py` | `appendix/figS2_porewater_salinity.png` |
| S3 | `08_figS3_monoculture_structure.py` | `appendix/figS3_monoculture_structure.png` |

## Rerunning the simulations

To re-run the simulation, you need to download the pyMANGA model and place it next to this
repository in a folder called `pyMANGA` (another location can be set in
`source/paths.py`). The simulations were run with pyMANGA v3.3.0 and you can download the official release [here](https://github.com/pymanga/pyMANGA/releases/tag/v3.3.0):

```powershell
python create_setups.py   # write the XML control files
python run_model.py       # run all 300 simulations
python run_analysis.py    # recreate the tables and figures
```

The XML files contain paths relative to the pyMANGA folder, so run
`create_setups.py` again after moving or renaming this repository or
pyMANGA. With 6 parallel runs, all simulations take about 1-2 hours. Completed
runs are logged in `model_output/logs/` and skipped, so an interrupted batch
can be restarted. `python run_model.py --help` lists the options.

The random seed of each simulation is its replicate number, so reruns give
identical output.

The 40 one-plant runs are not used by the figures. They show the single-plant
behaviour behind the calibration: at 70 ppt all four PFTs reach the same
aboveground height (about 1.022 m) within 200 days.

## Salinity scenarios

`model_input/salinity/` contains the daily porewater salinity of the dynamic
scenarios: seasonal (V1) and seasonal with tides (V2), with mean salinities
of 35, 70 and 105 ppt. They were derived from the hourly porewater salinity in
`model_input/salinity_from_model.npz`.

`create_salinity_scenarios.py` generates and plots salinity scenarios.
Run it only to generate new salinity inputs; it overwrites `model_input/salinity/`.

## Calibration of the maintenance factors

`calibrate_maintenance.py` shows how the maintenance factors `p_maint` in the
species files were obtained. A single plant is grown for 200 days at 70 ppt.
PFT 1 keeps `p_maint = 1.5e-6`; for PFTs 2-4, `p_maint` is set so that the
plant reaches the same height as PFT 1.

```powershell
python calibrate_maintenance.py
```

Result: 1.500e-6, 1.867e-6, 2.216e-6 and 2.517e-6 (rounded to four significant
figures in the species files).

## How to cite

*Will be added after acceptance*

## License

The code is licensed under the MIT License, see `LICENSE`. The data in
`model_input/`, `model_output/`, `figure_data/` and `figures/` are licensed
under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
