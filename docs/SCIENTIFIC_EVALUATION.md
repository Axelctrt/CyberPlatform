# Évaluation scientifique et interprétation du modèle

Ce document complète le README et décrit les évaluations réalisées sur le prototype CyberPlatform. La plateforme reste centrée sur une détection binaire `normal / attaque`, enrichie par une expérimentation multiclasses conditionnelle sur les événements d'attaque UNSW-NB15.

## 1. Protocole de seuil de décision binaire

La Random Forest produit une probabilité d'attaque. Le seuil opérationnel est fixé à `0.50`, mais une étude de sensibilité est réalisée afin de vérifier si un autre seuil améliore réellement le compromis de détection.

Le pipeline :

1. conserve le split officiel UNSW-NB15 `training / testing` ;
2. extrait un holdout stratifié de 20 % **uniquement depuis le jeu d'entraînement officiel** ;
3. entraîne une Random Forest provisoire sur les 80 % restants ;
4. teste des seuils de `0.10` à `0.90` ;
5. retient, pour l'expérience, le seuil maximisant le F1 parmi ceux respectant par défaut `recall >= 0.95` ;
6. réentraîne les modèles finaux sur l'ensemble du jeu d'entraînement officiel ;
7. évalue le seuil opérationnel `0.50` et le seuil expérimental sur le jeu de test officiel ;
8. conserve le seuil expérimental uniquement s'il apporte un compromis réellement meilleur.

Le jeu de test officiel n'est jamais utilisé pour **choisir** le seuil expérimental. Il sert uniquement à mesurer sa capacité de généralisation après sélection sur le holdout du train.

La contrainte de recall peut être modifiée :

```powershell
python -m cyberplatform.training --data-dir data/raw/unsw_nb15 --minimum-recall 0.95
```

## 2. Résultat de l'étude de seuil

Le holdout de validation contient **35 069 lignes**. La procédure a sélectionné un seuil expérimental de `0.42`.

Sur cette validation interne :

| Seuil 0.42 — validation train | Valeur |
|---|---:|
| Precision | 96.46 % |
| Recall | 97.65 % |
| F1 | 97.05 % |
| FPR | 7.63 % |
| FNR | 2.35 % |
| TN | 10 345 |
| FP | 855 |
| FN | 561 |
| TP | 23 308 |

Ce résultat est très bon sur le holdout, mais il ne suffit pas à justifier le déploiement du seuil. Il faut vérifier sa généralisation sur le jeu de test officiel.

## 3. Évaluation finale de la détection binaire

La validation finale utilise :

- **175 341** lignes d'entraînement ;
- **82 332** lignes de test ;
- le split officiel UNSW-NB15 ;
- `attack_cat`, `label` et `id` exclus des variables ML lorsque présents.

### Logistic Regression — baseline, seuil 0.50

| Métrique | Valeur |
|---|---:|
| Accuracy | 83.53 % |
| Precision | 80.20 % |
| Recall | 93.06 % |
| F1 | 86.15 % |
| FPR | 28.14 % |
| FNR | 6.94 % |
| ROC-AUC | 95.60 % |
| PR-AUC | 96.66 % |

Matrice de confusion :

```text
TN = 26 588    FP = 10 412
FN =  3 148    TP = 42 184
```

### Random Forest — seuil opérationnel 0.50

| Métrique | Valeur |
|---|---:|
| Accuracy | 89.02 % |
| Precision | 84.78 % |
| Recall | 97.58 % |
| F1 | 90.73 % |
| FPR | 21.46 % |
| FNR | 2.42 % |
| ROC-AUC | 98.04 % |
| PR-AUC | 98.38 % |

Matrice de confusion :

```text
TN = 29 058    FP = 7 942
FN =  1 097    TP = 44 235
```

### Random Forest — seuil expérimental 0.42

| Métrique | Valeur |
|---|---:|
| Accuracy | 87.20 % |
| Precision | 81.86 % |
| Recall | 98.60 % |
| F1 | 89.45 % |
| FPR | 26.78 % |
| FNR | 1.40 % |
| ROC-AUC | 98.04 % |
| PR-AUC | 98.38 % |

