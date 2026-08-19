from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from cyberplatform.datasets import load_unsw_nb15_file, prepare_unsw_nb15_split
from cyberplatform.ml import (
    compare_baseline_and_primary,
    evaluate_classifier,
    load_model,
    predict_attack_probabilities,
    save_model,
    train_baseline_classifier,
    train_primary_classifier,
)


class MLPipelineTest(unittest.TestCase):
    def setUp(self):
        frame = load_unsw_nb15_file("data/samples/unsw_nb15_sample.csv")
        self.split = prepare_unsw_nb15_split(frame, test_size=0.3, random_state=42)

    def test_baseline_classifier_trains_and_reports_cyber_metrics(self):
        model = train_baseline_classifier(self.split.train_features, self.split.train_target)
        metrics = evaluate_classifier(model, self.split.test_features, self.split.test_target)
        self.assertGreaterEqual(metrics.accuracy, 0.0)
        self.assertEqual(metrics.tn + metrics.fp + metrics.fn + metrics.tp, len(self.split.test_target))
        self.assertGreaterEqual(metrics.fpr, 0.0)
        self.assertGreaterEqual(metrics.fnr, 0.0)

    def test_random_forest_trains_and_predicts_probabilities(self):
        model = train_primary_classifier(self.split.train_features, self.split.train_target)
        probabilities = predict_attack_probabilities(model, self.split.test_features)
        self.assertEqual(len(probabilities), len(self.split.test_features))
        self.assertTrue(all(0 <= value <= 1 for value in probabilities))

    def test_models_are_compared_on_same_split(self):
        comparison = compare_baseline_and_primary(
            self.split.train_features,
            self.split.test_features,
            self.split.train_target,
            self.split.test_target,
        )
        self.assertIn(comparison.recommended_model, {"baseline", "primary"})

    def test_model_can_be_saved_reloaded_and_used(self):
        model = train_primary_classifier(self.split.train_features, self.split.train_target)
        with TemporaryDirectory() as tmpdir:
            path = save_model(model, Path(tmpdir) / "model.joblib")
            loaded = load_model(path)
            predictions = loaded.predict(self.split.test_features)
        self.assertEqual(len(predictions), len(self.split.test_features))


if __name__ == "__main__":
    unittest.main()
