from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from cyberplatform.ingestion import load_records, normalize_records
from cyberplatform.ml import (
    compare_baseline_and_primary,
    create_train_test_split,
    events_to_dataframe,
    load_model,
    predict_attack_probabilities,
    save_model,
    split_features_target,
    train_primary_classifier,
)
from cyberplatform.scoring import alert_records, enrich_events_with_scores


class ModelPrioritizationTest(unittest.TestCase):
    def _training_data(self):
        records = load_records("data/samples/training_events.csv")
        events = normalize_records(records)
        dataframe = events_to_dataframe(events)
        features, target = split_features_target(dataframe)
        return events, features, target

    def test_primary_model_can_predict_attack_probabilities(self):
        _, features, target = self._training_data()
        model = train_primary_classifier(features, target)
        probabilities = predict_attack_probabilities(model, features)

        self.assertEqual(len(probabilities), len(features))
        self.assertTrue(all(0 <= probability <= 1 for probability in probabilities))

    def test_baseline_and_primary_can_be_compared(self):
        _, features, target = self._training_data()
        train_features, test_features, train_target, test_target = create_train_test_split(
            features,
            target,
        )

        comparison = compare_baseline_and_primary(
            train_features,
            test_features,
            train_target,
            test_target,
        )

        self.assertIn(comparison.recommended_model, {"baseline", "primary"})

    def test_model_can_be_saved_loaded_and_used_for_alerts(self):
        events, features, target = self._training_data()
        model = train_primary_classifier(features, target)

        with TemporaryDirectory() as tmpdir:
            model_path = save_model(model, Path(tmpdir) / "primary_model.joblib")
            loaded_model = load_model(model_path)

        probabilities = predict_attack_probabilities(loaded_model, features)
        enriched_events = enrich_events_with_scores(events, probabilities)
        records = alert_records(enriched_events)

        self.assertGreaterEqual(len(records), 1)


if __name__ == "__main__":
    unittest.main()

