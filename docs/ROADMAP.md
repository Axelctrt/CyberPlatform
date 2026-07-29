# Roadmap Agile

## Sprint 1 - Socle projet et architecture

Objectif : mettre en place une base de projet claire et compatible avec le cahier des charges.

Livrables :

- structure du depot ;
- documentation initiale ;
- schema commun d'evenement de securite ;
- exemple minimal d'evenements ;
- premiers tests unitaires.

Critere de fin :

- le projet est lisible, versionnable et pret pour l'implementation des connecteurs.

## Sprint 2 - Ingestion et normalisation

Objectif : charger des sources simples et les transformer vers le schema commun.

Livrables :

- ingestion CSV ;
- ingestion JSON ;
- logs simules systeme, authentification, cloud et applicatif ;
- validation des champs obligatoires.

Etat actuel :

- connecteurs CSV et JSON ajoutes ;
- normalisation vers `SecurityEvent` ;
- exemples multi-sources dans `data/samples/` ;
- tests unitaires sur chargement, conversion et rejet des formats non supportes.

## Sprint 3 - Pretraitement et baseline ML

Objectif : obtenir un premier modele mesurable sans chercher encore la performance maximale.

Livrables :

- nettoyage des donnees ;
- encodage ;
- split train/test ;
- modele baseline ;
- metriques principales.

Etat actuel :

- conversion des `SecurityEvent` en tableau exploitable par Scikit-learn ;
- separation features / label ;
- separation train/test reproductible ;
- pipeline baseline avec imputation, encodage, normalisation numerique et regression logistique ;
- metriques accuracy, precision, recall et F1-score ;
- tests unitaires sur la preparation et l'entrainement baseline.

## Sprint 4 - Modele principal et priorisation

Objectif : produire des alertes classees et priorisees.

Livrables :

- comparaison baseline / modele principal ;
- sauvegarde du modele ;
- score de risque 0-100 ;
- priorites Low, Medium, High, Critical ;
- export des alertes enrichies.

## Sprint 5 - Dashboard et finalisation

Objectif : rendre la plateforme demonstrable.

Livrables :

- dashboard Streamlit ;
- vues evenements, alertes, metriques ;
- filtres par source et priorite ;
- documentation d'installation et d'utilisation.
