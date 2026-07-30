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
    """Compute a simple 0-100 risk score for a predicted alert."""
    bounded_probability = min(max(attack_probability, 0.0), 1.0)
    bounded_severity = min(max(severity, 1), 5)
    source_criticality = SOURCE_CRITICALITY.get(source_type, 0.50)

    score = (
        bounded_probability * 60
        + ((bounded_severity - 1) / 4) * 25
        + source_criticality * 15
    )
    return round(min(score, 100.0), 2)


def enrich_event_with_score(
    event: SecurityEvent,
    attack_probability: float,
    threshold: float = 0.5,
    attack_type: str | None = None,
) -> SecurityEvent:
    """Attach prediction, score and priority to an event."""
    event.prediction = int(attack_probability >= threshold)
    event.attack_type = attack_type if event.prediction else None
    event.risk_score = compute_risk_score(
        attack_probability=attack_probability,
        severity=event.severity,
        source_type=event.source_type,
    )
    event.priority = priority_from_score(event.risk_score)
    return event


def enrich_events_with_scores(
    events: Iterable[SecurityEvent],
    attack_probabilities: Iterable[float],
    threshold: float = 0.5,
) -> list[SecurityEvent]:
    """Score a batch of events using model attack probabilities."""
    return [
        enrich_event_with_score(event, probability, threshold=threshold)
        for event, probability in zip(events, attack_probabilities, strict=True)
    ]


def alert_records(events: Iterable[SecurityEvent]) -> list[dict[str, object]]:
    """Return serialized records for events predicted as attacks."""
    return [event.to_record() for event in events if event.prediction == 1]


def export_alerts_csv(records: list[dict[str, object]], path: str | Path) -> Path:
    """Export alert records to CSV for analyst review."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "timestamp",
        "source_type",
        "source_ip",
        "destination_ip",
        "username",
        "event_type",
        "severity",
        "raw_message",
        "prediction",
        "attack_type",
        "risk_score",
        "priority",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)

    return output_path


def priority_distribution(events: Iterable[SecurityEvent]) -> dict[Priority, int]:
    """Count scored events by priority level."""
    distribution = {priority: 0 for priority in Priority}
    for event in events:
        if event.priority is not None:
            distribution[event.priority] += 1
    return distribution

