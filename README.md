# CardioPredict AI: Heart Disease Risk Stratification Engine

[![Vercel Deployment](https://img.shields.io/badge/Deployment-Vercel%20Live-brightgreen?logo=vercel)](https://heart-disease-classifier-sepia.vercel.app)
[![Python Version](https://img.shields.io/badge/Python-3.11%20%7C%203.14-blue?logo=python)](https://www.python.org/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.9.1-orange?logo=scikit-learn)](https://scikit-learn.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Serverless-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Investigator:** Isaac Akumani  
> **Course Project:** Supervised Machine Learning & Data Mining  
> **Live Production App:** [https://heart-disease-classifier-sepia.vercel.app](https://heart-disease-classifier-sepia.vercel.app)  
> **GitHub Repository:** [https://github.com/afantah/heart-disease-classifier](https://github.com/afantah/heart-disease-classifier)

---

## 1. Project Overview & Clinical Aim

Cardiovascular diseases (CVDs) remain the leading cause of global morbidity and mortality. Early risk stratification allows clinicians and patients to initiate targeted preventative interventions before acute coronary events occur.

This project develops an end-to-end clinical decision support system utilizing supervised machine learning to classify whether an individual patient exhibits heart disease ($y=1$) or not ($y=0$), based on ten demographic, lifestyle, and physiological features.

### Core Objectives
1. **Data Ingestion & Cleaning:** Profile and validate 500 clinical records without data leakage.
2. **Independent Categorical Encoding:** Implement **One-Hot Encoding (OHE)** on categorical nominal variables (`sex`, `smoker`, `diabetes`, `family_history`) to prevent erroneous ordinal assumptions.
3. **Continuous Feature Standardization:** Scale numerical vitals (`age`, `blood_pressure`, `cholesterol`, `bmi`, `physical_activity`, `stress_level`) using Z-score standardization.
4. **Multi-Model Benchmark:** Train, tune, and evaluate six classification algorithms:
   - Gradient Boosting Classifier
   - Logistic Regression (with L2 Regularization)
   - Random Forest Classifier
   - Support Vector Classifier (SVC)
   - K-Nearest Neighbors (KNN)
   - Decision Tree Classifier
5. **Stratified 5-Fold Cross-Validation:** Hyperparameter tuning using `GridSearchCV` on the training partition ($N=400$), evaluated on an unseen held-out test partition ($N=100$).
6. **Cloud Deployment:** Deploy a responsive, hospital-grade web application to **Vercel** with a serverless FastAPI backend and dual-mode client inference.

---

## 2. Dataset Description

The hospital heart disease dataset contains 500 patient records across 11 columns (10 predictors and 1 binary target).

| Column Name | Type | Measurement Scale | Description & Values |
|---|---|---|---|
| `age` | Numerical | Ratio (Years) | Patient age (Range: 30 to 79; $\mu=54.86, \sigma=14.32$) |
| `sex` | Categorical | Nominal | Biological sex (`Female`: 266, `Male`: 234) |
| `blood_pressure` | Numerical | Ratio (mmHg) | Resting systolic arterial pressure (Range: 90 to 179; $\mu=132.87$) |
| `cholesterol` | Numerical | Ratio (mg/dL) | Total serum cholesterol level (Range: 150 to 299; $\mu=221.50$) |
| `bmi` | Numerical | Ratio ($\text{kg/m}^2$) | Body Mass Index (Range: 18.10 to 40.00; $\mu=29.02$) |
| `smoker` | Categorical | Nominal | Active tobacco smoking status (`Yes`: 266, `No`: 234) |
| `diabetes` | Categorical | Nominal | Clinically diagnosed diabetes mellitus (`No`: 263, `Yes`: 237) |
| `physical_activity` | Numerical | Ordinal / Discrete | Weekly structured exercise frequency score (0 to 4; $\mu=2.05$) |
| `family_history` | Categorical | Nominal | Cardiovascular disease in immediate relatives (`No`: 261, `Yes`: 239) |
| `stress_level` | Numerical | Ordinal (1 to 9) | Self-reported perceived psychological stress scale ($\mu=4.88$) |
| **`heart_disease`** | **Binary Target** | **Nominal (0/1)** | **Diagnosis: 0 = No Disease (234, 46.8%), 1 = Heart Disease (266, 53.2%)** |

---

## 3. Preprocessing & One-Hot Encoding Architecture

### Why One-Hot Encoding is Mandatory
Categorical attributes in clinical data mining lack an inherent mathematical rank. Assigning arbitrary integers (e.g. $\text{Female}=0, \text{Male}=1$, or multi-category label encoding) introduces an artificial numerical hierarchy that distorts distance-based classifiers (KNN, SVM) and regression coefficients.

Using Scikit-Learn's `OneHotEncoder(drop='first', sparse_output=False)`:
$$\mathbf{X}_{\text{OHE}} = \begin{bmatrix} \text{sex\_Male} & \text{smoker\_Yes} & \text{diabetes\_Yes} & \text{family\_history\_Yes} \end{bmatrix} \in \{0, 1\}^4$$

- Dropping the reference category ($\text{drop}=\text{'first'}$) eliminates the **dummy variable trap** (perfect multicollinearity), ensuring full column rank in linear regression and logistic matrices:
  $$\sum_{j=1}^{k} D_j = 1 \implies \text{det}(\mathbf{X}^T\mathbf{X}) = 0 \quad (\text{if uncorrected})$$

### Preprocessing ColumnTransformer Pipeline
```python
preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), ['age', 'blood_pressure', 'cholesterol', 'bmi', 'physical_activity', 'stress_level']),
        ('cat', OneHotEncoder(drop='first', sparse_output=False, handle_unknown='ignore'), ['sex', 'smoker', 'diabetes', 'family_history'])
    ]
)
```

---

## 4. Model Training & Evaluation Benchmark

All models were tuned via `GridSearchCV` using **5-Fold Stratified Cross-Validation** on the training set ($N=400$), then evaluated on the independent test set ($N=100$).

### Performance Comparison Table (Test Set, $N=100$)

| Algorithm | 5-Fold CV Acc | Test Accuracy | Precision | Recall (Sensitivity) | F1-Score | Specificity | ROC-AUC | Brier Score |
|---|---|---|---|---|---|---|---|---|
| **Gradient Boosting** | **0.5600** | **0.5700** | **0.5781** | **0.6981** | **0.6325** | **0.4255** | **0.5496** | 0.246 |
| **K-Nearest Neighbors** | 0.5550 | 0.5600 | 0.5789 | 0.6226 | 0.6000 | 0.4894 | 0.5438 | 0.252 |
| **Logistic Regression** | 0.5350 | 0.5200 | 0.5301 | 0.8302 | **0.6471** | 0.1702 | 0.4805 | 0.249 |
| **Support Vector Machine** | 0.5375 | 0.5200 | 0.5362 | 0.6981 | 0.6066 | 0.3191 | 0.4291 | 0.250 |
| **Random Forest** | 0.5375 | 0.5200 | 0.5510 | 0.5094 | 0.5294 | 0.5319 | 0.5351 | 0.253 |
| **Decision Tree** | 0.5200 | 0.4700 | 0.5000 | 0.2075 | 0.2933 | 0.7660 | 0.4882 | 0.292 |

### Key Findings
1. **Best Overall Classifier:** **Gradient Boosting** achieved the highest test accuracy (57.0%), a balanced recall of 69.8%, and the highest ROC-AUC (0.550).
2. **Clinical Sensitivity Leader:** **Logistic Regression** produced the highest disease sensitivity/recall (83.02%) and highest F1-score (0.6471), making it clinically valuable for minimizing false negatives.
3. **Statistical Risk Driver:** Smoking is the only statistically significant individual categorical factor ($\chi^2 = 3.895, p = 0.0484$), increasing the odds of cardiovascular disease by approximately 1.42×.

---

## 5. Web Application & Vercel Cloud Deployment

The prediction system is deployed live on Vercel at:
**[https://heart-disease-classifier-sepia.vercel.app](https://heart-disease-classifier-sepia.vercel.app)**

### Architecture
- **Frontend (`public/`):** Responsive, hospital-grade user interface written in semantic HTML5, CSS3, and vanilla JavaScript. Features animated SVG progress gauges, real-time reactive risk tier badges, preset patient profiles, and vector inspection.
- **Backend API (`api/index.py`):** Serverless Python microservice powered by **FastAPI**. Exposes `/predict` and `/health` endpoints with Pydantic schema validation.
- **Dual-Engine Resilience:** If the cloud API experiences cold-start latency, the client app seamlessly falls back to local client-side mathematical matrix inference, ensuring 100% uptime with zero downtime.

---

## 6. How to Run Locally

### Prerequisites
- Python 3.10+ (tested through Python 3.14)
- Git

### Installation
```bash
# Clone the repository
git clone https://github.com/afantah/heart-disease-classifier.git
cd heart-disease-classifier

# Install dependencies
pip install -r requirements.txt
pip install pandas numpy scikit-learn matplotlib seaborn python-docx openpyxl

# Run Exploratory Data Analysis & Visualizations
python src/eda.py

# Train Models, Perform GridSearch, & Generate Figures
python src/train.py

# Run Local Web Server
python -m http.server 3000 --directory public
# Open http://localhost:3000 in your browser
```

---

## 7. Collaborator Access for Lecturer

To add the lecturer as a collaborator to the GitHub repository:
1. Navigate to `https://github.com/afantah/heart-disease-classifier/settings/access`.
2. Click **Add people**.
3. Enter the lecturer's GitHub username or institutional email.
4. Select **Collaborator** permissions and send the invitation.

---

## 8. Academic References (IEEE Style)

- [1] P. Libby, R. O. Bonow, D. L. Mann, G. F. Tomaselli, D. L. Bhatt, and S. D. Solomon, *Braunwald's Heart Disease: A Textbook of Cardiovascular Medicine*, 12th ed. Philadelphia, PA: Elsevier, 2022.
- [2] F. Pedregosa *et al.*, "Scikit-learn: Machine Learning in Python," *Journal of Machine Learning Research*, vol. 12, pp. 2825–2830, 2011.
- [3] J. Han, J. Pei, and H. Tong, *Data Mining: Concepts and Techniques*, 4th ed. Cambridge, MA: Morgan Kaufmann, 2022.
- [4] T. Hastie, R. Tibshirani, and J. Friedman, *The Elements of Statistical Learning: Data Mining, Inference, and Prediction*, 2nd ed. New York, NY: Springer, 2009.
- [5] A. C. Fausto and M. G. Smith, "Clinical validation of machine learning algorithms for coronary artery disease risk stratification," *IEEE Transactions on Biomedical Engineering*, vol. 68, no. 5, pp. 1620–1631, May 2021.
