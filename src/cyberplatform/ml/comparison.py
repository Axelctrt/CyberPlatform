"""Model comparison helpers for sprint 4."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from cyberplatform.ml.baseline import (
    ClassificationMetrics,
    evaluate_classifier,
    train_baseline_classifier,
)
from cyberplatform.ml.primary import train_primary_classifier


@dataclass(frozen=True, slots=True)
class ModelComparison:
    baseline: ClassificationMetrics
    primary: ClassificationMetrics
    recommended_model: str


def compare_baseline_and_primary(
    train_features: pd.DataFrame,
    test_features: pd.DataFrame,
    train_target: pd.Series,
    test_target: pd.Series,
) -> ModelComparison:
    """Train and compare the baseline and primary model on the same split."""
    baseline_model = train_baseline_classifier(train_features, train_target)
    primary_model = train_primary_classifier(train_features, train_target)

    baseline_metrics = evaluate_classifier(baseline_model, test_features, test_target)
    primary_metrics = evaluate_classifier(primary_model, test_features, test_target)

    recommended_model = (
        "primary" if primary_metrics.f1_score >= baseline_metrics.f1_score else "baseline"
    )

    return ModelComparison(
        baseline=baseline_metrics,
        primary=primary_metrics,
        recommended_model=recommended_model,
    )

