from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
import tempfile
import rasterio
from rasterio.warp import transform as raster_transform
import os
import uuid
import json
import pandas as pd
import psycopg
from dotenv import load_dotenv
from xgboost import XGBClassifier
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="AapdaSetu",
    description="AI-powered Flash Flood Prediction and Disaster Response Platform",
    version="1.0.0"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# =========================================================
# LOAD XGBOOST MODEL
# =========================================================

model = XGBClassifier()
model.load_model("backend/xgboost_flood_model.json")


# =========================================================
# REQUEST MODELS
# =========================================================

class LocationInput(BaseModel):
    state: str
    district: str


class ChatInput(BaseModel):
    message: str
    language: str = "hinglish"


class RescueRequest(BaseModel):
    name: str
    phone: str
    people: int
    rescue_vehicle: str
    pickup_location: str
    priority: str = "Medium"
    additional_info: str = ""


class QuickRescueRequest(BaseModel):
    pickup_location: str
    state: str = ""
    district: str = ""
    latitude: float | None = None
    longitude: float | None = None
    flood_risk: str = "UNKNOWN"
    risk_probability: float = 0
    priority: str = "Critical"


class ForecastInput(BaseModel):
    state: str
    district: str


# =========================================================
# DATABASE HELPER
# =========================================================

def get_database_url():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise HTTPException(
            status_code=500,
            detail="DATABASE_URL is not configured"
        )

    return database_url


# =========================================================
# CREATE RESCUE TABLE
# =========================================================

def create_rescue_table():
    query = """
        CREATE TABLE IF NOT EXISTS rescue_requests (
            id SERIAL PRIMARY KEY,
            request_id VARCHAR(30) UNIQUE NOT NULL,
            name VARCHAR(150) NOT NULL,
            phone VARCHAR(30) NOT NULL,
            people INTEGER NOT NULL,
            rescue_vehicle VARCHAR(100) NOT NULL,
            pickup_location TEXT NOT NULL,
            priority VARCHAR(30) DEFAULT 'Medium',
            additional_info TEXT DEFAULT '',
            status VARCHAR(30) DEFAULT 'REQUESTED',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """

    try:
        with psycopg.connect(get_database_url()) as conn:
            with conn.cursor() as cur:
                cur.execute(query)
            conn.commit()
    except Exception as e:
        print(f"WARNING: Rescue table could not be created: {e}")


create_rescue_table()


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():
    return {
        "project": "AapdaSetu",
        "status": "Backend is running"
    }


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# =========================================================
# GET LOCATIONS
# =========================================================

@app.get("/locations")
def locations():
    query = """
        SELECT DISTINCT
            state,
            district
        FROM weather_data
        ORDER BY state, district;
    """

    try:
        with psycopg.connect(get_database_url()) as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )

    return [
        {
            "state": row[0],
            "district": row[1]
        }
        for row in rows
    ]


# =========================================================
# WEATHER API - DATABASE WEATHER
# =========================================================

@app.post("/weather")
def weather(data: LocationInput):
    """Return database weather when available, otherwise use live Open-Meteo data."""
    query = """
        SELECT
            rainfall_1h,
            rainfall_6h,
            rainfall_24h,
            rainfall_72h,
            temperature,
            humidity,
            wind_speed
        FROM weather_data
        WHERE LOWER(TRIM(state)) = LOWER(TRIM(%s))
        AND LOWER(TRIM(district)) = LOWER(TRIM(%s))
        LIMIT 1;
    """

    row = None

    try:
        with psycopg.connect(get_database_url()) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (data.state, data.district))
                row = cur.fetchone()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )

    if row is not None:
        return {
            "state": data.state,
            "district": data.district,
            "weather": {
                "rainfall_1h": row[0],
                "rainfall_6h": row[1],
                "rainfall_24h": row[2],
                "rainfall_72h": row[3],
                "temperature": row[4],
                "humidity": row[5],
                "wind_speed": row[6]
            },
            "source": "AapdaSetu PostgreSQL weather_data"
        }

    # Database does not contain this district. Use real Open-Meteo
    # observed precipitation/weather instead of inventing values.
    observed = get_open_meteo_observed_weather(
        data.state,
        data.district
    )

    return {
        "state": data.state,
        "district": data.district,
        "weather": observed["weather"],
        "source": "Open-Meteo live fallback",
        "message": (
            "This location was not present in weather_data, so live "
            "Open-Meteo observations were used."
        )
    }


