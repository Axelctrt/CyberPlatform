"""Data ingestion connectors."""

from cyberplatform.ingestion.loaders import (
    RawRecord,
    load_csv_records,
    load_json_records,
    load_records,
)
from cyberplatform.ingestion.normalization import normalize_record, normalize_records
from cyberplatform.ingestion.suricata import (
    load_eve_json_records,
    normalize_eve_record,
    normalize_eve_records,
)

__all__ = [
    "RawRecord",
    "load_eve_json_records",
    "load_csv_records",
    "load_json_records",
    "load_records",
    "normalize_eve_record",
    "normalize_eve_records",
    "normalize_record",
    "normalize_records",
]
