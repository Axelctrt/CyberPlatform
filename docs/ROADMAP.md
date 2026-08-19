# Roadmap Agile incrémentale pilotée par Kanban

## Règles de pilotage

- Backlog unique lié aux exigences F1 à F7.
- Colonnes de suivi : À faire / En cours / À tester / Terminé.
- Une tâche technique principale à la fois.
- Définition de terminé : code fonctionnel, tests associés, résultat vérifié, documentation mise à jour.
- Commits courts et fonctionnels ; pas de fusion vers une branche stable sans validation.

## Incréments historiques

### Sprint 1 — Socle

- structure du dépôt ;
- schéma `SecurityEvent` ;
- premiers tests.

### Sprint 2 — Ingestion / normalisation

- CSV ;
- JSON ;
- sources multi-sources simulées ;
- normalisation commune.

### Sprint 3 — Prétraitement / baseline

- conversion en features ;
- split reproductible ;
- Logistic Regression ;
- premières métriques.

### Sprint 4 — Modèle principal / scoring

- Random Forest ;
- comparaison baseline / principal ;
- Joblib ;
- score de risque ;
- export CSV.

### Sprint 5 — Dashboard

- vues événements / alertes / métriques ;
- filtres ;
- graphiques Streamlit.

### Sprint 6 — Contexte cyber optionnel

- Suricata EVE JSON Lines ;
- MITRE ATT&CK simplifié ;
- importance des variables.

## Phase de consolidation finale

Branche : `final-ml-platform-consolidation`

### Lot C1 — Dataset scientifique UNSW-NB15 — Terminé

- adaptateur dédié `datasets/unsw_nb15.py` ;
- nettoyage défensif ;
- séparation labels / features ;
- exclusion de `id`, `label` et `attack_cat` des features ;
- split officiel conservé lorsque les deux fichiers sont présents ;
- split stratifié reproductible en repli ;
- option de limitation de lignes pour l'environnement Windows.

### Lot C2 — Entraînement / inférence / métriques — Terminé

- entraînement CLI séparé de Streamlit ;
- Logistic Regression + Random Forest ;
- TN, FP, FN, TP, FPR, FNR ;
- ROC-AUC / PR-AUC lorsque calculables ;
- matrice de confusion ;
- sauvegarde des deux modèles et du modèle sélectionné ;
- rapport JSON des métriques ;
- service d'inférence validant les features attendues.

### Lot C3 — Scoring / dashboard / contexte menace — Terminé

- aucun score ni priorité sur un événement prédit normal ;
- seuils 0-30 / 31-60 / 61-80 / 81-100 ;
- High/Critical comptés uniquement parmi les alertes ;
- import CSV/JSON et UNSW-compatible depuis Streamlit ;
- Suricata EVE accessible depuis l'interface ;
- export CSV d'alertes ;
- modèle sauvegardé utilisé par le dashboard ;
- MITRE corrigé : pas de `T0000`, mapping uniquement pertinent ;
- distinction explicite entre ML réseau et démonstration multi-source.

### Lot C4 — Tests / CI — Terminé

- fixture UNSW-NB15 légère ;
- tests schéma, ingestion, dataset, ML, métriques, scoring, dashboard et MITRE ;
- test du pipeline d'entraînement complet sur fixture ;
- GitHub Actions sans dépendance au dataset complet.

### Lot C5 — Documentation / validation finale — En cours

- README Windows et commandes d'exploitation ;
- limites scientifiques ;
- architecture finale ;
- vérification CI et tests ;
- compte rendu final de conformité F1-F7.

## Extensions laissées au backlog

- classification multi-classe UNSW-NB15, uniquement après validation binaire sur le dataset complet ;
- SHAP local si l'installation et le temps restent maîtrisés ;
- SQLite si la persistance de plusieurs analyses devient nécessaire ;
- CICIDS-2018 comme validation externe éventuelle ;
- Docker uniquement après stabilisation de l'exécution locale Windows.

Restent explicitement hors périmètre : SIEM industriel complet, Wazuh/Elastic complet, orchestration SOC, réponse automatique, Kubernetes, microservices et Deep Learning complexe.
