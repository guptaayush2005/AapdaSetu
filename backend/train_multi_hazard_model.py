"""
AapdaSetu - Multi-Hazard XGBoost Model Trainer
Generates comprehensive multi-source training data and trains XGBoost classifiers for:
1. Flash Flood Risk (4 classes: 0=LOW, 1=MODERATE, 2=HIGH, 3=CRITICAL)
2. Landslide Risk (4 classes: 0=LOW, 1=MODERATE, 2=HIGH, 3=CRITICAL)
3. Backward-compatible Flood Model (3 classes: 0=LOW, 1=MEDIUM, 2=HIGH)
"""

import os
import random
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from xgboost import XGBClassifier

from hyperlocal_data import HYPERLOCAL_DATABASE

np.random.seed(42)
random.seed(42)


def generate_multi_hazard_dataset():
    records = []
    
    # Iterate through each state and district in the hyper-local database
    for state, districts in HYPERLOCAL_DATABASE.items():
        for district, wards in districts.items():
            for ward in wards:
                slope = ward["slope_angle_deg"]
                elevation = ward["elevation_m"]
                stability = ward["geological_stability"]
                hist_floods = ward["historical_floods"]
                hist_landslides = ward["historical_landslides"]
                
                danger_level = round(random.uniform(2.5, 4.2), 2) if slope < 25 else round(random.uniform(1.8, 3.2), 2)
                warning_level = round(danger_level - random.uniform(0.4, 0.7), 2)
                
                # Generate 25 scenario samples per hyper-local settlement
                for _ in range(25):
                    scenario = random.choices(["NORMAL", "MODERATE_MONSOON", "HEAVY_STORM", "EXTREME_CLOUDBURST"], weights=[0.40, 0.30, 0.20, 0.10])[0]
                    
                    if scenario == "NORMAL":
                        r1 = round(np.random.gamma(1.5, 1.2), 1)
                        r6 = round(r1 * random.uniform(1.8, 3.0) + random.uniform(0, 3), 1)
                        r24 = round(r6 * random.uniform(1.8, 2.8) + random.uniform(0, 8), 1)
                        r72 = round(r24 * random.uniform(1.3, 1.8) + random.uniform(0, 10), 1)
                        rfc = round(r24 * random.uniform(0.3, 0.7), 1)
                        soil_moisture = round(random.uniform(25.0, 58.0), 1)
                        river_lvl = round(random.uniform(0.5, warning_level * 0.75), 2)
                        temp = round(random.uniform(22.0, 32.0), 1)
                        humidity = round(random.uniform(45.0, 75.0), 1)
                        wind = round(random.uniform(5.0, 16.0), 1)
                        
                    elif scenario == "MODERATE_MONSOON":
                        r1 = round(np.random.gamma(3.0, 2.5), 1)
                        r6 = round(r1 * random.uniform(2.5, 4.0) + random.uniform(8, 18), 1)
                        r24 = round(r6 * random.uniform(2.0, 3.2) + random.uniform(15, 35), 1)
                        r72 = round(r24 * random.uniform(1.4, 2.0) + random.uniform(25, 50), 1)
                        rfc = round(r24 * random.uniform(0.5, 1.1), 1)
                        soil_moisture = round(random.uniform(62.0, 78.0), 1)
                        river_lvl = round(random.uniform(warning_level * 0.85, danger_level * 0.95), 2)
                        temp = round(random.uniform(20.0, 28.0), 1)
                        humidity = round(random.uniform(75.0, 88.0), 1)
                        wind = round(random.uniform(12.0, 28.0), 1)
                        
                    elif scenario == "HEAVY_STORM":
                        r1 = round(random.uniform(15.0, 40.0), 1)
                        r6 = round(r1 * random.uniform(2.8, 4.5) + random.uniform(25, 50), 1)
                        r24 = round(r6 * random.uniform(1.8, 2.8) + random.uniform(45, 90), 1)
                        r72 = round(r24 * random.uniform(1.3, 1.8) + random.uniform(60, 120), 1)
                        rfc = round(r24 * random.uniform(0.8, 1.4), 1)
                        soil_moisture = round(random.uniform(78.0, 92.0), 1)
                        river_lvl = round(random.uniform(danger_level * 0.95, danger_level * 1.25), 2)
                        temp = round(random.uniform(18.0, 26.0), 1)
                        humidity = round(random.uniform(85.0, 96.0), 1)
                        wind = round(random.uniform(25.0, 50.0), 1)
                        
                    else: # EXTREME_CLOUDBURST
                        r1 = round(random.uniform(42.0, 95.0), 1)  # Cloudburst definition >50mm/h
                        r6 = round(r1 * random.uniform(2.5, 4.0) + random.uniform(60, 110), 1)
                        r24 = round(r6 * random.uniform(1.6, 2.5) + random.uniform(90, 160), 1)
                        r72 = round(r24 * random.uniform(1.2, 1.6) + random.uniform(100, 180), 1)
                        rfc = round(r24 * random.uniform(1.0, 1.8), 1)
                        soil_moisture = round(random.uniform(90.0, 99.5), 1)
                        river_lvl = round(danger_level * random.uniform(1.20, 1.65), 2)
                        temp = round(random.uniform(16.0, 24.0), 1)
                        humidity = round(random.uniform(92.0, 99.0), 1)
                        wind = round(random.uniform(35.0, 75.0), 1)
                    
                    r1 = max(0.0, r1)
                    r6 = max(r1, r6)
                    r24 = max(r6, r24)
                    r72 = max(r24, r72)
                    
                    # Compute Ground Truth Flood Risk (0: Low, 1: Moderate, 2: High, 3: Critical)
                    f_score = 0
                    if r1 >= 40.0: f_score += 4
                    elif r1 >= 20.0: f_score += 2
                    
                    if r24 >= 140.0: f_score += 3
                    elif r24 >= 80.0: f_score += 2
                    elif r24 >= 40.0: f_score += 1
                    
                    if soil_moisture >= 88.0: f_score += 3
                    elif soil_moisture >= 75.0: f_score += 2
                    
                    if river_lvl >= (danger_level * 1.15): f_score += 4
                    elif river_lvl >= danger_level: f_score += 3
                    elif river_lvl >= warning_level: f_score += 2
                    
                    if hist_floods >= 18: f_score += 2
                    elif hist_floods >= 10: f_score += 1
                    
                    if f_score >= 9: flood_risk = 3       # CRITICAL
                    elif f_score >= 6: flood_risk = 2     # HIGH
                    elif f_score >= 3: flood_risk = 1     # MODERATE
                    else: flood_risk = 0                 # LOW
                    
                    # Compute Ground Truth Landslide Risk (0: Low, 1: Moderate, 2: High, 3: Critical)
                    ls_score = 0
                    if slope >= 34.0: ls_score += 4
                    elif slope >= 26.0: ls_score += 3
                    elif slope >= 18.0: ls_score += 2
                    elif slope < 8.0: ls_score = 0       # Plains don't slide
                    
                    if ls_score > 0:
                        if soil_moisture >= 85.0: ls_score += 4
                        elif soil_moisture >= 72.0: ls_score += 2
                        
                        if r72 >= 200.0: ls_score += 3
                        elif r72 >= 120.0: ls_score += 2
                        
                        if r1 >= 25.0: ls_score += 2
                        if hist_landslides >= 16: ls_score += 3
                        elif hist_landslides >= 8: ls_score += 1
                        if stability >= 0.85: ls_score += 2
                    
                    if slope < 8.0 or ls_score < 3:
                        landslide_risk = 0  # LOW
                    elif ls_score >= 11:
                        landslide_risk = 3  # CRITICAL
                    elif ls_score >= 7:
                        landslide_risk = 2  # HIGH
                    else:
                        landslide_risk = 1  # MODERATE
                        
                    records.append({
                        "state": state,
                        "district": district,
                        "ward_village": ward["name"],
                        "rainfall_1h": r1,
                        "rainfall_6h": r6,
                        "rainfall_24h": r24,
                        "rainfall_72h": r72,
                        "rainfall_forecast_24h": rfc,
                        "soil_moisture_pct": soil_moisture,
                        "slope_angle_deg": slope,
                        "elevation_m": elevation,
                        "geological_stability": stability,
                        "historical_floods": hist_floods,
                        "historical_landslides": hist_landslides,
                        "river_level": river_lvl,
                        "danger_level": danger_level,
                        "warning_level": warning_level,
                        "temperature": temp,
                        "humidity": humidity,
                        "wind_speed": wind,
                        "flood_risk": flood_risk,
                        "landslide_risk": landslide_risk
                    })

    df = pd.DataFrame(records)
    os.makedirs("data", exist_ok=True)
    df.to_csv("data/multi_hazard_training_data.csv", index=False)
    print(f"Generated {len(df)} multi-hazard hyper-local records across {df['district'].nunique()} districts.")
    return df


