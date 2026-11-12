> COPIE en lecture seule — source : [DOSSIER_PROJET]/03_ressources/references/Capstone_Project_1_Project_Brief.docx (énoncé du capstone, converti en Markdown), version du 2026-10-18. Ne pas modifier ici.

<table>
<tbody>
<tr class="odd">
<td><p><strong>NORTHSTAR PAYMENTS | CAPSTONE PROGRAMME</strong></p>
<p><strong>CAPSTONE PROJECT 1</strong></p>
<p>PROJECT BRIEF</p>
<p><strong>AI-POWERED FINANCIAL FRAUD &amp; RISK INTELLIGENCE PLATFORM</strong></p></td>
</tr>
<tr class="even">
<td></td>
</tr>
</tbody>
</table>

|              |                                                                                             |
| ------------ | ------------------------------------------------------------------------------------------- |
| **Item**     | **Detail**                                                                                  |
| **Audience** | Learners of Machine Learning, Deep Learning, Generative AI and Agentic AI.                  |
| **Status**   | Educational prototype. Synthetic data only. No real payment rails and no financial actions. |
| **Duration** | 15 working days, adjustable by the instructor.                                              |
| **Version**  | 18, October 2026                                                                            |

<table>
<tbody>
<tr class="odd">
<td><p><strong>Educational prototype notice</strong></p>
<p>Northstar Payments is a fictional company. This project must use synthetic data only and must never connect to real payment rails or take financial action.</p></td>
</tr>
</tbody>
</table>

# Project at a Glance

<table>
<tbody>
<tr class="odd">
<td><strong>Item</strong></td>
<td><strong>Summary</strong></td>
</tr>
<tr class="even">
<td><strong>Scenario</strong></td>
<td>Northstar Payments, a fictional digital-payment provider, needs help prioritising potentially fraudulent transactions for investigation.</td>
</tr>
<tr class="odd">
<td><strong>Your task</strong></td>
<td>Build an AI-powered fraud and risk intelligence platform that scores transactions, retrieves evidence, drafts a validated summary and supports human review.</td>
</tr>
<tr class="even">
<td><strong>Default dataset</strong></td>
<td>PaySim synthetic mobile-money transactions (Section 3). Alternatives need instructor approval.</td>
</tr>
<tr class="odd">
<td><strong>Required components</strong></td>
<td><ul>
<li><p>Data engineering and EDA.</p></li>
<li><p>Traditional ML and a Deep Learning experiment.</p></li>
<li><p>Evaluation and explainability.</p></li>
<li><p>LLM investigation-summary assistant.</p></li>
<li><p>Agentic workflow with callable tools and explicit states.</p></li>
<li><p>Application, human review and audit logging.</p></li>
<li><p>Testing, responsible AI and reproducibility.</p></li>
</ul></td>
</tr>
<tr class="even">
<td><strong>Minimum engineering bars</strong></td>
<td>Six or more annotated charts; a baseline plus at least two ML models; at least two callable tools; at least 15 automated tests with at least five on the validation workflow.</td>
</tr>
<tr class="odd">
<td><strong>Deliverables</strong></td>
<td>Repository, data documentation, technical report, presentation deck, demo video, live presentation and Q&amp;A, test evidence, and a contribution and originality statement (Section 15).</td>
</tr>
<tr class="even">
<td><strong>Assessment</strong></td>
<td>100 marks across ten criteria (Section 18). Final grading follows the instructor’s published policy.</td>
</tr>
<tr class="odd">
<td><strong>Hard boundaries</strong></td>
<td>No real data, no autonomous financial action, no accusatory language. The model supports review; it does not prove wrongdoing.</td>
</tr>
</tbody>
</table>

# Contents

Select a section title to jump to it. Section numbers match the cross-references used throughout this brief.

