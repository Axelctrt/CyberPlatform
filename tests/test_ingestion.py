from pathlib import Path
import tempfile
import unittest

from cyberplatform.ingestion import load_records, normalize_records
from cyberplatform.schema import SourceType


class IngestionTest(unittest.TestCase):
    def test_load_and_normalize_json_records(self):
        records = load_records("data/samples/mixed_events.json")
        events = normalize_records(records)

        self.assertEqual(len(events), 3)
        self.assertEqual(events[0].source_type, SourceType.SYSTEM)
        self.assertEqual(events[1].features["api_action"], "ListAccessKeys")

    def test_load_and_normalize_csv_records(self):
        records = load_records("data/samples/auth_events.csv")
        events = normalize_records(records)

        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].source_type, SourceType.AUTHENTICATION)
        self.assertEqual(events[0].features["failed_attempts"], 6)
        self.assertTrue(events[0].features["is_privileged_account"])

    def test_unsupported_source_format_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "events.txt"
            source.write_text("not supported", encoding="utf-8")

            with self.assertRaises(ValueError):
                load_records(source)


if __name__ == "__main__":
    unittest.main()

