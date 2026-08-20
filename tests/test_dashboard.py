from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from cyberplatform.dashboard import (
    analyze_unsw_dataframe,
    build_dashboard_data,
    category_detection_performance,
    confusion_matrix_table,
    known_category_counts,
    load_demo_events,
    metrics_report_to_table,
    multiclass_confusion_matrix_table,
    multiclass_per_class_table,
    normalize_generic_upload,
    priority_counts,
    source_counts,
    validate_unsw_dataframe,
)
from cyberplatform.datasets import load_unsw_nb15_file, prepare_unsw_nb15_split
from cyberplatform.ml import save_model, train_attack_family_classifier, train_primary_classifier


class DashboardDataTest(unittest.TestCase):
    def test_demo_sources_are_visible_but_not_fake_ml_alerts(self):
        data = build_dashboard_data(load_demo_events())
        self.assertGreaterEqual(len(data.event_table), 1)
        self.assertEqual(len(data.alert_table), 0)
        self.assertGreaterEqual(source_counts(data.event_table)["count"].sum(), 1)
        self.assertEqual(priority_counts(data.alert_table)["count"].sum(), 0)
        self.assertEqual(known_category_counts(data.event_table)["count"].sum(), 0)

    def test_generic_upload_is_normalized_without_prediction(self):
        payload = Path("data/samples/auth_events.csv").read_bytes()
        data = normalize_generic_upload(payload, "auth_events.csv")
        self.assertEqual(len(data.event_table), 2)
        self.assertTrue(data.event_table["prediction"].isna().all())

    def test_metrics_and_confusion_matrices_are_dashboard_ready(self):
        report = {
            "baseline_metrics": {"accuracy": .8, "precision": .7, "recall": .9, "f1_score": .79, "fpr": .2, "fnr": .1, "roc_auc": .9, "pr_auc": .88},
            "primary_metrics": {"accuracy": .9, "precision": .9, "recall": .9, "f1_score": .9, "fpr": .1, "fnr": .1, "roc_auc": .95, "pr_auc": .94},
        }
        self.assertEqual(len(metrics_report_to_table(report)), 2)
        matrix = confusion_matrix_table({"confusion_matrix": [[8, 2], [1, 9]]})
        self.assertEqual(matrix.loc["Actual Attack", "Pred Attack"], 9)

        multiclass = {
            "metrics": {
                "labels": ["DoS", "Exploits"],
                "confusion_matrix": [[3, 1], [2, 4]],
                "per_class": {
                    "DoS": {"precision": .6, "recall": .75, "f1_score": .67, "support": 4},
                    "Exploits": {"precision": .8, "recall": .67, "f1_score": .73, "support": 6},
                },
            }
        }
        multi_matrix = multiclass_confusion_matrix_table(multiclass)
        self.assertEqual(multi_matrix.loc["DoS", "Exploits"], 1)
        self.assertEqual(len(multiclass_per_class_table(multiclass)), 2)

    def test_saved_binary_model_exposes_dataset_category_without_family_model(self):
        frame = load_unsw_nb15_file("data/samples/unsw_nb15_sample.csv")
        split = prepare_unsw_nb15_split(frame, test_size=0.3)
        model = train_primary_classifier(split.train_features, split.train_target)
        with TemporaryDirectory() as tmpdir:
            path = save_model(model, Path(tmpdir) / "primary_model.joblib")
            validation = validate_unsw_dataframe(path, frame)
            data = analyze_unsw_dataframe(path, frame)

        self.assertTrue(validation["compatible"])
        self.assertEqual(validation["required_columns"], validation["recognized_columns"])
        self.assertTrue(validation["has_label"])
        self.assertTrue(validation["has_attack_cat"])
        self.assertEqual(len(data.event_table), len(frame))
        self.assertIn("prediction", data.event_table.columns)
        self.assertIn("known_attack_category", data.event_table.columns)
        self.assertEqual(known_category_counts(data.event_table)["count"].sum(), len(frame))
        self.assertSetEqual(
            set(data.event_table["known_attack_category"].dropna()),
            set(frame["attack_cat"].dropna()),
        )
        performance = category_detection_performance(data.event_table)
        self.assertFalse(performance.empty)
        self.assertIn("attack_detection_rate", performance.columns)
        self.assertIn("false_positive_rate", performance.columns)
        if not data.alert_table.empty:
            self.assertTrue(data.alert_table["attack_type"].isna().all())

    def test_detected_unsw_alerts_can_be_enriched_with_predicted_family(self):
        frame = load_unsw_nb15_file("data/samples/unsw_nb15_sample.csv")
        split = prepare_unsw_nb15_split(frame, test_size=0.3)
        binary_model = train_primary_classifier(split.train_features, split.train_target)

        attack_rows = frame[frame["label"].eq(1)].reset_index(drop=True)
        attack_features = attack_rows[list(split.feature_columns)]
        family_model = train_attack_family_classifier(attack_features, attack_rows["attack_cat"])

        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            binary_path = save_model(binary_model, root / "primary_model.joblib")
            family_path = save_model(family_model, root / "attack_family_random_forest.joblib")
            data = analyze_unsw_dataframe(
                binary_path,
                frame,
                attack_family_model_path=family_path,
            )

        if not data.alert_table.empty:
            self.assertTrue(data.alert_table["attack_type"].notna().all())
            self.assertTrue(data.alert_table["attack_family_confidence"].notna().all())
            self.assertTrue(
                data.alert_table["attack_type"].isin(set(attack_rows["attack_cat"].astype(str))).all()
            )

    def test_unsw_validation_reports_missing_model_columns(self):
        frame = load_unsw_nb15_file("data/samples/unsw_nb15_sample.csv")
        split = prepare_unsw_nb15_split(frame, test_size=0.3)
        model = train_primary_classifier(split.train_features, split.train_target)
        with TemporaryDirectory() as tmpdir:
            path = save_model(model, Path(tmpdir) / "primary_model.joblib")
            missing_column = split.feature_columns[0]
            invalid = frame.drop(columns=[missing_column])
            validation = validate_unsw_dataframe(path, invalid)

        self.assertFalse(validation["compatible"])
        self.assertIn(missing_column, validation["missing_columns"])


if __name__ == "__main__":
    unittest.main()
