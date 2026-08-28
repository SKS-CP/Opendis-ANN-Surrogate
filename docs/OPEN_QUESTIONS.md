# Decisions to make before this repository is published

Two things could not be settled from the files alone. Both are visible to a
reader, so they should be resolved before the repository is linked from the
paper.

## 1. Which surrogate notebook is authoritative

`notebooks/` contains two:

| Notebook | Writes checkpoints |
|---|---|
| `01_ddd_ann_lstm_full.ipynb` | `dpnet_v7_best.pt`, `rhonet_v7_best.pt` |
| `02_ann_v8.ipynb` | `dpnet_v8_best.pt`, `rhonet_v8_best.pt` |

Only one produced the 7.72% / 2.42% reported in the paper. Keep that one as the
reference and either delete the other or rename it with a clear `superseded_`
prefix and a line in `notebooks/README.md` saying so. Two unexplained versions
invites the question of which the results came from.

## 2. The train/validation/test split

The paper (Section 3.2.3) states **44 training, 8 validation, 16 test** runs,
and stresses that the ANN and LSTM use an identical split.

`docs/DDD_and_surrogate_documentation.pdf`, Section 7, states **52 training,
8 validation, 8 test** for the LSTM.

These cannot both be right. Whichever is correct, the other document needs
correcting, and the split actually used should be reproducible from the code.

## 3. Source folder for the database

Three folders were visible during preparation: `SimulationCsvs`,
`SimulationCsvs.2721` and `SimulationC...2721_0627`. Confirm which one the
published results came from, and copy only that one into `data/raw/`.

## Also worth doing

Both notebooks read the dataset from a hard-coded Colab path:

```
/content/SimulationCsvs.2721.zip
```

Replace this with a relative path into `data/` so the notebooks run for anyone
who clones the repository.
