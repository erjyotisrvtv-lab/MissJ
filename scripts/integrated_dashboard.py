
import streamlit as st
import pandas as pd
import requests

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Network Security Cloud Dashboard",
    page_icon="🛡️",
    layout="wide"
)

st.title("Network Intrusion Detection")
st.caption("DataOps | MLOps | REST APIs | Network Security")

def get_api(endpoint):
    try:
        response = requests.get(
            f"{API_URL}{endpoint}",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as error:
        st.error(f"API Error: {error}")
        return None

tab1, tab2, tab3 = st.tabs([
    "Application Overview",
    "MLOps Performance",
    "Network Prediction"
])

with tab1:
    st.header("Application Monitoring")

    health = get_api("/health")
    dataset = get_api("/dataset-info")
    model = get_api("/model-info")

    if health:
        st.subheader("API Health")
        st.json(health)

    if dataset:
        col1, col2 = st.columns(2)
        col1.metric(
            "Dataset Records",
            dataset["total_records"]
        )
        col2.metric(
            "Dataset Columns",
            dataset["total_columns"]
        )

    if model:
        st.subheader("Model Information")
        st.json(model)

with tab2:
    st.header("Machine Learning Performance")

    metrics = get_api("/metrics")

    if metrics:
        df = pd.DataFrame(metrics)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        columns = [
            "Accuracy", "Precision",
            "Recall", "F1 Score"
        ]

        st.bar_chart(
            df.set_index("Model")[columns]
        )

with tab3:
    st.header("Network Traffic Prediction")

    st.info(
        "Enter network traffic features "
        "to predict Normal or Attack."
    )

    features = [
        "dur", "spkts", "dpkts",
        "sbytes", "dbytes", "rate",
        "sttl", "dttl", "sload",
        "dload", "sloss", "dloss",
        "sinpkt", "dinpkt"
    ]

    with st.form("prediction_form"):
        values = {}

        for feature in features:
            values[feature] = st.number_input(
                feature,
                value=0.0,
                format="%.6f"
            )

        submitted = st.form_submit_button(
            "Predict Traffic"
        )

    if submitted:
        try:
            response = requests.post(
                f"{API_URL}/predict",
                json=values,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()

            if result["prediction"] == 1:
                st.error("Attack Traffic Detected")
            else:
                st.success("Normal Traffic Detected")

            st.json(result)

        except requests.RequestException as error:
            st.error(f"Prediction failed: {error}")
