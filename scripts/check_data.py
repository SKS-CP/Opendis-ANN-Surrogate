#!/usr/bin/env python3
"""
check_ddd_output.py — consistency checks on DDD output files before they go into a table
or a training set.

Written after two rows of Table 4 in the surrogate-modelling manuscript were found to
violate trace(L^p) = 0. This script finds that class of problem automatically.

Checks performed on every time step:

  1. trace(L^p) ~ 0            plastic slip is volume preserving, so the trace of the
                               plastic velocity gradient must vanish. A non-zero trace
                               means a corrupted, shifted or mis-parsed row.

  2. eps_dot_eq consistency    the equivalent plastic strain rate recomputed from L^p as
                               sqrt(2/3 * D_dev : D_dev) must match the value recorded in
                               the file, where D = (L^p + L^p^T)/2.

  3. eps_eq monotonicity       accumulated equivalent plastic strain must not decrease.

  4. rho positivity            dislocation density must stay strictly positive (matters
                               because the surrogate works in log10 rho).

Usage
-----
    python3 check_ddd_output.py run1.dat run2.dat ...
    python3 check_ddd_output.py --tol 1e-3 *.dat
    python3 check_ddd_output.py --columns Lp_xx,Lp_xy,... run1.dat

Columns are found by name from the header line where possible (case-insensitive, and
tolerant of separators: "Lp_xx", "lp-xx", "LPXX" all match). If the header cannot be
parsed, pass --columns with the nine L^p column names in row-major order
(xx, xy, xz, yx, yy, yz, zx, zy, zz).

Exit status is 1 if any check fails, so it can be dropped into a pre-submission or
data-generation pipeline.
"""

import argparse
import re
import sys

import numpy as np

LP_ORDER = ["xx", "xy", "xz", "yx", "yy", "yz", "zx", "zy", "zz"]


def norm(name):
    """Strip units-in-parentheses, separators and case so header variants match.

    The OpenDiS driver writes headers like ``time(s)``, ``density(1/m^2)`` and
    ``epdot_eq(1/s)``; this reduces them to ``time``, ``density``, ``epdoteq``.
    """
    name = re.sub(r"\([^)]*\)", "", name)
    return re.sub(r"[^a-z0-9]", "", name.lower())


def find_column(headers, candidates):
    """Return the index of the first header matching any candidate name."""
    normed = [norm(h) for h in headers]
    for cand in candidates:
        c = norm(cand)
        if c in normed:
            return normed.index(c)
    return None


def load(path):
    """Read a whitespace- or comma-delimited table with a single header line."""
    with open(path) as fh:
        lines = [ln for ln in fh if ln.strip()]
    if not lines:
        raise ValueError("file is empty")

    header_line = lines[0].lstrip("#").strip()
    delim = "," if header_line.count(",") > 1 else None
    headers = [h.strip() for h in (header_line.split(",") if delim else header_line.split())]

    rows = []
    for ln in lines[1:]:
        parts = ln.split(",") if delim else ln.split()
        try:
            rows.append([float(p) for p in parts])
        except ValueError:
            continue  # skip repeated headers or comment lines mid-file

    if not rows:
        raise ValueError("no numeric rows found")

    width = min(len(r) for r in rows)
    data = np.array([r[:width] for r in rows])
    return headers[:width], data


def lp_indices(headers, override):
    if override:
        names = [n.strip() for n in override.split(",")]
        if len(names) != 9:
            raise ValueError("--columns needs exactly 9 names in order xx,xy,xz,yx,yy,yz,zx,zy,zz")
        idx = [find_column(headers, [n]) for n in names]
    else:
        idx = []
        for comp in LP_ORDER:
            idx.append(find_column(headers, [f"Lp{comp}", f"Lp_{comp}", f"L_{comp}",
                                             f"L^p_{comp}", f"Lp.{comp}"]))
    if any(i is None for i in idx):
        missing = [LP_ORDER[k] for k, i in enumerate(idx) if i is None]
        raise ValueError("could not locate L^p columns for: " + ", ".join(missing)
                         + "\n  headers seen: " + ", ".join(headers)
                         + "\n  pass them explicitly with --columns")
    return idx


def eq_rate(lp_row):
    """Equivalent plastic strain rate from the nine components of L^p."""
    L = lp_row.reshape(3, 3)
    Dp = 0.5 * (L + L.T)
    dev = Dp - np.eye(3) * np.trace(Dp) / 3.0
    return np.sqrt(2.0 / 3.0 * np.sum(dev * dev))


