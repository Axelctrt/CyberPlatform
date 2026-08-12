"""Small MITRE ATT&CK mapping for the prototype alerts."""

from __future__ import annotations

from dataclasses import dataclass

from cyberplatform.schema import SecurityEvent


@dataclass(frozen=True, slots=True)
class MitreTechnique:
    tactic: str
    technique_id: str
    technique_name: str
    confidence: str


DEFAULT_TECHNIQUE = MitreTechnique(
    tactic="Detection",
    technique_id="T0000",
    technique_name="Unmapped suspicious activity",
    confidence="low",
)


EVENT_TYPE_MAPPING = {
    "login_failed": MitreTechnique(
        tactic="Credential Access",
        technique_id="T1110",
        technique_name="Brute Force",
        confidence="medium",
    ),
    "api_call": MitreTechnique(
        tactic="Discovery",
        technique_id="T1526",
        technique_name="Cloud Service Dashboard",
        confidence="low",
    ),
    "network_flow": MitreTechnique(
        tactic="Discovery",
        technique_id="T1046",
        technique_name="Network Service Discovery",
        confidence="low",
    ),
    "http_error": MitreTechnique(
        tactic="Initial Access",
        technique_id="T1190",
        technique_name="Exploit Public-Facing Application",
        confidence="low",
    ),
    "suricata_alert": MitreTechnique(
        tactic="Reconnaissance",
        technique_id="T1595",
        technique_name="Active Scanning",
        confidence="medium",
    ),
}


CATEGORY_MAPPING = {
    "attempted information leak": MitreTechnique(
        tactic="Collection",
        technique_id="T1005",
        technique_name="Data from Local System",
        confidence="low",
    ),
    "attempted administrator privilege gain": MitreTechnique(
        tactic="Privilege Escalation",
        technique_id="T1068",
        technique_name="Exploitation for Privilege Escalation",
        confidence="low",
    ),
}


def map_event_to_mitre(event: SecurityEvent) -> MitreTechnique:
    """Map one event to a simplified MITRE ATT&CK technique."""
    category = event.features.get("suricata_category") if event.features else None
    if isinstance(category, str):
        mapped_category = CATEGORY_MAPPING.get(category.lower())
        if mapped_category is not None:
            return mapped_category

    return EVENT_TYPE_MAPPING.get(event.event_type, DEFAULT_TECHNIQUE)


def map_events_to_mitre_records(events: list[SecurityEvent]) -> list[dict[str, str]]:
    """Return MITRE records ready for a dashboard table."""
    records: list[dict[str, str]] = []

    for event in events:
        technique = map_event_to_mitre(event)
        records.append(
            {
                "timestamp": event.timestamp.isoformat(),
                "source_type": event.source_type.value,
                "event_type": event.event_type,
                "priority": event.priority.value if event.priority else "",
                "tactic": technique.tactic,
                "technique_id": technique.technique_id,
                "technique_name": technique.technique_name,
                "confidence": technique.confidence,
            }
        )

    return records

