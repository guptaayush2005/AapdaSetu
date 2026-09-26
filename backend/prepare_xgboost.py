import pandas as pd

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

X = df[features]
y = df["flood_risk"]

print("XGBOOST DATA READY")
print("Features:", X.columns.tolist())
print("X shape:", X.shape)
print("y shape:", y.shape)
print("\nTarget distribution:")
print(y.value_counts().sort_index())