# =========================================================
# OPEN-METEO OBSERVED WEATHER FALLBACK
# =========================================================

def get_open_meteo_observed_weather(state: str, district: str):
    """Get real recent precipitation/weather for locations missing in DB."""
    location = get_location_coordinates(state, district)

    latitude = location.get("latitude")
    longitude = location.get("longitude")

    if latitude is None or longitude is None:
        raise HTTPException(
            status_code=404,
            detail=f"Coordinates not found for {district}, {state}"
        )

    params = urlencode({
        "latitude": latitude,
        "longitude": longitude,
        "timezone": "Asia/Kolkata",
        "past_days": 3,
        "forecast_days": 1,
        "current": ",".join([
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "rain",
            "wind_speed_10m"
        ]),
        "hourly": "precipitation"
    })

    url = "https://api.open-meteo.com/v1/forecast?" + params

    try:
        api_data = fetch_json(
            url,
            service_name="Open-Meteo Observed Weather"
        )
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=str(e)
        )

    current = api_data.get("current", {})
    hourly_rain = api_data.get("hourly", {}).get("precipitation", [])

    # Use the most recent hourly observations returned by the API.
    def rain_sum(hours):
        values = hourly_rain[-hours:] if hourly_rain else []
        return round(sum(float(v or 0) for v in values), 2)

    return {
        "latitude": latitude,
        "longitude": longitude,
        "weather": {
            "rainfall_1h": rain_sum(1),
            "rainfall_6h": rain_sum(6),
            "rainfall_24h": rain_sum(24),
            "rainfall_72h": rain_sum(72),
            "temperature": current.get("temperature_2m"),
            "humidity": current.get("relative_humidity_2m"),
            "wind_speed": current.get("wind_speed_10m")
        }
    }


# =========================================================
# FLOOD PREDICTION API
# =========================================================

@app.post("/predict")
def predict(data: LocationInput):
    query = """
        SELECT
            w.rainfall_1h,
            w.rainfall_6h,
            w.rainfall_24h,
            w.rainfall_72h,
            w.temperature,
            w.humidity,
            w.wind_speed,
            r.river_level,
            r.danger_level,
            r.warning_level
        FROM weather_data w
        LEFT JOIN rivers r
            ON LOWER(TRIM(w.state)) = LOWER(TRIM(r.state))
            AND LOWER(TRIM(w.district)) = LOWER(TRIM(r.district))
        WHERE LOWER(TRIM(w.state)) = LOWER(TRIM(%s))
        AND LOWER(TRIM(w.district)) = LOWER(TRIM(%s))
        LIMIT 1;
    """

    row = None

    try:
        with psycopg.connect(get_database_url()) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (data.state, data.district))
                row = cur.fetchone()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )

    data_source = "AapdaSetu PostgreSQL weather_data"
    river_source = "PostgreSQL rivers"

    # If the selected district is missing from weather_data, use real
    # Open-Meteo observed weather. River values remain 0 because we must
    # never invent a river measurement.
    if row is None:
        observed = get_open_meteo_observed_weather(
            data.state,
            data.district
        )
        weather = observed["weather"]

        row = (
            weather["rainfall_1h"],
            weather["rainfall_6h"],
            weather["rainfall_24h"],
            weather["rainfall_72h"],
            weather["temperature"],
            weather["humidity"],
            weather["wind_speed"],
            0,
            0,
            0
        )
        data_source = "Open-Meteo live fallback"
        river_source = "No river measurement available"

    columns = [
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

    input_data = pd.DataFrame([row], columns=columns)
    input_data = input_data.apply(
        pd.to_numeric,
        errors="coerce"
    ).fillna(0)

    try:
        prediction = int(model.predict(input_data)[0])
        probabilities = model.predict_proba(input_data)[0]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Model prediction error: {str(e)}"
        )

    probability = float(max(probabilities) * 100)

    risk_map = {
        0: "LOW",
        1: "MEDIUM",
        2: "HIGH"
    }

    risk = risk_map.get(prediction, "UNKNOWN")

    return {
        "state": data.state,
        "district": data.district,
        "flood_risk": risk,
        "risk_probability": round(probability, 2),
        "data_source": data_source,
        "river_source": river_source,
        "weather": {
            "rainfall_1h": row[0],
            "rainfall_6h": row[1],
            "rainfall_24h": row[2],
            "rainfall_72h": row[3],
            "temperature": row[4],
            "humidity": row[5],
            "wind_speed": row[6]
        },
        "river": {
            "river_level": row[7],
            "danger_level": row[8],
            "warning_level": row[9]
        }
    }


