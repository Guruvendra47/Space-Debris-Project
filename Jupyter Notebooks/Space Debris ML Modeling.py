# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# DBTITLE 1,Space Debris ML Modeling
# MAGIC %md
# MAGIC # Space Debris ML Modeling
# MAGIC
# MAGIC Phase 5 of the Space Debris Analysis project. This notebook trains and evaluates three classification models on the cleaned dataset from the companion data-prep notebook:
# MAGIC
# MAGIC 1. **Decay Prediction** (Binary) — Will an object re-enter the atmosphere?
# MAGIC 2. **Orbit Class Prediction** (Multi-class) — LEO / MEO / GEO / HEO classification
# MAGIC 3. **Object Type Prediction** (Multi-class) — Payload / Debris / Rocket Body classification
# MAGIC
# MAGIC All models use sklearn Pipelines with ColumnTransformer, MLflow experiment tracking, and fixed hyperparameters for quick results.

# COMMAND ----------

# DBTITLE 1,Import Libraries (Notes)
# MAGIC %md
# MAGIC ### Import Libraries
# MAGIC
# MAGIC **What it does** — Imports all libraries needed for ML modeling:
# MAGIC * `pandas` / `numpy` — data manipulation
# MAGIC * `matplotlib` / `seaborn` — visualization (confusion matrices, ROC curves)
# MAGIC * `sklearn` — preprocessing, model training, evaluation
# MAGIC * `mlflow` — experiment tracking (logs models, metrics, parameters)

# COMMAND ----------

# DBTITLE 1,Import Libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import RobustScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, confusion_matrix, classification_report,
                             roc_auc_score, roc_curve)

import mlflow
import mlflow.sklearn
from mlflow.models import infer_signature

mlflow.set_experiment("/Users/your-username/space-debris-ml")
print("Libraries imported. MLflow experiment: space-debris-ml")

# COMMAND ----------

# DBTITLE 1,Load Data (Notes)
# MAGIC %md
# MAGIC ### Load Data
# MAGIC
# MAGIC **What it does** — Loads the cleaned dataset from the companion data-prep notebook.
# MAGIC * Replaces sentinel `-1` values with `NaN` (original data used -1 for missing numeric fields)
# MAGIC * Parses date columns to datetime format
# MAGIC * Displays shape and sample rows to verify the load

# COMMAND ----------

# DBTITLE 1,Load Data
data_path = "/Workspace/Users/guruvendra47@gmail.com/Space-Debris-Project/data/raw/space_debris_cleaned.csv"
df = pd.read_csv(data_path)

# Replace sentinel -1 with NaN for numeric columns
sentinel_cols = ['OrbitalPeriodMin', 'InclinationDegrees', 'MaxAltitudeKM', 'MinAltitudeKM', 'RadarSizeSQM']
df[sentinel_cols] = df[sentinel_cols].replace(-1, np.nan)

# Parse dates
df['LaunchDate'] = pd.to_datetime(df['LaunchDate'], errors='coerce')
df['DecayDate'] = pd.to_datetime(df['DecayDate'], errors='coerce')

print(f"Dataset shape: {df.shape}")
print(f"\nMissing values after sentinel replacement:")
print(df[sentinel_cols].isnull().sum())
display(df.head(5))

# COMMAND ----------

# DBTITLE 1,EDA & Leakage Check (Notes)
# MAGIC %md
# MAGIC ### EDA & Target Leakage Check
# MAGIC
# MAGIC **What it does** — Visualizes target distributions for all 3 models and checks for data leakage.
# MAGIC * Plots class frequencies for `IsDecayed`, `OrbitClass`, and `ObjectType`
# MAGIC * Prints exact percentage breakdowns to detect class imbalance
# MAGIC * Creates a feature type reference table
# MAGIC * Documents excluded columns that would leak each target

# COMMAND ----------

# DBTITLE 1,EDA & Leakage Check
# --- Target Distributions ---
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Model 1 target: IsDecayed
df['IsDecayed'].value_counts().plot(kind='bar', ax=axes[0], color=['steelblue', 'coral'])
axes[0].set_title('IsDecayed Distribution')
axes[0].set_xticklabels(['In Orbit (0)', 'Decayed (1)'], rotation=0)

# Model 2 target: OrbitClass
df['OrbitClass'].value_counts().plot(kind='bar', ax=axes[1], color='steelblue')
axes[1].set_title('OrbitClass Distribution')
axes[1].tick_params(axis='x', rotation=45)

