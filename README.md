# CyberPlatform

CyberPlatform est un **prototype académique local et modulaire** de plateforme de cybersécurité intelligente. Il transforme des données de sécurité structurées en événements normalisés, entraîne et évalue des modèles de détection réseau, produit des alertes priorisées et restitue les résultats dans un dashboard Streamlit.

Le périmètre est volontairement limité : le projet **n'est pas un SIEM industriel**, ne remplace pas Wazuh ou Elastic Security, ne réalise pas de réponse automatique et ne prétend pas appliquer un modèle réseau à tous les types de logs.

La branche `main` constitue la **branche stable de référence du PFE**. Les évolutions sont réalisées sur des branches dédiées puis intégrées par pull request après validation.

## Chaîne fonctionnelle

```text
Sources de sécurité
  -> ingestion
  -> normalisation
  -> prétraitement
  -> IA / ML
  -> détection binaire normal / attaque
       -> si attaque détectée : estimation expérimentale de la famille d'attaque
  -> scoring des attaques détectées
  -> alertes
  -> dashboard Streamlit
```

Deux usages sont clairement séparés :

1. **Validation scientifique ML réseau** : UNSW-NB15 -> Logistic Regression + Random Forest -> métriques -> modèles sauvegardés.
2. **Démonstration plateforme multi-source** : réseau, système, authentification, cloud et applicatif -> ingestion/normalisation/visualisation. Les sources non compatibles UNSW-NB15 ne sont pas artificiellement envoyées dans les modèles réseau.

La décision opérationnelle reste **binaire** : `normal / attaque`. Une seconde Random Forest, entraînée uniquement sur les lignes d'attaque d'UNSW-NB15, peut ensuite estimer une famille parmi neuf catégories. Cette classification multiclasses est un **enrichissement expérimental** : elle ne remplace pas le détecteur binaire et sa confiance n'entre pas dans le score de risque.

Lorsque `attack_cat` est présent dans un fichier UNSW-NB15, cette colonne reste la **vérité terrain** utilisée pour l'évaluation. Elle est exclue des variables d'entrée des modèles.

## Fonctionnalités

- ingestion CSV et JSON ;
- ingestion optionnelle Suricata EVE JSON Lines ;
- normalisation vers `SecurityEvent` ;
- prise en charge du dataset UNSW-NB15 ;
- prétraitement Scikit-learn intégré aux pipelines pour limiter les fuites de données ;
- baseline Logistic Regression ;
- Random Forest comme détecteur binaire principal ;
- comparaison reproductible sur le même jeu de test ;
- étude de sensibilité du seuil Random Forest sur une validation issue uniquement du jeu d'entraînement ;
- accuracy, precision, recall, F1, TN, FP, FN, TP, FPR, FNR, ROC-AUC et PR-AUC ;
- matrices de confusion et courbes ROC / Precision-Recall ;
- analyse des décisions binaires par catégorie réelle UNSW-NB15 ;
- Random Forest multiclasses expérimentale pour l'identification conditionnelle des familles d'attaques ;
- balanced accuracy, Macro-F1, Weighted-F1 et métriques par famille pour l'expérience multiclasses ;
- sauvegarde Joblib des modèles ;
- inférence à partir de modèles sauvegardés, sans réentraînement dans Streamlit ;
- prévalidation des fichiers UNSW avant inférence ;
- scoring 0-100 uniquement pour les événements détectés comme attaques ;
- décomposition explicable du score de risque ;
- seuils Low 0-30, Medium 31-60, High 61-80, Critical 81-100 ;
- inspection détaillée et export CSV des alertes ;
- mapping MITRE ATT&CK simplifié et indicatif, sans identifiant fictif ;
- importance globale des variables du Random Forest binaire ;
- tests automatisés et GitHub Actions.

## Architecture du dépôt