# =========================================================
# AUTOMATIC DISASTER ALERT
# =========================================================

@app.post("/alerts")
def get_disaster_alert(data: LocationInput):
    try:
        prediction_response = predict(data)

        risk = prediction_response["flood_risk"]
        probability = prediction_response["risk_probability"]

        if risk == "HIGH":
            alert = {
                "level": "CRITICAL",
                "title": "🚨 HIGH FLOOD RISK",
                "message": (
                    f"AI model has detected a high flood risk in "
                    f"{data.district}, {data.state}. "
                    "Move to a safe or higher location and avoid flood water."
                ),
                "action": "IMMEDIATE EVACUATION / RESCUE",
                "color": "red"
            }
        elif risk == "MEDIUM":
            alert = {
                "level": "WARNING",
                "title": "⚠️ FLOOD WARNING",
                "message": (
                    f"Moderate flood risk detected in "
                    f"{data.district}, {data.state}. "
                    "Stay alert and keep emergency supplies ready."
                ),
                "action": "STAY ALERT",
                "color": "orange"
            }
        elif risk == "LOW":
            alert = {
                "level": "NORMAL",
                "title": "✅ LOW FLOOD RISK",
                "message": (
                    f"No significant flood risk is currently detected "
                    f"in {data.district}, {data.state}."
                ),
                "action": "NORMAL MONITORING",
                "color": "green"
            }
        else:
            alert = {
                "level": "UNKNOWN",
                "title": "ℹ️ RISK STATUS UNAVAILABLE",
                "message": "The AI model returned an unknown risk category.",
                "action": "CHECK DATA",
                "color": "gray"
            }

        return {
            "success": True,
            "state": data.state,
            "district": data.district,
            "flood_risk": risk,
            "risk_probability": probability,
            "alert": alert,
            "data_source": prediction_response.get("data_source"),
            "river_source": prediction_response.get("river_source"),
            "emergency_number": "112"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Alert generation failed: {str(e)}"
        )


# =========================================================
# DEBUG WEATHER LOCATION
# =========================================================

@app.post("/debug-weather")
def debug_weather(data: LocationInput):
    query = """
        SELECT
            state,
            district,
            rainfall_1h,
            rainfall_6h,
            rainfall_24h,
            rainfall_72h,
            temperature,
            humidity,
            wind_speed
        FROM weather_data
        WHERE LOWER(TRIM(state)) = LOWER(TRIM(%s))
        AND LOWER(TRIM(district)) = LOWER(TRIM(%s))
        LIMIT 5;
    """

    try:
        with psycopg.connect(get_database_url()) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (data.state, data.district))
                rows = cur.fetchall()

        return {
            "success": True,
            "requested_state": data.state,
            "requested_district": data.district,
            "rows_found": len(rows),
            "data": [
                {
                    "state": row[0],
                    "district": row[1],
                    "rainfall_1h": row[2],
                    "rainfall_6h": row[3],
                    "rainfall_24h": row[4],
                    "rainfall_72h": row[5],
                    "temperature": row[6],
                    "humidity": row[7],
                    "wind_speed": row[8]
                }
                for row in rows
            ]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Debug database error: {str(e)}"
        )


