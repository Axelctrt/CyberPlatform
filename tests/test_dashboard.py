from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from cyberplatform.dashboard import (
    analyze_unsw_dataframe,
    build_dashboard_data,
    confusion_matrix_table,
    load_demo_events,
    metrics_report_to_table,
    normalize_generic_upload,
    priority_counts,
    source_counts,
)
from cyberplatform.datasets import load_unsw_nb15_file, prepare_unsw_nb15_split
from cyberplatform.ml import save_model, train_primary_classifier


class DashboardDataTest(unittest.TestCase):
    def test_demo_sources_are_visible_but_not_fake_ml_alerts(self):
        data = build_dashboard_data(load_demo_events())
        self.assertGreaterEqual(len(data.event_table), 1)
        self.assertEqual(len(data.alert_table), 0)
        self.assertGreaterEqual(source_counts(data.event_table)["count"].sum(), 1)
        self.assertEqual(priority_counts(data.alert_table)["count"].sum(), 0)

    def test_generic_upload_is_normalized_without_prediction(self):
        payload = Path("data/samples/auth_events.csv").read_bytes()
        data = normalize_generic_upload(payload, "auth_events.csv")
        self.assertEqual(len(data.event_table), 2)
        self.assertTrue(data.event_table["prediction"].isna().all())

    def test_metrics_and_confusion_matrix_are_dashboard_ready(self):
        report = {
            "baseline_metrics": {"accuracy": .8, "precision": .7, "recall": .9, "f1_score": .79, "fpr": .2, "fnr": .1, "roc_auc": .9, "pr_auc": .88},
            "primary_metrics": {"accuracy": .9, "precision": .9, "recall": .9, "f1_score": .9, "fpr": .1, "fnr": .1, "roc_auc": .95, "pr_auc": .94},
        }
        self.assertEqual(len(metrics_report_to_table(report)), 2)
        matrix = confusion_matrix_table({"confusion_matrix": [[8, 2], [1, 9]]})
        self.assertEqual(matrix.loc["Actual Attack", "Pred Attack"], 9)

    def test_saved_binary_model_does_not_fake_multiclass_attack_type(self):
        frame = load_unsw_nb15_file("data/samples/unsw_nb15_sample.csv")
        split = prepare_unsw_nb15_split(frame, test_size=0.3)
        model = train_primary_classifier(split.train_features, split.train_target)
        with TemporaryDirectory() as tmpdir:
            path = save_model(model, Path(tmpdir) / "primary_model.joblib")
            data = analyze_unsw_dataframe(path, frame)
        self.assertEqual(len(data.event_table), len(frame))
        self.assertIn("prediction", data.event_table.columns)
        if not data.alert_table.empty:
            self.assertTrue(data.alert_table["attack_type"].isna().all())


if __name__ == "__main__":
    unittest.main()
