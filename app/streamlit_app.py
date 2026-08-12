from __future__ import annotations

import plotly.express as px
import streamlit as st

from cyberplatform.dashboard import (
    build_demo_dashboard_data,
    metrics_to_table,
    priority_counts,
    source_counts,
)


st.set_page_config(
    page_title="CyberPlatform",
    page_icon="CP",
    layout="wide",
)


@st.cache_data
def load_dashboard_data():
    return build_demo_dashboard_data()


data = load_dashboard_data()
event_table = data.event_table
alert_table = data.alert_table
mitre_table = data.mitre_table
importance_table = data.feature_importance_table
metrics_table = metrics_to_table(data.baseline_metrics, data.primary_metrics)

st.title("CyberPlatform")
st.caption("Detection, scoring and prioritization prototype")

summary_columns = st.columns(4)
summary_columns[0].metric("Events", len(event_table))
summary_columns[1].metric("Alerts", len(alert_table))
summary_columns[2].metric("Critical or High", int(event_table["priority"].isin(["Critical", "High"]).sum()))
summary_columns[3].metric("Recommended model", data.recommended_model.title())

priority_filter = st.multiselect(
    "Priority",
    options=["Low", "Medium", "High", "Critical"],
    default=["Medium", "High", "Critical"],
)
source_filter = st.multiselect(
    "Source",
    options=sorted(event_table["source_type"].unique()),
    default=sorted(event_table["source_type"].unique()),
)

filtered_events = event_table[
    event_table["priority"].isin(priority_filter)
    & event_table["source_type"].isin(source_filter)
]
filtered_alerts = alert_table[
    alert_table["priority"].isin(priority_filter)
    & alert_table["source_type"].isin(source_filter)
] if not alert_table.empty else alert_table

overview_tab, alerts_tab, metrics_tab, threat_tab, events_tab = st.tabs(
    ["Overview", "Alerts", "Metrics", "Threat Context", "Events"]
)

with overview_tab:
    chart_columns = st.columns(2)

    with chart_columns[0]:
        st.subheader("Priority distribution")
        priority_chart = priority_counts(filtered_events)
        st.plotly_chart(
            px.bar(
                priority_chart,
                x="priority",
                y="count",
                color="priority",
                color_discrete_map={
                    "Low": "#2ca25f",
                    "Medium": "#f0ad4e",
                    "High": "#f97316",
                    "Critical": "#dc2626",
                },
            ),
            use_container_width=True,
        )

    with chart_columns[1]:
        st.subheader("Sources")
        source_chart = source_counts(filtered_events)
        st.plotly_chart(
            px.pie(
                source_chart,
                values="count",
                names="source_type",
                hole=0.45,
            ),
            use_container_width=True,
        )

    st.subheader("Highest risk events")
    st.dataframe(
        filtered_events.sort_values("risk_score", ascending=False).head(8),
        use_container_width=True,
        hide_index=True,
    )

with alerts_tab:
    st.subheader("Prioritized alerts")
    st.dataframe(
        filtered_alerts.sort_values("risk_score", ascending=False)
        if not filtered_alerts.empty
        else filtered_alerts,
        use_container_width=True,
        hide_index=True,
    )

with metrics_tab:
    st.subheader("Model comparison")
    st.dataframe(
        metrics_table,
        use_container_width=True,
        hide_index=True,
    )
    st.bar_chart(metrics_table.set_index("model")[["accuracy", "precision", "recall", "f1_score"]])

    st.subheader("Random Forest feature importance")
    st.dataframe(
        importance_table,
        use_container_width=True,
        hide_index=True,
    )
    st.bar_chart(importance_table.set_index("feature")["importance"])

with threat_tab:
    st.subheader("MITRE ATT&CK mapping")
    st.dataframe(
        mitre_table,
        use_container_width=True,
        hide_index=True,
    )

with events_tab:
    st.subheader("Normalized events")
    st.dataframe(
        filtered_events,
        use_container_width=True,
        hide_index=True,
    )
