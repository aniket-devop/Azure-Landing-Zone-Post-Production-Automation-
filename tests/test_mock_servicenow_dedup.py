import mock_servicenow as m


def setup_function():
    m.incidents.clear()
    m.next_number = 100001


def test_open_incident_is_reused():
    c = m.app.test_client()
    first = c.post("/api/incidents", json={"correlation_id": "T1"})
    second = c.post("/api/incidents", json={"correlation_id": "T1"})
    assert first.status_code == 201
    assert second.status_code == 200
    assert first.get_json()["number"] == second.get_json()["number"]


def test_resolved_incident_is_not_reused():
    c = m.app.test_client()
    first = c.post("/api/incidents", json={"correlation_id": "T2"}).get_json()
    c.patch(
        f"/api/incidents/{first['number']}",
        json={"state": "Resolved", "recovery_verified": True},
    )
    second = c.post("/api/incidents", json={"correlation_id": "T2"})
    assert second.status_code == 201
    assert second.get_json()["number"] != first["number"]


def test_resolve_without_verified_recovery_is_rejected():
    c = m.app.test_client()
    inc = c.post("/api/incidents", json={"correlation_id": "T3"}).get_json()
    resp = c.patch(f"/api/incidents/{inc['number']}", json={"state": "Resolved"})
    assert resp.status_code == 409
