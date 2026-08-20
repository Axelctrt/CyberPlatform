from pathlib import Path
import unittest

from cyberplatform.datasets import load_unsw_nb15_file
from cyberplatform.ml import (
    evaluate_attack_family_classifier,
    predict_attack_families,
    train_attack_family_classifier,
)


class MulticlassAttackFamilyTest(unittest.TestCase):
    def setUp(self):
        frame = load_unsw_nb15_file(Path("data/samples/unsw_nb15_sample.csv"))
        attack_rows = frame[frame["label"].eq(1)].reset_index(drop=True)
        self.features = attack_rows.drop(columns=["id", "label", "attack_cat"], errors="ignore")
        self.target = attack_rows["attack_cat"].astype(str)

    def test_attack_family_model_trains_predicts_and_reports_per_class_metrics(self):
        model = train_attack_family_classifier(self.features, self.target)
        predictions, confidence = predict_attack_families(model, self.features)
        metrics = evaluate_attack_family_classifier(model, self.features, self.target)

        self.assertEqual(len(predictions), len(self.features))
        self.assertEqual(len(confidence), len(self.features))
        self.assertTrue(all(0.0 <= value <= 1.0 for value in confidence))
        self.assertGreaterEqual(metrics.macro_f1, 0.0)
        self.assertGreaterEqual(metrics.weighted_f1, 0.0)
        self.assertSetEqual(set(metrics.labels), set(self.target.unique()))
        self.assertSetEqual(set(metrics.per_class), set(metrics.labels))


if __name__ == "__main__":
    unittest.main()
