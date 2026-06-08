# Review notes — Saltmarsh research compendium

Reviewer: Selina Baldauf · Branch: `review_selina` · Started: 2026-06-08

Goal: confirm the compendium runs, the analysis makes sense, and it is reproducible
enough to publish as a digital appendix to the manuscript.

> **RESUME STATUS (last updated 2026-06-08).** Stages 1 & 3 verified and reproduce
> cleanly (XMLs regenerate byte-identical; figures visually identical). Stage 2 (running
> pyMANGA) not tested — needs Python 3.12, deferred. Bus-factor pass done: see findings
> E2/R1 (critical) and the "Questions for Jonas" list. **Next:** finish Pass 4 — file
> naming, doc quality, coding-style / AI-comment-bloat check, and add LICENSE + citation.
> To rebuild the env on a new machine: `py -3.13 -m venv .venv` (3.12 absent here),
> `.venv\Scripts\python -m pip install -r requirements.txt`; figures regenerate via
> `python run_analysis.py --figures-only` (needs `data/`, rebuilt by `--prepare-data-only`).
> Claude's memory does NOT transfer between machines — this file is the source of truth.

Review approach (5 passes, cheapest/highest-signal first):
1. Reproducibility smoke test — regenerate `data/` + `figures/` from committed `data_raw/`.
2. Re-run `create_setups.py`, diff against the 300 committed XMLs; sanity-check CONFIG.
3. Read analysis source in pipeline order for scientific logic.
4. Reproducibility hygiene (versions, license, lockfile, .gitignore, file sizes).
5. Read-only review of `run_model.py` (stage 2 / running pyMANGA).

Finding IDs are grouped by area, then numbered: **E** = Environment (tooling needed to
run the repo), **A** = Analysis (data-processing & figure pipeline), **R** =
Reproducibility & provenance (can results/inputs be regenerated and trusted), **H** =
Hygiene (repo cleanliness for publication). The ID is just a label, not a priority.

Severity legend (separate from the ID): 🔴 blocker · 🟡 should-fix · 🔵 nice-to-have / discuss

---

## Environment setup

- pyMANGA placed as sibling `../pyMANGA-1/MANGA.py` — matches the path expected by
  `source/utils/paths.py` (`REPO_ROOT.parent / "pyMANGA-1"`). ✅
- Review environment: fresh `.venv` from **Python 3.13** (3.12 not installed on this
  machine — see finding E2). `pip install -r requirements.txt` resolved cleanly:
  numpy 2.4.6, pandas 2.3.3, matplotlib 3.10.9, seaborn 0.13.2. ✅

---

## Findings

### E1 🟡 `py -3.12` is hardcoded but unavailable; breaks stage 2 as documented
The README's every command and `run_model.py` (`PYTHON_EXEC = "py -3.12"`, line 81)
require the `py -3.12` launcher. On the review machine only 3.13 and 3.14 are
installed, so `py -3.12` fails ("No suitable Python runtime found") and `run_model.py`
would fail to launch pyMANGA. `run_analysis.py` is unaffected because it uses
`sys.executable` (line 93).
- Impact: anyone without exactly Python 3.12 on the `py` launcher cannot run the
  model by following the README. Poor portability for a shareable appendix.
- Suggested fix: use `sys.executable`, or make the interpreter a single configurable
  variable, and relax the README from "must be 3.12" to "tested with 3.12".

### A1 🔵 `data/` structure undocumented (extra split files)
`02_data_processing.py` writes per-salinity / per-version / per-PFT `data.csv` files
(e.g. `data/community/static/105/data.csv`) in addition to the family-level
`raw_data.csv` + `data.csv` shown in README §2.3. Documentation is incomplete, not wrong.

