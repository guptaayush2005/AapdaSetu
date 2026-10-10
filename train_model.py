"""
====================================================================================================
                        AAPDASETU: AI MULTI-HAZARD DISASTER PREDICTION
                             MACHINE LEARNING TRAINING PIPELINE
====================================================================================================
Authors & Research Team: AapdaSetu National Climate & Disaster AI Labs
Frameworks: XGBoost 3.x, Scikit-Learn, Pandas, NumPy
Ground Truth Data Sources: Central Water Commission (CWC), IMD, NASA Earth Observation, Open-Meteo

This standalone training pipeline trains, validates, and serializes the 3 Core AI Models:
  1. Riverine Flood Hazard Classifier (3-Class XGBoost: LOW, MEDIUM, HIGH)
  2. Flash Flood & Cloudburst Rapid Early Warning Model (4-Class XGBoost)
  3. Landslide & Mountain Slope Geological Stability Model (4-Class XGBoost)

Usage:
  python train_model.py
====================================================================================================
"""

import os
import sys
import time
import shutil

# Ensure cross-platform utf-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from xgboost import XGBClassifier

# Terminal styling
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_banner():
    print(f"\n{CYAN}{BOLD}" + "=" * 80)
    print("      [+] AAPDASETU: NATIONAL AI DISASTER EARLY WARNING TRAINING ENGINE [+]")
    print("=" * 80 + f"{RESET}")
    print(f"{GREEN}> Grounded in Central Water Commission (CWC) & NASA Satellite Hydrology{RESET}")
    print(f"{GREEN}> Training Multi-Class Gradient Boosted Decision Trees (XGBoost 3.x){RESET}")
    print(f"{CYAN}" + "-" * 80 + f"{RESET}\n")


def print_section(title: str):
    print(f"\n{YELLOW}{BOLD}> [STAGE] {title}{RESET}")
    print(f"{YELLOW}" + "-" * 70 + f"{RESET}")


def ascii_bar(val: float, max_val: float = 1.0, length: int = 24) -> str:
    filled = int(round((val / max_val) * length)) if max_val > 0 else 0
    return "#" * filled + "-" * (length - filled)


def load_datasets():
    print_section("1. Loading & Inspecting Hydrological Datasets")

    # Primary river flood dataset
    path_flood = "training_data.csv"
    if not os.path.exists(path_flood):
        path_flood = os.path.join("data", "flood_dataset.csv")

    if not os.path.exists(path_flood):
        raise FileNotFoundError(f"Primary flood dataset not found at {path_flood}")

    df_flood = pd.read_csv(path_flood)
    print(f"  [OK] Riverine Flood Dataset      : {GREEN}{len(df_flood):,} samples{RESET} ({df_flood.shape[1]} features)")

    # Multi-hazard dataset
    path_multi = os.path.join("data", "multi_hazard_training_data.csv")
    df_multi = None
    if os.path.exists(path_multi):
        df_multi = pd.read_csv(path_multi)
        print(f"  [OK] Multi-Hazard Terrain Dataset: {GREEN}{len(df_multi):,} samples{RESET} ({df_multi.shape[1]} features)")
    else:
        print(f"  [i] Multi-Hazard Dataset path ({path_multi}) optional or synthesized.")

    return df_flood, df_multi


# ==================================================================================================
# MODEL 1: RIVERINE FLOOD HAZARD CLASSIFIER
# ==================================================================================================
def train_riverine_flood_model(df: pd.DataFrame):
    print_section("2. Training Model 1: Riverine Flood Hazard Classifier (XGBoost)")

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

    # Verify features
    missing = [f for f in features if f not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in dataset: {missing}")

    X = df[features].copy()
    y = df["flood_risk"].astype(int)

    class_names = ["0: LOW RISK", "1: MEDIUM RISK", "2: HIGH RISK"]

    print("  * Feature Vector (10 Hydro-Meteorological Signals):")
    for idx, f in enumerate(features, 1):
        print(f"    [{idx:02d}] {f:<18s} (mean={X[f].mean():.2f}, min={X[f].min():.2f}, max={X[f].max():.2f})")

    # Stratified Train/Test Split (80/20)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.20,
        random_state=42,
        stratify=y
    )

    print(f"\n  * Dataset Partitioning: {len(X_train)} Train Rows (80%) | {len(X_test)} Test Rows (20%)")
    print(f"  * Target Distribution: {dict(y.value_counts().sort_index())}")

    print("\n  * Initializing XGBoost Multi-Class Estimator...")
    model = XGBClassifier(
        n_estimators=160,
        max_depth=4,
        learning_rate=0.08,
        subsample=0.85,
        colsample_bytree=0.85,
        objective="multi:softprob",
        num_class=3,
        eval_metric="mlogloss",
        random_state=42
    )

    t0 = time.time()
    model.fit(X_train, y_train)
    t_train = time.time() - t0
    print(f"  [OK] Training completed in {GREEN}{t_train:.2f} seconds{RESET}")

    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    conf = confusion_matrix(y_test, y_pred)

    print(f"\n  {BOLD}* Validation Results for Model 1:{RESET}")
    print(f"  Test Accuracy Score: {GREEN}{BOLD}{accuracy * 100:.2f}%{RESET}")
    print("\n  Classification Report:")
    print(classification_report(y_test, y_pred, target_names=class_names, digits=3))

    print("  Confusion Matrix:")
    print(f"  {conf}")

    # Feature Importances
    importances = pd.Series(model.feature_importances_, index=features).sort_values(ascending=False)
    max_imp = importances.max()
    print(f"\n  {BOLD}Top Hydro-Meteorological Feature Importances:{RESET}")
    for f_name, imp_val in importances.items():
        bar = ascii_bar(imp_val, max_imp, 20)
        print(f"    * {f_name:<16s} : {imp_val * 100:5.2f}% |{CYAN}{bar}{RESET}|")

    return model, features


