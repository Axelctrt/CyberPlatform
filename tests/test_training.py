from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from cyberplatform.training import train_unsw_nb15


class TrainingCommandTest(unittest.TestCase):
    def test_training_pipeline_writes_models_metrics_threshold_and_curves_without_full_dataset(self):
        sample = Path("data/samples/unsw_nb15_sample.csv").read_text(encoding="utf-8")
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            data_dir = root / "unsw"
            data_dir.mkdir()
            (data_dir / "UNSW_NB15_training-set.csv").write_text(sample, encoding="utf-8")
            (data_dir / "UNSW_NB15_testing-set.csv").write_text(sample, encoding="utf-8")
            models_dir = root / "models"
            metrics_path = root / "reports" / "model_metrics.json"

            report = train_unsw_nb15(data_dir, models_dir=models_dir, metrics_path=metrics_path)

            self.assertEqual(report["dataset"], "UNSW-NB15")
            self.assertEqual(report["split_strategy"], "official_train_test_files")
            self.assertTrue(0.0 <= report["primary_decision_threshold"] <= 1.0)
            self.assertIn("threshold_selection", report)
            self.assertGreater(report["threshold_selection"]["validation_rows"], 0)
            self.assertIn("curves", report)
            self.assertTrue(report["curves"]["primary"]["roc"])
            self.assertTrue(report["curves"]["primary"]["precision_recall"])
            self.assertTrue((models_dir / "logistic_regression.joblib").exists())
            self.assertTrue((models_dir / "random_forest.joblib").exists())
            self.assertTrue((models_dir / "primary_model.joblib").exists())
            self.assertTrue(metrics_path.exists())


if __name__ == "__main__":
    unittest.main()
