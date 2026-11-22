"""
Machine Learning Training, Tuning, and Evaluation Pipeline for Heart Disease Classification.
Implements OneHotEncoder, StandardScaler, 5-Fold Stratified Cross-Validation,
Multi-model benchmark (Logistic Regression, Random Forest, Gradient Boosting, SVM, KNN, Decision Tree),
and exports serialized models and publication evaluation figures.
"""

import os
import json
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_validate, GridSearchCV
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, roc_curve, confusion_matrix, classification_report,
    brier_score_loss, balanced_accuracy_score
)

# Styling
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'Arial'
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300

OUTPUT_FIG_DIR = "figures"
OUTPUT_MODEL_DIR = "models"
os.makedirs(OUTPUT_FIG_DIR, exist_ok=True)
os.makedirs(OUTPUT_MODEL_DIR, exist_ok=True)

# 1. Load Dataset
df = pd.read_csv("data/heart_disease.csv")
X = df.drop(columns=['heart_disease'])
y = df['heart_disease']

cat_cols = ['sex', 'smoker', 'diabetes', 'family_history']
num_cols = ['age', 'blood_pressure', 'cholesterol', 'bmi', 'physical_activity', 'stress_level']

print("="*60)
print("DATASET PREPARATION & PREPROCESSING SPECIFICATION")
print("="*60)
print(f"Total Records: {len(df)}")
print(f"Categorical Features: {cat_cols}")
print(f"Numerical Features: {num_cols}")

# Train-Test Split (80% train, 20% test, stratified)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)
print(f"Training Instances: {len(X_train)} (Positive: {y_train.sum()}, Negative: {len(y_train) - y_train.sum()})")
print(f"Test Instances:     {len(X_test)} (Positive: {y_test.sum()}, Negative: {len(y_test) - y_test.sum()})")

# 2. Build ColumnTransformer with OneHotEncoder and StandardScaler
preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), num_cols),
        ('cat', OneHotEncoder(drop='first', sparse_output=False, handle_unknown='ignore'), cat_cols)
    ]
)

# Fit preprocessor to inspect encoded features
preprocessor.fit(X_train)
cat_encoder = preprocessor.named_transformers_['cat']
cat_feature_names = cat_encoder.get_feature_names_out(cat_cols).tolist()
all_feature_names = num_cols + cat_feature_names
print(f"\nOne-Hot Encoded Feature Columns ({len(all_feature_names)} features):")
for idx, fn in enumerate(all_feature_names):
    print(f"  [{idx}] {fn}")

