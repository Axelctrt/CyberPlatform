"""Simplified and explicitly indicative MITRE ATT&CK context mapping."""

from __future__ import annotations

from dataclasses import dataclass

from cyberplatform.schema import SecurityEvent


@dataclass(frozen=True, slots=True)
class MitreTechnique:
    tactic: str | None
    technique_id: str | None
    technique_name: str
    confidence: str
    mapping_basis: str


UNMAPPED_TECHNIQUE = MitreTechnique(
    tactic=None,
    technique_id=None,
    technique_name="Non mappé",
    confidence="none",
    mapping_basis="none",
)

ATTACK_TYPE_MAPPING = {
    "reconnaissance": MitreTechnique(
        "Discovery", "T1046", "Network Service Discovery", "medium", "attack_type"
    ),
    "dos": MitreTechnique(
        "Impact", "T1498", "Network Denial of Service", "medium", "attack_type"
    ),
    "exploits": MitreTechnique(
        "Initial Access", "T1190", "Exploit Public-Facing Application", "low", "attack_type"
    ),
}

SURICATA_CATEGORY_MAPPING = {
    "attempted information leak": MitreTechnique(
        "Collection", "T1005", "Data from Local System", "low", "suricata_category"
    ),
    "attempted administrator privilege gain": MitreTechnique(
        "Privilege Escalation", "T1068", "Exploitation for Privilege Escalation", "low", "suricata_category"
    ),
}

EVENT_TYPE_MAPPING = {
    "login_failed": MitreTechnique(
        "Credential Access", "T1110", "Brute Force", "medium", "event_type"
    ),
    "network_flow": MitreTechnique(
        "Discovery", "T1046", "Network Service Discovery", "low", "event_type"
    ),
    "http_error": MitreTechnique(
        "Initial Access", "T1190", "Exploit Public-Facing Application", "low", "event_type"
    ),
    "suricata_alert": MitreTechnique(
        "Reconnaissance", "T1595", "Active Scanning", "low", "event_type"
    ),
}


def is_suspicious_for_mapping(event: SecurityEvent) -> bool:
    """Map only detected attacks or native Suricata IDS alerts."""
    return event.prediction == 1 or event.event_type == "suricata_alert"


def map_event_to_mitre(event: SecurityEvent) -> MitreTechnique:
    if not is_suspicious_for_mapping(event):
        return UNMAPPED_TECHNIQUE

    if isinstance(event.attack_type, str):
        mapped = ATTACK_TYPE_MAPPING.get(event.attack_type.strip().lower())
        if mapped is not None:
            return mapped

    category = event.features.get("suricata_category") if event.features else None
    if isinstance(category, str):
        mapped = SURICATA_CATEGORY_MAPPING.get(category.strip().lower())
        if mapped is not None:
            return mapped

    return EVENT_TYPE_MAPPING.get(event.event_type, UNMAPPED_TECHNIQUE)


def map_events_to_mitre_records(events: list[SecurityEvent]) -> list[dict[str, object]]:
    """Return one transparent mapping record per event for dashboard display."""
    records: list[dict[str, object]] = []
    for event in events:
        technique = map_event_to_mitre(event)
        records.append(
            {
                "timestamp": event.timestamp.isoformat(),
                "source_type": event.source_type.value,
                "event_type": event.event_type,
                "prediction": event.prediction,
                "priority": event.priority.value if event.priority else None,
                "tactic": technique.tactic,
                "technique_id": technique.technique_id,
                "technique_name": technique.technique_name,
                "confidence": technique.confidence,
                "mapping_basis": technique.mapping_basis,
                "mapping_note": "Simplifié et indicatif",
            }
        )
    return records
