import os
import re
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Enterprise Network Security Dashboard",
    page_icon="🛡️",
    layout="wide",
)

BASE = Path(__file__).resolve().parent.parent

LOCAL_PREDICTIONS = BASE / "logs" / "auto_predictions.csv"
CLOUD_PREDICTIONS = BASE / "deployment" / "auto_predictions.csv"
PREDICTIONS = LOCAL_PREDICTIONS if LOCAL_PREDICTIONS.exists() else CLOUD_PREDICTIONS

LOCAL_DATAOPS_LOG = BASE / "logs" / "dataops_scheduler.log"
CLOUD_DATAOPS_LOG = BASE / "deployment" / "dataops_scheduler.log"
DATAOPS_LOG = LOCAL_DATAOPS_LOG if LOCAL_DATAOPS_LOG.exists() else CLOUD_DATAOPS_LOG

LOCAL_METRICS = BASE / "logs" / "model_metrics.csv"
CLOUD_METRICS = BASE / "deployment" / "model_metrics.csv"
METRICS = LOCAL_METRICS if LOCAL_METRICS.exists() else CLOUD_METRICS

def get_secret(name, default=""):
    """Use Streamlit Cloud secrets when present; allow local runs without secrets.toml."""
    try:
        return st.secrets.get(name, default)
    except (FileNotFoundError, KeyError):
        return default


API_URL = get_secret(
    "API_URL", os.getenv("API_URL", "http://127.0.0.1:8000")
).rstrip("/")

GITHUB_OWNER = "erjyotisrvtv-lab"
GITHUB_REPO = "MissJ"
GITHUB_WORKFLOW = "dataops-cloud.yml"
GITHUB_RUNS_PAGE = (
    f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/actions"
)

st.title("Enterprise Network Security Monitoring")
st.caption(
    "BITS Pilani | API-Driven Cloud Native Solutions | "
    "DataOps • MLOps • FastAPI"
)


@st.cache_data(ttl=30, show_spinner=False)
def fetch_api(endpoint):
    try:
        response = requests.get(API_URL + endpoint, timeout=8)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError):
        return None


@st.cache_data(ttl=120, show_spinner=False)
def fetch_github_workflow(token):
    """Read latest cloud run; token is required for private repositories."""
    if not token:
        return None, "GitHub token not configured."

    url = (
        f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
        f"/actions/workflows/{GITHUB_WORKFLOW}/runs"
    )
    try:
        response = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            params={"branch": "main", "per_page": 1},
            timeout=15,
        )
        if response.status_code in (401, 403, 404):
            return None, (
                f"GitHub API returned HTTP {response.status_code}. "
                "Check token access, repository permissions and Actions access."
            )
        response.raise_for_status()
        runs = response.json().get("workflow_runs", [])
        return (runs[0], None) if runs else (None, "No workflow runs found.")
    except (requests.RequestException, ValueError):
        return None, "Could not retrieve GitHub Actions status."


def show_cloud_workflow():
    st.divider()
    st.subheader("GitHub Actions — Cloud DataOps")
    st.caption(
        "Cloud workflow status fetched from GitHub Actions. "
        "Scheduled cron: every 5 minutes (best effort), not every 2 minutes."
    )

    token = get_secret("GITHUB_TOKEN", os.getenv("GITHUB_TOKEN", ""))
    run, error = fetch_github_workflow(token)

    if error:
        st.warning(error)
        st.markdown(f"[Open GitHub Actions]({GITHUB_RUNS_PAGE})")
        return

    status = run.get("status", "unknown")
    conclusion = run.get("conclusion") or "Pending"
    run_number = run.get("run_number", "N/A")
    event = run.get("event", "unknown")
    timestamp = run.get("run_started_at") or run.get("created_at") or "N/A"
    html_url = run.get("html_url") or GITHUB_RUNS_PAGE

    c1, c2, c3 = st.columns(3)
    c1.metric("Latest Cloud Run", f"#{run_number}")
    c2.metric("Run Status", str(status).title())
    c3.metric("Result", str(conclusion).title())

    if conclusion == "success":
        st.success("Latest GitHub Actions cloud pipeline succeeded.")
    elif conclusion in ("failure", "cancelled", "timed_out"):
        st.error(f"Latest cloud pipeline result: {conclusion}")
    else:
        st.info(f"Latest cloud pipeline: {status}")

    st.write(f"**Trigger:** {event}")
    st.write(f"**Run started (UTC):** {timestamp}")
    st.markdown(f"[View this run on GitHub]({html_url})")
    st.caption(
        "This reports workflow-level status. Check the GitHub job details "
        "to verify individual extraction, preprocessing and EDA steps."
    )


