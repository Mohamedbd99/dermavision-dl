# exp07-optuna-FINAL

## Hyperparameters

| Parameter | Value |
|-----------|-------|
| `backbone` | `efficientnet_b3` |
| `batch_size` | `32` |
| `dropout` | `0.22930163420191518` |
| `epochs` | `20` |
| `lr` | `0.000236288641842364` |
| `mixup_alpha` | `N/A` |
| `scheduler` | `cosine` |
| `seed` | `42` |
| `use_advanced_aug` | `True` |
| `use_class_weights` | `True` |
| `use_mixup` | `False` |
| `weight_decay` | `8.200518402245835e-06` |

## Results

Training epochs: **20**

| Metric | Value |
|--------|-------|
| `auc_roc` | **0.9776** |
| `accuracy` | **0.8542** |
| `f1_macro` | **0.7962** |
| `f1_weighted` | **0.8597** |
| `sensitivity` | **0.8284** |
| `specificity` | **0.9697** |
| `val_loss` | **0.6530** |
| `train_loss` | **0.1355** |
| `train_acc` | **0.9165** |
| `best_auc_roc` | **0.9776** |

## How to reproduce

```bash
python -m src.models.training \
  --backbone efficientnet_b3 \
  --batch_size 32 \
  --dropout 0.22930163420191518 \
  --epochs 20 \
  --lr 0.000236288641842364 \
  --mixup_alpha N/A \
  --scheduler cosine \
  --seed 42 \
  --use_advanced_aug \
  --use_class_weights \
  --weight_decay 8.200518402245835e-06
```
