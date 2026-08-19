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
    optimize_decision_threshold,
    save_model,
    train_primary_classifier,
)


def train_unsw_nb15(
    data_dir: str | Path,
    *,
    models_dir: str | Path = "models",
    metrics_path: str | Path = "reports/model_metrics.json",
    max_rows_per_file: int | None = None,
    minimum_recall: float = 0.95,
) -> dict[str, Any]:
    split = load_unsw_nb15_dataset(data_dir, max_rows_per_file=max_rows_per_file)

    # Threshold selection is deliberately isolated from the official test set.
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
    primary_threshold = float(threshold_selection["selected"]["threshold"])

    # Final models are fitted on the full official training partition.
    comparison = compare_baseline_and_primary(
        split.train_features,
        split.test_features,
        split.train_target,
        split.test_target,
        primary_threshold=primary_threshold,
        return_models=True,
    )
    if comparison.baseline_model is None or comparison.primary_model is None:
        raise RuntimeError("Training did not return fitted models.")

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
    selected_threshold = primary_threshold if comparison.recommended_model == "primary" else 0.5
    save_model(selected_model, output_dir / "primary_model.joblib")

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
        "baseline_decision_threshold": 0.5,
        "primary_decision_threshold": primary_threshold,
        "selected_decision_threshold": selected_threshold,
        "threshold_selection_scope": "stratified 20% holdout from official training partition only",
        "threshold_selection": threshold_selection,
        "baseline_metrics": comparison.baseline.to_dict(),
        "primary_metrics": comparison.primary.to_dict(),
        "curves": curves,
    }
    destination = Path(metrics_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


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
        help="Recall floor used to select the Random Forest decision threshold on training validation data.",
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
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
