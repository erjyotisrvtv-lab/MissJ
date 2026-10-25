"""Enterprise Network Security Monitoring — Streamlit dashboard.
Run: python -m streamlit run scripts/final_dashboard.py
"""
import base64
import json
import os
import re
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

BASE = Path(__file__).resolve().parent.parent
GITHUB_OWNER = "erjyotisrvtv-lab"
GITHUB_REPO = "MissJ"
GITHUB_WORKFLOW = "dataops-cloud.yml"
GITHUB_LOG_BRANCH = "dataops-logs"
GITHUB_RUNS_PAGE = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/actions"
def get_secret(name, default=""):
    """Safely read local environment or Streamlit Cloud secrets."""
    value = os.getenv(name)
    if value:
        return value
    try:
        return st.secrets.get(name, default)
    except (FileNotFoundError, KeyError, OSError, AttributeError):
        return default


def choose_file(local, deployed):
    local_path = BASE / local
    deployed_path = BASE / deployed
    return local_path if local_path.exists() else deployed_path


PREDICTIONS = choose_file("logs/auto_predictions.csv", "deployment/auto_predictions.csv")
METRICS = choose_file("logs/model_metrics.csv", "deployment/model_metrics.csv")
DATAOPS_LOG = choose_file("logs/dataops_scheduler.log", "deployment/dataops_scheduler.log")
API_URL = get_secret("API_URL", "https://missj.onrender.com").rstrip("/")

st.set_page_config(page_title="Enterprise Network Security Dashboard", page_icon="🛡️", layout="wide")
st.title("Enterprise Network Security Monitoring")
st.caption("BITS Pilani | API-Driven Cloud Native Solutions | DataOps • MLOps • FastAPI")




@st.cache_data(ttl=30, show_spinner=False)
def fetch_api(endpoint, base_url):
    try:
        response = requests.get(base_url + endpoint, timeout=10)
        response.raise_for_status()
        return response.json(), None
    except (requests.RequestException, ValueError) as exc:
        return None, str(exc)


@st.cache_data(ttl=30, show_spinner=False)
def fetch_live_dataops(token):
    if not token:
        return None, "GitHub token not configured. Set GITHUB_READ_TOKEN or GITHUB_TOKEN in Streamlit secrets."
    url = (f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
           "/contents/deployment/live_dataops.json")
    try:
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {token}",
                     "Accept": "application/vnd.github+json",
                     "X-GitHub-Api-Version": "2022-11-28"},
            params={"ref": GITHUB_LOG_BRANCH},
            timeout=15,
        )
        response.raise_for_status()
        encoded = response.json()["content"]
        document = json.loads(base64.b64decode(encoded).decode("utf-8-sig"))
        runs = document.get("runs", [])
        if not isinstance(runs, list):
            return None, "GitHub execution history has invalid format."
        return runs, None
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        return None, f"Unable to retrieve GitHub DataOps history: {exc}"


@st.cache_data(ttl=120, show_spinner=False)
def fetch_github_workflow(token):
    if not token:
        return None, "GitHub token not configured for workflow monitoring."
    url = (f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
           f"/actions/workflows/{GITHUB_WORKFLOW}/runs")
    try:
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {token}",
                     "Accept": "application/vnd.github+json"},
            params={"branch": "main", "per_page": 1},
            timeout=15,
        )
        response.raise_for_status()
        items = response.json().get("workflow_runs", [])
        return (items[0], None) if items else (None, "No GitHub Actions runs found.")
    except (requests.RequestException, ValueError, KeyError) as exc:
        return None, f"Unable to fetch GitHub Actions status: {exc}"


