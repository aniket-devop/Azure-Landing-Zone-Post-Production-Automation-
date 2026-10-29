
import pytest

from mock_servicenow import app, incidents


@pytest.fixture(autouse=True)
def reset_incidents():
    """Give every test a clean incident store."""
    with app.app_context():
        incidents.clear()
        yield
        incidents.clear()


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as test_client:
        yield test_client


def create_payload(correlation_id="IYAV-TEST-001"):
    return {
        "correlation_id": correlation_id,
        "short_description": "Automated test incident",
    }


def test_create_incident(client):
    response = client.post(
        "/api/incidents",
        json=create_payload(),
    )

    assert response.status_code == 201
    assert response.json["number"] == "INC100001"
    assert response.json["state"] == "New"


def test_duplicate_does_not_create_another_incident(client):
    first = client.post(
        "/api/incidents",
        json=create_payload(),
    )
    second = client.post(
        "/api/incidents",
        json=create_payload(),
    )

    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json["number"] == second.json["number"]
    assert len(incidents) == 1


def test_missing_correlation_id_is_rejected(client):
    response = client.post(
        "/api/incidents",
        json={"short_description": "Missing key"},
    )

    assert response.status_code == 400


def test_resolution_requires_verified_recovery(client):
    created = client.post(
        "/api/incidents",
        json=create_payload(),
    )
    number = created.json["number"]

    rejected = client.patch(
        f"/api/incidents/{number}",
        json={
            "state": "Resolved",
            "recovery_verified": False,
        },
    )

    assert rejected.status_code == 409

    current = client.get(f"/api/incidents/{number}")
    assert current.json["state"] == "New"


def test_verified_recovery_allows_resolution(client):
    created = client.post(
        "/api/incidents",
        json=create_payload(),
    )
    number = created.json["number"]

    resolved = client.patch(
        f"/api/incidents/{number}",
        json={
            "state": "Resolved",
            "recovery_verified": True,
        },
    )

    assert resolved.status_code == 200
    assert resolved.json["state"] == "Resolved"