# =========================================================
# AI CHATBOT
# =========================================================

@app.post("/chat")
def chat(data: ChatInput):
    message = data.message.strip().lower()

    if not message:
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty"
        )

    if any(word in message for word in [
        "flash flood",
        "flashflood",
        "achanak baadh",
        "sudden flood"
    ]):
        return {
            "reply": (
                "⚠️ Flash flood bahut rapidly aa sakta hai. "
                "Nadi, stream, drain aur low-lying area se "
                "immediately higher ground ki taraf move karein. "
                "Flood water cross karne ki koshish na karein."
            ),
            "type": "flash_flood"
        }

    if any(word in message for word in [
        "emergency",
        "help",
        "bachao",
        "madad",
        "danger",
        "112"
    ]):
        return {
            "reply": (
                "🚨 Agar emergency hai to turant 112 par call karein. "
                "Safe location ya higher ground par chale jayein. "
                "Flood water se door rahein."
            ),
            "type": "emergency"
        }

    if any(word in message for word in [
        "flood",
        "baadh",
        "badh",
        "paani bhar",
        "water level"
    ]):
        return {
            "reply": (
                "🌊 Flood ke time low-lying areas aur fast-flowing "
                "water se door rahein. Bijli ke poles aur damaged "
                "buildings ke paas na jayein. Official alerts follow karein."
            ),
            "type": "flood"
        }

    if any(word in message for word in [
        "drive",
        "car",
        "bike",
        "vehicle",
        "gaadi"
    ]):
        return {
            "reply": (
                "🚗 Flood water me vehicle drive karna dangerous "
                "ho sakta hai. Water level badh raha ho to vehicle "
                "chhodkar safe higher ground ki taraf move karein."
            ),
            "type": "vehicle"
        }

    if any(word in message for word in [
        "family",
        "parivar",
        "bachche",
        "children"
    ]):
        return {
            "reply": (
                "👨‍👩‍👧 Family ke liye emergency contacts, safe "
                "meeting point aur important documents ready rakhein. "
                "Har member ko emergency plan aur evacuation route "
                "pata hona chahiye."
            ),
            "type": "family"
        }

    if any(word in message for word in [
        "weather",
        "mausam",
        "rain",
        "rainfall",
        "baarish",
        "temperature"
    ]):
        return {
            "reply": (
                "🌦️ Aap AapdaSetu ke Weather section me state aur "
                "district select karke available weather information "
                "check kar sakte hain. Heavy rainfall ke time official "
                "warnings ko priority dein."
            ),
            "type": "weather"
        }

    if any(word in message for word in [
        "rescue",
        "ambulance",
        "rescue boat",
        "rescue vehicle"
    ]):
        return {
            "reply": (
                "🚑 Rescue help ke liye AapdaSetu ke Rescue section "
                "me service select karke apni location, phone number "
                "aur priority submit karein. Life-threatening emergency "
                "me 112 ko immediately call karein."
            ),
            "type": "rescue"
        }

    return {
        "reply": (
            "🤖 Main AapdaSetu Disaster Assistant hoon. "
            "Aap mujhse flood, flash flood, weather, rescue, "
            "emergency ya family safety ke baare me pooch sakte hain."
        ),
        "type": "general"
    }


# =========================================================
# CREATE RESCUE REQUEST
# =========================================================

@app.post("/rescue")
def create_rescue_request(data: RescueRequest):
    request_id = (
        "AS-" +
        uuid.uuid4().hex[:8].upper()
    )

    query = """
        INSERT INTO rescue_requests (
            request_id,
            name,
            phone,
            people,
            rescue_vehicle,
            pickup_location,
            priority,
            additional_info,
            status
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s
        )
        RETURNING request_id, status, created_at;
    """

    try:
        with psycopg.connect(get_database_url()) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    query,
                    (
                        request_id,
                        data.name,
                        data.phone,
                        data.people,
                        data.rescue_vehicle,
                        data.pickup_location,
                        data.priority,
                        data.additional_info,
                        "REQUESTED"
                    )
                )

                result = cur.fetchone()

            conn.commit()

        return {
            "success": True,
            "message": "Rescue request submitted successfully",
            "request_id": result[0],
            "status": result[1],
            "created_at": result[2]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=(
                "Could not create rescue request: "
                + str(e)
            )
        )
