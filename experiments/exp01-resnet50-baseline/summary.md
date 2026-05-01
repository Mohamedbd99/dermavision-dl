# exp01-resnet50-baseline

## Hyperparameters

| Parameter | Value |
|-----------|-------|
| `backbone` | `resnet50` |
| `batch_size` | `32` |
| `dropout` | `0.2` |
| `epochs` | `5` |
| `lr` | `0.0001` |
| `mixup_alpha` | `N/A` |
| `scheduler` | `cosine` |
| `seed` | `42` |
| `use_advanced_aug` | `False` |
| `use_class_weights` | `False` |
| `use_mixup` | `False` |
| `weight_decay` | `1e-05` |

## Results

Training epochs: **5**

| Metric | Value |
|--------|-------|
| `auc_roc` | **0.9301** |
| `accuracy` | **0.7783** |
| `f1_macro` | **0.4669** |
| `f1_weighted` | **0.7585** |
| `sensitivity` | **0.4333** |
| `specificity` | **0.9345** |
| `val_loss` | **0.6174** |
| `train_loss` | **0.6241** |
| `train_acc` | **0.7712** |
| `best_auc_roc` | **0.9301** |

## How to reproduce

```bash
python -m src.models.training \
  --backbone resnet50 \
  --batch_size 32 \
  --dropout 0.2 \
  --epochs 5 \
  --lr 0.0001 \
  --mixup_alpha N/A \
  --scheduler cosine \
  --seed 42 \
  --weight_decay 1e-05
```
