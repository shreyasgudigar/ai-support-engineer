from pathlib import Path

import joblib
import pandas as pd

from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_PATH = (
    BASE_DIR / "data" / "processed" / "support_training_v2.csv"
)

MODEL_PATH = (
    BASE_DIR / "artifacts" / "intent_classifier_v2.joblib"
)

# Load validated V2 dataset
df = pd.read_csv(DATA_PATH)

X = df["message"].astype(str)
y = df["category"].astype(str)

# Combine word-level and character-level features
features = FeatureUnion([
    (
        "word",
        TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
        ),
    ),
    (
        "character",
        TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(3, 5),
            min_df=2,
        ),
    ),
])

# Build classifier pipeline
model = Pipeline([
    ("features", features),
    (
        "classifier",
        LogisticRegression(
            max_iter=1000,
            random_state=42,
        ),
    ),
])

print("\nTRAINING V2 CLASSIFIER")
print("=" * 55)

print("Training examples:", len(df))
print("\nCategory distribution:")
print(y.value_counts())

# Train using the complete V2 development dataset
model.fit(X, y)

# Save separately from the deployed model
MODEL_PATH.parent.mkdir(
    parents=True,
    exist_ok=True,
)

joblib.dump(model, MODEL_PATH)

print("\nV2 CLASSIFIER TRAINED SUCCESSFULLY")
print("Model saved to:", MODEL_PATH)

# Quick prediction smoke tests
test_messages = [
    "My debit card was declined.",
    "My parcel has not arrived.",
    "I want a refund for my order.",
    "My bank shows two charges for one purchase.",
    "The payment went through but the order is pending.",
]

print("\nPREDICTION SMOKE TEST")
print("=" * 55)

for message in test_messages:
    prediction = model.predict([message])[0]
    probabilities = model.predict_proba([message])[0]
    confidence = max(probabilities)

    print(f"\nMessage: {message}")
    print(f"Prediction: {prediction}")
    print(f"Confidence: {confidence:.4f}")