"""Preprocessing helpers for the first Machine Learning sprint."""

from __future__ import annotations

from typing import Iterable

import pandas as pd
from sklearn.model_selection import train_test_split

from cyberplatform.schema import SecurityEvent


BASE_EVENT_COLUMNS = [
    "source_type",
    "event_type",
    "severity",
]


def events_to_dataframe(events: Iterable[SecurityEvent]) -> pd.DataFrame:
    """Convert normalized events to a flat tabular structure."""
    rows: list[dict[str, object]] = []

    for event in events:
        row: dict[str, object] = {
            "source_type": event.source_type.value,
            "event_type": event.event_type,
            "severity": event.severity,
        }
        row.update(event.features)
        rows.append(row)

    return pd.DataFrame(rows)


def split_features_target(
    dataframe: pd.DataFrame,
    target_column: str = "label",
) -> tuple[pd.DataFrame, pd.Series]:
    """Separate model features from the target label."""
    if target_column not in dataframe.columns:
        raise ValueError(f"Missing target column: {target_column}")

    features = dataframe.drop(columns=[target_column])
    target = dataframe[target_column].astype(int)
    return features, target


def create_train_test_split(
    features: pd.DataFrame,
    target: pd.Series,
    test_size: float = 0.3,
    random_state: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Create a reproducible train/test split for baseline evaluation."""
    return train_test_split(
        features,
        target,
        test_size=test_size,
        random_state=random_state,
        stratify=target,
    )


def infer_feature_types(dataframe: pd.DataFrame) -> tuple[list[str], list[str]]:
    """Infer numeric and categorical feature columns for a tabular model."""
    numeric_columns = dataframe.select_dtypes(include=["number", "bool"]).columns.tolist()
    categorical_columns = [
        column for column in dataframe.columns if column not in numeric_columns
    ]
    return numeric_columns, categorical_columns
