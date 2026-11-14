from pathlib import Path

import joblib
import numpy as np


BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = BASE_DIR / "artifacts" / "intent_classifier_v2.joblib"

# Load the trained V2 classifier
model = joblib.load(MODEL_PATH)

# Experimental human-review thresholds
CONFIDENCE_THRESHOLD = 0.80
MARGIN_THRESHOLD = 0.25


def predict_intent_v2(message: str) -> dict:

    if not message.strip():
        raise ValueError("Message cannot be empty.")

    probabilities = model.predict_proba([message])[0]
    classes = model.classes_

    sorted_indices = np.argsort(probabilities)[::-1]

    top_index = sorted_indices[0]
    second_index = sorted_indices[1]

    predicted_category = str(classes[top_index])

    confidence = float(probabilities[top_index])
    margin = float(
        probabilities[top_index] - probabilities[second_index]
    )

    needs_review = (
        confidence < CONFIDENCE_THRESHOLD
        or margin < MARGIN_THRESHOLD
    )

    return {
        "predicted_category": predicted_category,
        "confidence": round(confidence, 4),
        "margin": round(margin, 4),
        "needs_review": bool(needs_review),
        "routing_status": (
            "needs_review"
            if needs_review
            else "candidate_for_auto_routing"
        ),
        "model_version": "v2",
    }