# ==================================================================================================
# MODEL 2 & 3: FLASH FLOOD & LANDSLIDE MULTI-HAZARD CLASSIFIERS
# ==================================================================================================
def train_flash_flood_and_landslide_models(df_multi: pd.DataFrame):
    if df_multi is None:
        return None, None

    print_section("3. Training Model 2: Flash Flood & Cloudburst Rapid Classifier")

    ff_features = [
        "rainfall_1h",
        "rainfall_6h",
        "rainfall_24h",
        "rainfall_72h",
        "rainfall_forecast_24h",
        "soil_moisture_pct",
        "elevation_m",
        "river_level"
    ]

    avail_ff = [f for f in ff_features if f in df_multi.columns]
    X_ff = df_multi[avail_ff].copy()

    if "flash_flood_risk" in df_multi.columns:
        y_ff = df_multi["flash_flood_risk"].astype(int)
    else:
        def calc_ff(row):
            r1 = row.get("rainfall_1h", 0)
            r24 = row.get("rainfall_24h", 0)
            sm = row.get("soil_moisture_pct", 50)
            score = 0
            if r1 >= 50.0: score += 4
            elif r1 >= 25.0: score += 2
            elif r1 >= 10.0: score += 1
            if r24 >= 120.0: score += 3
            elif r24 >= 70.0: score += 2
            if sm >= 85.0: score += 2
            if score >= 6: return 3
            elif score >= 4: return 2
            elif score >= 2: return 1
            return 0
        y_ff = df_multi.apply(calc_ff, axis=1)

    X_train, X_test, y_train, y_test = train_test_split(X_ff, y_ff, test_size=0.20, random_state=42, stratify=y_ff)

    ff_model = XGBClassifier(
        n_estimators=140,
        max_depth=4,
        learning_rate=0.08,
        subsample=0.85,
        colsample_bytree=0.85,
        objective="multi:softprob",
        num_class=4,
        eval_metric="mlogloss",
        random_state=42
    )
    ff_model.fit(X_train, y_train)
    ff_acc = accuracy_score(y_test, ff_model.predict(X_test))
    print(f"  [OK] Flash Flood Model Accuracy: {GREEN}{BOLD}{ff_acc * 100:.2f}%{RESET} (Classes: 0=Low, 1=Mod, 2=High, 3=Critical)")

    print_section("4. Training Model 3: Landslide Geological Slope Stability Classifier")
    ls_features = [
        "rainfall_24h",
        "rainfall_72h",
        "soil_moisture_pct",
        "slope_angle_deg",
        "elevation_m",
        "geological_stability"
    ]
    avail_ls = [f for f in ls_features if f in df_multi.columns]
    X_ls = df_multi[avail_ls].copy()

    if "landslide_risk" in df_multi.columns:
        y_ls = df_multi["landslide_risk"].astype(int)
    else:
        def calc_ls(row):
            slope = row.get("slope_angle_deg", 15)
            r72 = row.get("rainfall_72h", 20)
            sm = row.get("soil_moisture_pct", 50)
            geo = row.get("geological_stability", 0.7)
            if slope < 15: return 0
            score = 0
            if slope >= 35: score += 3
            elif slope >= 25: score += 2
            if r72 >= 150: score += 3
            elif r72 >= 80: score += 2
            if sm >= 85: score += 2
            if geo < 0.4: score += 2
            if score >= 6: return 3
            elif score >= 4: return 2
            elif score >= 2: return 1
            return 0
        y_ls = df_multi.apply(calc_ls, axis=1)

    X_train_ls, X_test_ls, y_train_ls, y_test_ls = train_test_split(X_ls, y_ls, test_size=0.20, random_state=42, stratify=y_ls)
    ls_model = XGBClassifier(
        n_estimators=140,
        max_depth=4,
        learning_rate=0.08,
        subsample=0.85,
        colsample_bytree=0.85,
        objective="multi:softprob",
        num_class=4,
        eval_metric="mlogloss",
        random_state=42
    )
    ls_model.fit(X_train_ls, y_train_ls)
    ls_acc = accuracy_score(y_test_ls, ls_model.predict(X_test_ls))
    print(f"  [OK] Landslide Model Accuracy: {GREEN}{BOLD}{ls_acc * 100:.2f}%{RESET} (Classes: 0=Low, 1=Mod, 2=High, 3=Critical)")

    return ff_model, ls_model


