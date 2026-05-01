# exp07-optuna

## Hyperparameters

| Parameter | Value |
|-----------|-------|
| `backbone` | `efficientnet_b3` |
| `dropout` | `0.22930163420191518` |
| `lr` | `0.000236288641842364` |
| `n_trials` | `10` |
| `scheduler` | `cosine` |
| `trial_epochs` | `5` |
| `weight_decay` | `8.200518402245835e-06` |

## Results

Training epochs: **0**

| Metric | Value |
|--------|-------|

## How to reproduce

```bash
python -m src.models.training \
  --backbone efficientnet_b3 \
  --dropout 0.22930163420191518 \
  --lr 0.000236288641842364 \
  --n_trials 10 \
  --scheduler cosine \
  --trial_epochs 5 \
  --weight_decay 8.200518402245835e-06
```