def read_csv_safely(path):
    if not path.exists():
        return pd.DataFrame(), "File not found"
    try:
        return pd.read_csv(path), None
    except (OSError, ValueError, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
        return pd.DataFrame(), str(exc)


def show_overview():
    st.subheader("Automated Network Predictions")
    df, error = read_csv_safely(PREDICTIONS)
    if df.empty:
        st.warning(f"Prediction data unavailable: {error or 'No records'}")
        return
    if "prediction" not in df.columns:
        st.warning("Prediction CSV is missing the prediction column.")
        st.dataframe(df.tail(20), use_container_width=True)
        return
    prediction = pd.to_numeric(df["prediction"], errors="coerce")
    normal = int(prediction.eq(0).sum())
    attack = int(prediction.eq(1).sum())
    false_positive = 0
    if "actual_label" in df.columns:
        actual = pd.to_numeric(df["actual_label"], errors="coerce")
        false_positive = int((actual.eq(0) & prediction.eq(1)).sum())
    a, b, c, d = st.columns(4)
    a.metric("Total Predictions", len(df))
    b.metric("Normal", normal)
    c.metric("Attack", attack)
    d.metric("False Positives", false_positive if "actual_label" in df.columns else "N/A")
    st.bar_chart(pd.DataFrame({"Traffic": ["Normal", "Attack"],
                               "Predictions": [normal, attack]}).set_index("Traffic"))
    st.subheader("Recent Traffic Predictions")
    st.dataframe(df.tail(30).iloc[::-1], use_container_width=True, hide_index=True)
    if PREDICTIONS == BASE / "deployment/auto_predictions.csv":
        st.caption("Prediction records are a deployed snapshot, not a live feed.")


def show_dataops():
    st.subheader("Automated DataOps Pipeline")
    st.markdown("### Live GitHub DataOps Monitoring")
    token = get_secret("GITHUB_READ_TOKEN") or get_secret("GITHUB_TOKEN")
    runs, error = fetch_live_dataops(token)
    if error:
        st.warning(error)
    elif not runs:
        st.info("No cloud execution records available.")
    else:
        frame = pd.DataFrame(runs)
        required = {"timestamp_utc", "status", "duration_seconds"}
        if not required.issubset(frame.columns):
            st.warning("Live history is missing required fields.")
        else:
            frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True, errors="coerce")
            frame = frame.dropna(subset=["timestamp_utc"]).sort_values("timestamp_utc", ascending=False)
            if not frame.empty:
                latest = frame.iloc[0]
                ist = latest["timestamp_utc"].tz_convert("Asia/Kolkata")
                duration = pd.to_numeric(pd.Series([latest["duration_seconds"]]), errors="coerce").iloc[0]
                a, b, c, d = st.columns(4)
                a.metric("Cloud Records", len(frame))
                b.metric("Latest Status", str(latest["status"]).title())
                c.metric("Duration", f"{duration:.2f} sec" if pd.notna(duration) else "N/A")
                d.metric("Last Execution (IST)", ist.strftime("%d %b %H:%M:%S"))
                age = (pd.Timestamp.now(tz="UTC") - latest["timestamp_utc"]).total_seconds() / 60
                if age < 0:
                    st.warning("Latest record timestamp is in the future; check system clock.")
                elif age <= 10:
                   st.success(f"Recent DataOps execution ({age:.1f} minutes ago)")
                elif age <= 20:
                   st.warning(f"DataOps scheduler delayed: last execution {age:.1f} minutes ago.")
                else:
                   st.error(f"DataOps execution history is stale: no new record for {age:.1f} minutes. Check GitHub Actions.")
                history = frame.copy()
                history["Execution Time (IST)"] = history["timestamp_utc"].dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m-%d %H:%M:%S")
                st.subheader("Recent Cloud Execution History")
                cols = ["Execution Time (IST)", "status", "duration_seconds"]
                if "source" in history.columns:
                    cols.append("source")
                st.dataframe(history[cols].head(20), use_container_width=True, hide_index=True)
                st.caption("Records are written by the local scheduler to the dataops-logs branch. Manual test records may also be present.")

    st.divider()
    st.subheader("Recorded Scheduler Logs")
    if DATAOPS_LOG.exists():
        try:
            lines = DATAOPS_LOG.read_text(encoding="utf-8", errors="replace").splitlines()
            starts = [line for line in lines if "DataOps pipeline started" in line]
            finishes = [line for line in lines if "Pipeline finished in" in line or "DataOps pipeline completed successfully" in line]
            errors = [line for line in lines if "| ERROR |" in line or "| ERROR |" in line.upper()]
            a, b, c = st.columns(3)
            a.metric("Runs Started (log)", len(starts))
            b.metric("Completed (log)", len(finishes))
            c.metric("Errors (log)", len(errors))
            if finishes:
                match = re.search(r"Pipeline finished in ([\d.]+) seconds", finishes[-1])
                if match:
                    st.metric("Last Logged Duration", f"{float(match.group(1)):.2f} sec")
            st.code("\n".join(lines[-20:]), language="text")
            if DATAOPS_LOG == BASE / "deployment/dataops_scheduler.log":
                st.caption("This is a historical deployment snapshot, not live cloud logging.")
        except OSError as exc:
            st.warning(f"Unable to read scheduler log: {exc}")
    else:
        st.info("Scheduler log file not found.")

    st.divider()
    st.subheader("GitHub Actions — Cloud DataOps")
    st.caption("GitHub Actions scheduled runs are best-effort. Workflow status is independent of the local scheduler records.")
    workflow_token = get_secret("GITHUB_ACTIONS_TOKEN") or token
    workflow, workflow_error = fetch_github_workflow(workflow_token)
    if workflow_error:
        st.info(workflow_error)
    else:
        a, b, c = st.columns(3)
        a.metric("Latest Run", str(workflow.get("run_number", "N/A")))
        b.metric("Status", str(workflow.get("status", "Unknown")).title())
        c.metric("Result", str(workflow.get("conclusion") or "Pending").title())
        created = pd.to_datetime(workflow.get("created_at"), utc=True, errors="coerce")
        st.write("Run created (IST):", created.tz_convert("Asia/Kolkata").strftime("%Y-%m-%d %H:%M:%S") if pd.notna(created) else "N/A")
        st.write("Trigger:", workflow.get("event", "Unknown"))
        st.markdown(f"[View workflow run]({workflow.get('html_url', GITHUB_RUNS_PAGE)})")


