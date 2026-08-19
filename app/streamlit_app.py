from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from cyberplatform.dashboard import (
    analyze_unsw_dataframe,
    build_dashboard_data,
    confusion_matrix_table,
    load_demo_events,
    load_metrics_report,
    metrics_report_to_table,
    normalize_generic_upload,
    normalize_suricata_upload,
    priority_counts,
    source_counts,
)
from cyberplatform.ml import feature_importance_table, load_model

st.set_page_config(page_title="CyberPlatform", page_icon="🛡️", layout="wide")
st.title("CyberPlatform")
st.caption("Prototype académique local de détection, scoring et priorisation d'incidents")

MODEL_PATH = PROJECT_ROOT / "models" / "primary_model.joblib"
RF_MODEL_PATH = PROJECT_ROOT / "models" / "random_forest.joblib"
METRICS_PATH = PROJECT_ROOT / "reports" / "model_metrics.json"

if "dashboard_data" not in st.session_state:
    st.session_state.dashboard_data = build_dashboard_data(load_demo_events())
if "analysis_origin" not in st.session_state:
    st.session_state.analysis_origin = "Données multi-sources de démonstration — aucune validation ML"

data = st.session_state.dashboard_data
event_table = data.event_table
alert_table = data.alert_table
mitre_table = data.mitre_table
report = load_metrics_report(METRICS_PATH)

st.info(st.session_state.analysis_origin)
summary = st.columns(4)
summary[0].metric("Événements", len(event_table))
summary[1].metric("Alertes ML", len(alert_table))
high_critical = 0 if alert_table.empty else int(alert_table["priority"].isin(["High", "Critical"]).sum())
summary[2].metric("High / Critical", high_critical)
summary[3].metric("Modèle sélectionné", report.get("selected_model", "Non entraîné") if report else "Non entraîné")

overview_tab, alerts_tab, ml_tab, import_tab, threat_tab, explain_tab = st.tabs(
    ["Vue d'ensemble", "Alertes", "Analyse ML", "Import / Analyse", "Threat Context", "Explicabilité"]
)

with overview_tab:
    left, right = st.columns(2)
    with left:
        st.subheader("Sources des événements")
        sources = source_counts(event_table)
        if not sources.empty:
            st.plotly_chart(px.pie(sources, values="count", names="source_type", hole=0.4), use_container_width=True)
        else:
            st.caption("Aucun événement chargé.")
    with right:
        st.subheader("Priorités des alertes détectées")
        priorities = priority_counts(alert_table)
        if priorities["count"].sum() > 0:
            st.plotly_chart(px.bar(priorities, x="priority", y="count"), use_container_width=True)
        else:
            st.caption("Aucune alerte ML priorisée.")
    st.subheader("Événements")
    st.dataframe(event_table, use_container_width=True, hide_index=True)

with alerts_tab:
    st.subheader("Alertes détectées et priorisées")
    if alert_table.empty:
        st.caption("Aucune alerte ML disponible. Importez un CSV compatible UNSW-NB15 après entraînement du modèle.")
    else:
        priorities = ["Low", "Medium", "High", "Critical"]
        priority_filter = st.multiselect("Priorité", priorities, default=priorities)
        sources = sorted(alert_table["source_type"].dropna().unique())
        source_filter = st.multiselect("Source", sources, default=sources)
        filtered = alert_table[
            alert_table["priority"].isin(priority_filter) & alert_table["source_type"].isin(source_filter)
        ].sort_values("risk_score", ascending=False)
        st.dataframe(filtered, use_container_width=True, hide_index=True)
        st.download_button(
            "Télécharger les alertes CSV",
            data=filtered.to_csv(index=False).encode("utf-8"),
            file_name="cyberplatform_alerts.csv",
            mime="text/csv",
        )

