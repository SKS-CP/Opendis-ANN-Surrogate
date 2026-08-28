#!/usr/bin/env python3
"""
prepare_data.py -- resample the raw DDD runs onto the common uniform time grid
used to train the surrogates, and derive the quantities the networks consume.

Usage:
    python3 prepare_data.py --raw data/raw --out data/resampled
    python3 prepare_data.py --raw data/raw --out data/resampled --n 1000

For each run this script:

  1. reads the raw OpenDiS CSV,
  2. resamples every column onto N evenly spaced time points (default 1000),
  3. computes Dp = (Lp + Lp^T)/2 and writes its six independent components,
  4. computes log10(rho) and its time derivative d(log10 rho)/dt,
  5. records the run's loading mode, target stress, rate and initial density,
     parsed from the filename, as constant columns.

The output columns are exactly the inputs and targets described in the paper,
so the training scripts read these files directly.
"""

import argparse
import os
import re
import sys

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

NAME = re.compile(
    r"^(?P<mode>uniaxial|shear)_(?P<stress>\d+)Mpa_(?P<rate>[\d.]+e\d+)_"
    r"(?P<density>[\d.]+e\d+)\.csv$",
    re.IGNORECASE,
)

LP = ["xx", "xy", "xz", "yx", "yy", "yz", "zx", "zy", "zz"]


def clean(name):
    """Header -> canonical key: drop units in parentheses, separators, case."""
    return re.sub(r"[^a-z0-9]", "", re.sub(r"\([^)]*\)", "", name).lower())


def column(df, *cands):
    lookup = {clean(c): c for c in df.columns}
    for c in cands:
        if clean(c) in lookup:
            return lookup[clean(c)]
    raise KeyError(f"none of {cands} found in {list(df.columns)}")


def resample_run(path, n):
    df = pd.read_csv(path)

    t = df[column(df, "time")].to_numpy(float)
    if not np.all(np.diff(t) > 0):
        keep = np.concatenate(([True], np.diff(t) > 0))
        df, t = df.loc[keep].reset_index(drop=True), t[keep]

    grid = np.linspace(t[0], t[-1], n)
    out = pd.DataFrame({"time": grid})
    out["dt"] = np.gradient(grid)

    for col in df.columns:
        if clean(col) == "time":
            continue
        y = df[col].to_numpy(float)
        if not np.all(np.isfinite(y)):
            y = pd.Series(y).interpolate(limit_direction="both").to_numpy()
        out[clean(col)] = interp1d(t, y, kind="linear",
                                   bounds_error=False,
                                   fill_value=(y[0], y[-1]))(grid)

    # symmetric part of the plastic velocity gradient
    lp = np.stack([out[clean(f"Lp{c}")].to_numpy() for c in LP], axis=1)
    L = lp.reshape(-1, 3, 3)
    D = 0.5 * (L + np.transpose(L, (0, 2, 1)))
    for name, (i, j) in {"Dp_xx": (0, 0), "Dp_yy": (1, 1), "Dp_zz": (2, 2),
                         "Dp_yz": (1, 2), "Dp_xz": (0, 2), "Dp_xy": (0, 1)}.items():
        out[name] = D[:, i, j]

    # logarithmic density and its rate
    rho = out[clean("density")].to_numpy()
    out["log10_rho"] = np.log10(rho)
    out["dlog10_rho_dt"] = np.gradient(out["log10_rho"].to_numpy(), grid)

    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="data/raw")
    ap.add_argument("--out", default="data/resampled")
    ap.add_argument("--n", type=int, default=1000,
                    help="points on the common time grid (default 1000)")
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    files = sorted(f for f in os.listdir(a.raw) if f.lower().endswith(".csv"))
    if not files:
        sys.exit(f"no CSV files in {a.raw}")

    done, failed = 0, []
    for f in files:
        m = NAME.match(f)
        if not m:
            failed.append((f, "filename does not match the naming scheme"))
            continue
        try:
            out = resample_run(os.path.join(a.raw, f), a.n)
        except Exception as exc:
            failed.append((f, str(exc)))
            continue

        out["mode"] = 0 if m.group("mode").lower() == "uniaxial" else 1
        out["target_stress_MPa"] = float(m.group("stress"))
        out["rate_Pa_s"] = float(m.group("rate"))
        out["rho0"] = float(m.group("density"))

        out.to_csv(os.path.join(a.out, f.lower()), index=False)
        done += 1

    print(f"resampled {done} runs to {a.n} points -> {a.out}")
    if failed:
        print(f"\n{len(failed)} run(s) failed:")
        for f, why in failed:
            print(f"   {f}: {why}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
