"""
AapdaSetu - Multi-Source AI Flash Flood & Landslide Risk Prediction Engine
Fuses rainfall, soil moisture, terrain/slope stability, historical disaster records,
and river gauge telemetry to predict hyper-local dual risks with lead time & explainability.
"""

import os
import math
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd
from xgboost import XGBClassifier

# Model artifact paths
FLASH_FLOOD_MODEL_PATH = "backend/xgboost_flash_flood_model.json"
LANDSLIDE_MODEL_PATH = "backend/xgboost_landslide_model.json"
LEGACY_FLOOD_MODEL_PATH = "backend/xgboost_flood_model.json"

_flood_model: Any = None
_landslide_model: Any = None


def load_prediction_models():
    """Load or lazily initialize the multi-source XGBoost models."""
    global _flood_model, _landslide_model
    
    # 1. Load or initialize Flash Flood Model
    if _flood_model is None:
        model = XGBClassifier()
        if os.path.exists(FLASH_FLOOD_MODEL_PATH):
            try:
                model.load_model(FLASH_FLOOD_MODEL_PATH)
                _flood_model = model
            except Exception as e:
                print(f"[Multi-Risk Engine] Could not load flash flood model from {FLASH_FLOOD_MODEL_PATH}: {e}")
        elif os.path.exists(LEGACY_FLOOD_MODEL_PATH):
            try:
                model.load_model(LEGACY_FLOOD_MODEL_PATH)
                _flood_model = model
            except Exception as e:
                print(f"[Multi-Risk Engine] Fallback to legacy flood model failed: {e}")
    
    # 2. Load or initialize Landslide Model
    if _landslide_model is None:
        model_ls = XGBClassifier()
        if os.path.exists(LANDSLIDE_MODEL_PATH):
            try:
                model_ls.load_model(LANDSLIDE_MODEL_PATH)
                _landslide_model = model_ls
            except Exception as e:
                print(f"[Multi-Risk Engine] Could not load landslide model from {LANDSLIDE_MODEL_PATH}: {e}")

    return _flood_model, _landslide_model


