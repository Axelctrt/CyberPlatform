import unittest

from cyberplatform.datasets import load_unsw_nb15_file, prepare_unsw_nb15_split
from cyberplatform.ml import compare_baseline_and_primary, predict_attack_probabilities


class ModelPrioritizationTest(unittest.TestCase):
    def test_comparison_can_return_fitted_models_for_training_pipeline(self):
        split = prepare_unsw_nb15_split(load_unsw_nb15_file("data/samples/unsw_nb15_sample.csv"), test_size=0.3)
        comparison = compare_baseline_and_primary(
            split.train_features,
            split.test_features,
            split.train_target,
            split.test_target,
            return_models=True,
        )
        self.assertIsNotNone(comparison.baseline_model)
        self.assertIsNotNone(comparison.primary_model)
        probabilities = predict_attack_probabilities(comparison.primary_model, split.test_features)
        self.assertEqual(len(probabilities), len(split.test_features))


if __name__ == "__main__":
    unittest.main()
