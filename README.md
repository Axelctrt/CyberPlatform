# CyberPlatform

CyberPlatform est un **prototype académique local et modulaire** de plateforme de cybersécurité intelligente. Il transforme des données de sécurité structurées en événements normalisés, entraîne et évalue des modèles de détection réseau, produit des alertes priorisées et restitue les résultats dans un dashboard Streamlit.

Le périmètre est volontairement limité : le projet **n'est pas un SIEM industriel**, ne remplace pas Wazuh ou Elastic Security, ne réalise pas de réponse automatique et ne prétend pas appliquer un modèle réseau à tous les types de logs.

## Chaîne fonctionnelle

```text
Sources de sécurité
  -> ingestion
  -> normalisation
  -> prétraitement
  -> IA / ML
  -> détection binaire normal / attaque
  -> scoring des attaques détectées
  -> alertes
  -> dashboard Streamlit
```

Deux usages sont clairement séparés :

1. **Validation scientifique ML réseau** : UNSW-NB15 -> Logistic Regression + Random Forest -> métriques -> modèle sauvegardé.
2. **Démonstration plateforme multi-source** : réseau, système, authentification, cloud et applicatif -> ingestion/normalisation/visualisation. Les sources non compatibles UNSW-NB15 ne sont pas artificiellement envoyées dans le modèle réseau.

La chaîne ML déployée reste **binaire**. Si un fichier UNSW-NB15 contient `attack_cat`, cette colonne est considérée comme une vérité terrain / information de contexte éventuelle et **jamais comme une classe prédite par le modèle binaire**.

## Fonctionnalités

- ingestion CSV et JSON ;
- ingestion optionnelle Suricata EVE JSON Lines ;
- normalisation vers `SecurityEvent` ;
- prise en charge du dataset UNSW-NB15 ;
- prétraitement Scikit-learn intégré aux pipelines pour limiter les fuites de données ;
- baseline Logistic Regression ;
- modèle principal Random Forest ;
- comparaison reproductible sur le même jeu de test ;
- étude de sensibilité du seuil Random Forest sur une validation issue uniquement du jeu d'entraînement ;
- accuracy, precision, recall, F1, TN, FP, FN, TP, FPR, FNR, ROC-AUC et PR-AUC ;
- matrice de confusion ;
- courbes ROC et Precision-Recall ;
- analyse des décisions par catégorie réelle UNSW-NB15, sans fausse classification multi-classe ;
- sauvegarde Joblib des modèles ;
- inférence à partir d'un modèle sauvegardé, sans réentraînement dans Streamlit ;
- prévalidation des fichiers UNSW avant inférence ;
- scoring 0-100 uniquement pour les événements détectés comme attaques ;
- décomposition explicable du score de risque ;
- seuils Low 0-30, Medium 31-60, High 61-80, Critical 81-100 ;
- inspection détaillée et export CSV des alertes ;
- mapping MITRE ATT&CK simplifié et indicatif, sans identifiant fictif ;
- importance globale des variables du Random Forest ;
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
│   ├── ml/                      # Prétraitement, modèles, métriques, seuil, inférence
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
git switch final-ml-platform-consolidation

py -3.11 -m venv .venv
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
```

Si le dépôt est déjà présent :

```powershell
git fetch origin
git switch final-ml-platform-consolidation
git pull --ff-only origin final-ml-platform-consolidation
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

Pour la Random Forest, un holdout stratifié de 20 % est extrait **uniquement du jeu d'entraînement** afin d'étudier le seuil de décision. Par défaut, le pipeline recherche le seuil maximisant le F1 parmi ceux respectant `recall >= 0.95`. Le jeu de test officiel n'est jamais utilisé pour sélectionner ce seuil expérimental.

L'expérience finale a proposé un seuil de `0.42` sur ce holdout. Cependant, ce seuil dégrade le F1, la précision et le taux de faux positifs sur le jeu de test officiel. Le seuil opérationnel reste donc **0.50** ; `0.42` est conservé comme résultat d'étude de sensibilité et non comme seuil déployé.

Le pipeline sauvegarde :

```text
models/logistic_regression.joblib
models/random_forest.joblib
models/primary_model.joblib
reports/model_metrics.json
```

`model_metrics.json` contient les métriques finales, le seuil opérationnel, le seuil expérimental, les résultats de validation et les points nécessaires aux courbes ROC et Precision-Recall.

## Résultats scientifiques finaux

La validation finale utilise le split officiel UNSW-NB15 : **175 341 lignes d'entraînement** et **82 332 lignes de test**.

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

La Random Forest est retenue comme modèle principal : elle améliore nettement le recall, le F1, ROC-AUC et PR-AUC par rapport à la Logistic Regression et réduit le taux de faux négatifs. Le FPR reste néanmoins une limite importante du prototype et doit être discuté dans le rapport.

