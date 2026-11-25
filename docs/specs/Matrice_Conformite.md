> COPIE en lecture seule — source : [DOSSIER_PROJET]/00_ritual/Matrice_Conformite.md, version du 2026-11-25. Ne pas modifier ici : une correction se propose au §6 de PASSATION.md.

# MATRICE DE CONFORMITÉ — Capstone_Project_1

> Document source : `Capstone_Project_1_Project_Brief.docx` — « Northstar Payments | Capstone Programme — Capstone Project 1 —
> AI-Powered Financial Fraud & Risk Intelligence Platform », version du 18 octobre 2026 · Rempli par : Tensoratech (Claude, chat M2), 2026-10-19
> · Version : **v1.0** — **VALIDÉ par Erman le 2026-10-19** (v0.1 : même contenu, statut EN COURS). Document vivant : statuts et preuves mis à jour pendant le build.
> Rôle : relier chaque exigence à sa preuve. C'est l'outil de défense : à toute question « où est X ? », la réponse est une ligne de ce tableau.
> Système Tensoratech v2.3.4 · Palier **Noté** · Remise **2026-11-06** · Réalisé seul (Erman) · `Document_Maitre.md` v1.0 validé le 2026-10-19

**Conventions de ce document**
- Les exigences sont recopiées **en anglais, avec les mots exacts de l'énoncé** (la langue de la source). Tout le reste est en français.
- « Où est la preuve » donne l'emplacement **prévu** (structure suggérée par l'énoncé, §16). On le remplace par l'emplacement réel quand la preuve existe : fichier, test, section du rapport, minute de la vidéo.
- Critères de la grille : C1 à C10 (§18). Statuts : ⬜ pas commencé · 🟡 en cours · ✅ fait et preuve vérifiée · ❌ ne sera pas fait (raison écrite et validée).
- Ambiguïté → question dans `Points_A_Trancher_ENSEIGNANT.md`, posée sur **la plateforme du cours** (canal confirmé par Erman le 2026-10-19 ; nom de la plateforme à préciser). La réponse est gardée dans `03_ressources/references/`.
- Ce que l'énoncé autorise à adapter, noté « (adaptable) » : durée (§17), structure du dépôt (§16), schéma JSON extensible (§10.2), XGBoost optionnel (§7), jeu de données alternatif avec accord écrit (§3.1), notes du deep learning réattribuables **seulement** sur annonce écrite de l'enseignant (§9), longueur du rapport si l'enseignant la change (§15).

---

## 1. VUE D'ENSEMBLE DE LA NOTATION (si une grille existe)
| Critère | Points | Exigences liées (ID) | Statut global |
|---|---|---|---|
| C1 Problem framing and business relevance | 8 | R007, R008, R010, R020, R023 | ⬜ |
| C2 Data quality, EDA and data governance | 12 | R013, R024, R025, R040–R075, R080–R082 | ⬜ |
| C3 Traditional ML and feature engineering | 14 | R011, R014, R026–R028, R090–R128 | ⬜ |
| C4 Evaluation and explainability | 12 | R016, R030, R031, R104, R140–R155, R244, R249 | ⬜ |
| C5 Deep Learning experiment | 6 | R015, R029, R170–R177 | ⬜ |
| C6 Agentic AI workflow and callable tools | 16 | R018, R019, R033, R034, R210–R233, R247, R248 | ⬜ |
| C7 LLM grounding, structured output and validation | 10 | R017, R032, R180–R203, R242, R243, R251 | ⬜ |
| C8 Application and usability | 7 | R019, R021, R035, R280–R294 | ⬜ |
| C9 Testing, documentation and reproducibility | 7 | R022, R036, R037, R240–R246, R300–R308, R320–R329, R357 | ⬜ |
| C10 Report, presentation, demo and individual Q&A | 8 | R008, R038, R341–R347, R350–R356, livrables C à H | ⬜ |
| **Total** | **100** | Vérification de l'énoncé : 8 + 12 + 14 + 12 + 6 + 16 + 10 + 7 + 7 + 8 = 100 | |

Remarques de notation (§18.1, pas de pénalité automatique) :
- data leakage → C3, C4 ;
- fabricated results → procédure d'intégrité académique ;
- missing deliverables → critères concernés et règles de retard ;
- chatbot falsely presented as agentic AI → C6, C7 ;
- lack of individual understanding → note individuelle après l'oral ;
- unreproducible code → C9 ;
- unsupported production-readiness claims → C4, C10.

> « Final grading follows the instructor's published policy » : cette politique n'est pas jointe (voir `Points_A_Trancher_ENSEIGNANT`).

---

## 2. EXIGENCES

### 2.1 Cadre, limites et vue d'ensemble (page de garde, « Project at a Glance », §1)
| ID | Exigence (mots exacts de la source) | Source (§ / tableau) | Type | Critère / points | Preuve attendue | Où est la preuve | Statut | Vérifié le |
|---|---|---|---|---|---|---|---|---|
| R001 | "This project must use synthetic data only" | Notice ; §1.4 | Obligatoire | Tous | Données = PaySim uniquement ; contrôle du dépôt | `data/README.md` ; test sécurité | ⬜ | |
| R002 | "must never connect to real payment rails or take financial action" | Notice ; §1.4 | Interdit | C6 | Aucun outil ne peut agir ; test | `tests/` (sécurité) | ⬜ | |
| R003 | "No real data, no autonomous financial action, no accusatory language." | Glance, Hard boundaries | Interdit | C6, C7 | Test validateur + revue | `tests/`, rapport §Security | ⬜ | |
| R004 | "The model supports review; it does not prove wrongdoing." | Glance ; §1.4 | Obligatoire | C7, C8 | Avertissement visible dans l'app | `app/` ; vidéo | ⬜ | |
| R005 | "must not freeze accounts, block transactions, accuse customers or initiate any financial action, automatically or otherwise" | §1.4 | Interdit | C6 | Aucun outil de ce type ; test | `src/agent/tools/` ; `tests/` | ⬜ | |
| R006 | "A risk score or an AI-written summary is not proof of wrongdoing, and the application must say so clearly." | §1.4 | Obligatoire | C8 | Texte visible dans l'app | `app/` ; vidéo | ⬜ | |
| R007 | "a system that scores transactions, gathers structured evidence, drafts a neutral investigation summary, checks that summary independently, and hands the result to a human reviewer" | §1.1 | Obligatoire | C6 | Démo de bout en bout | vidéo ; `app/` | ⬜ | |
| R008 | "judged not only on model accuracy but on whether the whole system is sensible, safe, testable and explainable to a non-specialist reader" | §1.1 | Obligatoire | C10 | Rapport lisible par un non-spécialiste | `reports/` | ⬜ | |
| R009 | "A notebook that only trains a classifier covers a small part of the first two phases and is not a sufficient submission." | §1.5 | Interdit | Tous | Les 4 phases du cycle couvertes | rapport ; dépôt | ⬜ | |
| R010 | Phase 1 "Problem and data": "Business problem; problem formulation; dataset discovery and understanding; data quality assessment; exploratory data analysis; data cleaning." | §1.5 | Obligatoire | C1, C2 | Sections du rapport | `reports/` | ⬜ | |
| R011 | Phase 2 "Modelling": "Feature engineering; baseline development; traditional machine learning; Deep Learning experiment; model evaluation; explainability and error analysis." | §1.5 | Obligatoire | C3–C5 | Code + rapport | `src/models/` ; `reports/` | ⬜ | |
| R012 | Phase 3 "Generative and agentic AI": "LLM integration; agentic workflow; tool integration; independent validation and guardrails." / Phase 4 "Delivery": "Application development; human-in-the-loop review; testing and monitoring design; documentation; demonstration and presentation." | §1.5 | Obligatoire | C6–C10 | Code + rapport + démo | `src/agent/` ; `app/` | ⬜ | |
| R013 | Component A: "A documented, quality-checked dataset, data dictionary and exploratory analysis." | §1.3 | Obligatoire | C2 | Data doc + EDA | `data/README.md` ; `notebooks/` | ⬜ | |
| R014 | Component B: "A baseline plus at least two comparable models inside reproducible pipelines." | §1.3 | Obligatoire | C3 | Pipelines + tableau | `src/models/` ; `artifacts/` | ⬜ | |
| R015 | Component C: "A small feed-forward neural network evaluated like the other models." | §1.3 | Obligatoire | C5 | Résultats MLP dans le tableau | `src/models/` ; `artifacts/` | ⬜ | |
| R016 | Component D: "Imbalance-aware metrics, a validation-selected threshold, error analysis and explanations." | §1.3 | Obligatoire | C4 | Section évaluation | `artifacts/` ; `reports/` | ⬜ | |
| R017 | Component E: "An evidence-grounded assistant that drafts a structured, neutral summary." | §1.3 | Obligatoire | C7 | Module LLM + validateur | `src/agent/` | ⬜ | |
| R018 | Component F: "A bounded state machine with callable tools, retries and failure states." | §1.3 | Obligatoire | C6 | Orchestrateur + tests | `src/agent/` ; `tests/` | ⬜ | |
| R019 | Component H: "A reviewer screen that records approve, escalate or request-more-information." / Component I: "Structured, exportable events for every state change and tool call." | §1.3 | Obligatoire | C6, C8, C9 | Écran de revue + export audit | `app/` ; `src/audit/` | ⬜ | |
| R020 | Les 9 problèmes opérationnels de Northstar ("A large number of transactions must be evaluated." … "Agentic AI can coordinate scoring, evidence retrieval, validation and review preparation, but must not make autonomous financial decisions.") traités dans le cadrage | §1.2 | Obligatoire | C1 | Section Business problem du rapport | `reports/` | ⬜ | |
| R021 | Component G: "A Streamlit or Gradio app that runs intake through review." | §1.3 | Obligatoire | C8 | App lancée par une commande | `app/` | ⬜ | |
| R022 | Component J: "At least 15 automated tests, a risk register and a runnable README." | §1.3 | Obligatoire | C9 | Rapport pytest, registre, README | `tests/` ; `reports/` ; `README.md` | ⬜ | |

