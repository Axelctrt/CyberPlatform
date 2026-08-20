"""Command-line training pipeline for the scientific UNSW-NB15 experiment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from sklearn.model_selection import train_test_split

from cyberplatform.datasets import load_unsw_nb15_dataset
from cyberplatform.ml import (
    binary_curve_points,
    compare_baseline_and_primary,
    evaluate_attack_family_classifier,
    evaluate_classifier,
    optimize_decision_threshold,
    save_model,
    train_attack_family_classifier,
    train_primary_classifier,
)


DEFAULT_OPERATIONAL_THRESHOLD = 0.50


def _attack_family_experiment(split: Any, output_dir: Path) -> dict[str, Any]:
    """Train a conditional multiclass model on labelled attack rows only."""
    train_mask = split.train_target.eq(1) & split.train_attack_categories.notna()
    test_mask = split.test_target.eq(1) & split.test_attack_categories.notna()

    train_features = split.train_features.loc[train_mask].reset_index(drop=True)
    train_categories = split.train_attack_categories.loc[train_mask].astype(str).str.strip().reset_index(drop=True)
    test_features = split.test_features.loc[test_mask].reset_index(drop=True)
    test_categories = split.test_attack_categories.loc[test_mask].astype(str).str.strip().reset_index(drop=True)

    distinct_train_classes = sorted(train_categories.unique().tolist())
    if len(distinct_train_classes) < 2 or test_features.empty:
        return {
            "status": "unavailable",
            "reason": "At least two labelled attack families in training and labelled attack rows in test are required.",
            "train_rows": int(len(train_features)),
            "test_rows": int(len(test_features)),
            "train_classes": distinct_train_classes,
        }

    model = train_attack_family_classifier(train_features, train_categories)
    metrics = evaluate_attack_family_classifier(model, test_features, test_categories)
    save_model(model, output_dir / "attack_family_random_forest.joblib")

    return {
        "status": "available",
        "role": "secondary scientific enrichment; binary detection remains operational gate",
        "task": "conditional attack-family classification on attack rows only",
        "model": "Random Forest",
        "train_rows": int(len(train_features)),
        "test_rows": int(len(test_features)),
        "train_class_distribution": {
            str(key): int(value) for key, value in train_categories.value_counts().sort_index().items()
        },
        "test_class_distribution": {
            str(key): int(value) for key, value in test_categories.value_counts().sort_index().items()
        },
        "metrics": metrics.to_dict(),
    }


def train_unsw_nb15(
    data_dir: str | Path,
    *,
    models_dir: str | Path = "models",
    metrics_path: str | Path = "reports/model_metrics.json",
    max_rows_per_file: int | None = None,
    minimum_recall: float = 0.95,
) -> dict[str, Any]:
    split = load_unsw_nb15_dataset(data_dir, max_rows_per_file=max_rows_per_file)

    # Threshold tuning is an experiment isolated from the official test set.
    fit_features, validation_features, fit_target, validation_target = train_test_split(
        split.train_features,
        split.train_target,
        test_size=0.20,
        random_state=42,
        stratify=split.train_target,
    )
    provisional_primary = train_primary_classifier(fit_features, fit_target)
    threshold_selection = optimize_decision_threshold(
        provisional_primary,
        validation_features,
        validation_target,
        minimum_recall=minimum_recall,
    )
    experimental_threshold = float(threshold_selection["selected"]["threshold"])

    # The operational comparison keeps the pre-specified 0.50 threshold. This avoids
    # silently deploying a tuned threshold when the official train/test distributions
    # differ. The tuned threshold is still evaluated and reported as a sensitivity study.
    comparison = compare_baseline_and_primary(
        split.train_features,
        split.test_features,
        split.train_target,
        split.test_target,
        primary_threshold=DEFAULT_OPERATIONAL_THRESHOLD,
        return_models=True,
    )
    if comparison.baseline_model is None or comparison.primary_model is None:
        raise RuntimeError("Training did not return fitted models.")

    experimental_primary_metrics = evaluate_classifier(
        comparison.primary_model,
        split.test_features,
        split.test_target,
        threshold=experimental_threshold,
    )

    output_dir = Path(models_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    save_model(comparison.baseline_model, output_dir / "logistic_regression.joblib")
    save_model(comparison.primary_model, output_dir / "random_forest.joblib")

    selected_model = (
        comparison.primary_model
        if comparison.recommended_model == "primary"
        else comparison.baseline_model
    )
    selected_name = (
        "Random Forest" if comparison.recommended_model == "primary" else "Logistic Regression"
    )
    save_model(selected_model, output_dir / "primary_model.joblib")

    multiclass_experiment = _attack_family_experiment(split, output_dir)

    curves = {
        "baseline": binary_curve_points(
            comparison.baseline_model,
            split.test_features,
            split.test_target,
        ),
        "primary": binary_curve_points(
            comparison.primary_model,
            split.test_features,
            split.test_target,
        ),
    }

    payload: dict[str, Any] = {
        "dataset": "UNSW-NB15",
        "task": "binary normal/attack classification",
        "split_strategy": split.split_strategy,
        "train_rows": len(split.train_features),
        "test_rows": len(split.test_features),
        "feature_columns": list(split.feature_columns),
        "baseline_model": "Logistic Regression",
        "primary_candidate": "Random Forest",
        "selected_model": selected_name,
        "baseline_decision_threshold": DEFAULT_OPERATIONAL_THRESHOLD,
        "primary_decision_threshold": DEFAULT_OPERATIONAL_THRESHOLD,
        "selected_decision_threshold": DEFAULT_OPERATIONAL_THRESHOLD,
        "experimental_tuned_threshold": experimental_threshold,
        "threshold_selection_scope": "stratified 20% holdout from official training partition only",
        "threshold_selection": threshold_selection,
        "threshold_policy": (
            "The validation-tuned threshold is reported as a sensitivity experiment. "
            "The operational dashboard keeps the pre-specified 0.50 threshold so that "
            "a threshold that fails to generalize is not silently deployed."
        ),
        "baseline_metrics": comparison.baseline.to_dict(),
        "primary_metrics": comparison.primary.to_dict(),
        "primary_metrics_experimental_threshold": experimental_primary_metrics.to_dict(),
        "multiclass_experiment": multiclass_experiment,
        "curves": curves,
    }
    destination = Path(metrics_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


def console_summary(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a readable CLI summary while the full scientific report stays on disk."""
    selection = payload.get("threshold_selection", {})
    multiclass = payload.get("multiclass_experiment", {})
    multiclass_metrics = multiclass.get("metrics", {}) if multiclass.get("status") == "available" else {}
    return {
        "dataset": payload.get("dataset"),
        "task": payload.get("task"),
        "split_strategy": payload.get("split_strategy"),
        "train_rows": payload.get("train_rows"),
        "test_rows": payload.get("test_rows"),
        "selected_model": payload.get("selected_model"),
        "selected_decision_threshold": payload.get("selected_decision_threshold"),
        "experimental_tuned_threshold": payload.get("experimental_tuned_threshold"),
        "threshold_selection_scope": payload.get("threshold_selection_scope"),
        "threshold_validation": selection.get("selected"),
        "baseline_metrics": payload.get("baseline_metrics"),
        "primary_metrics": payload.get("primary_metrics"),
        "primary_metrics_experimental_threshold": payload.get("primary_metrics_experimental_threshold"),
        "multiclass_experiment": {
            "status": multiclass.get("status"),
            "train_rows": multiclass.get("train_rows"),
            "test_rows": multiclass.get("test_rows"),
            "classes": multiclass_metrics.get("labels", multiclass.get("train_classes", [])),
            "accuracy": multiclass_metrics.get("accuracy"),
            "balanced_accuracy": multiclass_metrics.get("balanced_accuracy"),
            "macro_f1": multiclass_metrics.get("macro_f1"),
            "weighted_f1": multiclass_metrics.get("weighted_f1"),
        },
        "full_report": "reports/model_metrics.json",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train CyberPlatform models on UNSW-NB15.")
    parser.add_argument("--data-dir", default="data/raw/unsw_nb15")
    parser.add_argument("--models-dir", default="models")
    parser.add_argument("--metrics-path", default="reports/model_metrics.json")
    parser.add_argument(
        "--max-rows-per-file",
        type=int,
        default=None,
        help="Optional Windows-friendly row cap for each CSV during experimentation.",
    )
    parser.add_argument(
        "--minimum-recall",
        type=float,
        default=0.95,
        help="Recall floor used for the experimental Random Forest threshold study.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    payload = train_unsw_nb15(
        args.data_dir,
        models_dir=args.models_dir,
        metrics_path=args.metrics_path,
        max_rows_per_file=args.max_rows_per_file,
        minimum_recall=args.minimum_recall,
    )
    summary = console_summary(payload)
    summary["full_report"] = str(args.metrics_path)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
