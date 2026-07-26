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

