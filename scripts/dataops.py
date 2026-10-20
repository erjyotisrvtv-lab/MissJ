
from apscheduler.schedulers.blocking import BlockingScheduler
from pathlib import Path
from datetime import datetime
import subprocess
import logging
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    filename=LOG_DIR / "dataops_scheduler.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    encoding="utf-8"
)

def run_data_pipeline():
    start_time = datetime.now()
    print(f"\nPipeline started: {start_time}", flush=True)
    logging.info("DataOps pipeline started")

    for script in ["preprocessing.py", "eda.py"]:
        script_path = BASE_DIR / "scripts" / script

        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=BASE_DIR,
                capture_output=True,
                text=True,
                check=True
            )

            logging.info("%s executed successfully", script)
            print(f"SUCCESS: {script}", flush=True)

            output_file = LOG_DIR / f"{script}_latest.log"
            output_file.write_text(
                result.stdout,
                encoding="utf-8"
            )

        except subprocess.CalledProcessError as error:
            logging.error("%s failed: %s", script, error.stderr)
            print(f"FAILED: {script}", flush=True)

    duration = (datetime.now() - start_time).total_seconds()
    logging.info("Pipeline finished in %.2f seconds", duration)
    print(f"Pipeline duration: {duration:.2f} seconds", flush=True)

scheduler = BlockingScheduler()

scheduler.add_job(
    run_data_pipeline,
    trigger="interval",
    minutes=2,
    id="dataops_pipeline",
    max_instances=1,
    coalesce=True
)

print("DataOps Scheduler Started")
print("Pipeline interval: Every 2 minutes")
print("Press Ctrl+C to stop")

run_data_pipeline()

try:
    scheduler.start()
except (KeyboardInterrupt, SystemExit):
    print("Scheduler stopped")
