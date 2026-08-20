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
from cyberplatform.ml import (
    expected_model_columns,
    load_model,
    predict_attack_families,
    predict_unsw_dataframe,
    prepare_inference_features,
)
from cyberplatform.scoring import enrich_events_with_scores
from cyberplatform.schema import Priority, SecurityEvent, SourceType
from cyberplatform.threat_intel import map_events_to_mitre_records


@dataclass(frozen=True, slots=True)
class DashboardData:
    events: list[SecurityEvent]
    event_table: pd.DataFrame
    alert_table: pd.DataFrame
    mitre_table: pd.DataFrame


def _known_attack_category(event: SecurityEvent) -> str | None:
    """Return dataset-provided attack context without presenting it as a model prediction."""
    value = event.features.get("known_attack_category")
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _attack_family_confidence(event: SecurityEvent) -> float | None:
    value = event.features.get("attack_family_confidence")
    if value is None:
        return None
    return float(value)


def _event_record_with_context(event: SecurityEvent) -> dict[str, Any]:
    record = event.to_record()
    record["known_attack_category"] = _known_attack_category(event)
    record["attack_family_confidence"] = _attack_family_confidence(event)
    return record


def events_to_display_table(events: list[SecurityEvent]) -> pd.DataFrame:
    """Serialize normalized events and expose dataset truth/context when available."""
    table = pd.DataFrame([_event_record_with_context(event) for event in events])
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
        "known_attack_category",
        "attack_type",
        "attack_family_confidence",
        "source_ip",
        "destination_ip",
        "username",
        "raw_message",
    ]
    return table[[column for column in visible_columns if column in table.columns]]


def events_to_alert_table(events: list[SecurityEvent]) -> pd.DataFrame:
    """Serialize detected alerts with optional predicted attack-family enrichment."""
    return pd.DataFrame(
        [_event_record_with_context(event) for event in events if event.prediction == 1]
    )


def build_dashboard_data(events: list[SecurityEvent]) -> DashboardData:
    return DashboardData(
        events=events,
        event_table=events_to_display_table(events),
        alert_table=events_to_alert_table(events),
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


def multiclass_confusion_matrix_table(experiment: dict[str, Any]) -> pd.DataFrame:
    """Return the attack-family confusion matrix stored in the scientific report."""
    metrics = experiment.get("metrics", {})
    labels = [str(label) for label in metrics.get("labels", [])]
    matrix = metrics.get("confusion_matrix", [])
    if not labels or not matrix:
        return pd.DataFrame()
    return pd.DataFrame(matrix, index=labels, columns=labels)


def multiclass_per_class_table(experiment: dict[str, Any]) -> pd.DataFrame:
    """Return per-family metrics in a dashboard-friendly table."""
    per_class = experiment.get("metrics", {}).get("per_class", {})
    rows = [
        {
            "family": family,
            "precision": values.get("precision"),
            "recall": values.get("recall"),
            "f1_score": values.get("f1_score"),
            "support": values.get("support"),
        }
        for family, values in per_class.items()
    ]
    return pd.DataFrame(rows)


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


def known_category_counts(event_table: pd.DataFrame) -> pd.DataFrame:
    """Count UNSW categories supplied by the input dataset, never model-inferred families."""
    if event_table.empty or "known_attack_category" not in event_table.columns:
        return pd.DataFrame({"known_attack_category": [], "count": []})
    values = event_table["known_attack_category"].dropna()
    if values.empty:
        return pd.DataFrame({"known_attack_category": [], "count": []})
    return (
        values.value_counts()
        .rename_axis("known_attack_category")
        .reset_index(name="count")
    )


def category_detection_performance(event_table: pd.DataFrame) -> pd.DataFrame:
    """Describe binary decisions by known UNSW attack category for error analysis."""
    required = {"known_attack_category", "prediction"}
    if event_table.empty or not required.issubset(event_table.columns):
        return pd.DataFrame()
    frame = event_table.dropna(subset=["known_attack_category", "prediction"]).copy()
    if frame.empty:
        return pd.DataFrame()
    frame["prediction"] = frame["prediction"].astype(int)
    rows: list[dict[str, Any]] = []
    for category, group in frame.groupby("known_attack_category", sort=True):
        detected = int(group["prediction"].eq(1).sum())
        not_detected = int(group["prediction"].eq(0).sum())
        total = int(len(group))
        is_normal = str(category).strip().casefold() == "normal"
        rows.append(
            {
                "category": str(category),
                "events": total,
                "attack_detected": detected,
                "no_attack_detected": not_detected,
                "attack_detection_rate": None if is_normal else detected / total,
                "false_positive_rate": detected / total if is_normal else None,
            }
        )
    return pd.DataFrame(rows)


def validate_unsw_dataframe(model_path: str | Path, dataframe: pd.DataFrame) -> dict[str, Any]:
    """Preview schema compatibility before a user launches UNSW inference."""
    model = load_model(model_path)
    frame = dataframe.copy()
    frame.columns = [str(column).strip().lower() for column in frame.columns]
    required = expected_model_columns(model)
    available = set(frame.columns)
    recognized = [column for column in required if column in available]
    missing = [column for column in required if column not in available]
    extra = [column for column in frame.columns if column not in required]
    return {
        "compatible": not missing and len(frame) > 0,
        "rows": int(len(frame)),
        "required_columns": int(len(required)),
        "recognized_columns": int(len(recognized)),
        "missing_columns": missing,
        "extra_columns": extra,
        "has_label": "label" in available,
        "has_attack_cat": "attack_cat" in available,
    }


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


def analyze_unsw_dataframe(
    model_path: str | Path,
    dataframe: pd.DataFrame,
    *,
    threshold: float = 0.5,
    attack_family_model_path: str | Path | None = None,
) -> DashboardData:
    """Analyze UNSW rows with binary detection and optional conditional family enrichment."""
    model = load_model(model_path)
    normalized_input = dataframe.copy()
    normalized_input.columns = [str(column).strip().lower() for column in normalized_input.columns]
    analyzed = predict_unsw_dataframe(model, normalized_input, threshold=threshold)

    attack_types: list[str | None] = [None] * len(analyzed)
    family_confidences: list[float | None] = [None] * len(analyzed)
    family_path = Path(attack_family_model_path) if attack_family_model_path is not None else None
    detected_positions = [position for position, value in enumerate(analyzed["prediction"].tolist()) if int(value) == 1]
    if family_path is not None and family_path.exists() and detected_positions:
        family_model = load_model(family_path)
        detected_rows = analyzed.iloc[detected_positions]
        family_features = prepare_inference_features(detected_rows, family_model)
        predicted_families, predicted_confidences = predict_attack_families(family_model, family_features)
        for position, family, family_confidence in zip(
            detected_positions,
            predicted_families,
            predicted_confidences,
            strict=True,
        ):
            attack_types[position] = family
            family_confidences[position] = family_confidence

    events: list[SecurityEvent] = []
    for position, (_, row) in enumerate(analyzed.iterrows()):
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
            features["known_attack_category"] = known_category
        if family_confidences[position] is not None:
            features["attack_family_confidence"] = family_confidences[position]

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
    enriched = enrich_events_with_scores(
        events,
        probabilities,
        threshold=threshold,
        attack_types=attack_types,
    )
    return build_dashboard_data(enriched)


def normalize_generic_upload(payload: bytes, filename: str) -> DashboardData:
    return build_dashboard_data(normalize_records(parse_uploaded_records(payload, filename)))


def normalize_suricata_upload(payload: bytes) -> DashboardData:
    return build_dashboard_data(normalize_eve_records(parse_suricata_bytes(payload)))
