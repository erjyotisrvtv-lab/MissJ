
import pandas as pd
import requests
import time
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "UNSW_NB15_training-set.csv"
OUTPUT_FILE = BASE_DIR / "logs" / "auto_predictions.csv"

API_URL = "http://127.0.0.1:8000/predict"

FEATURES = [
    "dur", "spkts", "dpkts", "sbytes", "dbytes",
    "rate", "sttl", "dttl", "sload", "dload",
    "sloss", "dloss", "sinpkt", "dinpkt"
]

BATCH_SIZE = 100
INTERVAL_SECONDS = 120

df = pd.read_csv(DATA_FILE)

print("Automatic Network Traffic Prediction Started")
print("Total Dataset Records:", len(df))
print("Batch Size:", BATCH_SIZE)
print("Interval: 2 minutes")

offset = 0

while True:
    batch = df.iloc[offset:offset + BATCH_SIZE].copy()

    if batch.empty:
        offset = 0
        continue

    results = []

    for index, row in batch.iterrows():
        payload = {
            feature: float(row[feature])
            for feature in FEATURES
        }

        try:
            response = requests.post(
                API_URL,
                json=payload,
                timeout=10
            )
            response.raise_for_status()

            prediction = response.json()

            results.append({
                "timestamp": datetime.now().isoformat(),
                "record_id": int(index),
                "actual_label": int(row["label"]),
                "prediction": prediction["prediction"],
                "traffic_class": prediction["traffic_class"]
            })

        except requests.RequestException as error:
            print(f"Prediction failed for record {index}: {error}")

    if results:
        result_df = pd.DataFrame(results)

        result_df.to_csv(
            OUTPUT_FILE,
            mode="a",
            header=not OUTPUT_FILE.exists(),
            index=False
        )

        print("\nBatch completed:", datetime.now())
        print("Records Processed:", len(result_df))
        print("Normal Predictions:",
              (result_df["prediction"] == 0).sum())
        print("Attack Predictions:",
              (result_df["prediction"] == 1).sum())

    offset += BATCH_SIZE

    if offset >= len(df):
        offset = 0

    print("\nWaiting 2 minutes for next batch...")
    time.sleep(INTERVAL_SECONDS)