|        |                                                                                                          |
| ------ | -------------------------------------------------------------------------------------------------------- |
| **1**  | [Project Overview and Business Context](#project-overview-and-business-context)                          |
| **2**  | [Learning Objectives](#learning-objectives)                                                              |
| **3**  | [Dataset Recommendations and Requirements](#dataset-recommendations-and-requirements)                    |
| **4**  | [Dataset Understanding and Data Dictionary](#dataset-understanding-and-data-dictionary)                  |
| **5**  | [Exploratory Data Analysis](#exploratory-data-analysis)                                                  |
| **6**  | [Data Preprocessing and Feature Engineering](#data-preprocessing-and-feature-engineering)                |
| **7**  | [Traditional Machine Learning](#traditional-machine-learning)                                            |
| **8**  | [Evaluation Metrics and Business Interpretation](#evaluation-metrics-and-business-interpretation)        |
| **9**  | [Deep Learning Component](#deep-learning-component)                                                      |
| **10** | [Generative AI and LLM Component](#generative-ai-and-llm-component)                                      |
| **11** | [Agentic AI: A Real Workflow, Not Just a Chatbot](#agentic-ai-a-real-workflow-not-just-a-chatbot)        |
| **12** | [Safety, Security and Responsible AI](#safety-security-and-responsible-ai)                               |
| **13** | [Application and User Interface](#application-and-user-interface)                                        |
| **14** | [Testing and Quality Assurance](#testing-and-quality-assurance)                                          |
| **15** | [Required Deliverables](#required-deliverables)                                                          |
| **16** | [Repository Structure and README](#repository-structure-and-readme)                                      |
| **17** | [Timeline: A 15-Working-Day Plan](#timeline-a-15-working-day-plan)                                       |
| **18** | [Assessment Rubric: 100 Marks](#assessment-rubric-100-marks)                                             |
| **19** | [Originality, Similarity Checking and AI-Use Policy](#originality-similarity-checking-and-ai-use-policy) |
| **20** | [Common Failure Modes](#common-failure-modes)                                                            |
| **21** | [Final Acceptance Checklist](#final-acceptance-checklist)                                                |
| **22** | [References and Links](#references-and-links)                                                            |

# 1\. Project Overview and Business Context

## 1.1 The scenario

**Northstar Payments** is a fictional digital-payment provider. Every day it receives a very large volume of transactions, and a small number of them may be fraudulent. The operations team must decide which transactions deserve an investigator’s limited time. This brief asks you to build an educational prototype of the decision-support platform that Northstar’s team would need: a system that scores transactions, gathers structured evidence, drafts a neutral investigation summary, checks that summary independently, and hands the result to a human reviewer.

You are acting as a small applied-AI team. Your work is judged not only on model accuracy but on whether the whole system is sensible, safe, testable and explainable to a non-specialist reader.

## 1.2 The operational problems Northstar faces

1.  A large number of transactions must be evaluated.

2.  Fraudulent transactions are rare compared with legitimate transactions.

3.  Investigators cannot manually investigate every transaction.

4.  False positives waste investigative resources and may inconvenience legitimate customers.

5.  False negatives allow potentially fraudulent activity to go undetected.

6.  A classification score alone does not give an investigator enough context.

7.  Investigators need structured evidence, consistent summaries, traceability and a documented review process.

8.  Generative AI can help draft investigation summaries, but its output must be validated and must not invent evidence.

9.  Agentic AI can coordinate scoring, evidence retrieval, validation and review preparation, but must not make autonomous financial decisions.

## 1.3 What you will build, and why each part matters

The platform combines ten components. The table states what you build, why it matters to the business, and which rubric criterion (Section 18) rewards it.

|                                                    |                                                                                            |                                                                                |            |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------ | ---------- |
| **Component**                                      | **What you build**                                                                         | **Why it matters**                                                             | **Rubric** |
| **A. Data engineering and EDA**                    | A documented, quality-checked dataset, data dictionary and exploratory analysis.           | Poor data understanding produces misleading models and hidden leakage.         | 2          |
| **B. Traditional ML**                              | A baseline plus at least two comparable models inside reproducible pipelines.              | Shows that model choice is evidence-based, not assumed.                        | 3          |
| **C. Deep Learning experiment**                    | A small feed-forward neural network evaluated like the other models.                       | Demonstrates technical breadth and honest comparison.                          | 5          |
| **D. Evaluation and explainability**               | Imbalance-aware metrics, a validation-selected threshold, error analysis and explanations. | Investigators and managers need to understand trade-offs, not a single number. | 4          |
| **E. Generative AI (LLM)**                         | An evidence-grounded assistant that drafts a structured, neutral summary.                  | Saves reviewer time while keeping claims traceable to sources.                 | 7          |
| **F. Agentic AI workflow**                         | A bounded state machine with callable tools, retries and failure states.                   | Coordination, control and traceability beyond a single prompt.                 | 6          |
| **G. Application**                                 | A Streamlit or Gradio app that runs intake through review.                                 | A model nobody can use has no business value.                                  | 8          |
| **H. Human-in-the-loop review**                    | A reviewer screen that records approve, escalate or request-more-information.              | Financial decisions stay with accountable people.                              | 6, 8       |
| **I. Audit logging**                               | Structured, exportable events for every state change and tool call.                        | Traceability is essential for regulated environments.                          | 6, 9       |
| **J. Testing, responsible AI and reproducibility** | At least 15 automated tests, a risk register and a runnable README.                        | Trustworthy systems are tested, documented and repeatable.                     | 9          |

## 1.4 Educational prototype boundaries

<table>
<tbody>
<tr class="odd">
<td><p><strong>Educational prototype - non-negotiable boundaries</strong></p>
<p>This project is an <strong>educational prototype</strong> that uses <strong>synthetic data only</strong>. It must <strong>not</strong> connect to real payment rails and must <strong>not</strong> freeze accounts, block transactions, accuse customers or initiate any financial action, automatically or otherwise.</p>
<p>The platform supports human review. A risk score or an AI-written summary is <strong>not</strong> proof of wrongdoing, and the application must say so clearly.</p></td>
</tr>
</tbody>
</table>

## 1.5 The applied AI lifecycle you will follow

The project follows the complete lifecycle below. A notebook that only trains a classifier covers a small part of the first two phases and is not a sufficient submission.

|                                  |                                                                                                                                                         |                         |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------- |
| **Phase**                        | **Stages**                                                                                                                                              | **Where in this brief** |
| **1. Problem and data**          | Business problem; problem formulation; dataset discovery and understanding; data quality assessment; exploratory data analysis; data cleaning.          | Sections 3 to 6         |
| **2. Modelling**                 | Feature engineering; baseline development; traditional machine learning; Deep Learning experiment; model evaluation; explainability and error analysis. | Sections 6 to 9         |
| **3. Generative and agentic AI** | LLM integration; agentic workflow; tool integration; independent validation and guardrails.                                                             | Sections 10 to 12       |
| **4. Delivery**                  | Application development; human-in-the-loop review; testing and monitoring design; documentation; demonstration and presentation.                        | Sections 13 to 17       |

# 2\. Learning Objectives

By the end of the project you should be able to do each of the following. The right-hand column shows where the evidence will appear in your submission.

|        |                                                                                      |                                              |
| ------ | ------------------------------------------------------------------------------------ | -------------------------------------------- |
| **\#** | **By the end of the project, you can...**                                            | **Primary evidence**                         |
| 1      | Translate a business problem into a machine-learning problem.                        | Technical report: problem formulation        |
| 2      | Find, evaluate, document and prepare a suitable dataset.                             | Data documentation                           |
| 3      | Conduct exploratory data analysis and identify data-quality issues.                  | EDA notebook and report section              |
| 4      | Explain target leakage and prevent it.                                               | Leakage discussion; pipeline code            |
| 5      | Create a reproducible preprocessing and feature-engineering pipeline.                | Pipeline code; data tests                    |
| 6      | Train and compare multiple traditional ML models.                                    | Model comparison table                       |
| 7      | Implement and evaluate a modest Deep Learning experiment.                            | Deep Learning notebook or script; comparison |
| 8      | Select metrics appropriate for imbalanced classification.                            | Evaluation section                           |
| 9      | Explain false positives, false negatives, threshold selection and trade-offs.        | Threshold analysis; error analysis           |
| 10     | Integrate an LLM into an evidence-grounded business workflow.                        | LLM module; prompt template                  |
| 11     | Build a bounded agentic workflow with tools, state, validation and failure handling. | Orchestrator code; demo video                |
| 12     | Implement structured output validation and audit logging.                            | Validator code; audit log export             |
| 13     | Build a usable application around the model and agent workflow.                      | Application; demo video                      |
| 14     | Test normal, edge, malformed-input and failure scenarios.                            | Test suite; test evidence                    |
| 15     | Document limitations, risks, reproducibility and responsible-AI considerations.      | Report; README; risk register                |
| 16     | Present and defend the technical decisions made during the project.                  | Live presentation and Q\&A                   |

# 3\. Dataset Recommendations and Requirements

## 3.1 Rules for choosing data

  - **PaySim is the default dataset** used throughout this brief.

  - You may use an alternative dataset **only with written instructor approval**.

  - Do **not** use real banking data, customer personal information (PII), confidential employer data or any dataset you are not authorised to use.

  - Do **not** assume that a dataset’s licence permits redistribution. Read the terms on the source page and record them. Do not commit the raw data to your repository unless you have verified that the terms allow it.

## 3.2 Primary dataset: PaySim

**Source:** [PaySim synthetic mobile-money transaction dataset on Kaggle](https://www.kaggle.com/datasets/ealaxi/paysim1). The dataset page describes data produced by the PaySim mobile-money simulator.

**Why it is appropriate for this project:**

  - It contains synthetic financial transaction records, so no real customer is affected.

  - It supports supervised fraud classification.

  - It provides both numerical and categorical features.

  - It has an explicit fraud target (isFraud).

  - It supports meaningful class-imbalance analysis, because fraud is a small fraction of transactions.

  - It is suitable for developing an educational risk-investigation workflow.

## 3.3 Alternative datasets (instructor approval required)

<table>
<tbody>
<tr class="odd">
<td><strong>Attribute</strong></td>
<td><strong>PaySim (default)</strong></td>
<td><strong>Credit Card Fraud Detection</strong></td>
<td><strong>IBM AMLSim</strong></td>
</tr>
<tr class="even">
<td><strong>Link</strong></td>
<td><a href="https://www.kaggle.com/datasets/ealaxi/paysim1">kaggle.com/datasets/ealaxi/paysim1</a></td>
<td><a href="https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud">kaggle.com/datasets/mlg-ulb/creditcardfraud</a></td>
<td><a href="https://github.com/IBM/AMLSim">github.com/IBM/AMLSim</a></td>
</tr>
<tr class="odd">
<td><strong>What it contains</strong></td>
<td>Synthetic mobile-money transactions with type, amount, origin and destination balances, a fraud label and a rule flag.</td>
<td>Anonymised card transactions labelled fraudulent or genuine. Most predictors are numeric components produced by a transformation, plus time and amount.</td>
<td>A simulator, not a ready-made table. It generates synthetic banking transactions with known money-laundering patterns.</td>
</tr>
<tr class="even">
<td><strong>Problem it supports</strong></td>
<td>Transaction-level fraud classification and case triage.</td>
<td>Binary fraud classification on anonymised features.</td>
<td>Anti-money-laundering research, including network or graph analysis.</td>
</tr>
<tr class="odd">
<td><strong>Strengths</strong></td>
<td><ul>
<li><p>Readable field names that support business explanations.</p></li>
<li><p>Clear target and strong imbalance.</p></li>
<li><p>Fits the evidence-and-summary workflow.</p></li>
</ul></td>
<td><ul>
<li><p>Widely used and easy to load.</p></li>
<li><p>Small enough for modest hardware.</p></li>
</ul></td>
<td><ul>
<li><p>Realistic AML scenario with network structure.</p></li>
<li><p>Open-source repository.</p></li>
</ul></td>
</tr>
<tr class="even">
<td><strong>Limitations</strong></td>
<td><ul>
<li><p>Synthetic, so patterns may be simulator artefacts.</p></li>
<li><p>Balance fields can act as shortcuts.</p></li>
<li><p>No customer or merchant context.</p></li>
</ul></td>
<td><ul>
<li><p>Anonymised features cannot be explained in business language, which weakens evidence-based summaries.</p></li>
<li><p>Limited time span.</p></li>
</ul></td>
<td><ul>
<li><p>Setup is demanding: the README describes Java and a specific older Python and library stack.</p></li>
<li><p>You must generate and document your own data.</p></li>
</ul></td>
</tr>
<tr class="odd">
<td><strong>Suitability</strong></td>
<td>Beginners and intermediate teams.</td>
<td>Beginners, for modelling only. Poor fit for the LLM evidence workflow.</td>
<td>Advanced teams only.</td>
</tr>
<tr class="even">
<td><strong>Verify before use</strong></td>
<td>Licence and terms on the Kaggle page; attribution requirements; exact file version and row count.</td>
<td>Licence and terms on the Kaggle page; attribution and citation requests.</td>
<td>Repository licence for the code, and the terms that apply to any data you generate; the README’s current setup steps.</td>
</tr>
</tbody>
</table>

## 3.4 Dataset documentation record

Create a dataset record in your data documentation. Every item is mandatory, and you must write it from the copy you actually downloaded, not from this brief.

|                                    |                                                                                                                                            |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| **Item**                           | **What to record**                                                                                                                         |
| **Exact source**                   | The URL, the page title and the file name you used.                                                                                        |
| **Version or download date**       | The date you downloaded the data and any version label shown on the source page.                                                           |
| **Licence and terms**              | The licence or terms exactly as stated on the source page, and what they allow. Write “not stated” if the page does not say; do not guess. |
| **Record count and feature count** | Counts you computed yourself after loading the data.                                                                                       |
| **Target definition**              | Which column is the label, what each value means and how you checked it.                                                                   |
| **Known limitations**              | At least five limitations, including synthetic origin and generalisation risk.                                                             |

# 4\. Dataset Understanding and Data Dictionary

## 4.1 PaySim field reference

The table covers the fields commonly found in PaySim. Field behaviour can differ between copies of a dataset, so you must verify each entry against your own download.

|                |                                                                                             |                         |                                                                   |                                                                                                                                                                       |
| -------------- | ------------------------------------------------------------------------------------------- | ----------------------- | ----------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Field**      | **What it represents**                                                                      | **Role**                | **Possible analytical use**                                       | **Limitations and leakage concerns**                                                                                                                                  |
| step           | A unit of simulated time. The dataset description states that one step is one hour.         | Feature or ordering key | Time-of-simulation patterns; time-aware train and test splitting. | Simulated time, not a real calendar. A random split across steps can leak future behaviour.                                                                           |
| type           | The transaction category, such as cash-in, cash-out, debit, payment or transfer.            | Feature (categorical)   | Fraud-rate comparison by type; one-hot encoding.                  | Fraud may be concentrated in only some types; check this and discuss why.                                                                                             |
| amount         | The transaction amount in the simulator’s currency units.                                   | Feature (numeric)       | Distribution analysis; log transformation; outlier review.        | Heavily skewed; outlier treatment must be justified.                                                                                                                  |
| nameOrig       | A synthetic identifier of the customer who started the transaction.                         | Identifier              | Grouping and de-duplication checks; case identifiers.             | Can encourage memorisation or overfitting. Exclude from predictors unless justified.                                                                                  |
| oldbalanceOrg  | The origin account balance before the transaction.                                          | Feature (numeric)       | Balance-to-amount relationships.                                  | Possibly simulator-specific. Discuss whether the model relies on shortcuts that may not generalise.                                                                   |
| newbalanceOrig | The origin account balance after the transaction.                                           | Feature (numeric)       | Balance-change features.                                          | Same concern. Combined with the old balance and amount, it can reveal simulator rules.                                                                                |
| nameDest       | A synthetic identifier of the transaction recipient.                                        | Identifier              | Case context; counterparty counts, if justified.                  | Same memorisation risk as nameOrig. Identifier style may differ by recipient category.                                                                                |
| oldbalanceDest | The recipient balance before the transaction.                                               | Feature (numeric)       | Recipient-balance patterns.                                       | May be recorded as zero for some recipients; check how often and why.                                                                                                 |
| newbalanceDest | The recipient balance after the transaction.                                                | Feature (numeric)       | Balance-change features.                                          | Same as above; possibly simulator-specific.                                                                                                                           |
| isFraud        | The ground-truth fraud label.                                                               | **Target**              | The label for the primary supervised classification task.         | Must never appear among predictors. Keep it separate from the feature matrix.                                                                                         |
| isFlaggedFraud | A flag produced by a rule inside the simulator. Check the dataset description for the rule. | Derived rule output     | Compare the simulator rule with your model as a baseline.         | Must **not** be casually used as a predictor. Exclude it from the primary feature set unless an alternative experiment is explicitly justified and clearly separated. |

## 4.2 Three points every team must discuss

  - **\`isFraud\`** is the target label for the primary supervised classification task.

  - **\`isFlaggedFraud\`** is a simulator-generated rule flag. It must not be included as a predictor in the main model. Any experiment that uses it must be separated and justified.

  - **\`nameOrig\` and \`nameDest\`** are synthetic identifiers that can encourage memorisation or overfitting. The **balance fields** are potentially informative but possibly simulator-specific, so you must discuss whether your model relies on shortcuts that would not generalise to real financial transactions.

## 4.3 Key concepts you must be able to explain

|                     |                                                                                                                        |                                                                                              |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| **Term**            | **Definition**                                                                                                         | **Example in this project**                                                                  |
| **Feature**         | An input variable the model uses to make a prediction.                                                                 | type, amount, balance fields.                                                                |
| **Target variable** | The outcome the model learns to predict.                                                                               | isFraud.                                                                                     |
| **Identifier**      | A value that names a record or entity and carries no general meaning.                                                  | nameOrig, nameDest, a synthetic case ID.                                                     |
| **Derived feature** | A new variable computed from existing ones.                                                                            | A balance-change value computed from old and new balances.                                   |
| **Data leakage**    | Information in the training inputs that would not be available at prediction time, or that reveals the label directly. | Using isFraud or a column computed from it as a predictor; fitting a scaler on the test set. |
| **Training data**   | Data used to fit model parameters.                                                                                     | The training partition.                                                                      |
| **Validation data** | Data used to compare models, tune settings and choose the threshold.                                                   | The validation partition.                                                                    |
| **Test data**       | Data kept untouched until the final evaluation, to estimate performance on unseen cases.                               | The held-out test partition.                                                                 |

## 4.4 Your own data dictionary

You must create your own final data dictionary based on the exact version of the dataset you download. Include the column name, data type, meaning, role (feature, identifier or target), missing-value count, whether it is used in the model, and any leakage or fairness concern.

# 5\. Exploratory Data Analysis

EDA is a structured stage, not a collection of random plots. It must produce findings that change what you do next, such as which columns you exclude, which features you create and how you split the data.

## 5.1 Required investigations

|        |                                           |                                                                                   |
| ------ | ----------------------------------------- | --------------------------------------------------------------------------------- |
| **\#** | **Investigation**                         | **Minimum expectation**                                                           |
| 1      | Dataset dimensions and schema             | Row and column counts, column names and a short schema table.                     |
| 2      | Data types                                | Check each type against its meaning; correct any mismatches.                      |
| 3      | Missing values                            | Count by column; state the handling decision or why none is needed.               |
| 4      | Duplicate records                         | Define what counts as a duplicate, count them and justify your action.            |
| 5      | Target distribution and class imbalance   | Class counts and percentages; implications for metrics and training.              |
| 6      | Transaction types                         | Counts and share by type.                                                         |
| 7      | Transaction amount distribution           | Summary statistics and a distribution plot; discuss skew.                         |
| 8      | Fraud rate by transaction type            | Fraud rate per type; discuss where fraud appears and where it does not.           |
| 9      | Patterns across simulation steps          | Volume and fraud rate over step; discuss any time pattern.                        |
| 10     | Relationships among numerical features    | A correlation view of selected numeric fields, with limits of correlation stated. |
| 11     | Potential leakage and simulator artefacts | Identify features or relationships that look too good; explain the risk.          |
| 12     | Outliers and unusual observations         | Detect, inspect and justify the treatment or non-treatment.                       |

## 5.2 Visualisation and interpretation

Produce **at least six meaningful visualisations**. Candidates include fraud versus non-fraud counts, transaction count by type, amount distributions, fraud rate by type, transaction volume across steps, a correlation heatmap for selected numeric variables, amount distributions by target, and false-positive and false-negative analysis after modelling.

<table>
<tbody>
<tr class="odd">
<td><p><strong>Every important chart needs an interpretation</strong></p>
<p>For each chart, write what it shows, the business implication for Northstar, and the decision it informs (for example, a feature choice, a metric choice or a data-quality fix).</p>
<p><strong>A chart without interpretation should not receive full credit.</strong></p></td>
</tr>
</tbody>
</table>

# 6\. Data Preprocessing and Feature Engineering

## 6.1 Required workflow

|        |                                                     |                                                                |
| ------ | --------------------------------------------------- | -------------------------------------------------------------- |
| **\#** | **Requirement**                                     | **Evidence expected**                                          |
| 1      | Validate input columns and data types.              | Validation function and a data test.                           |
| 2      | Handle missing values where applicable.             | Documented rule, or documented finding that none exist.        |
| 3      | Investigate duplicate records.                      | Count and decision recorded.                                   |
| 4      | Identify and justify outlier treatment.             | Written justification tied to the business context.            |
| 5      | Encode categorical variables.                       | Encoder inside the pipeline.                                   |
| 6      | Scale features where the chosen model requires it.  | Scaler inside the pipeline for the relevant models only.       |
| 7      | Consider useful derived features where justified.   | Rationale and leakage check for each derived feature.          |
| 8      | Create reproducible preprocessing pipelines.        | scikit-learn Pipeline and ColumnTransformer, or an equivalent. |
| 9      | Preserve the target separately from the predictors. | Separate X and y; a test that the target is not in X.          |
| 10     | Avoid target leakage.                               | Leakage review in the report.                                  |
| 11     | Never fit preprocessing on the test set.            | Fit on training data only; show where in the code.             |
| 12     | Document every major transformation.                | Preprocessing documentation.                                   |

## 6.2 Pipelines, scaling and resampling

  - Use **scikit-learn Pipelines** or an equivalent reproducible approach so that the same transformations are applied in training, evaluation and the application.

  - Scaling is usually important for Logistic Regression and neural networks, but is often less critical for tree-based models. State what you did for each model and why.

  - If you use class weights or oversampling, apply resampling **only inside the training process**. Never resample the validation or test data.

## 6.3 Splitting strategy

  - State your **splitting strategy and random seed** in the report and README. For example, a stratified train, validation and test split, with the exact proportions you chose.

  - The **final test set must remain untouched** until final evaluation. Use training and validation data for model selection, tuning and threshold choice.

  - **Time-aware evaluation is encouraged where feasible.** Randomly splitting simulated transaction sequences can give an overly optimistic picture of future performance. If you can, run an additional experiment that trains on earlier steps and evaluates on later steps, and compare it with the random split.

# 7\. Traditional Machine Learning

Build a baseline and compare **at least two traditional models**. The table lists the recommended options.

|                                             |                               |                     |                            |                                                                                        |
| ------------------------------------------- | ----------------------------- | ------------------- | -------------------------- | -------------------------------------------------------------------------------------- |
| **Model**                                   | **Role**                      | **Scaling needed?** | **Categorical handling**   | **Points to discuss**                                                                  |
| **Majority-class or other simple baseline** | Required reference point.     | No                  | Not applicable             | Why a model must beat it in a meaningful way, not only on accuracy.                    |
| **Logistic Regression**                     | Interpretable linear model.   | Usually yes         | Encode inside the pipeline | Coefficients, class weighting, regularisation, linear assumptions.                     |
| **Random Forest**                           | Non-linear ensemble of trees. | Usually no          | Encode inside the pipeline | Class weighting, depth and tree count, feature importance limits.                      |
| **Gradient Boosting or XGBoost (optional)** | Often strong on tabular data. | Usually no          | Encode inside the pipeline | Tuning effort and overfitting. XGBoost is not required if installation is impractical. |

## 7.1 What you must explain

  - Why each model was selected, and its main strengths and limitations.

  - Whether it requires feature scaling, and how categorical variables are handled.

  - How hyperparameters were selected, using training and validation data only.

  - How class imbalance was addressed.

  - Why the final model was selected, with reference to your validation evidence.

## 7.2 What you must produce

  - Reproducible training code that runs from a documented command.

  - A **saved model pipeline** (preprocessing and model together) that the scoring tool loads.

  - A **model comparison table** and documented parameters.

  - A clear validation and test strategy.

# 8\. Evaluation Metrics and Business Interpretation

## 8.1 Why accuracy alone is not enough

When fraud is rare, a model that labels every transaction as legitimate can still achieve very high accuracy while catching no fraud at all. Accuracy therefore hides the outcome that matters most. You must report imbalance-aware metrics and explain each in plain business language.

## 8.2 Required metrics

|                                               |                                                                              |                                                               |
| --------------------------------------------- | ---------------------------------------------------------------------------- | ------------------------------------------------------------- |
| **Metric**                                    | **Plain business meaning**                                                   | **What to watch for**                                         |
| **Confusion matrix**                          | A count of how many cases fell into each of the four outcomes below.         | Always report counts, not only percentages.                   |
| **True positives (TP)**                       | Fraudulent transactions correctly flagged.                                   | Fraud caught.                                                 |
| **True negatives (TN)**                       | Legitimate transactions correctly left alone.                                | Usually huge; it inflates accuracy.                           |
| **False positives (FP)**                      | Legitimate transactions flagged in error.                                    | Wasted investigator time and possible customer inconvenience. |
| **False negatives (FN)**                      | Fraudulent transactions missed.                                              | Undetected loss and risk.                                     |
| **Precision**                                 | Of the transactions we flagged, how many were really fraud.                  | Low precision overloads investigators.                        |
| **Recall**                                    | Of all real fraud, how much we caught.                                       | Low recall lets fraud through.                                |
| **F1-score**                                  | A single balance of precision and recall.                                    | Hides which side is weaker; always report both.               |
| **ROC-AUC**                                   | How well the model ranks fraud above legitimate cases across all thresholds. | Can look good on very imbalanced data.                        |
| **Precision-Recall AUC or average precision** | Ranking quality focused on the rare fraud class.                             | Usually more informative than ROC-AUC under strong imbalance. |

## 8.3 Business trade-offs you must discuss

  - What happens when a legitimate transaction is incorrectly flagged, and what happens when a fraudulent transaction is missed.

  - Why increasing recall may increase false positives, and why increasing precision may reduce the number of fraud cases caught.

  - Why a model score is **not automatically a calibrated probability**.

  - Why the decision threshold should reflect a documented operational objective, for example the review capacity of the investigation team.

## 8.4 Threshold selection

Choose and document a decision threshold using **validation data, not the final test set**. State the operational objective the threshold serves, show the precision-recall trade-off across candidate thresholds, and then report the final test results once, at the chosen threshold.

## 8.5 Error analysis and explainability

  - Inspect false positives and false negatives, group them by transaction type, amount range or other meaningful categories, and explain likely reasons.

  - Provide feature importance or another suitable explanation technique, such as permutation importance, model coefficients or SHAP.

  - Do **not** claim that feature importance establishes causality. It describes what the model uses, not what causes fraud.

  - Write an honest discussion of limitations, including why results on synthetic data may not carry over to real banking data.

# 9\. Deep Learning Component

Include a modest Deep Learning experiment to demonstrate technical breadth. It is **not** expected to beat the traditional models.

|                      |                                                                                                                                |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| **Aspect**           | **Requirement**                                                                                                                |
| **Model**            | A small feed-forward neural network (multilayer perceptron).                                                                   |
| **Framework**        | PyTorch or TensorFlow/Keras.                                                                                                   |
| **Inputs**           | Appropriately encoded and scaled, using the same leakage rules as Section 6.                                                   |
| **Output and loss**  | Binary classification output with a suitable loss function and optimiser; explain how you handle class imbalance.              |
| **Monitoring**       | Validation monitoring (for example, early stopping), recorded learning curves and fixed random seeds.                          |
| **Comparison**       | Evaluate on the **same splits, metrics and threshold procedure** as the traditional models and add it to the comparison table. |
| **Honest reporting** | Report the actual result, even if the neural network performs worse than Random Forest or Gradient Boosting.                   |

<table>
<tbody>
<tr class="odd">
<td><p><strong>Instructor exception</strong></p>
<p>If the course schedule or computing environment cannot support Deep Learning, the instructor may reallocate the marks for this component (criterion 5) to other criteria. That decision must be announced explicitly in writing. Teams must not drop the component on their own.</p></td>
</tr>
</tbody>
</table>

# 10\. Generative AI and LLM Component

Build an **LLM-powered investigation-summary assistant**. It drafts a structured summary for a human reviewer. It does not decide anything.

## 10.1 What the assistant receives

  - A synthetic case identifier.

  - The ML model score and the selected risk band.

  - A limited set of verified transaction features.

  - Evidence retrieved from an approved local store.

  - Relevant model and version information.

## 10.2 Required structured output

The assistant must return JSON containing at least the fields below. This is an illustrative schema, not a fixed result. You may expand it, but the output must remain structured and validated.

> {
> 
> "case\_id": "synthetic identifier",
> 
> "risk\_level": "low | medium | high",
> 
> "model\_score": 0.0,
> 
> "model\_version": "version identifier",
> 
> "evidence": \[\],
> 
> "summary": "neutral summary",
> 
> "uncertainties": \[\],
> 
> "recommended\_review\_steps": \[\],
> 
> "source\_ids": \[\],
> 
> "validation\_status": "pending | passed | failed"
> 
> }

## 10.3 Concepts you must explain and implement

|                                   |                                                                                                                 |
| --------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| **Concept**                       | **Role in this project**                                                                                        |
| **System instructions**           | Fixed rules that define the assistant’s task, tone and prohibitions. They are written by you, not by case data. |
| **User input**                    | The case request. Treat it as untrusted.                                                                        |
| **Context supplied to the model** | Only the verified fields and approved evidence you choose to pass in. Less context means less risk.             |
| **Prompt template**               | A versioned template with clearly separated instruction and data sections.                                      |
| **Structured output**             | A defined JSON schema that the validator checks.                                                                |
| **Grounding**                     | Every statement traces to a supplied field or evidence item.                                                    |
| **Hallucination**                 | A confident statement not supported by supplied data. The validator must be able to catch the common forms.     |
| **Evidence references**           | Source IDs that link each claim to an approved evidence item.                                                   |
| **Independent output validation** | Deterministic code, separate from the LLM, that accepts or rejects the draft.                                   |

## 10.4 What the LLM must not do

  - Invent transaction details or evidence.

  - Change the official model score.

  - Make unsupported allegations, or claim that a transaction is definitely fraudulent.

  - Execute financial actions.

  - Treat untrusted case text as trusted instructions.

If evidence is insufficient, the assistant must **state the uncertainty and recommend human review** rather than fill the gap.

## 10.5 Deployment disclosure

State whether you use a hosted API or a local model, and document the following. Automated tests must not depend on a paid API or network access, so design the LLM client so that a fake client can be substituted in tests.

|                   |                                                                                                |
| ----------------- | ---------------------------------------------------------------------------------------------- |
| **Consideration** | **What to document**                                                                           |
| **Privacy**       | What data leaves your machine, and why only synthetic data is sent.                            |
| **Cost**          | Approximate cost per case or per run, or confirmation that a local model has no per-call cost. |
| **Latency**       | Typical response time and what happens on a timeout.                                           |
| **Reliability**   | Behaviour on malformed output, rate limits and unavailable services.                           |

# 11\. Agentic AI: A Real Workflow, Not Just a Chatbot

This is a **major requirement**. An agentic implementation is not an LLM prompt wrapped in a user interface. It is a controlled workflow in which software components, some deterministic and some model-driven, are coordinated through explicit state.

## 11.1 Chatbot wrapper versus bounded workflow

|                      |                                               |                                                               |
| -------------------- | --------------------------------------------- | ------------------------------------------------------------- |
| **Aspect**           | **A prompt wrapped in a UI (not sufficient)** | **Bounded agentic workflow (required)**                       |
| **State**            | Held implicitly in the conversation.          | Explicit case state with defined transitions.                 |
| **Tools**            | Described in text, or none.                   | Genuinely callable functions with defined inputs and outputs. |
| **Control flow**     | Decided by the model alone.                   | Decided by an orchestrator you wrote; the LLM is one step.    |
| **Validation**       | None, or the LLM checks itself.               | Independent, deterministic validation.                        |
| **Failure handling** | Unplanned.                                    | Bounded retries, timeouts and named failure states.           |
| **Oversight**        | Optional.                                     | A recorded human review step.                                 |
| **Traceability**     | Chat history.                                 | Structured audit events.                                      |

## 11.2 Required capabilities

  - Explicit state, workflow orchestration and callable tools with defined inputs and outputs.

  - Validation, bounded retries and error handling.

  - Human-in-the-loop review and audit logging.

A deterministic state machine with selected LLM calls is acceptable, and is often preferable to an unconstrained autonomous agent.

## 11.3 Workflow and states

Recommended workflow: case intake, input validation, ML risk scoring, evidence retrieval, LLM summary drafting, independent output validation, human review, then audit logging and final case status.

> RECEIVED -\> SCORED -\> EVIDENCE\_READY -\> DRAFTED -\> VALIDATED -\> HUMAN\_REVIEW
> 
> HUMAN\_REVIEW -\> CLOSED | ESCALATED | NEEDS\_MORE\_INFORMATION
> 
> Any step -\> FAILED (tool error or timeout after bounded retries)
> 
> DRAFTED -\> VALIDATION\_REJECTED (validator fails after bounded retries)

|                                                 |                                                 |                                                                          |
| ----------------------------------------------- | ----------------------------------------------- | ------------------------------------------------------------------------ |
| **State**                                       | **Meaning**                                     | **Entered when**                                                         |
| **RECEIVED**                                    | The case passed input validation.               | A case ID is submitted and checked.                                      |
| **SCORED**                                      | The official model score exists.                | The scoring tool returned a valid result.                                |
| **EVIDENCE\_READY**                             | Approved evidence is attached.                  | The evidence tool returned results, or an explicit “no evidence” result. |
| **DRAFTED**                                     | An LLM draft exists but is not trusted.         | The LLM returned parseable output.                                       |
| **VALIDATED**                                   | The draft passed independent validation.        | The validator reports success.                                           |
| **HUMAN\_REVIEW**                               | Waiting for, or recording, a reviewer decision. | A validated case is queued for review.                                   |
| **CLOSED, ESCALATED, NEEDS\_MORE\_INFORMATION** | Final reviewer outcomes.                        | A reviewer decision is recorded.                                         |
| **FAILED, VALIDATION\_REJECTED**                | Terminal failure states.                        | Retries are exhausted; the cause is logged and visible in the UI.        |

Invalid transitions, for example jumping from RECEIVED to VALIDATED, must be rejected and tested.

## 11.4 Tools

Implement **at least two genuinely callable tools** that the workflow actually invokes. Describing tools only in documentation does not count. You must demonstrate real execution in the demo video and the test evidence. Four tools are suggested.

|                                     |                                                            |                                                             |                                                              |
| ----------------------------------- | ---------------------------------------------------------- | ----------------------------------------------------------- | ------------------------------------------------------------ |
| **Tool**                            | **Purpose**                                                | **Inputs**                                                  | **Outputs**                                                  |
| **score\_transaction()**            | Load the saved pipeline and model and score a transaction. | Validated transaction features.                             | Score, threshold, risk band and model version.               |
| **retrieve\_case\_evidence()**      | Fetch approved synthetic evidence for a case.              | Case identifier.                                            | Evidence items with source IDs, or an explicit empty result. |
| **validate\_investigation\_json()** | Check the LLM draft.                                       | Draft JSON plus the official score, evidence set and rules. | Pass or fail with specific reasons.                          |
| **write\_audit\_event()**           | Record a structured audit event.                           | Case ID, state, actor, action and result.                   | Confirmation of the stored event.                            |

## 11.5 Architecture diagram

Your report must include an architecture diagram containing at least the components shown below: user or reviewer, application, workflow orchestrator, ML scoring tool, evidence retrieval tool, LLM, independent validator, audit store and human review step. The figure is a reference, and your own diagram should reflect your actual design.

![Reviewer uses the application, which calls the workflow orchestrator. The orchestrator calls the scoring tool, evidence retrieval tool, LLM drafting and the independent validator, passes validated cases to human review, and writes every step to the audit store.](media/image1.png "Architecture diagram")

*Figure 1. Reference architecture for the agentic workflow.*

## 11.6 Design decisions you must explain

  - Why the chosen tasks benefit from orchestration, and which tasks remain deterministic.

  - Why the LLM must **not** calculate the official score.

  - How state is tracked.

  - How failures, timeouts and bounded retries are handled.

  - How duplicate calls or retries are handled, for example with an idempotency key built from the case ID and step.

  - How the system decides when human review is required, and how review priority is set.

In this prototype every case that reaches VALIDATED proceeds to HUMAN\_REVIEW. You must also document a review-routing policy, such as the table below, and justify the conditions you choose.

|                                                        |                                                                                        |
| ------------------------------------------------------ | -------------------------------------------------------------------------------------- |
| **Condition (examples)**                               | **Suggested routing**                                                                  |
| **High risk band, or score close to the threshold**    | Priority review with the uncertainty notes highlighted.                                |
| **Evidence missing or insufficient**                   | Review with a prompt to request more information.                                      |
| **Validator rejected the draft after bounded retries** | VALIDATION\_REJECTED; no summary shown as trusted; reviewer sees structured data only. |
| **Tool failure or timeout after bounded retries**      | FAILED; error visible in the UI and logged.                                            |

# 12\. Safety, Security and Responsible AI

Include a dedicated risk section in your report. The register below lists the topics you must cover, with the minimum control for each. Add risks specific to your design.

|                                         |                                                        |                                                                                                      |
| --------------------------------------- | ------------------------------------------------------ | ---------------------------------------------------------------------------------------------------- |
| **Risk**                                | **Why it matters**                                     | **Minimum required control**                                                                         |
| **Synthetic data and privacy**          | Real personal data must never enter the project.       | Use only the approved synthetic data; add a repository check for sensitive-looking fields.           |
| **Prompt injection**                    | Case text may contain instructions aimed at the model. | Treat case notes as untrusted data; keep instructions and data separate; test with an injected note. |
| **Hallucinations**                      | The model may state unsupported facts.                 | Ground in supplied evidence; validate references.                                                    |
| **Malformed structured output**         | Broken JSON can crash or mislead the workflow.         | Schema validation and bounded retries.                                                               |
| **Unsupported claims**                  | Accusatory language can harm people.                   | Validator checks for prohibited or definitive wording.                                               |
| **Data leakage**                        | Inflates results and hides real performance.           | Pipeline design, leakage review and data tests.                                                      |
| **Model bias**                          | Systematic errors may affect groups unevenly.          | Examine error patterns across available categories and discuss the limits of the data.               |
| **False positives and false negatives** | Both have real business cost.                          | Documented threshold and error analysis.                                                             |
| **Model drift**                         | Patterns change over time.                             | Design a monitoring plan describing what you would track and when you would retrain.                 |
| **API key protection**                  | Leaked keys cause cost and misuse.                     | Secrets in environment variables, .env ignored by version control, .env.example without values.      |
| **Excessive tool permissions**          | A tool that can do too much is a risk.                 | Tools are read-only or scoped; no tool performs a financial action.                                  |
| **Tool failures and timeouts**          | Dependencies fail.                                     | Timeouts, bounded retries and named failure states.                                                  |
| **Auditability**                        | Decisions must be traceable.                           | Structured audit events for each state change and reviewer decision.                                 |
| **Human oversight**                     | Accountability must stay with people.                  | Mandatory recorded review before any case outcome.                                                   |
| **Synthetic-to-real generalisation**    | Simulator patterns may not hold in real data.          | State this limitation prominently and avoid production-readiness claims.                             |

## 12.1 Mandatory controls

  - Input validation, schema validation and evidence-reference validation.

  - Bounded retries and clear failure states.

  - Secrets stored outside source control.

  - No real customer data and no autonomous financial action.

  - Neutral, non-accusatory language, and a clear disclosure that the model supports review rather than proving wrongdoing.

## 12.2 Neutral language

|                                  |                                                                                      |
| -------------------------------- | ------------------------------------------------------------------------------------ |
| **Avoid**                        | **Prefer**                                                                           |
| “This customer committed fraud.” | “This transaction received a high risk score and is recommended for review.”         |
| “The recipient is a criminal.”   | “The recipient account appears in two evidence items; further checks are suggested.” |
| “Block the account.”             | “A reviewer may wish to consider next steps.” (The system never takes the action.)   |

## 12.3 Frameworks to consult

  - [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)

  - [OWASP Top 10 for Large Language Model Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/)

# 13\. Application and User Interface

Build a working application with a reasonable framework such as Streamlit or Gradio. A reviewer must be able to run the workflow from intake through review **without manually executing notebook cells**. A notebook-only submission is insufficient unless the instructor explicitly approves it.

|        |                                |                                                                                 |
| ------ | ------------------------------ | ------------------------------------------------------------------------------- |
| **\#** | **Interface element**          | **Minimum requirement**                                                         |
| 1      | Case selection                 | Synthetic case selection or case ID input.                                      |
| 2      | Transaction details            | The verified fields for the selected case.                                      |
| 3      | Model score and risk band      | Shown with the threshold used.                                                  |
| 4      | Model and version information  | Model name, version and the date it was trained.                                |
| 5      | Supporting evidence            | Evidence items with their source IDs.                                           |
| 6      | LLM-generated draft summary    | Clearly labelled as an AI draft for human review.                               |
| 7      | Evidence and source references | Linked to the evidence list.                                                    |
| 8      | Uncertainty notes              | Shown, never hidden.                                                            |
| 9      | Validator status               | Pass or fail, with reasons when it fails.                                       |
| 10     | Human reviewer decision        | Approve and close, escalate or need more information, with an optional comment. |
| 11     | Audit trail                    | Visible in the app and exportable (for example, as CSV or JSON).                |
| 12     | Clear error messages           | Readable messages for invalid input, tool failure and validation failure.       |

The application must also display a visible notice that it is an educational prototype using synthetic data.

# 14\. Testing and Quality Assurance

Write **at least 15 meaningful automated tests**, of which **at least five target the agent and LLM validation workflow**. Use a standard test runner such as pytest. Tests must be deterministic and runnable without network access or paid services.

<table>
<tbody>
<tr class="odd">
<td><strong>Category</strong></td>
<td><strong>Example tests</strong></td>
</tr>
<tr class="even">
<td><strong>Data</strong></td>
<td><ul>
<li><p>Required columns exist.</p></li>
<li><p>Target has valid values.</p></li>
<li><p>Missing data is handled.</p></li>
<li><p>The target is excluded from predictors.</p></li>
<li><p>The train and test split is reproducible.</p></li>
</ul></td>
</tr>
<tr class="odd">
<td><strong>Model</strong></td>
<td><ul>
<li><p>The training pipeline completes.</p></li>
<li><p>The model returns valid scores in the expected range.</p></li>
<li><p>A saved model can be loaded.</p></li>
<li><p>Metrics are calculated on held-out data.</p></li>
</ul></td>
</tr>
<tr class="even">
<td><strong>Tool</strong></td>
<td><ul>
<li><p>Valid tool arguments work.</p></li>
<li><p>Unknown case IDs are handled safely.</p></li>
<li><p>Tool timeouts are handled and failures are logged.</p></li>
<li><p>Invalid state transitions are rejected.</p></li>
</ul></td>
</tr>
<tr class="odd">
<td><strong>LLM and validator</strong></td>
<td><ul>
<li><p>Valid JSON passes.</p></li>
<li><p>Malformed JSON fails.</p></li>
<li><p>A missing required field causes rejection.</p></li>
<li><p>An invalid risk label causes rejection.</p></li>
<li><p>Unsupported evidence IDs cause rejection.</p></li>
<li><p>A model-score mismatch is detected.</p></li>
<li><p>A prohibited or unsupported claim is rejected or flagged.</p></li>
</ul></td>
</tr>
<tr class="even">
<td><strong>Security</strong></td>
<td><ul>
<li><p>Prompt injection in a case note is treated as untrusted input.</p></li>
<li><p>Secrets are not written to logs.</p></li>
<li><p>No tool can execute a real financial action.</p></li>
</ul></td>
</tr>
<tr class="odd">
<td><strong>Application</strong></td>
<td><ul>
<li><p>Human review decisions are recorded.</p></li>
<li><p>Validation failures are visible.</p></li>
<li><p>Duplicate submissions are handled or documented.</p></li>
</ul></td>
</tr>
</tbody>
</table>

Submit a **test summary** (number run, passed, failed) and **evidence of failure scenarios**: for example, a captured malformed-output case being rejected and an audit entry showing a tool failure.

# 15\. Required Deliverables

Submit all eight deliverables. The table states the format, minimum content and acceptance criteria for each.

<table>
<tbody>
<tr class="odd">
<td><strong>Deliverable</strong></td>
<td><strong>Format</strong></td>
<td><strong>Minimum content</strong></td>
<td><strong>Acceptance criteria</strong></td>
</tr>
<tr class="even">
<td><strong>A. Source code repository</strong></td>
<td>Git repository or archive</td>
<td><ul>
<li><p>Readable, modular code and a README.</p></li>
<li><p>Requirements or environment file and .env.example without secrets.</p></li>
<li><p>Setup and run instructions.</p></li>
<li><p>Training and evaluation code, application, agent tools, validator and tests.</p></li>
<li><p>Configuration instructions.</p></li>
</ul></td>
<td>A reviewer can set up, train, launch the app and run the tests from the README alone. No credentials or restricted data are committed.</td>
</tr>
<tr class="odd">
<td><strong>B. Data documentation</strong></td>
<td>Markdown or PDF</td>
<td><ul>
<li><p>Dataset source and terms.</p></li>
<li><p>Data dictionary and data-quality summary.</p></li>
<li><p>Preprocessing and feature-engineering documentation.</p></li>
<li><p>Train, validation and test strategy.</p></li>
<li><p>Reproducibility details.</p></li>
</ul></td>
<td>All items are written from the downloaded copy; the seed and splits are stated.</td>
</tr>
<tr class="even">
<td><strong>C. Technical report</strong></td>
<td>PDF or Word, about 2,500 to 4,000 words unless the instructor specifies otherwise</td>
<td>Executive summary; business problem; stakeholders and requirements; dataset and provenance; EDA; data preparation; feature engineering; traditional ML; Deep Learning; evaluation; explainability; LLM design; agentic architecture; tool design; validation and guardrails; application; testing; security and responsible AI; limitations; recommendations; conclusion; references; individual contribution statement; AI-use statement.</td>
<td>All sections are present and consistent with the code. Results match the submitted experiments. References are real.</td>
</tr>
<tr class="odd">
<td><strong>D. Presentation deck</strong></td>
<td>Slides, 10 to 14 slides</td>
<td>Business problem; solution overview; dataset; EDA insights; ML approach; model results; error analysis; agentic architecture; LLM grounding and validation; application demo; safety and testing; limitations; recommendations; references.</td>
<td>Within the slide range; clear, readable, and consistent with the report.</td>
</tr>
<tr class="even">
<td><strong>E. Demo video</strong></td>
<td>Video, 6 to 10 minutes</td>
<td><ul>
<li><p>The application running.</p></li>
<li><p>A normal synthetic case.</p></li>
<li><p>A case that needs human review or escalation.</p></li>
<li><p>A malformed-output or failure-handling example.</p></li>
<li><p>The agent workflow and audit trail.</p></li>
<li><p>A brief explanation of results and limitations.</p></li>
</ul></td>
<td>All six items are visible on screen and narrated.</td>
</tr>
<tr class="odd">
<td><strong>F. Live presentation and Q&amp;A</strong></td>
<td>Live session</td>
<td>Each member explains their own contribution, design decisions, model results, limitations and the agentic workflow.</td>
<td>Each member can explain and defend the work they claim.</td>
</tr>
<tr class="even">
<td><strong>G. Test evidence</strong></td>
<td>Report appendix or folder</td>
<td><ul>
<li><p>Test results.</p></li>
<li><p>Selected screenshots or logs.</p></li>
<li><p>Failure-case evidence.</p></li>
<li><p>Validator and audit-log evidence.</p></li>
</ul></td>
<td>Evidence is real output from the submitted code.</td>
</tr>
<tr class="odd">
<td><strong>H. Contribution and originality statement</strong></td>
<td>One page</td>
<td><ul>
<li><p>Each member’s contribution.</p></li>
<li><p>External data and code sources.</p></li>
<li><p>AI tool usage.</p></li>
<li><p>Reused libraries and third-party assets.</p></li>
</ul></td>
<td>Complete, honest and signed off by all members.</td>
</tr>
</tbody>
</table>

# 16\. Repository Structure and README

Use the following suggested layout. You may adapt it, but the purpose of each area must remain clear.

> capstone-project-1/
> 
> README.md
> 
> requirements.txt
> 
> .env.example
> 
> data/
> 
> README.md
> 
> notebooks/
> 
> src/
> 
> data/
> 
> features/
> 
> models/
> 
> agent/
> 
> tools/
> 
> validators/
> 
> audit/
> 
> app/
> 
> tests/
> 
> artifacts/
> 
> reports/
> 
> presentation/

|                              |                                                                                                             |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------- |
| **Folder**                   | **Purpose**                                                                                                 |
| **data/**                    | Instructions for obtaining the dataset and your data documentation. Do not commit large or restricted data. |
| **notebooks/**               | EDA and experiments. Notebooks supplement the code and are not a substitute for it.                         |
| **src/data/, src/features/** | Loading, validation and the preprocessing and feature-engineering pipeline.                                 |
| **src/models/**              | Training, evaluation, threshold selection and model saving or loading.                                      |
| **src/agent/**               | The orchestrator and state machine, the LLM client, tools/ and validators/.                                 |
| **src/audit/**               | Audit event writing and export.                                                                             |
| **app/**                     | The Streamlit or Gradio application.                                                                        |
| **tests/**                   | Automated tests.                                                                                            |
| **artifacts/**               | Saved model pipeline, metrics and figures generated by the code.                                            |
| **reports/, presentation/**  | The technical report, test evidence, slides and video link.                                                 |

## 16.1 What the README must cover

  - Project overview and the educational-prototype notice.

  - Environment setup and the list of environment variables.

  - Dataset acquisition, without redistributing restricted data.

  - Training, evaluation and model artefact generation.

  - Application launch and test execution.

  - Known limitations.

# 17\. Timeline: A 15-Working-Day Plan

The plan below is a practical guide. **Instructors may adjust the duration, but students must still submit all required deliverables.** Agree team roles on Day 1 and record them for the contribution statement.

|         |                                                              |                                                       |
| ------- | ------------------------------------------------------------ | ----------------------------------------------------- |
| **Day** | **Focus**                                                    | **Expected output**                                   |
| 1       | Problem framing, scope, dataset confirmation and roles.      | Scope note, dataset record started, role list.        |
| 2 to 3  | Data loading, quality checks, data dictionary and EDA.       | Data dictionary and the six or more annotated charts. |
| 4 to 5  | Preprocessing, baseline and traditional ML.                  | Pipelines, baseline and at least two models.          |
| 6       | Evaluation, threshold selection and error analysis.          | Comparison table, chosen threshold, error findings.   |
| 7       | Deep Learning experiment.                                    | Neural network results on the same splits.            |
| 8 to 9  | Agent architecture, state management and callable tools.     | State machine and at least two working tools.         |
| 10      | LLM integration and independent validation.                  | Structured drafts passing or failing the validator.   |
| 11      | Application integration, human review and audit trail.       | End-to-end app run.                                   |
| 12      | Automated tests, safety checks and fixes.                    | At least 15 passing tests and failure evidence.       |
| 13      | Technical report.                                            | Complete draft.                                       |
| 14      | Slides and demo video.                                       | Deck and recorded demo.                               |
| 15      | Final testing, repository cleanup, rehearsal and submission. | Clean repository and all deliverables.                |

# 18\. Assessment Rubric: 100 Marks

Marks are allocated across ten criteria. The strong-work and weak-work columns describe what assessors look for at the top and bottom of each range.

|        |                                                 |           |                                                                                                                                                                                                                     |                                                                                                      |
| ------ | ----------------------------------------------- | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| **\#** | **Criterion**                                   | **Marks** | **Strong work looks like**                                                                                                                                                                                          | **Weak work looks like**                                                                             |
| 1      | Problem framing and business relevance          | 8         | Clear translation of the business problem into an ML task; stakeholders, costs of error and success measures are explicit.                                                                                          | Generic problem statement; business impact or error costs not discussed.                             |
| 2      | Data quality, EDA and data governance           | 12        | Complete dataset record and data dictionary; all required investigations; six or more charts with business interpretation; leakage and licence considerations addressed.                                            | Missing checks, charts without interpretation, or dataset terms not recorded.                        |
| 3      | Traditional ML and feature engineering          | 14        | Leak-free, reproducible pipelines; baseline plus at least two models; justified encoding, scaling and imbalance handling; tuning on validation data only; saved pipeline.                                           | Manual preprocessing, no baseline, tuning on test data or unexplained choices.                       |
| 4      | Evaluation and explainability                   | 12        | Full imbalance-aware metrics; validation-selected, documented threshold; thoughtful error analysis; explanations without causal claims; honest limitations.                                                         | Accuracy-focused evaluation; threshold not justified; explanations overclaimed.                      |
| 5      | Deep Learning experiment                        | 6         | Sound small network with monitoring; same evaluation as other models; honest comparison.                                                                                                                            | Different evaluation setup, no validation monitoring or results not compared.                        |
| 6      | Agentic AI workflow and callable tools          | 16        | Explicit states and transitions; at least two genuinely callable tools used in the workflow; bounded retries; failure states; idempotency; human review; audit log; architecture diagram; clear design explanation. | Chatbot with a prompt only; tools described but not executed; no explicit state or failure handling. |
| 7      | LLM grounding, structured output and validation | 10        | Schema-conforming output; evidence references checked; score consistency and prohibited-claim checks; prompt-injection handling; deployment considerations disclosed.                                               | Free-text output, no independent validation or unsupported claims allowed through.                   |
| 8      | Application and usability                       | 7         | All twelve interface elements; end-to-end run without notebooks; clear errors; exportable audit trail.                                                                                                              | Notebook-only or missing key elements; unclear errors.                                               |
| 9      | Testing, documentation and reproducibility      | 7         | At least 15 meaningful tests with at least five on the validation workflow; failure evidence; README that works from a clean setup; seeds recorded.                                                                 | Few or trivial tests; README does not run; results not reproducible.                                 |
| 10     | Report, presentation, demo and individual Q\&A  | 8         | Clear, consistent, complete report; effective deck and demo; each member explains their own work.                                                                                                                   | Inconsistent or incomplete materials; a member cannot explain their contribution.                    |
|        | **Total**                                       | **100**   |                                                                                                                                                                                                                     |                                                                                                      |

*Check: 8 + 12 + 14 + 12 + 6 + 16 + 10 + 7 + 7 + 8 = 100 marks.*

## 18.1 Marking guidance for common issues

The guidance below indicates how assessors may reflect these issues within the criteria above. It does not create automatic penalties. **Final grading follows the instructor’s published policy and the institution’s regulations.**

|                                               |                                                                                                                          |
| --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| **Issue**                                     | **Marking guidance**                                                                                                     |
| **Data leakage**                              | Reflect in criteria 3 and 4; assess how serious the leakage is and whether the team recognised and corrected it.         |
| **Fabricated results**                        | Refer to the institution’s academic-integrity process. Results must come from documented, reproducible experiments.      |
| **Missing required deliverables**             | Assess the affected criteria on the evidence available and apply the institution’s late or incomplete submission policy. |
| **A chatbot falsely presented as agentic AI** | Reflect in criteria 6 and 7; expect limited credit if there is no real state, tools or validation.                       |
| **Lack of individual understanding**          | Adjust individual marks following the live Q\&A, according to the instructor’s policy on team marking.                   |
| **Unreproducible code**                       | Reflect in criterion 9, and in the other criteria where results cannot be verified.                                      |
| **Unsupported production-readiness claims**   | Reflect in criteria 4 and 10; the work is an educational prototype on synthetic data.                                    |

# 19\. Originality, Similarity Checking and AI-Use Policy

The institution’s official policy takes precedence over this summary. This section describes what is expected in this project.

## 19.1 What is expected

  - Cite external material properly, and attribute datasets, libraries, models, code and design patterns.

  - Do not plagiarise, fabricate results or invent references.

  - Do not misrepresent individual contributions.

  - Disclose AI-assisted work according to the course policy.

  - You are responsible for verifying AI-generated code, claims and citations before using them.

  - Instructors may question individual members to establish understanding of the work.

## 19.2 Similarity reports

A Turnitin or other similarity percentage is **not automatically proof of plagiarism**. Instructors should review the matching content and its context, including references, common technical terminology, quoted material and boilerplate. This brief sets no universal acceptable percentage.

## 19.3 Suggested AI-use disclosure

<table>
<tbody>
<tr class="odd">
<td><p><strong>Disclosure template</strong></p>
<p>“We used [tool/model] for [specific tasks]. We reviewed, tested, and modified the output. All reported results were generated from our documented experiments. External sources and reused material are cited. Individual team-member contributions are listed below.”</p></td>
</tr>
</tbody>
</table>

# 20\. Common Failure Modes

|                                            |                                              |                                                                                 |
| ------------------------------------------ | -------------------------------------------- | ------------------------------------------------------------------------------- |
| **Mistake**                                | **Why it is a problem**                      | **How to avoid it**                                                             |
| **Accuracy-only evaluation**               | Hides missed fraud in an imbalanced dataset. | Report the full metric set in Section 8.                                        |
| **Data leakage**                           | Inflates results.                            | Exclude the target and isFlaggedFraud; fit preprocessing on training data only. |
| **Resampling the test set**                | Makes the test no longer representative.     | Resample only inside training.                                                  |
| **Tuning on the final test set**           | Makes the test estimate optimistic.          | Tune and choose thresholds on validation data.                                  |
| **Unexplained threshold selection**        | The operating point cannot be defended.      | Link the threshold to an operational objective.                                 |
| **LLM claims without evidence**            | Invites hallucinated allegations.            | Require source IDs and validate them.                                           |
| **No actual callable tools**               | The workflow is only a prompt.               | Implement and demonstrate at least two tools.                                   |
| **No explicit workflow state**             | Flow is untraceable and untestable.          | Implement the state machine with tests.                                         |
| **No independent output validation**       | The LLM grades itself.                       | Use deterministic validator code.                                               |
| **No human oversight**                     | Violates the core requirement.               | Record reviewer decisions.                                                      |
| **No failure-case testing**                | Only the happy path is known to work.        | Test malformed input, timeouts and rejections.                                  |
| **No audit trail**                         | Decisions cannot be reconstructed.           | Log every state change and tool call.                                           |
| **Overclaiming real-world generalisation** | Results come from synthetic data.            | State limits plainly.                                                           |
| **Hard-coded secrets**                     | Credentials can leak.                        | Use environment variables and .env.example.                                     |
| **Broken README or non-reproducible app**  | Reviewers cannot run the work.               | Test the README on a clean environment.                                         |

# 21\. Final Acceptance Checklist

Tick each item before submission. An unticked item is a signal to fix the work, not to hide the gap.

### Data and modelling

☐ Dataset record complete: source, date, licence or terms, counts, target definition and limitations.

☐ Own data dictionary created from the downloaded copy.

☐ At least six annotated visualisations.

☐ Target and isFlaggedFraud excluded from the main predictors.

☐ Preprocessing fitted on training data only, inside pipelines; seed and split strategy stated.

☐ Baseline plus at least two traditional models; saved pipeline and comparison table.

☐ Deep Learning experiment compared fairly, and results reported honestly.

☐ Full metric set; threshold chosen on validation data; error analysis and explanations included.

### LLM and agentic workflow

☐ Structured JSON output validated independently of the LLM.

☐ At least two callable tools executed within the workflow.

☐ Explicit states, invalid transitions rejected, bounded retries and named failure states.

☐ Human review decision recorded; audit log exportable.

☐ No path to a financial action; neutral language throughout.

### Application and testing

☐ App runs from a documented command without notebooks, and shows all twelve interface elements.

☐ At least 15 passing automated tests, including at least five on the validation workflow.

☐ Failure scenarios demonstrated and recorded as evidence.

### Documentation and submission

☐ README tested from a clean environment; .env.example present; no secrets or restricted data committed.

☐ Technical report with contribution and AI-use statements, and real references only.

☐ Presentation deck (10 to 14 slides) and demo video (6 to 10 minutes) prepared.

☐ Every team member ready to explain their own contribution in the live Q\&A.

# 22\. References and Links

## 22.1 Datasets

  - [PaySim synthetic financial datasets (Kaggle)](https://www.kaggle.com/datasets/ealaxi/paysim1)

  - [Credit Card Fraud Detection (Kaggle)](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud)

  - [IBM AMLSim (GitHub)](https://github.com/IBM/AMLSim)

## 22.2 Risk and security frameworks

  - [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)

  - [OWASP Top 10 for Large Language Model Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/)

Links were checked when this brief was prepared. Pages can change, so confirm the licence and terms on each source page yourself and cite what you use.
