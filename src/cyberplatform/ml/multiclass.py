"""Experimental multiclass attack-family classification for UNSW-NB15 attacks."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
)
from sklearn.pipeline import Pipeline

from cyberplatform.ml.baseline import build_baseline_pipeline


@dataclass(frozen=True, slots=True)
class MulticlassMetrics:
    """Metrics for conditional attack-family classification."""

    accuracy: float
    balanced_accuracy: float
    macro_precision: float
    macro_recall: float
    macro_f1: float
    weighted_precision: float
    weighted_recall: float
    weighted_f1: float
    labels: tuple[str, ...]
    confusion_matrix: tuple[tuple[int, ...], ...]
    per_class: dict[str, dict[str, float | int]]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["labels"] = list(self.labels)
        payload["confusion_matrix"] = [list(row) for row in self.confusion_matrix]
        return payload


def build_attack_family_pipeline(features: pd.DataFrame) -> Pipeline:
    """Build a Random Forest classifier dedicated to attack families."""
    pipeline = build_baseline_pipeline(features)
    pipeline.steps[-1] = (
        "classifier",
        RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            class_weight="balanced_subsample",
        ),
    )
    return pipeline


def train_attack_family_classifier(features: pd.DataFrame, target: pd.Series) -> Pipeline:
    """Train a multiclass classifier on attack rows only."""
    clean_target = target.astype(str).str.strip()
    if clean_target.nunique() < 2:
        raise ValueError("Attack-family training requires at least two distinct attack categories.")
    model = build_attack_family_pipeline(features)
    model.fit(features, clean_target)
    return model


def predict_attack_families(
    model: Pipeline,
    features: pd.DataFrame,
) -> tuple[list[str], list[float]]:
    """Return predicted attack family and maximum class probability for each row."""
    probabilities = np.asarray(model.predict_proba(features), dtype=float)
    classes = [str(value) for value in model.named_steps["classifier"].classes_]
    winning_indices = probabilities.argmax(axis=1)
    predictions = [classes[int(index)] for index in winning_indices]
    confidence = [float(probabilities[row_index, class_index]) for row_index, class_index in enumerate(winning_indices)]
    return predictions, confidence


def evaluate_attack_family_classifier(
    model: Pipeline,
    features: pd.DataFrame,
    target: pd.Series,
) -> MulticlassMetrics:
    """Evaluate attack-family identification with imbalance-aware metrics."""
    truth = target.astype(str).str.strip().to_numpy()
    predictions = np.asarray(model.predict(features), dtype=str)
    labels = tuple(sorted({*map(str, model.named_steps["classifier"].classes_), *truth.tolist()}))

    precision, recall, f1, support = precision_recall_fscore_support(
        truth,
        predictions,
        labels=list(labels),
        zero_division=0,
    )
    macro_precision, macro_recall, macro_f1, _ = precision_recall_fscore_support(
        truth,
        predictions,
        average="macro",
        zero_division=0,
    )
    weighted_precision, weighted_recall, weighted_f1, _ = precision_recall_fscore_support(
        truth,
        predictions,
        average="weighted",
        zero_division=0,
    )
    matrix = confusion_matrix(truth, predictions, labels=list(labels))

    per_class = {
        label: {
            "precision": float(precision[index]),
            "recall": float(recall[index]),
            "f1_score": float(f1[index]),
            "support": int(support[index]),
        }
        for index, label in enumerate(labels)
    }

    return MulticlassMetrics(
        accuracy=float(accuracy_score(truth, predictions)),
        balanced_accuracy=float(balanced_accuracy_score(truth, predictions)),
        macro_precision=float(macro_precision),
        macro_recall=float(macro_recall),
        macro_f1=float(macro_f1),
        weighted_precision=float(weighted_precision),
        weighted_recall=float(weighted_recall),
        weighted_f1=float(weighted_f1),
        labels=labels,
        confusion_matrix=tuple(tuple(int(value) for value in row) for row in matrix.tolist()),
        per_class=per_class,
    )
