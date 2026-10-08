# Model output

pyMANGA output of the 300 simulations, written by `run_model.py`. All
simulations cover 10 years with a daily time step on a 2 m x 2 m plot. The
analysis uses the 260 community and monoculture runs.

| Folder | Runs | Setup | Output steps |
| --- | --- | --- | --- |
| `community/static/<salinity>/<replicate>/` | 40 | four PFTs together | every 10th day, years 5-10 |
| `community/dynamic/<scenario>/<replicate>/` | 60 | four PFTs together | every 10th day, years 5-10 |
| `monoculture/static/<salinity>/PFT_<pft>/<replicate>/` | 160 | each PFT alone | every 10th day, years 5-10 |
| `one_plant/static/<salinity>/PFT_<pft>/` | 16 | single plant | daily |
| `one_plant/dynamic/<scenario>/PFT_<pft>/` | 24 | single plant | daily |

Static salinities are 0.035, 0.070, 0.105 and 0.140 kg/kg; dynamic scenarios
are `35_V1` to `105_V2` (mean salinity in ppt, seasonal V1 or seasonal with
tides V2). Replicates are `01` to `10`.

## `Population.csv`

Tab-separated, one row per plant and output step:

- `plant`: `Saltmarsh_<pft>_<id>`
- `time`: s
- `x`, `y`: position (m)
- `r_ag`, `h_ag`, `r_bg`, `h_bg`: radius and height of the above- and
  belowground cylinder (m)
- `aboveground_resources`, `belowground_resources`, `res_ag`, `res_bg`,
  `res_eff`, `grow`, `maint`: resource and growth variables of the pyMANGA
  Saltmarsh model
- `volume`: plant volume (m³)
- `age`: s
- `salinity`: porewater salinity at the plant (kg/kg)
- `transpiration`

The one-plant runs also contain `Population_group_died.csv`, written by
pyMANGA when the plant dies, with the same columns.
