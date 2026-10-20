
import streamlit as st
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
METRICS_FILE = BASE_DIR / "logs" / "model_metrics.csv"

st.set_page_config(
    page_title="MLOps Model Monitoring",
    page_icon="🤖",
    layout="wide"
)

st.title("Network Intrusion Detection – MLOps")
st.subheader("Decision Tree vs Random Forest")

if not METRICS_FILE.exists():
    st.error("Model metrics not found. Run train_model.py first.")
    st.stop()

df = pd.read_csv(METRICS_FILE)

st.subheader("Model Performance Comparison")
st.dataframe(df, use_container_width=True, hide_index=True)

metrics = ["Accuracy", "Precision", "Recall", "F1 Score"]

st.subheader("Performance Metrics")
st.bar_chart(df.set_index("Model")[metrics])

best_model = df.loc[df["F1 Score"].idxmax()]

st.success(
    f"Best Model by F1 Score: {best_model['Model']}"
)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Accuracy", f"{best_model['Accuracy']:.2%}")
col2.metric("Precision", f"{best_model['Precision']:.2%}")
col3.metric("Recall", f"{best_model['Recall']:.2%}")
col4.metric("F1 Score", f"{best_model['F1 Score']:.2%}")

st.info(
    "Metrics are calculated on the held-out 30% test dataset. "
    "This dashboard shows evaluation results, not live model drift."
)