@app.post("/rescue/quick")
def quick_rescue(data: QuickRescueRequest):
    """
    Emergency one-click rescue request.

    Unlike /rescue, this endpoint does not require the user to fill a form.
    The browser sends the current GPS location and the backend creates the
    rescue request using safe emergency defaults.
    """
    database_url = get_database_url()

    request_id = "AS-" + uuid.uuid4().hex[:8].upper()

    additional_info = (
        "EMERGENCY QUICK RESCUE REQUEST | "
        f"State: {data.state} | "
        f"District: {data.district} | "
        f"Flood Risk: {data.flood_risk} | "
        f"Risk Probability: {data.risk_probability}% | "
        f"GPS: {data.latitude}, {data.longitude}"
    )

    query = """
        INSERT INTO rescue_requests (
            request_id,
            name,
            phone,
            people,
            rescue_vehicle,
            pickup_location,
            priority,
            additional_info,
            status
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s
        )
        RETURNING request_id, status, created_at;
    """

    try:
        with psycopg.connect(database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    query,
                    (
                        request_id,
                        "AapdaSetu Emergency User",
                        "Not provided",
                        1,
                        "Emergency Rescue Team",
                        data.pickup_location,
                        data.priority,
                        additional_info,
                        "REQUESTED"
                    )
                )

                result = cur.fetchone()

            conn.commit()

        return {
            "success": True,
            "message": "Emergency rescue request submitted successfully.",
            "request_id": result[0],
            "status": result[1],
            "created_at": result[2],
            "pickup_location": data.pickup_location,
            "latitude": data.latitude,
            "longitude": data.longitude,
            "flood_risk": data.flood_risk,
            "risk_probability": data.risk_probability
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to create rescue request: {str(e)}"
        )


# =========================================================
# GET RESCUE REQUEST STATUS
# =========================================================

@app.get("/rescue/{request_id}")
def get_rescue_request(request_id: str):
    query = """
        SELECT
            request_id,
            name,
            phone,
            people,
            rescue_vehicle,
            pickup_location,
            priority,
            additional_info,
            status,
            created_at
        FROM rescue_requests
        WHERE request_id = %s;
    """

    try:
        with psycopg.connect(get_database_url()) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    query,
                    (request_id,)
                )

                result = cur.fetchone()

        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Rescue request not found"
            )

        return {
            "request_id": result[0],
            "name": result[1],
            "phone": result[2],
            "people": result[3],
            "rescue_vehicle": result[4],
            "pickup_location": result[5],
            "priority": result[6],
            "additional_info": result[7],
            "status": result[8],
            "created_at": result[9]
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=(
                "Could not fetch rescue request: "
                + str(e)
            )
        )


# =========================================================
# HTTP JSON HELPER
# =========================================================

def fetch_json(url, service_name="External API"):
    """
    Safely fetch JSON from an external API.

    This is used by Open-Meteo and NASA PMM.
    It gives a useful error instead of a generic JSONDecodeError.
    """

    try:
        request = Request(
            url,
            headers={
                "User-Agent": "AapdaSetu/1.0",
                "Accept": (
                    "application/json, "
                    "application/activity+json, "
                    "text/json;q=0.9, "
                    "*/*;q=0.1"
                )
            }
        )

        with urlopen(request, timeout=30) as response:
            status = response.status
            content_type = response.headers.get(
                "Content-Type",
                ""
            )

            raw = response.read().decode(
                "utf-8",
                errors="replace"
            )

        if status < 200 or status >= 300:
            raise RuntimeError(
                f"{service_name} HTTP {status}: "
                f"{raw[:500]}"
            )

        if not raw.strip():
            raise RuntimeError(
                f"{service_name} returned an empty response."
            )

        try:
            return json.loads(raw)

        except json.JSONDecodeError:
            raise RuntimeError(
                f"{service_name} returned non-JSON response "
                f"(Content-Type: {content_type}). "
                f"Response: {raw[:500]}"
            )

    except HTTPError as e:
        body = ""

        try:
            body = e.read().decode(
                "utf-8",
                errors="replace"
            )
        except Exception:
            pass

        raise RuntimeError(
            f"{service_name} HTTP {e.code}: "
            f"{body[:500]}"
        )

    except URLError as e:
        raise RuntimeError(
            f"{service_name} connection failed: "
            f"{e.reason}"
        )

    except RuntimeError:
        raise

    except Exception as e:
        raise RuntimeError(
            f"{service_name} request failed: "
            f"{str(e)}"
        )


