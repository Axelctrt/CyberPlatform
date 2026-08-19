from datetime import datetime, timezone
import unittest

from cyberplatform.schema import Priority, SecurityEvent, SourceType, priority_from_score, validate_security_event


class SecurityEventSchemaTest(unittest.TestCase):
    def _event(self, **overrides):
        values = dict(
            timestamp=datetime(2026, 7, 19, 10, 15, tzinfo=timezone.utc),
            source_type=SourceType.NETWORK,
            event_type="network_flow",
            raw_message="Sample event",
            severity=2,
        )
        values.update(overrides)
        return SecurityEvent(**values)

    def test_valid_event_serializes(self):
        event = self._event()
        validate_security_event(event)
        self.assertEqual(event.to_record()["source_type"], "network")

    def test_invalid_severity_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_security_event(self._event(severity=6))

    def test_invalid_risk_score_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_security_event(self._event(risk_score=101))

    def test_priority_boundaries_match_specification(self):
        expected = {
            0: Priority.LOW,
            30: Priority.LOW,
            31: Priority.MEDIUM,
            60: Priority.MEDIUM,
            61: Priority.HIGH,
            80: Priority.HIGH,
            81: Priority.CRITICAL,
            100: Priority.CRITICAL,
        }
        for score, priority in expected.items():
            with self.subTest(score=score):
                self.assertEqual(priority_from_score(score), priority)

    def test_out_of_range_priority_score_is_rejected(self):
        for score in (-1, 101):
            with self.assertRaises(ValueError):
                priority_from_score(score)


if __name__ == "__main__":
    unittest.main()