with ml_tab:
    st.subheader("Comparaison Logistic Regression / Random Forest")
    if report is None:
        st.warning("Aucun rapport d'entraînement trouvé. Exécutez le pipeline UNSW-NB15 avant la démonstration ML.")
        st.code("python -m cyberplatform.training --data-dir data/raw/unsw_nb15", language="powershell")
    else:
        st.caption(f"Dataset : {report.get('dataset')} — split : {report.get('split_strategy')}")
        metrics_table = metrics_report_to_table(report)
        st.dataframe(metrics_table, use_container_width=True, hide_index=True)
        selected_model = st.selectbox("Matrice de confusion", ["Random Forest", "Logistic Regression"])
        key = "primary_metrics" if selected_model == "Random Forest" else "baseline_metrics"
        matrix = confusion_matrix_table(report.get(key, {}))
        st.plotly_chart(
            px.imshow(matrix, text_auto=True, aspect="auto", labels={"x": "Prédit", "y": "Réel", "color": "Nombre"}),
            use_container_width=True,
        )
        st.caption("L'interprétation privilégie recall, precision, F1 et taux de faux positifs plutôt que l'accuracy seule.")

with import_tab:
    st.subheader("Importer une source")
    mode = st.selectbox(
        "Type de source",
        ["UNSW-NB15 compatible (CSV)", "CSV / JSON générique", "Suricata EVE JSON Lines"],
    )
    allowed = ["csv"] if mode.startswith("UNSW") else ["csv", "json"] if mode.startswith("CSV") else ["jsonl", "json"]
    uploaded = st.file_uploader("Fichier", type=allowed)
    if uploaded is not None and st.button("Analyser le fichier"):
        try:
            payload = uploaded.getvalue()
            if mode.startswith("UNSW"):
                if not MODEL_PATH.exists():
                    raise FileNotFoundError("models/primary_model.joblib absent : entraînez d'abord le modèle UNSW-NB15.")
                frame = pd.read_csv(uploaded)
                st.session_state.dashboard_data = analyze_unsw_dataframe(MODEL_PATH, frame)
                st.session_state.analysis_origin = "Analyse ML avec le modèle sauvegardé entraîné sur UNSW-NB15"
            elif mode.startswith("CSV"):
                st.session_state.dashboard_data = normalize_generic_upload(payload, uploaded.name)
                st.session_state.analysis_origin = "Source générique normalisée — non envoyée au modèle réseau UNSW-NB15"
                st.warning("Cette source est normalisée et visualisée, mais n'est pas analysée par le modèle réseau.")
            else:
                st.session_state.dashboard_data = normalize_suricata_upload(payload)
                st.session_state.analysis_origin = "Suricata EVE normalisé — contexte IDS, sans prétendre à une prédiction UNSW-NB15"
                st.warning("Les alertes Suricata sont contextualisées comme signaux IDS ; elles ne sont pas passées artificiellement dans le modèle UNSW-NB15.")
            st.success("Import traité. Les vues ont été mises à jour.")
            st.rerun()
        except Exception as error:
            st.error(str(error))

with threat_tab:
    st.subheader("MITRE ATT&CK — mapping simplifié et indicatif")
    if mitre_table.empty:
        st.caption("Aucun événement à contextualiser.")
    else:
        mapped = mitre_table[mitre_table["technique_id"].notna()]
        st.dataframe(mapped if not mapped.empty else mitre_table, use_container_width=True, hide_index=True)
        st.caption("Un événement bénin ou non détecté comme suspect reste non mappé. Aucun identifiant ATT&CK fictif n'est utilisé.")

with explain_tab:
    st.subheader("Importance globale des variables — Random Forest")
    if not RF_MODEL_PATH.exists():
        st.caption("Le modèle Random Forest sauvegardé n'est pas encore disponible.")
    else:
        try:
            importances = feature_importance_table(load_model(RF_MODEL_PATH), top_n=15)
            st.dataframe(importances, use_container_width=True, hide_index=True)
            st.bar_chart(importances.set_index("feature")["importance"])
        except ValueError as error:
            st.warning(str(error))
