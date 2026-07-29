import unittest

from cyberplatform.ingestion import load_records, normalize_records
from cyberplatform.ml import (
    create_train_test_split,
    evaluate_classifier,
    events_to_dataframe,
    split_features_target,
    train_baseline_classifier,
)


class MLPipelineTest(unittest.TestCase):
    def test_events_are_converted_to_training_dataframe(self):
        records = load_records("data/samples/training_events.csv")
        events = normalize_records(records)
        dataframe = events_to_dataframe(events)

        self.assertEqual(len(dataframe), 10)
        self.assertIn("source_type", dataframe.columns)
        self.assertIn("bytes_sent", dataframe.columns)
        self.assertIn("label", dataframe.columns)

    def test_baseline_classifier_can_be_trained_and_evaluated(self):
        records = load_records("data/samples/training_events.csv")
        events = normalize_records(records)
        dataframe = events_to_dataframe(events)
        features, target = split_features_target(dataframe)
        train_features, test_features, train_target, test_target = create_train_test_split(
            features,
            target,
        )

        model = train_baseline_classifier(train_features, train_target)
        metrics = evaluate_classifier(model, test_features, test_target)

        self.assertGreaterEqual(metrics.accuracy, 0.5)
        self.assertGreaterEqual(metrics.f1_score, 0.5)

    def test_missing_label_is_rejected(self):
        records = load_records("data/samples/mixed_events.json")
        events = normalize_records(records)
        dataframe = events_to_dataframe(events)

        with self.assertRaises(ValueError):
            split_features_target(dataframe)


if __name__ == "__main__":
    unittest.main()
