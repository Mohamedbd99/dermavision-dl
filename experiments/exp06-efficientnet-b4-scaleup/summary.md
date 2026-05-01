# exp06-efficientnet-b4-scaleup

## Hyperparameters

| Parameter | Value |
|-----------|-------|
| `backbone` | `efficientnet_b4` |
| `batch_size` | `32` |
| `dropout` | `0.4` |
| `epochs` | `20` |
| `lr` | `0.0001` |
| `mixup_alpha` | `N/A` |
| `scheduler` | `cosine` |
| `seed` | `42` |
| `use_advanced_aug` | `True` |
| `use_class_weights` | `True` |
| `use_mixup` | `False` |
| `weight_decay` | `1e-05` |

## Results

Training epochs: **20**

| Metric | Value |
|--------|-------|
| `auc_roc` | **0.9660** |
| `accuracy` | **0.7953** |
| `f1_macro` | **0.7105** |
| `f1_weighted` | **0.8072** |
| `sensitivity` | **0.7823** |
| `specificity` | **0.9600** |
| `val_loss` | **0.6267** |
| `train_loss` | **0.4121** |
| `train_acc` | **0.8015** |
| `best_auc_roc` | **0.9660** |

## How to reproduce

```bash
python -m src.models.training \
  --backbone efficientnet_b4 \
  --batch_size 32 \
  --dropout 0.4 \
  --epochs 20 \
  --lr 0.0001 \
  --mixup_alpha N/A \
  --scheduler cosine \
  --seed 42 \
  --use_advanced_aug \
  --use_class_weights \
  --weight_decay 1e-05
```
