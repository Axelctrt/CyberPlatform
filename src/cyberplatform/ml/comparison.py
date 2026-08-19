"""Model comparison helpers."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.pipeline import Pipeline

from cyberplatform.ml.baseline import ClassificationMetrics, evaluate_classifier, train_baseline_classifier
from cyberplatform.ml.primary import train_primary_classifier


@dataclass(frozen=True, slots=True)
class ModelComparison:
    baseline: ClassificationMetrics
    primary: ClassificationMetrics
    recommended_model: str
    baseline_model: Pipeline | None = None
    primary_model: Pipeline | None = None


def compare_baseline_and_primary(
    train_features: pd.DataFrame,
    test_features: pd.DataFrame,
    train_target: pd.Series,
    test_target: pd.Series,
    *,
    return_models: bool = False,
) -> ModelComparison:
    baseline_model = train_baseline_classifier(train_features, train_target)
    primary_model = train_primary_classifier(train_features, train_target)
    baseline_metrics = evaluate_classifier(baseline_model, test_features, test_target)
    primary_metrics = evaluate_classifier(primary_model, test_features, test_target)

    baseline_rank = (baseline_metrics.f1_score, baseline_metrics.recall, baseline_metrics.precision)
    primary_rank = (primary_metrics.f1_score, primary_metrics.recall, primary_metrics.precision)
    recommended_model = "primary" if primary_rank >= baseline_rank else "baseline"

    return ModelComparison(
        baseline=baseline_metrics,
        primary=primary_metrics,
        recommended_model=recommended_model,
        baseline_model=baseline_model if return_models else None,
        primary_model=primary_model if return_models else None,
    )
