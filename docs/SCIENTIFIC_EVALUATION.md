# Évaluation scientifique et interprétation du modèle

Ce document complète le README et décrit les améliorations d'évaluation ajoutées au prototype CyberPlatform sans élargir son périmètre fonctionnel. La plateforme reste un prototype académique local de détection binaire `normal / attaque`, validé principalement sur UNSW-NB15.

## 1. Sélection du seuil de décision

La Random Forest produit une probabilité d'attaque. Le seuil de décision n'est plus supposé arbitrairement égal à `0.5` pour l'expérience finale.

Le pipeline :

1. conserve le split officiel UNSW-NB15 `training / testing` ;
2. extrait un holdout stratifié de 20 % **uniquement depuis le jeu d'entraînement officiel** ;
3. entraîne une Random Forest provisoire sur les 80 % restants ;
4. teste des seuils de `0.10` à `0.90` ;
5. retient le seuil maximisant le F1 parmi ceux respectant par défaut `recall >= 0.95` ;
6. réentraîne les modèles finaux sur l'ensemble du jeu d'entraînement officiel ;
7. évalue une seule fois les performances finales sur le jeu de test officiel.

Le jeu de test officiel n'est donc jamais utilisé pour choisir le seuil.

La contrainte de recall peut être modifiée :

```powershell
python -m cyberplatform.training --data-dir data/raw/unsw_nb15 --minimum-recall 0.95
```

Le seuil sélectionné et les métriques de validation sont enregistrés dans `reports/model_metrics.json`.

## 2. Courbes ROC et Precision-Recall

Le rapport d'entraînement contient des points de courbe ROC et Precision-Recall pour Logistic Regression et Random Forest. Le dashboard les affiche dans l'onglet **Analyse ML**.

Ces courbes sont calculées sur le jeu de test officiel à des fins de comparaison scientifique des modèles. Elles ne servent pas à choisir le seuil de décision.

Les métriques globales restent également disponibles : accuracy, precision, recall, F1, TN, FP, FN, TP, FPR, FNR, ROC-AUC et PR-AUC.

## 3. Analyse des erreurs par catégorie UNSW-NB15

Le modèle final reste strictement binaire. Il ne prédit pas `DoS`, `Exploits`, `Generic`, `Reconnaissance`, etc.

Lorsque `attack_cat` est présent dans un fichier UNSW-NB15 importé, la plateforme l'utilise uniquement comme **vérité terrain** pour analyser les décisions binaires du modèle. Le dashboard peut ainsi afficher, pour chaque catégorie réelle :

- le nombre d'événements ;
- le nombre d'attaques détectées ;
- le nombre d'événements pour lesquels aucune attaque n'a été détectée ;
- le taux de détection pour les catégories d'attaque ;
- le taux de faux positifs pour la catégorie `Normal`.

Cette analyse permet d'étudier les limites du détecteur sans présenter artificiellement le modèle comme un classifieur multi-classe.

## 4. Explication du score de risque

Le score de risque reste une règle métier explicite du prototype :

- confiance ML : maximum 60 points ;
- sévérité : maximum 25 points ;
- criticité du type de source : maximum 15 points.

Dans l'onglet **Alertes**, une alerte peut être inspectée individuellement. La contribution de chaque composante est affichée afin que le score ne soit pas une valeur opaque.

Cette explicabilité concerne le **scoring opérationnel**. Elle ne remplace pas l'importance globale des variables de la Random Forest affichée dans l'onglet **Explicabilité**.

## 5. Validation avant inférence

Avant d'analyser un CSV en mode UNSW-NB15, le dashboard vérifie sa compatibilité avec les variables réellement attendues par le modèle sauvegardé.

La prévisualisation indique :

- le nombre de lignes ;
- le nombre de variables requises ;
- le nombre de variables reconnues ;
- la présence éventuelle de `label` et `attack_cat` ;
- les variables manquantes si le fichier n'est pas compatible.

Le bouton d'analyse ML reste désactivé tant que les variables obligatoires sont absentes.

## Reproductibilité

Après toute modification de la logique d'entraînement, le rapport scientifique doit être régénéré sur le dataset complet :

```powershell
python -m cyberplatform.training --data-dir data/raw/unsw_nb15
```

Puis les tests doivent être exécutés :

```powershell
$env:PYTHONPATH="src"
python -m unittest discover -s tests -v
```

Enfin, le dashboard peut être relancé :

```powershell
python -m streamlit run app/streamlit_app.py
```
