"""Pure data preparation helpers used by the Streamlit interface."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO, StringIO
import json
from pathlib import Path
from typing import Any

import pandas as pd

from cyberplatform.ingestion import normalize_eve_records, normalize_records
from cyberplatform.ml import load_model, predict_unsw_dataframe
from cyberplatform.scoring import alert_records, enrich_events_with_scores
from cyberplatform.schema import Priority, SecurityEvent, SourceType
from cyberplatform.threat_intel import map_events_to_mitre_records


@dataclass(frozen=True, slots=True)
class DashboardData:
    events: list[SecurityEvent]
    event_table: pd.DataFrame
    alert_table: pd.DataFrame
    mitre_table: pd.DataFrame


def events_to_display_table(events: list[SecurityEvent]) -> pd.DataFrame:
    """Serialize normalized events without hiding that some fields can be non-applicable."""
    table = pd.DataFrame([event.to_record() for event in events])
    if table.empty:
        return table
    visible_columns = [
        "timestamp",
        "source_type",
        "event_type",
        "severity",
        "prediction",
        "confidence",
        "risk_score",
        "priority",
        "attack_type",
        "source_ip",
        "destination_ip",
        "username",
        "raw_message",
    ]
    return table[[column for column in visible_columns if column in table.columns]]


def build_dashboard_data(events: list[SecurityEvent]) -> DashboardData:
    return DashboardData(
        events=events,
        event_table=events_to_display_table(events),
        alert_table=pd.DataFrame(alert_records(events)),
        mitre_table=pd.DataFrame(map_events_to_mitre_records(events)),
    )


def load_demo_events() -> list[SecurityEvent]:
    """Load multi-source samples for UI demonstration without any ML training."""
    from cyberplatform.ingestion import load_records

    events: list[SecurityEvent] = []
    for source in ("data/samples/mixed_events.json", "data/samples/auth_events.csv"):
        path = Path(source)
        if path.exists():
            events.extend(normalize_records(load_records(path)))
    return events


def load_metrics_report(path: str | Path = "reports/model_metrics.json") -> dict[str, Any] | None:
    source = Path(path)
    if not source.exists():
        return None
    return json.loads(source.read_text(encoding="utf-8"))


def metrics_report_to_table(report: dict[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for label, key in (
        ("Logistic Regression", "baseline_metrics"),
        ("Random Forest", "primary_metrics"),
    ):
        metrics = report.get(key, {})
        rows.append(
            {
                "model": label,
                "accuracy": metrics.get("accuracy"),
                "precision": metrics.get("precision"),
                "recall": metrics.get("recall"),
                "f1_score": metrics.get("f1_score"),
                "fpr": metrics.get("fpr"),
                "fnr": metrics.get("fnr"),
                "roc_auc": metrics.get("roc_auc"),
                "pr_auc": metrics.get("pr_auc"),
            }
        )
    return pd.DataFrame(rows)


def confusion_matrix_table(metrics: dict[str, Any]) -> pd.DataFrame:
    matrix = metrics.get("confusion_matrix") or [[0, 0], [0, 0]]
    return pd.DataFrame(
        matrix,
        index=["Actual Normal", "Actual Attack"],
        columns=["Pred Normal", "Pred Attack"],
    )


def priority_counts(alert_table: pd.DataFrame) -> pd.DataFrame:
    """Count priorities among actual detected alerts only."""
    if alert_table.empty or "priority" not in alert_table.columns:
        return pd.DataFrame({"priority": [], "count": []})
    ordered = [priority.value for priority in Priority]
    counts = alert_table["priority"].dropna().value_counts().reindex(ordered, fill_value=0)
    return counts.rename_axis("priority").reset_index(name="count")


def source_counts(event_table: pd.DataFrame) -> pd.DataFrame:
    if event_table.empty or "source_type" not in event_table.columns:
        return pd.DataFrame({"source_type": [], "count": []})
    return (
        event_table["source_type"]
        .value_counts()
        .rename_axis("source_type")
        .reset_index(name="count")
    )


def parse_uploaded_records(payload: bytes, filename: str) -> list[dict[str, Any]]:
    suffix = Path(filename).suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(BytesIO(payload)).to_dict(orient="records")
    if suffix == ".json":
        parsed = json.loads(payload.decode("utf-8"))
        if isinstance(parsed, dict):
            return [parsed]
        if isinstance(parsed, list) and all(isinstance(item, dict) for item in parsed):
            return parsed
        raise ValueError("JSON input must contain an object or a list of objects.")
    raise ValueError("Generic import supports CSV or JSON files.")


def parse_suricata_bytes(payload: bytes) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(StringIO(payload.decode("utf-8")), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid EVE JSON line {line_number}") from error
        if not isinstance(record, dict):
            raise ValueError(f"EVE JSON line {line_number} must contain an object")
        records.append(record)
    return records


def analyze_unsw_dataframe(model_path: str | Path, dataframe: pd.DataFrame) -> DashboardData:
    """Analyze UNSW-compatible rows with a saved binary model; never infer attack families."""
    model = load_model(model_path)
    normalized_input = dataframe.copy()
    normalized_input.columns = [str(column).strip().lower() for column in normalized_input.columns]
    analyzed = predict_unsw_dataframe(model, normalized_input)
    events: list[SecurityEvent] = []

    for _, row in analyzed.iterrows():
        known_category = row.get("attack_cat")
        known_category = (
            str(known_category).strip()
            if pd.notna(known_category) and str(known_category).strip()
            else None
        )
        features = {
            key: value
            for key, value in row.to_dict().items()
            if key not in {"prediction", "attack_probability", "label", "attack_cat"}
        }
        if known_category is not None:
            # This is ground-truth/context supplied by the input, not a multi-class prediction.
            features["known_attack_category"] = known_category

        events.append(
            SecurityEvent(
                timestamp=datetime.now(timezone.utc),
                source_type=SourceType.NETWORK,
                event_type="network_flow",
                raw_message="UNSW-NB15 compatible network flow",
                severity=3,
                features=features,
            )
        )

    probabilities = analyzed["attack_probability"].tolist()
    enriched = enrich_events_with_scores(events, probabilities)
    return build_dashboard_data(enriched)


def normalize_generic_upload(payload: bytes, filename: str) -> DashboardData:
    return build_dashboard_data(normalize_records(parse_uploaded_records(payload, filename)))


def normalize_suricata_upload(payload: bytes) -> DashboardData:
    return build_dashboard_data(normalize_eve_records(parse_suricata_bytes(payload)))
