"""UNSW-NB15 loading, cleaning and reproducible train/test preparation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

LABEL_COLUMN = "label"
ATTACK_CATEGORY_COLUMN = "attack_cat"
NON_FEATURE_COLUMNS = {"id", LABEL_COLUMN, ATTACK_CATEGORY_COLUMN}
OFFICIAL_TRAIN_FILENAMES = (
    "UNSW_NB15_training-set.csv",
    "UNSW_NB15_training_set.csv",
)
OFFICIAL_TEST_FILENAMES = (
    "UNSW_NB15_testing-set.csv",
    "UNSW_NB15_testing_set.csv",
)


@dataclass(frozen=True, slots=True)
class UNSWNB15Split:
    train_features: pd.DataFrame
    test_features: pd.DataFrame
    train_target: pd.Series
    test_target: pd.Series
    train_attack_categories: pd.Series
    test_attack_categories: pd.Series
    feature_columns: tuple[str, ...]
    split_strategy: str


def load_unsw_nb15_file(path: str | Path, *, max_rows: int | None = None) -> pd.DataFrame:
    """Load a headered UNSW-NB15 CSV and apply defensive cleaning."""
    source_path = Path(path)
    if not source_path.exists():
        raise FileNotFoundError(source_path)
    frame = pd.read_csv(source_path, nrows=max_rows, low_memory=False)
    return clean_unsw_nb15_dataframe(frame)


def clean_unsw_nb15_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    frame = dataframe.copy()
    frame.columns = [str(column).strip().lower() for column in frame.columns]
    if LABEL_COLUMN not in frame.columns:
        raise ValueError("UNSW-NB15 input must contain a 'label' column.")

    frame = frame.replace([np.inf, -np.inf], np.nan)
    frame[LABEL_COLUMN] = pd.to_numeric(frame[LABEL_COLUMN], errors="coerce")
    frame = frame[frame[LABEL_COLUMN].isin([0, 1])].copy()
    frame[LABEL_COLUMN] = frame[LABEL_COLUMN].astype(int)

    if ATTACK_CATEGORY_COLUMN not in frame.columns:
        frame[ATTACK_CATEGORY_COLUMN] = np.where(frame[LABEL_COLUMN].eq(0), "Normal", None)
    else:
        frame[ATTACK_CATEGORY_COLUMN] = frame[ATTACK_CATEGORY_COLUMN].map(
            lambda value: value.strip() if isinstance(value, str) else value
        )
        frame[ATTACK_CATEGORY_COLUMN] = frame[ATTACK_CATEGORY_COLUMN].replace(
            {"": np.nan, "nan": np.nan, "None": np.nan}
        )
        frame.loc[frame[LABEL_COLUMN].eq(0), ATTACK_CATEGORY_COLUMN] = "Normal"

    for column in frame.select_dtypes(include="object").columns:
        frame[column] = frame[column].map(
            lambda value: value.strip() if isinstance(value, str) else value
        )

    return frame.reset_index(drop=True)


def get_feature_columns(dataframe: pd.DataFrame) -> list[str]:
    """Return model features while explicitly excluding labels and identifiers."""
    return [column for column in dataframe.columns if column not in NON_FEATURE_COLUMNS]


def prepare_unsw_nb15_split(
    dataframe: pd.DataFrame,
    *,
    test_size: float = 0.2,
    random_state: int = 42,
) -> UNSWNB15Split:
    frame = clean_unsw_nb15_dataframe(dataframe)
    feature_columns = get_feature_columns(frame)
    features = frame[feature_columns]
    target = frame[LABEL_COLUMN]
    attack_categories = frame[ATTACK_CATEGORY_COLUMN]

    indices = np.arange(len(frame))
    train_idx, test_idx = train_test_split(
        indices,
        test_size=test_size,
        random_state=random_state,
        stratify=target,
    )
    return _split_from_indices(
        features,
        target,
        attack_categories,
        train_idx,
        test_idx,
        tuple(feature_columns),
        "stratified_random_split",
    )


def load_unsw_nb15_dataset(
    data_dir: str | Path,
    *,
    test_size: float = 0.2,
    random_state: int = 42,
    max_rows_per_file: int | None = None,
) -> UNSWNB15Split:
    """Load the common official train/test files, or split available headered CSV files."""
    directory = Path(data_dir)
    if not directory.exists():
        raise FileNotFoundError(directory)

    train_path = _first_existing(directory, OFFICIAL_TRAIN_FILENAMES)
    test_path = _first_existing(directory, OFFICIAL_TEST_FILENAMES)
    if train_path and test_path:
        train = load_unsw_nb15_file(train_path, max_rows=max_rows_per_file)
        test = load_unsw_nb15_file(test_path, max_rows=max_rows_per_file)
        common_features = [
            column
            for column in get_feature_columns(train)
            if column in test.columns and column not in NON_FEATURE_COLUMNS
        ]
        if not common_features:
            raise ValueError("No common UNSW-NB15 feature columns found between train and test files.")
        return UNSWNB15Split(
            train_features=train[common_features].copy(),
            test_features=test[common_features].copy(),
            train_target=train[LABEL_COLUMN].copy(),
            test_target=test[LABEL_COLUMN].copy(),
            train_attack_categories=train[ATTACK_CATEGORY_COLUMN].copy(),
            test_attack_categories=test[ATTACK_CATEGORY_COLUMN].copy(),
            feature_columns=tuple(common_features),
            split_strategy="official_train_test_files",
        )

    csv_files = sorted(directory.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(
            f"No UNSW-NB15 CSV file found in {directory}. Expected the official train/test CSV files."
        )
    frames = [load_unsw_nb15_file(path, max_rows=max_rows_per_file) for path in csv_files]
    combined = pd.concat(frames, ignore_index=True)
    return prepare_unsw_nb15_split(
        combined,
        test_size=test_size,
        random_state=random_state,
    )


def _first_existing(directory: Path, names: Iterable[str]) -> Path | None:
    for name in names:
        candidate = directory / name
        if candidate.exists():
            return candidate
    return None


def _split_from_indices(
    features: pd.DataFrame,
    target: pd.Series,
    attack_categories: pd.Series,
    train_idx: np.ndarray,
    test_idx: np.ndarray,
    feature_columns: tuple[str, ...],
    strategy: str,
) -> UNSWNB15Split:
    return UNSWNB15Split(
        train_features=features.iloc[train_idx].reset_index(drop=True),
        test_features=features.iloc[test_idx].reset_index(drop=True),
        train_target=target.iloc[train_idx].reset_index(drop=True),
        test_target=target.iloc[test_idx].reset_index(drop=True),
        train_attack_categories=attack_categories.iloc[train_idx].reset_index(drop=True),
        test_attack_categories=attack_categories.iloc[test_idx].reset_index(drop=True),
        feature_columns=feature_columns,
        split_strategy=strategy,
    )
