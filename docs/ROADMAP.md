# Roadmap Agile incrémentale pilotée par Kanban

## Statut de la version finale

La consolidation principale du projet est terminée. La branche `main` constitue la **branche stable de référence du PFE**.

Les branches historiques de développement restent utiles pour la traçabilité, mais elles ne représentent plus l'état de référence du projet. Toute évolution doit partir de `main`, être développée sur une branche dédiée, testée puis intégrée par pull request.

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

## Phase de consolidation principale — Terminée

La consolidation a été développée sur `final-ml-platform-consolidation`, validée par tests automatisés et expérimentation complète sur UNSW-NB15, puis fusionnée dans `threat-context-extensions`. L'état validé a ensuite servi de base à la branche stable `main`.

### Lot C1 — Dataset scientifique UNSW-NB15 — Terminé
- adaptateur dédié ; nettoyage défensif ; séparation labels/features ; exclusion de `id`, `label`, `attack_cat` ; split officiel ou repli stratifié reproductible ; option Windows de limitation de lignes.

### Lot C2 — Entraînement / inférence / métriques — Terminé
- CLI d'entraînement séparée de Streamlit ; Logistic Regression + Random Forest ; TN/FP/FN/TP/FPR/FNR ; ROC-AUC / PR-AUC ; matrice de confusion ; Joblib ; rapport JSON ; validation des features d'inférence.

### Lot C3 — Scoring / dashboard / contexte menace — Terminé
- aucun score/priorité sur un événement normal ; seuils 0-30 / 31-60 / 61-80 / 81-100 ; High/Critical parmi les alertes uniquement ; import CSV/JSON/UNSW/Suricata ; export CSV ; modèle sauvegardé ; MITRE sans `T0000` ; distinction ML réseau / multi-source.

### Lot C4 — Tests / CI — Terminé
- fixture UNSW-NB15 légère ; tests schéma, ingestion, dataset, ML, métriques, scoring, dashboard, MITRE et entraînement ; GitHub Actions sans dataset complet.

### Lot C5 — Documentation / validation scientifique — Terminé
- README Windows ; installation, dataset, entraînement, tests et dashboard ; résultats scientifiques ; limites du prototype ; architecture ; stockage léger ; documentation scientifique dédiée ; rapport `reports/model_metrics.json` versionné.

### Lot C6 — Améliorations finales du binaire — Terminé
- étude de sensibilité du seuil Random Forest ; maintien du seuil opérationnel `0.50` après vérification de généralisation ; courbes ROC et Precision-Recall ; analyse des erreurs par catégorie réelle UNSW-NB15 ; prévalidation des fichiers avant inférence ; inspection détaillée des alertes ; décomposition du score de risque.

## Extension finale dans le périmètre — Classification des familles

Branche de développement : `multiclass-attack-family`.

### Lot C7 — Multiclassification UNSW-NB15 — Validé expérimentalement

Objectif : compléter la détection binaire par une estimation de la famille d'attaque sans modifier le rôle du détecteur principal.

Réalisations :

- seconde Random Forest dédiée aux familles d'attaques ;
- entraînement uniquement sur les lignes `label == 1` ;
- `attack_cat` utilisée uniquement comme cible/vérité terrain et exclue des features ;
- neuf familles : Analysis, Backdoor, DoS, Exploits, Fuzzers, Generic, Reconnaissance, Shellcode et Worms ;
- `class_weight="balanced_subsample"` ;
- modèle sauvegardé séparément dans `models/attack_family_random_forest.joblib` ;
- accuracy, balanced accuracy, Macro-F1, Weighted-F1, métriques par classe et matrice de confusion ;
- enrichissement des alertes binaires par une famille estimée et une confiance multiclasses ;
- aucune utilisation de la confiance multiclasses dans le score de risque ;
- tests dédiés et CI validée.

Validation sur le split officiel, attaques uniquement :

- entraînement : **119 341** lignes ;
- test : **45 332** lignes ;
- accuracy : **76.13 %** ;
- balanced accuracy : **51.41 %** ;
- Macro-F1 : **51.46 %** ;
- Weighted-F1 : **78.91 %**.

Interprétation : les performances sont fortes sur `Generic`, `Reconnaissance`, `Fuzzers` et `Exploits`, mais faibles sur `Analysis`, `Backdoor` et `DoS`. `Worms` ne dispose que de 44 exemples de test. L'écart important entre Macro-F1 et Weighted-F1 confirme que le déséquilibre des classes reste une limite majeure.

Décision : la multiclassification est **conservée comme enrichissement expérimental**. La Random Forest binaire à seuil `0.50` reste la décision opérationnelle qui déclenche le scoring et la priorisation.

## Validation finale attendue avant fusion de C7

- résultats complets régénérés localement sur le dataset officiel : effectué ;
- CI de la branche : validée ;
- documentation technique et scientifique : mise à jour ;
- `reports/model_metrics.json` régénéré avec les résultats multiclasses : à versionner depuis l'environnement local ;
- pull request vers `main` : ouverte en draft jusqu'à versionnement du rapport final et dernière revue.

## Perspectives hors version finale

Les éléments ci-dessous restent des perspectives possibles et **ne sont pas nécessaires au périmètre final du PFE** :

- mécanisme de rejet/calibration pour les prédictions multiclasses incertaines ;
- SHAP local ;
- persistance SQLite multi-exécutions ;
- CICIDS-2018 comme validation externe complémentaire ;
- Docker pour la portabilité de l'environnement.

## Hors périmètre assumé

Restent volontairement hors périmètre : SIEM industriel complet, déploiement Wazuh/Elastic complet, orchestration SOC, réponse automatique, blocage réseau, Kubernetes, architecture microservices et Deep Learning complexe.
