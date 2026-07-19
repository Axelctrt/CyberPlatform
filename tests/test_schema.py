from datetime import datetime, timezone
import unittest

from cyberplatform.schema import (
    Priority,
    SecurityEvent,
    SourceType,
    priority_from_score,
    validate_security_event,
)


class SecurityEventSchemaTest(unittest.TestCase):
    def test_event_can_be_serialized_to_record(self):
        event = SecurityEvent(
            timestamp=datetime(2026, 7, 19, 10, 15, tzinfo=timezone.utc),
            source_type=SourceType.NETWORK,
            event_type="network_flow",
            raw_message="Sample event",
            severity=2,
        )

        validate_security_event(event)
        record = event.to_record()

        self.assertEqual(record["source_type"], "network")
        self.assertEqual(record["event_type"], "network_flow")
        self.assertEqual(record["severity"], 2)

    def test_priority_is_derived_from_risk_score(self):
        self.assertEqual(priority_from_score(10), Priority.LOW)
        self.assertEqual(priority_from_score(50), Priority.MEDIUM)
        self.assertEqual(priority_from_score(70), Priority.HIGH)
        self.assertEqual(priority_from_score(90), Priority.CRITICAL)


if __name__ == "__main__":
    unittest.main()

