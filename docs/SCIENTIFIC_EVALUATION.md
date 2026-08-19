# Évaluation scientifique et interprétation du modèle

Ce document complète le README et décrit les améliorations d'évaluation ajoutées au prototype CyberPlatform sans élargir son périmètre fonctionnel. La plateforme reste un prototype académique local de détection binaire `normal / attaque`, validé principalement sur UNSW-NB15.

## 1. Protocole de seuil de décision

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

## 3. Évaluation finale sur le test officiel

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

**Conclusion : le seuil opérationnel `0.50` est conservé.** Le seuil `0.42` reste documenté comme expérience de sensibilité. Ce résultat met en évidence qu'un seuil performant sur une validation interne ne doit pas être déployé automatiquement sans contrôle de généralisation.

## 4. Choix du modèle principal

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

## 6. Analyse des erreurs par catégorie UNSW-NB15

Le modèle final reste strictement binaire. Il ne prédit pas `DoS`, `Exploits`, `Generic`, `Reconnaissance`, etc.

Lorsque `attack_cat` est présent dans un fichier UNSW-NB15 importé, la plateforme l'utilise uniquement comme **vérité terrain** pour analyser les décisions binaires du modèle. Le dashboard peut ainsi afficher, pour chaque catégorie réelle :

- le nombre d'événements ;
- le nombre d'attaques détectées ;
- le nombre d'événements pour lesquels aucune attaque n'a été détectée ;
- le taux de détection pour les catégories d'attaque ;
- le taux de faux positifs pour la catégorie `Normal`.

Cette analyse permet d'étudier les limites du détecteur sans présenter artificiellement le modèle comme un classifieur multi-classe.

## 7. Explication du score de risque

Le score de risque reste une règle métier explicite du prototype :

- confiance ML : maximum 60 points ;
- sévérité : maximum 25 points ;
- criticité du type de source : maximum 15 points.

Dans l'onglet **Alertes**, une alerte peut être inspectée individuellement. La contribution de chaque composante est affichée afin que le score ne soit pas une valeur opaque.

Cette explicabilité concerne le **scoring opérationnel**. Elle ne remplace pas l'importance globale des variables de la Random Forest affichée dans l'onglet **Explicabilité**.

## 8. Validation avant inférence

Avant d'analyser un CSV en mode UNSW-NB15, le dashboard vérifie sa compatibilité avec les variables réellement attendues par le modèle sauvegardé.

La prévisualisation indique :

- le nombre de lignes ;
- le nombre de variables requises ;
- le nombre de variables reconnues ;
- la présence éventuelle de `label` et `attack_cat` ;
- les variables manquantes si le fichier n'est pas compatible.

Le bouton d'analyse ML reste désactivé tant que les variables obligatoires sont absentes.

## Reproductibilité

Le rapport scientifique final est versionné dans :

```text
reports/model_metrics.json
```

Il peut être régénéré sur le dataset complet avec :

```powershell
python -m cyberplatform.training --data-dir data/raw/unsw_nb15
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
