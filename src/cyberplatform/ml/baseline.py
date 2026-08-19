"""Baseline supervised model and cybersecurity-oriented evaluation metrics."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from cyberplatform.ml.preprocessing import infer_feature_types


@dataclass(frozen=True, slots=True)
class ClassificationMetrics:
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    tn: int
    fp: int
    fn: int
    tp: int
    fpr: float
    fnr: float
    roc_auc: float | None
    pr_auc: float | None
    confusion_matrix: tuple[tuple[int, int], tuple[int, int]]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["confusion_matrix"] = [list(row) for row in self.confusion_matrix]
        return payload


def build_baseline_pipeline(features: pd.DataFrame) -> Pipeline:
    """Create a leakage-safe logistic regression pipeline."""
    numeric_columns, categorical_columns = infer_feature_types(features)
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, numeric_columns),
            ("categorical", categorical_pipeline, categorical_columns),
        ],
        remainder="drop",
    )
    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", LogisticRegression(max_iter=1000, random_state=42, class_weight="balanced")),
        ]
    )


def train_baseline_classifier(features: pd.DataFrame, target: pd.Series) -> Pipeline:
    model = build_baseline_pipeline(features)
    model.fit(features, target)
    return model


def evaluate_classifier(
    model: Pipeline,
    features: pd.DataFrame,
    target: pd.Series,
    *,
    threshold: float = 0.5,
) -> ClassificationMetrics:
    """Evaluate a binary classifier with metrics relevant to SOC alert quality."""
    positive_scores: np.ndarray | None = None
    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(features)
        classes = list(model.named_steps["classifier"].classes_)
        if 1 in classes:
            positive_scores = np.asarray(probabilities[:, classes.index(1)], dtype=float)

    if positive_scores is not None:
        predictions = (positive_scores >= float(threshold)).astype(int)
    else:
        predictions = model.predict(features)

    matrix = confusion_matrix(target, predictions, labels=[0, 1])
    tn, fp, fn, tp = (int(value) for value in matrix.ravel())
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    fnr = fn / (fn + tp) if (fn + tp) else 0.0

    roc_auc: float | None = None
    pr_auc: float | None = None
    if positive_scores is not None and len(set(target.tolist())) == 2:
        roc_auc = float(roc_auc_score(target, positive_scores))
        pr_auc = float(average_precision_score(target, positive_scores))

    return ClassificationMetrics(
        accuracy=float(accuracy_score(target, predictions)),
        precision=float(precision_score(target, predictions, zero_division=0)),
        recall=float(recall_score(target, predictions, zero_division=0)),
        f1_score=float(f1_score(target, predictions, zero_division=0)),
        tn=tn,
        fp=fp,
        fn=fn,
        tp=tp,
        fpr=float(fpr),
        fnr=float(fnr),
        roc_auc=roc_auc,
        pr_auc=pr_auc,
        confusion_matrix=((tn, fp), (fn, tp)),
    )
