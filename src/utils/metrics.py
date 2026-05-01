import numpy as np
import torch
from sklearn.metrics import (
    roc_auc_score, f1_score, confusion_matrix,
    accuracy_score
)


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray) -> dict:
    """
    Compute all relevant metrics for multi-class classification.

    Args:
        y_true : (N,)    ground-truth integer class indices
        y_pred : (N,)    predicted integer class indices
        y_prob : (N, C)  predicted softmax probabilities

    Returns:
        dict of metric name → float value
    """
    n_classes = y_prob.shape[1]

    accuracy = accuracy_score(y_true, y_pred)
    f1_macro = f1_score(y_true, y_pred, average='macro', zero_division=0)
    f1_weighted = f1_score(y_true, y_pred, average='weighted', zero_division=0)

    # AUC-ROC (one-vs-rest, macro average)
    try:
        auc_roc = roc_auc_score(y_true, y_prob, multi_class='ovr', average='macro')
    except ValueError:
        auc_roc = 0.0

    # Per-class sensitivity (recall) and specificity from confusion matrix
    cm = confusion_matrix(y_true, y_pred, labels=list(range(n_classes)))
    sensitivity_per_class = []
    specificity_per_class = []

    for i in range(n_classes):
        tp = cm[i, i]
        fn = cm[i, :].sum() - tp
        fp = cm[:, i].sum() - tp
        tn = cm.sum() - tp - fn - fp

        sens = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        spec = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        sensitivity_per_class.append(sens)
        specificity_per_class.append(spec)

    sensitivity = float(np.mean(sensitivity_per_class))
    specificity  = float(np.mean(specificity_per_class))

    return {
        'accuracy'   : round(float(accuracy), 4),
        'auc_roc'    : round(float(auc_roc), 4),
        'f1_macro'   : round(float(f1_macro), 4),
        'f1_weighted': round(float(f1_weighted), 4),
        'sensitivity': round(sensitivity, 4),
        'specificity': round(specificity, 4),
    }