# 3. Model Definition and Hyperparameter Grids
model_definitions = {
    'Logistic Regression': {
        'model': LogisticRegression(random_state=42, max_iter=1000),
        'params': {
            'classifier__C': [0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
            'classifier__solver': ['lbfgs', 'liblinear'],
            'classifier__class_weight': [None, 'balanced']
        }
    },
    'Random Forest': {
        'model': RandomForestClassifier(random_state=42),
        'params': {
            'classifier__n_estimators': [50, 100, 200],
            'classifier__max_depth': [3, 5, 8, None],
            'classifier__min_samples_split': [2, 5, 10],
            'classifier__class_weight': [None, 'balanced']
        }
    },
    'Gradient Boosting': {
        'model': GradientBoostingClassifier(random_state=42),
        'params': {
            'classifier__n_estimators': [50, 100, 150],
            'classifier__learning_rate': [0.01, 0.05, 0.1],
            'classifier__max_depth': [2, 3, 4],
            'classifier__subsample': [0.8, 1.0]
        }
    },
    'Support Vector Machine': {
        'model': SVC(probability=True, random_state=42),
        'params': {
            'classifier__C': [0.1, 0.5, 1.0, 2.0, 5.0],
            'classifier__kernel': ['rbf', 'linear', 'poly'],
            'classifier__gamma': ['scale', 'auto', 0.1]
        }
    },
    'K-Nearest Neighbors': {
        'model': KNeighborsClassifier(),
        'params': {
            'classifier__n_neighbors': [3, 5, 7, 9, 11, 15],
            'classifier__weights': ['uniform', 'distance'],
            'classifier__metric': ['euclidean', 'manhattan']
        }
    },
    'Decision Tree': {
        'model': DecisionTreeClassifier(random_state=42),
        'params': {
            'classifier__max_depth': [2, 3, 4, 6, 8],
            'classifier__min_samples_split': [2, 5, 10],
            'classifier__criterion': ['gini', 'entropy']
        }
    }
}

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

results = {}
best_estimators = {}
test_predictions = {}
test_probabilities = {}

print("\n" + "="*60)
print("TRAINING & HYPERPARAMETER TUNING (5-FOLD STRATIFIED CV)")
print("="*60)

for name, config in model_definitions.items():
    pipe = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', config['model'])
    ])
    
    grid = GridSearchCV(pipe, config['params'], cv=cv, scoring='accuracy', n_jobs=-1)
    grid.fit(X_train, y_train)
    
    best_pipe = grid.best_estimator_
    best_estimators[name] = best_pipe
    
    # 5-fold CV evaluation on train set
    cv_scores = cross_validate(best_pipe, X_train, y_train, cv=cv,
                               scoring=['accuracy', 'precision', 'recall', 'f1', 'roc_auc'])
    
    # Evaluate on held-out test set
    y_pred = best_pipe.predict(X_test)
    y_proba = best_pipe.predict_proba(X_test)[:, 1] if hasattr(best_pipe, "predict_proba") else None
    
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    auc = roc_auc_score(y_test, y_proba) if y_proba is not None else 0.5
    bacc = balanced_accuracy_score(y_test, y_pred)
    brier = brier_score_loss(y_test, y_proba) if y_proba is not None else 0.0
    
    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()
    spec = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    
    test_predictions[name] = y_pred
    test_probabilities[name] = y_proba
    
    results[name] = {
        'best_params': {k.replace('classifier__', ''): v for k, v in grid.best_params_.items()},
        'cv_accuracy_mean': float(cv_scores['test_accuracy'].mean()),
        'cv_accuracy_std': float(cv_scores['test_accuracy'].std()),
        'cv_f1_mean': float(cv_scores['test_f1'].mean()),
        'cv_roc_auc_mean': float(cv_scores['test_roc_auc'].mean()),
        'test_accuracy': float(acc),
        'test_precision': float(prec),
        'test_recall': float(rec),
        'test_f1': float(f1),
        'test_specificity': float(spec),
        'test_balanced_accuracy': float(bacc),
        'test_roc_auc': float(auc),
        'test_brier_score': float(brier),
        'confusion_matrix': {
            'TN': int(tn), 'FP': int(fp), 'FN': int(fn), 'TP': int(tp)
        }
    }
    
    print(f"Model: {name:24s}")
    print(f"  Best Parameters: {results[name]['best_params']}")
    print(f"  Train 5-Fold CV Acc: {results[name]['cv_accuracy_mean']:.4f} (+/- {results[name]['cv_accuracy_std']:.4f})")
    print(f"  Test Accuracy:        {acc:.4f} | Precision: {prec:.4f} | Recall: {rec:.4f} | F1: {f1:.4f} | AUC: {auc:.4f}")
    print(f"  Confusion Matrix:     TN={tn}, FP={fp}, FN={fn}, TP={tp} (Specificity={spec:.4f})\n")

# Determine Best Model (by combination of Test Accuracy, F1, and AUC)
ranked_models = sorted(results.items(), key=lambda item: (item[1]['test_accuracy'] + item[1]['test_f1'] + item[1]['test_roc_auc']), reverse=True)
best_model_name = ranked_models[0][0]
best_pipeline = best_estimators[best_model_name]
print(f"*** TOP RANKED MODEL: {best_model_name} ***")

# Save primary serialized model
joblib.dump(best_pipeline, os.path.join(OUTPUT_MODEL_DIR, "best_model.joblib"))
# Also save Logistic Regression explicitly for transparent odds ratio and lightweight deployment
joblib.dump(best_estimators['Logistic Regression'], os.path.join(OUTPUT_MODEL_DIR, "logistic_regression.joblib"))
joblib.dump(best_estimators['Random Forest'], os.path.join(OUTPUT_MODEL_DIR, "random_forest.joblib"))
print("Saved models to models/ directory.")

# Save metadata JSON
metadata = {
    'dataset': {
        'total_samples': 500,
        'train_samples': len(X_train),
        'test_samples': len(X_test),
        'features_original': list(X.columns),
        'features_transformed': all_feature_names,
        'target': 'heart_disease (0=No, 1=Yes)'
    },
    'top_model': best_model_name,
    'model_evaluations': results
}
with open(os.path.join(OUTPUT_MODEL_DIR, "model_metadata.json"), "w") as f:
    json.dump(metadata, f, indent=2)

