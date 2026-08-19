from __future__ import annotations

from io import BytesIO
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
    category_detection_performance,
    confusion_matrix_table,
    load_demo_events,
    load_metrics_report,
    metrics_report_to_table,
    normalize_generic_upload,
    normalize_suricata_upload,
    priority_counts,
    source_counts,
    validate_unsw_dataframe,
)
from cyberplatform.ml import feature_importance_table, load_model
from cyberplatform.scoring import risk_score_components
from cyberplatform.schema import SourceType

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
selected_threshold = float(report.get("selected_decision_threshold", 0.5)) if report else 0.5

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
    sources = source_counts(event_table)
    if len(sources) == 1:
        active_source = str(sources.iloc[0]["source_type"])
        st.caption(
            f"Source de l'analyse courante : **{active_source}**. "
            "Pour UNSW-NB15, toutes les observations sont des flux réseau ; "
            "un graphique de répartition des sources serait donc artificiel."
        )
    elif len(sources) > 1:
        st.subheader("Répartition des sources")
        st.plotly_chart(
            px.pie(
                sources,
                values="count",
                names="source_type",
                hole=0.45,
                labels={"source_type": "Source", "count": "Événements"},
            ),
            use_container_width=True,
        )

    predicted = pd.DataFrame()
    if not event_table.empty and "prediction" in event_table.columns:
        predicted = event_table[event_table["prediction"].notna()].copy()
        if not predicted.empty:
            predicted["prediction_label"] = predicted["prediction"].map(
                {0: "Aucune attaque détectée", 1: "Attaque détectée"}
            )

    left, right = st.columns(2)
    with left:
        st.subheader("Résultat de la détection")
        if predicted.empty:
            st.caption("Aucune décision ML dans les données actuellement affichées.")
        else:
            prediction_counts = (
                predicted["prediction_label"]
                .value_counts()
                .rename_axis("prediction_label")
                .reset_index(name="count")
            )
            st.plotly_chart(
                px.pie(
                    prediction_counts,
                    values="count",
                    names="prediction_label",
                    hole=0.5,
                    labels={"prediction_label": "Décision du modèle", "count": "Événements"},
                ),
                use_container_width=True,
            )

    with right:
        st.subheader("Priorités des alertes détectées")
        priorities = priority_counts(alert_table)
        if priorities["count"].sum() > 0:
            priority_chart = px.bar(
                priorities,
                x="priority",
                y="count",
                color="priority",
                labels={"priority": "Priorité", "count": "Alertes"},
                category_orders={"priority": ["Low", "Medium", "High", "Critical"]},
            )
            priority_chart.update_layout(showlegend=False)
            st.plotly_chart(priority_chart, use_container_width=True)
        else:
            st.caption("Aucune alerte ML priorisée.")

    if not predicted.empty and "known_attack_category" in predicted.columns:
        category_predictions = predicted.dropna(subset=["known_attack_category"]).copy()
        if not category_predictions.empty:
            st.subheader("Décisions du modèle par catégorie réelle UNSW-NB15")

            actual_attack = (
                category_predictions["known_attack_category"]
                .astype(str)
                .str.casefold()
                .ne("normal")
            )
            predicted_attack = category_predictions["prediction"].astype(int).eq(1)
            true_positives = int((actual_attack & predicted_attack).sum())
            false_negatives = int((actual_attack & ~predicted_attack).sum())
            false_positives = int((~actual_attack & predicted_attack).sum())
            actual_attacks = int(actual_attack.sum())
            sample_recall = (true_positives / actual_attacks * 100) if actual_attacks else 0.0

            quality = st.columns(4)
            quality[0].metric("Attaques réelles", actual_attacks)
            quality[1].metric("Attaques détectées", true_positives)
            quality[2].metric("Faux négatifs", false_negatives)
            quality[3].metric("Faux positifs", false_positives)

            grouped = (
                category_predictions.groupby(
                    ["known_attack_category", "prediction_label"],
                    dropna=False,
                )
                .size()
                .reset_index(name="count")
            )
            st.plotly_chart(
                px.bar(
                    grouped,
                    x="known_attack_category",
                    y="count",
                    color="prediction_label",
                    barmode="group",
                    labels={
                        "known_attack_category": "Catégorie réelle",
                        "prediction_label": "Décision du modèle",
                        "count": "Événements",
                    },
                ),
                use_container_width=True,
            )

            category_table = category_detection_performance(event_table)
            if not category_table.empty:
                category_table = category_table.copy()
                category_table["attack_detection_rate"] = category_table["attack_detection_rate"].map(
                    lambda value: None if pd.isna(value) else round(float(value) * 100, 1)
                )
                category_table["false_positive_rate"] = category_table["false_positive_rate"].map(
                    lambda value: None if pd.isna(value) else round(float(value) * 100, 1)
                )
                st.dataframe(
                    category_table,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "category": "Catégorie réelle",
                        "events": "Événements",
                        "attack_detected": "Attaque détectée",
                        "no_attack_detected": "Aucune attaque détectée",
                        "attack_detection_rate": st.column_config.NumberColumn(
                            "Taux de détection (%)", format="%.1f %%"
                        ),
                        "false_positive_rate": st.column_config.NumberColumn(
                            "Faux positifs (%)", format="%.1f %%"
                        ),
                    },
                )
            st.caption(
                f"Recall observé sur cet échantillon : **{sample_recall:.1f} %**. "
                "Les catégories proviennent de attack_cat et représentent la vérité terrain ; "
                "le modèle décide uniquement si une attaque est détectée ou non."
            )

    st.subheader("Événements")
    st.dataframe(
        event_table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "source_type": "Source",
            "prediction": "Décision binaire (0/1)",
            "known_attack_category": "Catégorie réelle UNSW",
            "attack_type": "Type d'attaque prédit",
        },
    )

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
        ]

        if "known_attack_category" in alert_table.columns:
            categories = sorted(alert_table["known_attack_category"].dropna().unique())
            if categories:
                category_filter = st.multiselect(
                    "Catégorie UNSW connue (vérité terrain)",
                    categories,
                    default=categories,
                )
                filtered = filtered[filtered["known_attack_category"].isin(category_filter)]
                st.caption(
                    "Le filtre utilise attack_cat fourni par UNSW-NB15 ; "
                    "la catégorie n'est pas prédite par le classifieur binaire."
                )

        filtered = filtered.sort_values("risk_score", ascending=False).reset_index(drop=True)
        st.dataframe(
            filtered,
            use_container_width=True,
            hide_index=True,
            column_config={
                "source_type": "Source",
                "prediction": "Décision binaire (0/1)",
                "known_attack_category": "Catégorie réelle UNSW",
                "attack_type": "Type d'attaque prédit",
            },
        )

        if not filtered.empty:
            st.subheader("Détail d'une alerte")
            alert_choice = st.selectbox(
                "Alerte à inspecter",
                options=list(range(len(filtered))),
                format_func=lambda index: (
                    f"#{index + 1} — {filtered.iloc[index].get('priority', 'N/A')} — "
                    f"score {filtered.iloc[index].get('risk_score', 'N/A')}"
                ),
            )
            selected_alert = filtered.iloc[int(alert_choice)]
            confidence = float(selected_alert.get("confidence") or 0.0)
            severity = int(selected_alert.get("severity") or 1)
            source_type = SourceType(str(selected_alert.get("source_type")))
            components = risk_score_components(confidence, severity, source_type)

            detail_metrics = st.columns(4)
            detail_metrics[0].metric("Confiance ML", f"{confidence * 100:.1f} %")
            detail_metrics[1].metric("Score de risque", f"{float(selected_alert.get('risk_score') or 0):.2f} / 100")
            detail_metrics[2].metric("Priorité", str(selected_alert.get("priority") or "N/A"))
            detail_metrics[3].metric(
                "Catégorie réelle UNSW",
                str(selected_alert.get("known_attack_category") or "Non disponible"),
            )

            breakdown = pd.DataFrame(
                [
                    {"Composante": "Confiance ML", "Contribution": components["confidence_component"], "Maximum": 60},
                    {"Composante": "Sévérité", "Contribution": components["severity_component"], "Maximum": 25},
                    {
                        "Composante": "Criticité de la source",
                        "Contribution": components["source_criticality_component"],
                        "Maximum": 15,
                    },
                ]
            )
            st.markdown("**Décomposition du score de risque**")
            st.dataframe(breakdown, use_container_width=True, hide_index=True)
            st.caption(
                "Le score est une règle métier explicite du prototype : confiance ML 60 %, "
                "sévérité 25 % et criticité du type de source 15 %."
            )
            raw_message = selected_alert.get("raw_message")
            if pd.notna(raw_message):
                st.text_area("Événement source", value=str(raw_message), disabled=True)

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

        threshold_selection = report.get("threshold_selection")
        threshold_cols = st.columns(4)
        threshold_cols[0].metric("Seuil Random Forest", f"{float(report.get('primary_decision_threshold', 0.5)):.2f}")
        threshold_cols[1].metric("Seuil modèle utilisé", f"{selected_threshold:.2f}")
        if threshold_selection:
            selected_validation = threshold_selection.get("selected", {})
            threshold_cols[2].metric("Recall validation", f"{float(selected_validation.get('recall', 0)) * 100:.1f} %")
            threshold_cols[3].metric("F1 validation", f"{float(selected_validation.get('f1_score', 0)) * 100:.1f} %")
            st.caption(
                "Le seuil Random Forest est choisi sur un holdout stratifié issu uniquement du jeu d'entraînement, "
                "avec maximisation du F1 sous contrainte de recall. Le jeu de test officiel reste réservé à l'évaluation finale."
            )
        else:
            st.info(
                "Ce rapport a été généré avant l'ajout de l'optimisation de seuil. "
                "Relancez le pipeline d'entraînement pour produire le seuil et les courbes scientifiques."
            )

        selected_model = st.selectbox("Matrice de confusion", ["Random Forest", "Logistic Regression"])
        key = "primary_metrics" if selected_model == "Random Forest" else "baseline_metrics"
        matrix = confusion_matrix_table(report.get(key, {}))
        st.plotly_chart(
            px.imshow(matrix, text_auto=True, aspect="auto", labels={"x": "Décision", "y": "Réalité", "color": "Nombre"}),
            use_container_width=True,
        )

        curves = report.get("curves", {})
        if curves:
            st.subheader("Courbes ROC et Precision-Recall")
            roc_frames: list[pd.DataFrame] = []
            pr_frames: list[pd.DataFrame] = []
            for label, curve_key in (("Logistic Regression", "baseline"), ("Random Forest", "primary")):
                model_curves = curves.get(curve_key, {})
                roc_points = model_curves.get("roc", [])
                pr_points = model_curves.get("precision_recall", [])
                if roc_points:
                    roc_frame = pd.DataFrame(roc_points)
                    roc_frame["Modèle"] = label
                    roc_frames.append(roc_frame)
                if pr_points:
                    pr_frame = pd.DataFrame(pr_points)
                    pr_frame["Modèle"] = label
                    pr_frames.append(pr_frame)

            curve_left, curve_right = st.columns(2)
            with curve_left:
                if roc_frames:
                    roc_data = pd.concat(roc_frames, ignore_index=True)
                    st.plotly_chart(
                        px.line(
                            roc_data,
                            x="fpr",
                            y="tpr",
                            color="Modèle",
                            labels={"fpr": "Taux de faux positifs", "tpr": "Taux de vrais positifs"},
                        ),
                        use_container_width=True,
                    )
            with curve_right:
                if pr_frames:
                    pr_data = pd.concat(pr_frames, ignore_index=True)
                    st.plotly_chart(
                        px.line(
                            pr_data,
                            x="recall",
                            y="precision",
                            color="Modèle",
                            labels={"recall": "Recall", "precision": "Precision"},
                        ),
                        use_container_width=True,
                    )
            st.caption(
                "Les courbes sont calculées sur le jeu de test officiel pour comparer les modèles ; "
                "elles ne servent pas à choisir le seuil de décision."
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

    payload: bytes | None = uploaded.getvalue() if uploaded is not None else None
    unsw_frame: pd.DataFrame | None = None
    unsw_validation: dict | None = None

    if uploaded is not None and mode.startswith("UNSW"):
        try:
            unsw_frame = pd.read_csv(BytesIO(payload or b""))
            if not MODEL_PATH.exists():
                st.error("models/primary_model.joblib absent : entraînez d'abord le modèle UNSW-NB15.")
            else:
                unsw_validation = validate_unsw_dataframe(MODEL_PATH, unsw_frame)
                preview = st.columns(4)
                preview[0].metric("Lignes", unsw_validation["rows"])
                preview[1].metric("Variables requises", unsw_validation["required_columns"])
                preview[2].metric("Variables reconnues", unsw_validation["recognized_columns"])
                preview[3].metric(
                    "Contexte dataset",
                    "label + attack_cat" if unsw_validation["has_label"] and unsw_validation["has_attack_cat"] else "partiel",
                )
                if unsw_validation["compatible"]:
                    st.success(
                        f"Fichier compatible avec le modèle. L'analyse utilisera le seuil de décision {selected_threshold:.2f}."
                    )
                else:
                    missing = ", ".join(unsw_validation["missing_columns"][:12])
                    suffix = "..." if len(unsw_validation["missing_columns"]) > 12 else ""
                    st.error(f"Fichier incompatible. Variables manquantes : {missing}{suffix}")
        except Exception as error:
            st.error(f"Impossible de prévisualiser le CSV : {error}")

    can_analyze_unsw = bool(unsw_validation and unsw_validation.get("compatible"))
    analyze_clicked = False
    if uploaded is not None:
        if mode.startswith("UNSW"):
            analyze_clicked = st.button("Analyser le fichier", disabled=not can_analyze_unsw)
        else:
            analyze_clicked = st.button("Analyser le fichier")

    if uploaded is not None and analyze_clicked:
        try:
            if mode.startswith("UNSW"):
                if unsw_frame is None:
                    raise ValueError("Le fichier UNSW-NB15 n'a pas pu être lu.")
                st.session_state.dashboard_data = analyze_unsw_dataframe(
                    MODEL_PATH,
                    unsw_frame,
                    threshold=selected_threshold,
                )
                st.session_state.analysis_origin = (
                    f"Analyse ML avec le modèle sauvegardé entraîné sur UNSW-NB15 — seuil {selected_threshold:.2f}"
                )
            elif mode.startswith("CSV"):
                st.session_state.dashboard_data = normalize_generic_upload(payload or b"", uploaded.name)
                st.session_state.analysis_origin = "Source générique normalisée — non envoyée au modèle réseau UNSW-NB15"
                st.warning("Cette source est normalisée et visualisée, mais n'est pas analysée par le modèle réseau.")
            else:
                st.session_state.dashboard_data = normalize_suricata_upload(payload or b"")
                st.session_state.analysis_origin = "Suricata EVE normalisé — contexte IDS, sans prétendre à une prédiction UNSW-NB15"
                st.warning("Les alertes Suricata sont contextualisées comme signaux IDS ; elles ne sont pas passées artificiellement dans le modèle UNSW-NB15.")
            st.success("Import traité. Les vues ont été mises à jour.")
            st.rerun()
        except Exception as error:
            st.error(str(error))

    st.divider()
    st.caption(
        "La démonstration multi-sources permet de visualiser séparément des événements "
        "système, cloud, application et authentification, sans les faire passer dans le modèle UNSW-NB15."
    )
    if st.button("Recharger la démonstration multi-sources"):
        st.session_state.dashboard_data = build_dashboard_data(load_demo_events())
        st.session_state.analysis_origin = "Données multi-sources de démonstration — aucune validation ML"
        st.rerun()

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