### 2.2 Objectifs d'apprentissage (§2) — chaque objectif a sa preuve imposée
| ID | Exigence (mots exacts de la source) | Source (§ / tableau) | Type | Critère / points | Preuve attendue | Où est la preuve | Statut | Vérifié le |
|---|---|---|---|---|---|---|---|---|
| R023 | 1 "Translate a business problem into a machine-learning problem." | §2 | Obligatoire | C1 | "Technical report: problem formulation" | `reports/` | ⬜ | |
| R024 | 2 "Find, evaluate, document and prepare a suitable dataset." | §2 | Obligatoire | C2 | "Data documentation" | `data/README.md` | ⬜ | |
| R025 | 3 "Conduct exploratory data analysis and identify data-quality issues." | §2 | Obligatoire | C2 | "EDA notebook and report section" | `notebooks/` ; `reports/` | ⬜ | |
| R026 | 4 "Explain target leakage and prevent it." | §2 | Obligatoire | C3 | "Leakage discussion; pipeline code" | `reports/` ; `src/features/` | ⬜ | |
| R027 | 5 "Create a reproducible preprocessing and feature-engineering pipeline." | §2 | Obligatoire | C3 | "Pipeline code; data tests" | `src/features/` ; `tests/` | ⬜ | |
| R028 | 6 "Train and compare multiple traditional ML models." | §2 | Obligatoire | C3 | "Model comparison table" | `artifacts/` | ⬜ | |
| R029 | 7 "Implement and evaluate a modest Deep Learning experiment." | §2 | Obligatoire | C5 | "Deep Learning notebook or script; comparison" | `src/models/` | ⬜ | |
| R030 | 8 "Select metrics appropriate for imbalanced classification." | §2 | Obligatoire | C4 | "Evaluation section" | `reports/` | ⬜ | |
| R031 | 9 "Explain false positives, false negatives, threshold selection and trade-offs." | §2 | Obligatoire | C4 | "Threshold analysis; error analysis" | `reports/` ; `artifacts/` | ⬜ | |
| R032 | 10 "Integrate an LLM into an evidence-grounded business workflow." | §2 | Obligatoire | C7 | "LLM module; prompt template" | `src/agent/` | ⬜ | |
| R033 | 11 "Build a bounded agentic workflow with tools, state, validation and failure handling." | §2 | Obligatoire | C6 | "Orchestrator code; demo video" | `src/agent/` ; vidéo | ⬜ | |
| R034 | 12 "Implement structured output validation and audit logging." | §2 | Obligatoire | C6, C7 | "Validator code; audit log export" | `src/agent/validators/` ; `src/audit/` | ⬜ | |
| R035 | 13 "Build a usable application around the model and agent workflow." | §2 | Obligatoire | C8 | "Application; demo video" | `app/` ; vidéo | ⬜ | |
| R036 | 14 "Test normal, edge, malformed-input and failure scenarios." | §2 | Obligatoire | C9 | "Test suite; test evidence" | `tests/` ; `reports/` | ⬜ | |
| R037 | 15 "Document limitations, risks, reproducibility and responsible-AI considerations." | §2 | Obligatoire | C9, C10 | "Report; README; risk register" | `reports/` ; `README.md` | ⬜ | |
| R038 | 16 "Present and defend the technical decisions made during the project." | §2 | Obligatoire | C10 | "Live presentation and Q&A" | soutenance | ⬜ | |

### 2.3 Jeu de données (§3) et dictionnaire (§4)
| ID | Exigence (mots exacts de la source) | Source (§ / tableau) | Type | Critère / points | Preuve attendue | Où est la preuve | Statut | Vérifié le |
|---|---|---|---|---|---|---|---|---|
| R040 | "PaySim is the default dataset used throughout this brief." | §3.1 | Obligatoire | C2 | Source citée | `data/README.md` | ⬜ | |
| R041 | "You may use an alternative dataset only with written instructor approval." | §3.1 | Interdit (sans accord) | C2 | — (on garde PaySim) | — | ⬜ | |
| R042 | "Do not use real banking data, customer personal information (PII), confidential employer data or any dataset you are not authorised to use." | §3.1 | Interdit | C2 | Revue + contrôle du dépôt | `tests/` (sécurité) | ⬜ | |
| R043 | "Read the terms on the source page and record them. Do not commit the raw data to your repository unless you have verified that the terms allow it." | §3.1 | Obligatoire / Interdit | C2 | Licence notée ; `data/` dans `.gitignore` | `data/README.md` ; `.gitignore` — `data/raw/` ignoré (commit `6f6c050`) ; licence à recopier au J2 (I04) | 🟡 | 2026-11-04 |
| R044 | Dataset record — "Exact source": "The URL, the page title and the file name you used." | §3.4 | Obligatoire | C2 | Ligne du record | `data/README.md` — fichier relevé : `PS_20174392719_1491204439457_log.csv` (I04 — fiche PaySim) ; URL et titre de la page à recopier | 🟡 | 2026-11-06 |
| R045 | "Version or download date": "The date you downloaded the data and any version label shown on the source page." | §3.4 | Obligatoire | C2 | Ligne du record | `data/README.md` — téléchargé le 2026-10-27 (date du fichier, `kagglehub`, `versions/2`) ; libellé de version de la page à vérifier (I04 — fiche PaySim) | 🟡 | 2026-11-06 |
| R046 | "Licence and terms": "exactly as stated on the source page, and what they allow. Write "not stated" if the page does not say; do not guess." | §3.4 | Obligatoire | C2 | Copie exacte des conditions | `data/README.md` | ⬜ | |
| R047 | "Record count and feature count": "Counts you computed yourself after loading the data." | §3.4 | Obligatoire | C2 | Sortie du code | `data/README.md` ; notebook | ⬜ | |
| R048 | "Target definition": "Which column is the label, what each value means and how you checked it." | §3.4 | Obligatoire | C2 | Ligne du record | `data/README.md` | ⬜ | |
| R049 | "Known limitations": "At least five limitations, including synthetic origin and generalisation risk." | §3.4 | Obligatoire | C2 | ≥ 5 limites | `data/README.md` | ⬜ | |
| R050 | "you must write it from the copy you actually downloaded, not from this brief" | §3.4 | Obligatoire | C2 | Valeurs calculées | `data/README.md` | ⬜ | |
| R051 | "you must verify each entry against your own download" (référence des champs PaySim : step, type, amount, nameOrig, oldbalanceOrg, newbalanceOrig, nameDest, oldbalanceDest, newbalanceDest, isFraud, isFlaggedFraud) | §4.1 | Obligatoire | C2 | Vérification par champ | `data/README.md` | ⬜ | |
| R052 | "`isFraud` is the target label for the primary supervised classification task." | §4.2 | Obligatoire (à discuter) | C2, C3 | Discussion + code | `reports/` ; `src/features/` | ⬜ | |
| R053 | "`isFlaggedFraud` … must not be included as a predictor in the main model. Any experiment that uses it must be separated and justified." | §4.2 | Interdit | C3 | Test + discussion | `tests/` ; `reports/` | ⬜ | |
| R054 | "`nameOrig` and `nameDest` are synthetic identifiers that can encourage memorisation or overfitting. The balance fields are potentially informative but possibly simulator-specific, so you must discuss whether your model relies on shortcuts that would not generalise" | §4.2 | Obligatoire (à discuter) | C2, C4 | Discussion des raccourcis | `reports/` | ⬜ | |
| R055 | Final data dictionary: "column name, data type, meaning, role (feature, identifier or target), missing-value count, whether it is used in the model, and any leakage or fairness concern" | §4.4 | Obligatoire | C2 | Tableau complet | `data/README.md` | ⬜ | |
| R056 | "Key concepts you must be able to explain" (Feature, Target variable, Identifier, Derived feature, Data leakage, Training data, Validation data, Test data) | §4.3 | Obligatoire (oral) | C10 | Réponses ✅ | `Banque_Questions.md` | ⬜ | |

