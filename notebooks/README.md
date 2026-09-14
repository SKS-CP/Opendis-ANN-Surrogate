# Notebooks

| File | Contents |
|---|---|
| `ANNCODEMTECH.ipynb` | DDD drivers (PyExaDiS), and ANN and LSTM training and evaluation. Writes checkpoints `dpnet_v7_best.pt` and `rhonet_v7_best.pt` to `models/`. |

## Data path

The notebook reads the resampled database from `data/resampled/`, relative to the
repository root. Build it first:

```
python3 scripts/prepare_data.py --raw data/raw --out data/resampled
```

## Supervision modes

- **Mode A** supplies the true dislocation density at each step and rolls out the
  plastic strain only.
- **Mode B** is the fully coupled recursive rollout, in which both the plastic
  rate of deformation and the dislocation density are predicted and fed forward.
  This is the mode reported in the manuscript.
