import unittest

from cyberplatform.ingestion import load_eve_json_records, normalize_eve_records
from cyberplatform.ml import (
    events_to_dataframe,
    feature_importance_table,
    split_features_target,
    train_primary_classifier,
)
from cyberplatform.ingestion import load_records, normalize_records
from cyberplatform.threat_intel import map_event_to_mitre, map_events_to_mitre_records


class OptionalExtensionsTest(unittest.TestCase):
    def test_suricata_eve_records_are_loaded_and_normalized(self):
        records = load_eve_json_records("data/samples/suricata_eve_sample.jsonl")
        events = normalize_eve_records(records)

        self.assertEqual(len(events), 3)
        self.assertEqual(events[0].event_type, "suricata_alert")
        self.assertEqual(events[0].features["destination_port"], 443)

    def test_mitre_mapping_adds_threat_context(self):
        records = load_eve_json_records("data/samples/suricata_eve_sample.jsonl")
        event = normalize_eve_records(records)[0]
        technique = map_event_to_mitre(event)

        self.assertNotEqual(technique.technique_id, "T0000")
        self.assertTrue(technique.tactic)

    def test_mitre_records_are_dashboard_ready(self):
        records = load_records("data/samples/training_events.csv")
        events = normalize_records(records)
        mitre_records = map_events_to_mitre_records(events)

        self.assertEqual(len(mitre_records), len(events))
        self.assertIn("technique_id", mitre_records[0])

    def test_primary_model_feature_importances_are_available(self):
        records = load_records("data/samples/training_events.csv")
        events = normalize_records(records)
        dataframe = events_to_dataframe(events)
        features, target = split_features_target(dataframe)
        model = train_primary_classifier(features, target)

        importances = feature_importance_table(model, top_n=5)

        self.assertLessEqual(len(importances), 5)
        self.assertIn("feature", importances.columns)
        self.assertIn("importance", importances.columns)


if __name__ == "__main__":
    unittest.main()

