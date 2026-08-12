# CyberPlatform

Prototype local de plateforme cyber IA pour l'ingestion, la normalisation, la detection et la priorisation d'evenements de securite.

Ce projet suit une progression Agile en plusieurs sprints afin de construire une plateforme demonstrable sans aller trop vite dans l'implementation.

## Objectif

CyberPlatform vise a transformer des donnees de securite heterogenes en alertes exploitables par un analyste :

- ingestion de sources CSV, JSON ou logs simules ;
- normalisation vers un schema commun ;
- preparation des donnees pour des modeles de Machine Learning ;
- detection binaire normal / attaque ;
- scoring de criticite et priorisation ;
- restitution dans un dashboard Streamlit.

## Roadmap courte

1. Socle projet, architecture et schema commun.
2. Ingestion et normalisation des premieres sources.
3. Pretraitement et premier modele baseline.
4. Modele principal, scoring et alertes enrichies.
5. Dashboard Streamlit, documentation et finalisation.

## Structure initiale

```text
CyberPlatform/
  app/                  # Future interface Streamlit
  data/
    samples/            # Petits jeux de donnees de demonstration
  docs/                 # Notes projet et suivi Agile
  models/               # Modeles entraines sauvegardes localement
  notebooks/            # Analyses exploratoires
  src/cyberplatform/    # Code applicatif
  tests/                # Tests automatises
```

## Lancement des tests

```powershell
$env:PYTHONPATH='src'
python -m unittest discover -s tests
```

## Sprint 2 - Ingestion et normalisation

Le projet contient maintenant deux connecteurs simples :

- chargement de fichiers JSON ;
- chargement de fichiers CSV.

Les enregistrements bruts sont transformes en objets `SecurityEvent` afin de conserver un schema commun avant le futur pretraitement Machine Learning.

## Sprint 3 - Pretraitement et baseline ML

Le projet contient une premiere chaine Machine Learning volontairement simple :

- conversion des evenements normalises en tableau de features ;
- separation features / label ;
- separation train/test reproductible ;
- detection binaire normale / attaque avec une regression logistique ;
- calcul des premieres metriques : accuracy, precision, recall et F1-score.

Cette baseline sert de point de comparaison avant l'ajout d'un modele principal plus performant.

## Sprint 4 - Modele principal et priorisation

Le projet contient maintenant une premiere logique de detection exploitable :

- entrainement d'un modele principal Random Forest ;
- comparaison entre baseline et modele principal ;
- sauvegarde et rechargement de modeles entraines ;
- calcul d'un score de risque de 0 a 100 ;
- attribution d'une priorite Low, Medium, High ou Critical ;
- export CSV des alertes enrichies.

## Sprint 5 - Dashboard et finalisation

Le projet contient une premiere interface Streamlit :

- vue de synthese des evenements et alertes ;
- filtres par priorite et source ;
- graphiques de repartition ;
- tableau des alertes priorisees ;
- comparaison des metriques baseline / modele principal ;
- tableau des evenements normalises et enrichis.

## Lancement du dashboard

```powershell
$env:PYTHONPATH='src'
python -m streamlit run app/streamlit_app.py
```

## Sprint 6 optionnel - Contexte cyber

Le projet contient des extensions optionnelles utiles pour la demonstration :

- ingestion d'un exemple Suricata EVE JSON Lines ;
- mapping MITRE ATT&CK simplifie pour contextualiser les alertes ;
- importance des variables du modele Random Forest ;
- onglet dashboard dedie au contexte menace.
