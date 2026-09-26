"""
AapdaSetu - XGBoost Flood Prediction Model Trainer
Trains a robust multi-class XGBoost classifier on comprehensive hydrological data.
Target classes: 0 (LOW), 1 (MEDIUM), 2 (HIGH)
"""

import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from xgboost import XGBClassifier

# 1. Load dataset
DATA_PATH = "training_data.csv"
if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(f"Dataset not found at {DATA_PATH}. Run dataset_generator.py first.")

df = pd.read_csv(DATA_PATH)
print(f"Loaded {len(df)} records from {DATA_PATH}")

# 2. Define features & target
features = [
    "rainfall_1h",
    "rainfall_6h",
    "rainfall_24h",
    "rainfall_72h",
    "temperature",
    "humidity",
    "wind_speed",
    "river_level",
    "danger_level",
    "warning_level"
]

X = df[features].copy()
y = df["flood_risk"].astype(int)

# 3. Stratified Train/Test Split (80/20)
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print(f"Training set: {len(X_train)} rows | Testing set: {len(X_test)} rows")
print("Target distribution in train:")
print(y_train.value_counts().sort_index())

# 4. Initialize & Train XGBoost Classifier
model = XGBClassifier(
    n_estimators=150,
    max_depth=4,
    learning_rate=0.08,
    subsample=0.85,
    colsample_bytree=0.85,
    objective="multi:softprob",
    num_class=3,
    eval_metric="mlogloss",
    random_state=42
)

model.fit(X_train, y_train)

# 5. Evaluate Model
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
conf_matrix = confusion_matrix(y_test, y_pred)

print("\n" + "=" * 60)
print("XGBOOST MODEL TRAINING COMPLETE")
print("=" * 60)
print(f"Test Accuracy: {accuracy * 100:.2f}%\n")
print("Classification Report:")
print(classification_report(y_test, y_pred, target_names=["0: LOW", "1: MEDIUM", "2: HIGH"]))

print("Confusion Matrix:")
print(conf_matrix)

# 6. Feature Importances
importance = pd.Series(model.feature_importances_, index=features).sort_values(ascending=False)
print("\nTop Feature Importances:")
for f, imp in importance.items():
    print(f"  - {f:15s}: {imp * 100:.2f}%")

# 7. Save Model
MODEL_OUTPUT = "backend/xgboost_flood_model.json"
os.makedirs(os.path.dirname(MODEL_OUTPUT), exist_ok=True)
model.save_model(MODEL_OUTPUT)
print(f"\nModel successfully saved to: {MODEL_OUTPUT}")
print("=" * 60)
