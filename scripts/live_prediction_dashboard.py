
import streamlit as st
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CSV_FILE = BASE_DIR / "logs" / "auto_predictions.csv"

st.set_page_config(
    page_title="Live Network Intrusion Monitoring",
    page_icon="🛡️",
    layout="wide"
)

st.title("Automated Network Intrusion Detection")
st.caption("DataOps | MLOps | FastAPI | Automated Predictions")

@st.fragment(run_every="10s")
def live_dashboard():

    if not CSV_FILE.exists():
        st.warning("Waiting for automatic prediction data...")
        return

    try:
        df = pd.read_csv(CSV_FILE)
    except (pd.errors.EmptyDataError, OSError):
        st.warning("Prediction data is not ready yet.")
        return

    if df.empty:
        st.warning("No predictions available yet.")
        return

    required = {"timestamp", "actual_label", "prediction"}
    if not required.issubset(df.columns):
        st.error("Prediction CSV has missing columns.")
        return

    total = len(df)
    normal = int((df["prediction"] == 0).sum())
    attacks = int((df["prediction"] == 1).sum())

    accuracy = (
        (df["actual_label"] == df["prediction"]).mean()
        * 100
    )

    false_positives = int(
        ((df["actual_label"] == 0) &
         (df["prediction"] == 1)).sum()
    )

    st.subheader("Live Prediction Summary")

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Total Predictions", total)
    c2.metric("Normal", normal)
    c3.metric("Attack", attacks)
    c4.metric("Sample Accuracy", f"{accuracy:.2f}%")
    c5.metric("False Positives", false_positives)

    st.subheader("Traffic Classification")
    counts = pd.DataFrame({
        "Traffic": ["Normal", "Attack"],
        "Count": [normal, attacks]
    })

    st.bar_chart(counts.set_index("Traffic"))

    st.subheader("Recent Predictions")
    st.dataframe(
        df.tail(30).iloc[::-1],
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "Data comes from replayed historical UNSW-NB15 "
        "records, not live network packets. Sample accuracy "
        "is measured on processed records, not an independent "
        "held-out test set."
    )

live_dashboard()