# ============================================================
# OPEN-METEO LOCATION GEOCODING
# ============================================================

def get_location_coordinates(state: str, district: str):
    """
    Find latitude and longitude for the selected Indian district
    using Open-Meteo Geocoding API.
    """

    query = f"{district}, {state}, India"

    params = urlencode({
        "name": query,
        "count": 5,
        "language": "en",
        "format": "json"
    })

    url = (
        "https://geocoding-api.open-meteo.com/v1/search?"
        + params
    )

    try:
        data = fetch_json(
            url,
            service_name="Open-Meteo Geocoding"
        )

    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=str(e)
        )

    results = data.get(
        "results",
        []
    )

    if not results:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Coordinates not found for "
                f"{district}, {state}"
            )
        )

    india_results = [
        item
        for item in results
        if str(
            item.get("country_code", "")
        ).upper() == "IN"
    ]

    result = (
        india_results[0]
        if india_results
        else results[0]
    )

    return {
        "latitude": result.get("latitude"),
        "longitude": result.get("longitude"),
        "name": result.get("name"),
        "country": result.get("country"),
        "timezone": result.get("timezone")
    }


# ============================================================
# WEATHER CODE CONVERSION
# ============================================================

def weather_code_to_condition(code):
    code = int(code or 0)

    weather_codes = {
        0: "Clear Sky",
        1: "Mainly Clear",
        2: "Partly Cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing Rime Fog",
        51: "Light Drizzle",
        53: "Moderate Drizzle",
        55: "Dense Drizzle",
        56: "Light Freezing Drizzle",
        57: "Dense Freezing Drizzle",
        61: "Slight Rain",
        63: "Moderate Rain",
        65: "Heavy Rain",
        66: "Light Freezing Rain",
        67: "Heavy Freezing Rain",
        71: "Slight Snow",
        73: "Moderate Snow",
        75: "Heavy Snow",
        77: "Snow Grains",
        80: "Slight Rain Showers",
        81: "Moderate Rain Showers",
        82: "Violent Rain Showers",
        85: "Slight Snow Showers",
        86: "Heavy Snow Showers",
        95: "Thunderstorm",
        96: "Thunderstorm with Slight Hail",
        99: "Thunderstorm with Heavy Hail"
    }

    return weather_codes.get(
        code,
        "Unknown Weather"
    )


# ============================================================
# REAL WEATHER FORECAST - OPEN-METEO
# ============================================================