### 2.4 EDA (§5)
| ID | Exigence (mots exacts de la source) | Source (§ / tableau) | Type | Critère / points | Preuve attendue | Où est la preuve | Statut | Vérifié le |
|---|---|---|---|---|---|---|---|---|
| R060 | "It must produce findings that change what you do next, such as which columns you exclude, which features you create and how you split the data." | §5 | Obligatoire | C2 | Constats → décisions | `reports/` §EDA | ⬜ | |
| R061 | 1 "Dataset dimensions and schema": "Row and column counts, column names and a short schema table." | §5.1 | Obligatoire | C2 | Sortie + tableau | `notebooks/01_eda` | ⬜ | |
| R062 | 2 "Data types": "Check each type against its meaning; correct any mismatches." | §5.1 | Obligatoire | C2 | Vérification | notebook | ⬜ | |
| R063 | 3 "Missing values": "Count by column; state the handling decision or why none is needed." | §5.1 | Obligatoire | C2 | Comptes + décision | notebook | ⬜ | |
| R064 | 4 "Duplicate records": "Define what counts as a duplicate, count them and justify your action." | §5.1 | Obligatoire | C2 | Définition + compte | notebook | ⬜ | |
| R065 | 5 "Target distribution and class imbalance": "Class counts and percentages; implications for metrics and training." | §5.1 | Obligatoire | C2 | Comptes + % | notebook | ⬜ | |
| R066 | 6 "Transaction types": "Counts and share by type." | §5.1 | Obligatoire | C2 | Tableau | notebook | ⬜ | |
| R067 | 7 "Transaction amount distribution": "Summary statistics and a distribution plot; discuss skew." | §5.1 | Obligatoire | C2 | Stats + graphique | notebook | ⬜ | |
| R068 | 8 "Fraud rate by transaction type": "Fraud rate per type; discuss where fraud appears and where it does not." | §5.1 | Obligatoire | C2 | Tableau + discussion | notebook | ⬜ | |
| R069 | 9 "Patterns across simulation steps": "Volume and fraud rate over step; discuss any time pattern." | §5.1 | Obligatoire | C2 | Graphique | notebook | ⬜ | |
| R070 | 10 "Relationships among numerical features": "A correlation view of selected numeric fields, with limits of correlation stated." | §5.1 | Obligatoire | C2 | Carte de corrélation | notebook | ⬜ | |
| R071 | 11 "Potential leakage and simulator artefacts": "Identify features or relationships that look too good; explain the risk." | §5.1 | Obligatoire | C2, C3 | Analyse | notebook ; `reports/` | ⬜ | |
| R072 | 12 "Outliers and unusual observations": "Detect, inspect and justify the treatment or non-treatment." | §5.1 | Obligatoire | C2 | Analyse | notebook | ⬜ | |
| R073 | "Produce at least six meaningful visualisations." | §5.2 | Obligatoire | C2 | ≥ 6 graphiques | `artifacts/figures/` | ⬜ | |
| R074 | "For each chart, write what it shows, the business implication for Northstar, and the decision it informs" | §5.2 | Obligatoire | C2 | 3 phrases par graphique | notebook ; `reports/` | ⬜ | |
| R075 | "A chart without interpretation should not receive full credit." | §5.2 | Interdit | C2 | — | — | ⬜ | |

### 2.5 Prétraitement et variables (§6)
| ID | Exigence (mots exacts de la source) | Source (§ / tableau) | Type | Critère / points | Preuve attendue | Où est la preuve | Statut | Vérifié le |
|---|---|---|---|---|---|---|---|---|
| R080 | 1 "Validate input columns and data types." | §6.1 | Obligatoire | C2, C3 | "Validation function and a data test." | `src/data/` ; `tests/` | ⬜ | |
| R081 | 2 "Handle missing values where applicable." | §6.1 | Obligatoire | C2 | "Documented rule, or documented finding that none exist." | `data/README.md` | ⬜ | |
| R082 | 3 "Investigate duplicate records." | §6.1 | Obligatoire | C2 | "Count and decision recorded." | `data/README.md` | ⬜ | |
| R090 | 4 "Identify and justify outlier treatment." | §6.1 | Obligatoire | C3 | "Written justification tied to the business context." | `data/README.md` | ⬜ | |
| R091 | 5 "Encode categorical variables." | §6.1 | Obligatoire | C3 | "Encoder inside the pipeline." | `src/features/` | ⬜ | |
| R092 | 6 "Scale features where the chosen model requires it." | §6.1 | Obligatoire | C3 | "Scaler inside the pipeline for the relevant models only." | `src/features/` | ⬜ | |
| R093 | 7 "Consider useful derived features where justified." | §6.1 | Recommandé | C3 | "Rationale and leakage check for each derived feature." | `data/README.md` | ⬜ | |
| R094 | 8 "Create reproducible preprocessing pipelines." | §6.1 | Obligatoire | C3 | "scikit-learn Pipeline and ColumnTransformer, or an equivalent." | `src/features/` | ⬜ | |
| R095 | 9 "Preserve the target separately from the predictors." | §6.1 | Obligatoire | C3 | "Separate X and y; a test that the target is not in X." | `tests/` | ⬜ | |
| R096 | 10 "Avoid target leakage." | §6.1 | Obligatoire | C3 | "Leakage review in the report." | `reports/` | ⬜ | |
| R097 | 11 "Never fit preprocessing on the test set." | §6.1 | Interdit | C3 | "Fit on training data only; show where in the code." | `src/models/` (ligne citée) | ⬜ | |
| R098 | 12 "Document every major transformation." | §6.1 | Obligatoire | C3 | "Preprocessing documentation." | `data/README.md` | ⬜ | |
| R099 | "the same transformations are applied in training, evaluation and the application" | §6.2 | Obligatoire | C3 | Pipeline sauvegardé unique | `artifacts/` | ⬜ | |
| R100 | "State what you did for each model and why." (scaling) | §6.2 | Obligatoire | C3 | Tableau par modèle | `reports/` | ⬜ | |
| R101 | "apply resampling only inside the training process. Never resample the validation or test data." | §6.2 | Interdit | C3 | Code + test | `src/models/` | ⬜ | |
| R102 | "State your splitting strategy and random seed in the report and README." | §6.3 | Obligatoire | C3, C9 | Graine + proportions | `README.md` ; `reports/` | ⬜ | |
| R103 | "The final test set must remain untouched until final evaluation. Use training and validation data for model selection, tuning and threshold choice." | §6.3 | Interdit | C3, C4 | Code + journal | `src/models/` | ⬜ | |
| R104 | "If you can, run an additional experiment that trains on earlier steps and evaluates on later steps, and compare it with the random split." | §6.3 | Recommandé | C4 | Comparaison | `artifacts/` ; `reports/` | ⬜ | |

### 2.6 ML classique (§7)
| ID | Exigence (mots exacts de la source) | Source (§ / tableau) | Type | Critère / points | Preuve attendue | Où est la preuve | Statut | Vérifié le |
|---|---|---|---|---|---|---|---|---|
| R110 | "Build a baseline and compare at least two traditional models." | §7 | Obligatoire | C3 | Baseline + ≥ 2 | `artifacts/` | ⬜ | |
| R111 | "Majority-class or other simple baseline" — "Required reference point." — "Why a model must beat it in a meaningful way, not only on accuracy." | §7 tableau | Obligatoire | C3 | Baseline + discussion | `reports/` | ⬜ | |
| R112 | Logistic Regression — points to discuss: "Coefficients, class weighting, regularisation, linear assumptions." | §7 tableau | Recommandé | C3 | Discussion | `reports/` | ⬜ | |
| R113 | Random Forest — "Class weighting, depth and tree count, feature importance limits." | §7 tableau | Recommandé | C3 | Discussion | `reports/` | ⬜ | |
| R114 | Gradient Boosting or XGBoost "(optional)" — "Tuning effort and overfitting. XGBoost is not required if installation is impractical." | §7 tableau | Recommandé (adaptable) | C3 | — | — | ⬜ | |
| R120 | Must explain: "Why each model was selected, and its main strengths and limitations." | §7.1 | Obligatoire | C3 | Rapport + Q&A | `reports/` ; Banque | ⬜ | |
| R121 | "Whether it requires feature scaling, and how categorical variables are handled." | §7.1 | Obligatoire | C3 | Rapport | `reports/` | ⬜ | |
| R122 | "How hyperparameters were selected, using training and validation data only." | §7.1 | Obligatoire | C3 | Rapport + code | `reports/` | ⬜ | |
| R123 | "How class imbalance was addressed." | §7.1 | Obligatoire | C3 | Rapport | `reports/` | ⬜ | |
| R124 | "Why the final model was selected, with reference to your validation evidence." | §7.1 | Obligatoire | C3 | Rapport | `reports/` | ⬜ | |
| R125 | "Reproducible training code that runs from a documented command." | §7.2 | Obligatoire | C3, C9 | Commande dans le README | `README.md` | ⬜ | |
| R126 | "A saved model pipeline (preprocessing and model together) that the scoring tool loads." | §7.2 | Obligatoire | C3, C6 | Fichier + test de chargement | `artifacts/` ; `tests/` | ⬜ | |
| R127 | "A model comparison table and documented parameters." | §7.2 | Obligatoire | C3 | Tableau | `artifacts/` ; `reports/` | ⬜ | |
| R128 | "A clear validation and test strategy." | §7.2 | Obligatoire | C3 | Section du rapport | `reports/` | ⬜ | |

