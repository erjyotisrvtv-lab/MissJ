
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "UNSW_NB15_training-set.csv"

df = pd.read_csv(DATA_PATH)

print("=== DATA PREPROCESSING ===")

print("\n1. Dataset Shape:")
print(df.shape)

print("\n2. Data Types:")
print(df.dtypes.to_string())

print("\n3. Summary Statistics:")
print(df.describe(include="all").to_string())

print("\n4. Missing Values:")
print(df.isnull().sum().to_string())

print("\n5. Total Missing Values:")
print(df.isnull().sum().sum())

print("\nSTEP 4A COMPLETED")

import numpy as np

print("\n=== STEP 4B: INDUCING MISSING VALUES ===")

# Original data ko safe rakhein
df_missing = df.copy()

# Numeric columns select karein
numeric_columns = ["sbytes", "dbytes", "dur"]

# Reproducible experiment
rng = np.random.default_rng(42)

for col in numeric_columns:
    # Randomly 5% rows select karein
    selected_rows = rng.choice(
        df_missing.index,
        size=int(len(df_missing) * 0.05),
        replace=False
    )

    # Selected values ko missing banayein
    df_missing.loc[selected_rows, col] = np.nan

print("\nMissing values after induction:")
print(df_missing[numeric_columns].isnull().sum())

# Experiment ka output save karein
output_path = BASE_DIR / "data" / "dataset_with_missing.csv"
df_missing.to_csv(output_path, index=False)

print("\nDataset with missing values saved successfully!")
print("STEP 4B COMPLETED")

from sklearn.impute import SimpleImputer

print("\n=== STEP 4C: MISSING VALUE IMPUTATION ===")

# Step 4B se generated dataset use karein
df_cleaned = df_missing.copy()

# Median-based imputation
imputer = SimpleImputer(strategy="median")

df_cleaned[numeric_columns] = imputer.fit_transform(
    df_cleaned[numeric_columns]
)

print("\nMissing values after imputation:")
print(df_cleaned[numeric_columns].isnull().sum())

print("\nTotal missing values remaining:")
print(df_cleaned.isnull().sum().sum())

# Cleaned dataset save karein
cleaned_path = BASE_DIR / "data" / "dataset_cleaned.csv"
df_cleaned.to_csv(cleaned_path, index=False)

print("\nCleaned dataset saved successfully!")
print("STEP 4C COMPLETED")


from sklearn.preprocessing import StandardScaler

print("\n=== STEP 4D: DATA NORMALIZATION ===")

# Cleaned dataset ki copy
df_normalized = df_cleaned.copy()

# Selected numeric features
scale_columns = ["sbytes", "dbytes", "dur"]

# StandardScaler apply karein
scaler = StandardScaler()

df_normalized[scale_columns] = scaler.fit_transform(
    df_normalized[scale_columns]
)

print("\nBefore Normalization:")
print(df_cleaned[scale_columns].head())

print("\nAfter Normalization:")
print(df_normalized[scale_columns].head())

print("\nNormalized Feature Means:")
print(df_normalized[scale_columns].mean())

# Save normalized dataset
normalized_path = BASE_DIR / "data" / "dataset_normalized.csv"
df_normalized.to_csv(normalized_path, index=False)

print("\nNormalized dataset saved successfully!")
print("STEP 4D COMPLETED")