@app.post("/forecast")
def get_forecast(data: ForecastInput):

    try:

        # ----------------------------------------------------
        # 1. GET LOCATION COORDINATES
        # ----------------------------------------------------

        location = get_location_coordinates(
            data.state,
            data.district
        )

        latitude = location["latitude"]
        longitude = location["longitude"]

        if latitude is None or longitude is None:
            raise HTTPException(
                status_code=404,
                detail="Valid coordinates not found."
            )

        # ----------------------------------------------------
        # 2. REAL WEATHER FORECAST
        # ----------------------------------------------------

        forecast_params = urlencode({
            "latitude": latitude,
            "longitude": longitude,
            "timezone": "Asia/Kolkata",
            "forecast_days": 5,
            "current": ",".join([
                "temperature_2m",
                "relative_humidity_2m",
                "precipitation",
                "rain",
                "weather_code",
                "wind_speed_10m"
            ]),
            "daily": ",".join([
                "weather_code",
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "rain_sum",
                "precipitation_probability_max",
                "wind_speed_10m_max"
            ])
        })

        forecast_url = (
            "https://api.open-meteo.com/v1/forecast?"
            + forecast_params
        )

        weather_data = fetch_json(
            forecast_url,
            service_name="Open-Meteo Forecast"
        )

        current = weather_data.get(
            "current",
            {}
        )

        daily = weather_data.get(
            "daily",
            {}
        )

        dates = daily.get(
            "time",
            []
        )

        weather_codes = daily.get(
            "weather_code",
            []
        )

        max_temp = daily.get(
            "temperature_2m_max",
            []
        )

        min_temp = daily.get(
            "temperature_2m_min",
            []
        )

        rainfall = daily.get(
            "precipitation_sum",
            []
        )

        rain_probability = daily.get(
            "precipitation_probability_max",
            []
        )

        wind_speed = daily.get(
            "wind_speed_10m_max",
            []
        )

        # ----------------------------------------------------
        # 3. BUILD FORECAST RESPONSE
        # ----------------------------------------------------

        forecast = []

        for i in range(len(dates)):

            forecast.append({
                "date": dates[i],

                "condition": weather_code_to_condition(
                    weather_codes[i]
                    if i < len(weather_codes)
                    else 0
                ),

                "weather_code": (
                    weather_codes[i]
                    if i < len(weather_codes)
                    else None
                ),

                "temperature_max": (
                    max_temp[i]
                    if i < len(max_temp)
                    else None
                ),

                "temperature_min": (
                    min_temp[i]
                    if i < len(min_temp)
                    else None
                ),

                "rainfall": (
                    rainfall[i]
                    if i < len(rainfall)
                    else None
                ),

                "rain_probability": (
                    rain_probability[i]
                    if i < len(rain_probability)
                    else None
                ),

                "wind_speed": (
                    wind_speed[i]
                    if i < len(wind_speed)
                    else None
                )
            })

        # ----------------------------------------------------
        # 4. CURRENT WEATHER
        # ----------------------------------------------------

        current_weather = {
            "temperature": current.get(
                "temperature_2m"
            ),

            "humidity": current.get(
                "relative_humidity_2m"
            ),

            "precipitation": current.get(
                "precipitation"
            ),

            "rain": current.get(
                "rain"
            ),

            "wind_speed": current.get(
                "wind_speed_10m"
            ),

            "weather_code": current.get(
                "weather_code"
            ),

            "condition": weather_code_to_condition(
                current.get(
                    "weather_code",
                    0
                )
            )
        }

        # ----------------------------------------------------
        # 5. RETURN REAL FORECAST
        # ----------------------------------------------------

        return {
            "success": True,

            "location": {
                "state": data.state,
                "district": data.district,
                "latitude": latitude,
                "longitude": longitude,
                "timezone": location.get(
                    "timezone"
                )
            },

            "current": current_weather,

            "forecast": forecast,

            "forecast_type": "real",

            "source": {
                "name": "Open-Meteo",
                "website": "https://open-meteo.com/",
                "model_data": "Numerical weather model forecasts"
            },

            "message": (
                "Weather forecast retrieved successfully "
                "from Open-Meteo."
            )
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Forecast processing error: {str(e)}"
        )


# ============================================================
# NASA GPM / IMERG SATELLITE RAINFALL
# ============================================================

# NASA's current public GIBS service provides IMERG visualizations.
# The older Disasters Mapping Portal ArcGIS item URLs documented by
# NASA currently return 404 from the live portal, so this implementation
# does NOT fabricate numeric rainfall values from those dead services.
# Instead, /nasa-rainfall returns a live NASA visualization URL centered
# on the selected district. Numeric IMERG values remain explicitly null
# until a stable public numeric endpoint is available.
NASA_GIBS_WMS = "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi"
NASA_WORLDVIEW = "https://worldview.earthdata.nasa.gov/"
NASA_IMERG_LAYER = "IMERG_Precipitation_Rate"