### 2.7 Évaluation, seuil et explicabilité (§8)
| ID | Exigence (mots exacts de la source) | Source (§ / tableau) | Type | Critère / points | Preuve attendue | Où est la preuve | Statut | Vérifié le |
|---|---|---|---|---|---|---|---|---|
| R140 | "You must report imbalance-aware metrics and explain each in plain business language." | §8.1 | Obligatoire | C4 | Tableau + phrases | `reports/` | ⬜ | |
| R141 | Confusion matrix: "Always report counts, not only percentages." (TP, TN, FP, FN) | §8.2 | Obligatoire | C4 | Matrices en comptes | `artifacts/` | ⬜ | |
| R142 | Precision, Recall | §8.2 | Obligatoire | C4 | Valeurs | `artifacts/` | ⬜ | |
| R143 | F1-score: "Hides which side is weaker; always report both." | §8.2 | Obligatoire | C4 | F1 + P + R | `artifacts/` | ⬜ | |
| R144 | ROC-AUC ("Can look good on very imbalanced data.") and "Precision-Recall AUC or average precision" | §8.2 | Obligatoire | C4 | Valeurs | `artifacts/` | ⬜ | |
| R145 | Discuss: "What happens when a legitimate transaction is incorrectly flagged, and what happens when a fraudulent transaction is missed." | §8.3 | Obligatoire | C4 | Rapport | `reports/` | ⬜ | |
| R146 | Discuss: "Why increasing recall may increase false positives, and why increasing precision may reduce the number of fraud cases caught." | §8.3 | Obligatoire | C4 | Rapport | `reports/` | ⬜ | |
| R147 | Discuss: "Why a model score is not automatically a calibrated probability." | §8.3 | Obligatoire | C4 | Rapport | `reports/` | ⬜ | |
| R148 | Discuss: "Why the decision threshold should reflect a documented operational objective, for example the review capacity of the investigation team." | §8.3 | Obligatoire | C4 | Rapport | `reports/` | ⬜ | |
| R149 | "Choose and document a decision threshold using validation data, not the final test set." | §8.4 | Obligatoire / Interdit | C4 | Code + rapport | `src/models/` | ⬜ | |
| R150 | "State the operational objective the threshold serves, show the precision-recall trade-off across candidate thresholds" | §8.4 | Obligatoire | C4 | Courbe / tableau | `artifacts/figures/` | ⬜ | |
| R151 | "then report the final test results once, at the chosen threshold" | §8.4 | Obligatoire | C4 | Une seule évaluation test | `artifacts/` ; `Journal_Build.md` | ⬜ | |
| R152 | "Inspect false positives and false negatives, group them by transaction type, amount range or other meaningful categories, and explain likely reasons." | §8.5 | Obligatoire | C4 | Analyse d'erreurs | `reports/` | ⬜ | |
| R153 | "Provide feature importance or another suitable explanation technique, such as permutation importance, model coefficients or SHAP." | §8.5 | Obligatoire | C4 | Graphique | `artifacts/figures/` | ⬜ | |
| R154 | "Do not claim that feature importance establishes causality." | §8.5 | Interdit | C4 | Revue du rapport | `reports/` | ⬜ | |
| R155 | "Write an honest discussion of limitations, including why results on synthetic data may not carry over to real banking data." | §8.5 | Obligatoire | C4, C10 | Section Limitations | `reports/` | ⬜ | |

