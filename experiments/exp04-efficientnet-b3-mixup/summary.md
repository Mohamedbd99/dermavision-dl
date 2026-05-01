# exp04-efficientnet-b3-mixup

## Hyperparameters

| Parameter | Value |
|-----------|-------|
| `backbone` | `efficientnet_b3` |
| `batch_size` | `32` |
| `dropout` | `0.3` |
| `epochs` | `15` |
| `lr` | `0.0001` |
| `mixup_alpha` | `0.4` |
| `scheduler` | `cosine` |
| `seed` | `42` |
| `use_advanced_aug` | `False` |
| `use_class_weights` | `True` |
| `use_mixup` | `True` |
| `weight_decay` | `1e-05` |

## Results

Training epochs: **15**

| Metric | Value |
|--------|-------|
| `auc_roc` | **0.9523** |
| `accuracy` | **0.7903** |
| `f1_macro` | **0.6988** |
| `f1_weighted` | **0.8034** |
| `sensitivity` | **0.7939** |
| `specificity` | **0.9599** |
| `val_loss` | **0.6294** |
| `train_loss` | **0.7417** |
| `train_acc` | **0.6154** |
| `best_auc_roc` | **0.9523** |

## How to reproduce

```bash
python -m src.models.training \
  --backbone efficientnet_b3 \
  --batch_size 32 \
  --dropout 0.3 \
  --epochs 15 \
  --lr 0.0001 \
  --mixup_alpha 0.4 \
  --scheduler cosine \
  --seed 42 \
  --use_class_weights \
  --use_mixup \
  --weight_decay 1e-05
```
