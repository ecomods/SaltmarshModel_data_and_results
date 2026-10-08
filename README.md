# Salinity tolerance trade-offs in salt-marsh plant communities

Model setup, simulation output and analysis code for the manuscript
"Salinity tolerance trade-offs shape plant communities across static and
dynamic salinity regimes: insights from an individual-based model" (in
review). <!-- TODO: final title and reference after acceptance -->

The simulations use the individual-based model
[pyMANGA](https://github.com/pymanga/pyMANGA) with four plant functional
types (PFTs) that differ only in salinity tolerance and maintenance costs.
All figures of the manuscript and the supplement can be recreated from this
repository. Rerunning the simulations also requires pyMANGA.

Authors: Jonas Vollhüter, Selina Baldauf

Contact: <!-- TODO: contact email -->

## Contents

```text
model_input/      species parameters, salinity scenarios, XML control files
model_output/     pyMANGA output, one Population.csv per simulation
figure_data/      the 7 tables behind the figures
figures/          main/ (Figures 1-4) and appendix/ (Figures S1-S3)
source/           figure-table preparation, figure scripts, shared modules

create_setups.py              write the XML control files
run_model.py                  run the simulations with pyMANGA
run_analysis.py               create the figure tables and figures
calibrate_maintenance.py      calibrate the PFT maintenance factors
create_salinity_scenarios.py  create the salinity scenarios
```

The files in `model_output/` and `figure_data/` are described in the README
of each folder.

## Installation

The results were produced with Python 3.13.1 and the package versions in
`requirements.txt`:

```powershell
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
```

pyMANGA is only needed to rerun the simulations. Place it next to this
repository in a folder called `pyMANGA` (another location can be set in
`source/paths.py`). The simulations were run with commit `20dcbfc`:

```powershell
git clone https://github.com/pymanga/pyMANGA.git
cd pyMANGA
git checkout 20dcbfcd993af54000d6bdb421c459ceac7a4c05
```

## Recreating the figures

```powershell
python run_analysis.py --figures-only   # figures from the tables in figure_data/
python run_analysis.py                  # first recreate figure_data/ from model_output/ (about 30 s)
```

| Figure | Script in `source/` | Output in `figures/` |
| --- | --- | --- |
| 1 | `02_fig1_salinity_response.py` | `main/fig1_salinity_response.png` |
| 2 | `03_fig2_community_vs_monoculture.py` | `main/fig2_community_vs_monoculture.png` |
| 3 | `04_fig3_community_structure.py` | `main/fig3_community_structure.png` |
| 4 | `05_fig4_dynamic_biovolume.py` | `main/fig4_dynamic_biovolume.png` |
| S1 | `06_figS1_growth_vs_maintenance.py` | `appendix/figS1_growth_vs_maintenance.png` |
| S2 | `07_figS2_porewater_salinity.py` | `appendix/figS2_porewater_salinity.png` |
| S3 | `08_figS3_monoculture_structure.py` | `appendix/figS3_monoculture_structure.png` |

The tables in `figure_data/` are written by `source/01_prepare_figure_data.py`.
It uses output from years 5-10 (every 10th day) and excludes plants younger
than 10 days. For each replicate, values are summarised per output step and
then averaged over time. Steps without plants count as 0 biovolume and 0
plants; per-plant values are averaged only over steps with plants. Figures
show the mean of the ten replicates, error bars one standard deviation.

## Rerunning the simulations

```powershell
python create_setups.py   # write the XML control files
python run_model.py       # run all 300 simulations
python run_analysis.py    # recreate the tables and figures
```

The XML files contain paths relative to the pyMANGA folder, so run
`create_setups.py` again after moving or renaming this repository or
pyMANGA. With 6 parallel runs, all simulations take about 1 hour. Completed
runs are logged in `model_output/logs/` and skipped, so an interrupted batch
can be restarted. `python run_model.py --help` lists the options.

The random seed of each simulation is its replicate number, so reruns give
identical output. The committed XML files differ from the ones used for the
simulations only in the folder names in their paths.

The 40 one-plant runs are not used by the figures. They show the single-plant
behaviour behind the calibration: at 70 ppt all four PFTs reach the same
aboveground height (about 1.022 m) within 200 days.

## Salinity scenarios

`model_input/salinity/` contains the daily porewater salinity of the dynamic
scenarios: seasonal (V1) and seasonal with tides (V2), with mean salinities
of 35, 70 and 105 ppt. They were derived from the hourly porewater salinity in
`model_input/salinity_from_model.npz`, simulated with
<!-- TODO: model, site and reference of the hourly salinity data -->.

`create_salinity_scenarios.py` shows how the scenarios were created and can be
used for new ones. It overwrites the files in `model_input/salinity/`.

## Calibration of the maintenance factors

`calibrate_maintenance.py` shows how the maintenance factors `p_maint` in the
species files were obtained. A single plant is grown for 200 days at 70 ppt.
PFT 1 keeps `p_maint = 1.5e-6`; for PFTs 2-4, `p_maint` is set so that the
plant reaches the same height as PFT 1.

```powershell
python calibrate_maintenance.py
```

Result: 1.500e-6, 1.867e-6, 2.216e-6 and 2.517e-6 (rounded to four digits in
the species files).

## How to cite

<!-- TODO: citation and DOI of the paper and of the archived repository -->

## License

The code is licensed under the MIT License, see `LICENSE`.
<!-- TODO: license for model_input/, model_output/, figure_data/ and figures/
(proposed: CC BY 4.0), to be agreed with Jonas -->
