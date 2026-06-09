"""Reviewer helper: aggregate comparison of a model re-run vs the committed data.

Compares data_raw/ (fresh re-run) against data_raw_orig/ (committed snapshot) for the
community/static scenarios. Because there is no random seed (REVIEW.md R1), individual
runs differ; this checks that the *behaviour* (plant count + total biovolume at the final
timestep, summarised over the 10 replicates) is statistically equivalent.

Run with the venv python:  .venv\\Scripts\\python.exe compare_reruns.py
"""
from pathlib import Path
import pandas as pd

NEW = Path("data_raw/community/static")
ORIG = Path("data_raw_orig/community/static")
SALINITIES = ["0.035", "0.070", "0.105", "0.140"]


def final_stats(pop_csv: Path):
    df = pd.read_csv(pop_csv, sep="\t")
    last = df[df["time"] == df["time"].max()]
    return len(last), float(last["volume"].sum())


def collect(base: Path) -> pd.DataFrame:
    rows = []
    for sal in SALINITIES:
        for rep_dir in sorted((base / sal).iterdir()):
            f = rep_dir / "Population.csv"
            if f.exists():
                n, vol = final_stats(f)
                rows.append((sal, rep_dir.name, n, vol))
    return pd.DataFrame(rows, columns=["salinity", "rep", "n_plants", "total_volume"])


def summarise(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("salinity").agg(
        reps=("rep", "count"),
        plants_mean=("n_plants", "mean"),
        plants_min=("n_plants", "min"),
        plants_max=("n_plants", "max"),
        vol_mean=("total_volume", "mean"),
        vol_min=("total_volume", "min"),
        vol_max=("total_volume", "max"),
    )


orig = collect(ORIG)
new = collect(NEW)

print("\n=== ORIG (committed) — per salinity, final timestep ===")
print(summarise(orig).to_string())
print("\n=== NEW (re-run) — per salinity, final timestep ===")
print(summarise(new).to_string())

comp = pd.concat(
    [orig.groupby("salinity")["total_volume"].mean().rename("orig_vol_mean"),
     new.groupby("salinity")["total_volume"].mean().rename("new_vol_mean")],
    axis=1,
)
comp["pct_diff"] = (comp["new_vol_mean"] - comp["orig_vol_mean"]) / comp["orig_vol_mean"] * 100
print("\n=== mean total final biovolume: orig vs new (10-replicate mean) ===")
print(comp.round(3).to_string())
