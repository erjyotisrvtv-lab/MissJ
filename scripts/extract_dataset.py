from pathlib import Path
import zipfile

BASE_DIR = Path(__file__).resolve().parent.parent

ZIP_FILE = BASE_DIR / "deployment" / "UNSW_NB15_training-set.zip"
DATA_DIR = BASE_DIR / "data"
CSV_FILE = DATA_DIR / "UNSW_NB15_training-set.csv"

DATA_DIR.mkdir(parents=True, exist_ok=True)

if CSV_FILE.exists():
    print("Dataset already available")
else:
    if not ZIP_FILE.exists():
        raise FileNotFoundError(f"Dataset ZIP not found: {ZIP_FILE}")

    with zipfile.ZipFile(ZIP_FILE, "r") as archive:
        archive.extract("UNSW_NB15_training-set.csv", DATA_DIR)

    print("Dataset extracted successfully")

print(f"Dataset path: {CSV_FILE}")