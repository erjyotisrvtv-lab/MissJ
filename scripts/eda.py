
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_PATH = BASE_DIR / "data" / "dataset_cleaned.csv"
CHART_DIR = BASE_DIR / "charts"
CHART_DIR.mkdir(exist_ok=True)

df = pd.read_csv(DATA_PATH)

print("=== STEP 5A: CORRELATION ANALYSIS ===")
print("Dataset Shape:", df.shape)

# Select important network traffic features
features = [
    "dur", "spkts", "dpkts",
    "sbytes", "dbytes", "rate",
    "sload", "dload", "label"
]

# Calculate Pearson correlation
correlation = df[features].corr()

print("\nCorrelation Matrix:")
print(correlation.round(3).to_string())

# Generate heatmap
plt.figure(figsize=(11, 8))
sns.heatmap(
    correlation,
    annot=True,
    fmt=".2f",
    cmap="coolwarm",
    center=0
)

plt.title("UNSW-NB15 Network Traffic Correlation Heatmap")
plt.tight_layout()

output_path = CHART_DIR / "correlation_heatmap.png"
plt.savefig(output_path, dpi=200)
plt.close()

print("\nHeatmap saved:", output_path)
print("STEP 5A COMPLETED")


print("\n=== STEP 5B: UNIVARIATE AND BIVARIATE ANALYSIS ===")

# Univariate: Normal vs Attack Traffic
plt.figure(figsize=(8, 5))
sns.countplot(data=df, x="label")
plt.title("Normal vs Attack Traffic Distribution")
plt.xlabel("Traffic Class (0=Normal, 1=Attack)")
plt.ylabel("Number of Records")
plt.tight_layout()
plt.savefig(CHART_DIR / "traffic_distribution.png", dpi=200)
plt.close()

print("Univariate chart saved successfully!")

# Bivariate: Traffic Rate vs Attack Label
plt.figure(figsize=(9, 5))

# Sample data for readable visualization
sample_df = df.sample(
    n=min(5000, len(df)),
    random_state=42
)

sns.boxplot(
    data=sample_df,
    x="label",
    y="rate",
    showfliers=False
)

plt.title("Traffic Rate Comparison: Normal vs Attack")
plt.xlabel("Traffic Class (0=Normal, 1=Attack)")
plt.ylabel("Traffic Rate")
plt.tight_layout()
plt.savefig(CHART_DIR / "traffic_rate_comparison.png", dpi=200)
plt.close()

print("Bivariate chart saved successfully!")
print("STEP 5B COMPLETED")


print("\n=== STEP 5C: BINNING AND ENCODING ===")

# Create a separate copy for EDA transformations
df_encoded = df.copy()

# 1. Binning traffic rate into three categories
df_encoded["rate_category"] = pd.cut(
    df_encoded["rate"],
    bins=[-float("inf"), 100, 1000, float("inf")],
    labels=["Low", "Medium", "High"]
)

print("\nTraffic Rate Binning:")
print(df_encoded["rate_category"].value_counts())

# 2. One-hot encoding for network protocol
df_encoded = pd.get_dummies(
    df_encoded,
    columns=["proto", "service", "state"],
    dtype=int
)

print("\nOriginal Number of Columns:", df.shape[1])
print("Columns After Encoding:", df_encoded.shape[1])

# 3. Save encoded dataset
encoded_path = BASE_DIR / "data" / "dataset_encoded.csv"
df_encoded.to_csv(encoded_path, index=False)

print("\nEncoded dataset saved successfully!")
print("STEP 5C COMPLETED")


from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

print("\n=== STEP 5D: FEATURE IMPORTANCE ANALYSIS ===")

# Select numeric network traffic features
feature_columns = [
    "dur", "spkts", "dpkts", "sbytes", "dbytes",
    "rate", "sttl", "dttl", "sload", "dload",
    "sloss", "dloss", "sinpkt", "dinpkt"
]

X = df[feature_columns]
y = df["label"]

# Split before model fitting
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.30,
    random_state=42,
    stratify=y
)

# Train Random Forest
rf = RandomForestClassifier(
    n_estimators=50,
    max_depth=12,
    random_state=42,
    n_jobs=-1
)

rf.fit(X_train, y_train)

# Calculate feature importance
importance = pd.DataFrame({
    "Feature": feature_columns,
    "Importance": rf.feature_importances_
}).sort_values(by="Importance", ascending=False)

print("\nTop 10 Important Features:")
print(importance.head(10).to_string(index=False))

# Plot feature importance
plt.figure(figsize=(10, 6))
sns.barplot(
    data=importance.head(10),
    x="Importance",
    y="Feature"
)

plt.title("Top 10 Important Network Traffic Features")
plt.tight_layout()

output_path = CHART_DIR / "feature_importance.png"
plt.savefig(output_path, dpi=200)
plt.close()

print("\nFeature Importance Chart Saved:", output_path)
print("STEP 5D COMPLETED")



