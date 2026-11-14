
import pytest
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


def test_home():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == (
        "AI Customer Support API is running"
    )


def test_predict_v2_payment():
    response = client.post(
        "/predict/v2",
        json={"message": "My debit card was declined."},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["predicted_category"] == "payment"
    assert data["model_version"] == "v2"
    assert isinstance(data["confidence"], float)
    assert isinstance(data["margin"], float)
    assert isinstance(data["needs_review"], bool)


def test_predict_v2_refund_review():
    response = client.post(
        "/predict/v2",
        json={
            "message": (
                "Please reverse the purchase "
                "and return the amount I paid."
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["needs_review"] is True


def test_predict_v2_unsupported_request():
    response = client.post(
        "/predict/v2",
        json={"message": "I cannot log in to my account."},
    )

    assert response.status_code == 200
    assert response.json()["needs_review"] is True


def test_predict_v2_empty_message():
    response = client.post(
        "/predict/v2",
        json={"message": ""},
    )

    assert response.status_code == 422
