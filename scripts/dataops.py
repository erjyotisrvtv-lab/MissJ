from apscheduler.schedulers.blocking import BlockingScheduler
from pathlib import Path
from datetime import datetime
import subprocess
import logging
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

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

    for script in [
        "extract_dataset.py",
        "preprocessing.py",
        "eda.py"
    ]:
        script_path = BASE_DIR / "scripts" / script

        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=BASE_DIR,
                capture_output=True,
                text=True,
                check=True
            )

            print(f"{script} completed successfully", flush=True)
            logging.info("%s completed successfully", script)

            if result.stdout:
                print(result.stdout, flush=True)

        except subprocess.CalledProcessError as error:
            print(f"Error in {script}: {error.stderr}", flush=True)
            logging.error("%s failed: %s", script, error.stderr)
            return

    end_time = datetime.now()
    logging.info("DataOps pipeline completed successfully")
    print(f"Pipeline completed: {end_time}", flush=True)


scheduler = BlockingScheduler()

scheduler.add_job(
    run_data_pipeline,
    trigger="interval",
    minutes=2,
    id="dataops_pipeline",
    max_instances=1,
    coalesce=True
)

if __name__ == "__main__":
    print("DataOps Scheduler Started")
    print("Pipeline interval: Every 2 minutes")
    print("Press Ctrl+C to stop")

    run_data_pipeline()

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("Scheduler stopped")