### 2.8 Deep learning (§9)
| ID | Exigence (mots exacts de la source) | Source (§ / tableau) | Type | Critère / points | Preuve attendue | Où est la preuve | Statut | Vérifié le |
|---|---|---|---|---|---|---|---|---|
| R170 | Model: "A small feed-forward neural network (multilayer perceptron)." | §9 | Obligatoire | C5 | Code | `src/models/` | ⬜ | |
| R171 | Framework: "PyTorch or TensorFlow/Keras." | §9 | Obligatoire | C5 | Dépendance | `requirements.txt` | ⬜ | |
| R172 | Inputs: "Appropriately encoded and scaled, using the same leakage rules as Section 6." | §9 | Obligatoire | C5 | Même pipeline | `src/features/` | ⬜ | |
| R173 | Output and loss: "Binary classification output with a suitable loss function and optimiser; explain how you handle class imbalance." | §9 | Obligatoire | C5 | Code + rapport | `reports/` | ⬜ | |
| R174 | Monitoring: "Validation monitoring (for example, early stopping), recorded learning curves and fixed random seeds." | §9 | Obligatoire | C5 | Courbes + graine | `artifacts/figures/` | ⬜ | |
| R175 | Comparison: "Evaluate on the same splits, metrics and threshold procedure as the traditional models and add it to the comparison table." | §9 | Obligatoire | C5 | Ligne du tableau | `artifacts/` | ⬜ | |
| R176 | Honest reporting: "Report the actual result, even if the neural network performs worse than Random Forest or Gradient Boosting." | §9 | Obligatoire | C5 | Rapport | `reports/` | ⬜ | |
| R177 | "Teams must not drop the component on their own." (réattribution seulement si annoncée par écrit par l'enseignant) | §9 encadré | Interdit | C5 | — | — | ⬜ | |

### 2.9 LLM (§10)
| ID | Exigence (mots exacts de la source) | Source (§ / tableau) | Type | Critère / points | Preuve attendue | Où est la preuve | Statut | Vérifié le |
|---|---|---|---|---|---|---|---|---|
| R180 | "Build an LLM-powered investigation-summary assistant. It drafts a structured summary for a human reviewer. It does not decide anything." | §10 | Obligatoire | C7 | Module LLM | `src/agent/` | ⬜ | |
| R181 | Receives: "A synthetic case identifier." / "The ML model score and the selected risk band." / "A limited set of verified transaction features." / "Evidence retrieved from an approved local store." / "Relevant model and version information." | §10.1 | Obligatoire | C7 | Gabarit de prompt | `src/agent/` | ⬜ | |
| R182 | "The assistant must return JSON containing at least the fields below" — case_id, risk_level ("low \| medium \| high"), model_score, model_version, evidence, summary, uncertainties, recommended_review_steps, source_ids, validation_status ("pending \| passed \| failed") ; "You may expand it, but the output must remain structured and validated." | §10.2 | Obligatoire (adaptable : extension) | C7 | Schéma + validateur | `src/agent/validators/` | ⬜ | |
| R183 | System instructions: "Fixed rules that define the assistant's task, tone and prohibitions. They are written by you, not by case data." | §10.3 | Obligatoire | C7 | Prompt versionné | `src/agent/` | ⬜ | |
| R184 | User input: "The case request. Treat it as untrusted." | §10.3 | Obligatoire | C7 | Test injection | `tests/` | ⬜ | |
| R185 | Context: "Only the verified fields and approved evidence you choose to pass in. Less context means less risk." | §10.3 | Obligatoire | C7 | Code | `src/agent/` | ⬜ | |
| R186 | Prompt template: "A versioned template with clearly separated instruction and data sections." | §10.3 | Obligatoire | C7 | Fichier versionné | `src/agent/` | ⬜ | |
| R187 | Structured output: "A defined JSON schema that the validator checks." | §10.3 | Obligatoire | C7 | Schéma | `src/agent/validators/` | ⬜ | |
| R188 | Grounding: "Every statement traces to a supplied field or evidence item." | §10.3 | Obligatoire | C7 | Vérif. des références | validateur | ⬜ | |
| R189 | Hallucination: "The validator must be able to catch the common forms." | §10.3 | Obligatoire | C7 | Tests | `tests/` | ⬜ | |
| R190 | Evidence references: "Source IDs that link each claim to an approved evidence item." | §10.3 | Obligatoire | C7 | Vérif. des IDs | validateur | ⬜ | |
| R191 | Independent output validation: "Deterministic code, separate from the LLM, that accepts or rejects the draft." | §10.3 | Obligatoire | C7 | Module séparé | `src/agent/validators/` | ⬜ | |
| R192 | Must not: "Invent transaction details or evidence." | §10.4 | Interdit | C7 | Test | `tests/` | ⬜ | |
| R193 | Must not: "Change the official model score." | §10.4 | Interdit | C7 | Test score mismatch | `tests/` | ⬜ | |
| R194 | Must not: "Make unsupported allegations, or claim that a transaction is definitely fraudulent." | §10.4 | Interdit | C7 | Test mots interdits | `tests/` | ⬜ | |
| R195 | Must not: "Execute financial actions." | §10.4 | Interdit | C6, C7 | Test | `tests/` | ⬜ | |
| R196 | Must not: "Treat untrusted case text as trusted instructions." | §10.4 | Interdit | C7 | Test injection | `tests/` | ⬜ | |
| R197 | "If evidence is insufficient, the assistant must state the uncertainty and recommend human review rather than fill the gap." | §10.4 | Obligatoire | C7 | Cas démo + test | vidéo ; `tests/` | ⬜ | |
| R198 | "State whether you use a hosted API or a local model" | §10.5 | Obligatoire | C7 | Rapport + README | `reports/` | ⬜ | |
| R199 | Privacy: "What data leaves your machine, and why only synthetic data is sent." | §10.5 | Obligatoire | C7 | Rapport | `reports/` | ⬜ | |
| R200 | Cost: "Approximate cost per case or per run, or confirmation that a local model has no per-call cost." | §10.5 | Obligatoire | C7 | Rapport | `reports/` | ⬜ | |
| R201 | Latency: "Typical response time and what happens on a timeout." | §10.5 | Obligatoire | C7 | Mesure | `reports/` | ⬜ | |
| R202 | Reliability: "Behaviour on malformed output, rate limits and unavailable services." | §10.5 | Obligatoire | C7 | Rapport + tests | `reports/` ; `tests/` | ⬜ | |
| R203 | "Automated tests must not depend on a paid API or network access, so design the LLM client so that a fake client can be substituted in tests." | §10.5 | Obligatoire | C7, C9 | Faux client | `tests/` | ⬜ | |

### 2.10 Workflow agentique (§11)
| ID | Exigence (mots exacts de la source) | Source (§ / tableau) | Type | Critère / points | Preuve attendue | Où est la preuve | Statut | Vérifié le |
|---|---|---|---|---|---|---|---|---|
| R210 | "An agentic implementation is not an LLM prompt wrapped in a user interface. It is a controlled workflow in which software components … are coordinated through explicit state." | §11 | Obligatoire | C6 | Architecture | `src/agent/` | ⬜ | |
| R211 | Bounded workflow (required): State "Explicit case state with defined transitions." / Tools "Genuinely callable functions with defined inputs and outputs." / Control flow "Decided by an orchestrator you wrote; the LLM is one step." / Validation "Independent, deterministic validation." / Failure handling "Bounded retries, timeouts and named failure states." / Oversight "A recorded human review step." / Traceability "Structured audit events." | §11.1 | Obligatoire | C6 | Code + tests | `src/agent/` | ⬜ | |
| R212 | "Explicit state, workflow orchestration and callable tools with defined inputs and outputs." / "Validation, bounded retries and error handling." / "Human-in-the-loop review and audit logging." | §11.2 | Obligatoire | C6 | Code | `src/agent/` | ⬜ | |
| R213 | "A deterministic state machine with selected LLM calls is acceptable, and is often preferable to an unconstrained autonomous agent." | §11.2 | Recommandé | C6 | Choix d'architecture | `Architecture_Projet.md` | ⬜ | |
| R214 | Workflow : "case intake, input validation, ML risk scoring, evidence retrieval, LLM summary drafting, independent output validation, human review, then audit logging and final case status." | §11.3 | Recommandé | C6 | Orchestrateur | `src/agent/` | ⬜ | |
| R215 | Transitions : "RECEIVED -> SCORED -> EVIDENCE_READY -> DRAFTED -> VALIDATED -> HUMAN_REVIEW" ; "HUMAN_REVIEW -> CLOSED \| ESCALATED \| NEEDS_MORE_INFORMATION" ; "Any step -> FAILED (tool error or timeout after bounded retries)" ; "DRAFTED -> VALIDATION_REJECTED (validator fails after bounded retries)" | §11.3 | Obligatoire | C6 | Machine à états | `src/agent/` | ⬜ | |
| R216 | Les 11 états et leur condition d'entrée (RECEIVED … VALIDATION_REJECTED) ; terminal failure states : "Retries are exhausted; the cause is logged and visible in the UI." | §11.3 tableau | Obligatoire | C6, C8 | Code + UI | `src/agent/` ; `app/` | ⬜ | |
| R217 | EVIDENCE_READY : "The evidence tool returned results, or an explicit "no evidence" result." | §11.3 tableau | Obligatoire | C6 | Test | `tests/` | ⬜ | |
| R218 | "Invalid transitions, for example jumping from RECEIVED to VALIDATED, must be rejected and tested." | §11.3 | Obligatoire | C6, C9 | Test | `tests/` | ⬜ | |
| R219 | "Implement at least two genuinely callable tools that the workflow actually invokes. Describing tools only in documentation does not count." | §11.4 | Obligatoire | C6 | ≥ 2 outils | `src/agent/tools/` | ⬜ | |
| R220 | "You must demonstrate real execution in the demo video and the test evidence." | §11.4 | Obligatoire | C6 | Vidéo + tests | vidéo ; `reports/` | ⬜ | |
| R221 | `score_transaction()` — "Load the saved pipeline and model and score a transaction." In: "Validated transaction features." Out: "Score, threshold, risk band and model version." | §11.4 | Recommandé | C6 | Outil | `src/agent/tools/` | ⬜ | |
| R222 | `retrieve_case_evidence()` — "Fetch approved synthetic evidence for a case." In: "Case identifier." Out: "Evidence items with source IDs, or an explicit empty result." | §11.4 | Recommandé | C6 | Outil | `src/agent/tools/` | ⬜ | |
| R223 | `validate_investigation_json()` — "Check the LLM draft." In: "Draft JSON plus the official score, evidence set and rules." Out: "Pass or fail with specific reasons." | §11.4 | Recommandé | C6, C7 | Outil | `src/agent/validators/` | ⬜ | |
| R224 | `write_audit_event()` — "Record a structured audit event." In: "Case ID, state, actor, action and result." Out: "Confirmation of the stored event." | §11.4 | Recommandé | C6 | Outil | `src/audit/` | ⬜ | |
| R225 | "Your report must include an architecture diagram containing at least the components shown below: user or reviewer, application, workflow orchestrator, ML scoring tool, evidence retrieval tool, LLM, independent validator, audit store and human review step." / "your own diagram should reflect your actual design" | §11.5 | Obligatoire | C6 | Diagramme (9 composants) | `reports/` | ⬜ | |
| R226 | Explain: "Why the chosen tasks benefit from orchestration, and which tasks remain deterministic." | §11.6 | Obligatoire | C6 | Rapport + Q&A | `reports/` ; Banque | ⬜ | |
| R227 | Explain: "Why the LLM must not calculate the official score." | §11.6 | Obligatoire | C6 | Rapport | `reports/` | ⬜ | |
| R228 | Explain: "How state is tracked." | §11.6 | Obligatoire | C6 | Rapport | `reports/` | ⬜ | |
| R229 | Explain: "How failures, timeouts and bounded retries are handled." | §11.6 | Obligatoire | C6 | Rapport + tests | `reports/` | ⬜ | |
| R230 | Explain: "How duplicate calls or retries are handled, for example with an idempotency key built from the case ID and step." | §11.6 | Obligatoire | C6 | Rapport + code | `reports/` ; `src/agent/` | ⬜ | |
| R231 | Explain: "How the system decides when human review is required, and how review priority is set." | §11.6 | Obligatoire | C6 | Rapport | `reports/` | ⬜ | |
| R232 | "In this prototype every case that reaches VALIDATED proceeds to HUMAN_REVIEW." | §11.6 | Obligatoire | C6 | Test | `tests/` | ⬜ | |
| R233 | "You must also document a review-routing policy … and justify the conditions you choose." Exemples : high risk band / score close to threshold → "Priority review with the uncertainty notes highlighted." ; evidence missing → "Review with a prompt to request more information." ; validator rejected → "VALIDATION_REJECTED; no summary shown as trusted; reviewer sees structured data only." ; tool failure → "FAILED; error visible in the UI and logged." | §11.6 tableau | Obligatoire | C6 | Politique écrite | `reports/` | ⬜ | |

### 2.11 Sécurité et IA responsable (§12)
| ID | Exigence (mots exacts de la source) | Source (§ / tableau) | Type | Critère / points | Preuve attendue | Où est la preuve | Statut | Vérifié le |
|---|---|---|---|---|---|---|---|---|
| R240 | "Include a dedicated risk section in your report." / "Add risks specific to your design." | §12 | Obligatoire | C9 | Section + registre | `reports/` | ⬜ | |
| R241 | Synthetic data and privacy — "Use only the approved synthetic data; add a repository check for sensitive-looking fields." | §12 tableau | Obligatoire | C9 | Contrôle du dépôt | `tests/` | ⬜ | |
| R242 | Prompt injection — "Treat case notes as untrusted data; keep instructions and data separate; test with an injected note." | §12 tableau | Obligatoire | C7 | Test | `tests/` | ⬜ | |
| R243 | Hallucinations — "Ground in supplied evidence; validate references." / Malformed structured output — "Schema validation and bounded retries." / Unsupported claims — "Validator checks for prohibited or definitive wording." | §12 tableau | Obligatoire | C7 | Validateur + tests | `tests/` | ⬜ | |
| R244 | Data leakage — "Pipeline design, leakage review and data tests." / Model bias — "Examine error patterns across available categories and discuss the limits of the data." / False positives and false negatives — "Documented threshold and error analysis." | §12 tableau | Obligatoire | C3, C4 | Rapport | `reports/` | ⬜ | |
| R245 | Model drift — "Design a monitoring plan describing what you would track and when you would retrain." | §12 tableau | Obligatoire | C9 | Plan écrit | `reports/` | ⬜ | |
| R246 | API key protection — "Secrets in environment variables, .env ignored by version control, .env.example without values." | §12 tableau | Obligatoire | C9 | Fichiers | `.gitignore` ; `.env.example` — commit `6f6c050` (tag `vj1-cadrage-frozen`) : `.env` et `.env.*` ignorés, `!.env.example` gardé ; `.env.example` = 4 noms de variables sans valeur | 🟡 | 2026-11-04 |
| R247 | Excessive tool permissions — "Tools are read-only or scoped; no tool performs a financial action." / Tool failures and timeouts — "Timeouts, bounded retries and named failure states." | §12 tableau | Obligatoire | C6 | Code + tests | `src/agent/tools/` | ⬜ | |
| R248 | Auditability — "Structured audit events for each state change and reviewer decision." / Human oversight — "Mandatory recorded review before any case outcome." | §12 tableau | Obligatoire | C6 | Audit + test | `src/audit/` | ⬜ | |
| R249 | Synthetic-to-real generalisation — "State this limitation prominently and avoid production-readiness claims." | §12 tableau | Obligatoire / Interdit | C4, C10 | Rapport | `reports/` | ⬜ | |
| R250 | Mandatory controls : "Input validation, schema validation and evidence-reference validation." / "Bounded retries and clear failure states." / "Secrets stored outside source control." / "No real customer data and no autonomous financial action." / "Neutral, non-accusatory language, and a clear disclosure that the model supports review rather than proving wrongdoing." | §12.1 | Obligatoire | C6, C7 | Code + tests | `src/` ; `tests/` | ⬜ | |
| R251 | Neutral language : éviter "This customer committed fraud." / "The recipient is a criminal." / "Block the account." ; préférer les formulations de l'énoncé ("…is recommended for review." etc.) | §12.2 | Interdit / Obligatoire | C7 | Liste de mots du validateur | `src/agent/validators/` | ⬜ | |
| R252 | Frameworks to consult : "NIST AI Risk Management Framework" ; "OWASP Top 10 for Large Language Model Applications" | §12.3 | Recommandé | C9 | Cités dans le rapport | `reports/` | ⬜ | |

### 2.12 Application (§13)
| ID | Exigence (mots exacts de la source) | Source (§ / tableau) | Type | Critère / points | Preuve attendue | Où est la preuve | Statut | Vérifié le |
|---|---|---|---|---|---|---|---|---|
| R280 | "Build a working application with a reasonable framework such as Streamlit or Gradio." | §13 | Obligatoire | C8 | App | `app/` | ⬜ | |
| R281 | "A reviewer must be able to run the workflow from intake through review without manually executing notebook cells. A notebook-only submission is insufficient" | §13 | Obligatoire / Interdit | C8 | Démo | vidéo | ⬜ | |
| R282 | 1 Case selection — "Synthetic case selection or case ID input." | §13 | Obligatoire | C8 | Écran | `app/` | ⬜ | |
| R283 | 2 Transaction details — "The verified fields for the selected case." | §13 | Obligatoire | C8 | Écran | `app/` | ⬜ | |
| R284 | 3 Model score and risk band — "Shown with the threshold used." | §13 | Obligatoire | C8 | Écran | `app/` | ⬜ | |
| R285 | 4 Model and version information — "Model name, version and the date it was trained." | §13 | Obligatoire | C8 | Écran | `app/` | ⬜ | |
| R286 | 5 Supporting evidence — "Evidence items with their source IDs." | §13 | Obligatoire | C8 | Écran | `app/` | ⬜ | |
| R287 | 6 LLM-generated draft summary — "Clearly labelled as an AI draft for human review." | §13 | Obligatoire | C8 | Écran | `app/` | ⬜ | |
| R288 | 7 Evidence and source references — "Linked to the evidence list." | §13 | Obligatoire | C8 | Écran | `app/` | ⬜ | |
| R289 | 8 Uncertainty notes — "Shown, never hidden." | §13 | Obligatoire | C8 | Écran | `app/` | ⬜ | |
| R290 | 9 Validator status — "Pass or fail, with reasons when it fails." | §13 | Obligatoire | C8 | Écran | `app/` | ⬜ | |
| R291 | 10 Human reviewer decision — "Approve and close, escalate or need more information, with an optional comment." | §13 | Obligatoire | C8 | Écran | `app/` | ⬜ | |
| R292 | 11 Audit trail — "Visible in the app and exportable (for example, as CSV or JSON)." | §13 | Obligatoire | C8 | Export | `app/` | ⬜ | |
| R293 | 12 Clear error messages — "Readable messages for invalid input, tool failure and validation failure." | §13 | Obligatoire | C8 | Écrans d'erreur | `app/` ; vidéo | ⬜ | |
| R294 | "The application must also display a visible notice that it is an educational prototype using synthetic data." | §13 | Obligatoire | C8 | Bandeau | `app/` | ⬜ | |

### 2.13 Tests (§14)
| ID | Exigence (mots exacts de la source) | Source (§ / tableau) | Type | Critère / points | Preuve attendue | Où est la preuve | Statut | Vérifié le |
|---|---|---|---|---|---|---|---|---|
| R300 | "Write at least 15 meaningful automated tests, of which at least five target the agent and LLM validation workflow." | §14 | Obligatoire | C9 | Rapport pytest | `tests/` | ⬜ | |
| R301 | "Use a standard test runner such as pytest. Tests must be deterministic and runnable without network access or paid services." | §14 | Obligatoire | C9 | Exécution hors ligne | `tests/` | ⬜ | |
| R302 | Data : "Required columns exist." / "Target has valid values." / "Missing data is handled." / "The target is excluded from predictors." / "The train and test split is reproducible." | §14 tableau | Recommandé | C9 | 5 tests | `tests/` | ⬜ | |
| R303 | Model : "The training pipeline completes." / "The model returns valid scores in the expected range." / "A saved model can be loaded." / "Metrics are calculated on held-out data." | §14 tableau | Recommandé | C9 | 4 tests | `tests/` | ⬜ | |
| R304 | Tool : "Valid tool arguments work." / "Unknown case IDs are handled safely." / "Tool timeouts are handled and failures are logged." / "Invalid state transitions are rejected." | §14 tableau | Recommandé | C6, C9 | 4 tests | `tests/` | ⬜ | |
| R305 | LLM and validator : "Valid JSON passes." / "Malformed JSON fails." / "A missing required field causes rejection." / "An invalid risk label causes rejection." / "Unsupported evidence IDs cause rejection." / "A model-score mismatch is detected." / "A prohibited or unsupported claim is rejected or flagged." | §14 tableau | Recommandé | C7, C9 | 7 tests | `tests/` | ⬜ | |
| R306 | Security : "Prompt injection in a case note is treated as untrusted input." / "Secrets are not written to logs." / "No tool can execute a real financial action." | §14 tableau | Recommandé | C9 | 3 tests | `tests/` | ⬜ | |
| R307 | Application : "Human review decisions are recorded." / "Validation failures are visible." / "Duplicate submissions are handled or documented." | §14 tableau | Recommandé | C8, C9 | 3 tests | `tests/` | ⬜ | |
| R308 | "Submit a test summary (number run, passed, failed) and evidence of failure scenarios: for example, a captured malformed-output case being rejected and an audit entry showing a tool failure." | §14 | Obligatoire | C9 | Résumé + captures | `reports/test_evidence/` | ⬜ | |

### 2.14 Dépôt et README (§16)
| ID | Exigence (mots exacts de la source) | Source (§ / tableau) | Type | Critère / points | Preuve attendue | Où est la preuve | Statut | Vérifié le |
|---|---|---|---|---|---|---|---|---|
| R320 | "Use the following suggested layout. You may adapt it, but the purpose of each area must remain clear." (README.md, requirements.txt, .env.example, data/, notebooks/, src/{data,features,models,agent/{tools,validators},audit}, app/, tests/, artifacts/, reports/, presentation/) | §16 | Recommandé (adaptable) | C9 | Arborescence | dépôt | ⬜ | |
| R321 | data/ : "Do not commit large or restricted data." | §16 | Interdit | C2, C9 | `.gitignore` | dépôt | ⬜ | |
| R322 | notebooks/ : "Notebooks supplement the code and are not a substitute for it." | §16 | Obligatoire | C9 | Code dans `src/` | dépôt | ⬜ | |
| R323 | artifacts/ : "Saved model pipeline, metrics and figures generated by the code." | §16 | Obligatoire | C9 | Fichiers générés | `artifacts/` | ⬜ | |
| R324 | README : "Project overview and the educational-prototype notice." | §16.1 | Obligatoire | C9 | Section | `README.md` | ⬜ | |
| R325 | README : "Environment setup and the list of environment variables." | §16.1 | Obligatoire | C9 | Section | `README.md` | ⬜ | |
| R326 | README : "Dataset acquisition, without redistributing restricted data." | §16.1 | Obligatoire | C9 | Section | `README.md` | ⬜ | |
| R327 | README : "Training, evaluation and model artefact generation." | §16.1 | Obligatoire | C9 | Section | `README.md` | ⬜ | |
| R328 | README : "Application launch and test execution." | §16.1 | Obligatoire | C9 | Section | `README.md` | ⬜ | |
| R329 | README : "Known limitations." | §16.1 | Obligatoire | C9 | Section | `README.md` | ⬜ | |

### 2.15 Planning, originalité et usage de l'IA (§17, §19)
| ID | Exigence (mots exacts de la source) | Source (§ / tableau) | Type | Critère / points | Preuve attendue | Où est la preuve | Statut | Vérifié le |
|---|---|---|---|---|---|---|---|---|
| R340 | "students must still submit all required deliverables" (durée ajustable) | §17 | Obligatoire | Tous | 8 livrables | §3 ci-dessous | ⬜ | |
| R341 | "Agree team roles on Day 1 and record them for the contribution statement." | §17 | Obligatoire | C10 | Rôles notés (seul : tous les rôles) | `template_projet.md` ; livrable H | ⬜ | |
| R342 | "Cite external material properly, and attribute datasets, libraries, models, code and design patterns." | §19.1 | Obligatoire | C10 | Références | `reports/` ; livrable H | ⬜ | |
| R343 | "Do not plagiarise, fabricate results or invent references." | §19.1 | Interdit | Tous | Résultats reproductibles | `artifacts/` | ⬜ | |
| R344 | "Do not misrepresent individual contributions." | §19.1 | Interdit | C10 | Livrable H honnête | livrable H | ⬜ | |
| R345 | "Disclose AI-assisted work according to the course policy." (modèle de déclaration §19.3) | §19.1, §19.3 | Obligatoire | C10 | Déclaration IA | livrable H ; rapport | ⬜ | |
| R346 | "You are responsible for verifying AI-generated code, claims and citations before using them." | §19.1 | Obligatoire | C10 | Temps 2 ✅ par fichier | `Journal_Build.md` | ⬜ | |
| R347 | "Instructors may question individual members to establish understanding of the work." | §19.1 | Obligatoire (oral) | C10 | Banque de questions ✅ | `Banque_Questions.md` | ⬜ | |

### 2.16 Rapport, présentation, vidéo (§15, critère C10) — détail des contenus imposés
| ID | Exigence (mots exacts de la source) | Source (§ / tableau) | Type | Critère / points | Preuve attendue | Où est la preuve | Statut | Vérifié le |
|---|---|---|---|---|---|---|---|---|
| R350 | Rapport, **24** sections (« 23 » corrigé le 2026-11-23 : la liste de l'énoncé §15 C en compte 24 ; plan validé par Erman, J6) : "Executive summary; business problem; stakeholders and requirements; dataset and provenance; EDA; data preparation; feature engineering; traditional ML; Deep Learning; evaluation; explainability; LLM design; agentic architecture; tool design; validation and guardrails; application; testing; security and responsible AI; limitations; recommendations; conclusion; references; individual contribution statement; AI-use statement." | §15 C | Obligatoire | C10 | Table des matières | `reports/` | ⬜ | |
| R351 | Rapport : "All sections are present and consistent with the code. Results match the submitted experiments. References are real." | §15 C | Obligatoire | C10 | Relecture croisée | `reports/` | ⬜ | |
| R352 | Présentation, 14 contenus : "Business problem; solution overview; dataset; EDA insights; ML approach; model results; error analysis; agentic architecture; LLM grounding and validation; application demo; safety and testing; limitations; recommendations; references." | §15 D | Obligatoire | C10 | Diapositives | `presentation/` | ⬜ | |
| R353 | Présentation : "Within the slide range; clear, readable, and consistent with the report." | §15 D | Obligatoire | C10 | 10 à 14 diapositives | `presentation/` | ⬜ | |
| R354 | Vidéo, 6 éléments : "The application running." / "A normal synthetic case." / "A case that needs human review or escalation." / "A malformed-output or failure-handling example." / "The agent workflow and audit trail." / "A brief explanation of results and limitations." | §15 E | Obligatoire | C10, C6 | Minutes notées | `presentation/` (lien) | ⬜ | |
| R355 | Vidéo : "All six items are visible on screen and narrated." | §15 E | Obligatoire | C10 | Vidéo | lien | ⬜ | |
| R356 | Soutenance : "Each member explains their own contribution, design decisions, model results, limitations and the agentic workflow." / "Each member can explain and defend the work they claim." | §15 F | Obligatoire | C10 | Simulation de défense | `08_DEFENSE` (projet) | ⬜ | |
| R357 | Dépôt : "A reviewer can set up, train, launch the app and run the tests from the README alone. No credentials or restricted data are committed." | §15 A | Obligatoire | C9 | Essai sur installation propre | `README.md` | ⬜ | |

### 2.17 Erreurs fréquentes (§20) — chaque « How to avoid » renvoie à son exigence
| Erreur (mots exacts) | « How to avoid it » | Exigence(s) |
|---|---|---|
| Accuracy-only evaluation | "Report the full metric set in Section 8." | R140–R144 |
| Data leakage | "Exclude the target and isFlaggedFraud; fit preprocessing on training data only." | R053, R095–R097 |
| Resampling the test set | "Resample only inside training." | R101 |
| Tuning on the final test set | "Tune and choose thresholds on validation data." | R103, R149 |
| Unexplained threshold selection | "Link the threshold to an operational objective." | R148, R150 |
| LLM claims without evidence | "Require source IDs and validate them." | R188, R190 |
| No actual callable tools | "Implement and demonstrate at least two tools." | R219, R220 |
| No explicit workflow state | "Implement the state machine with tests." | R215, R218 |
| No independent output validation | "Use deterministic validator code." | R191 |
| No human oversight | "Record reviewer decisions." | R248, R291 |
| No failure-case testing | "Test malformed input, timeouts and rejections." | R304, R305, R308 |
| No audit trail | "Log every state change and tool call." | R019, R248 |
| Overclaiming real-world generalisation | "State limits plainly." | R155, R249 |
| Hard-coded secrets | "Use environment variables and .env.example." | R246 |
| Broken README or non-reproducible app | "Test the README on a clean environment." | R357 |

---

## 3. LIVRABLES
| Livrable | Format | Contenu minimum | Critère d'acceptation | Fichier | Statut |
|---|---|---|---|---|---|
| A. Source code repository | "Git repository or archive" | README ; requirements ou environnement ; `.env.example` sans secrets ; instructions d'installation et d'exécution ; code d'entraînement et d'évaluation, application, outils de l'agent, validateur et tests ; instructions de configuration | "A reviewer can set up, train, launch the app and run the tests from the README alone. No credentials or restricted data are committed." | dépôt `capstone-project-1` | ⬜ |
| B. Data documentation | "Markdown or PDF" | Source et conditions ; dictionnaire et qualité des données ; prétraitement et variables ; stratégie train / validation / test ; reproductibilité | "All items are written from the downloaded copy; the seed and splits are stated." | `data/README.md` | ⬜ |
| C. Technical report | "PDF or Word, about 2,500 to 4,000 words unless the instructor specifies otherwise" | Les 24 sections de R350 | "All sections are present and consistent with the code. Results match the submitted experiments. References are real." | `reports/` | ⬜ |
| D. Presentation deck | "Slides, 10 to 14 slides" | Les 14 contenus de R352 | "Within the slide range; clear, readable, and consistent with the report." | `presentation/` | ⬜ |
| E. Demo video | "Video, 6 to 10 minutes" | Les 6 éléments de R354 | "All six items are visible on screen and narrated." | lien dans `presentation/` | ⬜ |
| F. Live presentation and Q&A | "Live session" | Contribution, choix de conception, résultats, limites, workflow agentique | "Each member can explain and defend the work they claim." | — (soutenance) | ⬜ |
| G. Test evidence | "Report appendix or folder" | Résultats des tests ; captures ou logs ; preuves des cas d'échec ; preuves du validateur et de l'audit | "Evidence is real output from the submitted code." | `reports/test_evidence/` | ⬜ |
| H. Contribution and originality statement | "One page" | Contribution de chaque membre ; sources externes de données et de code ; usage des outils d'IA ; bibliothèques et ressources tierces réutilisées | "Complete, honest and signed off by all members." | `reports/` | ⬜ |

## 4. SEUILS CHIFFRÉS (minimums imposés)
| Seuil | Valeur exigée | Valeur atteinte | Preuve |
|---|---|---|---|
| Graphiques annotés | ≥ 6 (§5.2 ; Glance) | | R073 |
| Modèles classiques | baseline + ≥ 2 (§7 ; Glance) | | R110 |
| Outils appelables exécutés | ≥ 2 (§11.4 ; Glance) | | R219 |
| Tests automatisés | ≥ 15 (§14) | | R300 |
| … dont sur le workflow agent / LLM / validation | ≥ 5 (§14) | | R300 |
| Limites connues du jeu de données | ≥ 5 (§3.4) | | R049 |
| Composants du diagramme d'architecture | ≥ 9 (§11.5) | | R225 |
| Éléments d'interface | 12 / 12 (§13) | | R282–R293 |
| Rapport | ≈ 2 500 à 4 000 mots (§15 C) | | Livrable C |
| Présentation | 10 à 14 diapositives (§15 D) | | Livrable D |
| Vidéo | 6 à 10 minutes, 6 éléments (§15 E) | | Livrable E |
| Livrables | 8 / 8 (§15) | | §3 |
| Durée | 15 jours ouvrés, ajustable par l'enseignant (§17) | Remise 2026-11-06 | §6 |

## 5. LISTE DE CONTRÔLE FINALE (reprise telle quelle de la source)
*Data and modelling*
- [ ] Dataset record complete: source, date, licence or terms, counts, target definition and limitations. → R044–R050
- [ ] Own data dictionary created from the downloaded copy. → R051, R055
- [ ] At least six annotated visualisations. → R073, R074
- [ ] Target and isFlaggedFraud excluded from the main predictors. → R053, R095
- [ ] Preprocessing fitted on training data only, inside pipelines; seed and split strategy stated. → R094, R097, R102
- [ ] Baseline plus at least two traditional models; saved pipeline and comparison table. → R110, R126, R127
- [ ] Deep Learning experiment compared fairly, and results reported honestly. → R175, R176
- [ ] Full metric set; threshold chosen on validation data; error analysis and explanations included. → R140–R144, R149, R152, R153

*LLM and agentic workflow*
- [ ] Structured JSON output validated independently of the LLM. → R182, R191
- [ ] At least two callable tools executed within the workflow. → R219, R220
- [ ] Explicit states, invalid transitions rejected, bounded retries and named failure states. → R215, R216, R218
- [ ] Human review decision recorded; audit log exportable. → R248, R291, R292
- [ ] No path to a financial action; neutral language throughout. → R002, R005, R251

*Application and testing*
- [ ] App runs from a documented command without notebooks, and shows all twelve interface elements. → R281–R293
- [ ] At least 15 passing automated tests, including at least five on the validation workflow. → R300
- [ ] Failure scenarios demonstrated and recorded as evidence. → R308, R354

*Documentation and submission*
- [ ] README tested from a clean environment; .env.example present; no secrets or restricted data committed. → R246, R357
- [ ] Technical report with contribution and AI-use statements, and real references only. → R342–R345, R350, R351
- [ ] Presentation deck (10 to 14 slides) and demo video (6 to 10 minutes) prepared. → R352–R355
- [ ] Every team member ready to explain their own contribution in the live Q&A. → R347, R356

## 6. PLANNING IMPOSÉ (si la source en donne un)
Calé sur les 15 jours ouvrés de l'énoncé (§17), du lundi 2026-10-19 (J1) au vendredi 2026-11-06 (J15), sans week-ends.
**Jalons du palier Noté** (= paliers produit, avec un Freeze à chaque jalon) : *proposés par Claude, à valider.*

| Jour / semaine | Attendu par la source | Exigences liées | Statut |
|---|---|---|---|
| J1 — lun. 19 oct. | "Problem framing, scope, dataset confirmation and roles." → "Scope note, dataset record started, role list." **Jalon 1 : Cadrage** | R020, R023, R040–R046, R341 | 🟡 — J1 gelé le 2026-11-04 (`vj1-cadrage-frozen`) : cadrage = `Document_Maitre.md` ; « dataset record » → J2 (n° 15, I04) ; « role list » → P01 à l'enseignant |
| J2–J3 — mar. 20 – mer. 21 oct. | "Data loading, quality checks, data dictionary and EDA." → "Data dictionary and the six or more annotated charts." **Jalon 2 : Données** | R047–R075, R080–R082 | ⬜ |
| J4–J5 — jeu. 22 – ven. 23 oct. | "Preprocessing, baseline and traditional ML." → "Pipelines, baseline and at least two models." | R090–R128 | ⬜ |
| J6 — lun. 26 oct. | "Evaluation, threshold selection and error analysis." → "Comparison table, chosen threshold, error findings." | R140–R155 | ⬜ |
| J7 — mar. 27 oct. | "Deep Learning experiment." → "Neural network results on the same splits." **Jalon 3 : Modèles** | R170–R177 | ⬜ |
| J8–J9 — mer. 28 – jeu. 29 oct. | "Agent architecture, state management and callable tools." → "State machine and at least two working tools." | R210–R233 | ⬜ |
| J10 — ven. 30 oct. | "LLM integration and independent validation." → "Structured drafts passing or failing the validator." **Jalon 4 : Agent et LLM** | R180–R203, R242–R243 | ⬜ |
| J11 — lun. 2 nov. | "Application integration, human review and audit trail." → "End-to-end app run." | R280–R294 | ⬜ |
| J12 — mar. 3 nov. | "Automated tests, safety checks and fixes." → "At least 15 passing tests and failure evidence." **Jalon 5 : Application et tests** | R300–R308, R240–R252 | ⬜ |
| J13 — mer. 4 nov. | "Technical report." → "Complete draft." | R350, R351 | ⬜ |
| J14 — jeu. 5 nov. | "Slides and demo video." → "Deck and recorded demo." | R352–R355 | ⬜ |
| J15 — ven. 6 nov. | "Final testing, repository cleanup, rehearsal and submission." → "Clean repository and all deliverables." **Jalon 6 : Remise** | §5 (20 cases), R357 | ⬜ |

⚠️ **J1 est presque fini** (2026-10-19, soir) et il reste à faire, dans ce chat, `Banque_Questions.md`, `Features_Complet.md`, `Syllabus_Mapping.md` et `Architecture_Projet.md`, puis à créer le dépôt avant le premier code.
Le Jalon 1 déborde donc probablement sur J2. Ce risque va dans `Risk_Register.md`.

---

## VALIDATION
| Validé par | Date | Commentaire |
|---|---|---|
| Erman | 2026-10-19 | v1.0 — jalons §6 et statut « Recommandé » des exemples de tests §14 acceptés tels que proposés |

## ÉCARTS AVEC LE GABARIT v0
- **§2 découpée en 17 sous-tableaux** suivant les sections de l'énoncé (mêmes colonnes) : un seul tableau de plus de 200 lignes serait illisible.
- **§2.17 ajoutée** (erreurs fréquentes → exigences) : l'énoncé contient un tableau « How to avoid it » qui ne crée pas d'exigence nouvelle. Le renvoi évite les doublons.
- **Bloc « Conventions » ajouté en tête** : langue des citations, emplacement « prévu », éléments adaptables (réponse à la question « ne dit pas encore » n° 1).
- **Questions « ne dit pas encore » tranchées** :
  1. écarts autorisés → listés dans les Conventions ;
  2. qui tranche → l'enseignant, sur la plateforme du cours (nom à préciser).
- **Ambiguïtés du gabarit** :
  - (a) la colonne Type n'a pas de valeur pour un objectif d'apprentissage ; j'ai mis « Obligatoire », avec la preuve imposée par l'énoncé ;
  - (b) le gabarit ne dit pas si les « Example tests » (§14) sont obligatoires ; ils sont notés « Recommandé », et seuls les seuils 15 / 5 sont obligatoires ;
  - (c) les numéros R ont des trous volontaires, par bloc, pour pouvoir en insérer sans tout renuméroter.




<br> <br><br><br><br><br><br><br><br><br><br>
MES OBSERVATIONS EN LISANT CE FICHIER: 