"""Persistence helpers for trained models."""

from __future__ import annotations

from pathlib import Path

import joblib
from sklearn.pipeline import Pipeline


def save_model(model: Pipeline, path: str | Path) -> Path:
    """Save a trained model pipeline to disk."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output_path)
    return output_path


def load_model(path: str | Path) -> Pipeline:
    """Load a previously saved model pipeline."""
    return joblib.load(Path(path))

