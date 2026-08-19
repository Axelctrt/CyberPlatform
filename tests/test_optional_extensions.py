import unittest

from cyberplatform.ingestion import load_eve_json_records, load_records, normalize_eve_records, normalize_records
from cyberplatform.schema import SourceType
from cyberplatform.threat_intel import map_event_to_mitre


class OptionalExtensionsTest(unittest.TestCase):
    def test_benign_or_unscored_generic_event_is_not_mapped(self):
        event = normalize_records(load_records("data/samples/auth_events.csv"))[1]
        technique = map_event_to_mitre(event)
        self.assertIsNone(technique.technique_id)
        self.assertEqual(technique.technique_name, "Non mappé")

    def test_detected_suspicious_event_can_be_mapped(self):
        event = normalize_records(load_records("data/samples/auth_events.csv"))[0]
        event.prediction = 1
        technique = map_event_to_mitre(event)
        self.assertEqual(technique.technique_id, "T1110")

    def test_unknown_suspicious_event_has_clean_fallback(self):
        event = normalize_records(load_records("data/samples/mixed_events.json"))[0]
        event.prediction = 1
        technique = map_event_to_mitre(event)
        self.assertIsNone(technique.technique_id)

    def test_suricata_alert_can_use_native_ids_context(self):
        events = normalize_eve_records(load_eve_json_records("data/samples/suricata_eve_sample.jsonl"))
        alert = next(event for event in events if event.event_type == "suricata_alert")
        technique = map_event_to_mitre(alert)
        self.assertIsNotNone(technique.technique_id)


if __name__ == "__main__":
    unittest.main()
