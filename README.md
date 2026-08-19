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

## Fonctionnalités

- ingestion CSV et JSON ;
- ingestion optionnelle Suricata EVE JSON Lines ;
- normalisation vers `SecurityEvent` ;
- prise en charge du dataset UNSW-NB15 ;
- prétraitement Scikit-learn intégré aux pipelines pour limiter les fuites de données ;
- baseline Logistic Regression ;
- modèle principal candidat Random Forest ;
- comparaison reproductible sur le même jeu de test ;
- accuracy, precision, recall, F1, TN, FP, FN, TP, FPR, FNR, ROC-AUC et PR-AUC ;
- matrice de confusion ;
- sauvegarde Joblib des modèles ;
- inférence à partir d'un modèle sauvegardé, sans réentraînement dans Streamlit ;
- scoring 0-100 uniquement pour les événements détectés comme attaques ;
- seuils Low 0-30, Medium 31-60, High 61-80, Critical 81-100 ;
- export CSV des alertes ;
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
├── docs/                        # Roadmap Agile / Kanban
├── models/                      # Modèles Joblib générés localement
├── reports/                     # Métriques et résultats générés
├── src/cyberplatform/
│   ├── datasets/                # Adaptateurs datasets, dont UNSW-NB15
│   ├── ingestion/               # CSV, JSON, Suricata et normalisation
│   ├── ml/                      # Prétraitement, modèles, métriques, inférence
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

Exemple de copie depuis le dossier Téléchargements Windows :

```powershell
Copy-Item "$env:USERPROFILE\Downloads\UNSW_NB15_training-set.csv" "data\raw\unsw_nb15\"
Copy-Item "$env:USERPROFILE\Downloads\UNSW_NB15_testing-set.csv" "data\raw\unsw_nb15\"
```

## Entraîner les modèles

L'entraînement est volontairement séparé du dashboard.

```powershell
python -m cyberplatform.training --data-dir data/raw/unsw_nb15
```

Cette commande :

- charge et nettoie UNSW-NB15 ;
- exclut `id`, `label` et `attack_cat` des features ;
- conserve le split officiel train/test lorsqu'il est disponible ;
- entraîne Logistic Regression et Random Forest ;
- calcule les métriques cyber ;
- sauvegarde `models/logistic_regression.joblib` ;
- sauvegarde `models/random_forest.joblib` ;
- sauvegarde le modèle sélectionné sous `models/primary_model.joblib` ;
- écrit `reports/model_metrics.json`.

Pour un essai limité en mémoire sous Windows :

```powershell
python -m cyberplatform.training --data-dir data/raw/unsw_nb15 --max-rows-per-file 50000
```

Cette option est destinée aux essais techniques. Les résultats présentés dans le rapport final doivent préciser exactement la volumétrie réellement utilisée.

## Lancer les tests

```powershell
$env:PYTHONPATH="src"
python -m unittest discover -s tests -v
```

Les tests utilisent des fixtures légères. Ils ne téléchargent pas le dataset UNSW-NB15 complet.

## Lancer le dashboard

Après installation :

```powershell
python -m streamlit run app/streamlit_app.py
```

Le dashboard ne réentraîne aucun modèle. S'il ne trouve pas `models/primary_model.joblib` ou `reports/model_metrics.json`, il l'indique explicitement.

### Import / analyse

Trois modes sont proposés :

- **UNSW-NB15 compatible (CSV)** : vérification des features attendues, chargement du modèle Joblib, prédiction et scoring ;
- **CSV / JSON générique** : ingestion et normalisation pour la démonstration multi-source, sans fausse prédiction réseau ;
- **Suricata EVE JSON Lines** : ingestion et contextualisation IDS, sans prétendre que le modèle UNSW-NB15 sait traiter directement ces événements.

## Scoring et priorisation

Le score combine, à titre de règle métier de prototype :

- confiance du modèle : 60 % ;
- sévérité : 25 % ;
- criticité simple du type de source : 15 %.

Un événement prédit normal (`prediction == 0`) conserve sa confiance ML mais ne reçoit **ni `risk_score`, ni `priority`**. Le scoring opérationnel s'applique uniquement aux alertes détectées.

Seuils :

| Score | Priorité |
|---:|---|
| 0 à 30 | Low |
| 31 à 60 | Medium |
| 61 à 80 | High |
| 81 à 100 | Critical |

Ces coefficients et seuils sont des hypothèses explicites du prototype, pas une norme universelle de risque.

## MITRE ATT&CK

Le mapping est **simplifié et indicatif**. Il n'est appliqué qu'aux événements détectés comme suspects ou aux alertes natives Suricata. L'ordre de contextualisation est :

1. catégorie d'attaque connue ;
2. catégorie Suricata ;
3. type d'événement ;
4. aucune correspondance.

Un événement non mappé reçoit `technique_id = None` et `technique_name = "Non mappé"`. Aucun pseudo-identifiant comme `T0000` n'est utilisé.

## Stockage retenu

Le prototype reste volontairement léger :

- données brutes : fichiers hors Git ;
- fixtures : CSV / JSON versionnés ;
- modèles : Joblib ;
- métriques : JSON ;
- alertes : DataFrame + export CSV.

SQLite n'est pas imposé dans cette version : il n'apporterait pas de valeur suffisante tant que la persistance multi-exécutions n'est pas un besoin de démonstration. Il reste une extension possible.

## Limites assumées

- prototype académique local, non SIEM de production ;
- validation ML principalement sur un dataset réseau public ;
- généralisation à un réseau réel non démontrée par UNSW-NB15 seul ;
- sources système/authentification/cloud/applicatives utilisées surtout pour démontrer ingestion, normalisation et restitution ;
- pas de réponse automatique, blocage réseau ou orchestration SOC ;
- pas de Wazuh/Elastic complet ;
- pas de Deep Learning obligatoire ;
- classification multi-classe et SHAP restent des extensions après stabilisation du binaire.

## Méthode projet

Le développement suit une **approche Agile incrémentale pilotée par Kanban**. Chaque incrément doit être fonctionnel, testé, documenté et traçable par commit. La roadmap détaillée est disponible dans `docs/ROADMAP.md`.
