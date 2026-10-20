
import streamlit as st
import pandas as pd
from pathlib import Path
import re

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_FILE = BASE_DIR / "logs" / "dataops_scheduler.log"

st.set_page_config(
    page_title="Cloud DataOps Monitoring",
    page_icon="📊",
    layout="wide"
)

st.title("Cloud-Based Network Traffic Monitoring")
st.subheader("DataOps Pipeline Monitoring Dashboard")

st.info("Pipeline configured to run every 2 minutes")

@st.fragment(run_every="10s")
def monitor_pipeline():

    if not LOG_FILE.exists():
        st.warning("Waiting for DataOps scheduler logs...")
        return

    lines = LOG_FILE.read_text(
        encoding="utf-8"
    ).splitlines()

    starts = [
        line for line in lines
        if "DataOps pipeline started" in line
    ]

    successes = [
        line for line in lines
        if "executed successfully" in line
    ]

    failures = [
        line for line in lines
        if "| ERROR |" in line
    ]

    finished = [
        line for line in lines
        if "Pipeline finished in" in line
    ]

    last_time = (
        starts[-1].split(" | ")[0]
        if starts else "Not available"
    )

    status = "FAILED" if failures and (
        not successes or failures[-1] > successes[-1]
    ) else "SUCCESS" if finished else "WAITING"

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Pipeline Status", status)
    col2.metric("Pipeline Runs Started", len(starts))
    col3.metric("Successful Script Executions", len(successes))
    col4.metric("Failures Logged", len(failures))

    st.write("**Last Pipeline Start:**", last_time)

    if finished:
        match = re.search(
            r"Pipeline finished in ([\d.]+) seconds",
            finished[-1]
        )
        if match:
            st.metric(
                "Last Pipeline Duration",
                f"{float(match.group(1)):.2f} sec"
            )

    st.subheader("DataOps Execution Logs")
    st.code("\n".join(lines[-30:]), language="text")

    if starts:
        timestamps = pd.to_datetime(
            [line.split(" | ")[0] for line in starts],
            errors="coerce"
        )
        valid_times = timestamps.dropna()

        if len(valid_times) > 1:
            intervals = valid_times.to_series().diff()
            interval_minutes = intervals.dt.total_seconds() / 60

            st.subheader("Actual Execution Intervals")
            st.line_chart(
                interval_minutes.dropna().reset_index(drop=True)
            )

monitor_pipeline()
