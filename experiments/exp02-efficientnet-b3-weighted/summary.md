# exp02-efficientnet-b3-weighted

## Hyperparameters

| Parameter | Value |
|-----------|-------|
| `backbone` | `efficientnet_b3` |
| `batch_size` | `32` |
| `dropout` | `0.3` |
| `epochs` | `10` |
| `lr` | `0.0001` |
| `mixup_alpha` | `N/A` |
| `scheduler` | `cosine` |
| `seed` | `42` |
| `use_advanced_aug` | `False` |
| `use_class_weights` | `True` |
| `use_mixup` | `False` |
| `weight_decay` | `1e-05` |

## Results

Training epochs: **10**

| Metric | Value |
|--------|-------|
| `auc_roc` | **0.9644** |
| `accuracy` | **0.8113** |
| `f1_macro` | **0.7231** |
| `f1_weighted` | **0.8206** |
| `sensitivity` | **0.7946** |
| `specificity` | **0.9621** |
| `val_loss` | **0.6675** |
| `train_loss` | **0.3482** |
| `train_acc` | **0.8220** |
| `best_auc_roc` | **0.9644** |

## How to reproduce

```bash
python -m src.models.training \
  --backbone efficientnet_b3 \
  --batch_size 32 \
  --dropout 0.3 \
  --epochs 10 \
  --lr 0.0001 \
  --mixup_alpha N/A \
  --scheduler cosine \
  --seed 42 \
  --use_class_weights \
  --weight_decay 1e-05
```