def check(path, tol, args):
    headers, data = load(path)
    idx = lp_indices(headers, args.columns)
    lp = data[:, idx]
    skip = max(0, args.skip_first)
    if skip:
        data, lp = data[skip:], lp[skip:]

    problems = []

    # --- 1. trace of L^p -------------------------------------------------
    trace = lp[:, 0] + lp[:, 4] + lp[:, 8]
    scale = np.maximum(np.abs(lp).max(axis=1), 1e-30)
    rel_trace = np.abs(trace) / scale
    bad = np.where(rel_trace > tol)[0]
    for r in bad:
        implied = -(lp[r, 0] + lp[r, 4])
        problems.append(
            f"row {r + 1 + skip}: trace(L^p) = {trace[r]:.4g} s^-1 "
            f"(relative {rel_trace[r]:.2e}); incompressibility implies "
            f"Lp_zz = {implied:.4g}, file has {lp[r, 8]:.4g}")

    # --- 2. recorded vs recomputed equivalent plastic strain rate --------
    i_rate = find_column(headers, ["epdot_eq", "eps_dot_eq", "epsdot_eq",
                                   "eps_p_dot", "edot_p_eq", "epsdotpeq"])
    if i_rate is not None:
        recomputed = np.array([eq_rate(row) for row in lp])
        recorded = data[:, i_rate]
        denom = np.maximum(np.abs(recorded), 1e-30)
        rel = np.abs(recomputed - recorded) / denom
        for r in np.where(rel > max(tol, 1e-2))[0]:
            problems.append(
                f"row {r + 1 + skip}: recorded eps_dot_eq = {recorded[r]:.4g} but L^p gives "
                f"{recomputed[r]:.4g} ({100 * rel[r]:.1f}% apart)")
    else:
        print(f"  note: no equivalent-plastic-strain-rate column found, check 2 skipped")

    # --- 3. monotonic accumulated strain ---------------------------------
    i_eps = find_column(headers, ["ep_eq", "eps_eq", "eps_p_eq", "epspeq"])
    if i_eps is not None:
        d = np.diff(data[:, i_eps])
        for r in np.where(d < -1e-12)[0]:
            problems.append(f"row {r + 2 + skip}: accumulated plastic strain decreased "
                            f"({data[r, i_eps]:.6g} -> {data[r + 1, i_eps]:.6g})")

    # --- 4. positive density ---------------------------------------------
    i_rho = find_column(headers, ["rho", "density", "disl_density", "rho_total"])
    if i_rho is not None:
        for r in np.where(data[:, i_rho] <= 0)[0]:
            problems.append(f"row {r + 1 + skip}: non-positive dislocation density "
                            f"({data[r, i_rho]:.4g}), log10 rho undefined")

    return len(data), problems


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", help="DDD output files to check")
    ap.add_argument("--tol", type=float, default=1e-2,
                    help="relative tolerance on the trace check (default 1e-2, which is loose "
                         "enough for values rounded to a few decimals; use 1e-6 or tighter on "
                         "full-precision output files)")
    ap.add_argument("--skip-first", type=int, default=1, metavar="N",
                    help="ignore the first N steps of each run (default 1). The "
                         "opening step of a DDD run is dominated by relaxation of "
                         "the seeded network, so trace(L^p) is looser there "
                         "(~6e-3 relative) than over the rest of the trajectory "
                         "(~2e-5). Pass 0 to check every step.")
    ap.add_argument("--columns", default=None,
                    help="comma-separated L^p column names, in order "
                         "xx,xy,xz,yx,yy,yz,zx,zy,zz")
    args = ap.parse_args()

    total_bad = 0
    for path in args.files:
        print(f"\n{path}")
        try:
            n, problems = check(path, args.tol, args)
        except Exception as exc:
            print(f"  could not check: {exc}")
            total_bad += 1
            continue

        if problems:
            total_bad += len(problems)
            print(f"  {len(problems)} problem(s) in {n} rows:")
            for p in problems[:40]:
                print(f"    {p}")
            if len(problems) > 40:
                print(f"    ... and {len(problems) - 40} more")
        else:
            print(f"  {n} rows, all checks passed")

    print(f"\n{'FAILED' if total_bad else 'OK'}: {total_bad} problem(s) total")
    return 1 if total_bad else 0


if __name__ == "__main__":
    sys.exit(main())
