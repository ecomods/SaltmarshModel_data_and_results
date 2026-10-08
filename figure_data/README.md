# Figure data

Seven tables used by the figure scripts, written by
`source/01_prepare_figure_data.py` from `model_output/`. Salinity is in ppt,
`n` is the replicate and biovolume is in m³.

| File | Figures | Content |
| --- | --- | --- |
| `comm_mat.csv`, `mono_mat.csv` | 2 | mean total biovolume per salinity (rows) and PFT (columns), community and monocultures |
| `grouped_pft_static.csv` | 3 | static community runs, one row per salinity, PFT and replicate: time means of total biovolume, biovolume per plant, height `h_ag` (m), aboveground/belowground biovolume ratio (`ag_bg_ratio`) and number of plants |
| `grouped_all_static.csv` | 2, 3 | the same for the whole community (`pft` = 0) |
| `grouped_pft_mono_static.csv` | 2, S3 | the same for the monocultures |
| `summary_pft_tv.csv` | 4 | static and dynamic community runs: mean, minimum and maximum across replicates of the time-mean total biovolume per salinity, regime (`variant` V0-V2) and PFT |
| `ts_total_volume.csv` | 4 | static and dynamic community runs: mean total biovolume across replicates per PFT and output day (`time_days`); `version` is salinity and regime, e.g. `35_V1` |

Per-plant values are blank when no plants aged at least 10 days occur in
that PFT or community during the replicate's analysis period.
