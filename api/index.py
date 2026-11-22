"""
FastAPI Serverless Application for Heart Disease Prediction on Vercel
Supports /api/predict, /api/health, and root documentation.
"""

import os
import json
import math
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field

app = FastAPI(
    title="CardioPredict AI - Heart Disease Risk Prediction Engine",
    description="Clinical decision support API powered by machine learning with One-Hot categorical encoding.",
    version="1.0.0"
)

# CORS middleware for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent.parent
WEIGHTS_PATH = BASE_DIR / "models" / "inference_weights.json"
METADATA_PATH = BASE_DIR / "models" / "model_metadata.json"

# Load weights and metadata
_weights = None
_metadata = None

def load_resources():
    global _weights, _metadata
    if _weights is None and WEIGHTS_PATH.exists():
        with open(WEIGHTS_PATH, "r") as f:
            _weights = json.load(f)
    if _metadata is None and METADATA_PATH.exists():
        with open(METADATA_PATH, "r") as f:
            _metadata = json.load(f)
    return _weights

load_resources()

class PatientVitals(BaseModel):
    age: float = Field(..., ge=18, le=100, description="Patient age in years")
    sex: str = Field(..., description="Biological sex ('Male' or 'Female')")
    blood_pressure: float = Field(..., ge=70, le=240, description="Resting systolic blood pressure (mmHg)")
    cholesterol: float = Field(..., ge=100, le=450, description="Total serum cholesterol (mg/dL)")
    bmi: float = Field(..., ge=10.0, le=60.0, description="Body Mass Index (kg/m²)")
    smoker: str = Field(..., description="Smoking status ('Yes' or 'No')")
    diabetes: str = Field(..., description="Diabetes diagnosis ('Yes' or 'No')")
    physical_activity: float = Field(..., ge=0, le=7, description="Weekly physical activity frequency (0 - 4)")
    family_history: str = Field(..., description="Family history of cardiac disease ('Yes' or 'No')")
    stress_level: float = Field(..., ge=1, le=10, description="Perceived stress level (1 - 9)")

def compute_prediction(data: PatientVitals):
    weights = load_resources()
    if not weights:
        raise RuntimeError("Inference weights not found.")
    
    # 1. Scale numerical features
    num_vals = [
        data.age,
        data.blood_pressure,
        data.cholesterol,
        data.bmi,
        data.physical_activity,
        data.stress_level
    ]
    scaled_nums = [
        (v - m) / s for v, m, s in zip(num_vals, weights['scaler_means'], weights['scaler_scales'])
    ]
    
    # 2. One-Hot Encode categorical features (drop='first': Male=1, Smoker Yes=1, Diabetes Yes=1, Family History Yes=1)
    sex_male = 1.0 if data.sex.strip().lower() in ['male', 'm'] else 0.0
    smoker_yes = 1.0 if data.smoker.strip().lower() in ['yes', 'y'] else 0.0
    diabetes_yes = 1.0 if data.diabetes.strip().lower() in ['yes', 'y'] else 0.0
    family_yes = 1.0 if data.family_history.strip().lower() in ['yes', 'y'] else 0.0
    
    encoded_vector = scaled_nums + [sex_male, smoker_yes, diabetes_yes, family_yes]
    
    # 3. Logistic Sigmoid computation
    intercept = weights['lr_intercept']
    coefs = weights['lr_coefficients']
    z = intercept + sum(w * x for w, x in zip(coefs, encoded_vector))
    prob = 1.0 / (1.0 + math.exp(-z))
    pred = 1 if prob >= 0.50 else 0
    
    # Risk categorization
    if prob < 0.35:
        risk_tier = "Low Risk"
        badge_color = "green"
    elif prob < 0.60:
        risk_tier = "Moderate Risk"
        badge_color = "amber"
    else:
        risk_tier = "High Risk"
        badge_color = "red"
        
    # Contributing factors
    risk_factors = []
    if smoker_yes:
        risk_factors.append("Active Tobacco Smoking (Statistically significant risk factor, p=0.048)")
    if data.blood_pressure >= 130:
        risk_factors.append(f"Elevated Systolic Blood Pressure ({data.blood_pressure:.0f} mmHg - Stage 1/2 Hypertension)")
    if data.cholesterol >= 200:
        risk_factors.append(f"Hypercholesterolemia ({data.cholesterol:.0f} mg/dL - Above clinical threshold)")
    if data.bmi >= 30:
        risk_factors.append(f"Obesity Category BMI ({data.bmi:.1f} kg/m²)")
    elif data.bmi >= 25:
        risk_factors.append(f"Overweight BMI ({data.bmi:.1f} kg/m²)")
    if diabetes_yes:
        risk_factors.append("Diagnosed Diabetes Mellitus comorbidity")
    if family_yes:
        risk_factors.append("Familial predisposition / positive cardiovascular family history")
    if data.physical_activity <= 1:
        risk_factors.append("Sedentary lifestyle (Low physical activity frequency)")
    if data.stress_level >= 7:
        risk_factors.append(f"Severe perceived psychological stress (Level {data.stress_level:.0f}/9)")
        
    return {
        "prediction": pred,
        "diagnosis": "Positive (Likely Heart Disease)" if pred == 1 else "Negative (Unlikely Heart Disease)",
        "probability_percent": round(prob * 100, 2),
        "risk_tier": risk_tier,
        "badge_color": badge_color,
        "model_used": "Trained Classifier Pipeline with One-Hot Categorical Encoding",
        "contributing_risk_factors": risk_factors,
        "encoded_feature_vector": {fn: round(val, 4) for fn, val in zip(weights['features'], encoded_vector)}
    }

@app.get("/health")
@app.get("/api/health")
def health():
    return {
        "status": "online",
        "service": "CardioPredict AI Heart Disease Classification Engine",
        "author": "Isaac Akumani",
        "version": "1.0.0",
        "model_loaded": _weights is not None
    }

@app.get("/api/metadata")
def get_metadata():
    if _metadata:
        return _metadata
    return {"message": "Metadata loading"}

@app.post("/predict")
@app.post("/api/predict")
def predict(data: PatientVitals):
    try:
        result = compute_prediction(data)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def serve_index():
    public_index = BASE_DIR / "public" / "index.html"
    if public_index.exists():
        return FileResponse(public_index)
    return {"message": "Heart Disease Classification API is running. Visit /docs for OpenAPI specs."}
