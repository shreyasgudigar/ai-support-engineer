from app.predictor_v2 import predict_intent_v2
from app.generator import generate_support_answer


def run_support_agent(message: str) -> dict:
    """
    Orchestrate the customer support AI pipeline:
    1. Classify customer intent.
    2. Retrieve knowledge and generate a grounded answer.
    3. Decide whether human review is required.
    """

    if not message or not message.strip():
        raise ValueError("Customer message cannot be empty.")

    # Step 1: ML intent classification
    intent = predict_intent_v2(message)

    # Step 2: RAG retrieval and LLM answer generation
    # Retrieval is performed internally by generate_support_answer().
    generation = generate_support_answer(message)

    # Step 3: Agent decision-making
    review_reasons = []

    if intent["needs_review"]:
        review_reasons.append("low_intent_confidence_or_margin")

    if generation["needs_review"]:
        review_reasons.append("answer_requires_human_review")

    needs_review = bool(review_reasons)

    # Step 4: Return structured agent output
    return {
        "message": message,
        "intent": {
            "category": intent["predicted_category"],
            "confidence": intent["confidence"],
            "margin": intent["margin"],
            "model_version": intent["model_version"],
        },
        "answer": generation["answer"],
        "sources": generation["sources"],
        "needs_review": needs_review,
        "review_status": "pending" if needs_review else "not_required",
        "routing_status": (
            "needs_review" if needs_review
            else "candidate_for_auto_routing"
        ),
        "review_reasons": review_reasons,
        "agent_version": "1.0",
    }
