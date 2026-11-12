> COPIE en lecture seule — source : [DOSSIER_PROJET]/00_ritual/Donnees_et_Modeles.md, version du 2026-11-11. Ne pas modifier ici : une correction se propose au §6 de PASSATION.md.

# DONNÉES ET MODÈLES — Capstone_Project_1
> Gabarit : `19_Template_Donnees_et_Modeles.md` (système v2.15.6, gabarit v0) · Document de build (`01_sessions/Build_Control.md`,
> DOCUMENTS DE BUILD) : **partie données** due avant le n° 10 `load_paysim.py` (J2) ; **partie modèles** au J3.
> Version : **v0.1** — EN COURS (partie données) · Langue : **français** — source interne, jamais rendue (I28) ; le livrable B
> (`data/README.md`, n° 15) et le rapport technique (n° 73) sont écrits **en anglais** à partir d'elle.
> Rôle : documentation des données et du modèle ; source du rapport technique. ⟵ `03_Architecture_Globale_ML.md`
> **Règle des chiffres** : un chiffre marqué *provisoire* vient d'une lecture en ligne de commande (2026-11-06) ; il devient définitif
> seulement quand `src/data/eda.py` (n° 13) le recalcule (Q08 — preuve). Aucun résultat de modèle sans ligne au §6.

---

