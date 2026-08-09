"""Dashboard data preparation for the Streamlit prototype."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from cyberplatform.ingestion import load_records, normalize_records
from cyberplatform.ml import (
    compare_baseline_and_primary,
    create_train_test_split,
    events_to_dataframe,
    predict_attack_probabilities,
    split_features_target,
    train_primary_classifier,
)
from cyberplatform.ml.baseline import ClassificationMetrics
from cyberplatform.scoring import alert_records, enrich_events_with_scores
from cyberplatform.schema import Priority, SecurityEvent


@dataclass(frozen=True, slots=True)
class DashboardData:
    events: list[SecurityEvent]
    event_table: pd.DataFrame
    alert_table: pd.DataFrame
    baseline_metrics: ClassificationMetrics
    primary_metrics: ClassificationMetrics
    recommended_model: str


def build_demo_dashboard_data(
    sample_path: str = "data/samples/training_events.csv",
) -> DashboardData:
    """Build the sprint 5 dashboard dataset from the local sample file."""
    records = load_records(sample_path)
    events = normalize_records(records)
    feature_table = events_to_dataframe(events)
    features, target = split_features_target(feature_table)
    train_features, test_features, train_target, test_target = create_train_test_split(
        features,
        target,
    )

    comparison = compare_baseline_and_primary(
        train_features,
        test_features,
        train_target,
        test_target,
    )
    primary_model = train_primary_classifier(train_features, train_target)
    probabilities = predict_attack_probabilities(primary_model, features)
    enriched_events = enrich_events_with_scores(events, probabilities)

    event_table = events_to_display_table(enriched_events)
    alert_table = pd.DataFrame(alert_records(enriched_events))

    return DashboardData(
        events=enriched_events,
        event_table=event_table,
        alert_table=alert_table,
        baseline_metrics=comparison.baseline,
        primary_metrics=comparison.primary,
        recommended_model=comparison.recommended_model,
    )


def events_to_display_table(events: list[SecurityEvent]) -> pd.DataFrame:
    """Serialize scored events into a dashboard-friendly table."""
    table = pd.DataFrame([event.to_record() for event in events])
    if table.empty:
        return table

    visible_columns = [
        "timestamp",
        "source_type",
        "event_type",
        "severity",
        "prediction",
        "risk_score",
        "priority",
        "source_ip",
        "destination_ip",
        "username",
        "raw_message",
    ]
    return table[visible_columns]


def metrics_to_table(
    baseline: ClassificationMetrics,
    primary: ClassificationMetrics,
) -> pd.DataFrame:
    """Create a compact model comparison table."""
    return pd.DataFrame(
        [
            {
                "model": "Logistic regression",
                "accuracy": baseline.accuracy,
                "precision": baseline.precision,
                "recall": baseline.recall,
                "f1_score": baseline.f1_score,
            },
            {
                "model": "Random Forest",
                "accuracy": primary.accuracy,
                "precision": primary.precision,
                "recall": primary.recall,
                "f1_score": primary.f1_score,
            },
        ]
    )


def priority_counts(event_table: pd.DataFrame) -> pd.DataFrame:
    """Count events by priority while preserving the expected order."""
    if event_table.empty or "priority" not in event_table.columns:
        return pd.DataFrame({"priority": [], "count": []})

    ordered_priorities = [priority.value for priority in Priority]
    counts = event_table["priority"].value_counts().reindex(ordered_priorities, fill_value=0)
    return counts.rename_axis("priority").reset_index(name="count")


def source_counts(event_table: pd.DataFrame) -> pd.DataFrame:
    """Count events by source type."""
    if event_table.empty or "source_type" not in event_table.columns:
        return pd.DataFrame({"source_type": [], "count": []})

    return (
        event_table["source_type"]
        .value_counts()
        .rename_axis("source_type")
        .reset_index(name="count")
    )

