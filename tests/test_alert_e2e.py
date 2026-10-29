import requests

import alert_processor
import mock_servicenow as m


class _Resp:
    def __init__(self, resp):
        self._resp = resp
        self.status_code = resp.status_code

    def json(self):
        return self._resp.get_json()

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


def setup_function():
    m.incidents.clear()
    m.next_number = 100001


def sample_alert():
    return {
        "alert_id": "e2e-alert-001",
        "alert_rule": "Disk-Space-Low",
        "severity": "Sev2",
        "resource_id": (
            "/subscriptions/demo/resourceGroups/rg-lab/"
            "providers/Microsoft.Compute/virtualMachines/vm-demo"
        ),
        "description": "Disk free space below threshold",
    }


def test_alert_creates_and_reuses_local_incident(monkeypatch):
    client = m.app.test_client()

    def fake_post(url, json=None, timeout=None):
        path = url.replace(alert_processor.SERVICENOW_URL, "")
        return _Resp(client.post(path, json=json))

    monkeypatch.setattr(alert_processor.requests, "post", fake_post)

    result1 = alert_processor.handle_alert(sample_alert())
    result2 = alert_processor.handle_alert(sample_alert())

    assert result1["processing_status"] == "incident_linked"
    assert result1["incident_number"] == result2["incident_number"]

    listing = client.get("/api/incidents").get_json()
    matching = [
        item
        for item in listing
        if item["correlation_id"] == result1["correlation_id"]
    ]
    assert len(matching) == 1


def teardown_function():
    m.incidents.clear()
    m.next_number = 100001
