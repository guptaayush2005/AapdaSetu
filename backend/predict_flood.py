"""
AapdaSetu - Multi-District Flood Prediction Test
Tests the trained XGBoost model on representative samples across states.
"""

import pandas as pd
from xgboost import XGBClassifier

df = pd.read_csv("training_data.csv")

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

model = XGBClassifier()
model.load_model("backend/xgboost_flood_model.json")

# Sample 10 diverse districts
sample_df = df.drop_duplicates(subset=["state", "district"]).head(12).copy()
X_sample = sample_df[features]

predictions = model.predict(X_sample)
probabilities = model.predict_proba(X_sample)

import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

risk_labels = {0: "[LOW RISK]", 1: "[MODERATE]", 2: "[HIGH RISK]"}

print("=" * 75)
print("AAPDASETU - AI FLOOD PREDICTION TEST RUN")
print("=" * 75)
print(f"{'State':<18} | {'District':<15} | {'Rain24h':<8} | {'River/Danger':<14} | {'Risk Prediction':<16}")
print("-" * 75)

for i in range(len(sample_df)):
    row = sample_df.iloc[i]
    pred = int(predictions[i])
    risk_text = risk_labels.get(pred, "UNKNOWN")
    prob = probabilities[i][pred] * 100
    river_str = f"{row['river_level']:.1f}m / {row['danger_level']:.1f}m"

    print(
        f"{row['state']:<18} | "
        f"{row['district']:<15} | "
        f"{row['rainfall_24h']:<7.1f}m | "
        f"{river_str:<14} | "
        f"{risk_text} ({prob:.1f}%)"
    )

print("=" * 75)
