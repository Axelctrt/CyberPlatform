"""File loaders for the first ingestion sprint."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


RawRecord = dict[str, Any]


def load_json_records(path: str | Path) -> list[RawRecord]:
    """Load a JSON file containing one record or a list of records."""
    source_path = Path(path)
    with source_path.open(encoding="utf-8") as file:
        payload = json.load(file)

    if isinstance(payload, dict):
        return [payload]
    if isinstance(payload, list) and all(isinstance(item, dict) for item in payload):
        return payload

    raise ValueError("JSON input must contain an object or a list of objects.")


def load_csv_records(path: str | Path) -> list[RawRecord]:
    """Load a CSV file as a list of dictionaries."""
    source_path = Path(path)
    with source_path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def load_records(path: str | Path) -> list[RawRecord]:
    """Load records from a supported source file."""
    source_path = Path(path)
    suffix = source_path.suffix.lower()

    if suffix == ".json":
        return load_json_records(source_path)
    if suffix == ".csv":
        return load_csv_records(source_path)

    raise ValueError(f"Unsupported source format: {suffix}")

