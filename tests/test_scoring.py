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
    def test_risk_score_combines_probability_severity_and_source(self):
        score = compute_risk_score(
            attack_probability=0.9,
            severity=5,
            source_type=SourceType.AUTHENTICATION,
        )

        self.assertGreaterEqual(score, 85)

    def test_event_is_enriched_with_prediction_score_and_priority(self):
        event = normalize_records(load_records("data/samples/auth_events.csv"))[0]
        enriched = enrich_event_with_score(event, attack_probability=0.82)

        self.assertEqual(enriched.prediction, 1)
        self.assertIsNotNone(enriched.risk_score)
        self.assertIn(enriched.priority, {Priority.HIGH, Priority.CRITICAL})

    def test_alert_records_and_csv_export(self):
        events = normalize_records(load_records("data/samples/training_events.csv"))
        probabilities = [0.1, 0.2, 0.1, 0.15, 0.2, 0.8, 0.9, 0.75, 0.7, 0.85]
        enriched_events = enrich_events_with_scores(events, probabilities)
        records = alert_records(enriched_events)

        self.assertEqual(len(records), 5)

        with TemporaryDirectory() as tmpdir:
            output_path = export_alerts_csv(records, Path(tmpdir) / "alerts.csv")
            self.assertTrue(output_path.exists())
            self.assertIn("risk_score", output_path.read_text(encoding="utf-8"))

    def test_priority_distribution_counts_scored_events(self):
        events = normalize_records(load_records("data/samples/auth_events.csv"))
        enriched_events = enrich_events_with_scores(events, [0.85, 0.1])
        distribution = priority_distribution(enriched_events)

        self.assertEqual(sum(distribution.values()), 2)


if __name__ == "__main__":
    unittest.main()