# Model 3 target: ObjectType
df['ObjectType'].value_counts().plot(kind='bar', ax=axes[2], color='steelblue')
axes[2].set_title('ObjectType Distribution')
axes[2].tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.show()

# Print exact percentages
print("=== IsDecayed ===")
print(df['IsDecayed'].value_counts(normalize=True).round(4) * 100)
print("\n=== OrbitClass ===")
print(df['OrbitClass'].value_counts(normalize=True).round(4) * 100)
print("\n=== ObjectType ===")
print(df['ObjectType'].value_counts(normalize=True).round(4) * 100)

# Feature type reference
feature_types = pd.DataFrame({
    'Feature': ['OrbitalPeriodMin', 'InclinationDegrees', 'MaxAltitudeKM', 'MinAltitudeKM',
                'RadarSizeSQM', 'ObjectType', 'LaunchEra', 'OrbitClass', 'IsDecayed',
                'IsActive', 'IsDebris', 'IsRocketBody'],
    'Type': ['Numeric (float)', 'Numeric (float)', 'Numeric (float)', 'Numeric (float)',
             'Numeric (float)', 'Categorical (nominal)', 'Categorical (ordinal)',
             'Categorical (nominal)', 'Binary (target)', 'Binary', 'Binary', 'Binary']
})
display(feature_types)

# Leakage check
print("\n=== Target Leakage Check ===")
print("Model 1 (IsDecayed) — Excluded columns that directly indicate decay:")
print("  DecayDate — records the exact date an object re-entered")
print("  OrbitState — 'Impact (IMP)' means the object has already decayed")
print("  OperationalStatus — 'Decayed (D)' explicitly marks decayed objects")
print("\nModel 2 (OrbitClass) — Excluded columns that derive OrbitClass:")
print("  MaxAltitudeKM — OrbitClass was binned directly from this column")
print("  MinAltitudeKM — highly correlated with MaxAltitudeKM")

# COMMAND ----------

# DBTITLE 1,Model 1: Decay Prediction (Notes)
# MAGIC %md
# MAGIC ## Model 1: Decay Prediction (Binary Classification)
# MAGIC
# MAGIC **Goal** — Predict whether a space object has re-entered the atmosphere (`IsDecayed` = 1) or is still in orbit (`IsDecayed` = 0).
# MAGIC
# MAGIC **Features** — `OrbitalPeriodMin`, `InclinationDegrees`, `MaxAltitudeKM`, `MinAltitudeKM`, `RadarSizeSQM` (numeric) + `ObjectType`, `LaunchEra` (categorical)
# MAGIC
# MAGIC **Excluded (leakage)** — `DecayDate`, `OrbitState`, `OperationalStatus` all directly indicate decay status
# MAGIC
# MAGIC **Models** — Logistic Regression (interpretable baseline) + Random Forest (non-linear)
# MAGIC
# MAGIC **Preprocessing** — `SimpleImputer` (median for numeric, most_frequent for categorical) → `RobustScaler` (handles outliers) for numeric, `OneHotEncoder` for categorical
# MAGIC
# MAGIC **Handling imbalance** — `class_weight="balanced"` adjusts for class distribution

# COMMAND ----------

# DBTITLE 1,Model 1a: Logistic Regression (Notes)
# MAGIC %md
# MAGIC #### Model 1a: Logistic Regression
# MAGIC
# MAGIC Trains a logistic regression model with balanced class weights. Logs accuracy, precision, recall, F1, and ROC-AUC to MLflow. Plots confusion matrix and ROC curve.

# COMMAND ----------

# DBTITLE 1,Model 1a: Logistic Regression
# --- Model 1: Decay Prediction ---
features_1 = ['OrbitalPeriodMin', 'InclinationDegrees', 'MaxAltitudeKM', 'MinAltitudeKM',
              'RadarSizeSQM', 'ObjectType', 'LaunchEra']
X1 = df[features_1].copy()
y1 = df['IsDecayed'].copy()

X1_train, X1_test, y1_train, y1_test = train_test_split(
    X1, y1, test_size=0.2, random_state=42, stratify=y1
)

numeric_1 = ['OrbitalPeriodMin', 'InclinationDegrees', 'MaxAltitudeKM', 'MinAltitudeKM', 'RadarSizeSQM']
categorical_1 = ['ObjectType', 'LaunchEra']

preprocessor_1 = ColumnTransformer([
    ('num', Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', RobustScaler())
    ]), numeric_1),
    ('cat', Pipeline([
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('onehot', OneHotEncoder(handle_unknown='ignore'))
    ]), categorical_1)
])