```text
CyberPlatform/
├── app/                         # Interface Streamlit
├── data/
│   ├── raw/unsw_nb15/           # Dataset complet local, ignoré par Git
│   ├── processed/               # Données générées, ignorées par Git
│   └── samples/                 # Petits fixtures et démonstrations versionnés
├── docs/                        # Roadmap et documentation scientifique
├── models/                      # Modèles Joblib générés localement
├── reports/                     # Métriques et résultats générés
├── src/cyberplatform/
│   ├── datasets/                # Adaptateurs datasets, dont UNSW-NB15
│   ├── ingestion/               # CSV, JSON, Suricata et normalisation
│   ├── ml/                      # Prétraitement, modèles binaires/multiclasses, métriques et inférence
│   ├── scoring/                 # Score de risque et priorisation
│   ├── threat_intel/            # Mapping MITRE indicatif
│   ├── dashboard.py             # Préparation des données de l'interface
│   ├── schema.py                # Schéma commun SecurityEvent
│   └── training.py              # Pipeline d'entraînement CLI
├── tests/                       # Tests unitaires et d'intégration légère
└── pyproject.toml               # Dépendances et packaging Python
```

## Installation Windows / PowerShell

Python 3.10 ou 3.11 est recommandé.

```powershell
git clone https://github.com/Axelctrt/CyberPlatform.git
cd CyberPlatform
git fetch origin
git switch main

py -3.11 -m venv .venv
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
```

Si le dépôt est déjà présent :

```powershell
git fetch origin
git switch main
git pull --ff-only origin main
```

## Dataset principal : UNSW-NB15

La validation scientifique finale utilise **UNSW-NB15**. Le petit fichier `data/samples/unsw_nb15_sample.csv` sert uniquement aux tests automatisés ; il ne constitue pas le dataset d'évaluation final.

Page officielle du dataset :

`https://research.unsw.edu.au/projects/unsw-nb15-dataset`

Créer le dossier local :

```powershell
New-Item -ItemType Directory -Force data\raw\unsw_nb15
Start-Process "https://research.unsw.edu.au/projects/unsw-nb15-dataset"
```

Télécharger les fichiers CSV d'entraînement et de test avec en-têtes, puis les placer dans :

```text
data/raw/unsw_nb15/UNSW_NB15_training-set.csv
data/raw/unsw_nb15/UNSW_NB15_testing-set.csv
```

Le loader accepte également les variantes de nom avec `_training_set.csv` et `_testing_set.csv`. `data/raw/` est ignoré par Git afin de ne pas versionner le dataset volumineux.

## Entraîner les modèles

L'entraînement est volontairement séparé du dashboard.

```powershell
python -m cyberplatform.training --data-dir data/raw/unsw_nb15
```

Cette commande charge et nettoie UNSW-NB15, exclut `id`, `label` et `attack_cat` des features et conserve le split officiel train/test lorsqu'il est disponible.

Pour la Random Forest binaire, un holdout stratifié de 20 % est extrait **uniquement du jeu d'entraînement** afin d'étudier le seuil de décision. Par défaut, le pipeline recherche le seuil maximisant le F1 parmi ceux respectant `recall >= 0.95`. Le jeu de test officiel n'est jamais utilisé pour sélectionner ce seuil expérimental.

L'expérience finale a proposé un seuil de `0.42` sur ce holdout. Cependant, ce seuil dégrade le F1, la précision et le taux de faux positifs sur le jeu de test officiel. Le seuil opérationnel reste donc **0.50** ; `0.42` est conservé comme résultat d'étude de sensibilité et non comme seuil déployé.

Le même pipeline entraîne également un modèle multiclasses séparé sur les **attaques uniquement**. Les lignes `Normal` sont volontairement exclues de cette seconde tâche : le rôle du modèle est d'identifier une famille après une décision binaire positive, et non de refaire la détection normal/attaque.

Le pipeline sauvegarde :

```text
models/logistic_regression.joblib
models/random_forest.joblib
models/primary_model.joblib
models/attack_family_random_forest.joblib
reports/model_metrics.json
```

`model_metrics.json` contient les métriques binaires finales, l'étude de seuil, les points ROC/PR ainsi que les résultats détaillés de l'expérience multiclasses.

## Résultats scientifiques finaux — détection binaire

La validation binaire utilise le split officiel UNSW-NB15 : **175 341 lignes d'entraînement** et **82 332 lignes de test**.

| Modèle / seuil | Accuracy | Precision | Recall | F1 | FPR | FNR | ROC-AUC | PR-AUC |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Logistic Regression — 0.50 | 83.53 % | 80.20 % | 93.06 % | 86.15 % | 28.14 % | 6.94 % | 95.60 % | 96.66 % |
| **Random Forest — 0.50** | **89.02 %** | **84.78 %** | **97.58 %** | **90.73 %** | **21.46 %** | **2.42 %** | **98.04 %** | **98.38 %** |
| Random Forest — seuil expérimental 0.42 | 87.20 % | 81.86 % | 98.60 % | 89.45 % | 26.78 % | 1.40 % | 98.04 % | 98.38 % |

