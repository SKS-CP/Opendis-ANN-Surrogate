# OpenDiS-ANN-Surrogate

**Learning plastic flow and dislocation-density evolution from Discrete Dislocation Dynamics with a constitutive surrogate**

This repository contains the data, code and documentation for a data-driven
constitutive surrogate trained on three-dimensional Discrete Dislocation
Dynamics (DDD) simulations run with [OpenDiS](https://opendis.github.io/OpenDiS/).

**Authors:** Ayush Shankar, Santosh Kumar Shaw, Rajdip Nayek, Sabyasachi Chatterjee\*
Department of Applied Mechanics, Indian Institute of Technology Delhi
\*Corresponding author: sabyasachi@am.iitd.ac.in

> **Status:** the accompanying manuscript is in preparation. Please cite this
> repository (see [Citation](#citation)) until the paper is published.

---

## Contents

1. [What this repository does](#1-what-this-repository-does)
2. [Repository layout](#2-repository-layout)
3. [Installation](#3-installation)
4. [Quick start](#4-quick-start)
5. [The DDD dataset](#5-the-ddd-dataset)
6. [The surrogate model](#6-the-surrogate-model)
7. [Training and evaluation](#7-training-and-evaluation)
8. [Results](#8-results)
9. [Generating new DDD data](#9-generating-new-ddd-data)
10. [Citation](#citation)
11. [Licence](#licence)
12. [Contact](#contact)

---

## 1. What this repository does

Running a DDD simulation for every material point in a finite-element model is
far too expensive. Here, a neural network learns the DDD response directly and
can replace it as a constitutive law.

1. **Generate data.** 68 OpenDiS simulations of an FCC crystal under
   stress-controlled uniaxial and pure-shear loading.
2. **Learn plastic flow.** A network (**DpNet**) predicts the plastic rate of
   deformation tensor **D**ᵖ from the current stress, loading rate,
   dislocation density and accumulated plastic strain.
3. **Learn density evolution.** A second network (**RhoNet**) predicts the rate
   of change of log₁₀ρ.
4. **Roll out.** Starting from the initial state, the two networks are applied
   step by step. Each prediction is integrated in time and fed back as the next
   input, so the full plastic strain and density history is reproduced without
   running DDD.

Only five components of **D**ᵖ are predicted. The sixth follows from plastic
incompressibility (trace **D**ᵖ = 0):

```
Dp_zz = -(Dp_xx + Dp_yy)
```

A feed-forward network (ANN) and a recurrent network (LSTM) are compared on
the same data.

---

## 2. Repository layout

```
Opendis-ANN-Surrogate/
├── README.md                  this file
├── LICENSE                    MIT (code) + CC BY 4.0 (data)
├── CITATION.cff               citation metadata
├── requirements.txt           Python dependencies
│
├── data/
│   ├── README.md              file naming, units and column definitions
│   └── raw/                   68 DDD runs, one CSV per run (~213 MB)
│
├── scripts/
│   ├── verify_dataset.py      checks that all 68 expected runs are present
│   ├── check_data.py          physics consistency checks on each run
│   └── prepare_data.py        resamples runs onto a 1000-point time grid
│
├── notebooks/
│   ├── README.md
│   └── ANNCODEMTECH.ipynb     ANN training + evaluation, and the DDD driver
│
├── models/
│   └── README.md              trained weights and how to load them
│
├── results/                   rollout outputs and figures (created by the notebook)
│
└── docs/
    └── DDD_and_surrogate_documentation.pdf
                               OpenDiS installation, DDD drivers and the surrogate
```

---

## 3. Installation

**Requirements:** Python ≥ 3.9. A GPU is optional but makes training much faster.

1. Clone the repository:
   ```bash
   git clone https://github.com/SKS-CP/Opendis-ANN-Surrogate.git
   cd Opendis-ANN-Surrogate
   ```
2. (Recommended) Create a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install the Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. (Only if you want to run new DDD simulations) Install OpenDiS with the
   PyExaDiS Python bindings. Follow the
   [OpenDiS installation guide](https://opendis.github.io/OpenDiS/) or
   Section 1 of `docs/DDD_and_surrogate_documentation.pdf`.

You do **not** need OpenDiS to use the dataset or train the surrogate.

---

## 4. Quick start

Run these from the repository root.

1. **Check that the dataset is complete:**
   ```bash
   python3 scripts/verify_dataset.py data/raw
   ```
   Expected output: `expected runs : 68`, `matched runs : 68`, `no missing runs`.

2. **Run the physics consistency checks:**
   ```bash
   python3 scripts/check_data.py data/raw/*.csv
   ```
   See [Section 5.5](#55-consistency-checks) for what is checked and how to
   read the output.

3. **(Optional) Export a resampled copy of the data** for your own analysis:
   ```bash
   python3 scripts/prepare_data.py --raw data/raw --out data/resampled
   ```

4. **Train and evaluate the surrogate.** Follow
   [Section 7](#7-training-and-evaluation).

---

## 5. The DDD dataset

### 5.1 Simulation set-up

All runs use the same FCC crystal and simulation settings. Only the loading
and the initial dislocation density change between runs.

| Parameter | Value |
|---|---|
| Crystal structure | FCC |
| Burgers vector magnitude, *b* | 2.55 × 10⁻¹⁰ m |
| Shear modulus, μ | 54.6 GPa |
| Poisson's ratio, ν | 0.324 |
| Simulation box | 58 824 *b* ≈ 15 µm, periodic |
| Initial structure | straight dislocation lines (0°, 60°, 90° character), seed 1234 |
| Mobility law | `FCC_0`, M_edge = M_screw = 64 103 Pa⁻¹ s⁻¹ |
| Time integration | subcycling |
| Collisions | retroactive |

**Loading.** Stress is increased linearly in time, σ(t) = σ̇·t, and the run
stops when the target stress is reached.

1. **Uniaxial** runs load σ_zz. All other stress components are zero.
2. **Pure-shear** runs load σ_xy. All other stress components are zero.
   The "target stress" of a shear run is the value of σ_xy, so the von Mises
   stress at the end is √3 times larger.

### 5.2 Loading conditions

The dataset is a full grid of 2 × 4 × 3 × 3 = 72 conditions, minus 4 that were
not run, which leaves **68 runs**.

| Variable | Values |
|---|---|
| Loading mode | uniaxial, pure shear |
| Target stress | 30, 40, 50, 55 MPa |
| Stress rate, σ̇ | 4, 6, 8 × 10⁷ MPa/s |
| Initial dislocation density, ρ₀ | 0.957, 1.43, 2.05 × 10¹² m⁻² |

**Runs not performed.** All four are at 55 MPa with the lowest stress rate
(4 × 10⁷ MPa/s):

1. shear, all three initial densities
2. uniaxial, ρ₀ = 2.05 × 10¹² m⁻²

### 5.3 File naming

Each run is one CSV file in `data/raw/`:

```
<mode>_<target stress>Mpa_<stress rate>_<initial density>.csv
```

Example: `uniaxial_40Mpa_6e13_1.43e12.csv` is a uniaxial run to 40 MPa at
6 × 10¹³ Pa/s from ρ₀ = 1.43 × 10¹² m⁻².

> **Units in file names:** the stress rate is in **Pa/s**, so `6e13` in a file
> name is 6 × 10⁷ **MPa/s**. The initial densities in file names are
> `9.5668e11`, `1.43e12` and `2.055e12` m⁻².

### 5.4 Columns

Each file has one row per DDD time step (roughly 2 500 to 32 500 rows per run).

| Column | Meaning | Units |
|---|---|---|
| `step` | time-step index | – |
| `time(s)` | simulation time | s |
| `dt(s)` | time increment | s |
| `strain_eq` | equivalent total strain | – |
| `sigma_vm(Pa)` | von Mises stress | Pa |
| `s_xx(Pa)` … `s_xy(Pa)` | Cauchy stress, order xx, yy, zz, yz, zx, xy | Pa |
| `density(1/m^2)` | dislocation density ρ | m⁻² |
| `Lpxx` … `Lpzz` | plastic velocity gradient **L**ᵖ, 9 components, row-major | s⁻¹ |
| `epdot_eq(1/s)` | equivalent plastic strain rate | s⁻¹ |
| `ep_eq(-)` | accumulated equivalent plastic strain | – |

Full details are in [`data/README.md`](data/README.md).

### 5.5 Consistency checks

`scripts/check_data.py` checks every time step of every run for the following:

1. **Plastic incompressibility:** trace(**L**ᵖ) ≈ 0, relative to the largest
   component of **L**ᵖ at that step.
2. **Strain-rate consistency:** the recorded `epdot_eq` matches
   √(2/3 **D**ᵖ′ : **D**ᵖ′), where **D**ᵖ = (**L**ᵖ + **L**ᵖᵀ)/2 and
   **D**ᵖ′ is its deviatoric part.
3. **Monotonic plastic strain:** `ep_eq` never decreases.
4. **Positive density:** ρ > 0 at every step, because the surrogate works with
   log₁₀ρ.

The first step of each run is skipped by default because the seeded network
is still relaxing. Use `--skip-first 0` to include it.

**What to expect on this dataset:**

1. Checks 3 and 4 pass for every run.
2. Check 2 agrees except at a small number of steps.
3. For check 1, the median relative trace is about 1 × 10⁻³. With the default
   tolerance (`--tol 1e-2`), about 2 % of steps are flagged. These are mostly
   steps where plastic activity is very small, so the relative measure is
   noisy. The script therefore reports `FAILED`, which is expected with the
   default tolerance.

---

## 6. The surrogate model

### 6.1 Inputs and outputs

| Network | Inputs | Output |
|---|---|---|
| **DpNet** (10 inputs) | σ_xx, σ_yy, σ_zz, σ_yz, σ_zx, σ_xy; stress rate σ̇; log₁₀ρ; loading-mode flag (0 = uniaxial, 1 = shear); accumulated plastic strain ε̄ᵖ | Dᵖ_xx, Dᵖ_yy, Dᵖ_yz, Dᵖ_xz, Dᵖ_xy |
| **RhoNet** (11 inputs) | the same 10 inputs, plus the time step Δt | d(log₁₀ρ)/dt |

Inputs are scaled before training. Stress is divided by 55 MPa, log₁₀ρ is
shifted by 12, and σ̇ is used on a shifted log scale. The exact normalisation
statistics are saved by the notebook as a JSON file next to the dataset.

### 6.2 Architectures

| Network | Hidden layers | Activation | Dropout |
|---|---|---|---|
| DpNet (ANN) | 128 → 256 → 128 → 64 | SiLU | 0.05 |
| RhoNet (ANN) | 128 → 128 → 64 → 32 | SiLU | 0.05 |
| LSTM variants | recurrent, input window H = 24 steps | – | – |

### 6.3 Recursive rollout

At each time step *n*:

1. DpNet predicts **D**ᵖ, and ε̄ᵖ is updated:
   ε̄ᵖₙ₊₁ = ε̄ᵖₙ + ε̄̇ᵖₙ Δt
2. RhoNet predicts d(log₁₀ρ)/dt, and the density is updated:
   log₁₀ρₙ₊₁ = log₁₀ρₙ + (d log₁₀ρ/dt)ₙ Δt
3. The updated ε̄ᵖ and ρ are used as inputs for the next step.

Two evaluation modes are reported:

| Mode | What is predicted | Purpose |
|---|---|---|
| **Mode A** | plastic strain only; the true DDD density is supplied at every step | tests DpNet on its own |
| **Mode B** | plastic strain **and** density, both fed back (fully coupled) | the realistic use case, **reported in the paper** |

---

## 7. Training and evaluation

All training and evaluation code is in `notebooks/ANNCODEMTECH.ipynb`.

### 7.1 Running the notebook

The notebook was written for Google Colab and reads the raw CSVs from a zip
file.

1. Zip the raw data:
   ```bash
   cd data/raw && zip ../SimulationCsvs.zip *.csv && cd ../..
   ```
2. Open the notebook in Jupyter or Colab.
3. At the top of the first cell, set the paths:
   ```python
   ZIP_PATH    = "data/SimulationCsvs.zip"      # the zip from step 1
   DATASET_DIR = "results/dataset_v8_cellsplit"  # processed data is written here
   NN_OUT_DIR  = "results/nn_results_v8_cellsplit"  # models, metrics, plots
   ```
   On Colab, upload the zip and keep the default `/content/...` paths.
4. Run the **first cell only**. It builds the dataset, trains DpNet and RhoNet,
   and runs the Mode A and Mode B rollouts.
5. Do **not** run the second cell unless OpenDiS is installed. It is the DDD
   driver (see [Section 9](#9-generating-new-ddd-data)).

The notebook resamples the data itself. You do not need to run
`prepare_data.py` first.

### 7.2 Train / validation / test split

The split is made by **condition** (target stress, stress rate, ρ₀), not by
individual run. The uniaxial and shear runs of one condition always go into
the same split, so the surrogate is never tested on a condition it has seen
during training.

| Split | Conditions | Runs |
|---|---|---|
| Training | all remaining | **44** |
| Validation | 4 | **8** |
| Test | 8 | **16** |

**Test conditions** (each includes both the uniaxial and the shear run):

| Target stress | Stress rate (Pa/s) | ρ₀ (m⁻²) | Tests |
|---|---|---|---|
| 40 MPa | 4e13, 6e13, 8e13 | 1.43e12 | effect of loading rate |
| 40 MPa | 6e13 | 9.5668e11, 2.055e12 | effect of initial density |
| 30 MPa | 8e13 | 2.055e12 | low-stress coverage |
| 50 MPa | 8e13 | 9.5668e11 | mid-stress coverage |
| 55 MPa | 8e13 | 1.43e12 | high-stress coverage |

**Validation conditions:** (30 MPa, 4e13, 1.43e12), (40 MPa, 4e13, 9.5668e11),
(50 MPa, 6e13, 2.055e12), (55 MPa, 6e13, 9.5668e11).

### 7.3 Training settings

| Setting | Value |
|---|---|
| Time grid | 1000 uniform points per run |
| Loss | Huber (δ = 1), one-step term + rollout term |
| Rollout windows | length 24, stride 12 |
| Rollout loss weight | 0.35 (DpNet), 0.50 (RhoNet) |
| Optimiser | Adam, learning rate 3 × 10⁻⁴, weight decay 10⁻⁴ |
| Learning-rate schedule | cosine annealing with warm restarts (T₀ = 100, ×2) |
| Batch size | 512 (one-step), 128 (rollout) |
| Maximum epochs / early stopping | 2500 / patience 250 |
| Gradient clipping | 5.0 |
| Input noise | Gaussian, σ = 0.01 |
| Random seed | 42 |

### 7.4 Outputs

The notebook writes the following to `NN_OUT_DIR`:

| File | Contents |
|---|---|
| `dpnet_v8_best.pt`, `rhonet_v8_best.pt` | trained weights with normalisation and input order |
| `rollout_summary_modeA.csv`, `rollout_summary_modeB.csv` | error for each test run |
| `rollout_modeA_<run>.csv`, `rollout_modeB_<run>.csv` | predicted vs true history for each test run |
| `*_train_curves.png`, `dp_per_component_metrics.png` | training curves and diagnostics |

---

## 8. Results

Fully coupled rollout (Mode B) on the 16 held-out test runs. The error is the
mean relative error over the time history, averaged over all test runs.

| Model | Plastic-strain error | Density error |
|---|---|---|
| ANN | 7.72 % | 2.42 % |
| LSTM | 8.53 % | 2.07 % |

---

## 9. Generating new DDD data

The second cell of `notebooks/ANNCODEMTECH.ipynb` is the OpenDiS driver for
stress-controlled uniaxial loading. It writes the same columns as the files in
`data/raw/`.

1. Install OpenDiS and PyExaDiS (Section 3, step 4).
2. Copy the cell into a `.py` file inside `OpenDiS/core/exadis/python/`.
3. Set the loading for the run: target stress, stress rate and output folder
   (`write_dir`).
4. Set the initial density through `num_lines` in `generate_line_config`.
5. Run it:
   ```bash
   python3 your_run.py
   ```

`docs/DDD_and_surrogate_documentation.pdf` explains the driver line by line,
including the extension to strain-rate and cyclic strain-controlled loading.

---

## Citation

If you use this code or data, please cite:

```bibtex
@misc{shankar_opendis_ann_surrogate,
  author       = {Shankar, Ayush and Shaw, Santosh Kumar and Nayek, Rajdip and Chatterjee, Sabyasachi},
  title        = {{OpenDiS-ANN-Surrogate}: Learning plastic flow and dislocation-density
                  evolution from Discrete Dislocation Dynamics with a constitutive surrogate},
  year         = {2026},
  howpublished = {\url{https://github.com/SKS-CP/Opendis-ANN-Surrogate}}
}
```

Machine-readable metadata is in [`CITATION.cff`](CITATION.cff). This section
will be updated with the journal reference when the paper is published.

Please also cite OpenDiS if you use the DDD drivers.

---

## Licence

1. **Code:** MIT Licence, see [`LICENSE`](LICENSE).
2. **Data** (`data/`): Creative Commons Attribution 4.0 International
   ([CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)).

---

## Contact

1. **Corresponding author:** Prof. Sabyasachi Chatterjee, sabyasachi@am.iitd.ac.in
2. **Repository maintainer:** Santosh Kumar Shaw ([@SKS-CP](https://github.com/SKS-CP))

For bugs or questions about the code, please open a
[GitHub issue](https://github.com/SKS-CP/Opendis-ANN-Surrogate/issues).