def nasa_imerg_visualization_url(latitude, longitude, span=1.0):
    """Build a NASA Worldview/GIBS URL around the selected location."""
    lat = float(latitude)
    lon = float(longitude)
    lat_min = max(-90.0, lat - span)
    lat_max = min(90.0, lat + span)
    lon_min = max(-180.0, lon - span)
    lon_max = min(180.0, lon + span)

    # NASA Worldview accepts a layer selection and map center/zoom.
    # Keep the URL simple and human-shareable.
    return (
        "https://worldview.earthdata.nasa.gov/?v="
        f"{lon_min:.4f},{lat_min:.4f},{lon_max:.4f},{lat_max:.4f}"
        f"&l={NASA_IMERG_LAYER}"
    )


def nasa_gibs_wms_url(latitude, longitude, span=1.0):
    """Build a NASA GIBS WMS GetMap URL for IMERG precipitation rate."""
    lat = float(latitude)
    lon = float(longitude)
    lat_min = max(-90.0, lat - span)
    lat_max = min(90.0, lat + span)
    lon_min = max(-180.0, lon - span)
    lon_max = min(180.0, lon + span)

    params = urlencode({
        "service": "WMS",
        "version": "1.3.0",
        "request": "GetMap",
        "layers": NASA_IMERG_LAYER,
        "styles": "",
        "crs": "EPSG:4326",
        "bbox": f"{lat_min},{lon_min},{lat_max},{lon_max}",
        "width": 900,
        "height": 700,
        "format": "image/png",
        "transparent": "true"
    })

    return f"{NASA_GIBS_WMS}?{params}"


# ============================================================
# NASA RAINFALL API
# ============================================================

@app.post("/nasa-rainfall")
def nasa_rainfall(data: LocationInput):
    """
    Return NASA GPM IMERG visualization information for a district.

    Important: this endpoint does not invent numeric rainfall values.
    NASA's currently documented Disasters Mapping Portal ArcGIS item
    links are returning HTTP 404, while the public GIBS visualization
    service remains available. Therefore numeric IMERG values are null
    here and a live NASA visualization is returned instead.
    """

    try:
        location = get_location_coordinates(
            data.state,
            data.district
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Could not resolve location coordinates: {exc}"
        )

    latitude = location.get("latitude")
    longitude = location.get("longitude")

    if latitude is None or longitude is None:
        raise HTTPException(
            status_code=404,
            detail="Valid coordinates not found for the selected location."
        )

    worldview_url = nasa_imerg_visualization_url(
        latitude,
        longitude
    )
    gibs_url = nasa_gibs_wms_url(
        latitude,
        longitude
    )

    return {
        "success": True,
        "location": {
            "state": data.state,
            "district": data.district,
            "latitude": latitude,
            "longitude": longitude,
            "timezone": location.get("timezone")
        },
        "rainfall": {
            "rainfall_30min_mm": None,
            "rainfall_3h_mm": None,
            "rainfall_1d_mm": None,
            "rainfall_3d_mm": None,
            "rainfall_7d_mm": None,
            "numeric_data_available": False
        },
        "visualization": {
            "nasa_worldview": worldview_url,
            "nasa_gibs_wms": gibs_url,
            "layer": NASA_IMERG_LAYER,
            "description": (
                "NASA GPM IMERG precipitation visualization centered "
                "on the selected district."
            )
        },
        "source": {
            "name": "NASA Global Precipitation Measurement Mission",
            "product_family": "GPM IMERG",
            "service": "NASA GIBS / Worldview",
            "resolution": "0.1 degree (~10 km)",
            "website": "https://gpm.nasa.gov/data/imerg",
            "data_type": "Satellite precipitation estimate, not a forecast"
        },
        "status": (
            "NASA IMERG visualization is available. Numeric rainfall "
            "values are intentionally not reported until a stable public "
            "numeric NASA endpoint is available."
        )
    }
