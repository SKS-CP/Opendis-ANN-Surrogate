# Trained models

Checkpoints produced by `notebooks/01_ddd_ann_lstm_full.ipynb`. Each file holds
the network state at the epoch of lowest validation loss.

| File | Branch | Architecture | Predicts |
|---|---|---|---|
| `dpnet_v7_best_state.pt` | ANN, plastic flow | 10 → 128 → 256 → 128 → 64 → 5, SiLU, dropout 0.05 | Five independent components of **D**ᵖ |
| `rhonet_v7_best_state.pt` | ANN, density evolution | 11 → 128 → 128 → 64 → 32 → 1, SiLU, dropout 0.05 | d(log₁₀ρ)/dt |
| `dp_lstm_best_state.pt` | LSTM, plastic flow | Recurrent, input sequence length H = 24 | Five independent components of **D**ᵖ |
| `rho_lstm_best_state.pt` | LSTM, density evolution | Recurrent, H = 24, with Δt appended to the input | d(log₁₀ρ)/dt |

The sixth component of the plastic rate of deformation is not predicted. It
follows from plastic incompressibility:

```
Dp_zz = -(Dp_xx + Dp_yy)
```

## Loading a checkpoint

```python
import torch
state = torch.load("models/dpnet_v7_best_state.pt", map_location="cpu")
model.load_state_dict(state)
```

The normalisation statistics required to use these networks are written
alongside the processed dataset as `norm_stats_v7_rho_improved.json` and
`norm_stats_lstm_v1.json`. Regenerate them by running the notebook, which
rebuilds the processed dataset from `data/raw/`.

## Training configuration

Both surrogates were trained on the same 52 / 8 / 8 run-level split, grouped so
that no run appears in more than one split, and stratified by loading mode and
initial dislocation density. The loss combines a one-step supervised term with a
rollout term; optimisation used Adam with gradient clipping and a learning-rate
scheduler.
