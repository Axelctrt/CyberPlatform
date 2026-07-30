"""Primary supervised model used after the baseline sprint."""

from __future__ import annotations

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline

from cyberplatform.ml.baseline import build_baseline_pipeline


def build_primary_pipeline(features: pd.DataFrame) -> Pipeline:
    """Create the sprint 4 Random Forest model pipeline."""
    pipeline = build_baseline_pipeline(features)
    pipeline.steps[-1] = (
        "classifier",
        RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            class_weight="balanced",
        ),
    )
    return pipeline


def train_primary_classifier(features: pd.DataFrame, target: pd.Series) -> Pipeline:
    """Train the primary binary normal/attack classifier."""
    model = build_primary_pipeline(features)
    model.fit(features, target)
    return model


def predict_attack_probabilities(model: Pipeline, features: pd.DataFrame) -> list[float]:
    """Return the probability of the attack class for each row."""
    probabilities = model.predict_proba(features)
    classes = list(model.named_steps["classifier"].classes_)

    if 1 not in classes:
        return [0.0 for _ in range(len(features))]

    attack_index = classes.index(1)
    return [float(row[attack_index]) for row in probabilities]

