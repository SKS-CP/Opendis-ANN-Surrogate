# Repository status and planned work

This repository accompanies a manuscript currently under review. The dataset and
the trained surrogates are complete and reproduce the results reported in the
paper; the items below are improvements planned before the final release, listed
here so anyone using the repository knows what to expect.

Issues and suggestions are welcome — please open an issue.

## Planned

### Consolidate the training notebooks

`notebooks/` currently contains two entry points:

| Notebook | Contents |
|---|---|
| `01_ddd_ann_lstm_full.ipynb` | OpenDiS drivers, ANN and LSTM training in one place |
| `02_ann_v8.ipynb` | ANN training, later revision |

These will be reduced to a single reference notebook per model, with the
superseded version removed. Until then, see `notebooks/README.md` for which
checkpoints each one writes.

### Replace hard-coded dataset paths

Both notebooks currently read the database from an absolute path used during
development on Google Colab:

```
/content/SimulationCsvs.2721.zip
```

This will become a relative path into `data/`, so the notebooks run unmodified
after a clone. Anyone working from the repository now should change this line
by hand.

### Standalone training and rollout scripts

Training and evaluation live in notebooks. Command-line equivalents are planned,
so that a full retrain and rollout can be reproduced without opening Jupyter:

```
scripts/train_ann.py
scripts/train_lstm.py
scripts/rollout.py
```

### Figure scripts

The scripts that generate the manuscript figures will be added under `figures/`,
so every figure in the paper can be regenerated from the data in this
repository.

## Known characteristics of the dataset

Not defects, but worth knowing before you use the data.

### Plastic incompressibility is satisfied to a finite tolerance

`trace(Lp)` vanishes on the large majority of steps but departs from zero on a
scattered minority, coinciding with topological events in the dislocation
network and with adaptive time-step cutbacks. This matters because `Dp_zz` is
reconstructed from the other two normal components. The distribution is
quantified by:

```
python3 scripts/trace_statistics.py data/raw/*.csv
```

See `data/README.md` for the full discussion.

### Loading rates are in Pa/s in filenames

Filenames use Pa/s (`4e13`, `6e13`, `8e13`) while the manuscript quotes MPa/s
(4, 6, 8 x10^7). These are the same three rates.

## Reference

The train/validation/test split reported in the manuscript — 44 training, 8
validation and 16 test runs, grouped at run level and identical for both
architectures — is the one used throughout this repository.
