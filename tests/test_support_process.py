
import pytest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.auth.dependencies import get_current_user


@pytest.fixture(autouse=True)
def override_authentication():
    app.dependency_overrides[get_current_user] = lambda: {
        "id": 4,
        "email": "test-agent@example.com",
        "role": "support_agent",
        "customer_id": None,
        "is_active": True,
    }
    yield
    app.dependency_overrides.clear()


client = TestClient(app)


def make_agent_result(
    category="payment",
    needs_review=False,
    routing_status="candidate_for_auto_routing",
):
    return {
        "message": "I was charged twice.",
        "intent": {
            "category": category,
            "confidence": 0.90,
            "margin": 0.80,
            "model_version": "v2",
        },
        "answer": "We need to verify the transaction.",
        "sources": [
            {"id": 8, "title": "Duplicate Payment"}
        ],
        "needs_review": needs_review,
        "review_status": "pending" if needs_review else "not_required",
        "routing_status": routing_status,
        "review_reasons": (
            ["answer_requires_human_review"]
            if needs_review else []
        ),
        "agent_version": "1.0",
    }


def run_process_test(agent_result):
    ticket = {
        "id": 10,
        "message": "I was charged twice.",
    }

    saved_ticket = {
        "id": 10,
        "generated_answer": agent_result["answer"],
        "review_status": agent_result["review_status"],
    }

    with (
        patch(
            "app.main.get_ticket_by_id",
            return_value=ticket,
        ) as mock_get_ticket,
        patch(
            "app.main.run_support_agent",
            return_value=agent_result,
        ) as mock_agent,
        patch(
            "app.main.save_ai_result",
            return_value=saved_ticket,
        ) as mock_save,
    ):
        response = client.post(
            "/support/process",
            json={"ticket_id": 10},
        )

    mock_get_ticket.assert_called_once_with(10)
    mock_agent.assert_called_once_with(ticket["message"])
    mock_save.assert_called_once_with(
        ticket_id=10,
        generated_answer=agent_result["answer"],
        review_status=agent_result["review_status"],
    )

    return response


def test_support_process_auto_routing():
    result = make_agent_result()

    response = run_process_test(result)

    assert response.status_code == 200

    data = response.json()

    assert data["ticket_id"] == 10
    assert data["intent"]["category"] == "payment"
    assert data["needs_review"] is False
    assert data["routing_status"] == "candidate_for_auto_routing"
    assert len(data["sources"]) == 1


def test_support_process_classifier_review():
    result = make_agent_result(
        category="refund",
        needs_review=True,
        routing_status="needs_review",
    )

    response = run_process_test(result)

    assert response.status_code == 200
    assert response.json()["needs_review"] is True
    assert response.json()["review_status"] == "pending"
    assert response.json()["routing_status"] == "needs_review"


def test_support_process_generator_review():
    result = make_agent_result(
        needs_review=True,
        routing_status="needs_review",
    )

    response = run_process_test(result)

    assert response.status_code == 200
    assert response.json()["needs_review"] is True
    assert response.json()["review_status"] == "pending"
    assert "answer_requires_human_review" in (
        response.json()["review_reasons"]
    )


def test_support_process_ticket_not_found():
    with patch(
        "app.main.get_ticket_by_id",
        return_value=None,
    ):
        response = client.post(
            "/support/process",
            json={"ticket_id": 99999},
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Ticket not found"


def test_support_process_invalid_ticket_id():
    response = client.post(
        "/support/process",
        json={"ticket_id": 0},
    )

    assert response.status_code == 422