def assess_multi_source_risk(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main prediction pipeline:
    Location -> Data Collection -> Validation -> Feature Engineering ->
    Multi-source Fusion -> ML Inference -> Dual Risk Scoring -> Lead Time -> Factors Attribution
    """
    # 1. Extract and sanitize features
    rain_1h = max(0.0, float(features.get("rainfall_1h", 0.0)))
    rain_6h = max(rain_1h, float(features.get("rainfall_6h", 0.0)))
    rain_24h = max(rain_6h, float(features.get("rainfall_24h", 0.0)))
    rain_72h = max(rain_24h, float(features.get("rainfall_72h", 0.0)))
    rain_fc_24h = max(0.0, float(features.get("rainfall_forecast_24h", rain_24h * 0.45)))
    
    # Soil Moisture (Saturation percentage 0-100%)
    soil_moisture_pct = min(100.0, max(0.0, float(features.get("soil_moisture_pct", 65.0))))
    
    # Terrain, Slope & Elevation (SRTM 30m DEM + GSI)
    slope_angle_deg = min(60.0, max(0.0, float(features.get("slope_angle_deg", 15.0))))
    elevation_m = max(0.0, float(features.get("elevation_m", 450.0)))
    terrain_type = features.get("terrain_type", "River Valley Basin")
    geological_stability = min(1.0, max(0.05, float(features.get("geological_stability", 0.50))))
    
    # Historical Disasters
    hist_floods = max(0, int(features.get("historical_floods", 10)))
    hist_landslides = max(0, int(features.get("historical_landslides", 5)))
    
    # River & Weather Telemetry
    river_level = max(0.0, float(features.get("river_level", 0.0)))
    danger_level = max(0.1, float(features.get("danger_level", 3.5)))
    warning_level = max(0.1, float(features.get("warning_level", 2.8)))
    
    temperature = float(features.get("temperature", 24.0))
    humidity = min(100.0, max(10.0, float(features.get("humidity", 80.0))))
    wind_speed = max(0.0, float(features.get("wind_speed", 15.0)))
    
    # IoT Sensor Telemetry Integration (When available)
    iot_sensor_data = features.get("iot_sensor_data")
    iot_active = False
    if isinstance(iot_sensor_data, dict) and iot_sensor_data:
        iot_active = True
        if "water_level_m" in iot_sensor_data and float(iot_sensor_data["water_level_m"]) > 0:
            river_level = float(iot_sensor_data["water_level_m"])
        if "soil_moisture_pct" in iot_sensor_data and float(iot_sensor_data["soil_moisture_pct"]) > 0:
            soil_moisture_pct = min(100.0, max(0.0, float(iot_sensor_data["soil_moisture_pct"])))
        if "rainfall_rate_mmh" in iot_sensor_data and float(iot_sensor_data["rainfall_rate_mmh"]) > 0:
            rain_1h = max(rain_1h, float(iot_sensor_data["rainfall_rate_mmh"]))
            
    river_crest_ratio = round(river_level / danger_level, 2) if danger_level > 0 else 0.0
    soil_saturation_index = round(soil_moisture_pct / 100.0, 3)
    avg_hourly = max(0.5, rain_24h / 24.0)
    intensity_ratio = round(rain_1h / avg_hourly, 2)
    
    # 2. Physics-Informed Multi-Source Dual Risk Evaluation (incorporating elevation and weather)
    phys_flood_risk, phys_flood_prob = _compute_flash_flood_risk(
        rain_1h, rain_6h, rain_24h, rain_72h, rain_fc_24h,
        soil_moisture_pct, river_level, danger_level, warning_level,
        hist_floods, elevation_m, slope_angle_deg, humidity, wind_speed
    )
    
    phys_ls_risk, phys_ls_prob = _compute_landslide_risk(
        slope_angle_deg, elevation_m, geological_stability,
        rain_1h, rain_24h, rain_72h, soil_moisture_pct,
        hist_landslides, humidity
    )

    # 3. XGBoost Machine Learning Inference
    fm, lm = load_prediction_models()
    risk_classes = ["LOW", "MODERATE", "HIGH", "CRITICAL"]
    
    ml_f_risk = None
    ml_f_prob = None
    if fm is not None:
        try:
            f_df = pd.DataFrame([{
                "rainfall_1h": rain_1h,
                "rainfall_6h": rain_6h,
                "rainfall_24h": rain_24h,
                "rainfall_72h": rain_72h,
                "rainfall_forecast_24h": rain_fc_24h,
                "soil_moisture_pct": soil_moisture_pct,
                "river_level": river_level,
                "danger_level": danger_level,
                "warning_level": warning_level,
                "historical_floods": hist_floods,
                "elevation_m": elevation_m,
                "slope_angle_deg": slope_angle_deg,
                "humidity": humidity
            }])
            f_probs = fm.predict_proba(f_df)[0]
            ml_f_idx = int(np.argmax(f_probs))
            ml_f_risk = risk_classes[ml_f_idx]
            # Convert multi-class probability into high-risk confidence percentage
            if ml_f_idx >= 2: # HIGH or CRITICAL
                ml_f_prob = round(float(np.sum(f_probs[2:])) * 100.0, 1)
            elif ml_f_idx == 1:
                ml_f_prob = round(float(f_probs[1] + f_probs[2]) * 100.0, 1)
            else:
                ml_f_prob = round(max(50.0, float(f_probs[0]) * 70.0), 1)
        except Exception as e:
            print(f"[XGBoost Flash Flood Inference Notice]: {e}")

    ml_ls_risk = None
    ml_ls_prob = None
    if lm is not None:
        try:
            ls_df = pd.DataFrame([{
                "slope_angle_deg": slope_angle_deg,
                "elevation_m": elevation_m,
                "geological_stability": geological_stability,
                "soil_moisture_pct": soil_moisture_pct,
                "rainfall_1h": rain_1h,
                "rainfall_24h": rain_24h,
                "rainfall_72h": rain_72h,
                "historical_landslides": hist_landslides,
                "humidity": humidity
            }])
            ls_probs = lm.predict_proba(ls_df)[0]
            ml_ls_idx = int(np.argmax(ls_probs))
            ml_ls_risk = risk_classes[ml_ls_idx]
            if ml_ls_idx >= 2:
                ml_ls_prob = round(float(np.sum(ls_probs[2:])) * 100.0, 1)
            elif ml_ls_idx == 1:
                ml_ls_prob = round(float(ls_probs[1] + ls_probs[2]) * 100.0, 1)
            else:
                ml_ls_prob = round(max(50.0, float(ls_probs[0]) * 70.0), 1)
        except Exception as e:
            print(f"[XGBoost Landslide Inference Notice]: {e}")

    # 4. Fusion of ML Predictions and Physical Domain Boundaries
    # Map risk tiers to ordinal severity
    severity = {"LOW": 0, "MODERATE": 1, "HIGH": 2, "CRITICAL": 3}
    rev_severity = {0: "LOW", 1: "MODERATE", 2: "HIGH", 3: "CRITICAL"}

    # Flood Risk Consensus
    if ml_f_risk:
        final_f_sev = max(severity[phys_flood_risk], severity[ml_f_risk])
        flood_risk = rev_severity[final_f_sev]
        flood_prob = round((phys_flood_prob * 0.45 + (ml_f_prob or phys_flood_prob) * 0.55), 1)
    else:
        flood_risk = phys_flood_risk
        flood_prob = phys_flood_prob

    # Landslide Risk Consensus
    if ml_ls_risk:
        final_ls_sev = max(severity[phys_ls_risk], severity[ml_ls_risk])
        landslide_risk = rev_severity[final_ls_sev]
        landslide_prob = round((phys_ls_prob * 0.45 + (ml_ls_prob or phys_ls_prob) * 0.55), 1)
    else:
        landslide_risk = phys_ls_risk
        landslide_prob = phys_ls_prob

    # Enforce boundary guarantees
    if slope_angle_deg < 8.0:
        landslide_risk = "LOW"
        landslide_prob = min(40.0, landslide_prob)

    flood_prob = round(min(99.9, max(45.0, flood_prob)), 1)
    landslide_prob = round(min(99.9, max(35.0, landslide_prob)), 1)

    # Combined peak risk probability
    combined_prob = round(max(flood_prob, landslide_prob), 1)
    
    # Determine Primary Predicted Hazard Type
    hazard_type = _determine_hazard_type(flood_risk, landslide_risk, slope_angle_deg, river_crest_ratio)
    
    # 5. Lead Time & Time Window Estimation
    lead_time_hours, time_window_str = _estimate_lead_time(
        flood_risk, landslide_risk, rain_1h, rain_24h,
        soil_moisture_pct, river_level, danger_level, slope_angle_deg
    )
    
    # 6. Feature Attribution: "Prediction Factors" Breakdown (including Elevation & Topography)
    prediction_factors = _calculate_prediction_factors(
        rain_24h, rain_1h, soil_moisture_pct, slope_angle_deg,
        hist_floods, hist_landslides, river_crest_ratio, flood_risk, landslide_risk,
        elevation_m, iot_active
    )
    
    # 7. Evacuation & Action Recommendations
    recommended_action, evacuation_tier = _generate_action_protocol(
        flood_risk, landslide_risk, hazard_type, lead_time_hours
    )
    
    return {
        "flood_risk": flood_risk,
        "flood_probability": flood_prob,
        "landslide_risk": landslide_risk,
        "landslide_probability": landslide_prob,
        "risk_probability": combined_prob,
        "predicted_hazard_type": hazard_type,
        "lead_time_hours": lead_time_hours,
        "expected_time_window": time_window_str,
        "prediction_factors": prediction_factors,
        "recommended_action": recommended_action,
        "evacuation_tier": evacuation_tier,
        "hydrological_features": {
            "rainfall_1h": rain_1h,
            "rainfall_6h": rain_6h,
            "rainfall_24h": rain_24h,
            "rainfall_72h": rain_72h,
            "rainfall_forecast_24h": rain_fc_24h,
            "rainfall_intensity_ratio": intensity_ratio,
            "soil_moisture_pct": soil_moisture_pct,
            "soil_saturation_index": soil_saturation_index,
            "slope_angle_deg": slope_angle_deg,
            "elevation_m": elevation_m,
            "terrain_type": terrain_type,
            "geological_stability": geological_stability,
            "historical_floods": hist_floods,
            "historical_landslides": hist_landslides,
            "river_level": river_level,
            "danger_level": danger_level,
            "warning_level": warning_level,
            "river_crest_ratio": river_crest_ratio,
            "temperature": temperature,
            "humidity": humidity,
            "wind_speed": wind_speed,
            "iot_active": iot_active
        }
    }


def _compute_flash_flood_risk(
    r1: float, r6: float, r24: float, r72: float, rfc: float,
    soil_pct: float, river: float, danger: float, warning: float,
    hist_floods: int, elev: float, slope: float,
    humidity: float = 80.0, wind_speed: float = 15.0
) -> Tuple[str, float]:
    """Compute Flash Flood Risk tier and probability using physical multi-source indicators."""
    score = 0.0
    
    # Precipitation burst & accumulation factor (Max 40 pts)
    if r1 >= 35.0: score += 20.0     # Cloudburst intensity (>35mm/h)
    elif r1 >= 18.0: score += 12.0
    elif r1 >= 8.0: score += 6.0
    
    if r24 >= 140.0: score += 15.0
    elif r24 >= 85.0: score += 10.0
    elif r24 >= 45.0: score += 5.0
    
    if r72 >= 220.0: score += 8.0
    elif r72 >= 130.0: score += 5.0
    
    # Soil Moisture Saturation (Max 20 pts)
    # Saturated soil has near-zero infiltration, driving 95%+ surface runoff
    if soil_pct >= 88.0: score += 20.0
    elif soil_pct >= 75.0: score += 14.0
    elif soil_pct >= 60.0: score += 7.0
    
    # River Gauge Hydro-Discharge (Max 25 pts)
    if danger > 0 and river > 0:
        if river >= danger:
            score += 25.0
        elif river >= warning:
            ratio = (river - warning) / max(0.1, danger - warning)
            score += 15.0 + (ratio * 10.0)
        elif river >= (warning * 0.85):
            score += 8.0
    
    # Historical Disaster Frequency & Basin Vulnerability (Max 15 pts)
    if hist_floods >= 18: score += 15.0
    elif hist_floods >= 12: score += 10.0
    elif hist_floods >= 6: score += 5.0
    
    # Topographic Elevation & Slope Drainage Dynamics (Physical Head)
    if elev > 1200.0 and slope > 20.0:
        # High mountain headwaters: steep gravitational gradient drives high-velocity torrents & gorge surges
        score += 8.0
    elif elev < 100.0 and slope < 5.0:
        # Lowland flood basin: near-zero drainage gradient causes prolonged backwater ponding
        score += 6.0

    # Lowland accumulation vs steep funnel modifier
    if slope < 6.0:  # Flat floodplain prone to prolonged backwater inundation
        score *= 1.05
    elif slope > 25.0 and r1 > 20.0:  # Mountain torrent / steep gorge flash surge
        score *= 1.10

    # Atmospheric Weather Factor: zero-evapotranspiration saturation
    if humidity >= 88.0:
        score += 4.0
    if wind_speed >= 28.0:
        score += 3.0
        
    score = min(100.0, score)
    
    # Classification
    if score >= 75.0:
        return "CRITICAL", round(min(99.9, 88.0 + (score - 75.0) * 0.45), 1)
    elif score >= 50.0:
        return "HIGH", round(min(95.0, 75.0 + (score - 50.0) * 0.75), 1)
    elif score >= 28.0:
        return "MODERATE", round(min(80.0, 55.0 + (score - 28.0) * 0.90), 1)
    else:
        return "LOW", round(max(50.0, 70.0 - score * 0.6), 1)


def _compute_landslide_risk(
    slope: float, elev: float, stability: float,
    r1: float, r24: float, r72: float, soil_pct: float,
    hist_landslides: int, humidity: float = 80.0
) -> Tuple[str, float]:
    """
    Compute Landslide Risk using geotechnical infinite-slope criteria,
    elevation gravitational potential energy, pore-water pressure saturation,
    and empirical rainfall threshold curves.
    """
    score = 0.0
    
    # 1. Slope Angle is the foundational driving shear force (Max 35 pts)
    if slope >= 35.0: score += 35.0
    elif slope >= 28.0: score += 26.0
    elif slope >= 20.0: score += 18.0
    elif slope >= 12.0: score += 8.0
    else: score += 1.0  # Very flat plains have negligible slope failure risk
    
    # 2. Elevation Relief & Gravitational Head (Max 12 pts)
    # High mountain elevation has severe weathering, periglacial talus, and massive potential energy
    if elev >= 1600.0: score += 10.0
    elif elev >= 900.0: score += 6.0
    elif elev < 120.0 and slope < 8.0: score = min(score, 12.0)
    
    # 3. Soil Moisture & Pore-Water Pressure (Max 25 pts)
    # High pore-water pressure dramatically weakens internal friction angle
    if soil_pct >= 85.0: score += 25.0
    elif soil_pct >= 72.0: score += 18.0
    elif soil_pct >= 55.0: score += 8.0
    
    # 4. Antecedent 72h + 24h Rainfall (Liquefaction trigger) (Max 20 pts)
    if r72 >= 200.0: score += 14.0
    elif r72 >= 120.0: score += 9.0
    
    if r1 >= 25.0: score += 8.0  # Intense cloudburst triggering debris slip
    elif r24 >= 100.0: score += 6.0
    
    # 5. Historical Landslide Inventory & Geological Instability (Max 20 pts)
    if hist_landslides >= 18: score += 15.0
    elif hist_landslides >= 10: score += 10.0
    elif hist_landslides >= 4: score += 5.0
    
    if stability >= 0.85: score += 5.0  # GSI High susceptibility zone
    if humidity >= 90.0: score += 3.0   # Extreme air saturation prevents soil drainage
    
    # If slope is minimal (< 8 degrees), cap landslide risk strictly to LOW
    if slope < 8.0:
        score = min(20.0, score * 0.25)
        
    score = min(100.0, score)
    
    if score >= 72.0:
        return "CRITICAL", round(min(99.8, 86.0 + (score - 72.0) * 0.48), 1)
    elif score >= 48.0:
        return "HIGH", round(min(94.0, 74.0 + (score - 48.0) * 0.80), 1)
    elif score >= 26.0:
        return "MODERATE", round(min(78.0, 54.0 + (score - 26.0) * 0.88), 1)
    else:
        return "LOW", round(max(52.0, 75.0 - score * 0.8), 1)


def _determine_hazard_type(flood_risk: str, landslide_risk: str, slope: float, crest: float) -> str:
    """Classify primary combined hazard phenomenon."""
    high_risks = {"HIGH", "CRITICAL"}
    
    if flood_risk in high_risks and landslide_risk in high_risks:
        if slope >= 25.0:
            return "Multi-Hazard Debris Flow & Flash Torrential Surge"
        return "Severe Concurrent Inundation & Slope Failure"
    elif landslide_risk in high_risks:
        if slope >= 32.0:
            return "Precipitous Rockfall & Debris Avalanche Risk"
        return "Deep-Seated Slope Slip & Mudflow"
    elif flood_risk in high_risks:
        if crest >= 1.0:
            return "Active River Overtopping & Flash Flood Inundation"
        return "Intense Surface Runoff & Lowland Inundation"
    elif flood_risk == "MODERATE" or landslide_risk == "MODERATE":
        if landslide_risk == "MODERATE":
            return "Localized Slope Instability & Gully Erosion"
        return "Moderate Hydrological Waterlogging & River Sump"
    else:
        return "Normal Hydrological & Slope Stability Conditions"


def _estimate_lead_time(
    flood_risk: str, landslide_risk: str, r1: float, r24: float,
    soil_pct: float, river: float, danger: float, slope: float
) -> Tuple[float, str]:
    """Estimate remaining lead time buffer before peak critical impact in hours."""
    # Critical state: immediate threat within 1.0 - 3.0 hours
    if flood_risk == "CRITICAL" or landslide_risk == "CRITICAL":
        lead = round(max(1.2, 3.5 - (r1 / 18.0) - (soil_pct / 120.0)), 1)
        window = f"Next {lead} to {round(lead + 2.5, 1)} Hours (Immediate Red Alert)"
        return lead, window
    
    # High state: 3.0 - 6.5 hours buffer
    elif flood_risk == "HIGH" or landslide_risk == "HIGH":
        lead = round(max(3.0, 6.5 - (r1 / 15.0) - (r24 / 80.0)), 1)
        window = f"Next {lead} to {round(lead + 3.0, 1)} Hours (High Vulnerability Phase)"
        return lead, window
        
    # Moderate state: 7.0 - 14.0 hours buffer
    elif flood_risk == "MODERATE" or landslide_risk == "MODERATE":
        lead = round(max(7.0, 12.0 - (r24 / 30.0)), 1)
        window = f"Next {lead} to {round(lead + 6.0, 1)} Hours (Monitoring Phase)"
        return lead, window
        
    # Low / Normal state: > 24 hours safe window
    else:
        return 24.0, "Stable Over Next 24+ Hours (Normal Operations)"


def _calculate_prediction_factors(
    r24: float, r1: float, soil_pct: float, slope: float,
    hist_f: int, hist_ls: int, crest: float, flood_risk: str, ls_risk: str,
    elevation_m: float = 450.0, iot_active: bool = False
) -> Dict[str, Any]:
    """
    Compute explainable feature attribution weights summing to 100%.
    Demonstrates model reasoning across the core input categories including Topographic Elevation & Slope.
    """
    # Raw importance weights based on physics and ML attribution
    rain_weight = (r1 * 2.2) + (r24 * 0.4) + 12.0
    soil_weight = (soil_pct * 0.85) + 10.0
    # Topography incorporates both slope angle and elevation relief
    topo_weight = (slope * 1.5) + (min(elevation_m, 3000.0) / 100.0) + 8.0
    hist_weight = ((hist_f + hist_ls) * 1.5) + 10.0
    river_weight = (crest * 35.0) + 10.0
    iot_weight = 12.0 if iot_active else 0.0
    
    total = rain_weight + soil_weight + topo_weight + hist_weight + river_weight + iot_weight
    
    p_rain = round((rain_weight / total) * 100.0, 1)
    p_soil = round((soil_weight / total) * 100.0, 1)
    p_topo = round((topo_weight / total) * 100.0, 1)
    p_hist = round((hist_weight / total) * 100.0, 1)
    p_river = round((river_weight / total) * 100.0, 1)
    p_iot = round((iot_weight / total) * 100.0, 1) if iot_active else 0.0
    
    # Normalize rounding drift so sum = exactly 100.0
    diff = round(100.0 - (p_rain + p_soil + p_topo + p_hist + p_river + p_iot), 1)
    p_rain = round(p_rain + diff, 1)
    
    res = {
        "rainfall_dynamics_pct": p_rain,
        "soil_saturation_pct": p_soil,
        "slope_topography_pct": p_topo,
        "slope_elevation_pct": p_topo,
        "historical_disaster_pct": p_hist,
        "river_hydro_pct": p_river,
        "elevation_m": elevation_m,
        "summary": (
            f"Prediction driven primarily by Rainfall Surge ({p_rain}%) and "
            f"Soil Saturation ({p_soil}%), compounded by Topographic Slope & Elevation Relief ({p_topo}%)."
        )
    }
    if iot_active:
        res["iot_sensor_pct"] = p_iot
        res["summary"] += f" Calibrated with IoT Micro-Sensor Telemetry ({p_iot}%)."
        
    return res


def _generate_action_protocol(flood_risk: str, ls_risk: str, hazard: str, lead_time: float) -> Tuple[list, str]:
    """Generate hyper-local emergency action protocol and evacuation tier."""
    if flood_risk == "CRITICAL" or ls_risk == "CRITICAL":
        tier = "STAGE 3: IMMEDIATE EVACUATION - Relocate vulnerable settlements to high-ground relief centers immediately."
        actions = [
            f"Mandatory evacuation for all settlements along active waterways or steep slopes within {lead_time} hours.",
            "De-energize main high-tension power feeds and low-lying sub-stations to prevent electrocution.",
            "Mobilize SDRF / NDRF quick-response boats and mountain rescue ropes to designated staging zones.",
            "Activate emergency relief shelters and distribute water purification kits and ration packets."
        ]
    elif flood_risk == "HIGH" or ls_risk == "HIGH":
        tier = "STAGE 2: PRE-EVACUATION ALERT - High-risk wards on standby with essential emergency go-bags."
        actions = [
            "Alert hospital emergency wings, pregnant mothers, seniors, and livestock owners for priority transport.",
            "Clear debris and keep natural storm drains and culverts unobstructed to minimize hydraulic damming.",
            "Halt vehicular transit on vulnerable hillside passes, bridge approaches, and low submersible causeways.",
            "Verify backup telecommunication links (VHF radio/satellite) with district Emergency Operations Centre (EOC)."
        ]
    elif flood_risk == "MODERATE" or ls_risk == "MODERATE":
        tier = "STAGE 1: STANDBY & MONITORING - Automated warning broadcasts active; volunteer cells on watch."
        actions = [
            "Monitor hourly river gauge telemetry and soil moisture drainage trends across local catchments.",
            "Advise residents away from riverbanks, steep cuts, and excavated hillside embankments.",
            "Keep emergency vehicles fueled and relief equipment pre-positioned at block headquarters."
        ]
    else:
        tier = "STAGE 0: NORMAL PRECAUTION - Routine monitoring active; safe environmental thresholds."
        actions = [
            "Standard weather surveillance active. No imminent flood or landslide hazard detected.",
            "Continue regular maintenance of drainage corridors and geotechnical slope retaining walls.",
            "Community members advised to maintain standard home disaster survival kits."
        ]
        
    return actions, tier
