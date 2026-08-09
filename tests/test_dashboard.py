import unittest

from cyberplatform.dashboard import (
    build_demo_dashboard_data,
    metrics_to_table,
    priority_counts,
    source_counts,
)


class DashboardDataTest(unittest.TestCase):
    def test_demo_dashboard_data_contains_events_alerts_and_metrics(self):
        data = build_demo_dashboard_data()

        self.assertEqual(len(data.event_table), 10)
        self.assertIn("risk_score", data.event_table.columns)
        self.assertGreaterEqual(len(data.alert_table), 1)
        self.assertIn(data.recommended_model, {"baseline", "primary"})

    def test_metrics_are_formatted_as_comparison_table(self):
        data = build_demo_dashboard_data()
        table = metrics_to_table(data.baseline_metrics, data.primary_metrics)

        self.assertEqual(list(table["model"]), ["Logistic regression", "Random Forest"])
        self.assertIn("f1_score", table.columns)

    def test_chart_tables_are_generated_from_event_table(self):
        data = build_demo_dashboard_data()

        self.assertEqual(priority_counts(data.event_table)["count"].sum(), len(data.event_table))
        self.assertEqual(source_counts(data.event_table)["count"].sum(), len(data.event_table))


if __name__ == "__main__":
    unittest.main()

