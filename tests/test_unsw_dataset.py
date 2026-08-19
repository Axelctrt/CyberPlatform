import unittest

import numpy as np
import pandas as pd

from cyberplatform.datasets import clean_unsw_nb15_dataframe, load_unsw_nb15_file, prepare_unsw_nb15_split


class UNSWNB15DatasetTest(unittest.TestCase):
    def test_sample_is_loaded_and_labels_preserved(self):
        frame = load_unsw_nb15_file("data/samples/unsw_nb15_sample.csv")
        self.assertEqual(len(frame), 20)
        self.assertEqual(set(frame["label"]), {0, 1})

    def test_label_attack_category_and_id_are_excluded_from_features(self):
        split = prepare_unsw_nb15_split(load_unsw_nb15_file("data/samples/unsw_nb15_sample.csv"))
        self.assertNotIn("label", split.feature_columns)
        self.assertNotIn("attack_cat", split.feature_columns)
        self.assertNotIn("id", split.feature_columns)

    def test_split_is_reproducible_and_stratified(self):
        frame = load_unsw_nb15_file("data/samples/unsw_nb15_sample.csv")
        first = prepare_unsw_nb15_split(frame, test_size=0.3, random_state=42)
        second = prepare_unsw_nb15_split(frame, test_size=0.3, random_state=42)
        pd.testing.assert_frame_equal(first.test_features, second.test_features)
        self.assertEqual(set(first.test_target), {0, 1})

    def test_infinite_values_and_invalid_labels_are_cleaned(self):
        frame = pd.DataFrame({
            "dur": [1.0, np.inf, 3.0],
            "attack_cat": [" Normal ", "Generic", "Bad"],
            "label": [0, 1, 7],
        })
        cleaned = clean_unsw_nb15_dataframe(frame)
        self.assertEqual(len(cleaned), 2)
        self.assertTrue(pd.isna(cleaned.loc[1, "dur"]))
        self.assertEqual(cleaned.loc[0, "attack_cat"], "Normal")


if __name__ == "__main__":
    unittest.main()
