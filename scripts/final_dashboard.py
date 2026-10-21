import os
import pandas as pd
import requests
import re
import streamlit as st
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

PREDICTIONS = BASE / "logs" / "auto_predictions.csv"
DATAOPS_LOG = BASE / "logs" / "dataops_scheduler.log"

# Local metrics preferred; cloud deployment metrics as fallback
LOCAL_METRICS = BASE / "logs" / "model_metrics.csv"
CLOUD_METRICS = BASE / "deployment" / "model_metrics.csv"

METRICS = (
    LOCAL_METRICS
    if LOCAL_METRICS.exists()
    else CLOUD_METRICS
)

API_URL = os.getenv(
    "API_URL",
    "http://127.0.0.1:8000"
).rstrip("/")


st.set_page_config(
    page_title="Enterprise Network Security Dashboard",
    page_icon="🛡️",
    layout="wide"
)

st.title("Enterprise Network Security Monitoring")
st.caption(
    "BITS Pilani | API-Driven Cloud Native Solutions | "
    "DataOps • MLOps • FastAPI"
)

def fetch_api(endpoint):
    try:
        response = requests.get(
            API_URL + endpoint, timeout=5
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None

@st.fragment(run_every="10s")
def monitoring():

    overview, dataops, mlops, api = st.tabs([
        "Security Overview",
        "DataOps Monitoring",
        "MLOps Performance",
        "REST API Monitoring"
    ])

    with overview:
        st.subheader("Automated Network Predictions")

        if PREDICTIONS.exists():
            try:
                df = pd.read_csv(PREDICTIONS)
            except (OSError, pd.errors.EmptyDataError):
                df = pd.DataFrame()

            if not df.empty:
                total = len(df)
                normal = int((df["prediction"] == 0).sum())
                attack = int((df["prediction"] == 1).sum())
                false_positive = int((
                    (df["actual_label"] == 0) &
                    (df["prediction"] == 1)
                ).sum())

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Total Predictions", total)
                c2.metric("Normal", normal)
                c3.metric("Attack", attack)
                c4.metric("False Positives", false_positive)

                chart_data = pd.DataFrame({
                    "Traffic": ["Normal", "Attack"],
                    "Predictions": [normal, attack]
                })

                st.bar_chart(
                    chart_data.set_index("Traffic")
                )

                st.subheader("Recent Traffic Predictions")
                st.dataframe(
                    df.tail(30).iloc[::-1],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("Waiting for prediction records...")
        else:
            st.warning("Prediction CSV not found.")

    with dataops:
        st.subheader("Automated DataOps Pipeline")

        if DATAOPS_LOG.exists():
            lines = DATAOPS_LOG.read_text(
                encoding="utf-8",
                errors="replace"
            ).splitlines()

            starts = [
                x for x in lines
                if "DataOps pipeline started" in x
            ]
            finishes = [
                x for x in lines
                if "Pipeline finished in" in x
            ]
            errors = [
                x for x in lines
                if "| ERROR |" in x
            ]

            c1, c2, c3 = st.columns(3)
            c1.metric("Pipeline Runs Started", len(starts))
            c2.metric("Completed Runs", len(finishes))
            c3.metric("Error Entries", len(errors))

            if finishes:
                match = re.search(
                    r"Pipeline finished in ([\d.]+) seconds",
                    finishes[-1]
                )
                if match:
                    st.metric(
                        "Last Execution Duration",
                        f"{float(match.group(1)):.2f} seconds"
                    )

            st.subheader("Recent Scheduler Logs")
            st.code(
                "\n".join(lines[-20:]),
                language="text"
            )
            st.caption(
                "These are recorded executions, "
                "not an independent scheduler process health check."
            )
        else:
            st.warning("DataOps log file not found.")

    with mlops:
        st.subheader("ML Model Evaluation")

        if METRICS.exists():
            metrics_df = pd.read_csv(METRICS)

            st.dataframe(
                metrics_df,
                use_container_width=True,
                hide_index=True
            )

            columns = [
                "Accuracy", "Precision",
                "Recall", "F1 Score"
            ]

            st.bar_chart(
                metrics_df.set_index("Model")[columns]
            )

            best = metrics_df.loc[
                metrics_df["F1 Score"].idxmax()
            ]

            st.success(
                f"Best Model by F1 Score: {best['Model']}"
            )
        else:
            st.warning("ML metrics file not found.")

    with api:
        st.subheader("FastAPI Application Monitoring")

        health = fetch_api("/health")
        dataset = fetch_api("/dataset-info")
        model = fetch_api("/model-info")

        if health:
            st.success("FastAPI is responding")
            st.json(health)
        else:
            st.error("FastAPI is not responding")

        if dataset:
            st.subheader("Dataset Information")
            st.json(dataset)

        if model:
            st.subheader("Model Information")
            st.json(model)

monitoring()

st.caption(
    "Educational prototype using historical UNSW-NB15 "
    "network traffic. Not a production intrusion detection system."
)