@st.fragment(run_every="10s")
def monitoring():
    overview, dataops, mlops, api = st.tabs([
        "Security Overview",
        "DataOps Monitoring",
        "MLOps Performance",
        "REST API Monitoring",
    ])

    with overview:
        st.subheader("Automated Network Predictions")

        if PREDICTIONS.exists():
            try:
                df = pd.read_csv(PREDICTIONS)
            except (OSError, pd.errors.ParserError, pd.errors.EmptyDataError):
                df = pd.DataFrame()

            if not df.empty and "prediction" in df.columns:
                predictions = pd.to_numeric(df["prediction"], errors="coerce")
                total = len(df)
                normal = int((predictions == 0).sum())
                attack = int((predictions == 1).sum())

                if "actual_label" in df.columns:
                    actual = pd.to_numeric(df["actual_label"], errors="coerce")
                    false_positive = int(((actual == 0) & (predictions == 1)).sum())
                else:
                    false_positive = None

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Total Predictions", total)
                c2.metric("Normal", normal)
                c3.metric("Attack", attack)
                c4.metric(
                    "False Positives",
                    false_positive if false_positive is not None else "N/A",
                )

                chart_data = pd.DataFrame({
                    "Traffic": ["Normal", "Attack"],
                    "Predictions": [normal, attack],
                })
                st.bar_chart(chart_data.set_index("Traffic"))

                st.subheader("Recent Traffic Predictions")
                st.dataframe(
                    df.tail(30).iloc[::-1],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("Waiting for valid prediction records...")
        else:
            st.warning("Prediction CSV not found.")

        if PREDICTIONS == CLOUD_PREDICTIONS:
            st.caption("Prediction records are a deployed snapshot, not a live feed.")

    with dataops:
        st.subheader("Automated DataOps Pipeline")

        if DATAOPS_LOG.exists():
            lines = DATAOPS_LOG.read_text(
                encoding="utf-8", errors="replace"
            ).splitlines()

            starts = [x for x in lines if "DataOps pipeline started" in x]
            finishes = [
                x for x in lines
                if "Pipeline finished in" in x
                or "DataOps pipeline completed successfully" in x
            ]
            errors = [x for x in lines if "| ERROR |" in x]

            c1, c2, c3 = st.columns(3)
            c1.metric("Pipeline Runs Started (Log)", len(starts))
            c2.metric("Completion Entries (Log)", len(finishes))
            c3.metric("Error Entries (Log)", len(errors))

            durations = [
                float(match.group(1))
                for line in lines
                if (match := re.search(
                    r"Pipeline finished in ([\d.]+) seconds", line
                ))
            ]
            if durations:
                st.metric(
                    "Last Recorded Execution Duration",
                    f"{durations[-1]:.2f} seconds",
                )

            st.subheader("Recent Scheduler Logs")
            st.code("\n".join(lines[-20:]), language="text")
            if DATAOPS_LOG == CLOUD_DATAOPS_LOG:
                st.caption(
                    "These are deployment snapshot logs, not live cloud "
                    "scheduler logs. Multiple historical processes may "
                    "contribute entries."
                )
            else:
                st.caption(
                    "These are recorded local scheduler log entries, "
                    "not an independent process health check."
                )
        else:
            st.warning("DataOps log file not found.")

        show_cloud_workflow()

    with mlops:
        st.subheader("ML Model Evaluation")
        if METRICS.exists():
            try:
                metrics_df = pd.read_csv(METRICS)
            except (OSError, pd.errors.ParserError, pd.errors.EmptyDataError):
                metrics_df = pd.DataFrame()

            required = {"Model", "Accuracy", "Precision", "Recall", "F1 Score"}
            if not metrics_df.empty and required.issubset(metrics_df.columns):
                st.dataframe(
                    metrics_df,
                    use_container_width=True,
                    hide_index=True,
                )
                columns = ["Accuracy", "Precision", "Recall", "F1 Score"]
                st.bar_chart(metrics_df.set_index("Model")[columns])
                best = metrics_df.loc[metrics_df["F1 Score"].idxmax()]
                st.success(f"Best Model by F1 Score: {best['Model']}")
            else:
                st.warning("ML metrics file is empty or missing required columns.")
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
    "Educational prototype using historical UNSW-NB15 network traffic. "
    "Not a production intrusion detection system."
)