# Extract Logistic Regression coefficients for lightweight inference engine
lr_clf = best_estimators['Logistic Regression'].named_steps['classifier']
scaler = preprocessor.named_transformers_['num']
weights_export = {
    'features': all_feature_names,
    'num_cols': num_cols,
    'cat_cols': cat_cols,
    'scaler_means': scaler.mean_.tolist(),
    'scaler_scales': scaler.scale_.tolist(),
    'lr_intercept': float(lr_clf.intercept_[0]),
    'lr_coefficients': lr_clf.coef_[0].tolist(),
    'best_model_name': best_model_name
}
with open(os.path.join(OUTPUT_MODEL_DIR, "inference_weights.json"), "w") as f:
    json.dump(weights_export, f, indent=2)
print("Saved models/inference_weights.json for fast serverless & client-side inference.")

# -------------------------------------------------------------
# FIGURE 7: Model Comparison Across Metrics (Grouped Bar Chart)
# -------------------------------------------------------------
metrics_to_plot = ['test_accuracy', 'test_precision', 'test_recall', 'test_f1', 'test_roc_auc']
metric_labels = ['Accuracy', 'Precision', 'Recall', 'F1-Score', 'ROC-AUC']
model_names_list = list(results.keys())

fig, ax = plt.subplots(figsize=(12, 6))
x = np.arange(len(model_names_list))
width = 0.16
colors = ['#2563eb', '#059669', '#d97706', '#dc2626', '#7c3aed']

for idx, (metric, label, color) in enumerate(zip(metrics_to_plot, metric_labels, colors)):
    values = [results[m][metric] for m in model_names_list]
    rects = ax.bar(x + idx * width - width * 2, values, width, label=label, color=color, edgecolor='black', linewidth=0.8, alpha=0.9)
    for rect in rects:
        h = rect.get_height()
        ax.annotate(f"{h:.2f}",
                    xy=(rect.get_x() + rect.get_width() / 2, h),
                    xytext=(0, 2), textcoords="offset points",
                    ha='center', va='bottom', fontsize=7.5, rotation=90)

ax.set_ylabel("Score (0.0 to 1.0)", fontsize=11)
ax.set_title("Comparative Performance Across 6 Supervised Machine Learning Algorithms", fontsize=13, fontweight='bold', pad=15)
ax.set_xticks(x)
ax.set_xticklabels(model_names_list, fontsize=10, fontweight='bold')
ax.set_ylim(0, 1.08)
ax.axhline(0.5, color='gray', linestyle=':', label='Chance Level (0.50)')
ax.legend(loc='lower right', frameon=True, fontsize=9.5, ncol=3)
ax.grid(axis='y', linestyle='--', alpha=0.7)

plt.tight_layout()
fig7_path = os.path.join(OUTPUT_FIG_DIR, "fig7_model_comparison_metrics.png")
plt.savefig(fig7_path, bbox_inches='tight')
plt.close()
print(f"Saved: {fig7_path}")

# -------------------------------------------------------------
# FIGURE 8: ROC Curves Multi-Model Plot
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 6.5))
roc_palette = ['#2563eb', '#059669', '#d97706', '#dc2626', '#7c3aed', '#0891b2']

for idx, (name, proba) in enumerate(test_probabilities.items()):
    if proba is not None:
        fpr, tpr, _ = roc_curve(y_test, proba)
        auc = results[name]['test_roc_auc']
        ax.plot(fpr, tpr, label=f"{name} (AUC = {auc:.3f})", color=roc_palette[idx], linewidth=2.0)

ax.plot([0, 1], [0, 1], 'k--', linewidth=1.5, label='Random Chance (AUC = 0.500)')
ax.set_xlim([-0.02, 1.02])
ax.set_ylim([-0.02, 1.05])
ax.set_xlabel("False Positive Rate (1 - Specificity)", fontsize=11)
ax.set_ylabel("True Positive Rate (Sensitivity / Recall)", fontsize=11)
ax.set_title("Receiver Operating Characteristic (ROC) Curves", fontsize=13, fontweight='bold', pad=12)
ax.legend(loc='lower right', frameon=True, fontsize=9.5)
ax.grid(True, linestyle='--', alpha=0.7)

plt.tight_layout()
fig8_path = os.path.join(OUTPUT_FIG_DIR, "fig8_roc_curves.png")
plt.savefig(fig8_path, bbox_inches='tight')
plt.close()
print(f"Saved: {fig8_path}")

