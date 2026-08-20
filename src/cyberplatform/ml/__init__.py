"""Machine learning pipeline components."""

from cyberplatform.ml.baseline import (
    ClassificationMetrics,
    build_baseline_pipeline,
    evaluate_classifier,
    train_baseline_classifier,
)
from cyberplatform.ml.comparison import ModelComparison, compare_baseline_and_primary
from cyberplatform.ml.evaluation import binary_curve_points, metrics_at_threshold, optimize_decision_threshold
from cyberplatform.ml.explainability import feature_importance_table
from cyberplatform.ml.inference import expected_model_columns, predict_unsw_dataframe, prepare_inference_features
from cyberplatform.ml.multiclass import (
    MulticlassMetrics,
    build_attack_family_pipeline,
    evaluate_attack_family_classifier,
    predict_attack_families,
    train_attack_family_classifier,
)
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
    "MulticlassMetrics",
    "binary_curve_points",
    "build_attack_family_pipeline",
    "build_baseline_pipeline",
    "build_primary_pipeline",
    "compare_baseline_and_primary",
    "create_train_test_split",
    "evaluate_attack_family_classifier",
    "evaluate_classifier",
    "events_to_dataframe",
    "expected_model_columns",
    "feature_importance_table",
    "infer_feature_types",
    "load_model",
    "metrics_at_threshold",
    "optimize_decision_threshold",
    "predict_attack_families",
    "predict_attack_probabilities",
    "predict_unsw_dataframe",
    "prepare_inference_features",
    "save_model",
    "split_features_target",
    "train_attack_family_classifier",
    "train_baseline_classifier",
    "train_primary_classifier",
]