Matrice de confusion :

```text
TN = 27 093    FP = 9 907
FN =    633    TP = 44 699
```

Le seuil `0.42` détecte **464 attaques supplémentaires** par rapport au seuil `0.50`, mais génère également **1 965 faux positifs supplémentaires**. Il améliore donc le recall et le FNR, mais dégrade la precision, le F1, l'accuracy et le FPR.

**Conclusion : le seuil opérationnel `0.50` est conservé.** Le seuil `0.42` reste documenté comme expérience de sensibilité.

## 4. Choix du modèle binaire principal

La Random Forest est retenue comme modèle principal face à la Logistic Regression. À seuil opérationnel `0.50`, elle présente notamment :

- un recall de **97.58 %** contre **93.06 %** ;
- un F1 de **90.73 %** contre **86.15 %** ;
- un FPR de **21.46 %** contre **28.14 %** ;
- un FNR de **2.42 %** contre **6.94 %** ;
- un ROC-AUC de **98.04 %** contre **95.60 %** ;
- un PR-AUC de **98.38 %** contre **96.66 %**.

Le taux de faux positifs reste cependant significatif. Il constitue une limite opérationnelle importante du prototype et doit être explicitement discuté plutôt que masqué par l'accuracy globale.

## 5. Courbes ROC et Precision-Recall

Le rapport d'entraînement contient des points de courbe ROC et Precision-Recall pour Logistic Regression et Random Forest. Le dashboard les affiche dans l'onglet **Analyse ML**.

Ces courbes sont calculées sur le jeu de test officiel à des fins de comparaison scientifique des modèles. Elles ne servent pas à choisir le seuil de décision. Les AUC ne changent donc pas entre `0.50` et `0.42` : elles évaluent le classement produit par les probabilités du modèle, indépendamment d'un seuil binaire particulier.

## 6. Expérience multiclasses : identification des familles d'attaques

Une fois le détecteur binaire stabilisé, une seconde Random Forest a été ajoutée comme **expérience d'enrichissement**. Elle n'est entraînée que sur les lignes dont `label == 1` et utilise `attack_cat` comme cible. `attack_cat` reste exclu des variables d'entrée.

Cette expérience utilise donc :

- **119 341** lignes d'attaque pour l'entraînement ;
- **45 332** lignes d'attaque pour le test ;
- neuf familles : `Analysis`, `Backdoor`, `DoS`, `Exploits`, `Fuzzers`, `Generic`, `Reconnaissance`, `Shellcode` et `Worms`.

Le classifieur est une Random Forest de 100 arbres avec `class_weight="balanced_subsample"`. Il est sauvegardé séparément afin de ne pas modifier le rôle du modèle binaire.

### Résultats globaux

| Métrique | Valeur |
|---|---:|
| Accuracy | 76.13 % |
| Balanced accuracy | 51.41 % |
| Macro-F1 | 51.46 % |
| Weighted-F1 | 78.91 % |

L'accuracy et le Weighted-F1 peuvent donner une impression relativement favorable, mais ils sont fortement influencés par les classes majoritaires. Le **Macro-F1 de 51.46 %** est plus représentatif de l'hétérogénéité des résultats car chaque famille y a le même poids.

### Résultats par famille

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

Les familles `Generic`, `Reconnaissance`, `Fuzzers` et `Exploits` sont les mieux reconnues. `Shellcode` obtient un résultat intermédiaire malgré un faible support. À l'inverse, `Analysis`, `Backdoor` et `DoS` sont mal séparées par le modèle actuel. Pour `Worms`, seulement 44 exemples sont présents dans le jeu de test, ce qui rend toute conclusion sur cette famille particulièrement fragile.

L'écart entre les familles confirme que le déséquilibre des données et le recouvrement potentiel de leurs caractéristiques compliquent l'identification fine. Cette expérience n'est donc pas présentée comme un classifieur de familles fiable dans tous les cas.

### Rôle dans la chaîne finale

L'architecture retenue reste une cascade :

```text
événement réseau
   -> détecteur binaire
      -> normal : fin de l'analyse ML
      -> attaque détectée : classifieur de famille expérimental
```

