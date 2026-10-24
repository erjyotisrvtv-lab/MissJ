
"""Upload a compact DataOps execution record to GitHub."""

import base64
import json
import os
import sys
import time
from datetime import datetime, timezone

import requests

OWNER = "erjyotisrvtv-lab"
REPO = "MissJ"
BRANCH = "dataops-logs"
FILE_PATH = "deployment/live_dataops.json"

URL = (
    f"https://api.github.com/repos/{OWNER}/{REPO}"
    f"/contents/{FILE_PATH}"
)


def synchronize(status, duration_seconds=None):
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is not configured")

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "duration_seconds": duration_seconds,
        "source": "local_dataops_scheduler",
    }

    for attempt in range(3):
        response = requests.get(
            URL, headers=headers, params={"ref": BRANCH}, timeout=20
        )
        response.raise_for_status()
        metadata = response.json()

        content = base64.b64decode(metadata["content"]).decode("utf-8-sig")
        document = json.loads(content)

        document.setdefault("runs", []).append(record)
        document["runs"] = document["runs"][-100:]

        encoded = base64.b64encode(
            json.dumps(document, indent=2).encode("utf-8")
        ).decode("ascii")

        payload = {
            "message": "Update live DataOps execution record",
            "content": encoded,
            "sha": metadata["sha"],
            "branch": BRANCH,
        }

        result = requests.put(
            URL, headers=headers, json=payload, timeout=30
        )

        if result.status_code in (200, 201):
            print("SUCCESS: DataOps record synchronized to GitHub")
            return

        if result.status_code in (409, 422) and attempt < 2:
            time.sleep(attempt + 1)
            continue

        result.raise_for_status()

    raise RuntimeError("GitHub synchronization retries exhausted")


if __name__ == "__main__":
    status = sys.argv[1] if len(sys.argv) > 1 else "success"
    duration = float(sys.argv[2]) if len(sys.argv) > 2 else None

    if status not in ("success", "failed"):
        raise SystemExit("Status must be success or failed")

    synchronize(status, duration)
