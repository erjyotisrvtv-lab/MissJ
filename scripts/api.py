"""Network Intrusion Detection FastAPI service."""
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_FILE = BASE_DIR / "models" / "random_forest.pkl"
METRICS_FILE = BASE_DIR / "logs" / "model_metrics.csv"
DATA_FILE = BASE_DIR / "data" / "UNSW_NB15_training-set.csv"
FEATURES = [
    "dur", "spkts", "dpkts", "sbytes", "dbytes", "rate", "sttl",
    "dttl", "sload", "dload", "sloss", "dloss", "sinpkt", "dinpkt"
]

app = FastAPI(
    title="Network Intrusion Detection API",
    description="Network traffic classification with FastAPI and scikit-learn",
    version="1.0.0",
)


class TrafficInput(BaseModel):
    dur: float
    spkts: float
    dpkts: float
    sbytes: float
    dbytes: float
    rate: float
    sttl: float
    dttl: float
    sload: float
    dload: float
    sloss: float
    dloss: float
    sinpkt: float
    dinpkt: float


@lru_cache(maxsize=1)
def load_model():
    return joblib.load(MODEL_FILE)


@app.get("/")
def home():
    return {
        "application": "Network Intrusion Detection",
        "version": "1.0.0",
        "framework": "FastAPI",
        "status": "Running",
    }


@app.get("/health")
def health():
    return {
        "api_status": "Running",
        "model_available": MODEL_FILE.is_file(),
        "metrics_available": METRICS_FILE.is_file(),
    }


@app.get("/dataset-info")
def dataset_info():
    if not DATA_FILE.is_file():
        raise HTTPException(status_code=404, detail="Dataset not found")
    df = pd.read_csv(DATA_FILE)
    return {
        "dataset": "UNSW-NB15",
        "total_records": len(df),
        "total_columns": len(df.columns),
        "target": "label",
    }


@app.get("/model-info")
def model_info():
    return {
        "model": "Random Forest",
        "model_file": MODEL_FILE.name,
        "trained": MODEL_FILE.is_file(),
        "features": FEATURES,
    }


@app.get("/metrics")
def metrics():
    if not METRICS_FILE.is_file():
        raise HTTPException(status_code=404, detail="Model metrics not found")
    return pd.read_csv(METRICS_FILE).to_dict(orient="records")


@app.post("/predict")
def predict(traffic: TrafficInput):
    if not MODEL_FILE.is_file():
        raise HTTPException(status_code=503, detail="Trained model not available")
    try:
        model = load_model()
        input_df = pd.DataFrame([traffic.model_dump()], columns=FEATURES)
        prediction = int(model.predict(input_df)[0])
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Model prediction failed; check server logs") from exc
    return {
        "prediction": prediction,
        "traffic_class": "Attack" if prediction == 1 else "Normal",
    }
