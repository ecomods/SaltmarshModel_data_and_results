# Review notes — Saltmarsh research compendium

Reviewer: Selina Baldauf · Branch: `review_selina` · Started 2026-06-08 · Updated 2026-06-09

**Goal:** confirm the compendium runs, the analysis is sound, and it is reproducible enough to
publish as a digital appendix to the manuscript.

**Status:**
- **Stage 1 — figures from committed data:** reproduces cleanly ✅ (Pass 1).
- **Stage 2 — run the model:** runs on **Python 3.13** after installing `vtk`; a 40-sim
  `community_static` re-run reproduces manuscript behaviour within **~1.6%** ✅ (Pass 5).
  Needs the `run_model.py` / `paths.py` fixes (applied on this branch).
- **Setups:** `create_setups.py` regenerates the 300 XMLs byte-identical ✅ (Pass 2).
- **Pending:** Pass 3 (read analysis source for scientific logic); finish Pass 4 hygiene
  (file naming, LICENSE + citation).
- **Critical handover items:** E2 (pin pyMANGA) and R1 (random seed). See *Questions for Jonas*.

**Legend.** Severity: 🔴 blocker · 🟡 should-fix · 🔵 nice-to-have. ID area: **E** environment,
**A** analysis pipeline, **S** science / analysis logic (Pass 3), **R** reproducibility/provenance,
**H** hygiene (label only, not priority).

---

## Priority index

| Sev | ID | Issue | Where |
|-----|----|-------|-------|
| 🔴 | E2 | pyMANGA version not pinned (personal-fork PR branch) | pyMANGA checkout · README |
| 🔴 | R1 | No random seed → runs not bit-reproducible | `create_setups.py` / XMLs |
| 🟡 | E1 | `py -3.12` hardcoded but not actually required | `run_model.py:81` · README |
| 🟡 | E3 | `vtk` is a hidden, undocumented runtime dependency | `requirements.txt` · pyMANGA |
| 🟡 | E4 | README is not a working recipe for running the model | `readme.md` |
| 🟡 | A2 | Derived `data/` ≈ 6.7 GB from triple duplication | `source/01`, `source/02` |
| 🟡 | A4 | ~2 GB of split `data.csv` written but never read | `source/02_data_processing.py` |
| 🟡 | A8 | Data-prep can be ~10–20× smaller | `source/01`+`02`, `03_figure_utils.py` |
| 🟡 | A5 | Age filter documented in the wrong place; magic number | `source/02` docstring, `03_figure_utils.py` |
| 🟡 | A3 | Missing-file handling inconsistent (monoculture) | `source/01_read_raw_data.py:178` |
| 🟡 | S3 | Unexplained `.replace(10, 105)` on dynamic salinity | `source/03_figure_utils.py:93` |
| 🟡 | S5 | PFT "cost" labels contradict actual `p_maint` (PFT2/3) | `source/03_plot_2_2_forman.py` · `species/*.py` |
| 🟡 | R2 | PFT parameters undocumented; no calibration provenance | `data_model_input/species/*.py` |
| 🟡 | R3 | Dynamic salinity inputs have no provenance | `data_model_input/salinity/*.csv` |
| 🔵 | A1 | Split `data/` files undocumented (moot if A4 applied) | README §2.3 · `source/02` |
| 🔵 | A6 | `extract_pft_from_plant_id` is fragile | `source/02_data_processing.py:65` |
| 🔵 | A7 | pandas `FutureWarning`s on every run | `source/03_figure_utils.py` |
| 🔵 | A9 | Stale `# resource module FON` comment | `data_model_input/species/*.py:24` |
| 🔵 | S1 | Realized `salinity` column overwritten with scenario label | `source/01_read_raw_data.py` |
| 🔵 | S2 | `ag_bg_ratio` unguarded div-by-zero; `volume` recompute redundant | `source/02_data_processing.py` |
| 🔵 | S4 | Plant-level error bars pool over plant×timestep (time+plant spread) | `source/03_plot_3_2_static_community.py` |
| 🔵 | S6 | `plot_2_3` hardcodes model constants (match now); drift risk | `source/03_plot_2_3_growth_pot_maint.py` |
| 🔵 | S7 | `plot_3_3` "Total" bars may be clipped by shared y-limits | `source/03_plot_3_3_dynamic_biovolume.py` |
| 🔵 | H1 | ~~No `.gitignore`~~ — **resolved** | `.gitignore` |

