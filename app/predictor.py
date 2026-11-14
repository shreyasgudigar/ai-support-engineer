from pathlib import Path

import joblib


# Find the project root
BASE_DIR = Path(__file__).resolve().parent.parent

# Locate the trained model
MODEL_PATH = BASE_DIR / "artifacts" / "intent_classifier.joblib"

# Load the trained pipeline once
model = joblib.load(MODEL_PATH)


def predict_intent(message: str):
    # Predict the category
    prediction = model.predict([message])[0]

    # Calculate class probabilities
    probabilities = model.predict_proba([message])[0]

    # Find the highest probability
    confidence = float(max(probabilities))

    return {
        "predicted_category": str(prediction),
        "confidence": round(confidence, 4),
    }