Matrice de confusion du **Random Forest opérationnel à 0.50** :

```text
TN = 29 058    FP = 7 942
FN =  1 097    TP = 44 235
```

La Random Forest est retenue comme modèle principal : elle améliore nettement le recall, le F1, ROC-AUC et PR-AUC par rapport à la Logistic Regression et réduit le taux de faux négatifs. Le FPR reste néanmoins une limite importante du prototype.

L'étude de seuil montre aussi qu'abaisser le seuil à `0.42` augmente encore le recall, mais au prix de **1 965 faux positifs supplémentaires** par rapport au seuil `0.50`. Le compromis opérationnel à `0.50` est donc conservé.

## Résultats scientifiques — identification des familles d'attaques

L'expérience multiclasses utilise uniquement les lignes d'attaque du split officiel :

- **119 341** attaques pour l'entraînement ;
- **45 332** attaques pour le test ;
- **9 familles** : Analysis, Backdoor, DoS, Exploits, Fuzzers, Generic, Reconnaissance, Shellcode et Worms.

Résultats globaux :

| Métrique | Valeur |
|---|---:|
| Accuracy | 76.13 % |
| Balanced accuracy | 51.41 % |
| Macro-F1 | 51.46 % |
| Weighted-F1 | 78.91 % |

L'écart important entre le **Weighted-F1 (78.91 %)** et le **Macro-F1 (51.46 %)** montre que les performances sont fortement influencées par les classes majoritaires. L'accuracy seule serait donc insuffisante pour juger cette expérience.

| Famille | Precision | Recall | F1 | Support test |
|---|---:|---:|---:|---:|
| Analysis | 3.67 % | 3.99 % | 3.82 % | 677 |
| Backdoor | 3.80 % | 32.76 % | 6.81 % | 583 |
| DoS | 31.55 % | 20.35 % | 24.74 % | 4 089 |
| Exploits | 78.70 % | 67.89 % | 72.89 % | 11 132 |
| Fuzzers | 82.11 % | 76.53 % | 79.22 % | 6 062 |
| Generic | 99.92 % | 96.66 % | 98.26 % | 18 871 |
| Reconnaissance | 93.05 % | 79.23 % | 85.59 % | 3 496 |
| Shellcode | 56.19 % | 64.81 % | 60.20 % | 378 |
| Worms | 69.23 % | 20.45 % | 31.58 % | 44 |

Le modèle est très performant sur `Generic`, et solide sur `Reconnaissance`, `Fuzzers` et `Exploits`. Les résultats sont en revanche faibles sur `Analysis`, `Backdoor` et `DoS`. Le support de `Worms` n'est que de 44 exemples dans le test, ce qui rend son évaluation particulièrement fragile.

Cette hétérogénéité justifie le positionnement retenu : **la classification multiclasses reste un enrichissement expérimental**. Le détecteur binaire conserve la responsabilité de décider si un événement déclenche une alerte et sa probabilité continue d'alimenter le score de risque. Une fausse alerte du détecteur binaire peut par ailleurs recevoir malgré tout une famille, puisque le second modèle est entraîné uniquement sur des attaques ; la famille estimée ne doit donc jamais être interprétée comme une preuve indépendante d'attaque.

## Lancer les tests

```powershell
$env:PYTHONPATH="src"
python -m unittest discover -s tests -v
```

Les tests utilisent des fixtures légères. Ils ne téléchargent pas le dataset UNSW-NB15 complet.

## Lancer le dashboard

```powershell
python -m streamlit run app/streamlit_app.py
```

Le dashboard ne réentraîne aucun modèle. S'il ne trouve pas les modèles ou `reports/model_metrics.json`, il l'indique explicitement.

### Import / analyse

Trois modes sont proposés :