def train_models():
    df = generate_multi_hazard_dataset()
    
    # 1. Train Flash Flood Model
    flood_features = [
        "rainfall_1h", "rainfall_6h", "rainfall_24h", "rainfall_72h", "rainfall_forecast_24h",
        "soil_moisture_pct", "river_level", "danger_level", "warning_level",
        "historical_floods", "elevation_m", "slope_angle_deg", "humidity"
    ]
    
    X_f = df[flood_features]
    y_f = df["flood_risk"]
    
    X_train_f, X_test_f, y_train_f, y_test_f = train_test_split(X_f, y_f, test_size=0.2, random_state=42, stratify=y_f)
    
    flood_clf = XGBClassifier(
        n_estimators=160,
        max_depth=4,
        learning_rate=0.07,
        subsample=0.85,
        colsample_bytree=0.85,
        objective="multi:softprob",
        num_class=4,
        eval_metric="mlogloss",
        random_state=42
    )
    flood_clf.fit(X_train_f, y_train_f)
    acc_f = accuracy_score(y_test_f, flood_clf.predict(X_test_f))
    print(f"\n[FLASH FLOOD MODEL] Test Accuracy: {acc_f * 100:.2f}%")
    print(classification_report(y_test_f, flood_clf.predict(X_test_f), target_names=["0: LOW", "1: MOD", "2: HIGH", "3: CRIT"]))
    
    flood_clf.save_model("backend/xgboost_flash_flood_model.json")
    print("Saved backend/xgboost_flash_flood_model.json")
    
    # 2. Train Landslide Model
    ls_features = [
        "slope_angle_deg", "elevation_m", "geological_stability",
        "soil_moisture_pct", "rainfall_1h", "rainfall_24h", "rainfall_72h",
        "historical_landslides", "humidity"
    ]
    
    X_ls = df[ls_features]
    y_ls = df["landslide_risk"]
    
    X_train_ls, X_test_ls, y_train_ls, y_test_ls = train_test_split(X_ls, y_ls, test_size=0.2, random_state=42, stratify=y_ls)
    
    ls_clf = XGBClassifier(
        n_estimators=160,
        max_depth=4,
        learning_rate=0.07,
        subsample=0.85,
        colsample_bytree=0.85,
        objective="multi:softprob",
        num_class=4,
        eval_metric="mlogloss",
        random_state=42
    )
    ls_clf.fit(X_train_ls, y_train_ls)
    acc_ls = accuracy_score(y_test_ls, ls_clf.predict(X_test_ls))
    print(f"\n[LANDSLIDE MODEL] Test Accuracy: {acc_ls * 100:.2f}%")
    print(classification_report(y_test_ls, ls_clf.predict(X_test_ls), target_names=["0: LOW", "1: MOD", "2: HIGH", "3: CRIT"]))
    
    ls_clf.save_model("backend/xgboost_landslide_model.json")
    print("Saved backend/xgboost_landslide_model.json")
    
    # 3. Maintain 100% backward compatibility for legacy 10-feature model
    legacy_features = [
        "rainfall_1h", "rainfall_6h", "rainfall_24h", "rainfall_72h",
        "temperature", "humidity", "wind_speed",
        "river_level", "danger_level", "warning_level"
    ]
    # Map 4-class flood to 3-class legacy (0->0, 1->1, 2,3->2)
    y_legacy = df["flood_risk"].map({0: 0, 1: 1, 2: 2, 3: 2})
    X_legacy = df[legacy_features]
    
    legacy_clf = XGBClassifier(
        n_estimators=120,
        max_depth=4,
        learning_rate=0.08,
        objective="multi:softprob",
        num_class=3,
        eval_metric="mlogloss",
        random_state=42
    )
    legacy_clf.fit(X_legacy, y_legacy)
    legacy_clf.save_model("backend/xgboost_flood_model.json")
    print("Updated backend/xgboost_flood_model.json (backward compatible 10-feature model).")


if __name__ == "__main__":
    train_models()