### A2 🟡 Derived `data/` is very large (~6.7 GB) due to triple duplication
`data/` ≈ 6.7 GB vs `data_raw/` ≈ 1.4 GB. Investigated the cause (it is NOT float
precision — pyMANGA already writes full-precision floats; raw and processed rows are
byte-identical). The same rows are materialized three times:
1. `data/<fam>/raw_data.csv` (~1.6 GB) — `01` re-concatenates all of `data_raw` → a
   near-copy of `data_raw` + 5 metadata cols. Consumed only by `02`.
2. `data/<fam>/data.csv` (~2 GB) — `02` adds derived cols → strict superset of #1.
   This is the file actually consumed downstream.
3. `data/<fam>/<sal-or-PFT>/data.csv` (~2 GB) — `02` slices #2 by salinity/PFT. The
   slices sum exactly back to #2.
None of `data/` is needed for publication — it all regenerates from `data_raw/` in one
command. Recommend: do NOT ship `data/`; add it to `.gitignore` (see H1).

### A4 🟡 ~2 GB of split `data.csv` files are written but never read (dead output)
The per-salinity / per-PFT split files written by `02` (lines 85-94, 106-116, 128-137)
are not read by any script — `grep read_csv source/*.py` shows downstream reads only the
family-level `data.csv` via `COMMUNITY_STATIC_DATA` / `MONOCULTURE_STATIC_DATA` etc.
Likely leftover from an earlier notebook workflow. The three split-writing loops can be
removed with no effect on figures, saving ~2 GB and ~half the `02` runtime.

### A5 🟡 Seedling/age filter is documented in the wrong place
`02`'s docstring and README §5.2 state `02` "applies the seedling/age filter." It does
not — `02` writes unfiltered tables. The filter (`df["age"] >= 864000`, = 10 days at
delta_t 86400 s) is actually in `03_figure_utils.py` (lines 59, 75, 95). Figures are
filtered correctly, but the documentation misattributes where/when it happens. Also: the
threshold `864000` is a hardcoded magic number repeated in 3 places — extract to one
named constant.

### A8 🟡 Data-prep can be drastically simplified; `data/` could be ~10–20× smaller
The processing step (`01`+`02`) currently maximizes size instead of minimizing it.
Column-usage trace: the family `data.csv` has 27 columns, but the entire `03_*`
pipeline reads only 10 from it — `pft, pfts, salinity, n, version, time, volume, h_ag,
ag_bg_ratio` and `age` (the last only to filter). The other 17 (`plant, x, y, r_ag,
r_bg, h_bg, aboveground_resources, belowground_resources, res_ag, res_bg, res_eff,
grow, maint, transpiration, plant_uid, setup, ag_volume, bg_volume`) are never read
downstream — mostly float64 cols that dominate size. (Verified: raw-geometry mentions
in `03_plot_2_3` are a self-contained conceptual figure that does not read `data.csv`;
`"y"` hits are matplotlib `axis="y"`.)
Recommended simplification (safe, high value):
1. Remove the split-file loops (A4) — ~2 GB, never read.
2. Don't persist `raw_data.csv` as a separate artifact (it's `data_raw` re-concatenated);
   fold `01`+`02` into one step.
3. Apply the seedling filter (`age >= 864000`) once in `02` before writing, and remove
   the 3 repeated applications in `03_figure_utils.py` (lines 59/75/95).
4. Keep only the ~10 needed columns in `data/`.
Estimated effect: `data/` from ~6.7 GB to a few hundred MB. Transparency is preserved
because `data_raw/` already holds the unmodified pyMANGA output; `data/` is free to be a
lean analysis-ready table. (Most aggressive option: skip the big `data/` tables and go
straight from `data_raw` to the small `derived_figure_data/` summaries the plots
actually consume — bigger refactor, optional.)

### A6 🔵 `extract_pft_from_plant_id` is fragile
`02` line 65: `int("_".join(str(value).split("_")[1]))`. The `"_".join(...)` over a
string is a no-op for single-digit PFT ids (1-4) but would corrupt any multi-character
id (e.g. "10" → "1_0" → `int()` raises). Works for the current 4 PFTs; fragile if PFT
count grows. Simplify to `int(str(value).split("_")[1])`.