- **UNSW-NB15 compatible (CSV)** : prévisualisation des variables, décision binaire et scoring ; si le modèle multiclasses sauvegardé est disponible, les alertes sont enrichies par une famille estimée et une confiance multiclasses ;
- **CSV / JSON générique** : ingestion et normalisation pour la démonstration multi-source, sans fausse prédiction réseau ;
- **Suricata EVE JSON Lines** : ingestion et contextualisation IDS, sans prétendre que les modèles UNSW-NB15 savent traiter directement ces événements.

Pour un fichier UNSW contenant `attack_cat`, la vue d'ensemble utilise cette colonne uniquement comme vérité terrain pour comparer la décision binaire et, lorsque pertinent, la famille estimée.

### Analyse ML

L'onglet **Analyse ML** présente la comparaison Logistic Regression / Random Forest, la matrice de confusion binaire, l'étude de seuil, les courbes ROC et Precision-Recall, puis une section distincte consacrée à l'expérience multiclasses avec ses métriques globales, ses résultats par famille et sa matrice de confusion.

### Alertes

L'onglet **Alertes** permet de filtrer les alertes détectées, d'en inspecter une individuellement, d'afficher la famille estimée et sa confiance lorsqu'elles sont disponibles, et d'expliquer le score de risque. La confiance multiclasses n'est pas utilisée pour calculer ce score.

## Scoring et priorisation

Le score combine, à titre de règle métier de prototype : confiance du détecteur binaire 60 %, sévérité 25 % et criticité simple du type de source 15 %.

Un événement pour lequel aucune attaque n'est détectée (`prediction == 0`) conserve sa confiance binaire mais ne reçoit **ni `risk_score`, ni `priority`**. Le scoring opérationnel s'applique uniquement aux alertes détectées.

| Score | Priorité |
|---:|---|
| 0 à 30 | Low |
| 31 à 60 | Medium |
| 61 à 80 | High |
| 81 à 100 | Critical |

Ces coefficients et seuils sont des hypothèses explicites du prototype, pas une norme universelle de risque.

## MITRE ATT&CK

Le mapping est **simplifié et indicatif**. Il n'est appliqué qu'aux événements détectés comme suspects ou aux alertes natives Suricata. Une famille estimée par le modèle multiclasses peut contribuer au contexte, mais elle reste expérimentale et ne transforme pas le mapping en attribution certaine d'une technique.

Un événement non mappé reçoit `technique_id = None` et `technique_name = "Non mappé"`. Aucun pseudo-identifiant comme `T0000` n'est utilisé.

## Stockage retenu

Le prototype reste volontairement léger : données brutes en fichiers hors Git, fixtures CSV/JSON versionnées, modèles Joblib, métriques JSON et alertes en DataFrame avec export CSV. SQLite n'est pas imposé : il reste une perspective éventuelle si la persistance multi-exécutions devenait nécessaire.

## Limites assumées

- prototype académique local, non SIEM de production ;
- validation ML principalement sur un dataset réseau public ;
- généralisation à un réseau réel non démontrée par UNSW-NB15 seul ;
- sources système/authentification/cloud/applicatives utilisées surtout pour démontrer ingestion, normalisation et restitution ;
- FPR du détecteur binaire encore significatif ;
- performances multiclasses très inégales selon les familles ;
- classes minoritaires particulièrement difficiles à évaluer et à reconnaître ;
- toute fausse alerte binaire envoyée au modèle multiclasses reçoit nécessairement une estimation parmi les neuf familles ;
- le seuil expérimental binaire `0.42` ne généralise pas suffisamment pour remplacer automatiquement `0.50` ;
- pas de réponse automatique, blocage réseau ou orchestration SOC ;
- pas de Wazuh/Elastic complet ;
- pas de Deep Learning obligatoire.

## Perspectives hors version finale

Les pistes suivantes restent volontairement hors du périmètre final : calibration/rejet explicite des prédictions multiclasses incertaines, SHAP local, persistance SQLite, validation externe sur CICIDS-2018 et conteneurisation Docker.

## Documentation scientifique

Le protocole complet, l'interprétation des métriques binaires et multiclasses, les limites et la reproductibilité sont détaillés dans `docs/SCIENTIFIC_EVALUATION.md`.

## Méthode projet

Le développement suit une **approche Agile incrémentale pilotée par Kanban**. Chaque incrément doit être fonctionnel, testé, documenté et traçable par commit. La roadmap détaillée et l'historique de consolidation sont disponibles dans `docs/ROADMAP.md`.