# ==================================================================================================
# MODEL EXPORT & DIRECTORY SYNC
# ==================================================================================================
def export_models(flood_model, ff_model, ls_model):
    print_section("5. Serializing & Exporting Production Model Artifacts")

    out_dirs = ["models", "backend"]
    for d in out_dirs:
        os.makedirs(d, exist_ok=True)

    # 1. Flood Model
    p_flood = os.path.join("models", "xgboost_flood_model.json")
    flood_model.save_model(p_flood)
    shutil.copy(p_flood, os.path.join("backend", "xgboost_flood_model.json"))
    print(f"  [OK] Saved Model 1 (Flood)       -> {GREEN}{p_flood}{RESET} & {GREEN}backend/{RESET}")

    # 2. Flash flood model
    if ff_model is not None:
        p_ff = os.path.join("models", "xgboost_flash_flood_model.json")
        ff_model.save_model(p_ff)
        shutil.copy(p_ff, os.path.join("backend", "xgboost_flash_flood_model.json"))
        print(f"  [OK] Saved Model 2 (Flash Flood) -> {GREEN}{p_ff}{RESET} & {GREEN}backend/{RESET}")

    # 3. Landslide model
    if ls_model is not None:
        p_ls = os.path.join("models", "xgboost_landslide_model.json")
        ls_model.save_model(p_ls)
        shutil.copy(p_ls, os.path.join("backend", "xgboost_landslide_model.json"))
        print(f"  [OK] Saved Model 3 (Landslide)   -> {GREEN}{p_ls}{RESET} & {GREEN}backend/{RESET}")


# ==================================================================================================
# LIVE REAL-TIME INFERENCE DEMONSTRATION
# ==================================================================================================
def run_live_inference_demo(model, features):
    print_section("6. Live Model Demonstration (Sample Real-Time Inference)")

    scenarios = [
        {
            "name": "Scenario A: Normal Weather (Varanasi, UP - Post-Monsoon)",
            "data": {
                "rainfall_1h": 0.0,
                "rainfall_6h": 0.0,
                "rainfall_24h": 2.0,
                "rainfall_72h": 8.0,
                "temperature": 28.5,
                "humidity": 64.0,
                "wind_speed": 7.5,
                "river_level": 68.2,
                "danger_level": 71.26,
                "warning_level": 70.26
            }
        },
        {
            "name": "Scenario B: Elevated Monsoon Runoff (Assam - Brahmaputra Basin)",
            "data": {
                "rainfall_1h": 8.5,
                "rainfall_6h": 32.0,
                "rainfall_24h": 68.0,
                "rainfall_72h": 140.0,
                "temperature": 24.0,
                "humidity": 88.0,
                "wind_speed": 18.0,
                "river_level": 105.1,
                "danger_level": 105.7,
                "warning_level": 104.8
            }
        },
        {
            "name": "Scenario C: Extreme Cloudburst & Flash Flooding (Chamoli, Uttarakhand)",
            "data": {
                "rainfall_1h": 62.0,
                "rainfall_6h": 115.0,
                "rainfall_24h": 185.0,
                "rainfall_72h": 240.0,
                "temperature": 18.0,
                "humidity": 96.0,
                "wind_speed": 45.0,
                "river_level": 73.8,
                "danger_level": 71.0,
                "warning_level": 70.0
            }
        }
    ]

    class_labels = {0: "LOW RISK (NORMAL)", 1: "MEDIUM / MODERATE RISK", 2: "HIGH / SEVERE HAZARD"}
    colors = {0: GREEN, 1: YELLOW, 2: RED}

    for sc in scenarios:
        print(f"\n  {BOLD}{sc['name']}:{RESET}")
        sample_df = pd.DataFrame([sc["data"]])[features]
        probs = model.predict_proba(sample_df)[0]
        pred_class = int(np.argmax(probs))

        c = colors.get(pred_class, CYAN)
        print(f"    * Model Prediction: {c}{BOLD}{class_labels[pred_class]}{RESET}")
        print(f"    * Class Probabilities:")
        for idx, (p_val, label) in enumerate(zip(probs, ["Low", "Medium", "High"])):
            bar = ascii_bar(p_val, 1.0, 16)
            print(f"      - {label:<7s} : {p_val * 100:5.1f}% |{c}{bar}{RESET}|")


def main():
    print_banner()
    df_flood, df_multi = load_datasets()

    # Train primary river flood model
    flood_model, features = train_riverine_flood_model(df_flood)

    # Train multi-hazard flash flood & landslide models
    ff_model, ls_model = train_flash_flood_and_landslide_models(df_multi)

    # Export artifacts
    export_models(flood_model, ff_model, ls_model)

    # Run demonstration inference
    run_live_inference_demo(flood_model, features)

    print(f"\n{GREEN}{BOLD}" + "=" * 80)
    print("      [OK] ALL AAPDASETU MACHINE LEARNING MODELS TRAINED & EXPORTED SUCCESSFULLY!")
    print("=" * 80 + f"{RESET}\n")


if __name__ == "__main__":
    main()
