# exp03-efficientnet-b3-advanced-aug

## Hyperparameters

| Parameter | Value |
|-----------|-------|
| `backbone` | `efficientnet_b3` |
| `batch_size` | `32` |
| `dropout` | `0.3` |
| `epochs` | `15` |
| `lr` | `0.0001` |
| `mixup_alpha` | `N/A` |
| `scheduler` | `cosine` |
| `seed` | `42` |
| `use_advanced_aug` | `True` |
| `use_class_weights` | `True` |
| `use_mixup` | `False` |
| `weight_decay` | `1e-05` |

## Results

Training epochs: **15**

| Metric | Value |
|--------|-------|
| `auc_roc` | **0.9713** |
| `accuracy` | **0.8238** |
| `f1_macro` | **0.7720** |
| `f1_weighted` | **0.8321** |
| `sensitivity` | **0.8348** |
| `specificity` | **0.9642** |
| `val_loss` | **0.5689** |
| `train_loss` | **0.2944** |
| `train_acc` | **0.8498** |
| `best_auc_roc` | **0.9713** |

## How to reproduce

```bash
python -m src.models.training \
  --backbone efficientnet_b3 \
  --batch_size 32 \
  --dropout 0.3 \
  --epochs 15 \
  --lr 0.0001 \
  --mixup_alpha N/A \
  --scheduler cosine \
  --seed 42 \
  --use_advanced_aug \
  --use_class_weights \
  --weight_decay 1e-05
```