# Model 1a: Logistic Regression
lr_pipeline = Pipeline([
    ('preprocessor', preprocessor_1),
    ('classifier', LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42))
])

with mlflow.start_run(run_name="decay_lr"):
    lr_pipeline.fit(X1_train, y1_train)
    y1_pred_lr = lr_pipeline.predict(X1_test)
    y1_prob_lr = lr_pipeline.predict_proba(X1_test)[:, 1]

    acc_lr = accuracy_score(y1_test, y1_pred_lr)
    prec_lr = precision_score(y1_test, y1_pred_lr)
    rec_lr = recall_score(y1_test, y1_pred_lr)
    f1_lr = f1_score(y1_test, y1_pred_lr)
    auc_lr = roc_auc_score(y1_test, y1_prob_lr)

    mlflow.log_param("model_type", "LogisticRegression")
    mlflow.log_param("class_weight", "balanced")
    mlflow.log_param("max_iter", 1000)
    mlflow.log_metric("accuracy", acc_lr)
    mlflow.log_metric("precision", prec_lr)
    mlflow.log_metric("recall", rec_lr)
    mlflow.log_metric("f1", f1_lr)
    mlflow.log_metric("roc_auc", auc_lr)

    signature = infer_signature(X1_train.head(100), lr_pipeline.predict(X1_train.head(100)))
    mlflow.sklearn.log_model(lr_pipeline, "model", signature=signature, input_example=X1_train.head(3))

# Confusion matrix + ROC curve
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
cm_lr = confusion_matrix(y1_test, y1_pred_lr)
sns.heatmap(cm_lr, annot=True, fmt='d', cmap='Blues', ax=axes[0],
            xticklabels=['In Orbit', 'Decayed'], yticklabels=['In Orbit', 'Decayed'])
axes[0].set_title('Logistic Regression — Confusion Matrix')
axes[0].set_ylabel('Actual')
axes[0].set_xlabel('Predicted')

fpr_lr, tpr_lr, _ = roc_curve(y1_test, y1_prob_lr)
axes[1].plot(fpr_lr, tpr_lr, label=f'LR (AUC = {auc_lr:.4f})', color='steelblue')
axes[1].plot([0, 1], [0, 1], '--', color='gray')
axes[1].set_title('ROC Curve')
axes[1].set_xlabel('False Positive Rate')
axes[1].set_ylabel('True Positive Rate')
axes[1].legend()

plt.tight_layout()
plt.show()

print(f"Accuracy:  {acc_lr:.4f}")
print(f"Precision: {prec_lr:.4f}")
print(f"Recall:    {rec_lr:.4f}")
print(f"F1 Score:  {f1_lr:.4f}")
print(f"ROC-AUC:   {auc_lr:.4f}")
print("\nClassification Report:")
print(classification_report(y1_test, y1_pred_lr, target_names=['In Orbit', 'Decayed']))

# COMMAND ----------

# DBTITLE 1,Model 1b: Random Forest (Notes)
# MAGIC %md
# MAGIC #### Model 1b: Random Forest
# MAGIC
# MAGIC Trains a Random Forest with 100 trees and balanced class weights. Plots confusion matrix, ROC curve (overlaid with Logistic Regression), and feature importance.

# COMMAND ----------

# DBTITLE 1,Model 1b: Random Forest
# Model 1b: Random Forest
rf_pipeline = Pipeline([
    ('preprocessor', preprocessor_1),
    ('classifier', RandomForestClassifier(n_estimators=100, class_weight='balanced',
                                          random_state=42, n_jobs=-1))
])

with mlflow.start_run(run_name="decay_rf"):
    rf_pipeline.fit(X1_train, y1_train)
    y1_pred_rf = rf_pipeline.predict(X1_test)
    y1_prob_rf = rf_pipeline.predict_proba(X1_test)[:, 1]

    acc_rf = accuracy_score(y1_test, y1_pred_rf)
    prec_rf = precision_score(y1_test, y1_pred_rf)
    rec_rf = recall_score(y1_test, y1_pred_rf)
    f1_rf = f1_score(y1_test, y1_pred_rf)
    auc_rf = roc_auc_score(y1_test, y1_prob_rf)

    mlflow.log_param("model_type", "RandomForest")
    mlflow.log_param("n_estimators", 100)
    mlflow.log_param("class_weight", "balanced")
    mlflow.log_metric("accuracy", acc_rf)
    mlflow.log_metric("precision", prec_rf)
    mlflow.log_metric("recall", rec_rf)
    mlflow.log_metric("f1", f1_rf)
    mlflow.log_metric("roc_auc", auc_rf)

    signature = infer_signature(X1_train.head(100), rf_pipeline.predict(X1_train.head(100)))
    mlflow.sklearn.log_model(rf_pipeline, "model", signature=signature, input_example=X1_train.head(3))

