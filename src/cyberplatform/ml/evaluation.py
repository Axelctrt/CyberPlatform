"""Scientific evaluation helpers for binary cyberattack detection."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_curve,
)
from sklearn.pipeline import Pipeline

from cyberplatform.ml.primary import predict_attack_probabilities


def metrics_at_threshold(
    target: pd.Series,
    probabilities: list[float] | np.ndarray,
    threshold: float,
) -> dict[str, float | int]:
    """Compute decision metrics for a probability threshold."""
    scores = np.asarray(probabilities, dtype=float)
    truth = np.asarray(target, dtype=int)
    predictions = (scores >= float(threshold)).astype(int)

    tp = int(((truth == 1) & (predictions == 1)).sum())
    fp = int(((truth == 0) & (predictions == 1)).sum())
    fn = int(((truth == 1) & (predictions == 0)).sum())
    tn = int(((truth == 0) & (predictions == 0)).sum())
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    fnr = fn / (fn + tp) if (fn + tp) else 0.0

    return {
        "threshold": float(threshold),
        "precision": float(precision_score(truth, predictions, zero_division=0)),
        "recall": float(recall_score(truth, predictions, zero_division=0)),
        "f1_score": float(f1_score(truth, predictions, zero_division=0)),
        "fpr": float(fpr),
        "fnr": float(fnr),
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "tp": tp,
    }


def optimize_decision_threshold(
    model: Pipeline,
    validation_features: pd.DataFrame,
    validation_target: pd.Series,
    *,
    minimum_recall: float = 0.95,
) -> dict[str, Any]:
    """Choose a threshold on validation data only, never on the official test set.

    The primary objective is maximum F1 among thresholds satisfying the requested
    recall floor. Ties prefer lower FPR, then higher precision, then the higher
    threshold. If no threshold satisfies the recall floor, F1 is maximized without
    that constraint.
    """
    probabilities = predict_attack_probabilities(model, validation_features)
    candidates = [round(value, 2) for value in np.arange(0.10, 0.91, 0.01)]
    evaluated = [metrics_at_threshold(validation_target, probabilities, threshold) for threshold in candidates]
    feasible = [row for row in evaluated if float(row["recall"]) >= minimum_recall]
    pool = feasible or evaluated
    best = max(
        pool,
        key=lambda row: (
            float(row["f1_score"]),
            -float(row["fpr"]),
            float(row["precision"]),
            float(row["threshold"]),
        ),
    )
    return {
        "method": "validation_f1_with_recall_constraint",
        "minimum_recall": float(minimum_recall),
        "validation_rows": int(len(validation_features)),
        "constraint_satisfied": bool(feasible),
        "selected": best,
        "evaluated_thresholds": evaluated,
    }


def _downsample_curve(points: list[dict[str, float]], max_points: int = 160) -> list[dict[str, float]]:
    if len(points) <= max_points:
        return points
    indices = np.linspace(0, len(points) - 1, num=max_points, dtype=int)
    return [points[int(index)] for index in indices]


def binary_curve_points(
    model: Pipeline,
    features: pd.DataFrame,
    target: pd.Series,
    *,
    max_points: int = 160,
) -> dict[str, list[dict[str, float]]]:
    """Return compact ROC and precision-recall points for dashboard rendering."""
    probabilities = np.asarray(predict_attack_probabilities(model, features), dtype=float)
    truth = np.asarray(target, dtype=int)

    fpr, tpr, _ = roc_curve(truth, probabilities)
    precision, recall, _ = precision_recall_curve(truth, probabilities)

    roc_points = [
        {"fpr": float(x_value), "tpr": float(y_value)}
        for x_value, y_value in zip(fpr, tpr, strict=True)
    ]
    pr_points = [
        {"recall": float(x_value), "precision": float(y_value)}
        for x_value, y_value in zip(recall, precision, strict=True)
    ]
    return {
        "roc": _downsample_curve(roc_points, max_points=max_points),
        "precision_recall": _downsample_curve(pr_points, max_points=max_points),
    }
