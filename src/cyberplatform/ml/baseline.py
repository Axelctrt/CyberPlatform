"""Baseline supervised model for attack detection."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from cyberplatform.ml.preprocessing import infer_feature_types


@dataclass(frozen=True, slots=True)
class ClassificationMetrics:
    accuracy: float
    precision: float
    recall: float
    f1_score: float


def build_baseline_pipeline(features: pd.DataFrame) -> Pipeline:
    """Create a simple logistic regression baseline pipeline."""
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
        ]
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", LogisticRegression(max_iter=1000, random_state=42)),
        ]
    )


def train_baseline_classifier(features: pd.DataFrame, target: pd.Series) -> Pipeline:
    """Train the first binary normal/attack baseline."""
    model = build_baseline_pipeline(features)
    model.fit(features, target)
    return model


def evaluate_classifier(
    model: Pipeline,
    features: pd.DataFrame,
    target: pd.Series,
) -> ClassificationMetrics:
    """Evaluate a binary classifier with the sprint 3 metrics."""
    predictions = model.predict(features)

    return ClassificationMetrics(
        accuracy=accuracy_score(target, predictions),
        precision=precision_score(target, predictions, zero_division=0),
        recall=recall_score(target, predictions, zero_division=0),
        f1_score=f1_score(target, predictions, zero_division=0),
    )

