
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
import joblib

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "UNSW_NB15_training-set.csv"
MODEL_DIR = BASE_DIR / "models"
LOG_DIR = BASE_DIR / "logs"

MODEL_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

print("=== STEP 7A: MACHINE LEARNING TRAINING ===")

df = pd.read_csv(DATA_PATH)

# Select numeric network traffic features
features = [
    "dur", "spkts", "dpkts", "sbytes", "dbytes",
    "rate", "sttl", "dttl", "sload", "dload",
    "sloss", "dloss", "sinpkt", "dinpkt"
]

X = df[features]
y = df["label"]

# Split before fitting preprocessing steps
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.30,
    random_state=42,
    stratify=y
)

print("Total Records:", len(df))
print("Training Records:", len(X_train))
print("Testing Records:", len(X_test))

models = {
    "Decision Tree": DecisionTreeClassifier(
        max_depth=12,
        random_state=42
    ),
    "Random Forest": RandomForestClassifier(
        n_estimators=50,
        max_depth=12,
        random_state=42,
        n_jobs=-1
    )
}

results = []

for name, algorithm in models.items():
    print(f"\nTraining {name}...")

    pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("classifier", algorithm)
    ])

    pipeline.fit(X_train, y_train)
    predictions = pipeline.predict(X_test)

    metrics = {
        "Model": name,
        "Accuracy": accuracy_score(y_test, predictions),
        "Precision": precision_score(
            y_test, predictions, zero_division=0
        ),
        "Recall": recall_score(
            y_test, predictions, zero_division=0
        ),
        "F1 Score": f1_score(
            y_test, predictions, zero_division=0
        )
    }

    results.append(metrics)

    filename = name.lower().replace(" ", "_") + ".pkl"
    joblib.dump(pipeline, MODEL_DIR / filename)

    print(f"{name} trained and saved successfully!")

results_df = pd.DataFrame(results)

print("\n=== MODEL EVALUATION RESULTS ===")
print(results_df.to_string(index=False))

results_df.to_csv(
    LOG_DIR / "model_metrics.csv",
    index=False
)

print("\nSTEP 7A COMPLETED")
