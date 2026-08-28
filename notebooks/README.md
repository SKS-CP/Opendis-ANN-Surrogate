# Notebooks

| File | Contents |
|---|---|
| `01_ddd_ann_lstm_full.ipynb` | DDD drivers (PyExaDiS), ANN and LSTM training in one notebook. Checkpoints `dpnet_v7_best.pt`, `rhonet_v7_best.pt`. |
| `02_ann_v8.ipynb` | ANN training, later revision. Checkpoints `dpnet_v8_best.pt`, `rhonet_v8_best.pt`. |

**Before publishing, confirm which version produced the numbers in the paper.**
Both notebooks are present and they write different checkpoint names (v7 vs v8).
Whichever is authoritative should be the one the README points at; the other
should be removed or clearly labelled as superseded.

Both notebooks currently read the dataset from a hard-coded Colab path:

```
/content/SimulationCsvs.2721.zip
```

This must be replaced with a relative path into `data/` before release, or the
notebooks will not run for anyone else.