### A7 🔵 Deprecation warnings on every run
`03_figure_utils.py` triggers many pandas `FutureWarning: observed=False is deprecated`
(groupby on categoricals, lines ~161-252). Harmless now but will change behavior in a
future pandas; pass `observed=...` explicitly to be future-proof and quiet the output.

### A3 🟡 Inconsistent missing-file handling in `01_read_raw_data.py`
README and the script docstring state it "intentionally fails if an expected
Population.csv is missing." True for community (static/dynamic) via `read_population()`
which raises `FileNotFoundError`, but `aggregate_monoculture_static()` silently
`continue`s past missing files (line 178). A missing monoculture run would go
undetected, contradicting the documented fail-early guarantee.

### E2 🔴 pyMANGA pinned to a personal-fork PR branch, not pinned in the repo
The model code the whole compendium depends on is, locally:
- commit `bab0c0dcc87191265fa896b865d5cfc6f2a6c442` (`git describe` = `3.2.0-95-gbab0c0dc`)
- branch `pr/jvollhueter/380` (an **unmerged pull-request branch**)
- remote `https://github.com/jvollhueter/pymanga-1` (a **personal fork**, not the
  upstream pyMANGA org).
Risks: (a) the README only says "the `SaltmarshModel` branch" — which does not match the
actually-used branch name and pins nothing; (b) a PR branch on a personal fork can be
force-pushed, rebased, or deleted, and the fork owner (jvollhueter ≈ the departing
colleague) controls it. If that branch disappears, the exact model is unrecoverable and
nothing reproduces.
Action before he leaves: record the exact commit hash in the README; obtain a permanent
copy of pyMANGA at that commit (archive/Zenodo/DOI, or a tag in a lab-owned repo); ideally
get PR #380 merged upstream. See handover list Q1.

### R1 🔴 No random seed — model runs are not bit-for-bit reproducible
The setups use `Random` initial populations and `Random` mortality, and there is **no
seed** anywhere in `create_setups.py`, the XMLs, or `run_model.py` (grep finds none).
Consequence: re-running `run_model.py` produces statistically similar but numerically
different results than the committed `data_raw/`. The committed raw outputs are one
realization (the one behind the manuscript). The analysis uses 10 replicates + medians,
so conclusions should be robust, but exact reproduction is impossible as-is.
Action: confirm whether pyMANGA supports a seed; if so, set and document it. Either way,
state explicitly in the README that raw outputs are a fixed stochastic realization and
that re-running regenerates equivalent-but-not-identical data. See Q2.

### R2 🟡 PFT/species parameters undocumented; calibration provenance missing
`species/Saltmarsh_*.py` are bare `createPlant()` parameter dumps with no units, no
meaning, and no source. The 4 PFTs differ only in `salt_effect_ui` (60/70/80/90, clean
hand-set values) and `p_maint` (1.5e-6, then 1.867572e-6 / 2.215437e-6 / 2.517150e-6 —
7-significant-digit values that are clearly calculated/calibrated). No script or note in
the repo shows how the `p_maint` values were derived. These are the scientific core of
the model and currently only the author can explain/regenerate them. See Q3.

### R3 🟡 Dynamic salinity inputs have no provenance / generation code
`salinity/*.csv` (6 files, 7301 rows ≈ daily for ~20 yr) are committed as data with no
script to regenerate them and no documentation of the method (README says V1 = seasonal,
V2 = seasonal+tidal, but not how the series were produced). Columns are `t_step, V1, V27`
— the `V1`/`V27` column names are unexplained (and `V27` is suspicious given the file is
`*_V1`). Without generation code these inputs are not reproducible from the repo. See Q4.

### A9 🔵 Stale/contradictory comment in species files
`species/Saltmarsh_*.py` line 24 comments `# resource module FON`, but the configured
belowground modules are `FixedSalinity SymmetricZOI` with `r_salinity = "forman"` — FON
(Field Of Neighbourhood) is a different pyMANGA module. Likely a leftover comment; verify
which resource module is actually intended/used.

