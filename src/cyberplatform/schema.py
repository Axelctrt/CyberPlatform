"""Common security event schema used across the prototype."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class SourceType(str, Enum):
    NETWORK = "network"
    SYSTEM = "system"
    AUTHENTICATION = "authentication"
    CLOUD = "cloud"
    APPLICATION = "application"


class Priority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


@dataclass(slots=True)
class SecurityEvent:
    timestamp: datetime
    source_type: SourceType
    event_type: str
    raw_message: str
    source_ip: str | None = None
    destination_ip: str | None = None
    username: str | None = None
    severity: int = 1
    features: dict[str, Any] = field(default_factory=dict)
    prediction: int | None = None
    attack_type: str | None = None
    risk_score: float | None = None
    priority: Priority | None = None

    def to_record(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "source_type": self.source_type.value,
            "source_ip": self.source_ip,
            "destination_ip": self.destination_ip,
            "username": self.username,
            "event_type": self.event_type,
            "severity": self.severity,
            "raw_message": self.raw_message,
            "features": self.features,
            "prediction": self.prediction,
            "attack_type": self.attack_type,
            "risk_score": self.risk_score,
            "priority": self.priority.value if self.priority else None,
        }


def priority_from_score(score: float) -> Priority:
    if not 0 <= score <= 100:
        raise ValueError("Risk score must be between 0 and 100.")

    if score >= 85:
        return Priority.CRITICAL
    if score >= 65:
        return Priority.HIGH
    if score >= 35:
        return Priority.MEDIUM
    return Priority.LOW


def validate_security_event(event: SecurityEvent) -> None:
    if not event.event_type:
        raise ValueError("event_type is required.")
    if not event.raw_message:
        raise ValueError("raw_message is required.")
    if not 1 <= event.severity <= 5:
        raise ValueError("severity must be between 1 and 5.")
