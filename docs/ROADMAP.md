# Roadmap Agile incrémentale pilotée par Kanban

## Règles de pilotage

- Backlog unique lié aux exigences F1 à F7.
- Colonnes de suivi : À faire / En cours / À tester / Terminé.
- Une tâche technique principale à la fois.
- Définition de terminé : code fonctionnel, tests associés, résultat vérifié, documentation mise à jour.
- Commits courts et fonctionnels ; pas de fusion vers une branche stable sans validation.

## Incréments historiques

### Sprint 1 — Socle
- structure du dépôt ; schéma `SecurityEvent` ; premiers tests.

### Sprint 2 — Ingestion / normalisation
- CSV ; JSON ; sources multi-sources simulées ; normalisation commune.

### Sprint 3 — Prétraitement / baseline
- conversion en features ; split reproductible ; Logistic Regression ; premières métriques.

### Sprint 4 — Modèle principal / scoring
- Random Forest ; comparaison ; Joblib ; score de risque ; export CSV.

### Sprint 5 — Dashboard
- vues événements / alertes / métriques ; filtres ; graphiques Streamlit.

### Sprint 6 — Contexte cyber optionnel
- Suricata EVE JSON Lines ; MITRE ATT&CK simplifié ; importance des variables.

## Phase de consolidation finale

Branche : `final-ml-platform-consolidation`

### Lot C1 — Dataset scientifique UNSW-NB15 — Terminé
- adaptateur dédié ; nettoyage défensif ; séparation labels/features ; exclusion de `id`, `label`, `attack_cat` ; split officiel ou repli stratifié reproductible ; option Windows de limitation de lignes.

### Lot C2 — Entraînement / inférence / métriques — Terminé
- CLI d'entraînement séparée de Streamlit ; Logistic Regression + Random Forest ; TN/FP/FN/TP/FPR/FNR ; ROC-AUC / PR-AUC ; matrice de confusion ; Joblib ; rapport JSON ; validation des features d'inférence.

### Lot C3 — Scoring / dashboard / contexte menace — Terminé
- aucun score/priorité sur un événement normal ; seuils 0-30 / 31-60 / 61-80 / 81-100 ; High/Critical parmi les alertes uniquement ; import CSV/JSON/UNSW/Suricata ; export CSV ; modèle sauvegardé ; MITRE sans `T0000` ; distinction ML réseau / multi-source ; aucune fausse classification multi-classe à partir de `attack_cat`.

### Lot C4 — Tests / CI — Terminé
- fixture UNSW-NB15 légère ; tests schéma, ingestion, dataset, ML, métriques, scoring, dashboard, MITRE et entraînement ; GitHub Actions sans dataset complet.

### Lot C5 — Documentation / validation finale — Terminé
- README Windows ; installation, dataset, entraînement, tests, dashboard ; limites scientifiques ; architecture ; stockage léger ; roadmap mise à jour ; draft PR de validation sans fusion.

## Extensions laissées au backlog

- classification multi-classe UNSW-NB15 après validation binaire sur le dataset complet ;
- SHAP local si l'installation reste légère ;
- SQLite si la persistance de plusieurs analyses devient nécessaire ;
- CICIDS-2018 comme validation externe éventuelle ;
- Docker après stabilisation locale Windows.

Restent hors périmètre : SIEM industriel complet, Wazuh/Elastic complet, orchestration SOC, réponse automatique, Kubernetes, microservices et Deep Learning complexe.