---

## Findings

### Environment (E)

#### E2 🔴 pyMANGA version is not pinned
**Where:** pyMANGA checkout; README §"Notes on reproducibility".
**Problem:** the model runs from commit `bab0c0dc`, branch `pr/jvollhueter/380`, on a *personal
fork* (`github.com/jvollhueter/pymanga-1`). The README only says "the `SaltmarshModel` branch" —
wrong name, pins nothing. A PR branch on a personal fork can be force-pushed/deleted by the
departing author; if it disappears, the exact model is unrecoverable.
**Fix:** record the exact commit in the README; archive pyMANGA at that commit (Zenodo/DOI or a
lab-owned tag); ideally merge PR #380 upstream. → Q1.

#### E1 🟡 `py -3.12` hardcoded but not actually required
**Where:** `run_model.py:81` (was `PYTHON_EXEC = "py -3.12"`); README (all commands).
**Problem:** every command uses the Windows-only `py -3.12` launcher and the README implies 3.12
is required. It isn't — the model runs on 3.13. Without that exact launcher `run_model.py` can't
start pyMANGA. (`run_analysis.py` is unaffected; it uses `sys.executable`.)
**Fix (applied on this branch):** `PYTHON_EXEC = sys.executable`, launched from the active venv.
README should state a supported range (3.10–3.13), not require 3.12. → README checklist, Q7.

#### E3 🟡 `vtk` is a hidden, undocumented runtime dependency
**Where:** `requirements.txt`; pyMANGA `ResourceLib/BelowGround/Generic/__init__.py`.
**Problem:** a clean env built per the docs fails on the first sim with a *misleading*
`ModuleNotFoundError: ...Generic.Merge`. Real cause: that package's `__init__` eagerly imports the
OpenGeoSys chain (`OGSExternal → OGS → helpers/CellInformation.py → import vtk`). These setups
never use OpenGeoSys, yet `vtk` is mandatory. `requirements.txt` lists only the 4 analysis packages.
**Fix:** add `vtk` (plus `lxml`, `scipy`) to the documented deps / a lockfile. `pip install vtk`
unblocks it (confirmed: sim then ran to completion on 3.13). Upstream note: pyMANGA masks the true
error in `ProjectLib/Project.py` `importModule`. → Q7.