L'étude de seuil montre aussi qu'abaisser le seuil à `0.42` augmente encore le recall, mais au prix de **1 965 faux positifs supplémentaires** par rapport au seuil `0.50`. Le compromis opérationnel à `0.50` est donc conservé.

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

Le dashboard ne réentraîne aucun modèle. S'il ne trouve pas `models/primary_model.joblib` ou `reports/model_metrics.json`, il l'indique explicitement.

### Import / analyse

Trois modes sont proposés :

- **UNSW-NB15 compatible (CSV)** : prévisualisation du nombre de lignes et des variables, contrôle des features attendues, chargement du modèle Joblib, application du seuil sauvegardé, décision binaire et scoring ;
- **CSV / JSON générique** : ingestion et normalisation pour la démonstration multi-source, sans fausse prédiction réseau ;
- **Suricata EVE JSON Lines** : ingestion et contextualisation IDS, sans prétendre que le modèle UNSW-NB15 sait traiter directement ces événements.

Pour un fichier UNSW contenant `attack_cat`, la vue d'ensemble compare les décisions binaires du modèle aux catégories réelles et permet d'étudier les faux positifs, faux négatifs et taux de détection par famille réelle.

### Analyse ML

L'onglet **Analyse ML** présente la comparaison Logistic Regression / Random Forest, la matrice de confusion, le seuil opérationnel, l'expérience de seuil et les courbes ROC et Precision-Recall.

### Alertes

L'onglet **Alertes** permet de filtrer les alertes détectées, d'en inspecter une individuellement et d'expliquer son score de risque par ses trois contributions : confiance ML, sévérité et criticité de la source.

## Scoring et priorisation

Le score combine, à titre de règle métier de prototype : confiance du modèle 60 %, sévérité 25 % et criticité simple du type de source 15 %.

Un événement pour lequel aucune attaque n'est détectée (`prediction == 0`) conserve sa confiance ML mais ne reçoit **ni `risk_score`, ni `priority`**. Le scoring opérationnel s'applique uniquement aux alertes détectées.

| Score | Priorité |
|---:|---|
| 0 à 30 | Low |
| 31 à 60 | Medium |
| 61 à 80 | High |
| 81 à 100 | Critical |

Ces coefficients et seuils sont des hypothèses explicites du prototype, pas une norme universelle de risque.

## MITRE ATT&CK

Le mapping est **simplifié et indicatif**. Il n'est appliqué qu'aux événements détectés comme suspects ou aux alertes natives Suricata. L'ordre de contextualisation est : type/catégorie d'attaque explicitement fournie, catégorie connue du dataset lorsqu'elle existe comme contexte, catégorie Suricata, type d'événement, puis aucune correspondance.

Un événement non mappé reçoit `technique_id = None` et `technique_name = "Non mappé"`. Aucun pseudo-identifiant comme `T0000` n'est utilisé.

## Stockage retenu

Le prototype reste volontairement léger : données brutes en fichiers hors Git, fixtures CSV/JSON versionnées, modèles Joblib, métriques JSON et alertes en DataFrame avec export CSV. SQLite n'est pas imposé : il reste une extension si la persistance multi-exécutions devient utile à la démonstration.

## Limites assumées

- prototype académique local, non SIEM de production ;
- validation ML principalement sur un dataset réseau public ;
- généralisation à un réseau réel non démontrée par UNSW-NB15 seul ;
- sources système/authentification/cloud/applicatives utilisées surtout pour démontrer ingestion, normalisation et restitution ;
- classification multi-classe non implémentée dans la consolidation binaire ;
- `attack_cat` d'UNSW-NB15 est une vérité terrain/contexte, pas une sortie du classifieur binaire ;
- le FPR du modèle principal reste significatif et constitue une limite opérationnelle ;
- le seuil expérimental optimisé sur validation ne généralise pas suffisamment pour remplacer automatiquement le seuil 0.50 ;
- pas de réponse automatique, blocage réseau ou orchestration SOC ;
- pas de Wazuh/Elastic complet ;
- pas de Deep Learning obligatoire ;
- SHAP reste une extension après stabilisation du binaire.

## Documentation scientifique

Le protocole de sélection de seuil, l'interprétation des courbes, l'analyse d'erreurs et la prévalidation des imports sont détaillés dans `docs/SCIENTIFIC_EVALUATION.md`.

## Méthode projet

Le développement suit une **approche Agile incrémentale pilotée par Kanban**. Chaque incrément doit être fonctionnel, testé, documenté et traçable par commit. La roadmap détaillée est disponible dans `docs/ROADMAP.md`.