# Confusion matrix + ROC comparison
cm_rf = confusion_matrix(y1_test, y1_pred_rf)
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
sns.heatmap(cm_rf, annot=True, fmt='d', cmap='Greens', ax=axes[0],
            xticklabels=['In Orbit', 'Decayed'], yticklabels=['In Orbit', 'Decayed'])
axes[0].set_title('Random Forest — Confusion Matrix')
axes[0].set_ylabel('Actual')
axes[0].set_xlabel('Predicted')

fpr_rf, tpr_rf, _ = roc_curve(y1_test, y1_prob_rf)
axes[1].plot(fpr_rf, tpr_rf, label=f'RF (AUC = {auc_rf:.4f})', color='green')
axes[1].plot(fpr_lr, tpr_lr, label=f'LR (AUC = {auc_lr:.4f})', color='steelblue', linestyle='--')
axes[1].plot([0, 1], [0, 1], '--', color='gray')
axes[1].set_title('ROC Curves — Model 1 Comparison')
axes[1].set_xlabel('False Positive Rate')
axes[1].set_ylabel('True Positive Rate')
axes[1].legend()

plt.tight_layout()
plt.show()

print(f"Accuracy:  {acc_rf:.4f}")
print(f"Precision: {prec_rf:.4f}")
print(f"Recall:    {rec_rf:.4f}")
print(f"F1 Score:  {f1_rf:.4f}")
print(f"ROC-AUC:   {auc_rf:.4f}")
print("\nClassification Report:")
print(classification_report(y1_test, y1_pred_rf, target_names=['In Orbit', 'Decayed']))

# Feature importance
rf_model = rf_pipeline.named_steps['classifier']
feature_names = (numeric_1 +
                 list(rf_pipeline.named_steps['preprocessor']
                     .named_transformers_['cat']
                     .named_steps['onehot']
                     .get_feature_names_out(categorical_1)))
importances = pd.Series(rf_model.feature_importances_, index=feature_names).sort_values(ascending=True)

plt.figure(figsize=(10, 6))
importances.plot(kind='barh', color='steelblue')
plt.title('Random Forest — Feature Importance (Decay Prediction)')
plt.tight_layout()
plt.show()

# COMMAND ----------

# DBTITLE 1,Model 2: Orbit Class (Notes)
# MAGIC %md
# MAGIC ## Model 2: Orbit Class Prediction (Multi-class Classification)
# MAGIC
# MAGIC **Goal** — Predict an object's orbit class (LEO / MEO / GEO / HEO) from its physical characteristics.
# MAGIC
# MAGIC **Features** — `OrbitalPeriodMin`, `InclinationDegrees`, `RadarSizeSQM` (numeric) + `ObjectType` (categorical)
# MAGIC
# MAGIC **Excluded (leakage)** — `MaxAltitudeKM` and `MinAltitudeKM` are used to derive `OrbitClass` via binning, so including them would be target leakage. The model must predict orbit class from non-altitude features only.
# MAGIC
# MAGIC **Model** — Random Forest (100 trees, balanced class weights)
# MAGIC
# MAGIC **Evaluation** — Accuracy, macro/weighted F1, classification report, confusion matrix, feature importance

# COMMAND ----------

# DBTITLE 1,Model 2: Orbit Class Prediction
# --- Model 2: Orbit Class Prediction ---
features_2 = ['OrbitalPeriodMin', 'InclinationDegrees', 'RadarSizeSQM', 'ObjectType']
X2 = df[features_2].copy()
y2 = df['OrbitClass'].copy()

# Drop rows with missing target
mask = y2.notna()
X2, y2 = X2[mask], y2[mask]

X2_train, X2_test, y2_train, y2_test = train_test_split(
    X2, y2, test_size=0.2, random_state=42, stratify=y2
)

numeric_2 = ['OrbitalPeriodMin', 'InclinationDegrees', 'RadarSizeSQM']
categorical_2 = ['ObjectType']

