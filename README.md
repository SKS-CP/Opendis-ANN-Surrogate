# Surrogate Material Modelling of Plasticity Using a Data-Driven Method

Code and data supporting the manuscript:

> A. Shankar, S. K. Shaw, R. Nayek, S. Chatterjee.
> *Surrogate Material Modelling of Plasticity Using a Data-Driven Method.*
> Submitted to Modelling and Simulation in Materials Science and Engineering.

A data-driven constitutive surrogate trained on three-dimensional Discrete
Dislocation Dynamics (DDD) simulations. The surrogate predicts five independent
components of the plastic rate of deformation tensor **D**^p — the sixth follows
from plastic incompressibility — together with the rate of logarithmic
dislocation-density evolution, in a fully coupled recursive rollout.

A feed-forward network (ANN) and a recurrent network (LSTM) are trained and
compared on the same database under matched supervision.

---

## What is here

| Path | Contents |
|---|---|
| `scripts/` | Data verification, resampling and utilities |
| `data/raw/` | Raw OpenDiS output, one CSV per run |
| `data/resampled/` | Runs resampled onto the common 1000-point time grid |
| `models/` | Trained ANN and LSTM weights |
| `notebooks/` | Training and evaluation notebooks |
| `figures/` | Scripts that produce the manuscript figures |
| `results/` | Rollout CSVs and metrics reported in the paper |
| `docs/` | Detailed documentation of the DDD drivers and the surrogate |

## Start here

New to git? Follow **`SETUP.md`** step by step -- it covers putting the data in
place, creating the repository and pushing it to GitHub.

Before publishing, read **`docs/OPEN_QUESTIONS.md`**.

## Requirements

```
pip install -r requirements.txt
```

The DDD drivers additionally require OpenDiS with the PyExaDiS Python bindings.
Installation instructions: https://opendis.github.io/OpenDiS/

## Reproducing the results

### 1. Check the database

```
python3 scripts/verify_dataset.py data/raw     # all 68 runs present?
python3 scripts/check_data.py data/raw/*.csv   # physics consistent?
```

`check_data.py` verifies, for every run, that `trace(Lp) = 0` and that the
recorded equivalent plastic strain rate equals `sqrt(2/3 Dp_dev : Dp_dev)`
computed from the plastic velocity gradient. The first step of each run is
skipped by default, because the opening step is dominated by relaxation of the
seeded network and its trace is looser (~6e-3 relative) than the rest of the
trajectory (~2e-5). Pass `--skip-first 0` to check every step.

### 2. Build the training set

```
python3 scripts/prepare_data.py --raw data/raw --out data/resampled
```

Resamples each run onto the common 1000-point time grid and derives the six
components of `Dp`, `log10(rho)` and `d(log10 rho)/dt`.

### 3. Train and evaluate

Training and rollout are in `notebooks/`. See `docs/OPEN_QUESTIONS.md` first --
there are two notebook versions and only one is authoritative.

Mode A supplies the true dislocation density and rolls out plastic strain only.
Mode B is the fully coupled rollout reported in the paper.

## Dataset

68 DDD runs. Four of the 72 possible conditions were omitted, all at the highest
target stress combined with the lowest loading rate (55 MPa, 4x10^7 MPa/s).

| | Values |
|---|---|
| Loading mode | uniaxial, pure shear |
| Target stress | 30, 40, 50, 55 MPa |
| Loading rate | 4, 6, 8 x10^7 MPa/s |
| Initial density | 0.957, 1.43, 2.05 x10^12 m^-2 |

Split: 44 training runs, 8 validation, 16 test, grouped at run level so no run
appears in more than one split.

## Results reported in the paper

| Model | Mean plastic-strain rollout error | Mean density rollout error |
|---|---|---|
| ANN | 7.72% | 2.42% |
| LSTM | 8.53% | 2.07% |

Fully coupled recursive rollout (Mode B) on the 16 held-out test runs.

## Citation

See `CITATION.cff`.

## Licence

Code is released under the MIT Licence (`LICENSE`). Data is released under
CC BY 4.0.
