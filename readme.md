# Saltmarsh model: simulations and figures

This repository contains the model setup, the simulation output and the
analysis code for the manuscript on salinity tolerance trade-offs in
salt-marsh plant communities. The simulations use the individual-based model
[pyMANGA](https://github.com/pymanga/pyMANGA) with four plant functional types
(PFTs) that differ only in salinity tolerance and maintenance costs.

All figures of the manuscript and the supplement can be recreated from the
files in this repository. Rerunning the simulations additionally requires
pyMANGA.

## Repository structure

```text
model_input/          model input
    species/              parameters of the four PFTs (Saltmarsh_1.py to _4.py)
    salinity/             dynamic salinity scenarios (35, 70, 105 ppt; V1, V2)
    plant_distribution/   initial position of the single plant (one-plant runs)
    xml_control_files/    one pyMANGA control file per simulation (300)
model_output/         pyMANGA output: one Population.csv per simulation
figure_data/          the 7 tables behind the figures
figures/              main/ (Figures 1-4) and appendix/ (Figures S1-S3)
source/               data preparation, figure scripts and shared modules

create_setups.py          write the XML control files
run_model.py              run the simulations with pyMANGA
run_analysis.py           prepare the figure tables and create all figures
calibrate_maintenance.py  calibration of the PFT maintenance factors
```

The workflow is `create_setups.py` → `run_model.py` → `run_analysis.py`.

## Installation

The results were produced with Python 3.13.1 and the package versions in
`requirements.txt`. From the repository folder:

```powershell
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
```

pyMANGA is only needed to rerun the simulations. It must be placed next to
this repository in a folder called `pyMANGA`:

```text
pyMANGA/
data_and_results/       this repository (any folder name)
```

The simulations were run with pyMANGA commit `20dcbfc` (branch `master`,
26 June 2026):

```powershell
git clone https://github.com/pymanga/pyMANGA.git
cd pyMANGA
git checkout 20dcbfcd993af54000d6bdb421c459ceac7a4c05
```

See the [pyMANGA documentation](https://pymanga.forst.tu-dresden.de/docs/getting_started/installation/)
for details. A different location can be set in `source/paths.py`.

## Recreating the figures

To create all figures from the committed tables in `figure_data/`:

```powershell
python run_analysis.py --figures-only
```

To first recreate the tables from the simulation output in `model_output/`
(about 15 s) and then the figures:

```powershell
python run_analysis.py
```

`python run_analysis.py --prepare-data-only` only recreates the tables. Each
script in `source/` can also be run on its own.

| Figure | Script in `source/` | Input | Output |
| --- | --- | --- | --- |
| 1 | `02_fig1_salinity_response.py` | `model_input/species/` | `figures/main/fig1_salinity_response.png` |
| 2 | `03_fig2_community_vs_monoculture.py` | `comm_mat.csv`, `mono_mat.csv` | `figures/main/fig2_community_vs_monoculture.png` |
| 3 | `04_fig3_community_structure.py` | `grouped_pft_static.csv`, `grouped_all_static.csv` | `figures/main/fig3_community_structure.png` |
| 4 | `05_fig4_dynamic_biovolume.py` | `ts_total_volume.csv`, `summary_pft_tv.csv` | `figures/main/fig4_dynamic_biovolume.png` |
| S1 | `06_figS1_growth_vs_maintenance.py` | `model_input/species/` | `figures/appendix/figS1_growth_vs_maintenance.png` |
| S2 | `07_figS2_porewater_salinity.py` | `model_input/salinity/` | `figures/appendix/figS2_porewater_salinity.png` |
| S3 | `08_figS3_monoculture_structure.py` | `grouped_pft_mono_static.csv` | `figures/appendix/figS3_monoculture_structure.png` |

The `.csv` inputs are in `figure_data/`. They are written by
`source/01_prepare_figure_data.py`. Shared style, sizes and colours are in
`source/figure_config.py`, shared functions in `source/figure_utils.py`.

### How the output is summarised

Only output from years 5-10 is used (every 10th day), and plants younger than
10 days are excluded. Plant volume is calculated from the cylinder geometry
of the above- and belowground parts. For each replicate simulation, the
values are first summarised per output step (total biovolume, mean biovolume
per plant, mean height, mean AG/BG ratio, number of plants) and then averaged
over the output steps. An output step without plants (of a PFT, or at all)
counts as 0 total biovolume and 0 plants. The per-plant values are undefined
without plants and are averaged only over the steps with plants. Figures
show the mean of the ten replicates; error
bars (Figures 3 and S3) show one standard deviation across replicates. The
lines in Figure 4 are the mean across replicates at each output step.

## Rerunning the simulations

1. Write the XML control files and output folders:

   ```powershell
   python create_setups.py
   ```

   The XML files contain paths relative to the pyMANGA folder. Run this
   script again after cloning, moving or renaming the repository or pyMANGA.

2. Run pyMANGA for all 300 simulations:

   ```powershell
   python run_model.py --list-only   # show the selected simulations
   python run_model.py
   ```

   With 6 parallel runs (`MAX_WORKERS` in `run_model.py`), all simulations
   take about 1 hour. Each run writes a log file to `model_output/logs/`, and
   `model_output/logs/simulation_log.csv` records its exit status. Runs marked
   OK in that file are skipped, so an interrupted batch can simply be
   restarted. Useful options:

   ```powershell
   python run_model.py --override-only community_static   # one category
   python run_model.py --retry-errors                     # only failed runs
   python run_model.py --include-done                     # also completed runs
   ```

3. Recreate the tables and figures with `python run_analysis.py`.

The random seed of each simulation is its replicate number, so reruns give
identical output. The XML files in this repository were regenerated after
the folders were renamed (from `data_model_input`, `data_raw` and `data`);
apart from these paths they are identical to the files used for the
simulations.

### Simulations

All simulations cover 10 years with a daily time step on a 2 m x 2 m plot.

| Category | Runs | Setup | Output |
| --- | --- | --- | --- |
| `community_static` | 40 | 4 PFTs together; 35, 70, 105, 140 ppt; 10 replicates | every 10th day, years 5-10 |
| `community_dynamic` | 60 | 4 PFTs together; 35, 70, 105 ppt; V1 (seasonal), V2 (seasonal + tide); 10 replicates | every 10th day, years 5-10 |
| `monoculture_static` | 160 | each PFT alone; 35, 70, 105, 140 ppt; 10 replicates | every 10th day, years 5-10 |
| `oneplant_static` | 16 | single plant of each PFT, no competition; 4 salinities | daily |
| `oneplant_dynamic` | 24 | single plant of each PFT; 6 dynamic scenarios | daily |

The static community runs at 35, 70 and 105 ppt are the static regime (V0)
in Figure 4.

The one-plant runs are not used by the analysis scripts. They document the
single-plant behaviour behind the calibration: at 70 ppt all four PFTs reach
the same steady aboveground height (about 1.022 m, within 200 days). The
plant is removed after about 420-460 days, and PFTs 1-3 do not survive at
140 ppt.

## Data

### `model_input/`

- `species/Saltmarsh_1.py` to `Saltmarsh_4.py`: PFT parameters. They differ
  only in salinity tolerance (`salt_effect_ui`) and maintenance factor
  (`p_maint`).
- `salinity/{35,70,105}_{V1,V2}.csv`: daily porewater salinity (kg/kg) for
  20 years; `t_step` in seconds and two identical salinity columns. The
  static salinities are written directly into the XML files.
- `plant_distribution/one_plant.csv`: position and initial size of the plant
  in the one-plant runs.
- `xml_control_files/`: generated by `create_setups.py`; do not edit by hand.

### `model_output/`

Folders follow the setup, for example
`community/static/0.035/01/Population.csv` (salinity in kg/kg, replicate 01)
or `monoculture/static/0.070/PFT_2/05/Population.csv`. Each file is
tab-separated with one row per plant and output step, as written by pyMANGA:
plant name (`Saltmarsh_<PFT>_<id>`), `time` (s), position, geometry (`r_ag`,
`h_ag`, `r_bg`, `h_bg` in m), resources, growth, maintenance, volume, `age`
(s), salinity at the plant and transpiration. The analysis uses the 260
community and monoculture files.

### `figure_data/`

Salinities are in ppt and `n` is the replicate. All values are biovolume in
m³ unless stated otherwise.

| File | Content |
| --- | --- |
| `comm_mat.csv`, `mono_mat.csv` | mean total biovolume per salinity (rows) and PFT (columns), community and monocultures |
| `grouped_pft_static.csv` | community, one row per salinity, PFT and replicate: time means of total biovolume, biovolume per plant, height (m), AG/BG ratio and number of plants (per-plant values empty where a PFT never had plants) |
| `grouped_all_static.csv` | the same for the whole community (`pft` = 0) |
| `grouped_pft_mono_static.csv` | the same for the monocultures |
| `summary_pft_tv.csv` | dynamic runs: mean, minimum and maximum across replicates of the time-mean total biovolume per salinity, regime (`variant` V0-V2) and PFT |
| `ts_total_volume.csv` | dynamic runs: total biovolume per PFT and output day (`time_days`), mean across replicates; `version` is salinity and regime, e.g. `35_V1` |

### Plant-level data for new analyses

The cleaned plant rows are not saved. They can be loaded from `model_output/`
with the functions in `source/figure_utils.py` (from the `source/` folder):

```python
import figure_utils
plants = figure_utils.load_static_community()
# also: load_static_monoculture(), load_dynamic_community()
```

Each returns one row per plant and output step with the scenario columns
(`salinity`, `n`, and for dynamic runs `variant` and `version`), the PFT,
above- and belowground volume, total volume and AG/BG ratio. Seedlings are
removed; the model's salinity at the plant is kept as `plant_salinity`.
Output steps without plants have no rows. For totals or plant numbers per
output step, add them as zeros with `figure_utils.fill_missing_steps()`.

## Calibration of the maintenance factors

`calibrate_maintenance.py` documents how the PFT-specific maintenance factors
`p_maint` in the species files were obtained. A single plant is grown for 200
days at 70 ppt with a re-implementation of the pyMANGA Saltmarsh growth step.
PFT 1 keeps `p_maint = 1.5e-6`; for PFTs 2-4, `p_maint` is found by bisection
so that the plant reaches the same aboveground height as PFT 1. The script
prints its results and runs in about a second:

```powershell
python calibrate_maintenance.py
```

Result: 1.500e-6, 1.867e-6, 2.216e-6 and 2.517e-6 (rounded to four digits in
the species files).

## License

MIT, see `LICENSE`.
