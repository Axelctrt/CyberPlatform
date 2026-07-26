"""Normalize raw security records into the common event schema."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from cyberplatform.schema import SecurityEvent, SourceType, validate_security_event


KNOWN_SCHEMA_FIELDS = {
    "timestamp",
    "source_type",
    "source_ip",
    "destination_ip",
    "username",
    "event_type",
    "severity",
    "raw_message",
    "features",
    "prediction",
    "attack_type",
    "risk_score",
    "priority",
}


def parse_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if value in (None, ""):
        return datetime.now(timezone.utc)

    normalized = str(value).strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"

    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def parse_severity(value: Any) -> int:
    if value in (None, ""):
        return 1

    severity = int(value)
    if severity < 1:
        return 1
    if severity > 5:
        return 5
    return severity


def parse_features(record: dict[str, Any]) -> dict[str, Any]:
    features = record.get("features")
    if isinstance(features, dict):
        parsed_features = dict(features)
    elif isinstance(features, str) and features.strip():
        parsed_features = _parse_json_features(features)
    else:
        parsed_features = {}

    for key, value in record.items():
        if key not in KNOWN_SCHEMA_FIELDS and value not in (None, ""):
            parsed_features[key] = _coerce_scalar(value)

    return parsed_features


def normalize_record(record: dict[str, Any]) -> SecurityEvent:
    event = SecurityEvent(
        timestamp=parse_timestamp(record.get("timestamp")),
        source_type=SourceType(str(record.get("source_type", "application")).lower()),
        source_ip=_empty_to_none(record.get("source_ip")),
        destination_ip=_empty_to_none(record.get("destination_ip")),
        username=_empty_to_none(record.get("username")),
        event_type=str(record.get("event_type", "unknown_event")),
        severity=parse_severity(record.get("severity")),
        raw_message=str(record.get("raw_message") or record.get("message") or ""),
        features=parse_features(record),
    )
    validate_security_event(event)
    return event


def normalize_records(records: list[dict[str, Any]]) -> list[SecurityEvent]:
    return [normalize_record(record) for record in records]


def _empty_to_none(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def _parse_json_features(value: str) -> dict[str, Any]:
    try:
        parsed = __import__("json").loads(value)
    except ValueError:
        return {"raw_features": value}

    if isinstance(parsed, dict):
        return parsed
    return {"raw_features": parsed}


def _coerce_scalar(value: Any) -> Any:
    if not isinstance(value, str):
        return value

    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False

    try:
        return int(value)
    except ValueError:
        pass

    try:
        return float(value)
    except ValueError:
        return value