# -------------------------------------------------------------
# FIGURE 9: Confusion Matrices Grid (6 Models)
# -------------------------------------------------------------
fig, axes = plt.subplots(2, 3, figsize=(14, 8))
axes_flat = axes.flatten()

for idx, (name, pred) in enumerate(test_predictions.items()):
    ax = axes_flat[idx]
    cm = confusion_matrix(y_test, pred)
    tn, fp, fn, tp = cm.ravel()
    
    group_counts = [f"{v:d}" for v in cm.flatten()]
    group_percentages = [f"{v:.1%}" for v in cm.flatten() / np.sum(cm)]
    labels_cm = [f"{v1}\n({v2})" for v1, v2 in zip(group_counts, group_percentages)]
    labels_cm = np.asarray(labels_cm).reshape(2, 2)
    
    sns.heatmap(cm, annot=labels_cm, fmt="", cmap="Blues", cbar=False, ax=ax,
                linewidths=1.2, linecolor='gray',
                xticklabels=['Pred No (0)', 'Pred Yes (1)'],
                yticklabels=['Actual No (0)', 'Actual Yes (1)'],
                annot_kws={"size": 11, "fontweight": 'bold'})
    
    acc = results[name]['test_accuracy']
    f1 = results[name]['test_f1']
    ax.set_title(f"{name}\nAcc: {acc:.2f} | F1: {f1:.2f}", fontsize=11, fontweight='bold')

plt.suptitle("Confusion Matrices Across All Evaluated Classification Models (N = 100 Test)", fontsize=13, fontweight='bold', y=0.99)
plt.tight_layout()
fig9_path = os.path.join(OUTPUT_FIG_DIR, "fig9_confusion_matrices.png")
plt.savefig(fig9_path, bbox_inches='tight')
plt.close()
print(f"Saved: {fig9_path}")

# -------------------------------------------------------------
# FIGURE 10: Feature Importance & Odds Ratios
# -------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

# 1. Random Forest Feature Importance (MDI)
rf_model = best_estimators['Random Forest'].named_steps['classifier']
rf_importances = rf_model.feature_importances_
rf_indices = np.argsort(rf_importances)

ax1.barh(range(len(rf_indices)), rf_importances[rf_indices], color='#2563eb', edgecolor='black', linewidth=0.8, alpha=0.85)
ax1.set_yticks(range(len(rf_indices)))
ax1.set_yticklabels([all_feature_names[i] for i in rf_indices], fontsize=9)
ax1.set_xlabel("Mean Decrease in Impurity (Gini Importance)", fontsize=10)
ax1.set_title("Random Forest: Feature Importance", fontsize=11, fontweight='bold')
ax1.grid(axis='x', linestyle='--', alpha=0.7)

# 2. Logistic Regression Odds Ratios (exp(beta))
lr_coefs = lr_clf.coef_[0]
odds_ratios = np.exp(lr_coefs)
lr_indices = np.argsort(odds_ratios)

bars_lr = ax2.barh(range(len(lr_indices)), odds_ratios[lr_indices],
                   color=['#ef4444' if o > 1.0 else '#3b82f6' for o in odds_ratios[lr_indices]],
                   edgecolor='black', linewidth=0.8, alpha=0.85)
ax2.axvline(1.0, color='black', linestyle='--', linewidth=1.2, label='Neutral Odds Ratio (OR = 1.0)')
ax2.set_yticks(range(len(lr_indices)))
ax2.set_yticklabels([all_feature_names[i] for i in lr_indices], fontsize=9)
ax2.set_xlabel("Odds Ratio (exp(β))", fontsize=10)
ax2.set_title("Logistic Regression: Clinical Odds Ratios", fontsize=11, fontweight='bold')
ax2.legend(loc='lower right', fontsize=8.5)
ax2.grid(axis='x', linestyle='--', alpha=0.7)

plt.suptitle("Predictive Feature Attribution and Clinical Risk Multipliers", fontsize=13, fontweight='bold', y=1.02)
plt.tight_layout()
fig10_path = os.path.join(OUTPUT_FIG_DIR, "fig10_feature_importances.png")
plt.savefig(fig10_path, bbox_inches='tight')
plt.close()
print(f"Saved: {fig10_path}")

print("\nModel training, tuning, serialization, and evaluation figure generation completed successfully!")