## 1. FICHE DU JEU DE DONNÉES (écrite depuis la copie téléchargée)
| Élément | Valeur |
|---|---|
| Source exacte (URL, titre de la page, nom du fichier) | Page Kaggle « PaySim synthetic financial datasets » citée par l'énoncé (§3.2, §22.1) — **URL et titre exacts à recopier depuis la page** (I04, R044) · fichier : `PS_20174392719_1491204439457_log.csv` (471 Mo), rangé dans `data/raw/`, non versionné (D-15) |
| Version ou date de téléchargement | Téléchargé le **2026-10-27** (date du fichier ; outil `kagglehub`, dossier `ealaxi/paysim1/versions/2`) · empreinte SHA-256 `16910f90577b0d981bf8ff289714510bb89bc71bff7d3f220f024e287e4eea6b` · **libellé de version de la page à vérifier** (R045) |
| Licence et conditions (telles qu'écrites ; sinon « non indiquée ») | **À recopier mot pour mot depuis la page Kaggle** (I04, R046 — Q-02 de `PASSATION.md`) |
| Ce que la licence permet (redistribution ? commit dans le dépôt ?) | À déduire de la licence recopiée. En attendant : **aucun commit des données brutes** (`data/raw/` ignoré par git, R043 ✅ 🟡) |
| Nombre de lignes / de colonnes (comptés soi-même) | *Provisoire* : **6 362 620 lignes** (hors en-tête), **11 colonnes** — à confirmer par `eda.py` (R047) |
| Définition de la cible (colonne, valeurs, vérification faite) | `isFraud` : 1 = transaction frauduleuse, 0 = non frauduleuse (énoncé §4.1, « ground-truth fraud label ») · valeurs observées : 0 et 1 seulement, aucune case vide — vérifié par le contrat (`schema.py`, n° 09, Temps 1 du 2026-11-06) · *provisoire* : **8 213** fraudes, soit ≈ **0,13 %** |
| Limites connues (au moins cinq) | 1. **Données synthétiques** : produites par le simulateur PaySim, aucun client réel ; les résultats ne se transposent pas tels quels à de vraies données bancaires (R155). 2. **Risque de généralisation** : les soldes peuvent suivre des règles propres au simulateur, que le modèle risque d'apprendre comme raccourci (§4.2, R054). 3. **Temps simulé** : `step` est une heure simulée, pas un calendrier ; un découpage aléatoire peut faire fuir le futur (§4.1). 4. **Identifiants synthétiques** : `nameOrig`, `nameDest` favorisent la mémorisation ; exclus des variables du modèle. 5. **Soldes de destinataires à zéro** : `oldbalanceDest` peut valoir 0 pour certains destinataires (§4.1) ; fréquence et cause à mesurer au n° 13. 6. **Déséquilibre extrême** : ≈ 0,13 % de fraudes (*provisoire*) ; l'exactitude seule n'a aucun sens (R065). 7. **Drapeau du simulateur** : `isFlaggedFraud` est une règle interne au simulateur (*provisoire* : 16 lignes à 1), pas une vérité terrain. |

⟵ `03_Architecture_Globale_ML.md` §3 règle 1

## 2. DICTIONNAIRE DE DONNÉES
> Signification et risques : énoncé §4.1, vérifiés sur la copie téléchargée. Types et rôles : le contrat `src/data/schema.py` (n° 09).
> Colonne « Valeurs manquantes » : *provisoire* (0 case vide sur tout le fichier, lecture du 2026-11-06), recomptée par `eda.py`.

| Colonne | Type | Signification | Rôle (variable / identifiant / cible / ordre) | Valeurs manquantes | Utilisée dans le modèle ? | Risque de fuite ou d'équité |
|---|---|---|---|---|---|---|
| `step` | entier ≥ 0 | Unité de temps simulé ; 1 step = 1 heure | Variable (*feature*) et clé d'ordre | 0 (*provisoire*) | À décider au J3 (I09) | Découpage aléatoire entre les steps : fuite du futur (R104) |
| `type` | texte, 5 valeurs : `CASH_IN`, `CASH_OUT`, `DEBIT`, `PAYMENT`, `TRANSFER` | Catégorie de la transaction | Variable catégorielle | 0 (*provisoire*) | Oui (encodage au J3) | La fraude peut se concentrer dans quelques types (B40, R068) |
| `amount` | nombre ≥ 0 | Montant, en unités du simulateur | Variable numérique | 0 (*provisoire*) | Oui | Très asymétrique ; traitement des valeurs aberrantes à justifier (B41) |
| `nameOrig` | texte | Identifiant synthétique du client qui émet | Identifiant | 0 (*provisoire*) | **Non** | Mémorisation, surapprentissage (B03, R054) |
| `oldbalanceOrg` | nombre ≥ 0 | Solde de l'émetteur avant la transaction | Variable numérique | 0 (*provisoire*) | À décider au J3 | Possiblement propre au simulateur (raccourci, B42) |
| `newbalanceOrig` | nombre ≥ 0 | Solde de l'émetteur après la transaction | Variable numérique | 0 (*provisoire*) | À décider au J3 | Avec l'ancien solde et le montant, peut révéler les règles du simulateur |
| `nameDest` | texte | Identifiant synthétique du destinataire | Identifiant | 0 (*provisoire*) | **Non** | Même risque que `nameOrig` ; style différent selon la catégorie de destinataire |
| `oldbalanceDest` | nombre ≥ 0 | Solde du destinataire avant la transaction | Variable numérique | 0 (*provisoire*) | À décider au J3 | Parfois à zéro ; fréquence et cause à mesurer (B43) |
| `newbalanceDest` | nombre ≥ 0 | Solde du destinataire après la transaction | Variable numérique | 0 (*provisoire*) | À décider au J3 | Même risque ; possiblement propre au simulateur |
| `isFraud` | entier, 0 ou 1 | Étiquette de fraude (vérité terrain) | **Cible** (*target*) | 0 (*provisoire*) ; le contrat refuse toute case vide | **Non** — c'est ce qu'on prédit | Ne doit **jamais** entrer dans X (fuite de cible, B08, R095) |
| `isFlaggedFraud` | entier, 0 ou 1 | Drapeau produit par une règle du simulateur | Drapeau du simulateur (`RULE_FLAG`) | 0 (*provisoire*) | **Non** dans le modèle principal ; possible seulement comme référence de comparaison, séparée et justifiée | Interdit comme variable principale (B02, R053) |

## 3. ANALYSE EXPLORATOIRE — VÉRIFICATIONS ET CONSTATS
> Se remplit au n° 13 `eda.py` et au n° 14 `notebooks/01_eda.ipynb`, avec les chiffres calculés par le code. Énoncé §5.1 (R061–R072).

| # | Vérification | Résultat (chiffres) | Décision prise |
|---|---|---|---|
| 1 | Dimensions et schéma | *Provisoire* : 6 362 620 × 11 ; schéma conforme au contrat (n° 09) | À confirmer (n° 13) |
| 2 | Types de données (cohérents avec le sens ?) | Vérifiés par `validate_frame` (n° 09) | — |
| 3 | Valeurs manquantes par colonne | *Provisoire* : 0 partout | À confirmer (n° 13) |
| 4 | Doublons (définition, nombre, action) | À définir et compter (n° 13) | |
| 5 | Distribution de la cible, déséquilibre des classes | *Provisoire* : 8 213 fraudes (≈ 0,13 %) | Métriques adaptées au déséquilibre (J3) |
| 6 | Répartition par catégorie principale (`type`) | *Provisoire* : CASH_OUT 2 237 500 · PAYMENT 2 151 495 · CASH_IN 1 399 284 · TRANSFER 532 909 · DEBIT 41 432 | À confirmer (n° 13) |
| 7 | Distribution des valeurs numériques (asymétrie) | n° 13 | |
| 8 | Taux de la cible par catégorie | n° 13 | |
| 9 | Évolution dans le temps (`step`) | n° 13 | |
| 10 | Relations entre variables numériques (corrélations, et leurs limites) | n° 13 | |
| 11 | Fuites possibles, artefacts du simulateur | n° 13 | |
| 12 | Valeurs aberrantes (détection, traitement ou non, justification) | n° 13 | |

### 3.1 Graphiques (chacun avec ses trois lignes)
| # | Graphique (fichier dans `artifacts/`) | Ce qu'il montre | Ce que ça veut dire pour le métier | Décision |
|---|---|---|---|---|
| G1 | `figures/fig01_class_balance.png` | n° 13 | | |
| G2 | `figures/fig02_type_counts.png` | n° 13 | | |
| G3 | `figures/fig03_amount_distribution.png` | n° 13 | | |
| G4 | `figures/fig04_fraud_rate_by_type.png` | n° 13 | | |
| G5 | `figures/fig05_volume_fraud_by_step.png` | n° 13 | | |
| G6 | `figures/fig06_correlation_heatmap.png` | n° 13 | | |

## 4. PRÉTRAITEMENT ET VARIABLES
Rempli au J3 (n° 18 `build_features.py`, I36, 2026-11-11). Exclues de X, lues dans les rôles de `schema.py` : `isFraud` (cible), `isFlaggedFraud` (drapeau du simulateur), `nameOrig`, `nameDest` (identifiants).

| Variable du modèle | Origine | Transformation | Pourquoi |
|---|---|---|---|
| `amount` | brute | log signé + standardisation | montants très asymétriques |
| `oldbalanceOrg`, `oldbalanceDest` | brutes | log signé + standardisation | idem |
| `error_balance_orig` | `oldbalanceOrg − newbalanceOrig − amount` | log signé + standardisation | le solde émetteur ne bouge pas comme il devrait (fig05) |
| `error_balance_dest` | `oldbalanceDest − newbalanceDest + amount` | log signé + standardisation | idem côté destinataire |
| `hour_of_day` | `step % 24` | standardisation | comportement par heure, réutilisable ; `step` brut retiré (apprend la période) |
| `type` (5 colonnes) | brute | one-hot, catégories fixées | — |
| `is_risky_type` | `type ∈ {TRANSFER, CASH_OUT}` | telle quelle (0/1) | seuls types où la fraude existe (décision J2) |

Retirées après VIF : `newbalanceOrig`, `newbalanceDest` (combinaisons exactes des autres ; aucune information perdue). VIF restant : `amount` 17,2 et `error_balance_orig` 17,1, gardés (régularisation L2, explication par permutation). Limite : les erreurs de solde peuvent être un raccourci propre au simulateur (B42).


## 5. DÉCOUPAGE
Rempli au J3 (n° 16 `split.py`, I34). Stratifié sur `isFraud`, **70 / 15 / 15**, graine **42** — valeurs dans `configs/settings.yaml` (`split`), transmises par `train.py`, recopiées dans `model_metadata.json`.
Résultat : train 4 453 833 · validation 954 394 · test 954 393 lignes ; taux de fraude 0,1291 % dans les trois parts ; aucune ligne perdue ni en double ; mêmes lignes à graine égale (vérifié deux jours de suite). Découpage temporel écrit (`temporal_split`, R104) : 0,08 % / 0,06 % / 0,44 % de fraudes selon la période — non utilisé pour le modèle final, il justifie `hour_of_day` à la place de `step`.

## 6. JOURNAL DES EXPÉRIENCES
| Date | Expérience | Données | Résultat clé | Décision |
|---|---|---|---|---|
| 2026-11-11 | VIF (7 variables numériques) | train, 200 000 lignes | tous infinis ; sans `newbalance…` : 1,1 à 17,2 | I36 : retirer `newbalanceOrig/Dest` |
| 2026-11-11 | Classiques, Temps 1 | train 200 000 / val 200 000 | RF 0,899 · LogReg 0,670 · baseline 0,0012 | I37 |
| 2026-11-11 | MLP, 20 époques puis 50 | idem | meilleure époque = dernière (0,767) → 50 / 5 : 0,857 | I38 révisée |
| 2026-11-11 | Run complet `python -m src.train` | train 1 M / val et test complets | RF 0,919 (val), test 0,908 | I09 : RF ; seuil 0,5492 (I08) |

Suivi des expériences (*experiment tracking*) : ce tableau **plus** les fichiers écrits par le code
(`src/train.py` → `artifacts/metrics/comparison_table.csv`, registre n° 30) ; chaque ligne renvoie à sa commande et à son commit.
Pas de MLflow pour le Capstone (I28) ; MLflow prévu si le projet devient un produit Tensoratech (I29).
## 7. COMPARAISON DES MODÈLES (validation)
Run complet `python -m src.train` (2026-11-11 23:38, 3 min 56 ; train = 1 000 000 lignes stratifiées, I37/I05 ; validation complète 954 394 lignes). Source : `artifacts/metrics/comparison_table.csv`.

| Modèle | Réglage retenu | PR-AUC | ROC-AUC | Meilleur F1 |
|---|---|---|---|---|
| **Random Forest** (final, I09) | profondeur 20, 200 arbres | **0,9186** | 0,9991 | 0,885 |
| MLP PyTorch | 32-16, dropout 0,1, époque 26 | 0,8981 | 0,9993 | 0,847 |
| Régression logistique | C = 1,0 | 0,6366 | 0,9960 | 0,623 |
| Baseline (taux) | — | 0,0013 | 0,5000 | 0,003 |

Lecture : la ROC-AUC est ~0,999 pour tous les vrais modèles (les 950 000 vrais négatifs écrasent le taux de faux positifs) ; la PR-AUC les sépare — c'est la métrique de choix (décision J2).

## 8. SEUIL DE DÉCISION
Objectif (I08) : **300 cas/jour** revus par l'équipe (~205 500 transactions/jour → 0,146 % alertables) ; marge « proche du seuil » 0,05 (revue prioritaire, J4). Règle : le seuil le plus bas dont le volume d'alertes tient dans la capacité, choisi sur la validation. **Seuil retenu : 0,5492** (source unique : `model_metadata.json`).

| Capacité/jour | Seuil | Alertes (val.) | Fraudes attrapées | Fausses alertes | Précision | Rappel |
|---|---|---|---|---|---|---|
| 100 | 0,995 | 464 | 464 | 0 | 1,000 | 0,377 |
| 200 | 0,852 | 928 | 925 | 3 | 0,997 | 0,751 |
| **300** | **0,549** | **1 393** | **1 082** | **311** | **0,777** | **0,878** |
| 500 | 0,421 | 2 321 | 1 132 | 1 189 | 0,488 | 0,919 |
| 1 000 | 0,290 | 4 643 | 1 184 | 3 459 | 0,255 | 0,961 |

Source : `artifacts/metrics/threshold_analysis.csv` ; fig07.

## 9. RÉSULTAT FINAL SUR LE TEST (rapporté une seule fois)
Random Forest, seuil 0,5492, 954 393 lignes dont 1 232 fraudes (`artifacts/metrics/test_results.json`, fig08) :
**PR-AUC 0,908 · ROC-AUC 0,999 · précision 0,776 · rappel 0,863 · F1 0,817** — tp 1 063, fp 307, fn 169, tn 952 854 (1 370 alertes, dans la capacité).
Écart validation → test faible (rappel 0,878 → 0,863 ; précision 0,777 → 0,776) : les choix faits sur la validation se généralisent.

## 10. ANALYSE DES ERREURS ET EXPLICABILITÉ
Importance par permutation (I10, D-11 ; colonnes brutes, validation, score PR-AUC ; fig09). Valeurs du Temps 1 (RF, 200 000 lignes) : `oldbalanceOrg` 0,78 · `type` 0,76 · `amount` 0,41 · `newbalanceDest` 0,33 · `newbalanceOrig` 0,15 · `oldbalanceDest` 0,14 · `step` 0,06. **Importance ≠ cause** : c'est ce dont le modèle dépend.
Erreurs au seuil (validation, `error_analysis.csv`) : fraudes ratées surtout en **CASH_OUT** (148, montant médian ~103 000, contre ~835 000 pour les attrapées) → le modèle rate surtout les **petites** fraudes ; fausses alertes surtout en CASH_OUT (307). SHAP non réalisé (recommandé, temps). Limite : les erreurs de solde, très fortes, peuvent être un raccourci propre au simulateur (B42).

## 11. EXPÉRIENCE DE DEEP LEARNING (si demandée)
MLP PyTorch (I38) : 12 → 32 → 16 → 1, ReLU, dropout 0,1 ; perte `BCEWithLogitsLoss(pos_weight ≈ 775)` ; Adam 1e-3, lots de 2 048 ; arrêt précoce sur PR-AUC de validation (MAX_EPOCHS 50, PATIENCE 5 — révisé après un Temps 1 où la meilleure époque était la dernière à 20). Run complet : meilleure époque 26, PR-AUC validation **0,898** — proche de la Random Forest (0,919), qui reste le modèle final. Courbes : fig10. Emballé (`TorchMLPClassifier`, `predict_proba` seulement) pour partager le pipeline et `model_io`.

## 12. FICHE DU MODÈLE
- **Modèle** : Random Forest (200 arbres, profondeur 20, `min_samples_leaf` 5, `class_weight` balanced_subsample), dans un pipeline préprocesseur + modèle (`final_pipeline.joblib`, non versionné, reconstruit par `python -m src.train`).
- **Entrées** : 7 colonnes brutes PaySim → 12 variables (§4). **Jamais** : `isFraud`, `isFlaggedFraud`, `nameOrig`, `nameDest`.
- **Sortie** : un score de fraude entre 0 et 1 ; décision = score ≥ **0,5492** (`model_metadata.json`, I20) ; pas de `predict()` à 0,5.
- **Usage prévu** : prioriser les cas pour une équipe de ~300 revues/jour ; aide à la décision, jamais décision automatique.
- **Performances (test, une fois)** : §9. **Limites** : données synthétiques (PaySim) ; raccourci possible des erreurs de solde (B42) ; petites fraudes CASH_OUT moins bien vues ; bornes des bandes de risque fixées au J4 (`risk_band_bounds: null`).

---

## VALIDATION
| Validé par | Date | Commentaire |
|---|---|---|
| Erman | 2026-11-10 | Partie données (§1–§3) — v0.1 ✅ |

## ÉCARTS AVEC LE GABARIT v0
- **Ajouts** : un en-tête de **règle des chiffres** (*provisoire* / définitif) ; colonnes de renvoi vers la banque de questions (B…) et la matrice (R…) dans les §1–§2 ; liste anticipée des colonnes exclues au §4 (elle découle du contrat n° 09).
- **Questions « ne dit pas encore » tranchées avant de générer (I28)** : le document est une source interne en français, pas un livrable ; le tableau §6 suffit, sans MLflow.
- **Ambiguïté du gabarit** : il ne dit pas comment noter un chiffre vu **avant** le code d'EDA (pré-vérification nécessaire pour écrire le contrat) ; ici : marqué *provisoire* jusqu'au recalcul par le code.