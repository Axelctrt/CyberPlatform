"""Suricata EVE JSON ingestion support."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cyberplatform.schema import SecurityEvent, SourceType, validate_security_event
from cyberplatform.ingestion.normalization import parse_severity, parse_timestamp


def load_eve_json_records(path: str | Path) -> list[dict[str, Any]]:
    """Load Suricata EVE JSON records from a JSON Lines file."""
    source_path = Path(path)
    records: list[dict[str, Any]] = []

    with source_path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            stripped_line = line.strip()
            if not stripped_line:
                continue
            try:
                records.append(json.loads(stripped_line))
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid EVE JSON line {line_number}") from error

    return records


def normalize_eve_record(record: dict[str, Any]) -> SecurityEvent:
    """Convert one Suricata EVE record to the common security event schema."""
    alert = record.get("alert") if isinstance(record.get("alert"), dict) else {}
    flow = record.get("flow") if isinstance(record.get("flow"), dict) else {}
    event_type = str(record.get("event_type", "suricata_event"))
    signature = str(alert.get("signature", event_type))

    event = SecurityEvent(
        timestamp=parse_timestamp(record.get("timestamp")),
        source_type=SourceType.NETWORK,
        source_ip=_string_or_none(record.get("src_ip")),
        destination_ip=_string_or_none(record.get("dest_ip")),
        event_type=f"suricata_{event_type}",
        severity=parse_severity(alert.get("severity", record.get("severity", 1))),
        raw_message=signature,
        attack_type=_string_or_none(alert.get("category")),
        features={
            "protocol": record.get("proto"),
            "source_port": record.get("src_port"),
            "destination_port": record.get("dest_port"),
            "suricata_category": alert.get("category"),
            "signature": alert.get("signature"),
            "bytes_toserver": flow.get("bytes_toserver"),
            "bytes_toclient": flow.get("bytes_toclient"),
        },
    )
    validate_security_event(event)
    return event


def normalize_eve_records(records: list[dict[str, Any]]) -> list[SecurityEvent]:
    """Normalize a batch of Suricata EVE records."""
    return [normalize_eve_record(record) for record in records]


def _string_or_none(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)

