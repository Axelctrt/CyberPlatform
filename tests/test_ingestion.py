from pathlib import Path
import tempfile
import unittest

from cyberplatform.ingestion import load_eve_json_records, load_records, normalize_eve_records, normalize_records
from cyberplatform.schema import SourceType


class IngestionTest(unittest.TestCase):
    def test_load_and_normalize_json_records(self):
        events = normalize_records(load_records("data/samples/mixed_events.json"))
        self.assertEqual(len(events), 3)
        self.assertEqual(events[0].source_type, SourceType.SYSTEM)
        self.assertEqual(events[1].features["api_action"], "ListAccessKeys")

    def test_load_and_normalize_csv_records(self):
        events = normalize_records(load_records("data/samples/auth_events.csv"))
        self.assertEqual(events[0].source_type, SourceType.AUTHENTICATION)
        self.assertEqual(events[0].features["failed_attempts"], 6)
        self.assertTrue(events[0].features["is_privileged_account"])

    def test_unsupported_source_format_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "events.txt"
            source.write_text("not supported", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_records(source)

    def test_suricata_eve_json_is_loaded_and_normalized(self):
        events = normalize_eve_records(load_eve_json_records("data/samples/suricata_eve_sample.jsonl"))
        self.assertGreaterEqual(len(events), 1)
        self.assertEqual(events[0].source_type, SourceType.NETWORK)

    def test_invalid_suricata_json_line_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "bad.jsonl"
            source.write_text('{"event_type":"alert"}\n{bad json}\n', encoding="utf-8")
            with self.assertRaises(ValueError):
                load_eve_json_records(source)


if __name__ == "__main__":
    unittest.main()
