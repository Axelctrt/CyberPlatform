"""Lightweight explainability helpers for tree-based prototype models."""

from __future__ import annotations

import pandas as pd
from sklearn.pipeline import Pipeline


def feature_importance_table(model: Pipeline, top_n: int = 10) -> pd.DataFrame:
    """Extract feature importances from a fitted tree-based pipeline."""
    classifier = model.named_steps.get("classifier")
    preprocessor = model.named_steps.get("preprocessor")

    if classifier is None or not hasattr(classifier, "feature_importances_"):
        raise ValueError("The model classifier does not expose feature importances.")
    if preprocessor is None or not hasattr(preprocessor, "get_feature_names_out"):
        raise ValueError("The model preprocessor does not expose feature names.")

    feature_names = [
        _clean_feature_name(name) for name in preprocessor.get_feature_names_out()
    ]
    importances = classifier.feature_importances_

    table = pd.DataFrame(
        {
            "feature": feature_names,
            "importance": importances,
        }
    ).sort_values("importance", ascending=False)

    return table.head(top_n).reset_index(drop=True)


def _clean_feature_name(name: str) -> str:
    return name.replace("numeric__", "").replace("categorical__", "")

