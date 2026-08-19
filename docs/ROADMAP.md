# Roadmap Agile incrémentale pilotée par Kanban

## Statut de la version finale

La consolidation du projet est terminée. La branche `main` constitue désormais la **version stable finale du PFE**.

Les branches historiques de développement restent utiles pour la traçabilité, mais elles ne représentent plus l'état de référence du projet. Toute évolution future éventuelle doit partir de `main`, être développée sur une branche dédiée, testée puis intégrée par pull request.

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

## Phase de consolidation finale — Terminée

La consolidation a été développée sur `final-ml-platform-consolidation`, validée par tests automatisés et expérimentation complète sur UNSW-NB15, puis fusionnée dans la branche de consolidation `threat-context-extensions`. L'état validé a ensuite servi de base à la branche stable `main`.

### Lot C1 — Dataset scientifique UNSW-NB15 — Terminé
- adaptateur dédié ; nettoyage défensif ; séparation labels/features ; exclusion de `id`, `label`, `attack_cat` ; split officiel ou repli stratifié reproductible ; option Windows de limitation de lignes.

### Lot C2 — Entraînement / inférence / métriques — Terminé
- CLI d'entraînement séparée de Streamlit ; Logistic Regression + Random Forest ; TN/FP/FN/TP/FPR/FNR ; ROC-AUC / PR-AUC ; matrice de confusion ; Joblib ; rapport JSON ; validation des features d'inférence.

### Lot C3 — Scoring / dashboard / contexte menace — Terminé
- aucun score/priorité sur un événement normal ; seuils 0-30 / 31-60 / 61-80 / 81-100 ; High/Critical parmi les alertes uniquement ; import CSV/JSON/UNSW/Suricata ; export CSV ; modèle sauvegardé ; MITRE sans `T0000` ; distinction ML réseau / multi-source ; aucune fausse classification multi-classe à partir de `attack_cat`.

### Lot C4 — Tests / CI — Terminé
- fixture UNSW-NB15 légère ; tests schéma, ingestion, dataset, ML, métriques, scoring, dashboard, MITRE et entraînement ; GitHub Actions sans dataset complet.

### Lot C5 — Documentation / validation scientifique finale — Terminé
- README Windows ; installation, dataset, entraînement, tests et dashboard ; résultats scientifiques finaux ; limites du prototype ; architecture ; stockage léger ; documentation scientifique dédiée ; rapport `reports/model_metrics.json` versionné.

### Lot C6 — Améliorations finales dans le périmètre — Terminé
- étude de sensibilité du seuil Random Forest ; maintien du seuil opérationnel `0.50` après vérification de généralisation ; courbes ROC et Precision-Recall ; analyse des erreurs par catégorie réelle UNSW-NB15 ; prévalidation des fichiers avant inférence ; inspection détaillée des alertes ; décomposition du score de risque.

### Validation finale — Terminée
- validation sur le split officiel UNSW-NB15 : 175 341 lignes d'entraînement et 82 332 lignes de test ;
- Random Forest retenue comme modèle principal ;
- résultats détaillés versionnés dans `reports/model_metrics.json` et documentés dans `docs/SCIENTIFIC_EVALUATION.md` ;
- CI finale validée ;
- pull request de consolidation fusionnée ;
- création de `main` à partir de l'état final validé.

## Perspectives hors version finale

Les éléments ci-dessous sont des perspectives possibles et **ne font pas partie des travaux nécessaires à la version finale du PFE** :

- classification multi-classe UNSW-NB15 ;
- SHAP local ;
- persistance SQLite multi-exécutions ;
- CICIDS-2018 comme validation externe complémentaire ;
- Docker pour la portabilité de l'environnement.

Ces pistes pourraient prolonger le prototype dans un travail ultérieur, mais elles ne sont pas requises pour atteindre le périmètre actuel.

## Hors périmètre assumé

Restent volontairement hors périmètre : SIEM industriel complet, déploiement Wazuh/Elastic complet, orchestration SOC, réponse automatique, blocage réseau, Kubernetes, architecture microservices et Deep Learning complexe.
