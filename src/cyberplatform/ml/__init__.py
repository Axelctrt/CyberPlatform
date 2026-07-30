"""Machine learning pipeline components."""

from cyberplatform.ml.baseline import (
    ClassificationMetrics,
    build_baseline_pipeline,
    evaluate_classifier,
    train_baseline_classifier,
)
from cyberplatform.ml.comparison import ModelComparison, compare_baseline_and_primary
from cyberplatform.ml.persistence import load_model, save_model
from cyberplatform.ml.preprocessing import (
    create_train_test_split,
    events_to_dataframe,
    infer_feature_types,
    split_features_target,
)
from cyberplatform.ml.primary import (
    build_primary_pipeline,
    predict_attack_probabilities,
    train_primary_classifier,
)

__all__ = [
    "ClassificationMetrics",
    "ModelComparison",
    "build_baseline_pipeline",
    "build_primary_pipeline",
    "compare_baseline_and_primary",
    "create_train_test_split",
    "evaluate_classifier",
    "events_to_dataframe",
    "infer_feature_types",
    "load_model",
    "predict_attack_probabilities",
    "save_model",
    "split_features_target",
    "train_baseline_classifier",
    "train_primary_classifier",
]