def show_mlops():
    st.subheader("ML Model Evaluation")
    df, error = read_csv_safely(METRICS)
    if df.empty:
        st.warning(f"ML metrics unavailable: {error or 'No records'}")
        return
    st.dataframe(df, use_container_width=True, hide_index=True)
    required = {"Model", "Accuracy", "Precision", "Recall", "F1 Score"}
    if not required.issubset(df.columns):
        st.warning("Model metrics are missing one or more required columns.")
        return
    numeric_cols = ["Accuracy", "Precision", "Recall", "F1 Score"]
    for column in numeric_cols:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    st.bar_chart(df.set_index("Model")[numeric_cols])
    valid = df.dropna(subset=["F1 Score"])
    if not valid.empty:
        best = valid.loc[valid["F1 Score"].idxmax()]
        st.success(f"Best Model by F1 Score: {best['Model']}")


def show_api():
    st.subheader("FastAPI Application Monitoring")
    st.caption(f"API endpoint: {API_URL}")
    for endpoint, label in [("/health", "Health"),
                            ("/dataset-info", "Dataset Information"),
                            ("/model-info", "Model Information"),
                            ("/metrics", "API Metrics")]:
        data, error = fetch_api(endpoint, API_URL)
        with st.expander(label, expanded=(endpoint == "/health")):
            if error:
                st.warning(f"{endpoint} unavailable: {error}")
            else:
                if endpoint == "/health":
                    st.success("FastAPI responded successfully")
                st.json(data)
    st.caption("Free-tier Render services may need time to wake up after inactivity.")


@st.fragment(run_every="10s")
def monitoring():
    overview, dataops, mlops, api = st.tabs([
        "Security Overview", "DataOps Monitoring", "MLOps Performance", "REST API Monitoring"
    ])
    with overview:
        show_overview()
    with dataops:
        show_dataops()
    with mlops:
        show_mlops()
    with api:
        show_api()


monitoring()
st.caption("Educational prototype using historical UNSW-NB15 network traffic. Not a production intrusion detection system.")
