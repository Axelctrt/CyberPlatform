from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from cyberplatform.ingestion import load_records, normalize_records
from cyberplatform.schema import Priority, SourceType
from cyberplatform.scoring import (
    alert_records,
    compute_risk_score,
    enrich_event_with_score,
    enrich_events_with_scores,
    export_alerts_csv,
    priority_distribution,
)


class RiskScoringTest(unittest.TestCase):
    def test_risk_score_is_bounded(self):
        score = compute_risk_score(1.5, 8, SourceType.AUTHENTICATION)
        self.assertTrue(0 <= score <= 100)

    def test_benign_prediction_has_no_risk_or_priority(self):
        event = normalize_records(load_records("data/samples/auth_events.csv"))[1]
        enriched = enrich_event_with_score(event, attack_probability=0.10)
        self.assertEqual(enriched.prediction, 0)
        self.assertIsNone(enriched.risk_score)
        self.assertIsNone(enriched.priority)

    def test_attack_receives_score_and_priority(self):
        event = normalize_records(load_records("data/samples/auth_events.csv"))[0]
        enriched = enrich_event_with_score(event, attack_probability=0.95, attack_type="Generic")
        self.assertEqual(enriched.prediction, 1)
        self.assertIsNotNone(enriched.risk_score)
        self.assertIn(enriched.priority, set(Priority))
        self.assertEqual(enriched.attack_type, "Generic")

    def test_only_detected_attacks_are_exported_and_counted(self):
        events = normalize_records(load_records("data/samples/auth_events.csv"))
        enriched = enrich_events_with_scores(events, [0.90, 0.10])
        records = alert_records(enriched)
        self.assertEqual(len(records), 1)
        self.assertEqual(sum(priority_distribution(enriched).values()), 1)
        with TemporaryDirectory() as tmpdir:
            path = export_alerts_csv(records, Path(tmpdir) / "alerts.csv")
            content = path.read_text(encoding="utf-8")
        for column in ("timestamp", "source_type", "prediction", "risk_score", "priority"):
            self.assertIn(column, content.splitlines()[0])


if __name__ == "__main__":
    unittest.main()
