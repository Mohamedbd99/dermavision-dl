# exp05-efficientnet-b3-full-stack

## Hyperparameters

| Parameter | Value |
|-----------|-------|
| `backbone` | `efficientnet_b3` |
| `batch_size` | `32` |
| `dropout` | `0.3` |
| `epochs` | `20` |
| `lr` | `0.0001` |
| `mixup_alpha` | `0.4` |
| `scheduler` | `cosine` |
| `seed` | `42` |
| `use_advanced_aug` | `True` |
| `use_class_weights` | `True` |
| `use_mixup` | `True` |
| `weight_decay` | `1e-05` |

## Results

Training epochs: **20**

| Metric | Value |
|--------|-------|
| `auc_roc` | **0.9603** |
| `accuracy` | **0.8013** |
| `f1_macro` | **0.7208** |
| `f1_weighted` | **0.8135** |
| `sensitivity` | **0.8199** |
| `specificity` | **0.9624** |
| `val_loss` | **0.5911** |
| `train_loss` | **0.7210** |
| `train_acc` | **0.6124** |
| `best_auc_roc` | **0.9603** |

## How to reproduce

```bash
python -m src.models.training \
  --backbone efficientnet_b3 \
  --batch_size 32 \
  --dropout 0.3 \
  --epochs 20 \
  --lr 0.0001 \
  --mixup_alpha 0.4 \
  --scheduler cosine \
  --seed 42 \
  --use_advanced_aug \
  --use_class_weights \
  --use_mixup \
  --weight_decay 1e-05
```