#### E4 🟡 README is not a working recipe for running the model
**Where:** `readme.md`.
**Problem:** following the README does not get a new user to a running model — the Python framing,
dependency list, pyMANGA setup, and environment steps are all incomplete. Only figures-from-
committed-data reproduce, not the simulations.
**Fix:** see the [README checklist](#readme--issues-to-fix-before-publication) and the tested
draft in the [Appendix](#appendix--proposed-readme-section-draft--not-yet-merged-into-readmemd).

### Analysis pipeline (A)

#### A2 🟡 Derived `data/` ≈ 6.7 GB from triple duplication
**Where:** `source/01_read_raw_data.py`, `source/02_data_processing.py`.
**Problem:** `data/` (~6.7 GB) vs `data_raw/` (~1.4 GB). Not a precision issue — the same rows are
materialised three times: `raw_data.csv` (01 re-concatenates `data_raw`), family `data.csv` (02
adds derived cols; the only file read downstream), and per-salinity/PFT split `data.csv` (02 slices).
**Fix:** don't ship `data/` — it regenerates from `data_raw/` in one command (now gitignored, H1).
For code-level reduction see A4 + A8.

#### A4 🟡 ~2 GB of split `data.csv` files written but never read
**Where:** `source/02_data_processing.py` (loops at lines 85-94, 106-116, 128-137).
**Problem:** the per-salinity/PFT split files are not read by any script (downstream reads only the
family `data.csv` via the `*_DATA` path constants). Dead output, likely a notebook leftover.
**Fix:** remove the three split-writing loops — no effect on figures; saves ~2 GB and ~half of
`02`'s runtime.

#### A8 🟡 Data-prep can be ~10–20× smaller
**Where:** `source/01`+`02`; `source/03_figure_utils.py`.
**Problem:** the family `data.csv` has 27 columns; the entire `03_*` pipeline reads only 10
(`pft, pfts, salinity, n, version, time, volume, h_ag, ag_bg_ratio`, + `age` for filtering). The
other 17 (mostly float64) dominate size and are never used downstream.
**Fix:** (1) drop the split loops (A4); (2) fold 01+02, stop persisting `raw_data.csv`; (3) apply
the age filter once in 02 (A5); (4) keep only the ~10 needed columns. Estimated ~6.7 GB → a few
hundred MB; transparency preserved because `data_raw/` holds the unmodified output.

#### A5 🟡 Age filter documented in the wrong place; magic number
**Where:** claimed in `source/02_data_processing.py` docstring + README §5.2; actually in
`source/03_figure_utils.py:59,75,95`.
**Problem:** docs say `02` applies the seedling/age filter (`age >= 864000`, = 10 days at
`delta_t` 86400 s). It doesn't — `02` writes unfiltered tables; the filter lives in `03`. Figures
are filtered correctly, but the docs misattribute it. `864000` is also a magic number repeated 3×.
**Fix:** correct the docs; extract `864000` to one named constant; ideally filter once in `02` (A8).

#### A3 🟡 Inconsistent missing-file handling
**Where:** `source/01_read_raw_data.py:178` (`aggregate_monoculture_static`).
**Problem:** the README/docstring promise the script "fails if an expected `Population.csv` is
missing." True for community runs (`read_population()` raises `FileNotFoundError`), but the
monoculture path silently `continue`s past missing files — a missing run goes undetected.
**Fix:** raise on a missing monoculture file too, to honour the documented fail-early guarantee.

#### A1 🔵 Split `data/` files undocumented
**Where:** README §2.3 vs `source/02_data_processing.py`.
**Problem:** `02` writes per-salinity/version/PFT `data.csv` files not shown in the README's
`data/` structure. Incomplete docs, not wrong. Moot if the split files are removed (A4).
**Fix:** remove the files (A4) or document them.

#### A6 🔵 `extract_pft_from_plant_id` is fragile
**Where:** `source/02_data_processing.py:65`.
**Problem:** `int("_".join(str(value).split("_")[1]))` — the `"_".join` over a string is a no-op
for single-digit PFT ids (1–4) but corrupts multi-character ids ("10" → "1_0" → `int()` raises).
**Fix:** `int(str(value).split("_")[1])`.

#### A7 🔵 pandas `FutureWarning`s on every run
**Where:** `source/03_figure_utils.py` (~lines 161-252).
**Problem:** many `observed=False is deprecated` warnings (groupby on categoricals). Harmless now,
but behaviour changes in a future pandas — and noisy output.
**Fix:** pass `observed=...` explicitly.

#### A9 🔵 Stale comment in species files
**Where:** `data_model_input/species/Saltmarsh_*.py:24`.
**Problem:** comment says `# resource module FON`, but the configured belowground modules are
`FixedSalinity SymmetricZOI` (`r_salinity = "forman"`). FON is a different pyMANGA module.
**Fix:** remove/correct the comment. → Q5.

### Science / analysis logic (S)

#### S1 🔵 Realized `salinity` output column overwritten with the scenario label
**Where:** `source/01_read_raw_data.py:101, 132, 188`.
**Problem:** `Population.csv` already has a `salinity` column = the realized porewater salinity per
plant (e.g. `0.035`; time-varying for dynamic runs). All three aggregators overwrite it with an
integer scenario label (35/70/105/140 ppt) — same name, different quantity and units — discarding
the realized salinity, including the entire dynamic series.
**Fix:** write the label to a distinct column (e.g. `salinity_scenario`); keep or explicitly drop
the model's `salinity`; document the encoding. Low priority — confirmed with reviewer that the
realized salinity isn't used downstream (figures use the label; `plot_2_1` reads the salinity CSVs
directly), so this is clarity-only, not a data-correctness bug.

#### S2 🔵 Derived metrics verified correct; two minor notes
**Where:** `source/02_data_processing.py:70-73`.
**Verified (good):** `volume = π(r_ag²·h_ag + r_bg²·h_bg)` matches pyMANGA's `Saltmarsh.plantVolume`
exactly (two cylinders, `V_ag + V_bg`; `Saltmarsh.py:149-151`), so the recomputed biovolume equals
the model's own `volume`. The AG/BG split is recomputed legitimately — pyMANGA outputs `volume` but
not `V_ag`/`V_bg`/ratio.
**Notes:** (1) recomputing `volume` and overwriting the model's identical column is redundant (could
just keep the model's `volume`). (2) `ag_bg_ratio = ag_volume / bg_volume` lacks the zero-guard the
model uses (`r_V_ag_bg = V_ag / max(V_bg, 1e-22)`), so it yields `inf`/`NaN` for `bg_volume == 0`
plants — only safe because the later age filter drops those before aggregation. Consider guarding.

#### S3 🟡 Unexplained magic correction on dynamic salinity
**Where:** `source/03_figure_utils.py:93` (`prep_dynamic_comm_df`).
**Problem:** `df["salinity"] = df["salinity"].replace(10, 105)`. Nothing in the pipeline produces a
salinity of `10` — `01` derives dynamic salinity from the version prefix (`"105_V1" → 105`), so the
column only holds {35, 70, 105}. The line therefore either silently rewrites a value that shouldn't
exist (masking a latent mislabeling/parse bug) or is dead defensive code. Undocumented either way.
**Fix:** trace whether/why `10` can occur; fix at the source or remove the line (document if kept).

#### S4 🔵 Plant-level error bars combine inter-plant and temporal spread
**Where:** `source/03_plot_3_2_static_community.py:163-191` (`summary_minmax_individuals`), on
`df_comm_prepared`.
**Verified (good):** error-bar semantics match the README §6.5 / docstring — plant-level metrics
(`volume_per_plant`, `h_ag`, `ag_bg_ratio`) use the individual-plant table; `num_plants` uses the
replicate-level range. No doc/code mismatch.
**Note:** `df_comm_prepared` keeps *all output timesteps*, so the median/min/max are over all
(plant × timestep) observations — the bars combine inter-plant variation *and* each plant's growth
over time, not a pure across-plant spread at a comparable stage. "Range of individual plants" may
understate this; confirm it's intended for the caption.

#### S5 🟡 PFT cost labels contradict the actual `p_maint` values
**Where:** `source/03_plot_2_2_forman.py:80-85` (`PFT_LABELS`) vs `data_model_input/species/Saltmarsh_*.py` (`p_maint`).
**Verified first (good):** the plotted salinity response `1/(1+exp(d·(U_i−U)))` matches pyMANGA's
forman formula exactly (`FixedSalinity.py:84-87`, including the kg/kg→ppt ×1000). With
`salt_effect_d = -0.045` the curve correctly *decreases* with salinity, and `salt_effect_ui` =
60/70/80/90 gives a monotonic tolerance gradient PFT1→4. The curves are faithful to the model.
**Problem:** the *cost* labels don't match `p_maint`, which increases monotonically
(`1.5e-6 < 1.867572e-6 (PFT2) < 2.215437e-6 (PFT3) < 2.517150e-6`). The legend calls **PFT2 "high
cost" and PFT3 "low cost"**, but PFT2 actually has the *lower* maintenance — the figure even draws
PFT2's maintenance line below PFT3's, contradicting its own legend. More broadly, since both
`p_maint` and `salt_effect_ui` rise monotonically PFT1→4, the intended cost×tolerance 2×2 contrast
(PFT2 vs PFT3 = equal tolerance, opposite cost) is not realised by these parameters.
**Fix:** confirm with Jonas whether the PFT2/PFT3 `p_maint` values are swapped or the labels are
wrong; correct either the parameters or the figure/manuscript PFT descriptions. → Q3.

#### S6 🔵 `plot_2_3` reimplements model equations with hardcoded constants
**Where:** `source/03_plot_2_3_growth_pot_maint.py:75-80, 147-174`.
**Status (good):** the hardcoded `P_SUN=1361`, `P_WATER=1.5`, `P_GROW=5e-9`, `P_RATIO_AG/BG=0.5`
currently **match** `Saltmarsh_4.py`, and `p_maint`/`salt_effect_*` are read from it — so the figure
is correct as-is.
**Note:** it duplicates those model parameters instead of reading them (only `p_maint`/`salt_effect`
are read) and reimplements the growth concept (`res_ag`, `res_bg`, `grow = min(res_ag,res_bg)·p_grow`)
in parallel to pyMANGA — drift risk if the model or parameters change. The `res_bg` term includes
`p_sun`, which is worth confirming against pyMANGA's `Saltmarsh` growth concept.
**Fix:** read all constants from the species file; validate the reimplemented equations against the
model once.

#### S7 🔵 `plot_3_3` "Total" stacked bars may be clipped by shared y-limits
**Where:** `source/03_plot_3_3_dynamic_biovolume.py:199, 244, 282`.
**Problem:** `y_lim` is derived from the **per-PFT** time-series (`get_y_limits(median_ts_total_volume)`)
and then applied to both the per-PFT line panels *and* the **stacked Total** bar column (`set_ylim`).
The stacked total (sum of 4 PFTs) can exceed that limit — especially at low salinity where PFTs
coexist — so the Total bars may be visually clipped.
**Fix:** verify against the rendered figure; if clipped, give the Total column its own y-limit.
Visual only — no effect on the underlying numbers.

### Reproducibility & provenance (R)

#### R1 🔴 No random seed → runs not bit-reproducible
**Where:** `create_setups.py` / generated XMLs (no `<random_seed>` tag).
**Problem:** setups use `Random` initial population + `Random` mortality with no seed anywhere, so
re-running differs numerically from the committed `data_raw/` (one fixed realisation).
**Fix:** pyMANGA *does* support a seed — a top-level `<random_seed>` tag (`XMLtoProject.py:50` →
`Project.py:55-57` → `np.random.seed`). Write one per XML from `create_setups.py`, using a
**distinct seed per replicate** (a shared seed would make all 10 replicates identical). Otherwise,
document the outputs as a fixed realisation. → Q2.
**Verified (Pass 5):** a 40-sim `community_static` re-run matched the committed replicate-mean
biovolume within ~1.6% at every salinity — statistically equivalent, not identical (`compare_reruns.py`).

#### R2 🟡 PFT parameters undocumented; calibration provenance missing
**Where:** `data_model_input/species/Saltmarsh_*.py`.
**Problem:** bare `createPlant()` parameter dumps — no units, meaning, or source. The 4 PFTs differ
in `salt_effect_ui` (60/70/80/90) and calibrated `p_maint` (7-significant-figure values); no script
shows how `p_maint` was derived. This is the scientific core and currently author-only knowledge.
**Fix:** document the parameters + units and the `p_maint` derivation (script/formula). → Q3.

#### R3 🟡 Dynamic salinity inputs have no provenance
**Where:** `data_model_input/salinity/*.csv`.
**Problem:** 6 files (7301 rows ≈ daily for ~20 yr) committed with no generation code or documented
method. Columns `t_step, V1, V27` are unexplained (`V27` is suspicious inside `*_V1.csv`). Not
regenerable from the repo; also unclear why ~20 yr when simulations run 10 yr. Note: `plot_2_1`
plots `value_columns[0]` (the first non-`t_step` column) from each file, so which series the figure
shows depends entirely on resolving this column ambiguity.
**Fix:** add the generation script and document the method + column meanings. → Q4.

### Hygiene (H)

#### H1 🔵 No `.gitignore` — resolved
A `.gitignore` now exists and ignores `.venv/`, `data/`, `__pycache__/`, and `data_raw_orig/`. The
original risk (untracked venv/derived data/caches being committed) is addressed. No action needed.

---

## README — issues to fix before publication

`readme.md` documents the analysis/figure workflow well but is not a working recipe for running the
**model** (finding E4). Concrete fixes:

- [ ] **Python version (E1).** Drop `py -3.12` and "3.12 required" wording; state a supported range
      (3.10–3.13) and a generic invocation.
- [ ] **Dependencies (E3).** `requirements.txt` covers only the analysis. Document the full model
      set incl. `lxml`, `scipy`, `vtk` — `pip install -r requirements.txt` alone won't run a sim.
- [ ] **pyMANGA setup (E2).** Add the clone command, the exact commit/branch, and make the required
      sibling-folder name explicit (only implicit in `source/utils/paths.py` `DEFAULT_MANGA_DIR`).
- [ ] **Environment setup.** Document venv creation/activation and the PowerShell execution-policy
      step, plus how to verify the venv is active.
- [ ] **Cross-platform.** All commands are Windows PowerShell; add macOS/Linux equivalents.
- [ ] **Add a "Run the model from scratch" section.** Tested draft in the
      [Appendix](#appendix--proposed-readme-section-draft--not-yet-merged-into-readmemd), based on
      `HOW_TO_RUN.md`. Decide: fold into the README, or ship `HOW_TO_RUN.md` alongside and link it.

> Likely a **handover item for Jonas** (his manual; he knows the intended pyMANGA commit) rather
> than a unilateral reviewer rewrite. See Q1/Q7.

---

## Questions for Jonas (handover — resolve before he leaves)

- **Q1 (🔴, E2) — pyMANGA version.** Which exact commit is the manuscript built on? Confirm
  `bab0c0dc` on `pr/jvollhueter/380`. Can we archive a permanent copy (Zenodo/DOI or lab-owned tag)
  and merge PR #380 upstream? Where does the Saltmarsh `vegetation_model_type` code live?
- **Q2 (🔴, R1) — random seed.** pyMANGA supports `<random_seed>` (`XMLtoProject.py:50` →
  `Project.py:55-57`); the XMLs just omit it. Should `create_setups.py` set a per-replicate seed for
  exact reproducibility (shared seed → identical replicates)? Were the committed outputs a single
  documented run, and how do we describe model reproducibility in the paper?
- **Q3 (🟡, R2 / S5) — PFT parameters.** Meaning/units of `p_maint, p_grow, salt_effect_d,
  salt_effect_ui, aa, bb, fmin, p_transpiration, volume_thr`? How were the calibrated `p_maint`
  values (PFT 2–4) derived — script/formula? **And resolve S5:** the figure labels PFT2 "high cost"
  / PFT3 "low cost", but `p_maint` is PFT2 (1.87e-6) < PFT3 (2.22e-6) — are the PFT2/PFT3 values
  swapped, or are the labels/manuscript descriptions wrong?
- **Q4 (🟡, R3) — salinity inputs.** How were `salinity/*.csv` generated (method + code)? What do
  `V1`/`V27` mean, is `V27` in `*_V1.csv` correct, and why 7301 rows (~20 yr) for 10-yr sims?
- **Q5 (🔵, A9) — resource module.** Belowground module FON or SymmetricZOI? (Code says
  SymmetricZOI/forman; a species-file comment says FON.)
- **Q6 (🔵) — one-plant simulations.** README says one-plant outputs are generated but "not used by
  the current main analysis." Drop them from the compendium, or document their purpose?
- **Q7 (🟡, E3) — full model runtime env.** What is the complete, tested package set (and Python
  version) to run pyMANGA for these setups? `vtk` is required in practice but undocumented. A
  lockfile would help.

---

## Verification log

- [x] **Pass 1 — figures & data prep.** `run_analysis.py --prepare-data-only` and `--figures-only`
      both exit 0; all 7 figures regenerate, visually identical (byte diffs cosmetic: PDF timestamp,
      PNG re-compression). Working tree restored via `git checkout figures/`.
- [x] **Pass 2 — setups.** `create_setups.py` → **0/300 XMLs differ** from committed; category
      counts 40/60/160/16/24 = 300 match. (XML paths are relative to pyMANGA's cwd — no `pyMANGA-1`
      hardcoding; only `paths.py` `DEFAULT_MANGA_DIR` depends on the folder name.)
- [x] **Pass 5 — model run + reproduction check.** Applied the `run_model.py`/`paths.py` fixes
      (E1); built a Python 3.13 venv (deps incl. `vtk`, E3); re-ran 40 `community_static` sims →
      **40/40 OK** (~70–90 s each, 6 parallel). Aggregate comparison (`compare_reruns.py`) reproduces
      committed behaviour within ~1.6% (R1). Stage 2 confirmed runnable; procedure in `HOW_TO_RUN.md`.
- [x] **Pass 3 — analysis source / scientific logic.** Read the full `01`→`02`→utils→main→plot
      pipeline. Core science is sound: the biovolume formula matches pyMANGA's `Saltmarsh.plantVolume`
      (S2), the salinity-response curve matches the model's forman implementation (S5), and the
      error-bar semantics match the docs (S4). Findings logged S1–S7; the notable one is **S5**
      (PFT cost labels contradict `p_maint`) and **S3** (`.replace(10,105)`). No correctness bug in
      the figure computations themselves.
- [~] **Pass 4 — hygiene/provenance.** Done: E2, R1, R2, R3, A9. To do: file-naming consistency,
      LICENSE + citation, doc quality, missing-files-for-a-compendium checklist.

---

## Appendix · Proposed README section (draft — NOT yet merged into `readme.md`)

A "Run the model from scratch" section the README is missing (E1–E4). Cross-platform; verified on
Windows 11 / Python 3.13, the macOS/Linux commands are the standard equivalents (untested here).
Confirm the exact pyMANGA commit (E2) before publishing.

> ### Running the simulations (full setup)
>
> The figure pipeline (`run_analysis.py`) reproduces from the committed `data_raw/` alone. To
> re-run the **model** you also need pyMANGA and a few extra dependencies.
>
> **1. Get pyMANGA as a sibling folder**, checked out at the exact manuscript commit, so the layout
> is `…/pyMANGA/` beside `…/data_and_results/`:
>
> ```bash
> git clone https://github.com/pymanga/pyMANGA.git pyMANGA
> cd pyMANGA && git checkout bab0c0dc   # TODO: confirm exact manuscript commit (E2)
> cd ..
> ```
> If you name the folder anything other than `pyMANGA`, update `DEFAULT_MANGA_DIR` in
> `source/utils/paths.py`.
>
> **2. Create and activate a virtual environment** (any Python 3.10–3.13; 3.12 not required):
>
> ```powershell
> # Windows (PowerShell)
> py -3.13 -m venv .venv
> .venv\Scripts\Activate.ps1     # if blocked: Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
> ```
> ```bash
> # macOS / Linux
> python3 -m venv .venv && source .venv/bin/activate
> ```
>
> **3. Install dependencies** (model + analysis; `requirements.txt` covers only the analysis):
>
> ```bash
> python -m pip install --upgrade pip
> pip install numpy pandas matplotlib seaborn lxml scipy vtk
> ```
> `vtk` is required even though these setups don't use OpenGeoSys (pyMANGA imports it eagerly).
>
> **4. Generate setups, run, analyse** (from the activated venv, so `run_model.py` uses the right
> interpreter):
>
> ```bash
> python create_setups.py          # writes 300 XML files + output dirs
> python run_model.py --list-only  # preview selection (runs nothing)
> python run_model.py              # run all simulations (hours)
> python run_analysis.py           # process data + build figures
> ```
> Add `--include-done` to re-run sims already marked `OK` in `data_raw/logs/simulation_log.csv`;
> `--override-only community_static` runs one category.
>
> **Reproducibility:** runs use unseeded random initial populations/mortality, so a re-run is
> statistically equivalent — not byte-identical — to the committed data (R1).