### H1 🔵 No `.gitignore`
The repo has no `.gitignore`, so `.venv/`, regenerated `data/` (~5 GB), and
`__pycache__/` all appear as untracked and could be committed accidentally. Recommend
adding one before publication.

---

## Questions for Jonas (handover — resolve before he leaves)

These are things only the author can answer or fix. Priority for the 2-week window.

- **Q1 (🔴, ref E2) — pyMANGA version.** Which exact pyMANGA commit is the manuscript
  built on? Confirm `bab0c0dc` on `pr/jvollhueter/380`. Can we get a permanent archived
  copy (Zenodo/DOI or a lab-owned tag) and the PR merged upstream? Where does the
  `SaltmarshModel` / Saltmarsh `vegetation_model_type` code live in that branch?
- **Q2 (🔴, ref R1) — stochasticity.** Does pyMANGA accept a random seed? Were the
  committed `data_raw/` outputs produced in a single documented run? How should we
  describe reproducibility of the model results in the paper?
- **Q3 (🟡, ref R2) — PFT parameters.** What do the key parameters mean and what are
  their units (`p_maint`, `p_grow`, `salt_effect_d`, `salt_effect_ui`, `aa`, `bb`,
  `fmin`, `p_transpiration`, `volume_thr`)? How were the calibrated `p_maint` values for
  PFT 2–4 derived — is there a script/notebook/formula?
- **Q4 (🟡, ref R3) — salinity inputs.** How were `salinity/*.csv` generated (method +
  code)? What do the `V1` and `V27` columns mean, and is `V27` in `*_V1.csv` correct?
  Why 7301 rows (~20 yr) when simulations run 10 yr?
- **Q5 (🔵, ref A9) — resource module.** Is the belowground resource module FON or
  SymmetricZOI? (Code says SymmetricZOI/forman; a species-file comment says FON.)
- **Q6 (🔵) — one-plant simulations.** README says one-plant outputs are generated but
  "not used by the current main analysis." Confirm they can be dropped from the published
  compendium, or document their purpose.

## Verification log

- [x] Pass 1 · data prep: `run_analysis.py --prepare-data-only` → exit 0; both
      `01` and `02` ran; `data/` populated (raw_data.csv + data.csv per family,
      plus split files). Observed plausible signal: monoculture PFT_1–3 nearly empty
      at salinity 0.140 while PFT_4 large (salt tolerance) — confirm expected.
- [x] Pass 1 · figures: `run_analysis.py --figures-only` → exit 0, all 7 figures
      regenerate. Byte diffs are cosmetic only (PDF = 2-byte timestamp; PNG ~7% smaller
      = matplotlib-version compression). Visual spot-check by reviewer: figures look
      identical. ✅ Regenerated figures restored to committed versions via
      `git checkout figures/` (working tree clean).
- [x] Pass 2 · re-run `create_setups.py` → **0 of 300 XMLs differ** from committed. ✅
      Generator fully reproduces committed XMLs (confirms no manual edits). Category
      counts match documented design exactly (40/60/160/16/24 = 300). Relative paths
      resolve for the sibling pyMANGA-1 layout. Note: XML paths hardcode the folder
      names `data_and_results`/`pyMANGA-1`; renaming either requires re-running
      create_setups.py (documented in README).
- [ ] Pass 3 · read source scripts (scientific logic).
- [~] Pass 4 · bus-factor / provenance (read-only): pyMANGA version (E2), random seed
      (R1), PFT param provenance (R2), salinity provenance (R3), FON comment (A9) done.
      Still to do: file naming consistency, doc quality, coding style / AI-comment smell,
      license + citation, missing-files-for-a-compendium checklist.
- [ ] Pass 5 · `run_model.py` read-only review + single-sim test (after installing 3.12).
