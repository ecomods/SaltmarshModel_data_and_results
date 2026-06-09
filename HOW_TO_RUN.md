# How to run this compendium (reviewer runbook)

A practical, tested step-by-step for running the saltmarsh compendium from scratch on a
Windows machine. Written during review (Selina, 2026-06-09) because the official
`readme.md` assumes Python 3.12 + a `py -3.12` launcher that is not always available, and
omits a real runtime dependency (`vtk`). This file records what **actually worked**.

> Environment used here: Windows 11, **Python 3.13.1** (Python 3.12 was *not* installed),
> PowerShell. The model ran fine on 3.13 — exact 3.12 is **not** required (see REVIEW.md E1).

---

## 0. Prerequisites — folder layout

This repo expects pyMANGA to sit **next to it** as a sibling folder. After cloning, the
layout must be:

```text
...\Jonas\
├── pyMANGA\            # the model code (cloned separately)
│   └── MANGA.py
└── data_and_results\   # THIS repo
    ├── create_setups.py
    ├── run_model.py
    └── run_analysis.py
```

⚠️ **Folder-name gotcha.** `source/utils/paths.py` (line ~60) hardcodes the sibling name
as **`pyMANGA-1`**, but the model was cloned here as **`pyMANGA`**. This does *not* affect
running a single simulation by hand (Step 4), but it *does* break the batch runner
`run_model.py` (Step 5). See Step 5 for the fix.

pyMANGA version actually used (record this — see REVIEW.md E2):
- branch `pr/jvollhueter/380`, commit `bab0c0dc`, reports itself as `pyMANGA v3.1.0`.

---

## 1. Create and activate a Python environment

From the `data_and_results` folder, in **PowerShell**:

```powershell
cd C:\Users\Selina\Repos\Projects\Mascot\Jonas\data_and_results

# Create a venv with Python 3.13 (use whatever 3.1x you have; 3.13 worked)
py -3.13 -m venv .venv

# Allow venv activation for THIS PowerShell session (only if activation is blocked)
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process

# Activate it
.venv\Scripts\Activate.ps1
```

Your prompt should now start with `(.venv)`.

> If you are in the old **Command Prompt (cmd.exe)** instead of PowerShell, the activation
> command is different: `.venv\Scripts\activate.bat`. `Activate.ps1` only works in PowerShell.

## 2. Verify you are really in the venv (do not skip)

```powershell
python --version
python -c "import sys; print(sys.executable)"
```

Expect `Python 3.13.x` and a path ending in `...\data_and_results\.venv\Scripts\python.exe`.
If you instead see a system path under `...\AppData\Roaming\Python\...`, the venv did **not**
activate — fix that before installing anything.

## 3. Install dependencies

The model needs more than this repo's `requirements.txt` lists. Install:

```powershell
python -m pip install --upgrade pip
pip install numpy lxml pandas scipy matplotlib seaborn
pip install vtk
```

Notes / gotchas:
- **`vtk` is required even though we do not use OpenGeoSys.** pyMANGA eagerly imports its
  OpenGeoSys modules when loading the belowground "Merge" concept, which pulls in `vtk`.
  Without it the first simulation fails with a *misleading* error
  (`No module named 'ResourceLib.BelowGround.Generic.Merge'`). See REVIEW.md E3.
- pip currently pulls **pandas 3.0.x**, which is newer than this repo's own `<3` pin. The
  model ran fine, but if the *analysis* step (Step 6) misbehaves, downgrade with
  `pip install "pandas<3"`.

---

## 4. Generate the simulation setups (XML control files)

```powershell
python create_setups.py
```

