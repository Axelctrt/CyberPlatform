"""Risk scoring and alert enrichment rules."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from cyberplatform.schema import Priority, SecurityEvent, SourceType, priority_from_score


SOURCE_CRITICALITY = {
    SourceType.NETWORK: 0.55,
    SourceType.SYSTEM: 0.60,
    SourceType.AUTHENTICATION: 0.80,
    SourceType.CLOUD: 0.75,
    SourceType.APPLICATION: 0.50,
}


def compute_risk_score(
    attack_probability: float,
    severity: int,
    source_type: SourceType,
) -> float:
    """Compute a documented prototype score from confidence, severity and source context."""
    bounded_probability = min(max(float(attack_probability), 0.0), 1.0)
    bounded_severity = min(max(int(severity), 1), 5)
    source_criticality = SOURCE_CRITICALITY.get(source_type, 0.50)
    score = (
        bounded_probability * 60
        + ((bounded_severity - 1) / 4) * 25
        + source_criticality * 15
    )
    return round(min(max(score, 0.0), 100.0), 2)


def enrich_event_with_score(
    event: SecurityEvent,
    attack_probability: float,
    threshold: float = 0.5,
    attack_type: str | None = None,
) -> SecurityEvent:
    """Attach ML confidence and only prioritize events actually detected as attacks."""
    event.confidence = min(max(float(attack_probability), 0.0), 1.0)
    event.prediction = int(event.confidence >= threshold)
    if event.prediction == 0:
        event.attack_type = None
        event.risk_score = None
        event.priority = None
        return event

    event.attack_type = attack_type
    event.risk_score = compute_risk_score(
        attack_probability=event.confidence,
        severity=event.severity,
        source_type=event.source_type,
    )
    event.priority = priority_from_score(event.risk_score)
    return event


def enrich_events_with_scores(
    events: Iterable[SecurityEvent],
    attack_probabilities: Iterable[float],
    threshold: float = 0.5,
    attack_types: Iterable[str | None] | None = None,
) -> list[SecurityEvent]:
    events_list = list(events)
    probabilities_list = list(attack_probabilities)
    if len(events_list) != len(probabilities_list):
        raise ValueError("events and attack_probabilities must have the same length")
    types = list(attack_types) if attack_types is not None else [None] * len(events_list)
    if len(types) != len(events_list):
        raise ValueError("attack_types must have the same length as events")
    return [
        enrich_event_with_score(event, probability, threshold=threshold, attack_type=attack_type)
        for event, probability, attack_type in zip(events_list, probabilities_list, types, strict=True)
    ]


def alert_records(events: Iterable[SecurityEvent]) -> list[dict[str, object]]:
    return [event.to_record() for event in events if event.prediction == 1]


def export_alerts_csv(records: list[dict[str, object]], path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "timestamp",
        "source_type",
        "source_ip",
        "destination_ip",
        "username",
        "event_type",
        "prediction",
        "attack_type",
        "confidence",
        "risk_score",
        "priority",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
    return output_path


def priority_distribution(events: Iterable[SecurityEvent]) -> dict[Priority, int]:
    """Count priorities among detected alerts only."""
    distribution = {priority: 0 for priority in Priority}
    for event in events:
        if event.prediction == 1 and event.priority is not None:
            distribution[event.priority] += 1
    return distribution
