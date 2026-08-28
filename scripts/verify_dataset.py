#!/usr/bin/env python3
"""
verify_dataset.py -- check the DDD CSV collection against the condition grid
described in the manuscript, before it goes into the repository.

Usage:
    python3 verify_dataset.py /path/to/SimulationCsvs
    python3 verify_dataset.py /path/to/SimulationCsvs --normalize-names

Expected grid (72 combinations, 4 deliberately omitted -> 68 runs):

    mode            uniaxial, shear
    target stress   30, 40, 50, 55 MPa
    loading rate    4e13, 6e13, 8e13 Pa/s   (= 4, 6, 8 x10^7 MPa/s)
    initial density 9.5668e11, 1.43e12, 2.055e12 m^-2

    omitted: shear 55 MPa 4e13 (all three densities)
             uniaxial 55 MPa 4e13 2.055e12

Reports: missing runs, unexpected extras, duplicates, case inconsistencies,
per-file size, and the column header of the first file so the data README can
be written against reality.
"""

import argparse
import os
import re
import sys
from itertools import product

MODES = ["uniaxial", "shear"]
STRESSES = ["30", "40", "50", "55"]
RATES = ["4e13", "6e13", "8e13"]
DENSITIES = ["9.5668e11", "1.43e12", "2.055e12"]

OMITTED = {
    ("shear", "55", "4e13", "9.5668e11"),
    ("shear", "55", "4e13", "1.43e12"),
    ("shear", "55", "4e13", "2.055e12"),
    ("uniaxial", "55", "4e13", "2.055e12"),
}

PATTERN = re.compile(
    r"^(?P<mode>uniaxial|shear)_(?P<stress>\d+)Mpa_(?P<rate>[\d.]+e\d+)_"
    r"(?P<density>[\d.]+e\d+)\.csv$",
    re.IGNORECASE,
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory")
    ap.add_argument("--normalize-names", action="store_true",
                    help="rewrite filenames to all-lowercase mode prefix")
    a = ap.parse_args()

    files = sorted(f for f in os.listdir(a.directory) if f.lower().endswith(".csv"))
    print(f"{len(files)} CSV files in {a.directory}\n")

    found, unparsed, mixed_case = {}, [], []
    for f in files:
        m = PATTERN.match(f)
        if not m:
            unparsed.append(f)
            continue
        key = (m.group("mode").lower(), m.group("stress"),
               m.group("rate").lower(), m.group("density"))
        if m.group("mode") != m.group("mode").lower():
            mixed_case.append(f)
        found.setdefault(key, []).append(f)

    expected = {k for k in product(MODES, STRESSES, RATES, DENSITIES)} - OMITTED

    missing = sorted(expected - set(found))
    extra = sorted(set(found) - expected)
    dupes = {k: v for k, v in found.items() if len(v) > 1}

    print(f"expected runs : {len(expected)}")
    print(f"matched runs  : {len(found)}")

    if unparsed:
        print(f"\nfilenames that do not match the naming scheme ({len(unparsed)}):")
        for f in unparsed:
            print("   " + f)

    if missing:
        print(f"\nMISSING ({len(missing)}):")
        for k in missing:
            print("   {}_{}Mpa_{}_{}.csv".format(*k))
    else:
        print("\nno missing runs")

    if extra:
        print(f"\nUNEXPECTED ({len(extra)}) -- not in the manuscript grid:")
        for k in extra:
            print("   " + ", ".join(k))

    if dupes:
        print(f"\nDUPLICATE conditions ({len(dupes)}):")
        for k, v in dupes.items():
            print("   " + ", ".join(k) + " -> " + ", ".join(v))

    if mixed_case:
        print(f"\ninconsistent capitalisation ({len(mixed_case)} files, "
              f"e.g. {mixed_case[0]})")
        print("   rerun with --normalize-names to fix")

    # sizes
    sizes = [(f, os.path.getsize(os.path.join(a.directory, f))) for f in files]
    total = sum(s for _, s in sizes)
    print(f"\ntotal size: {total/1e6:.1f} MB "
          f"(largest single file {max(s for _, s in sizes)/1e6:.1f} MB)")
    if total > 900e6:
        print("   -> too large for a comfortable GitHub repo; use Zenodo for the data")
    elif max(s for _, s in sizes) > 100e6:
        print("   -> at least one file exceeds GitHub's 100 MB limit")
    else:
        print("   -> fits in a GitHub repository")

    # header of the first file
    if files:
        with open(os.path.join(a.directory, files[0])) as fh:
            header = fh.readline().strip()
        print(f"\ncolumns in {files[0]}:")
        for c in header.split(","):
            print("   " + c.strip())

    if a.normalize_names:
        n = 0
        for f in mixed_case:
            m = PATTERN.match(f)
            new = f.replace(m.group("mode"), m.group("mode").lower(), 1)
            os.rename(os.path.join(a.directory, f), os.path.join(a.directory, new))
            n += 1
        print(f"\nrenamed {n} files to lowercase mode prefix")

    return 1 if (missing or extra or dupes or unparsed) else 0


if __name__ == "__main__":
    sys.exit(main())