preprocessor_2 = ColumnTransformer([
    ('num', Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', RobustScaler())
    ]), numeric_2),
    ('cat', Pipeline([
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('onehot', OneHotEncoder(handle_unknown='ignore'))
    ]), categorical_2)
])

rf2_pipeline = Pipeline([
    ('preprocessor', preprocessor_2),
    ('classifier', RandomForestClassifier(n_estimators=100, class_weight='balanced',
                                          random_state=42, n_jobs=-1))
])

with mlflow.start_run(run_name="orbitclass_rf"):
    rf2_pipeline.fit(X2_train, y2_train)
    y2_pred = rf2_pipeline.predict(X2_test)

    acc2 = accuracy_score(y2_test, y2_pred)
    f1_macro2 = f1_score(y2_test, y2_pred, average='macro')
    f1_weighted2 = f1_score(y2_test, y2_pred, average='weighted')

    mlflow.log_param("model_type", "RandomForest")
    mlflow.log_param("n_estimators", 100)
    mlflow.log_param("task", "multiclass_orbit")
    mlflow.log_metric("accuracy", acc2)
    mlflow.log_metric("f1_macro", f1_macro2)
    mlflow.log_metric("f1_weighted", f1_weighted2)

    signature = infer_signature(X2_train.head(100), rf2_pipeline.predict(X2_train.head(100)))
    mlflow.sklearn.log_model(rf2_pipeline, "model", signature=signature, input_example=X2_train.head(3))

# Confusion matrix
cm2 = confusion_matrix(y2_test, y2_pred, labels=rf2_pipeline.classes_)
plt.figure(figsize=(8, 6))
sns.heatmap(cm2, annot=True, fmt='d', cmap='Blues',
            xticklabels=rf2_pipeline.classes_, yticklabels=rf2_pipeline.classes_)
plt.title('Orbit Class Prediction — Confusion Matrix')
plt.ylabel('Actual')
plt.xlabel('Predicted')
plt.tight_layout()
plt.show()

print(f"Accuracy:      {acc2:.4f}")
print(f"F1 (macro):    {f1_macro2:.4f}")
print(f"F1 (weighted): {f1_weighted2:.4f}")
print("\nClassification Report:")
print(classification_report(y2_test, y2_pred))

# Feature importance
rf2_model = rf2_pipeline.named_steps['classifier']
feature_names_2 = (numeric_2 +
                   list(rf2_pipeline.named_steps['preprocessor']
                       .named_transformers_['cat']
                       .named_steps['onehot']
                       .get_feature_names_out(categorical_2)))
importances2 = pd.Series(rf2_model.feature_importances_, index=feature_names_2).sort_values(ascending=True)

plt.figure(figsize=(8, 5))
importances2.plot(kind='barh', color='steelblue')
plt.title('Feature Importance — Orbit Class Prediction')
plt.tight_layout()
plt.show()

# COMMAND ----------

# DBTITLE 1,Model 3: Object Type (Notes)
# MAGIC %md
# MAGIC ## Model 3: Object Type Classification (Multi-class)
# MAGIC
# MAGIC **Goal** — Predict the type of a space object (Payload, Debris, Rocket Body, etc.) from its orbital and physical characteristics.
# MAGIC
# MAGIC **Features** — `OrbitalPeriodMin`, `InclinationDegrees`, `MaxAltitudeKM`, `MinAltitudeKM`, `RadarSizeSQM` (numeric) + `OrbitClass`, `LaunchEra` (categorical)
# MAGIC
# MAGIC **Model** — Random Forest (100 trees, balanced class weights)
# MAGIC
# MAGIC **Evaluation** — Accuracy, macro/weighted F1, classification report, confusion matrix, feature importance

# COMMAND ----------

# DBTITLE 1,Model 3: Object Type Classification
# --- Model 3: Object Type Classification ---
features_3 = ['OrbitalPeriodMin', 'InclinationDegrees', 'MaxAltitudeKM', 'MinAltitudeKM',
              'RadarSizeSQM', 'OrbitClass', 'LaunchEra']
X3 = df[features_3].copy()
y3 = df['ObjectType'].copy()

# Drop rows with missing target or categorical features
mask3 = y3.notna() & X3['OrbitClass'].notna() & X3['LaunchEra'].notna()
X3, y3 = X3[mask3], y3[mask3]

X3_train, X3_test, y3_train, y3_test = train_test_split(
    X3, y3, test_size=0.2, random_state=42, stratify=y3
)

numeric_3 = ['OrbitalPeriodMin', 'InclinationDegrees', 'MaxAltitudeKM', 'MinAltitudeKM', 'RadarSizeSQM']
categorical_3 = ['OrbitClass', 'LaunchEra']

