"""
Exploratory Data Analysis (EDA) Script for Heart Disease Dataset
Performs statistical profiling, hypothesis testing, and generates high-resolution figures.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Set styling
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'Arial'
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['axes.titlesize'] = 13
plt.rcParams['axes.labelsize'] = 11

OUTPUT_DIR = "figures"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load data
df = pd.read_csv("data/heart_disease.csv")
print(f"Loaded dataset: {df.shape[0]} rows, {df.shape[1]} columns")

# Statistical Profiling
print("\n" + "="*50)
print("DESCRIPTIVE SUMMARY STATISTICS")
print("="*50)
num_cols = ['age', 'blood_pressure', 'cholesterol', 'bmi', 'physical_activity', 'stress_level']
cat_cols = ['sex', 'smoker', 'diabetes', 'family_history']

stats_df = df[num_cols].describe().T[['mean', 'std', 'min', '25%', '50%', '75%', 'max']]
stats_df['skewness'] = df[num_cols].skew()
print(stats_df.round(2))

# Statistical tests
print("\n" + "="*50)
print("HYPOTHESIS TESTING (NUMERICAL: T-TEST / MANN-WHITNEY)")
print("="*50)
for col in num_cols:
    g0 = df[df['heart_disease'] == 0][col]
    g1 = df[df['heart_disease'] == 1][col]
    t_stat, p_val = stats.ttest_ind(g0, g1, equal_var=False)
    u_stat, u_pval = stats.mannwhitneyu(g0, g1)
    print(f"{col:20s}: Mean(HD=0)={g0.mean():.2f}, Mean(HD=1)={g1.mean():.2f} | T-stat={t_stat:.3f}, p={p_val:.4f} | MW-U p={u_pval:.4f}")

print("\n" + "="*50)
print("CHI-SQUARE INDEPENDENCE TESTS (CATEGORICAL)")
print("="*50)
for col in cat_cols:
    contingency = pd.crosstab(df[col], df['heart_disease'])
    chi2, p, dof, _ = stats.chi2_contingency(contingency)
    print(f"{col:20s}: Chi2={chi2:.3f}, dof={dof}, p-value={p:.4f}")

# -------------------------------------------------------------
# FIGURE 1: Target Variable Distribution
# -------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))

counts = df['heart_disease'].value_counts().sort_index()
labels = ['No Heart Disease (0)', 'Heart Disease (1)']
colors = ['#3b82f6', '#ef4444']

# Bar plot
bars = ax1.bar(labels, counts, color=colors, width=0.55, edgecolor='black', linewidth=1.1, alpha=0.9)
for bar in bars:
    height = bar.get_height()
    pct = height / len(df) * 100
    ax1.text(bar.get_x() + bar.get_width()/2., height + 4,
             f"{height} ({pct:.1f}%)", ha='center', va='bottom', fontsize=11, fontweight='bold')
ax1.set_ylim(0, 310)
ax1.set_ylabel("Patient Count", fontsize=11)
ax1.set_title("Class Frequency Distribution", fontsize=12, fontweight='bold')
ax1.grid(axis='y', linestyle='--', alpha=0.7)

# Donut chart
wedges, texts, autotexts = ax2.pie(
    counts, labels=labels, autopct='%1.1f%%', startangle=90,
    colors=colors, wedgeprops=dict(width=0.45, edgecolor='black', linewidth=1.1),
    textprops=dict(fontsize=11)
)
for autotext in autotexts:
    autotext.set_fontsize(11)
    autotext.set_fontweight('bold')
    autotext.set_color('white')
ax2.set_title("Target Proportion Breakdown", fontsize=12, fontweight='bold')

plt.suptitle("Target Variable Distribution (Heart Disease Status)", fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
fig1_path = os.path.join(OUTPUT_DIR, "fig1_target_distribution.png")
plt.savefig(fig1_path, bbox_inches='tight')
plt.close()
print(f"Saved: {fig1_path}")

# -------------------------------------------------------------
# FIGURE 2: Age and BMI Distributions
# -------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

# Age distribution
sns.histplot(data=df, x='age', hue='heart_disease', kde=True, bins=15,
             palette={0: '#3b82f6', 1: '#ef4444'}, ax=axes[0], alpha=0.55, edgecolor='black')
axes[0].set_title("Age Distribution by Heart Disease Status", fontsize=12, fontweight='bold')
axes[0].set_xlabel("Age (Years)", fontsize=11)
axes[0].set_ylabel("Patient Count", fontsize=11)
axes[0].legend(labels=['Heart Disease', 'No Heart Disease'], title="Diagnosis", loc='upper right')

# BMI distribution
sns.histplot(data=df, x='bmi', hue='heart_disease', kde=True, bins=15,
             palette={0: '#3b82f6', 1: '#ef4444'}, ax=axes[1], alpha=0.55, edgecolor='black')
axes[1].axvline(25, color='#eab308', linestyle='--', linewidth=1.5, label='Overweight (BMI ≥ 25)')
axes[1].axvline(30, color='#dc2626', linestyle=':', linewidth=1.5, label='Obese (BMI ≥ 30)')
axes[1].set_title("Body Mass Index (BMI) Distribution", fontsize=12, fontweight='bold')
axes[1].set_xlabel("BMI (kg/m²)", fontsize=11)
axes[1].set_ylabel("Patient Count", fontsize=11)
axes[1].legend(title="Diagnosis & Clinical Thresholds", loc='upper right', fontsize=9)

plt.suptitle("Demographic and Anthropometric Feature Profiles", fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
fig2_path = os.path.join(OUTPUT_DIR, "fig2_age_bmi_distributions.png")
plt.savefig(fig2_path, bbox_inches='tight')
plt.close()
print(f"Saved: {fig2_path}")

# -------------------------------------------------------------
# FIGURE 3: Blood Pressure vs Cholesterol
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 6))

scatter = sns.scatterplot(
    data=df, x='blood_pressure', y='cholesterol', hue='heart_disease',
    palette={0: '#3b82f6', 1: '#ef4444'}, style='heart_disease',
    markers={0: 'o', 1: 's'}, s=50, alpha=0.75, edgecolor='black', linewidth=0.6, ax=ax
)

# Reference lines for medical stages
ax.axvline(130, color='#f97316', linestyle='--', linewidth=1.3, label='Hypertension Stage 1 (130 mmHg)')
ax.axhline(200, color='#8b5cf6', linestyle='--', linewidth=1.3, label='Borderline High Cholesterol (200 mg/dL)')

# Quadrant annotations
ax.text(92, 285, "High Cholesterol\nNormal BP", fontsize=9, color='#6b7280', fontstyle='italic',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#f3f4f6', alpha=0.7))
ax.text(155, 285, "High Risk Quadrant\n(Elevated BP & Chol)", fontsize=9, color='#dc2626', fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#fee2e2', alpha=0.8))

ax.set_title("Clinical Vitals: Blood Pressure vs. Total Serum Cholesterol", fontsize=13, fontweight='bold')
ax.set_xlabel("Blood Pressure (mmHg)", fontsize=11)
ax.set_ylabel("Cholesterol Level (mg/dL)", fontsize=11)
handles, labels = ax.get_legend_handles_labels()
ax.legend(handles, ['No Heart Disease', 'Heart Disease', 'Hypertension (130 mmHg)', 'High Cholesterol (200 mg/dL)'],
          title="Clinical Legend", loc='lower right', frameon=True, fontsize=9)

plt.tight_layout()
fig3_path = os.path.join(OUTPUT_DIR, "fig3_clinical_vitals_scatter.png")
plt.savefig(fig3_path, bbox_inches='tight')
plt.close()
print(f"Saved: {fig3_path}")

# -------------------------------------------------------------
# FIGURE 4: Categorical Risk Factor Breakdown
# -------------------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(10, 8))
cat_list = [('sex', 'Gender (Sex)'), ('smoker', 'Smoking Status'),
            ('diabetes', 'Diabetes Status'), ('family_history', 'Family Cardiac History')]

for idx, (cat_var, title) in enumerate(cat_list):
    ax = axes[idx // 2, idx % 2]
    ct = pd.crosstab(df[cat_var], df['heart_disease'], normalize='index') * 100
    ct.plot(kind='bar', stacked=True, color=['#3b82f6', '#ef4444'],
            ax=ax, edgecolor='black', linewidth=0.9, width=0.55)
    ax.set_title(f"{title} vs Heart Disease", fontsize=11, fontweight='bold')
    ax.set_xlabel("")
    ax.set_ylabel("Proportion (%)", fontsize=10)
    ax.set_ylim(0, 105)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0, fontsize=10)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Add percentage labels inside bars
    for n, c in enumerate(ct.index):
        val0 = ct.loc[c, 0]
        val1 = ct.loc[c, 1]
        ax.text(n, val0/2, f"{val0:.1f}%", ha='center', va='center', color='white', fontweight='bold', fontsize=9)
        ax.text(n, val0 + val1/2, f"{val1:.1f}%", ha='center', va='center', color='white', fontweight='bold', fontsize=9)

    if idx == 0:
        ax.legend(['No Disease', 'Heart Disease'], loc='upper right', fontsize=8)
    else:
        ax.get_legend().remove()

plt.suptitle("Proportional Prevalence Across Categorical Clinical Attributes", fontsize=13, fontweight='bold', y=0.99)
plt.tight_layout()
fig4_path = os.path.join(OUTPUT_DIR, "fig4_categorical_risk_analysis.png")
plt.savefig(fig4_path, bbox_inches='tight')
plt.close()
print(f"Saved: {fig4_path}")

# -------------------------------------------------------------
# FIGURE 5: Correlation Heatmap (One-Hot Encoded)
# -------------------------------------------------------------
encoded_df = pd.get_dummies(df, drop_first=True, dtype=int)
# Rename columns for clarity in publication
encoded_df = encoded_df.rename(columns={
    'sex_Male': 'sex_Male',
    'smoker_Yes': 'smoker_Yes',
    'diabetes_Yes': 'diabetes_Yes',
    'family_history_Yes': 'family_history_Yes'
})

corr = encoded_df.corr()

plt.figure(figsize=(10, 8))
mask = np.triu(np.ones_like(corr, dtype=bool))
cmap = sns.diverging_palette(230, 20, as_cmap=True)

sns.heatmap(corr, mask=mask, cmap=cmap, vmax=.3, vmin=-.3, center=0,
            square=True, linewidths=.8, cbar_kws={"shrink": .8, "label": "Pearson Correlation (r)"},
            annot=True, fmt=".2f", annot_kws={"size": 9})

plt.title("Correlation Matrix of Numerical and One-Hot Encoded Features", fontsize=13, fontweight='bold', pad=15)
plt.xticks(rotation=45, ha='right', fontsize=9)
plt.yticks(rotation=0, fontsize=9)
plt.tight_layout()
fig5_path = os.path.join(OUTPUT_DIR, "fig5_correlation_matrix.png")
plt.savefig(fig5_path, bbox_inches='tight')
plt.close()
print(f"Saved: {fig5_path}")

# -------------------------------------------------------------
# FIGURE 6: Lifestyle Factors (Physical Activity & Stress Level)
# -------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))

sns.boxplot(data=df, x='heart_disease', y='physical_activity', hue='heart_disease',
            palette=['#3b82f6', '#ef4444'], legend=False,
            ax=ax1, width=0.45, boxprops=dict(edgecolor='black', linewidth=1.1))
sns.stripplot(data=df, x='heart_disease', y='physical_activity', color='black', alpha=0.25, jitter=0.2, ax=ax1, size=4)
ax1.set_xticks([0, 1])
ax1.set_xticklabels(['No Disease (0)', 'Heart Disease (1)'])
ax1.set_xlabel("Heart Disease Diagnosis", fontsize=11)
ax1.set_ylabel("Physical Activity Level (0 - 4)", fontsize=11)
ax1.set_title("Physical Activity Distribution", fontsize=12, fontweight='bold')

sns.boxplot(data=df, x='heart_disease', y='stress_level', hue='heart_disease',
            palette=['#3b82f6', '#ef4444'], legend=False,
            ax=ax2, width=0.45, boxprops=dict(edgecolor='black', linewidth=1.1))
sns.stripplot(data=df, x='heart_disease', y='stress_level', color='black', alpha=0.25, jitter=0.2, ax=ax2, size=4)
ax2.set_xticks([0, 1])
ax2.set_xticklabels(['No Disease (0)', 'Heart Disease (1)'])
ax2.set_xlabel("Heart Disease Diagnosis", fontsize=11)
ax2.set_ylabel("Perceived Stress Level (1 - 9)", fontsize=11)
ax2.set_title("Stress Level Distribution", fontsize=12, fontweight='bold')

plt.suptitle("Lifestyle Modifiers: Physical Activity and Stress Level Profiles", fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
fig6_path = os.path.join(OUTPUT_DIR, "fig6_lifestyle_factors.png")
plt.savefig(fig6_path, bbox_inches='tight')
plt.close()
print(f"Saved: {fig6_path}")

print("\nEDA processing and visual artifact generation completed successfully!")
