
import pandas as pd
from pathlib import Path

# Project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Dataset location
DATASET_PATH = BASE_DIR / "data" / "UNSW_NB15_training-set.csv"

print("=== NETWORK TRAFFIC DATA INGESTION ===")

if not DATASET_PATH.exists():
    raise FileNotFoundError(
        f"Dataset not found: {DATASET_PATH}"
    )

# Load CSV dataset
df = pd.read_csv(DATASET_PATH)

# Display dataset information
print("\nDataset loaded successfully!")
print(f"Total Records: {df.shape[0]}")
print(f"Total Columns: {df.shape[1]}")

print("\nFirst 5 Records:")
print(df.head().to_string())

print("\nColumn Names:")
print(df.columns.tolist())

print("\nData Types:")
print(df.dtypes.to_string())

print("\nMissing Values:")
print(df.isnull().sum().to_string())

print("\nTarget Distribution:")
if "label" in df.columns:
    print(df["label"].value_counts())
else:
    print("Target column 'label' not found")

print("\nDATA INGESTION COMPLETED SUCCESSFULLY")
