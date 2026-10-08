# Model output

Output from 300 pyMANGA simulations on a 2 m x 2 m plot, using a daily
time step and a maximum duration of 10 years. The analysis uses the
260 community and monoculture runs.

| Folder | Runs | Setup | Output steps |
| --- | --- | --- | --- |
| `community/static/<salinity>/<replicate>/` | 40 | four PFTs together | every 10th day, years 5-10 |
| `community/dynamic/<scenario>/<replicate>/` | 60 | four PFTs together | every 10th day, years 5-10 |
| `monoculture/static/<salinity>/PFT_<pft>/<replicate>/` | 160 | each PFT alone | every 10th day, years 5-10 |
| `one_plant/static/<salinity>/PFT_<pft>/` | 16 | single plant | daily |
| `one_plant/dynamic/<scenario>/PFT_<pft>/` | 24 | single plant | daily |

Static salinities are 35, 70, 105 and 140 ppt, stored in folders named
`0.035`, `0.070`, `0.105` and `0.140`. Dynamic scenarios
are `35_V1` to `105_V2` (mean salinity, seasonal V1 or seasonal with
tides V2). Replicates are `01` to `10`.

## `Population.csv`

Model output in separate folders per scenario. Tab-separated, one row per plant and output step:

- `plant`: `Saltmarsh_<pft>_<id>`
- `time`: s
- `x`, `y`: position (m)
- `r_ag`, `h_ag`, `r_bg`, `h_bg`: radius and height of the above- and
  belowground cylinder (m)
- `aboveground_resources`, `belowground_resources`: resource availability
  factors (dimensionless)
- `res_ag`, `res_bg`, `res_eff`: aboveground, belowground and limiting
  resource supply (J per time step)
- `grow`, `maint`: net growth and maintenance cost (m³ per time step)
- `volume`: plant volume (m³)
- `age`: s
- `salinity`: porewater salinity at the plant (kg/kg)
- `transpiration`: soil water uptake (m³ per time step)

The one-plant runs stop when the plant dies. pyMANGA then writes
`Population_group_died.csv` with the same columns.
