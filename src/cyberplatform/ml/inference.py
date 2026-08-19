"""Inference helpers for a saved UNSW-NB15-compatible model."""

from __future__ import annotations

import pandas as pd
from sklearn.pipeline import Pipeline

from cyberplatform.ml.primary import predict_attack_probabilities


def expected_model_columns(model: Pipeline) -> list[str]:
    preprocessor = model.named_steps.get("preprocessor")
    columns = getattr(preprocessor, "feature_names_in_", None)
    if columns is None:
        raise ValueError("The saved model does not expose its training feature columns.")
    return [str(column) for column in columns]


def prepare_inference_features(dataframe: pd.DataFrame, model: Pipeline) -> pd.DataFrame:
    """Validate and align incoming network rows to the training schema."""
    frame = dataframe.copy()
    frame.columns = [str(column).strip().lower() for column in frame.columns]
    required = expected_model_columns(model)
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(
            "Input is not compatible with the trained UNSW-NB15 model. Missing columns: "
            + ", ".join(missing[:12])
            + ("..." if len(missing) > 12 else "")
        )
    return frame[required].copy()


def predict_unsw_dataframe(
    model: Pipeline,
    dataframe: pd.DataFrame,
    *,
    threshold: float = 0.5,
) -> pd.DataFrame:
    """Return binary decisions and attack probabilities without retraining."""
    features = prepare_inference_features(dataframe, model)
    probabilities = predict_attack_probabilities(model, features)
    predictions = [int(probability >= threshold) for probability in probabilities]
    result = dataframe.copy().reset_index(drop=True)
    result["prediction"] = predictions
    result["attack_probability"] = probabilities
    return result
