from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
from xgboost import XGBClassifier


app = FastAPI(
    title="AapdaSetu",
    description="AI-powered Flash Flood Prediction and Disaster Response Platform",
    version="1.0.0"
)


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# Load ML Model
model = XGBClassifier()
model.load_model("backend/xgboost_flood_model.json")


# Input Schema
class FloodInput(BaseModel):
    rainfall_1h: float
    rainfall_6h: float
    rainfall_24h: float
    rainfall_72h: float
    temperature: float
    humidity: float
    wind_speed: float
    river_level: float
    danger_level: float
    warning_level: float


# Home
@app.get("/")
def home():
    return {
        "project": "AapdaSetu",
        "status": "Backend is running"
    }


# Health Check
@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# Flood Prediction
@app.post("/predict")
def predict(data: FloodInput):

    input_data = pd.DataFrame([{
        "rainfall_1h": data.rainfall_1h,
        "rainfall_6h": data.rainfall_6h,
        "rainfall_24h": data.rainfall_24h,
        "rainfall_72h": data.rainfall_72h,
        "temperature": data.temperature,
        "humidity": data.humidity,
        "wind_speed": data.wind_speed,
        "river_level": data.river_level,
        "danger_level": data.danger_level,
        "warning_level": data.warning_level
    }])


    prediction = int(model.predict(input_data)[0])

    probabilities = model.predict_proba(input_data)[0]

    # Model classes are 0 = LOW, 1 = HIGH
    if prediction == 1:
        risk = "HIGH"
        probability = float(probabilities[1] * 100)
    else:
        risk = "LOW"
        probability = float(probabilities[0] * 100)


    return {
        "flood_risk": risk,
        "risk_probability": round(probability, 2)
    }