preprocessor_3 = ColumnTransformer([
    ('num', Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', RobustScaler())
    ]), numeric_3),
    ('cat', Pipeline([
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('onehot', OneHotEncoder(handle_unknown='ignore'))
    ]), categorical_3)
])

rf3_pipeline = Pipeline([
    ('preprocessor', preprocessor_3),
    ('classifier', RandomForestClassifier(n_estimators=100, class_weight='balanced',
                                          random_state=42, n_jobs=-1))
])

with mlflow.start_run(run_name="objecttype_rf"):
    rf3_pipeline.fit(X3_train, y3_train)
    y3_pred = rf3_pipeline.predict(X3_test)

    acc3 = accuracy_score(y3_test, y3_pred)
    f1_macro3 = f1_score(y3_test, y3_pred, average='macro')
    f1_weighted3 = f1_score(y3_test, y3_pred, average='weighted')

    mlflow.log_param("model_type", "RandomForest")
    mlflow.log_param("n_estimators", 100)
    mlflow.log_param("task", "multiclass_objecttype")
    mlflow.log_metric("accuracy", acc3)
    mlflow.log_metric("f1_macro", f1_macro3)
    mlflow.log_metric("f1_weighted", f1_weighted3)

    signature = infer_signature(X3_train.head(100), rf3_pipeline.predict(X3_train.head(100)))
    mlflow.sklearn.log_model(rf3_pipeline, "model", signature=signature, input_example=X3_train.head(3))

# Confusion matrix
cm3 = confusion_matrix(y3_test, y3_pred, labels=rf3_pipeline.classes_)
plt.figure(figsize=(10, 7))
sns.heatmap(cm3, annot=True, fmt='d', cmap='Blues',
            xticklabels=rf3_pipeline.classes_, yticklabels=rf3_pipeline.classes_)
plt.title('Object Type Prediction — Confusion Matrix')
plt.ylabel('Actual')
plt.xlabel('Predicted')
plt.tight_layout()
plt.show()

print(f"Accuracy:      {acc3:.4f}")
print(f"F1 (macro):    {f1_macro3:.4f}")
print(f"F1 (weighted): {f1_weighted3:.4f}")
print("\nClassification Report:")
print(classification_report(y3_test, y3_pred))

# Feature importance
rf3_model = rf3_pipeline.named_steps['classifier']
feature_names_3 = (numeric_3 +
                   list(rf3_pipeline.named_steps['preprocessor']
                       .named_transformers_['cat']
                       .named_steps['onehot']
                       .get_feature_names_out(categorical_3)))
importances3 = pd.Series(rf3_model.feature_importances_, index=feature_names_3).sort_values(ascending=True)

plt.figure(figsize=(10, 6))
importances3.plot(kind='barh', color='steelblue')
plt.title('Feature Importance — Object Type Prediction')
plt.tight_layout()
plt.show()

# COMMAND ----------

# DBTITLE 1,Model Comparison (Notes)
# MAGIC %md
# MAGIC ## Model Comparison Summary
# MAGIC
# MAGIC Consolidates metrics from all trained models for side-by-side comparison and highlights key takeaways.

# COMMAND ----------

# DBTITLE 1,Model Comparison Summary
comparison = pd.DataFrame({
    'Model': [
        '1a. Decay Prediction — Logistic Regression',
        '1b. Decay Prediction — Random Forest',
        '2. Orbit Class — Random Forest',
        '3. Object Type — Random Forest'
    ],
    'Task': ['Binary Classification', 'Binary Classification', 'Multi-class (4)', 'Multi-class (4+)'],
    'Accuracy': [acc_lr, acc_rf, acc2, acc3],
    'F1 (macro)': [f1_lr, f1_rf, f1_macro2, f1_macro3],
    'F1 (weighted)': [f1_lr, f1_rf, f1_weighted2, f1_weighted3],
    'ROC-AUC': [auc_lr, auc_rf, np.nan, np.nan]
})

display(comparison.round(4))

print("\n=== Key Takeaways ===")
best_decay = "Random Forest" if f1_rf > f1_lr else "Logistic Regression"
print(f"1. Decay Prediction: {best_decay} performs best (F1 = {max(f1_lr, f1_rf):.4f})")
print(f"2. Orbit Class: Random Forest accuracy = {acc2:.4f}")
print(f"3. Object Type: Random Forest accuracy = {acc3:.4f}")