This writes 300 XML files into `data_model_input\xml_control_files\` and creates the output
directory tree under `data_raw\`. Verify:

```powershell
(Get-ChildItem data_model_input\xml_control_files\*.xml | Measure-Object).Count   # expect 300
```

---

## 5. Run the model

### 5a. Run ONE simulation by hand (recommended first — this is what we verified)

Run a single XML directly with pyMANGA, watching the output live. Done from **inside the
pyMANGA folder** (the venv stays active across `cd`):

```powershell
cd ..\pyMANGA
python MANGA.py -i ..\data_and_results\data_model_input\xml_control_files\community_static_0.035_01.xml
cd ..\data_and_results
```

Success = it runs to completion (a ~10-year simulation, takes a few minutes) with no
Python traceback, and refreshes
`data_raw\community\static\0.035\01\Population.csv`.

⚠️ This **overwrites** the committed manuscript output in that folder. To put the committed
version back (a re-run will differ anyway — no random seed, REVIEW.md R1):

```powershell
git checkout -- data_raw/community/static/0.035/01
```

### 5b. Run many simulations with the batch runner

`run_model.py` runs simulations in parallel and logs them. **Two edits are needed for it to
work on this machine; they are already applied on the `review_selina` branch.** On a fresh
clone of the *original* repo you would have to make them yourself (and ideally they get fixed
upstream — see REVIEW.md E1/E4):

1. **Interpreter** — `run_model.py` originally had `PYTHON_EXEC = "py -3.12"`. Changed to
   `PYTHON_EXEC = sys.executable`. ⚠️ This means the batch runner uses **whatever Python runs
   `run_model.py`**, so you **must launch it from the activated venv** (`python run_model.py`).
   Do *not* use `py -3.13 run_model.py` — that would start system Python without `vtk`/deps and
   every simulation would fail.
2. **pyMANGA folder name** — `source/utils/paths.py` `DEFAULT_MANGA_DIR` originally expected a
   sibling named `pyMANGA-1`; changed to `pyMANGA` to match the cloned folder.

**Always preview first** with `--list-only` (runs nothing):

```powershell
python run_model.py --override-only community_static --list-only
```

⚠️ **The `--include-done` gotcha.** The repo ships a `data_raw\logs\simulation_log.csv` that
already marks all 300 runs as `OK`. By default the runner **skips** anything marked OK, so the
command above will say *"No XML files to run."* To actually re-run, add `--include-done`:

```powershell
python run_model.py --override-only community_static --include-done --list-only   # expect 40
python run_model.py --override-only community_static --include-done               # run them
python run_model.py --include-done                                                # ALL 300 (hours)
```

Notes:
- Runs `MAX_WORKERS = 6` in parallel; prints `OK: ...` / `ERROR: ...` per sim. One category
  (`community_static`, 40 sims) took roughly 20–40 min here; all 300 is a multi-hour job.
- Each run overwrites the committed `Population.csv` and per-sim `.log` files under `data_raw\`
  and **appends** to `simulation_log.csv` — all git-tracked, so all restorable (Step 5c).

### 5c. Compare a re-run against the committed data, then restore

Because there is **no random seed** (REVIEW.md R1), a re-run will *not* match the committed
output byte-for-byte — comparing raw files with a diff is meaningless. Instead:

1. Before running, snapshot the committed data (gitignored, ~1.5 GB):
   ```powershell
   Copy-Item data_raw data_raw_orig -Recurse
   ```
2. Run the simulations (Step 5b). The fresh output lands in `data_raw\`, the originals stay in
   `data_raw_orig\`.
3. Compare on **aggregates** (e.g. number of plants, total biovolume per scenario), not bytes,
   to confirm the model reproduces the manuscript *behaviour*.
4. When done, restore the tracked files and remove the snapshot:
   ```powershell
   git checkout -- data_raw
   Remove-Item data_raw_orig -Recurse -Force
   ```

---

## 6. Run the analysis and figures

This part was already verified reproducible earlier (REVIEW.md Pass 1). Uses `sys.executable`,
so no `py -3.12` issue:

```powershell
python run_analysis.py                      # full: process data + all figures
python run_analysis.py --prepare-data-only  # only rebuild data\ from data_raw\
python run_analysis.py --figures-only        # only redraw figures from existing data\
```

Figures land in `figures\main\` and `figures\appendix\`. Note `data\` is large (~6.7 GB)
and is gitignored — it regenerates from `data_raw\`.

---

## Quick reference (the happy path)

```powershell
cd C:\Users\Selina\Repos\Projects\Mascot\Jonas\data_and_results
py -3.13 -m venv .venv
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install numpy lxml pandas scipy matplotlib seaborn vtk
python create_setups.py
# single test sim:
cd ..\pyMANGA; python MANGA.py -i ..\data_and_results\data_model_input\xml_control_files\community_static_0.035_01.xml; cd ..\data_and_results
git checkout -- data_raw/community/static/0.035/01   # restore committed output
# analysis:
python run_analysis.py --figures-only
```