La probabilité du détecteur binaire reste la seule confiance utilisée dans le score de risque. La probabilité multiclasses sert uniquement à contextualiser la famille estimée.

Une conséquence importante doit être explicitement comprise : **une fausse alerte du détecteur binaire est quand même transmise au classifieur de famille**, qui est entraîné uniquement sur des attaques et choisira donc nécessairement une des neuf familles. La famille estimée ne constitue donc jamais une confirmation indépendante de l'existence d'une attaque.

De même, une attaque manquée par le détecteur binaire ne peut pas être classifiée par le second modèle. Les performances multiclasses mesurées sur les 45 332 attaques du test évaluent la capacité intrinsèque du classifieur de familles, pas la performance complète de la cascade de bout en bout.

**Conclusion : la multiclassification est conservée comme enrichissement expérimental du prototype, et non comme nouvelle décision opérationnelle.**

## 7. Analyse binaire par catégorie réelle UNSW-NB15

Indépendamment de la multiclassification, lorsque `attack_cat` est présent dans un fichier UNSW-NB15 importé, la plateforme peut l'utiliser comme **vérité terrain** pour analyser les décisions du détecteur binaire.

Le dashboard peut ainsi afficher, pour chaque catégorie réelle :

- le nombre d'événements ;
- le nombre d'attaques détectées ;
- le nombre d'événements pour lesquels aucune attaque n'a été détectée ;
- le taux de détection pour les catégories d'attaque ;
- le taux de faux positifs pour la catégorie `Normal`.

Cette vue reste distincte de l'estimation multiclasses afin de ne pas confondre vérité terrain, décision binaire et famille prédite.

## 8. Explication du score de risque

Le score de risque reste une règle métier explicite du prototype :

- confiance du détecteur binaire : maximum 60 points ;
- sévérité : maximum 25 points ;
- criticité du type de source : maximum 15 points.

Dans l'onglet **Alertes**, une alerte peut être inspectée individuellement. La contribution de chaque composante est affichée afin que le score ne soit pas une valeur opaque.

La confiance du classifieur multiclasses n'entre pas dans ce calcul.

## 9. Validation avant inférence

Avant d'analyser un CSV en mode UNSW-NB15, le dashboard vérifie sa compatibilité avec les variables réellement attendues par le modèle sauvegardé.

La prévisualisation indique :

- le nombre de lignes ;
- le nombre de variables requises ;
- le nombre de variables reconnues ;
- la présence éventuelle de `label` et `attack_cat` ;
- les variables manquantes si le fichier n'est pas compatible.

Le bouton d'analyse ML reste désactivé tant que les variables obligatoires sont absentes.

## 10. Limites scientifiques principales

Les résultats doivent être interprétés dans le cadre d'un prototype académique :

- UNSW-NB15 reste un dataset public et ne démontre pas à lui seul une généralisation à un réseau réel ;
- le détecteur binaire conserve un FPR de **21.46 %** ;
- le seuil `0.42`, bien que très performant sur le holdout du train, généralise moins bien que `0.50` ;
- les performances multiclasses sont fortement hétérogènes ;
- les classes rares disposent de très peu d'exemples de test ;
- les erreurs du détecteur binaire se propagent vers l'étage multiclasses ;
- la confiance multiclasses n'est pas calibrée comme une probabilité opérationnelle de certitude.

Ces limites sont conservées dans la documentation au lieu d'être masquées, car elles font partie de l'analyse scientifique du projet.

## Reproductibilité

Le rapport scientifique final est versionné dans :

```text
reports/model_metrics.json
```

Il peut être régénéré sur le dataset complet avec :

```powershell
python -m cyberplatform.training --data-dir data/raw/unsw_nb15
```

Cette commande produit les trois modèles principaux :

```text
models/logistic_regression.joblib
models/random_forest.joblib
models/primary_model.joblib
models/attack_family_random_forest.joblib
```

Puis les tests peuvent être exécutés :

```powershell
$env:PYTHONPATH="src"
python -m unittest discover -s tests -v
```

Enfin, le dashboard peut être relancé :

```powershell
python -m streamlit run app/streamlit_app.py
```
